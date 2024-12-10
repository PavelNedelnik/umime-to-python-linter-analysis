"""Collect and cache the necessary data for <student_tracking.py>."""

from pathlib import Path

import pandas as pd

from src.code_processing import parse_code_string

data_path = Path("data")
ipython_path = data_path / "ipython_old"

print("Loading items...", end="", flush=True)
items = pd.read_csv(ipython_path / "item.csv", sep=";", index_col=0)
# drop unused columns
items = items[["name", "instructions", "solution"]]
# extract user instructions
items["instructions"] = items["instructions"].apply(lambda x: eval(x)[0][1])
# extract and decode example solutions
items["solution"] = items["solution"].apply(lambda x: eval(x)[0][1]).apply(parse_code_string)
print(" Done.", flush=True)

print("Loading log...", end="", flush=True)
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
# only known items
log = log[log["item"].isin(items.index)]
print(" Done.", flush=True)

print("Loading defects...", end="", flush=True)
defects = pd.read_csv(data_path / "defects.csv")
# drop unused columns
defects = defects[
    ["defect name", "EduLint code", "defect type", "description", "code example", "code fix example", "severity"]
]
# drop defects not detected by EduLint
defects.dropna(subset=["EduLint code"], inplace=True)
# convert EduLint codes from string to tuple
defects["EduLint code"] = defects["EduLint code"].apply(lambda x: tuple(map(str.strip, x.split(","))))
# create a dictionary mapping EduLint codes to the index of the associated defect
code_to_defect_id = {val: idx for idx, val in defects["EduLint code"].explode().items()}
print(" Done.", flush=True)

print("Loading messages...", end="", flush=True)
# open the message log
with open(ipython_path / "messages.txt", "r") as f:
    messages = [eval(line) for line in f.readlines()]
# create a dataframe
messages = [
    {"log entry": idx, "defect": code, "message": message}
    for idx, code_message_list in messages
    for code, message in code_message_list
]
messages = pd.DataFrame(messages)
# keep only the messages still in the ipython log
messages = messages[messages["log entry"].isin(log.index)]
# keep only messages with an associated defect
messages = messages[messages["defect"].isin(code_to_defect_id.keys())]
# use defect ids instead of message codes
messages["defect"] = messages["defect"].replace(code_to_defect_id).astype(int)
print(" Done.", flush=True)

print("Generating defect log...", end="", flush=True)
defect_log = pd.crosstab(messages["log entry"], messages["defect"]).reindex(log.index, fill_value=0)
# replace defect counts with presence
defect_log = (defect_log > 0).astype(int)
print(" Done.", flush=True)

# keep only detected defects
defects = defects.loc[defects.index.isin(defect_log.columns)]

print("Caching data...", end="", flush=True)
cache = ipython_path / "cache"
log.to_csv(cache / "log.csv", sep=";")
items.to_csv(cache / "items.csv", sep=";")
defects.to_csv(cache / "defects.csv", sep=";")
defect_log.to_csv(cache / "defect_log.csv", sep=";")
print(" Done.", flush=True)
