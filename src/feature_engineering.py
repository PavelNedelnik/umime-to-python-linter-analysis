"""Contains functions used to add features to the pairwise benchmark dataset."""

import pandas as pd
from sklearn.preprocessing import OneHotEncoder


def remove_suffix(col: str) -> str:
    """
    Return base name before the first ' (' occurrence; fall back to original.

    Util to simplify organizing feature sets.
    """
    if not isinstance(col, str):
        return col
    idx = col.find(" (")
    return col[:idx] if idx != -1 else col


def add_feature_sets(
    pairwise_df_with_scores: pd.DataFrame, items: pd.DataFrame, defects: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    """
    Add feature sets to a dataframe.

    Arguments:
        pairwise_df_with_scores (pd.DataFrame): DataFrame with pairwise data, heuristic scores, and metadata.
        items (pd.DataFrame): DataFrame with items.
        defects (pd.DataFrame): DataFrame with defects.

    Returns:
        pd.DataFrame: DataFrame with feature sets.
        dict: Dictionary of feature groups.
    """
    left_discrete_features = [col for col in pairwise_df_with_scores.columns if col.endswith("(Left Discrete)")]
    right_discrete_features = [col for col in pairwise_df_with_scores.columns if col.endswith("(Right Discrete)")]
    left_continuous_features = [col for col in pairwise_df_with_scores.columns if col.endswith("(Left Continuous)")]
    right_continuous_features = [col for col in pairwise_df_with_scores.columns if col.endswith("(Right Continuous)")]

    left_discrete_values = pairwise_df_with_scores[left_discrete_features].rename(columns=remove_suffix)
    right_discrete_values = pairwise_df_with_scores[right_discrete_features].rename(columns=remove_suffix)
    left_continuous_values = pairwise_df_with_scores[left_continuous_features].rename(columns=remove_suffix)
    right_continuous_values = pairwise_df_with_scores[right_continuous_features].rename(columns=remove_suffix)

    discrete_diff, continuous_diff = _calculate_difference_features(
        left_discrete_values, right_discrete_values, left_continuous_values, right_continuous_values
    )

    discrete_is_larger, continuous_is_larger, left_is_extreme_max, left_is_extreme_min = _calculate_binary_flags(
        left_discrete_values, right_discrete_values, left_continuous_values, right_continuous_values
    )

    metadata = _calculate_metadata_features(pairwise_df_with_scores, items, defects)

    engineered_df = pd.concat(
        [
            pairwise_df_with_scores[left_discrete_features],
            pairwise_df_with_scores[right_discrete_features],
            discrete_diff,
            pairwise_df_with_scores[left_continuous_features],
            pairwise_df_with_scores[right_continuous_features],
            continuous_diff,
            discrete_is_larger,
            continuous_is_larger,
            left_is_extreme_max,
            left_is_extreme_min,
            metadata,
        ],
        axis=1,
    )

    feature_groups = {
        "Left Discrete": left_discrete_features,
        "Right Discrete": right_discrete_features,
        "Discrete Diff": discrete_diff.columns.tolist(),
        "Left+Right Continuous": left_continuous_features + right_continuous_features,
        "Continuous Diff": continuous_diff.columns.tolist(),
        "Derived Rules": discrete_is_larger.columns.tolist() + continuous_is_larger.columns.tolist(),
        "Additional Rules": left_is_extreme_max.columns.tolist() + left_is_extreme_min.columns.tolist(),
        "Metadata": metadata.columns.tolist(),
        "All Features": engineered_df.columns.tolist(),
    }

    return engineered_df, feature_groups


def _calculate_metadata_features(
    pairwise_df_with_scores: pd.DataFrame,
    items: pd.DataFrame,
    defects: pd.DataFrame,
):
    left_type = defects["defect type"].loc[pairwise_df_with_scores["left"]].reset_index(drop=True).rename("left")
    right_type = defects["defect type"].loc[pairwise_df_with_scores["right"]].reset_index(drop=True).rename("right")

    item_topic = items["topic"].loc[pairwise_df_with_scores["item"]].reset_index(drop=True).rename("item")

    all_defect_types = defects["defect type"].unique()
    all_item_topics = items["topic"].unique()
    metadata_encoder = OneHotEncoder(categories=[all_defect_types, all_defect_types, all_item_topics])
    metadata = metadata_encoder.fit_transform(pd.concat([left_type, right_type, item_topic], axis=1))

    metadata = pd.DataFrame(metadata.toarray(), columns=metadata_encoder.get_feature_names_out())

    return metadata


def _calculate_binary_flags(
    left_discrete_values: pd.DataFrame,
    right_discrete_values: pd.DataFrame,
    left_continuous_values: pd.DataFrame,
    right_continuous_values: pd.DataFrame,
):
    discrete_is_larger = left_discrete_values > right_discrete_values
    discrete_is_larger = discrete_is_larger.add_suffix(" (Discrete >)")

    continuous_is_larger = left_continuous_values > right_continuous_values
    continuous_is_larger = continuous_is_larger.add_suffix(" (Continuous >)")

    left_is_extreme_max = left_discrete_values == 5
    left_is_extreme_max = left_is_extreme_max.add_suffix(" (Left Max)")
    left_is_extreme_min = left_discrete_values == 1
    left_is_extreme_min = left_is_extreme_min.add_suffix(" (Left Min)")

    return discrete_is_larger, continuous_is_larger, left_is_extreme_max, left_is_extreme_min


def _calculate_difference_features(
    left_discrete_values: pd.DataFrame,
    right_discrete_values: pd.DataFrame,
    left_continuous_values: pd.DataFrame,
    right_continuous_values: pd.DataFrame,
):
    discrete_diff = left_discrete_values - right_discrete_values
    discrete_diff = discrete_diff.add_suffix(" (Discrete Diff)")

    continuous_diff = left_continuous_values - right_continuous_values
    continuous_diff = continuous_diff.add_suffix(" (Continuous Diff)")

    return discrete_diff, continuous_diff


def add_heuristic_scores(
    defect_pairs: pd.DataFrame, discrete_features: pd.DataFrame, continuous_features: pd.DataFrame
):
    """Add heuristic scores to a dataframe.

    Arguments:
        defect_pairs (pd.DataFrame): DataFrame with defect pairs.
        discrete_features (pd.DataFrame): DataFrame with discrete heuristic scores.
        continuous_features (pd.DataFrame): DataFrame with continuous heuristic scores.

    Returns:
        Pairwise dataframe with correctly suffixed heuristic scores.
    """
    return pd.concat(
        [
            defect_pairs,
            _add_scores(defect_pairs, discrete_features, "left", " (Left Discrete)"),
            _add_scores(defect_pairs, discrete_features, "right", " (Right Discrete)"),
            _add_scores(defect_pairs, continuous_features, "left", " (Left Continuous)"),
            _add_scores(defect_pairs, continuous_features, "right", " (Right Continuous)"),
        ],
        axis=1,
    )


def _add_scores(defect_pairs: pd.DataFrame, scores: pd.DataFrame, which: str = "left", suffix: str = ""):
    """
    Add correctly suffixed heuristic scores to a dataframe.

    Args:
        defect_pairs (pd.DataFrame): DataFrame with defect pairs.
        scores (pd.DataFrame): DataFrame with heuristic scores.
        which (str): Which defect to use.
        suffix (str): Suffix to add to column names.
    Returns:
        pd.DataFrame: DataFrame with heuristic scores.
    """
    if which not in defect_pairs.columns:
        raise ValueError(f"Column '{which}' not found in defect pairs.")
    return (
        defect_pairs[["submission id", which]]
        .merge(scores, left_on=["submission id", which], right_on=["submission id", "defect id"], how="left")
        .drop(columns=["defect id", "submission id", which])
        .add_suffix(suffix)
    )
