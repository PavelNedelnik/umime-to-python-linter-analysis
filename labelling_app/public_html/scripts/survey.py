"""Survey page logic — displays questions, collects answers, and shows context."""

import cgi
import csv
import random
from pathlib import Path

from .survey_logic import *


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


def render_defects_section(defects: list, question_index: str):
    """Render the right-hand column with selectable defect buttons."""
    print("""
        <section class="defects-section">
            <form action='defects.py?page=survey' method='post' class='defect-form'>
    """)

    for defect in defects:
        code_example = defect.get("code example", "")
        code_fix = defect.get("code fix example", "")

        print(f"""
            <button type='submit' name='choice' value='{defect["defect id"]}' class='defect-button'>
                <div class="defect-content-wrapper">
                    <div class="defect-info">
                        <p><strong>{defect["name"]}:</strong> {defect["description"]}</p>
                        <div class="defect-fix-block">
        """)

        if code_example:
            safe_example = code_example.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            print(f'<pre class="code-block"><code>Example:\n{safe_example}</code></pre>')

        if code_fix:
            safe_fix = code_fix.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            print(f'<pre class="code-block"><code>Fix:\n{safe_fix}</code></pre>')

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
