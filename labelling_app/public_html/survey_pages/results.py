"""Results page logic — display votes, highlights, and context."""

import cgi
from pathlib import Path

from .utils import data_access, shared_components, survey_logic

# ============================================================
# =========================  ROUTE  ==========================
# ============================================================


def results(data_path: Path, form: cgi.FieldStorage):
    """Display survey results with vote-based highlights."""
    # --- Collect data ---
    question_index = int(form.getvalue("question_index", 0))
    submissions = data_access.load_csv(data_path / "submissions.csv")

    if not (0 <= question_index < len(submissions)):
        return show_no_results_page()

    question = submissions[question_index]

    defects = survey_logic.get_defects_for_submission(data_path, question["index"])
    defect_counts = survey_logic.get_defect_counts(data_path, question["index"])
    heuristics = data_access.load_csv(data_path / "heuristics.csv")

    # --- Render page components ---
    print(render_navigation_bar(submissions, question_index))
    print(shared_components.render_task_section(question, defects, heuristics))
    print(render_results_defects_section(defects, defect_counts))

    # Close wrapper divs
    print("</div></div>")


# ============================================================
# =====================  PAGE COMPONENTS  =====================
# ============================================================


def render_navigation_bar(submissions, question_index):
    """Render the navigation bar for the results page."""
    return """
    <div class="survey-container">
        <header class="survey-header">
            <h1>Survey Results</h1>
            <button onclick="window.location.href='defects.py'" class="nav-button">Exit</button>
            <button onclick="window.location.href='defects.py?page=results&question_index={prev_index}'"
                    class="nav-button" {prev_disabled}>Previous</button>
            <button onclick="window.location.href='defects.py?page=results&question_index={next_index}'"
                    class="nav-button" {next_disabled}>Next</button>
        </header>
        <div class="survey-content">
    """.format(
        prev_index=max(0, question_index - 1),
        next_index=min(len(submissions) - 1, question_index + 1),
        prev_disabled="disabled" if question_index == 0 else "",
        next_disabled="disabled" if question_index == len(submissions) - 1 else "",
    )


def render_results_defects_section(defects: list, defect_counts: dict) -> str:
    """Render read-only defects with vote counts and highlight the most-voted one."""
    if not defects:
        return "<p>No defects available.</p>"

    most_votes = max(defect_counts.values(), default=0)

    html = ['<section class="defects-section"><form class="defect-form">']
    for defect in defects:
        votes = defect_counts.get(defect["defect id"], 0)
        highlight = votes == most_votes and votes > 0
        html.append(
            shared_components.render_defect_button(defect, is_clickable=False, highlight=highlight, votes=votes)
        )
    html.append("</form></section>")
    return "".join(html)


def show_no_results_page():
    """Display when no results are available."""
    print("""
    <div class="survey-container">
        <div class="survey-header">
            <button onclick="window.location.href='defects.py'" class="nav-button">Exit</button>
            <h1>Survey Results</h1>
            <h2>No Results Found</h2>
            <p>No questions are available.</p>
        </div>
    </div>
    """)
