"""Survey page logic — display questions, collect answers, and handle comments."""

import cgi
import random
from pathlib import Path

from .utils import components, data_access, survey_logic


def survey(data_path: Path, form: cgi.FieldStorage):
    """Display a survey question and handle recording the user's answer and comment."""
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
    defects = data_access.load_csv(data_path / "defects.csv")
    defects = [d for d in defects if d["submission id"] == question["index"]]
    heuristics = data_access.load_csv(data_path / "heuristics.csv")

    # ---- HTML output ----
    print("""
    <div class="survey-container">
        <header class="survey-header">
            <h1>Beginner Code Quality Defects</h1>
            <p>Analyze the submission and select the most relevant defect. Pay attention to the context.</p>
            <button onclick="window.location.href='defects.py'" class="nav-button">Exit</button>
        </header>

        <div class="survey-content">
    """)

    # Left: task + context table
    print(components.render_task_section(question, defects, heuristics))

    # Right: defects + comment box
    print(render_survey_defects_section(defects, question["index"]))

    # Close containers
    print("""
        </div> <!-- survey-content -->
    </div> <!-- survey-container -->
    """)


def render_survey_defects_section(defects: list, question_index: str) -> str:
    """Render defects as selectable buttons with an attached comment box."""
    html = ['<section class="defects-section">']
    html.append(f'<form action="defects.py?page=survey" method="post" class="defect-form">')

    for defect in defects:
        html.append(f"""
        <button type="submit" name="choice" value="{defect["defect id"]}" class="defect-button">
            <div class="defect-content-wrapper">
                <div class="defect-info">
                    <p><strong>{defect["name"]}:</strong> {defect["description"]}</p>
                    <div class="defect-fix-block">
        """)
        if defect.get("code example"):
            html.append(f"<pre class='code-block'>{defect['code example']}</pre>")
        if defect.get("code fix example"):
            html.append(f"<pre class='code-block'>{defect['code fix example']}</pre>")
        html.append("</div></div></div></button>")

    # Comment box
    html.append(components.render_comment_box())

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
