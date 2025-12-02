"""Contains functions used to add features to the pairwise benchmark dataset."""

import pandas as pd


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
