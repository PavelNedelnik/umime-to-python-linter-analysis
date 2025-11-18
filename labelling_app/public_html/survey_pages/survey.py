"""Survey page logic — display questions, collect answers, and handle comments."""

import cgi
import random
from pathlib import Path
from urllib.parse import urlencode

from .utils import data_access, shared_components, survey_logic

# ============================================================
# =========================  ROUTE  ==========================
# ============================================================


def survey(data_path: Path, form: cgi.FieldStorage):
    """Display a survey question, record the user's responses, and handle feedback prompts."""
    # Collect initial request data
    user_id = survey_logic.get_user_id()
    user_choice = form.getvalue("choice")
    question_id = form.getvalue("question_id")
    comment = form.getvalue("comment", "").strip()
    feedback = form.getvalue("feedback", "").strip()
    feedback_just_submitted = form.getvalue("feedback_submitted")

    # Handle feedback submission
    if feedback:
        survey_logic.save_feedback(data_path, user_id, feedback)
        params = urlencode({"page": "survey", "feedback_submitted": "1"})
        print(f"<meta http-equiv='refresh' content='0; url=defects.py?{params}'>")
        return

    # Record answer to previous question (if provided)
    if user_choice:
        survey_logic.save_answer(data_path, user_id, question_id, user_choice, comment)

    # Determine whether to show periodic feedback prompt
    show_feedback_prompt = not feedback_just_submitted and survey_logic.is_feedback_checkpoint(data_path, user_id)

    # Retrieve next question
    questions = survey_logic.get_unanswered_questions(data_path, user_id)
    if not questions:
        return show_thank_you_page()

    question = questions[0]

    defects = survey_logic.get_defects_for_submission(data_path, question["index"])
    heuristics = data_access.load_csv(data_path / "heuristics.csv")

    # Render Page
    print(render_header())

    if show_feedback_prompt:
        print(render_feedback_prompt())

    print("<div class='survey-content'>")
    print(shared_components.render_task_section(question, defects, heuristics))
    print(shared_components.render_survey_defects_section(defects, question["index"]))
    print("</div></div>")  # Close .survey-content and overall container


# ============================================================
# ====================  PAGE COMPONENTS  ======================
# ============================================================


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


def render_feedback_prompt() -> str:
    """Render a feedback box shown periodically during the survey."""
    return """
    <section class="feedback-section">
        <h2>Quick Feedback</h2>
        <p>You've completed several questions! How is the survey experience so far?</p>
        <form action="defects.py?page=survey" method="post" class="feedback-form">
            <textarea name="feedback" rows="3" class="feedback-box" placeholder="Your feedback (optional)"></textarea>
            <br>
            <button type="submit" class="nav-button">Submit Feedback</button>
        </form>
    </section>
    """


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
