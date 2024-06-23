"""Continuously generates linter messages for the dataset specified by path."""

import sys
from pathlib import Path

from tqdm import tqdm

from src.code_processing import generate_linter_messages
from src.load_scripts import load_log

if len(sys.argv) != 2:
    print("Usage: python generate_linter_messages.py <data_path>")
    sys.exit(1)
data_path = Path(sys.argv[1])

log = load_log(data_path)

with open(data_path / "messages.txt", "a+") as f:
    print("Collecting already processed indices...", end="")
    processed_indices = []
    f.seek(0)
    for line in f:
        processed_indices.append(eval(line)[0])
    print(" Done. Found {}.".format(len(processed_indices)))
    print("Dropping from log...", end="")
    log.drop(processed_indices, inplace=True)
    print(" Done. Processed {}/{} rows.".format(len(processed_indices), len(log)))

    print("Generating linter messages...")
    for i, row in tqdm(log.iterrows()):
        f.write(str((i, generate_linter_messages(row["answer"]))) + "\n")
    print(" Done.")
