"""Landing page for the survey."""


def show_landing_page():
    """Display the landing page HTML."""
    print("""
        <div class="landing-container">
            <div class="survey-header">
                <h1>Beginner Code Quality Defects Survey</h1>
                <p>This survey is designed to gather feedback from educators about common code quality defects that students encounter when writing beginner-level code.</p>
                <p>Your feedback will help shape how automated tools like linters prioritize presenting messages to the user.</p>
            </div>
            <div class="buttons-container">
                <!-- Button to participate in the survey -->
                <a href="defects.py?page=survey" class="button-link">
                    <button type="button" class="button">Participate in the Survey</button>
                </a>
                <!-- Button to view the results -->
                <a href="defects.py?page=results" class="button-link">
                    <button type="button" class="button">See Results</button>
                </a>
            </div>
        </div>
""")
