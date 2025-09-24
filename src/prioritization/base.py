"""
This module contains the foundational classes for the prioritization system.

It defines the core interfaces, including the `PrioritizationModel` base class and
the `ContextProvider` for data access. It handles common utilities like
model saving and loading, ensuring all models have a consistent, reliable
interface.
"""

import pickle as pkl
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
import pandas as pd


class ContextProvider:
    """Provides contextual data while keeping logs separate."""

    def __init__(self, log: pd.DataFrame, defect_log: pd.DataFrame, defects: pd.DataFrame, items: pd.DataFrame):
        """Initialize the ContextProvider with logs and defects."""
        self._log = log
        self._defect_log = defect_log
        self.defects = defects
        self.items = items
        self.users = self._log["user"].unique()

    def get_log(self) -> pd.DataFrame:
        """Return the main submission log."""
        return self._log

    def get_defect_log(self) -> pd.DataFrame:
        """Return the matrix of detected defects."""
        return self._defect_log

    def get_user_defect_frequency(self, normalized=True) -> pd.DataFrame:
        """Calculate a student's defect frequency from separate logs."""
        user_defect_counts = self._defect_log.groupby(self._log["user"]).sum()
        if normalized:
            user_opportunities = self._log.groupby("user").size()
            return user_defect_counts.divide(user_opportunities, axis=0).fillna(0)
        return user_defect_counts

    def get_sorted_user_log_and_defects(self) -> dict:
        """Return a dictionary of chronologically sorted logs and defects for each user."""
        sorted_user_data = {}
        for user_id, user_log_data in self._log.groupby("user"):
            sorted_log = user_log_data.sort_values("time")
            sorted_defect_log = self._defect_log.loc[sorted_log.index]
            sorted_user_data[user_id] = (sorted_log, sorted_defect_log)
        return sorted_user_data

    def get_global_defect_multiplicity_stats(self) -> tuple[pd.Series, pd.Series]:
        """Calculate global mean and std for defect counts."""
        defect_counts = self._defect_log.sum(axis=0)
        return defect_counts.mean(), defect_counts.std()


class PrioritizationModel:
    """Base class for context-aware prioritization models."""

    def train(self, context_provider: ContextProvider):
        """Train the model with a given ContextProvider."""
        self.context_provider = context_provider
        self.is_trained = True
        return self

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects for a new submission."""
        raise NotImplementedError("Subclasses must implement the prioritize method.")

    def __call__(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects for a new submission."""
        return self.prioritize(submission, defect_counts)

    def save(self, path: Path | str):
        """Save the trained model to a file."""
        path = Path(path)
        with open(path, "wb") as f:
            pkl.dump(self, f)

    @classmethod
    def load(cls, path: Path | str):
        """Load a trained model from a file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found at {path}")
        with open(path, "rb") as f:
            obj = pkl.load(f)
        if not isinstance(obj, cls):
            raise TypeError(f"Pickle does not contain a valid {cls.__name__} instance.")
        return obj

    def _apply_scores(self, scores: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Apply scores to defects."""
        defect_presence = (defect_counts > 0).astype(int)
        priorities = scores.loc[defect_presence.index] * defect_presence
        return priorities

    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed weight matrix for analysis."""
        return None
