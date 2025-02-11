"""Models for prioritization of linter messsages."""

import pandas as pd


class PrioritizationModel:
    """Base class for prioritization models."""

    def __init__(self, *args, **kwargs) -> None:
        """Set any and all model hyperparameters."""
        pass

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
        return self

    def prioritize(self, submission: pd.Series, defects: pd.Series) -> pd.Series:
        """Prioritize defects.

        Arguments:
            submission -- Information about the user's submission.
            defects -- Vector of detected defects.

        Returns:
            Vector of defects with assigned priorities.
        """
        return pd.Series([0] * len(defects))


class SeverityPrioritizer(PrioritizationModel):
    """Prioritize defects by severity."""

    def train(self, log: pd.DataFrame, defect_log: pd.DataFrame, defects: pd.DataFrame, items: pd.DataFrame):
        """Store the defect severity."""
        self.severity = defects["severity"]
        return self

    def prioritize(self, submission: pd.Series, defects: pd.Series) -> pd.Series:
        """Prioritize linter messages.

        Arguments:
            submission -- Information about the user's submission.
            defects -- Vector of detected defects.

        Returns:
            Vector of defects with assigned priorities.
        """
        return (defects > 0) * self.severity
