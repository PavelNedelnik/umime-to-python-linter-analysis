"""
This module contains prioritization models that focus purely on student context.

These models calculate a weight matrix where rows are students and columns are defects.
"""

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
from scipy.stats import zscore
from tqdm import tqdm

from .base import ContextProvider, PrioritizationModel


class StudentPrioritizationModel(PrioritizationModel, ABC):
    """Base class for student-pure prioritization models.

    These models have an `update` method for incremental learning and
    must return a student-defect weight matrix.
    """

    def update(self, submission: pd.Series, defect_counts: pd.Series):
        """Update the model's state with a new submission."""
        pass

    @abstractmethod
    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed student-defect weight matrix."""
        pass


class StudentCharacteristicModel(PrioritizationModel):
    """Prioritizes defects a student makes with a statistically significant frequency."""

    def __init__(self, *args, **kwargs):
        """Initialize the model."""
        super().__init__(*args, **kwargs)
        self.user_data = pd.DataFrame(columns=["submissions"])
        self.user_defect_counts = pd.DataFrame()

    def _calculate_stats(self):
        """Calculate user frequencies and z-scores."""
        if self.user_data.empty:
            self.user_z_scores = pd.DataFrame(columns=self.context_provider.defects.index)
            return

        user_defect_freqs = self.user_defect_counts.divide(self.user_data["submissions"], axis=0).fillna(0)
        self.user_z_scores = user_defect_freqs.apply(lambda col: zscore(col, nan_policy="omit"))

    def train(self, context_provider: ContextProvider):
        """Initialize the model with all available data."""
        super().train(context_provider)

        log = self.context_provider.get_log()
        defect_log = self.context_provider.get_defect_log()

        self.user_data = log.groupby("user").size().rename("submissions").to_frame()
        self.user_defect_counts = (defect_log > 0).groupby(log["user"]).sum()

        self._calculate_stats()
        return self

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        user_id = submission["user"]
        if user_id not in self.user_z_scores.index:
            return pd.Series(0, index=defect_counts.index)

        priorities = self.user_z_scores.loc[user_id]
        return self._apply_scores(priorities.abs().fillna(0), defect_counts)

    def update(self, submission: pd.Series, defect_counts: pd.Series):
        """Update the model's state with a new submission and recalculate stats."""
        user_id = submission["user"]
        defect_presence = (defect_counts > 0).astype(int)

        # Update submission count
        self.user_data.loc[user_id, "submissions"] = self.user_data.get("submissions").get(user_id, 0) + 1

        # Update defect counts
        if user_id not in self.user_defect_counts.index:
            self.user_defect_counts.loc[user_id] = defect_presence
        else:
            self.user_defect_counts.loc[user_id, defect_presence.index] = self.user_defect_counts.loc[
                user_id, defect_presence.index
            ].add(defect_presence, fill_value=0)

        self._calculate_stats()

    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed student-defect z-score matrix."""
        return self.user_z_scores


class StudentFrequencyModel(StudentPrioritizationModel):
    """Prioritizes defects based on a student's past frequency of making them."""

    def train(self, context_provider: ContextProvider):
        """Train the model."""
        super().train(context_provider)
        log = context_provider.get_log()
        defect_log = context_provider.get_defect_log()

        self.user_data = log.groupby("user").size().rename("submissions")
        self.user_defect_counts = (defect_log > 0).groupby(log["user"]).sum()
        self.user_defect_freqs = self.user_defect_counts.divide(self.user_data, axis=0).fillna(0)
        return self

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        user_id = submission["user"]
        if user_id not in self.user_defect_freqs.index:
            raise ValueError(f"Unknown user {user_id}")

        priorities = self.user_defect_freqs.loc[user_id]
        return self._apply_scores(priorities.fillna(0), defect_counts)

    def update(self, submission: pd.Series, defect_counts: pd.Series):
        """Update the model's state with a new submission."""
        user_id = submission["user"]
        defect_presence = (defect_counts > 0).astype(int)

        self.user_data.loc[user_id] = self.user_data.get(user_id, 0) + 1
        self.user_defect_counts.loc[user_id, defect_presence.index] = self.user_defect_counts.loc[
            user_id, defect_presence.index
        ].add(defect_presence, fill_value=0)
        self.user_defect_freqs = self.user_defect_counts.divide(self.user_data, axis=0).fillna(0)

    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed student-defect frequency matrix."""
        return self.user_defect_freqs


class StudentEncounteredBeforeModel(PrioritizationModel):
    """Prioritizes defects that a student has encountered recently."""

    def train(self, context_provider: ContextProvider):
        """Initialize the submission counters for each user by a full chronological pass."""
        super().train(context_provider)

        # A dictionary to store the 'submissions since last encounter' vector for each user.
        self.user_counters = {}

        # We perform a full chronological pass over the data to build the final state.
        temp_log = self.context_provider.get_log().sort_values("time")
        temp_defect_log = self.context_provider.get_defect_log().loc[temp_log.index]

        for submission_id, submission in tqdm(
            temp_log.iterrows(), total=len(temp_log), desc="Training Student Encountered Model"
        ):
            self.update(submission, temp_defect_log.loc[submission_id])

        return self

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects based on the current state of submissions since last encounter."""
        user_id = submission["user"]

        if user_id not in self.user_counters:
            return pd.Series(0, index=defect_counts.index)

        scores = self.user_counters[user_id].loc[defect_counts.index]
        priorities = (1 / scores.replace(0, np.nan)).fillna(0)

        return self._apply_scores(priorities.fillna(0), defect_counts)

    def update(self, submission: pd.Series, defect_counts: pd.Series):
        """Update the model's state with a new submission."""
        user_id = submission["user"]

        if user_id not in self.user_counters:
            self.user_counters[user_id] = pd.Series(0, index=self.context_provider.defects.index, dtype=int)

        self.user_counters[user_id] += 1

        defect_presence_mask = (defect_counts > 0).astype(int)
        self.user_counters[user_id] *= 1 - defect_presence_mask


class DefectMultiplicityModel(PrioritizationModel):
    """Prioritizes defects based on how many times they appear in a submission, normalized by global statistics."""

    def train(self, context_provider: ContextProvider):
        """Train the model."""
        super().train(context_provider)
        self.global_means = self.context_provider.get_defect_log().mean()
        self.global_stds = self.context_provider.get_defect_log().std()
        return self

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        # Normalize the defect counts using global stats
        normalized_counts = (defect_counts - self.global_means) / self.global_stds
        return self._apply_scores(normalized_counts.abs().fillna(0), defect_counts)
