"""This module contains models that do not consider any student or task context."""

import numpy as np
import pandas as pd

from src.prioritization.base import PrioritizationModel


class SeverityModel(PrioritizationModel):
    """
    Prioritize defects based on their inherent severity.

    This is a stateless baseline model.
    """

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, *args, **kwargs):
        """Initialize the model with shared data."""
        super().__init__(items, defects, *args, **kwargs)
        self.severity_map = self.defects["severity"].reindex(self.defects.index)
        self.thresholds = np.array([1, 2, 3, 4, 5])

    def _calculate_scores(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects based on their severity."""
        return self.severity_map.reindex(defect_counts.index)

    def _calculate_thresholds(self):
        """Do nothing. The model has static thresholds."""
        pass

    def get_context_type(self) -> str:
        """Return the type of context the model uses."""
        return "stateless"

    def get_model_weights(self) -> pd.DataFrame:
        """Return a single-row matrix for consistency in analysis."""
        return self.severity_map.to_frame().T

    @classmethod
    def get_discretization_scale(cls):
        """Return the name of the model's discretization scale (e.g., '1-5')."""
        return "1-5"

    @classmethod
    def get_model_name(cls) -> str:  # noqa: D102
        return "Naive Severity"

    @classmethod
    def get_measure_name(cls) -> str:  # noqa: D102
        return "Severity from a Survey"

    @classmethod
    def get_model_description(cls) -> str:  # noqa: D102
        return "Context-free defect severity from a previous survey."

    @classmethod
    def get_model_interpretation(cls) -> str:  # noqa: D102
        return "Higher = more severe / critical to fix."
