"""
This module contains the foundational classes for the prioritization system.

It defines the core interfaces, including the `PrioritizationModel` base class.
It handles common utilities like model saving and loading, ensuring all models
have a consistent, reliable interface.
"""

import pickle as pkl
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import softmax


class PrioritizationModel(ABC):
    """
    Provide a unified base for all prioritization models.

    All models must conform to this consistent, robust interface.
    """

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, *args, **kwargs):
        """
        Initialize the model and store canonical data.

        Args:
            items: A DataFrame of all tasks/items in the universe.
            defects: A DataFrame of all possible defects.
        """
        self.items = items
        self.defects = defects

    @abstractmethod
    def _calculate_scores(self, submission: pd.Series, defect_counts: pd.Series):
        """Calculate prioritiy scores for a single submission.

        Args:
            submission: A Series with information about a single submission - includes task id, user id, etc.
            defect_counts: A Series of the number of times each defect is present in the submission.
        Returns:
            A Series of scores for each defect. The returned Series should have the same index as `defects`.
        """
        raise NotImplementedError

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects for a single submission.

        Args:
            submission: A Series with information about a single submission - includes task id, user id, etc.
            defect_counts: A Series of the number of times each defect is present in the submission.
        Returns:
            A Series of priorities for each defect (Higher is more important, -1 indicates the defect is not present).
        """
        scores = self._calculate_scores(submission, defect_counts).loc[defect_counts > 0]
        if scores.empty:
            return pd.Series(0, index=self.defects.index, dtype=float)
        scaled_scores = pd.Series(softmax(scores), index=scores.index)
        return scaled_scores.reindex(self.defects.index, fill_value=0.0)

    def _update_weights(self, submissions: pd.DataFrame, weights: pd.DataFrame):
        """Update the model's internal state with a batch of new submissions."""
        pass

    def update(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame):
        """
        Update the model's internal state with a batch of new submissions.

        This method does nothing for stateless models.
        """
        if isinstance(submissions, pd.Series):
            submissions = pd.DataFrame([submissions])
            defect_counts = pd.DataFrame([defect_counts])

        self._update_weights(submissions, defect_counts)

        return self

    def reset_model(self):
        """Reset the model's internal state to its initial configuration."""
        return self

    # --- Introspection Methods ---
    def get_context_type(self) -> str:
        """Return the type of context the model uses: 'stateless', 'task', or 'student'."""
        return "stateless"

    @abstractmethod
    def get_model_description(self) -> str:
        """Return a human-readable description of the model's logic."""
        pass

    @abstractmethod
    def get_measure_name(self) -> str:
        """Return a short, descriptive name of the model's measure (e.g., 'Frequency')."""
        pass

    @abstractmethod
    def get_measure_description(self) -> str:
        """Return a human readable description of the model output (e.g. 'Commonality')."""
        pass

    def get_model_weights(self) -> pd.DataFrame:
        """Return the model's pre-computed weight matrix for analysis."""
        return None

    # --- Save/Load Functionality ---
    def save(self, path: Path | str):
        """Save the model's state to a file using pickle."""
        path = Path(path)
        with open(path, "wb") as f:
            pkl.dump(self, f)

    @classmethod
    def load(cls, path: Path | str):
        """Load a trained model from a file using pickle."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found at {path}")
        with open(path, "rb") as f:
            obj = pkl.load(f)
        if not isinstance(obj, cls):
            raise TypeError(f"Pickle does not contain a valid {cls.__name__} instance.")
        return obj
