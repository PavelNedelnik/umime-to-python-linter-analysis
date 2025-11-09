"""Survey page logic — displays questions, collects answers, and shows context."""

import cgi
import csv
import random
from pathlib import Path

from .survey_logic import get_unanswered_questions, get_user_id, load_heuristics, render_context_table, save_answer


def show_survey_page(data_path: Path, form: cgi.FieldStorage):
    """Display a survey question and handle recording the user's answer."""
    user_choice = form.getvalue("choice")
    question_id = form.getvalue("question_id")
    user_id = get_user_id()

    # Record previous answer if available
    if user_choice:
        save_answer(data_path, user_id, question_id, user_choice)

    # Determine next question
    questions = get_unanswered_questions(data_path, user_id)
    if not questions:
        return show_thank_you_page()

    question = random.choice(questions)
    defects = load_defects_for_submission(data_path, question["index"])
    heuristics = load_heuristics(data_path)

    # ---- HTML Output ----
    print("""
    <div class="survey-container">
        <header class="survey-header">
            <h1>Beginner Code Quality Defects</h1>
            <p>
                Analyze the student's submission and select the most relevant defect —
                the one you would explain to the student at this point.
                Pay particular attention to the <strong>Defect Context</strong> section.
            </p>
            <button onclick="window.location.href='defects.py'" class="nav-button">Exit</button>
        </header>

        <div class="survey-content">
    """)

    # Left column (task + context)
    render_task_section(question, defects, heuristics)

    # Right column (defects list)
    render_defects_section(defects, question["index"])

    # Close content + container
    print("""
        </div> <!-- survey-content -->
    </div> <!-- survey-container -->
    """)


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------


def load_defects_for_submission(data_path: Path, submission_index: str):
    """Load all defect entries for a given submission index."""
    defects = []
    with open(data_path / "defects.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if row["submission id"] == submission_index:
                defects.append(row)
    return defects


def render_task_section(question: dict, defects: list, heuristics: list):
    """Render the left-hand column: task description, code, and context table."""
    print(f"""
        <section class="task-section">
            <h3>({question["index"]}) {question["task name"]}</h3>
            <p><strong>Instructions:</strong> {question["instructions"]}</p>
            <pre class="code-block"><code>{question["submission"]}</code></pre>
    """)

    # Context table section
    print("""
        <div class="context-section">
            <h3>Defect Context by Heuristic</h3>
    """)
    relevant_defects = [d for d in defects if d["submission id"] == question["index"]]
    print(render_context_table(relevant_defects, heuristics))
    print("""
        </div> <!-- context-section -->
        </section> <!-- task-section -->
    """)


def render_defects_section(defects: list, question_index: str):
    """Render the right-hand column with selectable defect buttons."""
    print("""
        <section class="defects-section">
            <form action='defects.py?page=survey' method='post' class='defect-form'>
    """)

    for defect in defects:
        print(f"""
            <button type='submit' name='choice' value='{defect["defect id"]}' class='defect-button'>
                <div class="defect-content-wrapper">
                    <div class="defect-info">
                        <p><strong>{defect["name"]}:</strong> {defect["description"]}</p>
                        <div class="defect-fix-block">
        """)

        if defect["code example"]:
            print(f'<pre class="code-block"><code>Example:\n{defect["code example"]}</code></pre>')
        if defect["code fix example"]:
            print(f'<pre class="code-block"><code>Fix:\n{defect["code fix example"]}</code></pre>')

        print("""
                        </div> <!-- defect-fix-block -->
                    </div> <!-- defect-info -->
                </div> <!-- defect-content-wrapper -->
            </button>
        """)

    print(f"""
                <input type='hidden' name='question_id' value='{question_index}'>
            </form>
        </section> <!-- defects-section -->
    """)


def show_thank_you_page():
    """Display a completion message when all questions are done."""
    print("""
    <div class="survey-container">
        <div class="survey-header">
            <button onclick="window.location.href='defects.py'" class="nav-button">Exit</button>
            <h1>Beginner Code Quality Defects</h1>
            <h2>Thank you!</h2>
            <p>You have answered all available questions in the survey.</p>
        </div>
    </div>
    """)
