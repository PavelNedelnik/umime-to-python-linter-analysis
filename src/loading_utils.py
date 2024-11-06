"""Utility functions for <loading_scripts> module."""

import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd


class DataLoadingLogger:
    """Displays information about the loading progress to the user."""

    def __init__(self) -> None:
        """Initialize the logging.Logger and set up the indentation level."""
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.indentation_level = 0

    def simple_step_start(self, step_description: str) -> None:
        """Display information at the start of an atomic step.

        Arguments:
            step_description -- Brief description of the step to be shown to the user.
        """
        self._logging_message(step_description, 0)
        self.indentation_level += 1

    def simple_step_end(self, additional_information: str = "") -> None:
        """Inform the user that the last atomic step is completed.

        Arguments:
            additional_information -- Any addition information to be shown to the user.
        """
        self._logging_message("Done. {}".format(additional_information), 0)
        self.indentation_level -= 1

    def advanced_step_decorator(
        self, start_message: str, end_message: str | None = None, heading_level: int = 1
    ) -> callable:
        """Wrap a step with multiple substeps.

        Arguments:
            start_message -- Message to be displayed at the start of the step.
            end_message -- Message to be displayed after its completion.

        Keyword Arguments:
            heading_level -- Defines how the messages are formatted (default: {1})
        """

        def wrap(function: callable):
            def wrapped(*args, **kwargs):
                self._logging_message(start_message, heading_level)
                self.indentation_level += 1
                result = function(*args, **kwargs)
                self.indentation_level -= 1
                self._logging_message(
                    end_message if end_message else "finished {}".format(start_message), heading_level
                )
                return result

            return wrapped

        return wrap

    def _logging_message(self, message: str, heading_level: int = 0) -> None:
        """Output the message with the right indentation and formatting.

        Arguments:
            message -- Message to the user.

        Keyword Arguments:
            heading_level -- How the message will be formatted. The lower the number, the more
                            prominent it will be. 0 = no formatting (default: {0})
        """
        # TODO text adjusting
        if heading_level == 1:
            message = " ===== {} ===== ".format(message.upper())
        elif heading_level == 2:
            message = " --- {} --- ".format(message.upper())

        self.logger.info("\t" * self.indentation_level + message)


logger = DataLoadingLogger()


def filter_columns(
    data: pd.DataFrame, columns_to_keep: list[str], description: str = "Filtering columns..."
) -> pd.DataFrame:
    """Only keep the specified columns and report to the user.

    Arguments:
        data -- Dataframe to modify.
        columns_to_keep -- Columns to keep. All other columns will be dropped.

    Keyword Arguments:
        description -- Describe to the user what columns you are dropping. (default: {"Filtering columns..."})

    Returns:
        Dataframe with only the specified columns.
    """
    logger.simple_step_start(description)
    num_columns = data.shape[1]
    data = data.loc[:, columns_to_keep]
    logger.simple_step_end("Dropped {} unused columns.".format(num_columns - data.shape[1]))
    return data


def filter_rows(data: pd.DataFrame, rows_to_keep: pd.Series, description: str = "Filtering rows...") -> pd.DataFrame:
    """Only keep the specified rows and report to the user.

    Arguments:
        data -- Dataframe to modify.
        rows_to_keep -- pd.Series of booleans signyfing which rows to keep. All other rows will be dropped.

    Keyword Arguments:
        description -- Describe to the user what rows you are dropping. (default: {"Filtering rows..."})

    Returns:
        Dataframe with only the specified rows.
    """
    logger.simple_step_start(description)
    num_rows = data.shape[0]
    data = data.loc[rows_to_keep]
    logger.simple_step_end("Dropped {} rows, {} rows remaining.".format(num_rows - data.shape[0], data.shape[0]))
    return data


def setup_data_path(path: str | Path, default_name: str | None = None) -> Path:
    """Find the path to the data file.

    Arguments:
        path -- Path of the folder or the file.

    Keyword Arguments:
        default_name -- If path leads to the folder, it will be used to access the file. (default: {None})

    Returns:
        Path to the data file.
    """
    if isinstance(path, str):
        path = Path(path)
    if path.is_dir():
        path = path / default_name
    return path
