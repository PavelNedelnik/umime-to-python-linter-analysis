"""
This module contains prioritization models that focus on student-specific context.

These models calculate a weight matrix where rows are students and columns are defects.
"""

from collections import defaultdict

import numpy as np
import pandas as pd

from src.prioritization.base import (
    FrequencyBasedModel,
    PrioritizationModel,
    StudentPrioritizationModel,
    ZScoreBasedModel,
)
from src.prioritization.utils import DefaultDictFactory, combine_stats


class StudentFrequencyModel(StudentPrioritizationModel, FrequencyBasedModel):
    """Prioritizes defects based on a student's past frequency of making them."""

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, *args, **kwargs):
        """Initialize the model."""
        super().__init__(items, defects, *args, **kwargs)
        self.user_submissions = defaultdict(DefaultDictFactory(0))
        self.user_defect_counts = defaultdict(DefaultDictFactory(pd.Series(0, index=self.defects.index, dtype=int)))
        self.user_defect_freqs = pd.DataFrame(columns=self.defects.index, dtype=float)

    def _calculate_scores(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        try:
            return self.user_defect_freqs.loc[submission["user"]]
        except KeyError:
            return pd.Series(0, index=self.defects.index, dtype=float)

    def _update_weights(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame):
        """Update the model's state with a batch of new submissions."""
        defect_presence = (defect_counts > 0).astype(int)
        user_histories = defect_presence.groupby(submissions["user"])

        for user_id, user_history in user_histories:
            self.user_submissions[user_id] += len(user_history)
            self.user_defect_counts[user_id] += user_history.sum()

        self.user_defect_freqs = pd.DataFrame.from_dict(self.user_defect_counts, orient="index").divide(
            pd.Series(self.user_submissions).replace(0, 1), axis=0
        )

    def reset_model(self) -> PrioritizationModel:
        """Reset the model's internal state to its initial configuration."""
        self.user_submissions = defaultdict(DefaultDictFactory(0))
        self.user_defect_counts = defaultdict(DefaultDictFactory(pd.Series(0, index=self.defects.index, dtype=int)))
        self.user_defect_freqs = pd.DataFrame(columns=self.defects.index, dtype=float)

        return self

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


class StudentCharacteristicModel(ZScoreBasedModel, StudentFrequencyModel):
    """Prioritize defects a student makes with a statistically significant frequency."""

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, *args, **kwargs):
        """Initialize the model."""
        super().__init__(items, defects, *args, **kwargs)
        self.global_samples = pd.Series(0, index=self.defects.index, dtype=int)
        self.global_mean = pd.Series(0, index=self.defects.index, dtype=int)
        self.global_var = pd.Series(0, index=self.defects.index, dtype=int)

        self.user_z_scores = pd.DataFrame(columns=self.defects.index, dtype=float)

    def _calculate_scores(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        try:
            return self.user_z_scores.loc[submission["user"]]
        except KeyError:
            return pd.Series(0, index=self.defects.index, dtype=float)

    def _update_weights(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame):
        """Update the model's state with a batch of new submissions."""
        super()._update_weights(submissions, defect_counts)

        presence = (defect_counts > 0).astype(int)

        new_mean = presence.mean()
        new_var = presence.var(ddof=0, skipna=True).fillna(0)

        self.global_samples, self.global_mean, self.global_var = combine_stats(
            presence.shape[0], new_mean, new_var, self.global_samples, self.global_mean, self.global_var
        )

        self.user_z_scores = self.user_defect_freqs - self.global_mean / self.global_var.pow(0.5).replace(0, 1)

    def reset_model(self) -> PrioritizationModel:
        """Reset the model's internal state to its initial configuration."""
        super().reset_model()
        self.global_samples = pd.Series(0, index=self.defects.index, dtype=int)
        self.global_mean = pd.Series(0, index=self.defects.index, dtype=int)
        self.global_var = pd.Series(0, index=self.defects.index, dtype=int)

        self.user_z_scores = pd.DataFrame(columns=self.defects.index, dtype=float)

        return self

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


class StudentEncounteredBeforeModel(StudentPrioritizationModel, FrequencyBasedModel):
    """Prioritizes defects that a student has encountered recently."""

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, *args, **kwargs):
        """Initialize the model."""
        super().__init__(items, defects, *args, **kwargs)
        self.user_counters = defaultdict(DefaultDictFactory(pd.Series(np.nan, index=self.defects.index, dtype=int)))
        self.user_weights = pd.DataFrame(columns=self.defects.index, dtype=float)

    def _calculate_scores(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects based on how recently they were encountered."""
        try:
            return self.user_weights.loc[submission["user"]]
        except KeyError:
            return pd.Series(0, index=self.defects.index, dtype=float)

    def _update_weights(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame):
        """Update the model's state with a batch of new submissions."""
        defect_presence = defect_counts > 0
        user_histories = defect_presence.groupby(submissions["user"])

        for user_id, user_history in user_histories:
            counter = self.user_counters[user_id]

            for _, defect_presence in user_history.iterrows():
                counter = counter.where(~defect_presence, 0)
                counter += 1

            self.user_counters[user_id] = counter

        self.user_weights = (1 / pd.DataFrame.from_dict(self.user_counters, orient="index")).fillna(0.0)

    def reset_model(self) -> PrioritizationModel:
        """Reset the model's internal state to its initial configuration."""
        self.user_counters = defaultdict(DefaultDictFactory(pd.Series(np.nan, index=self.defects.index, dtype=int)))
        self.user_weights = pd.DataFrame(columns=self.defects.index, dtype=float)

        return self

    def get_model_weights(self) -> pd.DataFrame:
        """Return the inverted user counters as a DataFrame."""
        return self.user_weights

    def get_measure_name(self) -> str:
        """Return a precise, short description of the model's output."""
        return "Submissions since last encounter (inverted)"

    def get_measure_description(self) -> str:
        """Return a human-readable description of the model's output."""
        return "Student-Defect Recency"

    def get_model_description(self) -> str:
        """Return a human-readable description of the model's logic."""
        return "Prioritizes defects that a student has encountered recently."


class DefectMultiplicityModel(ZScoreBasedModel, StudentPrioritizationModel):
    """Prioritizes defects based on how many times they appear in a submission, normalized."""

    def __init__(self, items: pd.DataFrame, defects: pd.DataFrame, *args, **kwargs):
        """Initialize the model."""
        super().__init__(items, defects, *args, **kwargs)
        self.n_samples = pd.Series(0, index=self.defects.index, dtype=int)
        self.mean = pd.Series(0, index=self.defects.index, dtype=int)
        self.var = pd.Series(0, index=self.defects.index, dtype=int)

    def _calculate_scores(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects based on normalized multiplicity."""
        scores = (defect_counts - self.mean) / self.var.pow(0.5).replace(0, 1)
        scores = scores.where(self.n_samples >= 2, 0)
        return scores.reindex(defect_counts.index)

    def _update_weights(self, submissions: pd.DataFrame, defect_counts: pd.DataFrame):
        """Update the model's state with a batch of new submissions."""
        present = (defect_counts > 0).astype(int)
        encountered = present.sum(axis=0)
        instances = defect_counts.sum(axis=0)

        new_mean = instances / encountered.replace(0, 1)
        new_var = defect_counts.mask(~present.astype(bool)).var(axis=0, ddof=0, skipna=True).astype(float).fillna(0.0)

        self.n_samples, self.mean, self.var = combine_stats(
            encountered, new_mean, new_var, self.n_samples, self.mean, self.var
        )

    def reset_model(self) -> PrioritizationModel:
        """Reset the model's internal state to its initial configuration."""
        self.n_samples = pd.Series(0, index=self.defects.index, dtype=int)
        self.mean = pd.Series(0, index=self.defects.index, dtype=int)
        self.var = pd.Series(0, index=self.defects.index, dtype=int)

        return self

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
        return pd.concat([self.mean, self.var**0.5], axis=1)
