"""Pages with the survey questions."""

import cgi
import csv
import random
from pathlib import Path

from .survey_logic import get_unanswered_questions, get_user_id, save_answer


def show_survey_page(data_path: Path, form: cgi.FieldStorage):
    """Display a page with one of the survey questions and record the answer."""
    user_choice = form.getvalue("choice")
    question_id = form.getvalue("question_id")

    user_id = get_user_id()

    # Record the previous answer
    if user_choice:
        save_answer(data_path, user_id, question_id, user_choice)

    # Get all unanswered questions
    questions = get_unanswered_questions(data_path, user_id)

    if questions:
        print(f"""<div class="survey-container">
                <div class="survey-header">
                    <h1>Beginner Code Quality Defects</h1>
                    <p>Analyze the student’s submission and select the most relevant defect (the defect you would explain to the student at this point). Please, pay particular attention to the Additional Context section.</p>
                <button onclick="window.location.href='defects.py'" class="nav-button">Exit</button>
                </div>
        """)
        # TODO: use a better than random selection
        question = random.choice(questions)

        # Get corresponding defects
        defects = []
        with open(data_path / "defects.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                if row["submission id"] == question["index"]:
                    defects.append(row)

        # Task section
        print(f"""
            <div class="survey-content">
                <div class="task-section">
                    <h3>({question["index"]}) {question["task name"]}</h3>
                    <p><strong>Instructions:</strong> {question["instructions"]}</p>
                    <pre class="code-block"><code>{question["submission"]}</code></pre>
                </div>

                <div class="defects-section">
                    <form action='defects.py?page=survey' method='post' class="defect-form">
        """)

        # Defect section
        for defect in defects:
            print(f"""
                <button type='submit' name='choice' value='{defect["defect id"]}' class='defect-button'>
                    <div class="defect-content-wrapper">
                        <div class="defect-info">
                            <p><strong>{defect["name"]}:</strong> {defect["description"]}</p>
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
                print("</div>")  # closes defect-fix-block

            print("""
                    </div>
                </button>
            """)

        print(f"""
                        <input type='hidden' name='question_id' value='{question["index"]}'>
                    </form>
                </div>
        """)

    else:
        # Thank you page
        print(f"""<div class="survey-container">
                <div class="survey-header">
                    <button onclick="window.location.href='defects.py'" class="nav-button">Exit</button>
                    <h1>Beginner Code Quality Defects</h1>
                    <h2>Thank you!</h2>
                    <p>You have answered all the questions in the database.</p>
                    </div>
                </div>
        """)
