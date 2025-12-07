"""Explanations of the final model ranking."""

import numpy as np
import pandas as pd

MAX_EXPLANATION_LENGTH = 3
MIN_CONTRIBUTION = 0.01

from collections import Counter, defaultdict
from typing import Dict, List

import numpy as np
import pandas as pd

# constants already in your notebook; if not, set defaults here
MAX_EXPLANATION_LENGTH = 3
MIN_CONTRIBUTION = 1e-3


def explain_submission(
    submission_df: pd.DataFrame,
    ranking: List,
    X: pd.DataFrame,
    weights: np.ndarray,
    catalog: Dict[str, object],
) -> Dict:
    """Explain the ordering of defects in a submission as determined by a Logistic Regression model.

    Args:
        submission_df: DataFrame of pairwise rows for this submission (same order as X).
        ranking: List of defect ids in ranked order (highest first).
        X: Feature matrix (rows correspond to submission_df rows) used by ordering model.
        weights: 1D array of model weights aligned with X.columns.
        catalog: FeatureCatalog mapping column name -> FeatureMeta.
    Returns:
        dict: mapping defect_id -> list[str] (explanation sentences).
    """
    assert len(X) == len(submission_df)
    # Map pair to row index for fast lookup
    pair_to_idx = {}
    for idx, row in submission_df.iterrows():
        pair_to_idx[(row["left"], row["right"])] = idx
        pair_to_idx[(row["right"], row["left"])] = idx  # allow reversed lookup

    # Precompute contributions (array) for each row index
    # contribution per column = weight * x_value
    contributions = {}
    cols = list(X.columns)
    w = np.asarray(weights)

    for idx in X.index:
        xv = X.loc[idx].values.astype(float)
        contrib = w * xv  # signed contributions
        contributions[idx] = dict(zip(cols, contrib))

    # Helper: aggregate column-level contributions into base-level contributions
    def row_base_contribs(row_idx):
        """Return dict base -> signed contribution sum for the row."""
        col_contribs = contributions[row_idx]
        base_acc = defaultdict(float)
        for colname, val in col_contribs.items():
            meta = catalog.get(colname)
            if meta.base == "Metadata":
                continue
            base_acc[meta.base] += val
        return base_acc

    # For each pair, compute which bases are "meaningful" (abs >= min_contribution)
    pair_base_support = {}  # row_idx -> set of bases that meaningfully supported the winner
    for idx in submission_df.index:
        base_acc = row_base_contribs(idx)
        # Keep bases whose absolute signed contribution >= threshold
        meaningful = {b for b, v in base_acc.items() if abs(v) >= MIN_CONTRIBUTION}
        pair_base_support[idx] = meaningful

    # Map defect -> aggregated supporting bases -> list of other defects that contributed
    explanations = {}
    # Precompute rank position lookup (1-based for student-friendly)
    rank_pos = {def_id: pos + 1 for pos, def_id in enumerate(ranking)}

    # For each defect in ranking, examine comparisons vs defects ranked below it
    for i, defect in enumerate(ranking):
        below = ranking[i + 1 :]
        # collect base -> list of (other_defect, pair_idx) that supported defect over other_defect
        base_to_peers = defaultdict(list)

        for other in below:
            # find pair row and ensure the model's pairwise prediction aligns with final ranking
            if (defect, other) not in pair_to_idx:
                continue
            row_idx = pair_to_idx[(defect, other)]
            row = submission_df.loc[row_idx]
            # Determine which side corresponds to defect in this row
            left_is_defect = row["left"] == defect
            pred = row.get("model_prediction")

            aligns = (left_is_defect and pred == 1) or ((not left_is_defect) and pred == 0)
            if not aligns:
                # The pairwise model disagrees with final ranking for this pair; skip
                continue

            # Which bases supported this pair (from pair_base_support)
            supporting_bases = pair_base_support.get(row_idx, set())
            for b in supporting_bases:
                base_to_peers[b].append(other)

        if len(base_to_peers) == 0:
            # fallback short message
            explanations[defect] = ["No single heuristic strongly supported this defect over those ranked below."]
            continue

        # Rank bases by number of supporting peers (descending)
        base_counts = sorted(base_to_peers.items(), key=lambda kv: len(kv[1]), reverse=True)

        sentences = []
        for base, peers in base_counts[:MAX_EXPLANATION_LENGTH]:
            # Keep peers unique and in the same order as ranking
            unique_peers = []
            seen = set()
            for p in peers:
                if p in seen:
                    continue
                seen.add(p)
                unique_peers.append(p)
            # map to "defect {id} (rank N)" strings and join
            mapped = ", ".join(f"{p} (rank {rank_pos.get(p, '?')})" for p in unique_peers)
            # sentence: "More <base> than defects X and Y."
            # use simple phrasing — base lowercased
            if len(unique_peers) == 1:
                sent = f"More {base.lower()} than defect {mapped}."
            else:
                sent = f"More {base.lower()} than defects {mapped}."
            sentences.append(sent)

        explanations[defect] = sentences

    return explanations


def explain_baseline_submission(
    submission_df: pd.DataFrame,
    ranking: list,
    primary_cols: list,
    secondary_cols: list,
) -> dict:
    """Explain the ordering of defects in a submission as determined by the baseline model.

    Args:
        submission_df: Pairwise rows for this submission.
        ranking: Final baseline ranking of defect ids (highest first).
        primary_cols: List of feature names used by the primary baseline model.
        secondary_cols: List of feature names used by the secondary baseline model.

    Returns:
        dict: defect_id -> list[str]
    """

    # For convenience, build mapping from feature name to base heuristic
    def normalize(col):
        # e.g. "Task Common (Difference Discrete)" → "Task Common"
        return col.split(" (")[0]

    primary_bases = {normalize(c) for c in primary_cols}
    secondary_bases = {normalize(c) for c in secondary_cols}

    # Identify the *dominant* base (usually exactly one)
    # If multiple: include all.
    primary_base = list(primary_bases)
    secondary_base = list(secondary_bases)

    # Make student-friendly descriptions
    def base_desc(b):
        return b.lower()

    # Precompute rank lookup
    rank_pos = {d: i + 1 for i, d in enumerate(ranking)}

    # Build lookup: (d1, d2) → row index
    pair_index = {}
    for idx, row in submission_df.iterrows():
        pair_index[(row["left"], row["right"])] = idx
        pair_index[(row["right"], row["left"])] = idx

    explanations = {}

    for i, defect in enumerate(ranking):
        below = ranking[i + 1 :]

        primary_peers = []  # defects ranked lower because of primary heuristic
        secondary_peers = []  # defects tied in primary but broken by secondary

        for other in below:
            if (defect, other) not in pair_index:
                continue

            row = submission_df.loc[pair_index[(defect, other)]]
            pred = row["baseline_prediction"]

            # Determine which defect is 'left' in this row
            defect_is_left = row["left"] == defect

            # Check if primary decision placed defect above other
            primary_decision = pred

            # Interpret: pred == 1 means left > right
            if defect_is_left and primary_decision == 1:
                primary_peers.append(other)
                continue
            elif (not defect_is_left) and primary_decision == 0:
                primary_peers.append(other)
                continue

            # Otherwise, check secondary tiebreak
            tiebreak = row["baseline_tiebreak"]
            if defect_is_left and tiebreak > 0:
                secondary_peers.append(other)
            elif (not defect_is_left) and tiebreak < 0:
                secondary_peers.append(other)

        sentences = []

        # --- Primary heuristic explanations ---
        if len(primary_peers) > 0:
            peers_txt = ", ".join(f"{p} (rank {rank_pos[p]})" for p in primary_peers)
            if len(primary_base) == 1:
                b = base_desc(primary_base[0])
                if len(primary_peers) == 1:
                    sent = f"Ranked above defect {peers_txt} because its {b} score is higher."
                else:
                    sent = f"Ranked above defects {peers_txt} because its {b} score is higher."
            else:
                # Multiple primary heuristics (rare but supported)
                bases_txt = ", ".join(base_desc(b) for b in primary_base)
                sent = f"Ranked above defects {peers_txt} based on {bases_txt} scores."
            sentences.append(sent)

        # --- Secondary heuristic explanations (ties) ---
        if len(secondary_peers) > 0:
            peers_txt = ", ".join(f"{p} (rank {rank_pos[p]})" for p in secondary_peers)
            if len(secondary_base) == 1:
                b = base_desc(secondary_base[0])
                if len(secondary_peers) == 1:
                    sent = f"Tied on the main heuristic but ranked above defect {peers_txt} due to {b}."
                else:
                    sent = f"Tied on the main heuristic but ranked above defects {peers_txt} due to {b}."
            else:
                bases_txt = ", ".join(base_desc(b) for b in secondary_base)
                sent = f"Tied on the main heuristic but broken in favor of this defect using {bases_txt}."
            sentences.append(sent)

        if len(sentences) == 0:
            sentences = ["No strong heuristic differences compared to lower-ranked defects."]

        explanations[defect] = sentences[:MAX_EXPLANATION_LENGTH]

    return explanations
