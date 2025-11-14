"""Shared rendering components for survey pages."""

from .survey_logic import map_score

# -------------------- Task Section --------------------


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
    html.append(render_heuristic_explanation())
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


def render_heuristic_explanation() -> str:
    """Educator-friendly explanation of heuristic models, displayed below the table."""
    return """
    <section class="heuristics-explanation">
        <h3>How the Models Work</h3>
        <p>
            Defects are prioritized using patterns from the assignment, the student’s history,
            and educator-rated severity.
        </p>

        <table class="heuristics-table">
            <thead>
                <tr><th>Heuristic</th><th>Meaning</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td>Task: Common Defects</td>
                    <td>Frequent errors across students on this task</td>
                </tr>
                <tr>
                    <td>Task: Characteristic Defects</td>
                    <td>Unique mistakes tied to this specific task</td>
                </tr>
                <tr>
                    <td>Student: Frequency</td>
                    <td>Persistent individual mistakes</td>
                </tr>
                <tr>
                    <td>Student: Characteristic Defect</td>
                    <td>Personal learning gaps</td>
                </tr>
                <tr>
                    <td>Student: Encountered Before</td>
                    <td>Reinforces previously seen mistakes</td>
                </tr>
                <tr>
                    <td>Defect Multiplicity</td>
                    <td>Indicates fundamental misunderstandings</td>
                </tr>
                <tr>
                    <td>Baseline: Severity</td>
                    <td>Overall seriousness of the defect</td>
                </tr>
            </tbody>
        </table>
    </section>
    """


# -------------------- Defect Section --------------------


def render_comment_box(disabled: bool = False) -> str:
    """Render a comment box to be included in the survey defects section."""
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


def render_defect_content(defect: dict, votes: int | None = None) -> str:
    """Render the inner content of a defect card: name, description, examples, etc."""
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
    defect: dict, is_clickable: bool = True, highlight: bool = False, votes: int | None = None
) -> str:
    """Render a single defect as a button."""
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


def render_survey_defects_section(defects: list, question_index: str, is_clickable: bool = True) -> str:
    """Render defects as selectable buttons with an attached comment box."""
    if not defects:
        return "<p>No defects available.</p>"

    html = ['<section class="defects-section">']
    html.append('<form action="defects.py?page=survey" method="post" class="defect-form">')

    for defect in defects:
        html.append(render_defect_button(defect, is_clickable=is_clickable))

    # Add comment box
    html.append(render_comment_box(disabled=not is_clickable))
    html.append(f'<input type="hidden" name="question_id" value="{question_index}">')
    html.append("</form></section>")

    return "".join(html)
