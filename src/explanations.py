"""Student-friendly explanation generation for model and baseline rankings."""

from collections import defaultdict
from typing import Dict, List

import numpy as np
import pandas as pd

# ======================================================================
# = CONFIG
# ======================================================================

MAX_EXPLANATION_LENGTH = 3
MIN_CONTRIBUTION = 1e-3


# Student-friendly names (based on educator table)
BASE_TO_CLAUSES = {
    "Task Common": {
        "pos": "it is more common in this task",
        "neg": "it is less common in this task",
    },
    "Task Characteristic": {
        "pos": "it is more typical of this task",
        "neg": "it is less typical of this task",
    },
    "Student Common": {
        "pos": "the student introduces this defect more often",
        "neg": "the student introduces this defect less often",
    },
    "Student Characteristic": {
        "pos": "the student introduces this defect more often than their peers",
        "neg": "the student introduces this defect less often than their peers",
    },
    "Student Encountered": {
        "pos": "the student has repeated this defect more recently",
        "neg": "the student has repeated this defect longer time ago",
    },
    "Defect Multiplicity": {
        "pos": "there are more instances of it in this submission",
        "neg": "there are fewer instances of it in this submission",
    },
    "Naive Severity": {
        "pos": "it is considered more severe",
        "neg": "it is considered less severe",
    },
}


# ======================================================================
# = HELPER FUNCTIONS
# ======================================================================


def _assemble_sentence(base: str, peers_ranks: List[int], signed_value: float) -> str:
    """Generate final student-visible explanation."""
    if not peers_ranks:
        return ""

    clause_dict = BASE_TO_CLAUSES.get(base)
    if clause_dict is None:
        return ""

    clause = clause_dict["pos"] if signed_value >= 0 else clause_dict["neg"]

    if len(peers_ranks) == 1:
        return f"Ranked above rank {peers_ranks[0]} because {clause}."
    else:
        ranks_text = ", ".join(str(r) for r in peers_ranks)
        return f"Ranked above ranks {ranks_text} because {clause}."


def _aggregate_base_contributions(contrib_dict: Dict[str, float], catalog) -> Dict[str, float]:
    base_sum = defaultdict(float)

    for col, val in contrib_dict.items():
        meta = catalog.get(col)
        if meta is None:
            continue
        if meta.base == "Metadata":
            continue
        base_sum[meta.base] += val

    return dict(base_sum)


# ======================================================================
# = MODEL EXPLANATIONS
# ======================================================================


def explain_submission(
    submission_df: pd.DataFrame,
    ranking: List[int],
    X: pd.DataFrame,
    weights: np.ndarray,
    catalog: Dict[str, object],
) -> Dict[int, List[str]]:
    """Generate student-friendly explanations for the model-based ranking."""
    # Map pair to row index
    pair_idx = {}
    for idx, row in submission_df.iterrows():
        pair_idx[(row["left"], row["right"])] = idx
        pair_idx[(row["right"], row["left"])] = idx

    # Compute contributions for each row: weight * feature_value
    cols = list(X.columns)
    w = np.asarray(weights, float)

    row_contribs = {}
    for idx in X.index:
        xv = X.loc[idx].values.astype(float)
        contrib = w * xv
        row_contribs[idx] = dict(zip(cols, contrib))

    # For each row, compute base-level contributions
    row_base_contribs = {idx: _aggregate_base_contributions(cd, catalog) for idx, cd in row_contribs.items()}

    # Which bases are "meaningful" for a row?
    row_meaningful_bases = {
        idx: {b for b, v in base_sum.items() if abs(v) >= MIN_CONTRIBUTION}
        for idx, base_sum in row_base_contribs.items()
    }

    # Precompute ranks
    rank_pos = {d: i + 1 for i, d in enumerate(ranking)}

    explanations = {}

    # For each defect, compare against lower-ranked defects
    for i, defect in enumerate(ranking):
        lower = ranking[i + 1 :]
        base_to_peers = defaultdict(list)

        for other in lower:
            if (defect, other) not in pair_idx:
                continue
            r_idx = pair_idx[(defect, other)]
            row = submission_df.loc[r_idx]

            left_is_defect = row["left"] == defect
            pred = row["model_prediction"]

            # Check if model agrees with final ranking for this pair
            aligns = (left_is_defect and pred == 1) or ((not left_is_defect) and pred == 0)
            if not aligns:
                continue

            # Add bases that supported this pair
            for base in row_meaningful_bases.get(r_idx, set()):
                base_to_peers[base].append(other)

        # No supporting bases?
        if not base_to_peers:
            explanations[defect] = ["Placed here: no heuristic clearly distinguished it from lower-ranked defects."]
            continue

        # Order bases by number of peers supported
        ordered = sorted(base_to_peers.items(), key=lambda kv: len(kv[1]), reverse=True)

        sentences = []
        for base, peers in ordered[:MAX_EXPLANATION_LENGTH]:
            # Convert peers → ranks
            peer_ranks = [rank_pos[p] for p in peers]

            # Signed value = sum of contributions for this base (take from the FIRST peer, same sign)
            signed_value = row_base_contribs[pair_idx[(defect, peers[0])]][base]

            sent = _assemble_sentence(base, peer_ranks, signed_value)
            if sent:
                sentences.append(sent)

        if not sentences:
            sentences = ["Placed here: no heuristic clearly distinguished it from lower-ranked defects."]

        explanations[defect] = sentences

    return explanations


# ======================================================================
# = BASELINE EXPLANATIONS
# ======================================================================


def explain_baseline_submission(
    submission_df: pd.DataFrame,
    ranking: List[int],
    primary_cols: List[str],
    secondary_cols: List[str],
) -> Dict[int, List[str]]:
    """Student-friendly explanations for the baseline ranking (primary + secondary heuristic)."""

    def normalize(col):
        return col.split(" (")[0]

    primary_bases = {normalize(c) for c in primary_cols}
    secondary_bases = {normalize(c) for c in secondary_cols}

    # Pick one (baseline usually uses only one)
    primary_base = list(primary_bases)[0] if primary_bases else None
    secondary_base = list(secondary_bases)[0] if secondary_bases else None

    # Base names must still map to BASE_TO_NOUN
    base_for_primary = primary_base
    base_for_secondary = secondary_base

    # Build pair → index
    pair_idx = {}
    for idx, row in submission_df.iterrows():
        pair_idx[(row["left"], row["right"])] = idx
        pair_idx[(row["right"], row["left"])] = idx

    rank_pos = {d: i + 1 for i, d in enumerate(ranking)}

    explanations = {}

    for i, defect in enumerate(ranking):
        lower = ranking[i + 1 :]

        primary_peers = []
        secondary_peers = []

        for other in lower:
            if (defect, other) not in pair_idx:
                continue

            idx_row = pair_idx[(defect, other)]
            row = submission_df.loc[idx_row]

            pred = row["baseline_prediction"]
            tiebreak = row["baseline_tiebreak"]
            defect_is_left = row["left"] == defect

            # PRIMARY decision
            primary_win = (defect_is_left and pred == 1) or ((not defect_is_left) and pred == 0)

            if primary_win:
                primary_peers.append(other)
                continue

            # SECONDARY tiebreak decision
            secondary_win = (defect_is_left and tiebreak > 0) or ((not defect_is_left) and tiebreak < 0)
            if secondary_win:
                secondary_peers.append(other)

        sentences = []

        # --- Primary heuristic explanation ---
        if primary_peers:
            peers_ranks = [rank_pos[p] for p in primary_peers]
            # Baseline always uses "more" because it is a heuristic score, not a signed LR contribution.
            # But the model might prefer smaller values? If so, adapt here.
            sent = _assemble_sentence(base_for_primary, peers_ranks, signed_value=1.0)
            sentences.append(sent)

        # --- Secondary explanation ---
        if secondary_peers and base_for_secondary:
            peers_ranks = [rank_pos[p] for p in secondary_peers]
            sent = _assemble_sentence(base_for_secondary, peers_ranks, signed_value=1.0)
            sentences.append(sent)

        if not sentences:
            sentences = ["Placed here: no heuristic clearly distinguished it from lower-ranked defects."]

        explanations[defect] = sentences[:MAX_EXPLANATION_LENGTH]

    return explanations
