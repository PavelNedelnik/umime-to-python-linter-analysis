"""Discretization mixins."""

import numpy as np
import pandas as pd

PERCENTILES = [0.15, 0.30, 0.70, 0.85]
# number of submissions before the defect decreases in priority
# [never, over 10, 5-10, 2-5, 1-2]
STUDENT_ENCOUNTERED_DISCRETIZATION_THRESHOLDS = [1000.0, 10.0, 5.0, 2.0]
MIN_HURDLE = 1e-3


def _weighted_quantile(values, quantiles, weights=None):
    """
    Compute weighted quantiles.

    Source: https://stackoverflow.com/questions/21844024/weighted-percentile-using-numpy
    """
    sorter = np.argsort(values)
    values = values[sorter]
    weights = weights[sorter]

    cumulative = np.cumsum(weights) - 0.5 * weights
    total = np.sum(weights)

    percentile_positions = np.array(quantiles) * total
    return np.interp(percentile_positions, cumulative, values)


# ---------------------------------------------------------------------------
# Discretization mixins (provide thresholds + discretize adjustments)
# ---------------------------------------------------------------------------


class TrafficDiscretizationBase:
    """Computes thresholds using traffic-weighted percentiles with a minimum hurdle."""

    def _calculate_thresholds(self):
        values = self.get_model_weights().values.flatten()
        weights = self._get_count()

        # Remove zero frequency pairs
        values = values[weights > MIN_HURDLE]
        weights = weights[weights > MIN_HURDLE]
        if len(values) == 0:
            self.thresholds = np.array([])
            return

        # Calculate frequency-weighted percentiles
        self.thresholds = _weighted_quantile(values, PERCENTILES, weights)


class FrequencyDiscretizationMixin(TrafficDiscretizationBase):
    """Discretization mixin for frequency-based models."""

    def discretize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Discretize scores into levels 1-5 using the fixed thresholds."""
        return super().discretize(submission, defect_counts) + 1

    @classmethod
    def get_discretization_scale(cls) -> str:
        """Return the name of the model's discretization scale (e.g., '1-5')."""
        return "1-5"


class ZScoreDiscretizationMixin(TrafficDiscretizationBase):
    """Discretization mixin for Z-score-based models."""

    def discretize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Discretize scores into levels -2-2 using the learned thresholds."""
        return super().discretize(submission, defect_counts) - 2

    @classmethod
    def get_discretization_scale(cls) -> str:
        """Return the name of the model's discretization scale (e.g., '-2-2')."""
        return "-2-2"
