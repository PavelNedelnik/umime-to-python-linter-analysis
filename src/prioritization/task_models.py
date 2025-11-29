"""
This module contains prioritization models that focus purely on task context.

These models calculate a weight matrix where rows are tasks and columns are defects.
"""

import numpy as np
import pandas as pd

from src.prioritization.base import PrioritizationModel, TaskContextMixin
from src.prioritization.discretization import FrequencyDiscretizationMixin, ZScoreDiscretizationMixin
from src.prioritization.utils import combine_stats


class TaskFrequencyBase(TaskContextMixin, PrioritizationModel):
    """Base class for models that count task submissions and defect frequencies."""

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, *args, **kwargs):
        """Initialize the model with empty tracking structures."""
        super().__init__(items, defects, *args, **kwargs)
        self.n_samples = pd.Series(0, index=self.items.index, dtype=int)
        self.task_defect_freqs = pd.DataFrame(0, index=self.items.index, columns=self.defects.index, dtype=float)

    def _get_count(self) -> np.array:
        """Return the count of each task-defect pair for traffic weights."""
        return self.task_defect_freqs.values.flatten()

    def _update_weights(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame):
        """Update counts for each task and defect."""
        old_total = self.task_defect_freqs.multiply(self.n_samples, axis=0)
        new_samples = submissions["item"].value_counts().reindex(self.items.index, fill_value=0)
        new_total = (defect_counts > 0).groupby(submissions["item"]).mean()
        new_total = new_total.multiply(new_samples, axis=0).fillna(0)

        self.n_samples += new_samples
        self.task_defect_freqs = (old_total + new_total).divide(self.n_samples.replace(0, 1), axis=0)

    def reset_model(self) -> PrioritizationModel:
        """Reset the internal tracking structures."""
        self.n_samples = pd.Series(0, index=self.items.index, dtype=int)
        self.task_defect_freqs = pd.DataFrame(0, index=self.items.index, columns=self.defects.index, dtype=float)
        return self

    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed task-defect frequency matrix."""
        return self.task_defect_freqs


class TaskCommonModel(FrequencyDiscretizationMixin, TaskFrequencyBase):
    """Prioritize defects based on how common they are for a given task."""

    def _calculate_scores(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        return self.task_defect_freqs.loc[submission["item"]]

    def reset_model(self) -> PrioritizationModel:
        """Reset the model's internal state to its initial configuration."""
        self.n_samples = pd.Series(0, index=self.items.index, dtype=float)
        self.task_defect_freqs = pd.DataFrame(0, index=self.items.index, columns=self.defects.index, dtype=float)

        return self

    @classmethod
    def get_model_name(cls) -> str:  # noqa: D102
        return "Task Common"

    @classmethod
    def get_measure_name(cls) -> str:  # noqa: D102
        return "Task-Specific Frequency"

    @classmethod
    def get_model_description(cls) -> str:  # noqa: D102
        return "Defects commonly seen on this task."

    @classmethod
    def get_model_interpretation(cls) -> str:  # noqa: D102
        return "Higher = more students introduce this defect."


class TaskCharacteristicModel(ZScoreDiscretizationMixin, TaskFrequencyBase):
    """Prioritizes defects that are unusually common for a given task."""

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, *args, **kwargs):
        """Initialize the model with shared data."""
        super().__init__(items, defects, *args, **kwargs)
        self.global_samples = pd.Series(0, index=self.defects.index, dtype=int)
        self.global_mean = pd.Series(0, index=self.defects.index, dtype=int)
        self.global_var = pd.Series(0, index=self.defects.index, dtype=int)

        self.task_z_scores = pd.DataFrame(0, index=self.items.index, columns=self.defects.index, dtype=float)

    def _calculate_scores(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        return self.task_z_scores.loc[submission["item"]]

    def _update_weights(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame) -> PrioritizationModel:
        """Update the model's state with a batch of new submissions."""
        TaskFrequencyBase._update_weights(self, submissions, defect_counts)

        presence = (defect_counts > 0).astype(int)

        new_mean = presence.mean()
        new_var = presence.var(ddof=0, skipna=True).fillna(0)

        self.global_samples, self.global_mean, self.global_var = combine_stats(
            presence.shape[0], new_mean, new_var, self.global_samples, self.global_mean, self.global_var
        )

        self.task_z_scores = (self.task_defect_freqs - self.global_mean) / self.global_var.pow(0.5).replace(0, 1)

    def reset_model(self) -> PrioritizationModel:
        """Reset the model's internal state to its initial configuration."""
        super().reset_model()
        self.global_samples = pd.Series(0, index=self.defects.index, dtype=int)
        self.global_mean = pd.Series(0, index=self.defects.index, dtype=int)
        self.global_var = pd.Series(0, index=self.defects.index, dtype=int)

        self.task_z_scores = pd.DataFrame(0, index=self.items.index, columns=self.defects.index, dtype=float)

        return self

    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed task-defect z-score matrix."""
        return self.task_z_scores

    @classmethod
    def get_model_name(cls) -> str:  # noqa: D102
        return "Task Characteristic"

    @classmethod
    def get_measure_name(cls) -> str:  # noqa: D102
        return "Task-Specific Z-Score"

    @classmethod
    def get_model_description(cls) -> str:  # noqa: D102
        return "Defects uniquely common on this task."

    @classmethod
    def get_model_interpretation(cls) -> str:  # noqa: D102
        return "Higher = more distinctive to this task."
