"""Demo / Instructions page for the survey."""

from .utils import data_access, shared_components, survey_logic

# ============================================================
# =========================  ROUTE  ==========================
# ============================================================


def demo(data_path) -> str:
    """Return the full demo page HTML as a string."""
    questions = data_access.get_submissions(data_path)
    if not questions:
        return "<p>No demo submissions available.</p>"

    question = questions[0]
    defects = survey_logic.get_defects_for_submission(data_path, question["index"])
    heuristics = data_access.load_csv(data_path / "heuristics.csv")

    left_column = [
        shared_components.render_task_section(question, defects, heuristics),
        shared_components.render_heuristics_section(defects, heuristics),
    ]

    right_column = [
        shared_components.render_defects_section(
            defects,
            question["index"],
            is_clickable=False,
            show_comment_box=True,
        )
    ]

    html = [
        render_demo_header(),
        render_demo_instructions(),
        shared_components.two_column_layout(left_column, right_column),
        "</div>",  # close survey-container
    ]

    return "".join(html)


# ============================================================
# ====================  PAGE COMPONENTS  =====================
# ============================================================


def render_demo_header() -> str:
    """Render the header for the demo page with a welcoming, explanatory tone."""
    return """
    <div class="survey-container">
        <header class="survey-header">
            <h1>Survey Demo & Instructions</h1>
            <p>This demo shows how a survey question will appear, using a real student submission.
            Nothing you do here will be recorded—it's just to help you get comfortable with the layout and components.</p>

            <p>Remember, the goal of the survey is to see how educators prioritize code quality defects for beginner programmers.
            In this demo, you can explore the same tools you'll use in the real survey.</p>
        </header>
    """


def render_demo_instructions() -> str:
    """Render clear and friendly instructions with navigation buttons for the demo page."""
    return """
    <section class="feedback-section">
        <h2>Survey Demo Overview</h2>

        <p>Here's what you can explore in this demo:</p>

        <ol class="demo-list">
            <li><strong>The submission:</strong> See the student's original code exactly as submitted.</li>
            <li><strong>Defects:</strong> Browse the potential code quality issues flagged in the submission.</li>
            <li><strong>Contextual considerations:</strong> Check how each defect is framed based on teaching priorities and student learning context.</li>
            <li><strong>Context table:</strong> Compare defects side by side for this submission to see which ones might deserve more attention.</li>
            <li><strong>(Note on submitting):</strong> In the real survey, clicking a defect registers your choice—but here, selections are disabled so you can explore freely.</li>
        </ol>
    
        <p>Take your time exploring. When you feel ready, proceed to the real survey to actively indicate which defects you would prioritize first.</p>

        <div class="nav-buttons">
            <button onclick="window.location.href='defects.py'" class="nav-button">Back to the Landing Page</button>
            <button onclick="window.location.href='defects.py?page=survey'" class="nav-button">Start the Real Survey</button>
        </div>
    </section>


    """
