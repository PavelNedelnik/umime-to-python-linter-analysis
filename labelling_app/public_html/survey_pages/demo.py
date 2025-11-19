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
            <p>
                Welcome! This demo shows you exactly how a survey question will appear.
                You'll see a real student submission along with the potential defects identified in it.
            </p>
            <p>
                Your goal is to understand the layout, the context tables, and the defect cards.
                In the real survey, clicking a defect will submit your answer—but here, you can freely explore without affecting anything.
            </p>
        </header>
    """


def render_demo_instructions() -> str:
    """Render clear and friendly instructions with navigation buttons for the demo page."""
    return """
    <section class="feedback-section">
        <h2>Survey Demo Overview</h2>

        <p>This demo shows how a survey question will appear using a real student submission. 
        Nothing you do here will be recorded—it's just for getting familiar with the layout and components.</p>

        <p>In this demo, you can explore:</p>
        <ul>
            <li><strong>The submission:</strong> See the student's code as it was submitted.</li>
            <li><strong>Defects:</strong> Browse the potential issues identified in the code.</li>
            <li><strong>Heuristics:</strong> Understand how defects are contextualized based on common mistakes and educational priorities.</li>
            <li><strong>Context table:</strong> Compare this submission to others and see the broader learning context.</li>
            <li><strong>Note:</strong> In the real survey, clicking a defect will submit your answer—but selections are disabled here.</li>
        </ul>

        <p>Take your time exploring. When ready, you can proceed to the real survey to actively select which defect you would highlight first.</p>

        <div class="nav-buttons">
            <button onclick="window.location.href='defects.py'" class="nav-button">Back to the Landing Page</button>
            <button onclick="window.location.href='defects.py?page=survey'" class="nav-button">Start the Real Survey</button>
        </div>
    </section>
    """
