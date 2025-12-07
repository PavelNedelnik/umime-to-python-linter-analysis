"""
Survey Logic Utilities.

Functions for handling user sessions, mapping heuristic scores,
selecting questions, and recording survey answers.
"""

import http.cookies
import math
import os
import random
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import DefaultDict, Dict, List, Optional

from .data_access import load_csv, save_csv_row

# ============================================================
# ===================  GLOBAL CONSTANTS  =====================
# ============================================================

# Frequency of showing the feedback prompt (every N answered questions).
FEEDBACK_FREQUENCY = 10

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


# ============================================================
# ==================  UTILITY / HELPERS  =====================
# ============================================================


def map_score(score, scale: str = "1-5"):
    """Convert numeric score → (label, css_class)."""
    try:
        key = int(round(float(score)))
    except Exception:
        return (str(score), "")
    return SCALE_MAP.get(scale, {}).get(key, (str(score), ""))


def get_timestamp() -> str:
    """Return a timezone-aware ISO 8601 UTC timestamp string."""
    try:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return "unknown"


def _parse_index(submission: Dict) -> int:
    """Parse a submission's numeric index. (Helper)."""
    try:
        return int(submission.get("index", -1))
    except Exception:
        return 10**9


# ============================================================
# =====================  USER / SESSIONS  ====================
# ============================================================


def get_user_id() -> str:
    """
    Retrieve the user ID from cookies or generate a new UUID.

    Other modules should always call this function for session handling.
    """
    cookie = http.cookies.SimpleCookie()
    if "HTTP_COOKIE" in os.environ:
        cookie.load(os.environ["HTTP_COOKIE"])

    if "user_id" in cookie:
        return cookie["user_id"].value

    # Need a new one
    user_id = str(uuid.uuid4())
    cookie["user_id"] = user_id
    cookie["user_id"]["path"] = "/"
    cookie["user_id"]["max-age"] = 3600
    # Caller prints cookie header
    return user_id


# ============================================================
# =====================  SAVING RESULTS  =====================
# ============================================================


def save_answer(data_path: Path, user_id: str, question_id: str, answer: str, comment: str = ""):
    """Write one user answer to responses.csv."""
    row = {
        "timestamp": get_timestamp(),
        "respondent": user_id,
        "submission id": question_id,
        "answer": answer,
        "comment": comment,
    }
    fieldnames = ["timestamp", "respondent", "submission id", "answer", "comment"]
    save_csv_row(data_path / "responses.csv", fieldnames, row)


def save_feedback(data_path: Path, user_id: str, feedback_text: str):
    """Write a feedback entry to feedback.csv."""
    row = {"timestamp": get_timestamp(), "respondent": user_id, "feedback": feedback_text}
    fieldnames = ["timestamp", "respondent", "feedback"]
    save_csv_row(data_path / "feedback.csv", fieldnames, row)


# ============================================================
# ===============  QUESTION / DEFECT RETRIEVAL  ==============
# ============================================================


def _compute_entropy(votes, k):
    counts = Counter(votes)
    total = len(votes)

    probs = [c / total for c in counts.values()]
    H = -sum(p * math.log2(p) for p in probs)

    H_norm = H / math.log2(k)  # normalized entropy
    return H_norm


def get_next_question(data_path: Path, user_id: str) -> Optional[Dict]:
    """
    Return the next question for the user.

    - Unanswered questions first
    - Otherwise, select the question with highest uncertainty score (combines # of votes and consensus)
    """
    total_responses = {}
    user_answered = set()

    responses = load_csv(data_path / "responses.csv")
    for row in responses:
        if row.get("respondent") == user_id:
            user_answered.add(row["submission id"])
        try:
            total_responses[row["submission id"]].append(row["answer"])
        except KeyError:
            total_responses[row["submission id"]] = [row["answer"]]

    submissions = load_csv(data_path / "submissions.csv")

    # look for completely unanswered questions
    globally_unanswered_questions = [s for s in submissions if s.get("index") not in total_responses]
    if len(globally_unanswered_questions) > 0:
        return random.choice(globally_unanswered_questions)

    # eligible questions
    user_unanswered_questions = [s for s in submissions if s.get("index") not in user_answered]

    if len(user_unanswered_questions) == 0:
        return None

    # compute number of possibilities for each question
    defects = load_csv(data_path / "defects.csv")
    num_possibilities = defaultdict(lambda: 0)
    for d in defects:
        num_possibilities[d["submission id"]] += 1

    # Compute uncertainty for each question
    uncertainty_scores = []
    for question in user_unanswered_questions:
        votes = total_responses.get(question["index"], [])
        total_votes = len(votes)
        score = (1 / (1 + total_votes)) + _compute_entropy(votes, num_possibilities[question["index"]])
        uncertainty_scores.append((score, question))

    # Return the question with the highest uncertainty
    _, next_question = max(uncertainty_scores, key=lambda x: x[0])
    return next_question


def get_defects_for_submission(data_path: Path, submission_id: str) -> List[Dict]:
    """Return all defects associated with a specific submission ID."""
    defects = load_csv(data_path / "defects.csv")
    return [d for d in defects if d.get("submission id") == submission_id]


def get_defect_counts(data_path: Path, submission_id: str) -> DefaultDict[str, int]:
    """Return defect vote counts for a given submission."""
    responses = load_csv(data_path / "responses.csv")
    defect_counts = defaultdict(lambda: 0)

    for response in responses:
        if response.get("submission id") == submission_id:
            defect = response.get("answer")
            defect_counts[defect] = defect_counts.get(defect, 0) + 1

    return defect_counts


# ============================================================
# =================  SURVEY FLOW / CHECKPOINTS  ==============
# ============================================================


def is_feedback_checkpoint(data_path: Path, user_id: str) -> bool:
    """Return True if the user has responded to N questions (N % FEEDBACK_FREQUENCY == 0)."""
    responses = load_csv(data_path / "responses.csv")
    user_responses = [r for r in responses if r.get("respondent") == user_id]

    return len(user_responses) > 0 and (len(user_responses) % FEEDBACK_FREQUENCY == 0)
