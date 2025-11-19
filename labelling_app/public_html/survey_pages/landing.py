"""Landing page for the survey."""


def landing() -> str:
    """Return the landing page HTML content as a string."""
    return """
    <div class="survey-container">
        <header class="survey-header">
            <h1>Exploring Feedback for Beginner Programmers</h1>

            <p>
                Welcome! This survey is part of a research project on how automated tools
                can give more useful feedback to students learning to code.
            </p>

            <p>
                You will see short beginner-level code submissions along with a set of
                common code-quality issues. Your task is to indicate which issues you
                would focus on first when giving feedback. There's no “right” answer— 
                we're interested in your perspective as an educator.
            </p>

            <p>
                A key feature you'll use throughout the survey is the <strong>Context Table</strong>.
                This table presents a summary of some of the contextual considerations educators
                typicaly weigh when giving feedback. We're especially interested in how context
                helps you decide which defects to prioritize.
            </p>

            <p>
                If you'd like, you can first explore the <strong>demo</strong> to get a feel
                for the layout and how the survey works before starting.
            </p>

            <p>
                Your responses will be used to better understand how educators prioritize
                code quality feedback. The data will be aggregated for research purposes
                and help improve tools that support teaching programming.
            </p>

            <p>
                The survey is completely anonymous and contains 70 questions. However, you can stop
                at any point if you need to.
            </p>

        </header>

        <main class="landing-main">
            <section class="buttons-container">
                <a href="defects.py?page=survey" class="nav-button large-button" aria-label="Start the Survey">Start the Survey</a>
                <a href="defects.py?page=demo" class="nav-button large-button" aria-label="View Demo">Try the Demo</a>
                <a href="defects.py?page=results" class="nav-button large-button" aria-label="See Results">See Results</a>
            </section>
        </main>
    </div>
    """
