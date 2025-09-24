"""This module contains models that do not consider any student or task context."""

import pandas as pd

from src.prioritization.base import ContextProvider, PrioritizationModel


class SeverityModel(PrioritizationModel):
    """Prioritizes defects based on their inherent severity."""

    def train(self, context_provider: ContextProvider):
        """Train the model."""
        super().train(context_provider)
        self.severity_map = self.context_provider.defects["severity"]
        return self

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        return self._apply_scores(self.severity_map, defect_counts)

    def get_model_weights(self) -> pd.DataFrame:
        """Return None. The model has no contextual weights."""
        return None
