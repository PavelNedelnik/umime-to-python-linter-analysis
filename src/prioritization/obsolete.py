"""This module contains prioritization models that for various reasons were retired from the experiment."""

from pathlib import Path

import pandas as pd

from src.prioritization.base import PrioritizationModel
from src.prioritization.task_models import TaskPrioritizationModel


class CurrentlyTaughtPrioritizer(TaskPrioritizationModel):
    """Prioritizes defects based on LLM judgements on where they relate to the currently taught concepts."""

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, data_path: Path | str, *args, **kwargs):
        """Initialize the model by loading LLM judgments from a file."""
        super().__init__(items, defects, *args, **kwargs)
        self.data_path = data_path
        self.task_weights = self._load_llm_judgments()

    def _load_llm_judgments(self) -> pd.DataFrame:
        """Load LLM data and prepare the task-weights matrix."""
        llm_data = pd.read_csv(self.data_path, sep="|", index_col=False)
        task_name_to_id = self.items.reset_index().set_index("name")["id"]
        llm_data["Task ID"] = llm_data["Task Name"].map(task_name_to_id)
        task_weights = pd.crosstab(llm_data["Task ID"], llm_data["Defect ID"]).astype(bool).astype(int)
        task_weights = task_weights.reindex(index=self.items.index, columns=self.defects.index, fill_value=0)
        return task_weights

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects based on pre-computed LLM weights."""
        task_id = submission["item"]
        if task_id not in self.task_weights.index:
            return pd.Series(0, index=defect_counts.index)
        llm_scores = self.task_weights.loc[task_id]
        return self._apply_scores(llm_scores, defect_counts)

    def update(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame) -> PrioritizationModel:
        """Update is a no-op as LLM judgments are static."""
        return self

    def reset_model(self) -> PrioritizationModel:
        """Reset the model's state by re-loading the judgments."""
        self.task_weights = self._load_llm_judgments()

        return self

    def get_measure_name(self) -> str:
        """Return a precise, short description of the model's output."""
        return "LLM Judgment (0 = No, 1 = Yes)"

    def get_measure_description(self) -> str:
        """Return a human readable description of the model output."""
        return "LLM Judgments on Currently Taught Concepts"

    def get_model_description(self) -> str:
        """Return a human-readable description of the model's logic."""
        return "Prioritizes defects based on static LLM judgments about 'currently taught' concepts."

    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed task-defect LLM weight matrix."""
        return self.task_weights
        return self.task_weights
