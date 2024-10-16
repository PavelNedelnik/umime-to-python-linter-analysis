"""Data loading and preprocessing.

TODO use logging

Provides scripts for simplified loading and cleaning of the data.
"""

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

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

    len_before = len(log)
    log = log[log["answer"].apply(lambda x: len(str.strip(x))) > 0]
    print("\tDropped {} rows with empty submissions.".format(len_before - (len_before := len(log))))

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
    print("\tDropped {} unused columns".format(num_columns - item.shape[1]))

    print("\tDecoding instructions and solutions...", end="")
    item["instructions"] = item["instructions"].apply(lambda x: eval(x)[0][1])
    item["solution"] = item["solution"].apply(lambda x: eval(x)[0][1]).apply(decode_code_string)
    print("Done")

    print("All finished. Returning item.")
    return item


def load_defects(data_path: Path) -> pd.DataFrame:
    """Load and clean the ipython defects database.

    Arguments:
        data_path -- Path to the ipython log.

    Returns:
        Loaded and cleaned ipython defects.
    """
    print("Loading defects...", end="")
    if data_path.is_dir():
        data_path = data_path / "defects.csv"
    defects = pd.read_csv(data_path)
    print("Done.")

    print("Cleaning...")
    num_columns = defects.shape[1]
    defects = defects[["defect name", "EduLint code", "defect type", "description"]]
    print("\tDropped {} unused columns".format(num_columns - defects.shape[1]))

    len_before = len(defects)
    defects.dropna(inplace=True)
    print("\tDropped {} defects not detected by EduLint".format(len_before - (len_before := len(defects))))

    print("\tCleaning EduLint codes...", end="")
    defects["EduLint code"] = defects["EduLint code"].apply(lambda x: tuple(map(str.strip, x.split(","))))
    print("\tDone.")

    print("Done.")

    print("All finished. Returning defects.")
    return defects


def load_messages(data_path: Path) -> pd.DataFrame:
    """Load linter messages corresponding to the entries in the log as generated by the <generate_linter_messages.py> script.

    Arguments:
        data_path -- Path to the log with linter messages.

    Returns:
        Dataframe of message codes and message logs for each processed submission.
    """
    print("Loading messages...", end="")
    if data_path.is_dir():
        data_path = data_path / "messages.txt"
    with open(data_path, "r") as f:
        messages = [eval(line) for line in f.readlines()]
    index, data = list(zip(*messages))
    result = pd.DataFrame(
        [list(zip(*row)) if len(row) else [(), ()] for row in data], index=index, columns=["codes", "text"]
    )
    print("Done.")

    print("All finished. Returning messages for {} submissions.".format(result.shape[0]))
    return result


def assign_defects(log: pd.DataFrame, defects: pd.DataFrame) -> pd.DataFrame:
    """Replace defect codes with defect ids in the log.

    Arguments:
        log -- Dataframe of ipython log.
        defects -- Dataframe of recognized defects.

    Returns:
        Dataframe of ipython log with assigned defect ids.
    """
    inv_code_dict = {}
    for defect_id, codes in defects["EduLint code"].to_dict().items():
        for code in codes:
            inv_code_dict[code] = defect_id

    defect_ids = []
    for row in log["codes"]:
        codes = []
        for code in row:
            if code in inv_code_dict:
                codes.append(inv_code_dict[code])
        defect_ids.append(codes)
    log["defects"] = defect_ids
    return log


def vectorize_defects(log: pd.DataFrame) -> np.array:
    """Vectorize messages into a count matrix.

    Arguments:
        messages -- Dataframe of message codes and message logs for each processed submission.

    Returns:
        Matrix of message counts.
    """
    vectorizer = CountVectorizer()
    defect_log = pd.DataFrame(
        vectorizer.fit_transform(log["defects"].apply(lambda x: " ".join(map(str, x)))).toarray(),
        columns=vectorizer.get_feature_names_out().astype(int),
        index=log.index,
    )

    defect_log = (defect_log > 0).astype(int)
    return defect_log


def load_ipython_data(data_path: Path, defect_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load and clean the ipython data.

    Arguments:
        data_path -- Path to the ipython log.
        defect_path -- Path to the EduLint defects.

    Returns:
        Loaded and cleaned ipython data.
    """
    print("Loading ipython data...")
    item = load_item(data_path)
    defects = load_defects(defect_path)

    log = load_log(data_path)
    log_length = len(log)
    messages = load_messages(data_path)
    messages_length = len(messages)

    print("Merging EduLint messages with log...")
    log = log.merge(messages, left_index=True, right_index=True)
    print(
        "Done. Dropped {} submissions from messages. Dropped {} submissions from log.".format(
            messages_length - len(log), log_length - len(log)
        )
    )

    print("Assigning defects to EduLint messages...")
    log = assign_defects(log, defects)
    print("Done.")

    print("Vectorizing defects...")
    defect_log = vectorize_defects(log)
    print("Done.")

    print("All finished. Returning log, item, defects.")

    return item, defects, log, defect_log
