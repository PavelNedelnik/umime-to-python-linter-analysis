"""Results page logic — display votes, highlights, and context."""

import cgi
from pathlib import Path

from .utils import components, data_access, survey_logic


def results(data_path: Path, form: cgi.FieldStorage):
    """Display survey results with vote-based highlights."""
    question_index = int(form.getvalue("question_index", 0))
    submissions = data_access.load_csv(data_path / "submissions.csv")

    if not (0 <= question_index < len(submissions)):
        return show_no_results_page()

    question = submissions[question_index]
    defects = data_access.load_csv(data_path / "defects.csv")
    defects = [d for d in defects if d["submission id"] == question["index"]]

    # Calculate votes
    responses = data_access.load_csv(data_path / "responses.csv")
    defect_counts = {d["defect id"]: 0 for d in defects}
    for r in responses:
        if r["submission id"] == question["index"]:
            defect_counts[r["answer"]] = defect_counts.get(r["answer"], 0) + 1
    for d in defects:
        d["vote_count"] = defect_counts.get(d["defect id"], 0)

    heuristics = data_access.load_csv(data_path / "heuristics.csv")

    # HTML output
    print(
        """
    <div class="survey-container">
        <header class="survey-header">
            <h1>Survey Results</h1>
            <button onclick="window.location.href='defects.py'" class="nav-button">Exit</button>
            <button onclick="window.location.href='defects.py?page=results&question_index={prev_index}'" class="nav-button" {prev_disabled}>Previous</button>
            <button onclick="window.location.href='defects.py?page=results&question_index={next_index}'" class="nav-button" {next_disabled}>Next</button>
        </header>
        <div class="survey-content">
    """.format(
            prev_index=max(0, question_index - 1),
            next_index=min(len(submissions) - 1, question_index + 1),
            prev_disabled="disabled" if question_index == 0 else "",
            next_disabled="disabled" if question_index == len(submissions) - 1 else "",
        )
    )

    # Left: task + context table
    print(components.render_task_section(question, defects, heuristics))

    # Right: defects with vote highlight
    print(render_results_defects_section(defects))

    print("</div></div>")  # survey-content + container


def render_results_defects_section(defects: list) -> str:
    """Render defects with vote counts; highlight the most voted defect (unclickable)."""
    if not defects:
        return "<p>No defects available.</p>"

    most_voted = max(defects, key=lambda d: int(d.get("vote_count", 0)))

    html = ['<section class="defects-section">']
    html.append('<form class="defect-form">')

    for d in defects:
        cls = "defect-button"
        if d == most_voted:
            cls += " highlighted unclickable"

        html.append(f"""
        <button type='submit' class='{cls}'>
            <div class="defect-content-wrapper">
                <div class="defect-info">
                    <p><strong>{d["name"]}:</strong> {d["description"]}</p>
                    <p><strong>Votes:</strong> {d.get("vote_count", 0)}</p>
                    <div class="defect-fix-block">
        """)
        if d.get("code example"):
            html.append(f"<pre class='code-block'>{d['code example']}</pre>")
        if d.get("code fix example"):
            html.append(f"<pre class='code-block'>{d['code fix example']}</pre>")
        html.append("</div></div></div></button>")

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
