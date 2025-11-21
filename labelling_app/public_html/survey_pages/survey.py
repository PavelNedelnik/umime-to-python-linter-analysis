"""Survey page logic — display questions, collect answers, and handle comments."""

from pathlib import Path
from urllib.parse import urlencode

from utils import data_access, shared_components, survey_logic

# ============================================================
# =========================  ROUTE  ==========================
# ============================================================


def survey(data_path: Path, form) -> str:
    """Return survey page HTML with question, defects, and optional feedback."""
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
        return f"<meta http-equiv='refresh' content='0; url=defects.py?{params}'>"

    # Record answer to the previous question
    if user_choice:
        survey_logic.save_answer(data_path, user_id, question_id, user_choice, comment)

    # Determine whether to show the feedback prompt
    show_feedback_prompt = not feedback_just_submitted and survey_logic.is_feedback_checkpoint(data_path, user_id)

    # Retrieve the next question
    question = survey_logic.get_next_question(data_path, user_id)
    if question is None:
        return show_thank_you_page()

    defects = survey_logic.get_defects_for_submission(data_path, question["index"])
    heuristics = data_access.load_csv(data_path / "heuristics.csv")

    # Render the page content
    html = [render_header()]
    if show_feedback_prompt:
        html.append(render_feedback_prompt())

    left_column = [
        shared_components.render_task_section(question, defects, heuristics),
        shared_components.render_heuristics_section(defects, heuristics),
    ]

    right_column = [
        shared_components.render_defects_section(
            defects,
            question["index"],
            is_clickable=True,
            show_comment_box=True,
        ),
    ]

    html.append(shared_components.two_column_layout(left_column, right_column))

    html.append("</div>")  # close survey-container
    return "".join(html)


# ============================================================
# ====================  PAGE COMPONENTS  ======================
# ============================================================


def render_header() -> str:
    """Render the header for the survey page."""
    return """
    <div class="survey-container">
        <header class="survey-header">
            <h1>Beginner Code Quality Defects Survey</h1>
            <p>Review the submission below and pick the defect you think is the most important to address first.</p>
            <p>Pay special attention to the <strong>Context Table</strong> embedding common cosiderations educators make while giving feedback.</p>
            <button onclick="window.location.href='defects.py'" class="nav-button">Exit Survey</button>
        </header>
    """


def render_feedback_prompt() -> str:
    """Render a friendly feedback box shown periodically during the survey."""
    return """
    <section class="feedback-section">
        <h2>Quick Check-In</h2>
        <p>You're doing great! How is the survey experience going so far?</p>
        <form action="defects.py?page=survey" method="post" class="feedback-form">
            <textarea name="feedback" rows="3" class="feedback-box" placeholder="Your feedback (optional)"></textarea>
            <br>
            <button type="submit" class="nav-button">Send Feedback</button>
        </form>
    </section>
    """


def show_thank_you_page() -> str:
    """Display a friendly completion message when all questions are done."""
    return """
    <div class="survey-container">
        <div class="survey-header">
            <button onclick="window.location.href='defects.py'" class="nav-button">Exit Survey</button>
            <h1>Survey Complete</h1>
            <h2>Thank You!</h2>
            <p>You've finished all the questions. Your input will help us improve code feedback tools for beginner programmers.</p>
        </div>
    </div>
    """
