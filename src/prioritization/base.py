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
    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects for a single submission.

        Args:
            submission: A Series with information about a single submission - includes task id, user id, etc.
            defect_counts: A Series of the number of times each defect is present in the submission.
        Returns:
            A Series of priorities for each defect (Higher is more important, -1 indicates the defect is not present).
        """
        pass

    def update(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame):
        """
        Update the model's internal state with a batch of new submissions.

        This method does nothing for stateless models.
        """
        pass

    def reset_model(self):
        """Reset the model's internal state to its initial configuration."""
        pass

    def _apply_scores(self, scores: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Apply scores to defects, filtering out those not present in the submission."""
        scores = scores.loc[defect_counts.index]  # Align scores and counts
        scores[scores < 0] = 0  # Avoid negative priorities for present defects
        scores[defect_counts <= 0] = -1  # Missing defects get negative priority
        return scores

    def _handle_update_input(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame):
        if isinstance(submissions, pd.Series):
            submissions = pd.DataFrame([submissions])
            defect_counts = pd.DataFrame([defect_counts])

        return submissions, defect_counts

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
