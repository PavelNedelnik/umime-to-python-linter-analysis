"""Functionality to serve the users with appropriate questions and record answers."""

import csv
import http.cookies
import os
import uuid
from pathlib import Path

# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

SCALE_LABELS = {
    "1-5": {
        1: "very low",
        2: "low",
        3: "medium",
        4: "high",
        5: "very high",
    },
    "-2-2": {
        -2: "much lower than others",
        -1: "lower than others",
        0: "average",
        1: "higher than others",
        2: "much higher than others",
    },
}


# ---------------------------------------------------------------------
# User tracking and session handling
# ---------------------------------------------------------------------


def get_user_id() -> str:
    """Return the user ID from cookie, or generate and set a new one."""
    cookie = http.cookies.SimpleCookie()
    if "HTTP_COOKIE" in os.environ:
        cookie.load(os.environ["HTTP_COOKIE"])

    if "user_id" in cookie:
        return cookie["user_id"].value

    # Generate new UUID if not found
    user_id = str(uuid.uuid4())
    cookie["user_id"] = user_id
    cookie["user_id"]["path"] = "/"
    cookie["user_id"]["max-age"] = 3600  # one hour
    return user_id


# ---------------------------------------------------------------------
# Question and response management
# ---------------------------------------------------------------------


def get_unanswered_questions(data_path: Path, user_id: str) -> list[dict]:
    """Return a list of unanswered questions for this user."""
    responses_path = data_path / "responses.csv"
    submissions_path = data_path / "submissions.csv"

    answered = set()
    if responses_path.exists():
        with open(responses_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                if row.get("respondent") == user_id:
                    try:
                        answered.add(int(row["submission id"]))
                    except (ValueError, KeyError):
                        continue

    questions = []
    if submissions_path.exists():
        with open(submissions_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                try:
                    idx = int(row["index"])
                    if idx not in answered:
                        questions.append(row)
                except (ValueError, KeyError):
                    continue

    return questions


def save_answer(data_path: Path, user_id: str, question_id: str, answer: str) -> None:
    """Append a user response safely to responses.csv."""
    responses_path = data_path / "responses.csv"
    file_exists = responses_path.exists()

    with open(responses_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, delimiter=";", fieldnames=["respondent", "submission id", "answer"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(
            {
                "respondent": user_id,
                "submission id": question_id,
                "answer": answer,
            }
        )


# ---------------------------------------------------------------------
# Data loading and mapping
# ---------------------------------------------------------------------


def load_heuristics(data_path: Path) -> list[dict]:
    """Load heuristics definitions from heuristics.csv."""
    heuristics_file = data_path / "heuristics.csv"
    if not heuristics_file.exists():
        return []

    heuristics = []
    with open(heuristics_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            heuristics.append(
                {
                    "name": row.get("name", "").strip(),
                    "description": row.get("description", "").strip(),
                    "scale": row.get("scale", "1-5").strip(),
                }
            )
    return heuristics


def load_defects(data_path: Path) -> list[dict]:
    """Load all defects from defects.csv."""
    defects_file = data_path / "defects.csv"
    if not defects_file.exists():
        return []

    defects = []
    with open(defects_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            defects.append(row)
    return defects


def map_score_to_label(score: str, scale: str) -> str:
    """Convert a numeric score to a qualitative label."""
    if score in (None, "", " "):
        return "n/a"
    try:
        key = int(round(float(score)))
        return SCALE_LABELS.get(scale, {}).get(key, str(score))
    except Exception:
        return str(score)


def generate_css_class_name(label: str) -> str:
    """Generate a CSS-safe class name from a label."""
    return label.lower().replace(" ", "-").replace("/", "-").replace(".", "").replace(">", "gt").replace("<", "lt")


# ---------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------


def render_context_table(defects: list[dict], heuristics: list[dict]) -> str:
    """Render an HTML table showing heuristic context for each defect."""
    if not defects or not heuristics:
        return "<p>No context available.</p>"

    html = ['<table class="heuristics-table" style="width:100%; border-collapse: collapse;">']
    html.append("<thead><tr><th class='cell cell-left'>Defect</th>")

    for h in heuristics:
        tooltip = f"{h['description']} (Scale: {h['scale']})" if h.get("description") else f"Scale: {h['scale']}"
        html.append(f"<th class='cell' title='{tooltip}'>{h['name']}</th>")
    html.append("</tr></thead><tbody>")

    for defect in defects:
        html.append(f"<tr><td class='cell cell-left'>{defect.get('name', '')}</td>")
        for h in heuristics:
            score = defect.get(h["name"], "")
            label = map_score_to_label(score, h["scale"])
            css_class = generate_css_class_name(label)
            html.append(f"<td class='cell {css_class}'>{label}</td>")
        html.append("</tr>")

    html.append("</tbody></table>")
    return "".join(html)
