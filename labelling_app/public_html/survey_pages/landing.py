"""Landing page for the survey."""


def landing() -> str:
    """Return the landing page HTML content as a string."""
    return """
    <div class="survey-container">
        <header class="survey-header">
            <h1>Beginner Code Quality Defects Survey</h1>
            <p>
                Welcome! This survey gathers feedback from educators and reviewers
                about <strong>common code quality defects</strong> in beginner-level programming submissions.
            </p>
            <p>
                Your insights will help improve automated tools—like linters and tutoring systems—prioritize messages for students.
            </p>
        </header>

        <main class="landing-main">
            <section class="buttons-container">
                <a href="defects.py?page=survey" class="nav-button large-button" aria-label="Start the Survey">Start the Survey</a>
                <a href="defects.py?page=demo" class="nav-button large-button" aria-label="View Demo">View Example / Demo</a>
                <a href="defects.py?page=results" class="nav-button large-button" aria-label="See Results">See Results</a>
            </section>
        </main>
    </div>
    """
