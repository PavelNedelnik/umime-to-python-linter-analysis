"""Landing page for the survey."""


def landing() -> str:
    """Return the landing page HTML content as a string."""
    return """
    <div class="survey-container">
        <header class="survey-header">
            <h1>Exploring Feedback for Beginner Programmers</h1>

            <div class="landing-narrow">
                <h2 class="mini-heading">What This Survey Is About</h2>
                <p>
                    <strong>Welcome!</strong> This survey is part of a research project on how automated tools
                    can give more useful feedback to students learning to code.
                </p>

                <p>
                    You'll see short beginner-level code submissions along with a set of
                    common code-quality issues. Your task is to indicate which issues you
                    would focus on first when giving feedback. There's no “right” answer—
                    we're interested in your perspective.
                </p>
            </div>

            <div class="landing-narrow">
                <h2 class="mini-heading">Why Context Matters</h2>
                <p>
                    A feature you'll use throughout the survey is the
                    <strong>Context Table</strong>. It summarizes some of the
                    considerations educators typically weigh when reviewing student work.
                    We're especially interested in how this context shapes your priorities.
                </p>
            </div>

            <div class="landing-narrow">
                <div class="left-text">
                    <h2 class="mini-heading">Before You Start</h2>
                    <p>
                        If you'd like, you can first explore the <strong>demo</strong> to
                        get a feel for the layout and how the survey works before starting.
                    </p>
                    <p>
                        Your responses will help us understand how educators naturally
                        prioritize feedback, and will be used to improve tools that support
                        programming instruction.
                    </p>
                    <p>
                        The survey is completely anonymous and contains 70 questions.
                        However, you can stop at any point if you need to.
                    </p>
                </div>
            </div>
        </header>

        <main class="landing-main">
            <section class="buttons-container">
                <a href="defects.py?page=survey" class="nav-button large-button">Start the Survey</a>
                <a href="defects.py?page=demo" class="nav-button large-button">Try the Demo</a>
                <a href="defects.py?page=results" class="nav-button large-button">See Results</a>
            </section>
        </main>
    </div>

    """
