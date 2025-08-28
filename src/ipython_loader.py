"""Loading, cleaning and processing of the iPython data."""

from pathlib import Path

import pandas as pd

from src.code_processing import parse_code_string


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

    # order by difficulty
    ps_order = [
        "Proměnné a číselné výrazy",
        "Cyklus for",
        "Logické výrazy",
        "Podmíněný příkaz (if): základy",
        "Cyklus for s vnořenou podmínkou",
        "Cyklus while",
        "Podmíněný příkaz (if): těžší",
        "Posloupnosti",
        "Úpravy programů",
        "Řízení výpočtu",
        "Textové obrázky",
        "Řetězce: základy",
        "Seznamy",
        "Řetězce: těžší",
        "Seznamy a řetězce: vnořené",
        "Slovníky",
        "Záludné",
    ]

    # load problem sets
    ps = pd.read_csv(ipython_path / "ps.csv", index_col=0, header=0, sep=";")
    ps = ps[ps["url"].apply(lambda x: "interaktivni-python" in x)][["topic", "ordering"]]
    ps.rename(columns={"ordering": "topic order"}, inplace=True)
    ps["difficulty order"] = ps["topic"].apply(lambda x: ps_order.index(x))

    # load mapping to items
    item_to_ps = pd.read_csv(ipython_path / "ps_problem.csv", index_col=0, header=0, sep=";")
    item_to_ps = item_to_ps[
        item_to_ps["problem"].apply(lambda x: x in items.index) & item_to_ps["ps"].apply(lambda x: x in ps.index)
    ]

    # add to items
    keep = items.columns.union(ps.columns).tolist() + ["id"]
    items = (
        items.reset_index(names="id")
        .merge(item_to_ps, left_on="id", right_on="problem")
        .merge(ps, left_on="ps", right_index=True)[keep]
    )
    items.set_index("id", inplace=True)

    return items


def load_log(ipython_path):
    """Load and preprocess log data."""
    log = pd.read_csv(ipython_path / "log.csv", sep=";")

    # Keep only relevant columns
    log = log[["id", "user", "item", "answer", "correct", "responseTime", "time"]]

    # Convert time column to datetime and correct data types
    log["time"] = pd.to_datetime(log["time"])
    log["correct"] = log["correct"].astype(bool)

    # Sort by time
    log.sort_values("time", inplace=True)

    # Drop problematic rows
    log.dropna(inplace=True)
    log.drop_duplicates(inplace=True)

    # keep only users with at least 5 submissions
    log = log[log["user"].map(log["user"].value_counts()) >= 5]

    # Decode submissions
    log["answer"] = log["answer"].apply(parse_code_string)

    # Keep only sessions lasting at least 1 minutes
    log = log[log["responseTime"] >= 6e4]

    return log


def filter_items_and_log(items, log):
    """Filter items and log entries based on submission count."""
    # Filter out items with duplicate names
    duplicate_names = items["name"].value_counts() > 1
    duplicate_names = duplicate_names[duplicate_names].index
    if len(duplicate_names) > 0:
        for item_name in duplicate_names:
            # keep only the first entry in items
            duplicate_entries = items[items["name"] == item_name].index
            shared_id = duplicate_entries[0]
            for id in duplicate_entries[1:]:
                # drop from items
                if id != shared_id:
                    items = items[items.index != id]
                # propagate shared id to log
                log.loc[log["item"] == id, "item"] = shared_id

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

    # Replace missing values with None
    defects["code fix example"] = defects["code fix example"].fillna("")
    defects["code example"] = defects["code example"].fillna("")

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

    return defect_log


def load(ipython_path, data_path, only_correct=True, only_final=True, only_presence=True):
    """Load and preprocess data."""
    items = load_items(ipython_path)
    log = load_log(ipython_path)
    items, log = filter_items_and_log(items, log)
    defects, code_to_defect_id = load_defects(data_path)
    messages = load_messages(ipython_path, log, code_to_defect_id)
    defect_log = vectorize_defects(messages, log)

    # optinal filtering is here at the end to ensure consistency in kept items and defects

    # Keep only correct answers
    if only_correct:
        log = log[log["correct"]]

    # Keep only one answer per session
    if only_final:
        log = log.reset_index().groupby(["user", "item"], as_index=False).last().set_index("index")

    # Apply the filters to the defect log
    defect_log = defect_log.loc[log.index]

    # Replace defect counts with presence (1 if present, 0 otherwise)
    if only_presence:
        defect_log = (defect_log > 0).astype(int)

    # Keep only detected defects
    defects = defects.loc[defects.index.isin(defect_log.columns)]
    defect_log = defect_log.loc[:, defects.index]

    return items, log, defects, defect_log, code_to_defect_id
