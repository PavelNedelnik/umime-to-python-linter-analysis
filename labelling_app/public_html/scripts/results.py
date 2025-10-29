"""Pages with the survey results."""

import cgi
import csv
from pathlib import Path

from .survey_logic import get_user_id


def show_results_page(data_path: Path, form: cgi.FieldStorage):
    """Display the survey results with navigation and vote-based highlighting."""
    question_index = form.getvalue("question_index", 0)
    question_index = int(question_index)

    questions = []
    with open(f"{data_path}/submissions.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            questions.append(row)

    if 0 <= question_index < len(questions):
        question = questions[question_index]

        # Get defect statistics
        defect_counts = {}
        total_votes = 0
        with open(data_path / "responses.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                if row["submission id"] == question["index"]:
                    defect_counts[row["answer"]] = defect_counts.get(row["answer"], 0) + 1
                    total_votes += 1

        # Get corresponding defects
        defects = []
        with open(data_path / "defects.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                if row["submission id"] == question["index"]:
                    row["vote_count"] = defect_counts.get(row["defect id"], 0)
                    defects.append(row)

        # Sort defects by vote count in descending order
        sorted_defects = sorted(defects, key=lambda x: x["vote_count"], reverse=True)
        most_voted_defect = sorted_defects[0] if sorted_defects else None

        print(f"""
            <div class="survey-container">
                <div class="survey-header">
                    <h1>Survey Results</h1>
                <button onclick="window.location.href='defects.py'" class="nav-button">Exit</button>
                <button onclick="window.location.href='defects.py?page=results&question_index={max(0, question_index - 1)}'" class="nav-button" {"disabled" if question_index == 0 else ""}>Previous</button>
                <button onclick="window.location.href='defects.py?page=results&question_index={min(len(questions) - 1, question_index + 1)}'" class="nav-button" {"disabled" if question_index == len(questions) - 1 else ""}>Next</button>
                </div>
                <div class="survey-content">
                    <div class="task-section">
                        <h3>{question["task name"]}</h3>
                        <p><strong>Instructions:</strong> {question["instructions"]}</p>
                        <pre class="code-block"><code>{question["submission"]}</code></pre>
                    </div>
                    <div class="defects-section">
                        <form>
        """)

        # Defect section with vote count and highlight the most voted defect
        for defect in sorted_defects:
            # Determine the style for the most voted defect
            is_most_voted = defect == most_voted_defect
            highlight_class = "highlighted" if is_most_voted else ""

            print(f"""
                        <button type='submit' class='defect-button {highlight_class} unclickable'>
                            <div class="defect-content">
                                <p><strong>{defect["name"]}: </strong>{defect["description"]}</p>
                                <p><strong>Votes:</strong> {defect["vote_count"]}</p>
                                <div class="defect-fix-block">
            """)
            if defect["code example"]:
                print(f'<pre class="code-block">Example:\n<code>{defect["code example"]}</code></pre>')
            if defect["code fix example"]:
                print(f'<pre class="code-block">Fix:\n<code>{defect["code fix example"]}</code></pre>')
            context_text = defect["additional context"]
            if context_text:
                print(f"""
                            </div>
                            <div class="defect-context">
                                <p><strong>Additional Context:</strong> {context_text}</p>
                            </div>
                """)
            else:
                print("</div>")

            print("""
                    </div>
                </button>
            """)
    else:
        print(f"""
            <div class="survey-container">
                <div class="survey-header">
                    <button onclick="window.location.href='defects.py'" class="return-button">Exit</button>
                    <h1>Survey Results</h1>
                    <h2>No Results Found</h2>
                    <p>No questions are available.</p>
                </div>
            </div>
        """)
