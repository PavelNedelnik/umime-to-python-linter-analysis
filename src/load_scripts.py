"""Provides scripts for simplified loading and cleaning of the data."""

# TODO caching

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

from src.code_processing import decode_code_string
from src.loading_utils import filter_columns, filter_rows, logger, setup_data_path


@logger.advanced_step_decorator("loading ipython log", "finished loading ipython log", heading_level=1)
def load_log(data_path: str | Path, mode: str = "correct") -> pd.DataFrame:
    """Load and clean the ipython log database.

    Arguments:
        data_path -- Path to the ipython log.

    Returns:
        Properly loaded and cleaned ipython log.
    """
    log = open_ipython_log(data_path)

    log = clean_ipython_log(log)

    logger.simple_step_start("Filtering submissions...")
    len_before = log.shape[0]
    if mode == "correct":
        log = log[log["correct"]]
        log = log.drop("correct", axis=1)
        logger.simple_step_end(
            "Keeping only correct submissions. Dropped {} rows, {} remaining.".format(
                len_before - log.shape[0], log.shape[0]
            )
        )
    elif mode == "final":
        log = filter_final_submissions(log)
        logger.simple_step_end(
            "Keeping only the last submission of the session. Dropped {} rows, {} remaining.".format(
                len_before - log.shape[0], log.shape[0]
            )
        )
    else:
        logger.simple_step_end("No filtering applied.")

    return log


def filter_final_submissions(log: pd.DataFrame) -> pd.DataFrame:
    """Keep only the last submission from each user session.

    The end of the session is defined as a sucessful submission, the user changing to a different
    task or the user not submitting for more than 20 minutes.

    Arguments:
        log -- Ipython log.

    Returns:
        Ipython log with only the last submission from each user session.
    """
    new_log = []
    for user in np.unique(log["user"]):
        # get the user history and make sure the values are sorted
        user_history = log[log["user"] == user].sort_values("time")

        # find the session breakpoints
        user_history = user_history[
            user_history["correct"]
            | user_history["item"].ne(user_history["item"].shift(-1))
            | (user_history["time"].diff() > pd.Timedelta(minutes=20))
        ]

        new_log.append(user_history)

    log = pd.concat(new_log).sort_index()
    return log


def open_ipython_log(data_path: pd.DataFrame) -> pd.DataFrame:
    """Open the ipython log database.

    Arguments:
        data_path -- Path to the ipython log.

    Returns:
        Dataframe with the ipython log.
    """
    logger.simple_step_start("Opening...")
    data_path = setup_data_path(data_path, "log.csv")
    log = pd.read_csv(data_path, sep=";")
    logger.simple_step_end("Found {} rows.".format(log.shape[0]))
    return log


@logger.advanced_step_decorator("data cleaning", "finished cleaning data", heading_level=2)
def clean_ipython_log(log: pd.DataFrame) -> pd.DataFrame:
    """Do all the necessary data cleaning of the ipython log.

    Arguments:
        log -- Dataframe with the ipython log.

    Returns:
       Ipython log with all the necessary data cleaning done.
    """
    log = filter_columns(log, ["id", "user", "item", "answer", "correct", "responseTime", "time"])

    log = convert_types_in_ipython_log(log)

    logger.simple_step_start("Dropping empty rows...")
    len_before = len(log)
    log.dropna(inplace=True)
    logger.simple_step_end(
        "Dropped {} rows, {} remaining.".format(len_before - log.shape[0], len_before := log.shape[0])
    )

    logger.simple_step_start("Dropping duplicates...")
    log.drop_duplicates(inplace=True)
    logger.simple_step_end(
        "Dropped {} rows, {} remaining.".format(len_before - log.shape[0], len_before := log.shape[0])
    )

    logger.simple_step_start("Dropping empty submissions...")
    log = log[log["answer"].apply(lambda x: len(str.strip(x))) > 0]
    logger.simple_step_end("Dropped {} rows, {} remaining.".format(len_before - log.shape[0], log.shape[0]))

    logger.simple_step_start("Decoding answers...")
    log["answer"] = log["answer"].apply(decode_code_string)
    logger.simple_step_end()

    return log


@logger.advanced_step_decorator("converting column types", "finished converting types", heading_level=2)
def convert_types_in_ipython_log(log: pd.DataFrame) -> pd.DataFrame:
    """Fix columns with incorrectly loaded data type.

    Arguments:
        log -- Dataframe with the ipython log.

    Returns:
        Ipython log with columns properly typed.
    """
    logger.simple_step_start("<time> column...")
    log["time"] = pd.to_datetime(log["time"])
    logger.simple_step_end()

    logger.simple_step_start("<correct> column...")
    log["correct"] = log["correct"].astype(bool)
    logger.simple_step_end()

    return log


@logger.advanced_step_decorator("loading ipython items", "finished loading ipython items", heading_level=1)
def load_item(data_path: Path) -> pd.DataFrame:
    """Load and clean the ipython item database.

    Arguments:
        data_path -- Path to the ipython log.

    Returns:
        Loaded and cleaned ipython item.
    """
    items = open_ipython_items(data_path)

    items = clean_ipython_items(items)

    return items


def open_ipython_items(data_path: Path) -> pd.DataFrame:
    """Open the ipython item table.

    Arguments:
        data_path -- Path to the ipython item table.

    Returns:
        Dataframe with the ipython items.
    """
    logger.simple_step_start("Opening...")
    data_path = setup_data_path(data_path, "item.csv")
    items = pd.read_csv(data_path, sep=";", index_col=0)
    logger.simple_step_end("Found {} rows.".format(items.shape[0]))
    return items


@logger.advanced_step_decorator("data cleaning", "finished cleaning data", heading_level=2)
def clean_ipython_items(items: pd.DataFrame) -> pd.DataFrame:
    """Do all the necessary data cleaning of the ipython items.

    Arguments:
        items -- Dataframe with the ipython items.

    Returns:
       Ipythons item with all the necessary data cleaning done.
    """
    items = filter_columns(items, ["name", "instructions", "solution"])

    logger.simple_step_start("Decoding instructions...")
    items["instructions"] = items["instructions"].apply(lambda x: eval(x)[0][1])
    logger.simple_step_end()

    logger.simple_step_start("Decoding solution...")
    items["solution"] = items["solution"].apply(lambda x: eval(x)[0][1]).apply(decode_code_string)
    logger.simple_step_end()

    return items


@logger.advanced_step_decorator("loading defect database", "finished loading defects", heading_level=1)
def load_defects(data_path: Path) -> pd.DataFrame:
    """Load and clean the defect table.

    Arguments:
        data_path -- Path to the defect table.

    Returns:
        Loaded and cleaned defect database.
    """
    defects = open_defects(data_path)

    defects = clean_defects(defects)

    return defects


def open_defects(data_path: Path) -> pd.DataFrame:
    """Open the defect table.

    Arguments:
        data_path -- Path to the defect table.

    Returns:
        Dataframe with the ipython item.
    """
    logger.simple_step_start("Opening...")
    data_path = setup_data_path(data_path, "defects.csv")
    defects = pd.read_csv(data_path)
    logger.simple_step_end("Found {} rows.".format(defects.shape[0]))
    return defects


@logger.advanced_step_decorator("data cleaning", "finished cleaning data", heading_level=2)
def clean_defects(defects: pd.DataFrame) -> pd.DataFrame:
    """Clean the defect table.

    Arguments:
        defects -- Dataframe with the defects.

    Returns:
        Cleaned defect table.
    """
    defects = filter_columns(defects, ["defect name", "EduLint code", "defect type", "description"])

    logger.simple_step_start("Dropping duplicates...")
    len_before = len(defects)
    defects.drop_duplicates(inplace=True)
    logger.simple_step_end(
        "Dropped {} rows, {} remaining.".format(len_before - defects.shape[0], len_before := defects.shape[0])
    )

    logger.simple_step_start("Dropping defects not detected by EduLint...")
    defects.dropna(subset=["EduLint code"], inplace=True)
    logger.simple_step_end("Dropped {} rows, {} remaining.".format(len_before - defects.shape[0], defects.shape[0]))

    logger.simple_step_start("Decoding EduLint codes...")
    defects["EduLint code"] = defects["EduLint code"].apply(lambda x: tuple(map(str.strip, x.split(","))))
    logger.simple_step_end()

    return defects


@logger.advanced_step_decorator("loading messages", "finished loading messages", heading_level=1)
def load_messages(data_path: Path) -> pd.DataFrame:
    """Load linter messages corresponding to the entries in the log as generated by the <generate_linter_messages.py> script.

    Arguments:
        data_path -- Path to the log with linter messages.

    Returns:
        Dataframe of message codes and message logs for each processed submission.
    """
    messages = open_ipython_messages(data_path)

    logger.simple_step_start("Building dataframe...")
    index, data = list(zip(*messages))
    result = pd.DataFrame(
        [[pd.Series(row[0]), pd.Series(row[1])] if len(row) == 2 else [pd.Series(), pd.Series()] for row in data],
        index=index,
        columns=["EduLint codes", "EduLint messages"],
    )
    logger.simple_step_end()

    return result


def open_ipython_messages(data_path: Path) -> pd.DataFrame:
    """Open the ipython messages database.

    Arguments:
        data_path -- Path to the ipython messages.

    Returns:
        Dataframe with the ipython messages.
    """
    logger.simple_step_start("Opening...")
    data_path = setup_data_path(data_path, "messages.csv")
    with open(data_path, "r") as f:
        messages = [eval(line) for line in f.readlines()]
    logger.simple_step_end("Found {} rows.".format(len(messages)))
    return messages


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
    for row in log["EduLint codes"]:
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
