"""Functionality to serve the users with appropriate questions and record answers."""

import csv
import http.cookies
import os
import uuid
from pathlib import Path


def get_user_id() -> str:
    """Get the user ID from the cookie or generate a new one."""
    cookie = http.cookies.SimpleCookie()
    if "HTTP_COOKIE" in os.environ:
        cookie.load(os.environ["HTTP_COOKIE"])

    if "user_id" in cookie:
        return cookie["user_id"].value
    else:
        user_id = str(uuid.uuid4())  # generate a random user id
        cookie["user_id"] = user_id
        cookie["user_id"]["path"] = "/"
        cookie["user_id"]["max-age"] = 3600  # cookie lasts for 1 hour
        return user_id


def get_unanswered_questions(data_path: Path, user_id: str) -> list:
    """Get one of the questions not yet answered by the user."""
    # Mark all questions that have been answered by this user
    answered = set()
    with open(data_path / "responses.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if row["respondent"] == user_id:
                answered.add(int(row["submission id"]))

    # Collect all the questions that have not been answered
    questions = []
    with open(data_path / "submissions.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if int(row["index"]) not in answered:
                questions.append(row)
    return questions


def save_answer(data_path: Path, user_id: str, question_id: str, answer: str):
    """Save the user's response to the local log."""
    with open(data_path / "responses.csv", mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, delimiter=";", fieldnames=["respondent", "submission id", "answer"])
        writer.writerow({"respondent": user_id, "submission id": question_id, "answer": answer})
