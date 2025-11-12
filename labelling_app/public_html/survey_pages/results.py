"""Pages with the survey results."""

import cgi
import csv
from html import escape
from pathlib import Path

from .survey_logic import get_user_id


def results(data_path: Path, form: cgi.FieldStorage):
    """
    Display the survey results page with navigation and vote highlighting.

    - Shows each submission, its code, and the associated defects.
    - Highlights the most-voted defect.
    - Provides navigation between submissions.
    """
    # --- Determine which question to show ---
    try:
        question_index = int(form.getvalue("question_index", 0))
    except ValueError:
        question_index = 0

    # --- Load all submissions safely ---
    submissions_path = data_path / "submissions.csv"
    if not submissions_path.exists():
        print("<p>Error: submissions.csv not found.</p>")
        return

    questions = []
    with open(submissions_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        questions.extend(reader)

    if not (0 <= question_index < len(questions)):
        print("""
            <div class="survey-container">
                <div class="survey-header">
                    <button onclick="window.location.href='defects.py'" class="return-button">Exit</button>
                    <h1>Survey Results</h1>
                    <h2>No Results Found</h2>
                    <p>No questions are available.</p>
                </div>
            </div>
        """)
        return

    question = questions[question_index]

    # --- Load responses and defects ---
    responses_path = data_path / "responses.csv"
    defects_path = data_path / "defects.csv"

    defect_counts = {}
    total_votes = 0
    if responses_path.exists():
        with open(responses_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                if row.get("submission id") == question["index"]:
                    defect_id = row.get("answer")
                    defect_counts[defect_id] = defect_counts.get(defect_id, 0) + 1
                    total_votes += 1

    defects = []
    if defects_path.exists():
        with open(defects_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                if row.get("submission id") == question["index"]:
                    row["vote_count"] = defect_counts.get(row.get("defect id"), 0)
                    defects.append(row)

    sorted_defects = sorted(defects, key=lambda x: x["vote_count"], reverse=True)
    most_voted_defect = sorted_defects[0] if sorted_defects else None

    # --- Render HTML ---
    print(f"""
        <div class="survey-container">
            <div class="survey-header">
                <h1>Survey Results</h1>
                <div class="nav-buttons">
                    <button onclick="window.location.href='defects.py'" class="nav-button">Exit</button>
                    <button onclick="window.location.href='defects.py?page=results&question_index={max(0, question_index - 1)}'"
                            class="nav-button" {"disabled" if question_index == 0 else ""}>
                        Previous
                    </button>
                    <button onclick="window.location.href='defects.py?page=results&question_index={min(len(questions) - 1, question_index + 1)}'"
                            class="nav-button" {"disabled" if question_index == len(questions) - 1 else ""}>
                        Next
                    </button>
                </div>
            </div>

            <div class="survey-content">
                <div class="task-section">
                    <h3>{escape(question.get("task name", ""))}</h3>
                    <p><strong>Instructions:</strong> {escape(question.get("instructions", ""))}</p>
                    <pre class="code-block"><code>{escape(question.get("submission", ""))}</code></pre>
                </div>

                <div class="defects-section">
    """)

    if not sorted_defects:
        print("<p>No defects or responses found for this question.</p>")
    else:
        for defect in sorted_defects:
            is_most_voted = defect == most_voted_defect
            highlight_class = "highlighted" if is_most_voted else ""

            print(f"""
                <div class="defect-card {highlight_class}">
                    <div class="defect-info">
                        <p><strong>{escape(defect.get("name", ""))}:</strong> {escape(defect.get("description", ""))}</p>
                        <p><strong>Votes:</strong> {defect.get("vote_count", 0)}</p>
                    </div>
                    <div class="defect-examples">
            """)

            # Optional code examples
            if defect.get("code example"):
                print(f"<pre class='code-block'>Example:\n<code>{escape(defect['code example'])}</code></pre>")
            if defect.get("code fix example"):
                print(f"<pre class='code-block'>Fix:\n<code>{escape(defect['code fix example'])}</code></pre>")

            # Additional context
            context_text = defect.get("additional context", "").strip()
            if context_text:
                print(f"""
                    <div class="defect-context">
                        <p><strong>Additional Context:</strong> {escape(context_text)}</p>
                    </div>
                """)

            print("</div></div>")  # close defect-examples and defect-card

    print("</div></div></div>")  # close defects-section, content, container
