"""Loading, cleaning and processing of the iPython data."""

from pathlib import Path

import pandas as pd

from src.code_processing import parse_code_string  # Ensure parse_code_string is defined in utils.py or another module


def load_items(ipython_path):
    """Load and preprocess item data."""
    items = pd.read_csv(ipython_path / "item.csv", sep=";", index_col=0)

    # Keep only relevant columns
    items = items[["name", "instructions", "solution", "democode"]]

    # Extract user instructions
    items["instructions"] = items["instructions"].apply(lambda x: eval(x)[0][1])

    # Extract and decode example solutions
    items["solution"] = items["solution"].apply(lambda x: eval(x)[0][1]).apply(parse_code_string)
    items["democode"] = items["democode"].apply(lambda x: eval(x)[0][1]).apply(parse_code_string)

    return items


def load_log(ipython_path, only_correct=True, only_final=True):
    """Load and preprocess log data."""
    log = pd.read_csv(ipython_path / "log.csv", sep=";")

    # Keep only relevant columns
    log = log[["id", "user", "item", "answer", "correct", "responseTime", "time"]]

    # Convert time column to datetime and correct data types
    log["time"] = pd.to_datetime(log["time"])
    log["correct"] = log["correct"].astype(bool)

    # Drop problematic rows
    log.dropna(inplace=True)
    log.drop_duplicates(inplace=True)

    # keep only users with at least 5 submissions
    log = log[log["user"].map(log["user"].value_counts()) >= 5]

    # Decode submissions
    log["answer"] = log["answer"].apply(parse_code_string)

    if only_correct:
        # Keep only correct answers
        log = log[log["correct"]]

    if only_final:
        # Keep only one answer per session
        log = log.reset_index().groupby(["user", "item"], as_index=False).last().set_index("index")

    return log


def filter_items_and_log(items, log):
    """Filter items and log entries based on submission count."""
    # Keep only items with at least 100 submissions
    valid_items = items.index.isin((log["item"].value_counts() > 100).index)
    items = items.loc[valid_items]

    # Filter them out of the log also
    log = log[log["item"].isin(items.index)]

    return items, log


def load_defects(data_path):
    """Load and preprocess defect data."""
    defects = pd.read_csv(data_path / "defects.csv")

    # Keep only relevant columns
    defects = defects[
        [
            "defect name",
            "EduLint code",
            "defect type",
            "description",
            "code example",
            "code fix example",
            "severity",
            "id",
        ]
    ]

    # Drop defects not detected by EduLint
    defects.dropna(subset=["EduLint code"], inplace=True)

    # Convert EduLint codes from string to tuple
    defects["EduLint code"] = defects["EduLint code"].apply(lambda x: tuple(map(str.strip, x.split(","))))

    # Drop noisy defects:
    ## "missing docstring" (students are not introduced to the concept of docstrings)
    ## "mixed indentation" (very likely caused by logging errors or copy-pasting)
    defects.drop([66, 4], axis=0, inplace=True)

    # Create a dictionary mapping EduLint codes to defect indices
    code_to_defect_id = {val: idx for idx, val in defects["EduLint code"].explode().items()}

    return defects, code_to_defect_id


def load_messages(ipython_path, log, code_to_defect_id):
    """Load and preprocess message log data."""
    messages = pd.read_csv(ipython_path / "message_log.csv", index_col=0, header=0)

    # Remove some of the messages associated with the "trailing whitespace" defect (likely logging errors)
    messages = messages[~messages["message"].isin(["no newline at end of file", "trailing whitespace"])]

    # Keep only the messages still in the ipython log
    messages = messages[messages["log entry"].isin(log.index)]

    # Keep only messages with an associated defect
    messages = messages[messages["defect"].isin(code_to_defect_id.keys())]

    # Use defect IDs instead of message codes
    messages["defect"] = messages["defect"].replace(code_to_defect_id).astype(int)

    messages.reset_index(drop=True, inplace=True)

    return messages


def vectorize_defects(messages, log):
    """Vectorize defects based on log entries."""
    # Create a defect log matrix (binary presence of defects per log entry)
    defect_log = pd.crosstab(messages["log entry"], messages["defect"]).reindex(log.index, fill_value=0)

    # Replace defect counts with presence (1 if present, 0 otherwise)
    defect_log = (defect_log > 0).astype(int)

    return defect_log


def load(ipython_path, data_path, only_correct=True, only_final=True):
    """Load and preprocess data."""
    items = load_items(ipython_path)
    log = load_log(ipython_path, only_correct=only_correct, only_final=True)
    items, log = filter_items_and_log(items, log)
    defects, code_to_defect_id = load_defects(data_path)
    messages = load_messages(ipython_path, log, code_to_defect_id)
    defect_log = vectorize_defects(messages, log)

    # Keep only detected defects
    defects = defects.loc[defects.index.isin(defect_log.columns)]

    return items, log, defects, defect_log, code_to_defect_id
