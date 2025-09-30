"""
This module contains prioritization models that focus on student-specific context.

These models calculate a weight matrix where rows are students and columns are defects.
"""

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
from scipy.stats import zscore

from src.prioritization.base import PrioritizationModel


class StudentPrioritizationModel(PrioritizationModel, ABC):
    """
    Provide a base for all student-pure prioritization models.

    These models have a bulk `update` method for learning and
    must return a student-defect weight matrix.
    """

    def get_context_type(self) -> str:
        """Return the type of context the model uses."""
        return "student"

    @abstractmethod
    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed student-defect weight matrix."""
        pass


class StudentCharacteristicModel(StudentPrioritizationModel):
    """Prioritize defects a student makes with a statistically significant frequency."""

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, *args, **kwargs):
        """Initialize the model."""
        super().__init__(items, defects, *args, **kwargs)
        self.user_data = pd.DataFrame(columns=["submissions"])
        self.user_defect_counts = pd.DataFrame(columns=self.defects.index, dtype=int)
        self.user_z_scores = pd.DataFrame(columns=self.defects.index)

    def _calculate_stats(self):
        """Calculate user frequencies and z-scores."""
        if self.user_data.empty:
            self.user_z_scores = pd.DataFrame(columns=self.defects.index)
            return

        user_defect_freqs = (
            self.user_defect_counts.divide(self.user_data["submissions"], axis=0).astype(float).fillna(0.0)
        )
        temp_z_scores = user_defect_freqs.apply(lambda col: zscore(col, nan_policy="omit"))
        self.user_z_scores = temp_z_scores.reindex(columns=self.defects.index, fill_value=0).fillna(0)

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        user_id = submission["user"]
        if user_id not in self.user_z_scores.index:
            return pd.Series(0, index=defect_counts.index)

        priorities = self.user_z_scores.loc[user_id]
        return self._apply_scores(priorities.abs().fillna(0), defect_counts)

    def update(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame):
        """Update the model's state with a batch of new submissions."""
        submissions, defect_counts = self._handle_update_input(submissions, defect_counts)

        submissions_by_user = submissions.groupby("user")

        for user_id, user_submissions in submissions_by_user:
            self.user_data.loc[user_id, "submissions"] = self.user_data.get("submissions", {}).get(user_id, 0) + len(
                user_submissions
            )

            defect_counts_for_user = defect_counts.loc[user_submissions.index]
            defect_presence_sum = (defect_counts_for_user > 0).astype(int).sum()

            if user_id not in self.user_defect_counts.index:
                self.user_defect_counts.loc[user_id] = defect_presence_sum
            else:
                self.user_defect_counts.loc[user_id] = self.user_defect_counts.loc[user_id].add(
                    defect_presence_sum, fill_value=0
                )

        self._calculate_stats()

    def reset_model(self):
        """Reset the model's internal state to its initial configuration."""
        self.user_data = pd.DataFrame(columns=["submissions"])
        self.user_defect_counts = pd.DataFrame(columns=self.defects.index, dtype=int)
        self.user_z_scores = pd.DataFrame(columns=self.defects.index)

    def get_model_description(self) -> str:
        """Return a human-readable description of the model's logic."""
        return "Prioritizes defects a student makes with a statistically significant frequency (z-score)."

    def get_measure_name(self) -> str:
        """Return a short, descriptive name of the model's measure (e.g., 'Frequency')."""
        return "Z-Score"

    def get_measure_description(self) -> str:
        """Return a human readable description of the model output (e.g. 'Commonality')."""
        return "Student-Defect Characteristic Scores"

    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed student-defect z-score matrix."""
        return self.user_z_scores


class StudentFrequencyModel(StudentPrioritizationModel):
    """Prioritizes defects based on a student's past frequency of making them."""

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, *args, **kwargs):
        """Initialize the model."""
        super().__init__(items, defects, *args, **kwargs)
        self.user_data = pd.Series(dtype=int)
        self.user_defect_counts = pd.DataFrame(columns=self.defects.index, dtype=int)
        self.user_defect_freqs = pd.DataFrame(columns=self.defects.index)

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        user_id = submission["user"]
        if user_id not in self.user_defect_freqs.index:
            return pd.Series(0, index=defect_counts.index)

        priorities = self.user_defect_freqs.loc[user_id]
        return self._apply_scores(priorities.fillna(0), defect_counts)

    def update(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame):
        """Update the model's state with a batch of new submissions."""
        submissions, defect_counts = self._handle_update_input(submissions, defect_counts)

        submissions_by_user = submissions.groupby("user")
        defect_counts_by_user = defect_counts.groupby(submissions["user"])

        for user_id, user_submissions in submissions_by_user:
            self.user_data.loc[user_id] = self.user_data.get(user_id, 0) + len(user_submissions)

            defect_counts_for_user = defect_counts.loc[user_submissions.index]
            defect_presence_sum = (defect_counts_for_user > 0).astype(int).sum()

            if user_id not in self.user_defect_counts.index:
                self.user_defect_counts.loc[user_id] = defect_presence_sum
            else:
                self.user_defect_counts.loc[user_id] = self.user_defect_counts.loc[user_id].add(
                    defect_presence_sum, fill_value=0
                )

        self.user_defect_freqs = self.user_defect_counts.divide(self.user_data, axis=0).fillna(0)

    def reset_model(self):
        """Reset the model's internal state to its initial configuration."""
        self.user_data = pd.Series(dtype=int)
        self.user_defect_counts = pd.DataFrame(columns=self.defects.index, dtype=int)
        self.user_defect_freqs = pd.DataFrame(columns=self.defects.index)

    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed student-defect frequency matrix."""
        return self.user_defect_freqs

    def get_measure_name(self) -> str:
        """Return a short, descriptive name of the model's measure (e.g., 'Frequency')."""
        return "Relative Frequency"

    def get_measure_description(self) -> str:
        """Return a human readable description of the model output (e.g. 'Commonality')."""
        return "Student-Specific Frequencies"

    def get_model_description(self) -> str:
        """Return a human-readable description of the model's logic."""
        return "Prioritizes defects based on a student's past frequency of making them."


class StudentEncounteredBeforeModel(StudentPrioritizationModel):
    """Prioritizes defects that a student has encountered recently."""

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, *args, **kwargs):
        """Initialize the model."""
        super().__init__(items, defects, *args, **kwargs)
        self.user_counters = {}

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects based on the current state of submissions since last encounter."""
        user_id = submission["user"]

        if user_id not in self.user_counters:
            return pd.Series(0, index=defect_counts.index)

        scores = self.user_counters[user_id].loc[defect_counts.index]
        priorities = (1 / scores.replace(0, np.nan)).fillna(0)

        return self._apply_scores(priorities.fillna(0), defect_counts)

    def update(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame):
        """Update the model's state with a batch of new submissions."""
        submissions, defect_counts = self._handle_update_input(submissions, defect_counts)

        for submission_id, submission in submissions.iterrows():
            user_id = submission["user"]
            defect_presence_mask = (defect_counts.loc[submission_id] > 0).astype(int)

            if user_id not in self.user_counters:
                self.user_counters[user_id] = pd.Series(0, index=self.defects.index, dtype=int)

            self.user_counters[user_id] += 1
            self.user_counters[user_id] *= 1 - defect_presence_mask

    def reset_model(self):
        """Reset the model's internal state to its initial configuration."""
        self.user_counters = {}

    def get_model_weights(self) -> pd.DataFrame:
        """Return None. This model does not have a static weight matrix."""
        return None

    def get_measure_name(self) -> str:
        """Return a precise, short description of the model's output."""
        return "Submissions since last encounter (inverted)"

    def get_measure_description(self) -> str:
        """Return a human-readable description of the model's output."""
        return "Student-Defect Recency"

    def get_model_description(self) -> str:
        """Return a human-readable description of the model's logic."""
        return "Prioritizes defects that a student has encountered recently."


class DefectMultiplicityModel(PrioritizationModel):
    """Prioritizes defects based on how many times they appear in a submission, normalized by global statistics."""

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, *args, **kwargs):
        """Initialize the model."""
        super().__init__(items, defects, *args, **kwargs)
        self.all_submissions = pd.DataFrame()
        self.all_defect_counts = pd.DataFrame(columns=self.defects.index, dtype=int)

    def _calculate_stats(self):
        """Calculate global mean and std from all submissions seen so far."""
        if self.all_defect_counts.empty:
            self.global_means = pd.Series(0, index=self.defects.index)
            self.global_stds = pd.Series(1, index=self.defects.index)
        else:
            self.global_means = self.all_defect_counts.mean()
            self.global_stds = self.all_defect_counts.std().replace(0, 1)

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects based on normalized multiplicity."""
        self._calculate_stats()

        aligned_defect_counts = defect_counts.reindex(self.global_means.index, fill_value=0)

        normalized_counts = (aligned_defect_counts - self.global_means) / self.global_stds

        return self._apply_scores(normalized_counts.abs().astype(float).fillna(0), defect_counts)

    def update(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame):
        """Update the model's state with a batch of new submissions."""
        submissions, defect_counts = self._handle_update_input(submissions, defect_counts)

        self.all_submissions = pd.concat([self.all_submissions, submissions])
        self.all_defect_counts = pd.concat(
            [self.all_defect_counts, defect_counts.reindex(columns=self.defects.index, fill_value=0)]
        )

    def reset_model(self):
        """Reset the model's internal state to its initial configuration."""
        self.all_submissions = pd.DataFrame()
        self.all_defect_counts = pd.DataFrame(columns=self.defects.index, dtype=int)

    def get_context_type(self) -> str:
        """Return the type of context the model uses."""
        return "student"

    def get_measure_name(self) -> str:
        """Return a precise, short description of the model's output."""
        return "Normalized Defect Counts"

    def get_measure_description(self) -> str:
        """Return a human-readable description of the model's output."""
        return "Defect Muliplicity"

    def get_model_description(self) -> str:
        """Return a human-readable description of the model's logic."""
        return "Prioritizes defects by how unusually common they are in a submission, with adaptive global statistics."

    def get_model_weights(self) -> pd.DataFrame:
        """Return the pre-computed weight matrix for analysis."""
        self._calculate_stats()
        return pd.DataFrame({"means": self.global_means, "stds": self.global_stds}).T
