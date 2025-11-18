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

    html = [
        render_demo_header(),
        '<div class="survey-content">',
        render_demo_instructions(),
        shared_components.render_task_section(question, defects, heuristics),
        shared_components.render_survey_defects_section(defects, question["index"], is_clickable=False),
        "</div>",  # close survey-content
    ]

    return "".join(html)


# ============================================================
# ====================  PAGE COMPONENTS  =====================
# ============================================================


def render_demo_header() -> str:
    """Render the header for the demo page."""
    return """
    <div class="survey-container">
        <header class="survey-header">
            <h1>Survey Demo & Instructions</h1>
            <p>
                This demo uses a real student submission. Your task is to select
                the defect that best describes the main issue in the code.
            </p>
        </header>
    """


def render_demo_instructions() -> str:
    """Render instructions and navigation buttons."""
    return """
    <section class="feedback-section">
        <h2>How the Survey Works</h2>

        <p>This demo shows exactly how each survey question is structured.</p>

        <p><strong>1. Review the student’s submission.</strong></p>
        <p><strong>2. Compare it with the list of defects.</strong></p>
        <p><strong>3. Choose the defect that best describes the main issue.</strong></p>

        <p>All components here—the task panel, context table, and defect cards—are
        the same ones used in the actual survey. The only difference is that selections are disabled.</p>

        <section class="buttons-container">
            <button onclick="window.location.href='defects.py'" class="nav-button">Back to the Landing Page</button>
            <button onclick="window.location.href='defects.py?page=survey'" class="nav-button">Start the Real Survey</button>
        </section>
    </section>
    """
