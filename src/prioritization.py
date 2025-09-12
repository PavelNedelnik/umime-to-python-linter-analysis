"""Models for prioritization of linter messsages."""

import pickle as pkl
from pathlib import Path

import numpy as np
import pandas as pd


class PrioritizationModel:
    """Base class for prioritization models."""

    def __init__(self, model_path: Path | str | None = None, *args, **kwargs) -> None:
        """Initialize the model.

        Keyword Arguments:
            model_path -- Path to a previously trained model. (default: {None})
        """
        self.trained = False

    def train(self, log: pd.DataFrame, defect_log: pd.DataFrame, defects: pd.DataFrame, items: pd.DataFrame):
        """Train the model.

        Arguments:
            log -- Log of user activity.
            defect_log -- Detected defects.
            defects -- Additional infomation about the defects.
            items -- Additional information about tasks.

        Returns:
            Trained model.
        """
        self.trained = True
        return self

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects.

        Arguments:
            submission -- Information about the user's submission.
            defect_counts -- Vector of detected defects.

        Returns:
            Vector of defects with assigned priorities.
        """
        if not self.trained:
            raise ValueError("Model is not trained.")
        return pd.Series()

    def save(self, path):
        """Save the model."""
        pkl.dump(self, open(path, "wb"))

    @classmethod
    def load(cls, path: Path | str):
        """Load the model."""
        path = Path(path)
        with open(path, "rb") as f:
            obj = pkl.load(f)
        if not isinstance(obj, cls):
            raise TypeError(f"Pickle does not contain a {cls.__name__}")
        return obj

    def __call__(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects."""
        return self.prioritize(submission, defect_counts)


class DummyTaskPrioritizer(PrioritizationModel):
    """Simple task prioritization model."""

    def train(self, log, defect_log, defects, items):
        """Train the model.

        Arguments:
            log -- Log of user activity.
            defect_log -- Detected defects.
            defects -- Additional infomation about the defects.
            items -- Additional information about tasks.

        Returns:
            Trained model.
        """
        super().train(log, defect_log, defects, items)

        self.task_weights = pd.DataFrame(
            data=np.ones((len(items), len(defects))), columns=defects.index, index=items.index
        )

        return self

    def prioritize(self, submission: pd.Series, defect_counts: pd.Series) -> pd.Series:
        """Prioritize defects.

        Arguments:
            submission -- Information about the user's submission.
            defect_counts -- Vector of detected defects.

        Returns:
            Vector of defects with assigned priorities.
        """
        if defect_counts.index != self.task_weights.columns:
            raise ValueError("Defects and task weights must have the same columns.")
        if "item" not in submission:
            raise ValueError("Unknown task.")
        if submission["item"] not in self.task_weights.index:
            raise ValueError("Unknown task.")
        return pd.Series(self.task_weights.loc[submission["item"], :] * defect_counts)
