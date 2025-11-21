"""Shared rendering components for survey pages."""

from typing import List, Optional

from .survey_logic import map_score

CSS_RELATIVE_PATH = "../css/defects.css"  # relative to /public_html


# ============================================================
# =====================  LAYOUT HELPER =======================
# ============================================================


def two_column_layout(left: List[str], right: List[str]) -> str:
    """Render a responsive two-column layout for survey pages.

    Left column typically contains task + heuristics.
    Right column contains defects, feedback, or related content.
    """
    return f"""
    <div class="two-column-layout">
        <div class="left-column">
            {"".join(left)}
        </div>
        <div class="right-column">
            {"".join(right)}
        </div>
    </div>
    """


# ============================================================
# ======================  TASK SECTION  ======================
# ============================================================


def render_task_section(question: dict, defects: list, heuristics: list) -> str:
    """Render the task section: instructions and code only."""
    html = [
        f"""
        <section class="task-section">
            <h3>({question["index"]}) {question["task name"]}</h3>
            <p><strong>Instructions:</strong> {question["instructions"]}</p>
            <pre class="code-block"><code>{question["submission"]}</code></pre>
        </section>
        """
    ]
    return "".join(html)


# ============================================================
# ====================  HEURISTICS SECTION ===================
# ============================================================


def render_heuristics_section(defects: list, heuristics: list) -> str:
    """Render heuristics table + explanation as a separate section."""
    html = ['<section class="heuristics-section">']
    html.append("<h3>Context Table</h3>")
    html.append(render_heuristics_table(defects, heuristics))
    html.append(render_heuristic_explanation(heuristics))
    html.append("</section>")
    return "".join(html)


def render_heuristics_table(defects: list, heuristics: list) -> str:
    """Render an HTML table showing heuristic context for each defect."""
    if not defects or not heuristics:
        return "<p>No context available.</p>"

    html = [
        '<div class="table-wrapper"><table class="heuristics-table" style="width:100%; border-collapse: collapse;">'
    ]
    html.append("<thead><tr><th class='cell cell-left'>Defect</th>")
    for h in heuristics:
        tooltip = f"{h.get('description', '')} (Scale: {h.get('scale', '1-5')})"
        html.append(f"<th class='cell' title='{tooltip}'>{h['name']}</th>")
    html.append("</tr></thead><tbody>")

    for defect in defects:
        html.append(f"<tr><td class='cell cell-left'>{defect.get('name', '')}</td>")
        for h in heuristics:
            score = defect.get(h["name"], "")
            label, css_class = map_score(score, h.get("scale", "1-5"))
            html.append(f"<td class='cell {css_class}'>{label}</td>")
        html.append("</tr>")

    html.append("</tbody></table></div>")
    return "".join(html)


def render_heuristic_explanation(heuristics: list) -> str:
    """Educator-friendly explanation of heuristic models."""
    html = [
        """
    <section class="heuristics-explanation">
        <h3>What the Contextual Heuristics Represent</h3>
        <p>
            Below is a summary of the heuristics used to contextually frame defects.
        </p>

        <table class="heuristics-table">
            <thead>
                <tr>
                    <th>Heuristic</th>
                    <th>Intuition</th>
                    <th>Scale</th>
                    <th>Interpretation</th>
                </tr>
            </thead>
            <tbody>
    """
    ]
    for h in heuristics:
        html.append(f"""
            <tr>
                <td>{h["name"]}</td>
                <td>{h.get("description", "")}</td>
                <td>{"Relative" if h.get("scale", "1-5") == "-2-2" else "Absolute"}</td>
                <td>{h.get("interpretation", "")}</td>
            </tr>
        """)
    html.append("</tbody></table></section>")

    return "".join(html)


# ============================================================
# ====================  DEFECTS SECTION  =====================
# ============================================================


def render_defects_section(
    defects: list,
    question_index: str,
    is_clickable: bool = True,
    show_comment_box: bool = False,
    defect_vote_counts: Optional[None] = None,
) -> str:
    """Render all defects as cards with options for clickable, votes display, highlighting, and the comment box."""
    if not defects:
        return "<p>No defects available.</p>"

    # Determine most-voted defect for highlighting
    most_votes = 0
    if defect_vote_counts is not None:
        most_votes = max(defect_vote_counts.values()) if defect_vote_counts else 0

    html = ['<section class="defects-section">']
    html.append('<form action="defects.py?page=survey" method="post" class="defect-form">')

    for defect in defects:
        votes = defect_vote_counts.get(defect["defect id"], 0) if defect_vote_counts is not None else None
        highlight = votes == most_votes and votes > 0
        html.append(render_defect_button(defect, is_clickable=is_clickable, highlight=highlight, votes=votes))

    if show_comment_box:
        html.append(render_comment_box(disabled=not is_clickable))
    html.append(f'<input type="hidden" name="question_id" value="{question_index}">')
    html.append("</form></section>")

    return "".join(html)


def render_comment_box(disabled: bool = False) -> str:
    """Render a comment box for survey submissions."""
    attribute = ""
    instructions = "Will be submitted with the response"
    if disabled:
        attribute = "disabled"
        instructions = "Disabled for the demo"

    return f"""
    <div class="comment-section">
        <h3>Optional Comment: ({instructions})</h3>
        <textarea name="comment" id="comment" class="comment-box" rows="4" {attribute}></textarea>
    </div>
    """


def render_defect_fix_block(defect: dict) -> str:
    """Render code example and fix example for a defect."""
    html = ["<div class='defect-fix-block'>"]
    if defect.get("code example"):
        html.append(f"<pre class='code-block'>{defect['code example']}</pre>")
    if defect.get("code fix example"):
        html.append(f"<pre class='code-block'>{defect['code fix example']}</pre>")
    html.append("</div>")
    return "".join(html)


def render_defect_content(defect: dict, votes: Optional[int] = None) -> str:
    """Render name, description, examples, and optional vote counts."""
    html = [
        "<div class='defect-content-wrapper'>",
        "<div class='defect-info'>",
        f"<p><strong>{defect.get('name', '')}:</strong> {defect.get('description', '')}</p>",
    ]
    if votes is not None:
        html.append(f"<p><strong>Votes:</strong> {votes}</p>")
    html.append(render_defect_fix_block(defect))
    html.append("</div></div>")
    return "".join(html)


def render_defect_button(
    defect: dict, is_clickable: bool = True, highlight: bool = False, votes: Optional[int] = None
) -> str:
    """Render a single defect card as a button."""
    classes = ["defect-button"]
    if highlight:
        classes.append("highlighted")
    if not is_clickable:
        classes.append("unclickable")

    class_str = " ".join(classes)
    name_attr = "name='choice'" if is_clickable else ""
    value_attr = f"value='{defect.get('defect id', '')}'" if is_clickable else ""

    html = [f"<button type='submit' {name_attr} {value_attr} class='{class_str}'>"]
    html.append(render_defect_content(defect, votes=votes))
    html.append("</button>")
    return "".join(html)


# ============================================================
# =====================  PAGE WRAPPER  =======================
# ============================================================


def render_html_page(title: str, body_content: str) -> str:
    """Wrap body content in a full HTML page with head and CSS."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" href="{CSS_RELATIVE_PATH}">
</head>
<body>
{body_content}
</body>
</html>
"""


"""
"""
