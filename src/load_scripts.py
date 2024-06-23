"""Data loading and preprocessing.

TODO use logging

Provides scripts for simplified loading and cleaning of the data.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from src.code_processing import decode_code_string


def load_log(data_path: Path) -> pd.DataFrame:
    """Load and clean the ipython log database.

    Arguments:
        data_path -- Path to the ipython log.

    Returns:
        Loaded and cleaned ipython log.
    """
    print("Loading log...", end="")
    if data_path.is_dir():
        data_path = data_path / "log.csv"
    log = pd.read_csv(data_path, sep=";")
    print(" Done. Found {} values.".format(len(log)))

    print("Cleaning...")
    len_before = len(log)
    log.drop_duplicates(inplace=True)
    print("\tDropped {} duplicates.".format(len_before - (len_before := len(log))))
    log.dropna(inplace=True)
    print("\tDropped {} rows with missing values.".format(len_before - (len_before := len(log))))

    print("\tConverting types...")
    print("\t\tTime...", end="")
    log["time"] = pd.to_datetime(log["time"])
    print(" Done.")
    print("\t\tCorrect...", end="")
    log["correct"] = log["correct"].astype(bool)
    print(" Done.")
    print("\tDone.")

    print("\tDecoding submissions...", end="")
    log["answer"] = log["answer"].apply(decode_code_string)
    print(" Done.")
    ## discard submissions with empty answers
    print("\tDropped {} rows with empty submissions.".format(len_before - (len_before := len(log))))

    # TODO discard duplicit and other nonsensical answers

    print("Done.")

    print("All finished. Returning log with {} values.".format(len(log)))
    return log


def load_item(data_path: Path) -> pd.DataFrame:
    """Load and clean the ipython item database.

    Arguments:
        data_path -- Path to the ipython log.

    Returns:
        Loaded and cleaned ipython item.
    """
    print("Loading item...", end="")
    if data_path.is_dir():
        data_path = data_path / "item.csv"
    item = pd.read_csv(data_path, sep=";", index_col=0)
    print("Done.")

    print("Cleaning...")
    num_columns = item.shape[1]
    item = item[["name", "instructions", "solution"]]
    print("\tDropped {} irrelevant columns".format(num_columns - item.shape[1]))

    print("\tDecoding instructions and solutions...", end="")
    item["instructions"] = item["instructions"].apply(lambda x: eval(x)[0][1])
    item["solution"] = item["solution"].apply(lambda x: eval(x)[0][1]).apply(decode_code_string)
    print("Done")

    print("All finished. Returning item.")
    return item


def load_messages(data_path: Path) -> pd.DataFrame:
    """Load linter messages corresponding to the entries in the log as generated by the <generate_linter_messages.py> script.

    Arguments:
        data_path -- Path to the log with linter messages.

    Returns:
        _description_
    """
    print("Loading messages...", end="")
    if data_path.is_dir():
        data_path = data_path / "messages.csv"
    messages = pd.read_csv(data_path, sep=";", index_col=0)
    print("Done.")

    return messages
