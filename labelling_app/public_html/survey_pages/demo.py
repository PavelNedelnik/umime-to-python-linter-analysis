"""Demo / Instructions page for the survey."""


def demo():
    """Display an instructional demo showing how to complete the survey."""
    print("""
    <main class="demo-container">
        <section class="survey-header">
            <h1>Survey Demo & Instructions</h1>
            <p>
                This short demo will show you how to complete the survey.
                You will be presented with a student's code submission and a list of potential defects.
                Your task is to <strong>select the defect</strong> that you think best describes
                the main issue in the code.
            </p>
        </section>

        <section class="demo-example">
            <h2>Example Task</h2>
            <p><strong>Instructions:</strong> Identify the most relevant defect in the following code.</p>
            <pre class="code-block"><code>
def add_numbers(a, b):
    result = a + b
    print(result)
    return print(result)
            </code></pre>
        </section>

        <section class="demo-defects">
            <h3>Example Defects</h3>
            <div class="defect-button unclickable">
                <p><strong>Redundant Output:</strong> The result is printed twice unnecessarily.</p>
            </div>
            <div class="defect-button unclickable">
                <p><strong>Return Value Misuse:</strong> Returning the result of print() yields None instead of the sum.</p>
            </div>
            <div class="defect-button unclickable">
                <p><strong>Variable Naming:</strong> Variable names could be clearer but do not affect correctness.</p>
            </div>
        </section>

        <section class="demo-footer">
            <p>
                When you take the actual survey, simply click the button corresponding
                to the defect you think is most relevant.
            </p>
            <a href="defects.py?page=survey" class="nav-button large-button">Start the Real Survey</a>
            <a href="defects.py?page=landing" class="nav-button large-button">Back to Landing Page</a>
        </section>
    </main>
    """)
