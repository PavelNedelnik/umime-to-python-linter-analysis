"""
Data Access Utilities.

Provides functions to load and save CSV data for the survey application.
All file interactions with submissions, defects, heuristics, and responses
are centralized here for easier maintenance.
"""

import csv
from pathlib import Path
from typing import Dict, List

# ============================================================
# =====================  CSV OPERATIONS  ======================
# ============================================================


def load_csv(path: Path) -> List[Dict]:
    """Load a CSV file into a list of dictionaries."""
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        return list(reader)


def save_csv_row(path: Path, fieldnames: List[str], row: dict):
    """Append a row to a CSV file, creating it if necessary."""
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writerow(row)


# ============================================================
# =====================  DATA RETRIEVAL  ======================
# ============================================================


def get_submissions(data_path: Path) -> List[Dict]:
    """Return a list of all submissions from submissions.csv."""
    return load_csv(data_path / "submissions.csv")


def get_defects(data_path: Path) -> List[Dict]:
    """Return a list of all defects from defects.csv."""
    return load_csv(data_path / "defects.csv")


def get_heuristics(data_path: Path) -> List[Dict]:
    """Return a list of all heuristics from heuristics.csv."""
    return load_csv(data_path / "heuristics.csv")


def get_responses(data_path: Path) -> List[Dict]:
    """Return a list of all responses from responses.csv."""
    return load_csv(data_path / "responses.csv")
