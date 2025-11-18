"""Results page logic — display votes, highlights, and context."""

from pathlib import Path

from .utils import data_access, shared_components, survey_logic

# ============================================================
# =========================  ROUTE  ==========================
# ============================================================


def results(data_path: Path, form) -> str:
    """Return survey results HTML with vote-based highlights."""
    question_index = int(form.getvalue("question_index", 0))
    submissions = data_access.load_csv(data_path / "submissions.csv")

    if not (0 <= question_index < len(submissions)):
        return show_no_results_page()

    question = submissions[question_index]
    defects = survey_logic.get_defects_for_submission(data_path, question["index"])
    defect_counts = survey_logic.get_defect_counts(data_path, question["index"])
    heuristics = data_access.load_csv(data_path / "heuristics.csv")

    # Build left and right columns for consistent layout
    left_column = [
        shared_components.render_task_section(question, defects, heuristics),
        shared_components.render_heuristics_section(defects, heuristics),
    ]

    right_column = [
        shared_components.render_defects_section(
            defects, question["index"], is_clickable=False, show_comment_box=False, defect_vote_counts=defect_counts
        ),
    ]

    html = [
        render_navigation_bar(submissions, question_index),
        shared_components.two_column_layout(left_column, right_column),
        "</div>",  # close survey-container
    ]
    return "".join(html)


# ============================================================
# =====================  PAGE COMPONENTS  =====================
# ============================================================


def render_navigation_bar(submissions, question_index) -> str:
    """Render the navigation bar for the results page."""
    return """
    <div class="survey-container">
        <header class="survey-header">
            <h1>Survey Results</h1>
            <div class="nav-buttons">
                <button onclick="window.location.href='defects.py'" class="nav-button">Exit</button>
                <button onclick="window.location.href='defects.py?page=results&question_index={prev_index}'"
                        class="nav-button" {prev_disabled}>Previous</button>
                <button onclick="window.location.href='defects.py?page=results&question_index={next_index}'"
                        class="nav-button" {next_disabled}>Next</button>
            </div>
        </header>
    """.format(
        prev_index=max(0, question_index - 1),
        next_index=min(len(submissions) - 1, question_index + 1),
        prev_disabled="disabled" if question_index == 0 else "",
        next_disabled="disabled" if question_index == len(submissions) - 1 else "",
    )


def show_no_results_page() -> str:
    """Display when no results are available."""
    return """
    <div class="survey-container">
        <div class="survey-header">
            <button onclick="window.location.href='defects.py'" class="nav-button">Exit</button>
            <h1>Survey Results</h1>
            <h2>No Results Found</h2>
            <p>No questions are available.</p>
        </div>
    </div>
    """
