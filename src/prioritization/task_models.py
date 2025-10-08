"""
This module contains prioritization models that focus purely on task context.

These models calculate a weight matrix where rows are tasks and columns are defects.
"""

from abc import ABC
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import zscore

from src.prioritization.base import PrioritizationModel


class TaskPrioritizationModel(PrioritizationModel, ABC):
    """
    Provide a base class for models that prioritize based on task context.

    These models calculate a weight matrix where rows are tasks and columns are defects.
    """

    def get_context_type(self) -> str:
        """Return the type of context the model uses."""
        return "task"


class TaskCommonModel(TaskPrioritizationModel):
    """Prioritize defects based on how common they are for a given task."""

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, *args, **kwargs):
        """Initialize the model with shared data."""
        super().__init__(items, defects, *args, **kwargs)
        self.task_frequencies = pd.DataFrame(columns=self.defects.index, dtype=float)

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        task_id = submission["item"]
        if task_id not in self.task_frequencies.index:
            return pd.Series(0, index=defect_counts.index)

        commonality_scores = self.task_frequencies.loc[task_id]
        return self._apply_scores(commonality_scores, defect_counts)

    def update(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame) -> PrioritizationModel:
        """Update the model's state with a batch of new submissions."""
        submissions, defect_counts = self._handle_update_input(submissions, defect_counts)

        task_freqs = (defect_counts > 0).groupby(submissions["item"]).mean()
        self.task_frequencies = self.task_frequencies.add(task_freqs, fill_value=0)

        return self

    def reset_model(self) -> PrioritizationModel:
        """Reset the model's internal state to its initial configuration."""
        self.task_frequencies = pd.DataFrame(columns=self.defects.index, dtype=float)

        return self

    def get_measure_name(self) -> str:
        """Return a precise, short description of the model's output."""
        return "Relative Frequency"

    def get_measure_description(self) -> str:
        """Return a human readable description of the model output."""
        return "Task-Defect Commonality"

    def get_model_description(self) -> str:
        """Return a human-readable description of the model's logic."""
        return "Prioritizes defects based on their average frequency in a task."

    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed task-defect frequency matrix."""
        return self.task_frequencies


class TaskCharacteristicModel(TaskPrioritizationModel):
    """Prioritizes defects that are unusually common for a given task."""

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, *args, **kwargs):
        """Initialize the model with shared data."""
        super().__init__(items, defects, *args, **kwargs)
        self.task_freqs = pd.DataFrame(columns=self.defects.index, dtype=float)
        self.task_z_scores = pd.DataFrame(columns=self.defects.index)

    def _calculate_stats(self):
        """Calculate z-scores for all task frequencies."""
        self.task_z_scores = self.task_freqs.apply(lambda col: zscore(col, nan_policy="omit")).fillna(0)

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        task_id = submission["item"]
        if task_id not in self.task_z_scores.index:
            return pd.Series(0, index=defect_counts.index)

        priorities = self.task_z_scores.loc[task_id]
        return self._apply_scores(priorities.abs().fillna(0), defect_counts)

    def update(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame) -> PrioritizationModel:
        """Update the model's state with a batch of new submissions."""
        submissions, defect_counts = self._handle_update_input(submissions, defect_counts)

        if isinstance(submissions, pd.Series):
            submissions = pd.DataFrame([submissions])
            defect_counts = pd.DataFrame([defect_counts])

        task_freqs_new = (defect_counts > 0).groupby(submissions["item"]).mean()
        self.task_freqs = self.task_freqs.add(task_freqs_new, fill_value=0)
        self._calculate_stats()

        return self

    def reset_model(self) -> PrioritizationModel:
        """Reset the model's internal state to its initial configuration."""
        self.task_freqs = pd.DataFrame(columns=self.defects.index, dtype=float)
        self.task_z_scores = pd.DataFrame(columns=self.defects.index)

        return self

    def get_measure_name(self) -> str:
        """Return a precise, short description of the model's output."""
        return "Z-Score"

    def get_measure_description(self) -> str:
        """Return a human readable description of the model output."""
        return "Characteristic Task-Defect Scores"

    def get_model_description(self) -> str:
        """Return a human-readable description of the model's logic."""
        return "Prioritizes defects by their z-score (unusualness) within a task."

    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed task-defect z-score matrix."""
        return self.task_z_scores
