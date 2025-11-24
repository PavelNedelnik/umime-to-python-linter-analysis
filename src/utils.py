"""Utility functions."""

import math

import numpy as np
import pandas as pd


def split_users(
    log: pd.DataFrame, train_pct: float = 0.8, val_pct: float = 0.0, test_pct: float = 0.2, seed: int = 0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Split the data into train and test sets, keeping submissions from the same user together.

    Expects log and defect log to share index.
    Args:
        log: A DataFrame of submissions.
        train_pct: The percentage of data to use for training.
        val_pct: The percentage of data to use for validation.
        test_pct: The percentage of data to use for testing.

    Returns:
        A tuple of pd.Series masking train, val, and test data.
    """
    all_users = np.sort(log["user"].unique())
    rng = np.random.default_rng(seed)
    all_users = rng.permutation(all_users)

    train_pivot = int(len(all_users) * train_pct)
    train_users = all_users[:train_pivot]
    train_mask = log["user"].isin(train_users).copy()

    val_pivot = int(len(all_users) * (train_pct + val_pct))
    val_users = all_users[train_pivot:val_pivot]
    val_mask = log["user"].isin(val_users).copy()

    test_pivot = int(len(all_users) * (train_pct + val_pct + test_pct))
    test_users = all_users[val_pivot:test_pivot]
    test_mask = log["user"].isin(test_users).copy()

    return train_mask, val_mask, test_mask


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
