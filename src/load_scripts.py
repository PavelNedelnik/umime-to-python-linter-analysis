"""Loading, cleaning and processing of data."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns
from IPython.display import HTML, display
from ipywidgets import Output

from src.code_processing import generate_linter_messages, parse_code_string

data_path = Path("data")
ipython_path = data_path / "ipython_new"


def load_ipython_data(
    only_correct: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int]]:
    ## load ipython items
    items = pd.read_csv(ipython_path / "item.csv", sep=";", index_col=0)
    # drop unused columns
    items = items[["name", "instructions", "solution", "democode"]]
    # extract user instructions
    items["instructions"] = items["instructions"].apply(lambda x: eval(x)[0][1])
    # extract and decode example solutions
    items["solution"] = items["solution"].apply(lambda x: eval(x)[0][1]).apply(parse_code_string)
    items["democode"] = items["democode"].apply(lambda x: eval(x)[0][1]).apply(parse_code_string)

    ## load the ipython log
    log = pd.read_csv(ipython_path / "log.csv", sep=";")
    # drop unused columns
    log = log[["id", "user", "item", "answer", "correct", "responseTime", "time"]]
    # correct data types
    log["time"] = pd.to_datetime(log["time"])
    log["correct"] = log["correct"].astype(bool)
    # drop problematic rows
    log.dropna(inplace=True)
    log.drop_duplicates(inplace=True)
    # decode submissions
    log["answer"] = log["answer"].apply(parse_code_string)
    if only_correct:
        # only correct answers
        log = log[log["correct"]]
        # only one answer per session, first because EduLint might already be integrated
        log = log.reset_index().groupby(["user", "item"], as_index=False).first().set_index("index")
    # keep only items with at least 100 submission
    items = items.loc[items.index.isin((log["item"].value_counts() > 100).index)]
    # filter them out of the log also
    log = log[log["item"].isin(items.index)]

    ## load the defect table
    defects = pd.read_csv(data_path / "defects.csv")
    # drop unused columns
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
    # drop defects not detected by EduLint
    defects.dropna(subset=["EduLint code"], inplace=True)
    # convert EduLint codes from string to tuple
    defects["EduLint code"] = defects["EduLint code"].apply(lambda x: tuple(map(str.strip, x.split(","))))
    # drop the "missing docstring" defect (not really appropriate in the context)
    # drop the "mixed indentation" defect (it is exceptionally noisy - errors during logging, students copy-pasting, ...)
    defects.drop([66, 4], axis=0, inplace=True)
    # create a dictionary mapping EduLint codes to the index of the associated defect
    code_to_defect_id = {val: idx for idx, val in defects["EduLint code"].explode().items()}

    ## load the EduLint messages corresponding to the entries in the ipython log
    # open the message log
    messages = pd.read_csv(ipython_path / "message_log.csv", index_col=0, header=0)
    # remove some of the messages associated with the "trailing whitespace" defect (they are likely logging errors)
    messages = messages[~messages["message"].isin(["no newline at end of file", "trailing whitespace"])]
    # keep only the messages still in the ipython log
    messages = messages[messages["log entry"].isin(log.index)]
    # keep only messages with an associated defect
    messages = messages[messages["defect"].isin(code_to_defect_id.keys())]
    # use defect ids instead of message codes
    messages["defect"] = messages["defect"].replace(code_to_defect_id).astype(int)
    messages.reset_index(drop=True, inplace=True)

    # vectorize defects
    defect_log = pd.crosstab(messages["log entry"], messages["defect"]).reindex(log.index, fill_value=0)

    # replace defect counts with presence
    defect_log = (defect_log > 0).astype(int)

    # keep only detected defects
    defects = defects.loc[defects.index.isin(defect_log.columns)]

    return log, defect_log, defects, items, code_to_defect_id
