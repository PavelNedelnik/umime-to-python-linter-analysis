"""Utility functions."""

import numpy as np


def split_data_by_users(log, defect_log, pct=0.8):
    """
    Split the data into train and test sets, keeping submissions from the same user together.

    Expects log and defect log to share index.
    """
    all_users = log["user"].unique()
    np.random.seed(0)
    np.random.shuffle(all_users)

    train_users = all_users[: int(len(all_users) * pct)]
    mask = log["user"].isin(train_users)

    return log[mask], log[~mask], defect_log[mask], defect_log[~mask]


def gini(array):
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
