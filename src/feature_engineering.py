"""Functions for building and processing features."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sklearn.preprocessing import OneHotEncoder

# ============================================================
# Controlled vocabularies
# ============================================================

BASE_VALUES = {
    "Task Common",
    "Task Characteristic",
    "Student Common",
    "Student Characteristic",
    "Student Encountered",
    "Defect Multiplicity",
    "Naive Severity",
    "Metadata",
}

KIND_VALUES = {"Original", "Difference", "Binary", "Extreme", "Metadata"}

DTYPE_VALUES = {"Discrete", "Continuous", "Binary", "Categorical"}

SIDE_VALUES = {"Left", "Right", None}


# ============================================================
# Feature metadata structure
# ============================================================


@dataclass(frozen=True)
class FeatureMeta:
    """Metadata for a feature."""

    base: str  # The heuristic family
    kind: str  # "orig", "diff", "bin", "ext", "meta"
    dtype: str  # "disc", "cont", "bin", "cat"
    side: str  # "L", "R", "NA"
    extra: dict | None  # free-form additional information
    description: str  # human-readable explanation


FeatureCatalog = Dict[str, FeatureMeta]

# ============================================================
# Feature name generation
# ============================================================


def make_feature_name(
    base: str,
    kind: str,
    dtype: str,
    side: Optional[str] = None,
    *,
    extra_label: Optional[str] = None,
) -> str:
    """Create a feature name from its components."""
    # 1. Metadata special case
    if kind == "Metadata":
        # Human readable:
        #   "Metadata: Left Type = LogicError"
        return f"Metadata: {extra_label}"

    # 2. Original: "Task Common (Left Discrete)"
    if kind == "Original":
        return f"{base} ({side} {dtype})"

    # 3. Difference: "Task Common (Difference Discrete)"
    if kind == "Difference":
        return f"{base} (Difference {dtype})"

    # 4. Binary: "Task Common (Binary Left>Right Discrete)"
    if kind == "Binary":
        return f"{base} (Binary Left>Right {dtype})"

    # 5. Extreme: "Task Common (Extreme Left Max)"
    if kind == "Extreme":
        return f"{base} (Extreme {side} {extra_label})"

    raise ValueError(f"Unsupported feature kind: {kind}")


# ============================================================
# Feature builder
# ============================================================


def _create_original_features(
    df: pd.DataFrame,
    discrete_scores: pd.DataFrame,
    continuous_scores: pd.DataFrame,
    catalog: FeatureCatalog,
) -> None:
    def attach(score_table: pd.DataFrame, dtype: str):
        # Identify bases (all heuristic names stored in wide format)
        bases = [col for col in score_table.columns if col not in ("submission id", "defect id")]

        # ---- LEFT MERGE ----
        left_merge = df[["submission id", "left"]].merge(
            score_table, how="left", left_on=["submission id", "left"], right_on=["submission id", "defect id"]
        )

        # Drop lookup helper columns
        left_merge = left_merge.drop(columns=["defect id", "left"])

        # Rename base columns → e.g. "Task Common" → "Task Common (Left Discrete)"
        left_renamed = {base: f"{base} (Left {dtype})" for base in bases}
        left_merge = left_merge.rename(columns=left_renamed)

        # ---- RIGHT MERGE ----
        right_merge = df[["submission id", "right"]].merge(
            score_table, how="left", left_on=["submission id", "right"], right_on=["submission id", "defect id"]
        )

        right_merge = right_merge.drop(columns=["defect id", "right"])

        right_renamed = {base: f"{base} (Right {dtype})" for base in bases}
        right_merge = right_merge.rename(columns=right_renamed)

        # ---- COMBINE RESULTS ----
        # Only keep renamed heuristic columns (drop "submission id")
        new_cols = pd.concat([left_merge[left_renamed.values()], right_merge[right_renamed.values()]], axis=1)

        # Attach to main df all at once (prevents fragmentation)
        df[new_cols.columns] = new_cols

        # ---- REGISTER METADATA ----
        for base in bases:
            for side in ("Left", "Right"):
                col = f"{base} ({side} {dtype})"
                catalog[col] = FeatureMeta(
                    base=base,
                    kind="Original",
                    dtype=dtype,
                    side=side,
                    extra=None,
                    description=f"{base}: {side.lower()} side {dtype.lower()} value",
                )

    # Attach discrete and continuous separately
    attach(discrete_scores, "Discrete")
    attach(continuous_scores, "Continuous")


def _create_difference_features(df, catalog):
    new_cols = {}

    for col, meta in list(catalog.items()):
        if meta.kind == "Original" and meta.side == "Left":
            base = meta.base
            dtype = meta.dtype

            left = f"{base} (Left {dtype})"
            right = f"{base} (Right {dtype})"
            diff_col = f"{base} ({dtype} Diff)"

            if left in df.columns and right in df.columns:
                new_cols[diff_col] = df[left] - df[right]

                catalog[diff_col] = FeatureMeta(
                    base=base,
                    kind="Difference",
                    dtype=dtype,
                    side=None,
                    extra=None,
                    description=f"{base}: left minus right ({dtype.lower()})",
                )

    return pd.DataFrame(new_cols, index=df.index)


def _create_binary_features(df, catalog):
    new_cols = {}

    for col, meta in list(catalog.items()):
        if meta.kind == "Difference":
            base = meta.base
            dtype = meta.dtype

            binary_col = f"{base} ({dtype} Binary)"
            new_cols[binary_col] = (df[col] > 0).astype(int)

            catalog[binary_col] = FeatureMeta(
                base=base,
                kind="Binary",
                dtype="Binary",
                side=None,
                extra=None,
                description=f"{base}: 1 if left > right ({dtype.lower()})",
            )

    return pd.DataFrame(new_cols, index=df.index)


def _create_extreme_features(df, catalog):
    new_cols = {}

    for col, meta in list(catalog.items()):
        if meta.kind == "Original":
            base = meta.base
            dtype = meta.dtype
            side = meta.side

            extreme_col = f"{base} ({dtype} IsExtreme {side})"

            if side == "Left":
                values = df[col]
                new_cols[extreme_col] = ((values == values.max()) | (values == values.min())).astype(int)
                extra = {"min": values.min(), "max": values.max()}

            elif side == "Right":
                values = df[col]
                new_cols[extreme_col] = ((values == values.max()) | (values == values.min())).astype(int)
                extra = {"min": values.min(), "max": values.max()}

            else:
                continue  # should not occur

            catalog[extreme_col] = FeatureMeta(
                base=base,
                kind="Extreme",
                dtype="Binary",
                side=side,
                extra=extra,
                description=f"{base}: flag if {side.lower()} is global min/max ({dtype.lower()})",
            )

    return pd.DataFrame(new_cols, index=df.index)


def _create_metadata_features(df, items, defects, catalog):
    new_cols = {}

    left_type = defects["defect type"].loc[df["left"]].reset_index(drop=True)
    right_type = defects["defect type"].loc[df["right"]].reset_index(drop=True)
    item_topic = items["topic"].loc[df["item"]].reset_index(drop=True)

    all_defect_types = sorted(defects["defect type"].unique())
    all_topics = sorted(items["topic"].unique())

    # One-hot defect type (left)
    for t in all_defect_types:
        name = f"Metadata: Left Defect Type = {t}"
        new_cols[name] = (left_type == t).astype(int)
        catalog[name] = FeatureMeta(
            base="Metadata",
            kind="Metadata",
            dtype="Categorical",
            side="Left",
            extra={"value": t},
            description=f"Left defect type equals '{t}'",
        )

    # One-hot defect type (right)
    for t in all_defect_types:
        name = f"Metadata: Right Defect Type = {t}"
        new_cols[name] = (right_type == t).astype(int)
        catalog[name] = FeatureMeta(
            base="Metadata",
            kind="Metadata",
            dtype="Categorical",
            side="Right",
            extra={"value": t},
            description=f"Right defect type equals '{t}'",
        )

    # One-hot topic
    for t in all_topics:
        name = f"Metadata: Item Topic = {t}"
        new_cols[name] = (item_topic == t).astype(int)
        catalog[name] = FeatureMeta(
            base="metadata",
            kind="Metadata",
            dtype="Categorical",
            side=None,
            extra={"value": t},
            description=f"Item topic equals '{t}'",
        )

    return pd.DataFrame(new_cols, index=df.index)


def build_pairwise_features(
    pairs, discrete_scores, continuous_scores, items, defects
) -> Tuple[pd.DataFrame, FeatureCatalog]:
    """Build a dataframe of features for each pair of defects."""
    df = pairs.copy()
    catalog: FeatureCatalog = {}

    df = pd.concat([df, _create_original_features(df, discrete_scores, continuous_scores, catalog)], axis=1)
    df = pd.concat([df, _create_difference_features(df, catalog)], axis=1)
    df = pd.concat([df, _create_binary_features(df, catalog)], axis=1)
    df = pd.concat([df, _create_extreme_features(df, catalog)], axis=1)
    df = pd.concat([df, _create_metadata_features(df, items, defects, catalog)], axis=1)

    return df, catalog


# ==============================================================================
# Feature selection
# ==============================================================================


def select_features(catalog, base=None, kind=None, dtype=None, side=None) -> list[str]:
    """Return list of feature names matching all provided constraints."""
    return [
        col
        for col, meta in catalog.items()
        if (base is None or meta.base == base)
        and (kind is None or meta.kind == kind)
        and (dtype is None or meta.dtype == dtype)
        and (side is None or meta.side == side)
    ]
