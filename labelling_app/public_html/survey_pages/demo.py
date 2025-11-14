"""Demo / Instructions page for the survey."""

from .utils import data_access, shared_components, survey_logic


def demo(data_path):
    """Render an instructional demo that automatically matches the survey layout."""
    questions = data_access.get_submissions(data_path)

    question = questions[0]
    defects = survey_logic.get_defects_for_submission(data_path, question["index"])
    heuristics = data_access.load_csv(data_path / "heuristics.csv")

    # ---- Render page ----
    print(render_demo_header())

    print('<div class="survey-content">')

    # Instructions / Start button aligned like feedback form
    print(render_demo_instructions())

    # Task section
    print(shared_components.render_task_section(question, defects, heuristics))

    # Defects section (unclickable)
    print(shared_components.render_survey_defects_section(defects, question["index"], is_clickable=False))

    print("</div>")  # close survey-content


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
    """Render instructions with a start button, styled like feedback form."""
    return """
    <section class="feedback-section">
        <h2>How the Survey Works</h2>

        <p>This demo shows exactly how each survey question is structured.</p>

        <p><strong>1. Review the student’s submission.</strong></p>
        <p><strong>2. Compare it with the list of defects.</strong></p>
        <p><strong>3. Choose the defect that best describes the main issue.</strong></p>

        <p>All components you see here—the task panel, context table,
        defect cards, and examples—are the same ones used in the actual survey.</p>

        <p>The only difference is that selections are disabled.</p>

        <p>When ready, click “Start the Real Survey” below.</p>
        <section class="buttons-container">
            <button onclick="window.location.href='defects.py'" class="nav-button">Back to the Landing Page</button>
            <button onclick="window.location.href='defects.py?page=survey'" class="nav-button">Start the Real Survey</button>
        </section>
    </section>
    """
