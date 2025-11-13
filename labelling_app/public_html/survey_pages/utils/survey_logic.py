"""
Survey Logic Utilities.

Functions for handling user sessions, mapping heuristic scores, and
recording answers in the survey application.
"""

import http.cookies
import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .data_access import load_csv, save_csv_row

"""
Simplified mapping of numeric scores to qualitative labels and CSS class names.
"""

FEEDBACK_FREQUENCY = 3

# --- Mapping of scale names to numeric -> (label, css_class) ---
SCALE_MAP = {
    "1-5": {
        1: ("very low", "level-very-low"),
        2: ("low", "level-low"),
        3: ("medium", "level-medium"),
        4: ("high", "level-high"),
        5: ("very high", "level-very-high"),
    },
    "-2-2": {
        -2: ("much lower than others", "level-much-lower"),
        -1: ("lower than others", "level-lower"),
        0: ("average", "level-average"),
        1: ("higher than others", "level-higher"),
        2: ("much higher than others", "level-much-higher"),
    },
}


def map_score(score, scale="1-5"):
    """Convert a numeric score to a tuple (label, css_class) for a given scale."""
    key = int(round(float(score)))

    return SCALE_MAP.get(scale, {}).get(key, (str(score), ""))


def get_user_id() -> str:
    """
    Retrieve the user ID from cookies or generate a new UUID if not present.

    :return: A string representing the user ID.
    """
    cookie = http.cookies.SimpleCookie()
    if "HTTP_COOKIE" in os.environ:
        cookie.load(os.environ["HTTP_COOKIE"])
    if "user_id" in cookie:
        return cookie["user_id"].value
    else:
        user_id = str(uuid.uuid4())
        cookie["user_id"] = user_id
        cookie["user_id"]["path"] = "/"
        cookie["user_id"]["max-age"] = 3600  # 1 hour expiration
        return user_id


def get_timestamp() -> str:
    """
    Return a timezone-aware ISO 8601 timestamp string (UTC).

    Example: "2025-11-12T16:30:45Z"
    """
    try:
        # Use UTC for consistency across systems
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        return "unknown"


def save_answer(data_path: Path, user_id: str, question_id: str, answer: str, comment: str = ""):
    """Save a user's answer (and optional comment) to the responses.csv file."""
    row = {"respondent": user_id, "submission id": question_id, "answer": answer, "comment": comment}
    fieldnames = ["respondent", "submission id", "answer", "comment"]
    save_csv_row(data_path / "responses.csv", fieldnames, row)


def save_feedback(data_path: Path, user_id: str, feedback_text: str):
    """Save a user’s general feedback."""
    row = {"timestamp": get_timestamp(), "respondent": user_id, "feedback": feedback_text}
    fieldnames = ["timestamp", "respondent", "feedback"]
    save_csv_row(data_path / "feedback.csv", fieldnames, row)


def get_unanswered_questions(data_path: Path, user_id: str) -> list:
    """Return submissions the user has not yet answered."""
    responses = load_csv(data_path / "responses.csv")
    answered_ids = {row["submission id"] for row in responses if row["respondent"] == user_id}
    submissions = load_csv(data_path / "submissions.csv")
    return [s for s in submissions if s["index"] not in answered_ids]


def get_defects_for_submission(data_path: Path, submission_id: str) -> list:
    """Return the defects for a given submission ID."""
    defects = load_csv(data_path / "defects.csv")
    defects = [d for d in defects if d["submission id"] == submission_id]

    return defects


def get_defect_counts(data_path: Path, submission_id: str) -> defaultdict:
    """Return the defects for a given submission ID."""
    responses = load_csv(data_path / "responses.csv")
    defect_counts = defaultdict(lambda: 0)
    for response in responses:
        if response["submission id"] == submission_id:
            defect_counts[response["answer"]] = defect_counts.get(response["answer"], 0) + 1

    return defect_counts


def is_feedback_checkpoint(data_path: Path, user_id: str) -> bool:
    """Return True if it's time to show the feedback prompt."""
    responses = load_csv(data_path / "responses.csv")
    user_responses = [r for r in responses if r["respondent"] == user_id]
    return len(user_responses) > 0 and len(user_responses) % FEEDBACK_FREQUENCY == 0
