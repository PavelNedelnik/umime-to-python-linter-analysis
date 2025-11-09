"""Landing page for the survey."""


def show_landing_page():
    """Display the landing page HTML."""
    print("""
    <main class="landing-container">
        <section class="survey-header">
            <h1>Beginner Code Quality Defects Survey</h1>
            <p>
                Welcome! This survey gathers feedback from educators and reviewers
                about <strong>common code quality defects</strong> that students encounter
                in beginner-level programming submissions.
            </p>
            <p>
                Your insights will help improve how automated tools — like linters and
                tutoring systems — prioritize messages for students.
            </p>
        </section>

        <section class="buttons-container">
            <a href="defects.py?page=survey" class="nav-button large-button">Start the Survey</a>
            <a href="defects.py?page=demo" class="nav-button large-button">View Example / Demo</a>
            <a href="defects.py?page=results" class="nav-button large-button">See Results</a>
        </section>
    </main>
    """)
