"""
This module contains prioritization models that focus purely on task context.

These models calculate a weight matrix where rows are tasks and columns are defects.
"""

from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import zscore

from .base import ContextProvider, PrioritizationModel


class TaskPrioritizationModel(PrioritizationModel, ABC):
    """Base class for task-pure prioritization models.

    All models that inherit from this class must implement the `get_model_weights`
    method, which returns the pre-computed weights from the `train` method.
    """

    @abstractmethod
    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed task-defect weight matrix."""
        pass


class TaskCommonModel(TaskPrioritizationModel):
    """Prioritizes defects based on how common they are for a given task."""

    def train(self, context_provider: ContextProvider):
        """Train the model."""
        super().train(context_provider)
        log = self.context_provider.get_log()
        defect_log = self.context_provider.get_defect_log()
        self.task_frequencies = (defect_log > 0).groupby(log["item"]).mean()
        return self

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        task_id = submission["item"]
        if task_id not in self.task_frequencies.index:
            raise ValueError(f"Unknown task {task_id}")

        commonality_scores = self.task_frequencies.loc[task_id]
        return self._apply_scores(commonality_scores, defect_counts)

    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed task-defect frequency matrix."""
        return self.task_frequencies


class TaskCharacteristicModel(TaskPrioritizationModel):
    """Prioritizes defects that are unusually common for a given task."""

    def train(self, context_provider: ContextProvider):
        """Train the model."""
        super().train(context_provider)
        log = self.context_provider.get_log()
        defect_log = self.context_provider.get_defect_log()
        task_freqs = (defect_log > 0).groupby(log["item"]).mean()
        self.task_z_scores = task_freqs.apply(lambda col: zscore(col, nan_policy="omit"))
        return self

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        task_id = submission["item"]
        if task_id not in self.task_z_scores.index:
            raise ValueError(f"Unknown task {task_id}")

        priorities = self.task_z_scores.loc[task_id]
        return self._apply_scores(priorities.abs().fillna(0), defect_counts)

    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed task-defect z-score matrix."""
        return self.task_z_scores


class CurrentlyTaughtPrioritizer(TaskPrioritizationModel):
    """Prioritizes defects based on LLM judgements on where they relate to the currently taught concepts."""

    def __init__(self, data_path: Path | str, *args, **kwargs):
        """Initialize the model by loading LLM judgments from a file."""
        super().__init__(*args, **kwargs)
        self.data_path = data_path

    def train(self, context_provider: ContextProvider):
        """Train the model by preparing the LLM judgments."""
        super().train(context_provider)

        llm_data = pd.read_csv(self.data_path, sep="|", index_col=False)

        items = context_provider.items
        defects = context_provider.defects

        task_name_to_id = items.reset_index().set_index("name")["id"]
        llm_data["Task ID"] = llm_data["Task Name"].map(task_name_to_id)

        self.task_weights = pd.crosstab(llm_data["Task ID"], llm_data["Defect ID"]).astype(bool).astype(int)

        self.task_weights = self.task_weights.reindex(index=items.index, columns=defects.index, fill_value=0)

        return self

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects based on pre-computed LLM weights."""
        task_id = submission["item"]

        if task_id not in self.task_weights.index:
            raise ValueError(f"Unknown task {task_id}")

        llm_scores = self.task_weights.loc[task_id]
        return self._apply_scores(llm_scores, defect_counts)

    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed task-defect LLM weight matrix."""
        return self.task_weights
