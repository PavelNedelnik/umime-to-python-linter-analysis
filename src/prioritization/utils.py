"""Utility functions."""

from copy import deepcopy

import pandas as pd


def combine_stats(
    new_samples: pd.Series,
    new_mean: pd.Series,
    new_var: pd.Series,
    old_samples: pd.Series,
    old_mean: pd.Series,
    old_var: pd.Series,
):
    """Combine number of samples, means and variances of two batches of data.

    https://notmatthancock.github.io/2017/03/23/simple-batch-stat-updates.html
    """
    combined_samples = (new_samples + old_samples).replace(0, 1)
    combined_mean = (new_samples * new_mean + old_samples * old_mean) / combined_samples
    combined_var = (
        old_samples * old_var
        + new_samples * new_var
        + old_samples * new_samples / combined_samples * (new_mean - old_mean) ** 2
    ) / combined_samples

    return combined_samples, combined_mean, combined_var


class DefaultDictFactory:
    """
    A callable factory for use with <collections.defaultdict> that consistently returns a given default value.

    Might be used over <lamda> for compatibility with <pickle>.
    """

    def __init__(self, default_value):
        """Initialize the factory."""
        self.default_value = default_value

    def __call__(self):
        """Return the default value."""
        return deepcopy(self.default_value)
