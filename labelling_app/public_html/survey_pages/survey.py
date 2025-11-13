"""Survey page logic — display questions, collect answers, and handle comments."""

import cgi
import random
from pathlib import Path

from .utils import data_access, shared_components, survey_logic


def survey(data_path: Path, form: cgi.FieldStorage):
    """Display a survey question and handle recording the user's answer and comment."""
    # --- Collect data ---
    user_id = survey_logic.get_user_id()
    user_choice = form.getvalue("choice")
    question_id = form.getvalue("question_id")
    comment = form.getvalue("comment", "").strip()

    # Record previous answer if available
    if user_choice:
        survey_logic.save_answer(data_path, user_id, question_id, user_choice, comment)

    # Get next unanswered question
    questions = survey_logic.get_unanswered_questions(data_path, user_id)
    if not questions:
        return show_thank_you_page()

    question = random.choice(questions)
    defects = survey_logic.get_defects_for_submission(data_path, question["index"])
    heuristics = data_access.load_csv(data_path / "heuristics.csv")

    # ---- Render page components ----
    print(render_header())
    print("<div class='survey-content'>")
    print(shared_components.render_task_section(question, defects, heuristics))
    print(render_survey_defects_section(defects, question["index"]))
    print("</div></div>")  # Close content + container


def render_header() -> str:
    """Render the header for the survey page."""
    return """
    <div class="survey-container">
        <header class="survey-header">
            <h1>Beginner Code Quality Defects</h1>
            <p>
                Analyze the submission and select the most relevant defect.
                Pay attention to the context.
            </p>
            <button onclick="window.location.href='defects.py'" class="nav-button">Exit</button>
        </header>
    """


def render_survey_defects_section(defects: list, question_index: str) -> str:
    """Render defects as selectable buttons with an attached comment box."""
    if not defects:
        return "<p>No defects available.</p>"

    html = ['<section class="defects-section">']
    html.append('<form action="defects.py?page=survey" method="post" class="defect-form">')

    for defect in defects:
        html.append(shared_components.render_defect_button(defect, is_clickable=True))

    # Add comment box
    html.append(shared_components.render_comment_box())
    html.append(f'<input type="hidden" name="question_id" value="{question_index}">')
    html.append("</form></section>")

    return "".join(html)


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
