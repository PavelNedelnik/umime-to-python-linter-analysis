"""
Shared rendering components for survey pages.

Includes:
- Task section
- Context table
- Comment box
"""

from .survey_logic import map_score


def render_task_section(question: dict, defects: list, heuristics: list) -> str:
    """Render the task section: instructions, code, context table."""
    html = [
        f"""
        <section class="task-section">
            <h3>({question["index"]}) {question["task name"]}</h3>
            <p><strong>Instructions:</strong> {question["instructions"]}</p>
            <pre class="code-block"><code>{question["submission"]}</code></pre>
        """
    ]
    html.append('<div class="context-section"><h3>Defect Context by Heuristic</h3>')
    html.append(render_context_table(defects, heuristics))
    html.append("</div></section>")
    return "".join(html)


def render_context_table(defects: list, heuristics: list) -> str:
    """Render an HTML table showing heuristic context for each defect."""
    if not defects or not heuristics:
        return "<p>No context available.</p>"

    html = ['<table class="heuristics-table" style="width:100%; border-collapse: collapse;">']
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

    html.append("</tbody></table>")
    return "".join(html)


def render_comment_box() -> str:
    """Render a comment box to be included in the survey defects section."""
    return """
    <div class="comment-section">
        <h3>Optional Comment: (Will be submitted with the response)</h3>
        <textarea name="comment" id="comment" class="comment-box" rows="4"></textarea>
    </div>
    """


def render_defect_content(defect: dict) -> str:
    """
    Render the content inside a defect button: description, example, and fix code.

    :param defect: Defect dictionary.
    :return: HTML string for the inner content of a defect
    """
    html = [
        "<div class='defect-content-wrapper'>",
        "<div class='defect-info'>",
        f"<p><strong>{defect.get('name', '')}:</strong> {defect.get('description', '')}</p>",
        "<div class='defect-fix-block'>",
    ]

    if defect.get("code example"):
        html.append(f"<pre class='code-block'>{defect['code example']}</pre>")
    if defect.get("code fix example"):
        html.append(f"<pre class='code-block'>{defect['code fix example']}</pre>")

    html.append("</div></div></div>")  # Close blocks
    return "".join(html)


def render_defect_button(defect: dict, is_clickable: bool = True, highlight: bool = False) -> str:
    """
    Render a single defect as a button (survey) or read-only (results).

    :param defect: Defect dictionary
    :param is_clickable: True for survey buttons, False for results
    :param highlight: True to highlight (most voted) defect
    :return: HTML string
    """
    classes = ["defect-button"]
    if highlight:
        classes.append("highlighted")
    if not is_clickable:
        classes.append("unclickable")

    class_str = " ".join(classes)
    name_attr = f"name='choice'" if is_clickable else ""
    value_attr = f"value='{defect.get('defect id', '')}'" if is_clickable else ""

    html = [f"<button type='submit' {name_attr} {value_attr} class='{class_str}'>"]
    html.append(render_defect_content(defect))
    html.append("</button>")
    return "".join(html)
