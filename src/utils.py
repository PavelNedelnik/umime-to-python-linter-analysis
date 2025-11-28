"""Utility functions."""

import math
import warnings

import numpy as np
import pandas as pd


def split_users(log: pd.DataFrame, splits: list[float], seed: int = 0) -> list[pd.Series]:
    """
    Split the data, keeping submissions from the same user together.

    Args:
        log: A DataFrame of submissions.
        splits: A list of train, val, and test split proportions.
        seed: A random seed.

    Returns:
        A list of pd.Series masking users belonging to the corresponding split.
    """
    unassigned_users = np.sort(log["user"].unique())
    rng = np.random.default_rng(seed)
    unassigned_users = rng.permutation(unassigned_users)

    if sum(splits) < 1:
        warnings.warn("The sum of split proportions is less than 1. Some data will remain unassigned.")
    elif sum(splits) > 1:
        raise ValueError("Split proportions must sum to less than 1.")

    result = []
    # some users might be lost to rounding errors
    pivots = [int(len(unassigned_users) * split) for split in splits]
    for pivot in pivots:
        users, unassigned_users = unassigned_users[:pivot], unassigned_users[pivot:]
        split_mask = log["user"].isin(users).copy()

        result.append(split_mask)

    return result


def gini(array: np.ndarray) -> float:
    """Compute the Gini coefficient of a sorted numpy array."""
    array = array.flatten()
    # avoid zero division
    if array.sum() == 0:
        return 0.0
    # ensure all values are non-negative
    if np.amin(array) < 0:
        array -= np.amin(array)
    # order values for computation
    array = np.sort(array)
    index = np.arange(1, array.shape[0] + 1)
    # gini formula
    return (np.sum((2 * index - array.shape[0] - 1) * array)) / (array.shape[0] * np.sum(array))
