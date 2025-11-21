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
        self.thresholds = np.array([])

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

    # --- Prioritization ---
    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects for a single submission.

        Args:
            submission: A Series with information about a single submission - includes task id, user id, etc.
            defect_counts: A Series of the number of times each defect is present in the submission.
        Returns:
            A Series of priorities for each defect (Higher is more important, 0 indicates the defect should not be explained to the student).
        """
        present = defect_counts > 0
        if not present.any():
            return pd.Series(0, index=self.defects.index, dtype=float)

        scores = self._calculate_scores(submission, defect_counts).loc[present]
        scaled_scores = pd.Series(softmax(scores), index=scores.index)
        return scaled_scores.reindex(self.defects.index, fill_value=0.0)

    # --- Discretization ---
    def discretize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Return discretized priority labels for a single submission.

        Args:
            submission: A Series with information about a single submission - includes task id, user id, etc.
            defect_counts: A Series of the number of times each defect is present in the submission.
        Returns:
            A Series of discretized priority labels for each defect ().
        """
        present = defect_counts > 0
        if not present.any():
            return pd.Series(0, index=self.defects.index, dtype=float)

        scores = self._calculate_scores(submission, defect_counts).loc[present]
        levels = pd.Series(np.digitize(scores.values, self.thresholds), index=scores.index)
        return levels.reindex(self.defects.index)

    # --- Model Training Methods ---
    def _update_weights(self, submissions: pd.DataFrame, weights: pd.DataFrame):
        """Update the model's internal state with a batch of new submissions."""
        pass

    @abstractmethod
    def _calculate_thresholds(self):
        """Calculate and store discretization thresholds based on the distribution of model weights."""
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

        self._calculate_thresholds()

        return self

    def reset_model(self):
        """Reset the model's internal state to its initial configuration."""
        self.thresholds = np.array([])
        return self

    # --- Model Metadata ---
    @classmethod
    @abstractmethod
    def get_context_type(cls) -> str:
        """Return the type of context the model uses: 'stateless', 'task', or 'student'."""
        pass

    @classmethod
    @abstractmethod
    def get_discretization_scale(cls) -> str:
        """Return the name of the model's discretization scale (e.g., '1-5')."""
        pass

    @classmethod
    @abstractmethod
    def get_model_name(cls) -> str:
        """
        Return a user-friendly name for the model (e.g., 'Student Commonality').

        Should correspond to how the model is named in the accompanying thesis.
        """
        pass

    @classmethod
    @abstractmethod
    def get_measure_name(cls) -> str:
        """
        Return a short, descriptive name of what the model measures (e.g., 'Student-Specific Frequency').

        Might be used for example to label a histogram of model scores.
        """
        pass

    @classmethod
    @abstractmethod
    def get_model_description(cls) -> str:
        """
        Return a user-friendly intuitive justification for the model.

        Will be used to present the model to educators as part of the teacher survey.
        """
        pass

    @classmethod
    @abstractmethod
    def get_model_interpretation(cls) -> str:
        """
        Return a user-friendly explanation of how the priorities should be interpreted.

        Will be used to present the model to educators as part of the teacher survey.
        """
        pass

    # --- Introspection Methods ---
    def get_model_weights(self) -> pd.DataFrame:
        """Return the model's pre-computed weight matrix for analysis."""
        return None

    def get_model_thresholds(self) -> np.array:
        """Return the model's pre-computed discretization thresholds for analysis."""
        return self.thresholds

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


class StudentPrioritizationModel(PrioritizationModel, ABC):
    """
    Provide a base for all student-pure prioritization models.

    These models have a bulk `update` method for learning and
    must return a student-defect weight matrix.
    """

    def get_context_type(self) -> str:
        """Return the type of context the model uses."""
        return "student"


class TaskPrioritizationModel(PrioritizationModel, ABC):
    """
    Provide a base class for models that prioritize based on task context.

    These models calculate a weight matrix where rows are tasks and columns are defects.
    """

    def get_context_type(self) -> str:
        """Return the type of context the model uses."""
        return "task"


class FrequencyBasedModel(PrioritizationModel, ABC):
    """Base class for models using frequency-like scores (0 to 1, skewed)."""

    def _calculate_thresholds(self):
        """Set fixed threshold boundaries for the 1 to 5 scale."""
        self.thresholds = np.array([0.05, 0.1, 0.25, 0.5])

    def discretize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Discretize scores into levels 1-5 using the fixed thresholds."""
        return super().discretize(submission, defect_counts) + 1

    @classmethod
    def get_discretization_scale(cls) -> str:
        """Return the name of the model's discretization scale (e.g., '1-5')."""
        return "1-5"


class ZScoreBasedModel(PrioritizationModel, ABC):
    """Base class for models using Z-score like scores (symmetric around 0)."""

    def _calculate_thresholds(self):
        """Set fixed threshold boundaries for the -2 to +2 scale."""
        self.thresholds = np.array([-1.5, -0.5, 0.5, 1.5])

    def discretize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Discretize scores into levels -2-2 using the fixed thresholds."""
        return super().discretize(submission, defect_counts) - 2

    @classmethod
    def get_discretization_scale(cls) -> str:
        """Return the name of the model's discretization scale (e.g., '-2-2')."""
        return "-2-2"
