#!C:\Python312\python.exe
"""
Main entry point for the CGI script.

Handles selecting the appropriate page of the survey and tracking user sessions.
"""

import cgi
import http.cookies
import os
import sys
import uuid
from pathlib import Path

BASE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BASE, "survey_pages"))
sys.path.insert(0, os.path.join(BASE, "survey_pages", "utils"))

from survey_pages import demo, landing, results, survey
from survey_pages.utils.shared_components import render_html_page

# ============================================================
# ====================  CONFIGURATION  =======================
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "survey_data" / "production"

# ============================================================
# ====================  DATA FILE SETUP  =====================
# ============================================================

responses_file = DATA_PATH / "responses.csv"
if not responses_file.exists():
    with open(responses_file, mode="a", newline="", encoding="utf-8") as f:
        f.write("timestamp;respondent;submission id;answer;comment\n")

feedback_file = DATA_PATH / "feedback.csv"
if not feedback_file.exists():
    with open(feedback_file, mode="a", newline="", encoding="utf-8") as f:
        f.write("timestamp;respondent;feedback\n")

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")


# ============================================================
# =====================  COOKIE HANDLING  ====================
# ============================================================

cookie = http.cookies.SimpleCookie()
if "HTTP_COOKIE" in os.environ:
    cookie.load(os.environ["HTTP_COOKIE"])

if "user_id" in cookie:
    user_id = cookie["user_id"].value
else:
    user_id = str(uuid.uuid4())
    cookie["user_id"] = user_id
    cookie["user_id"]["path"] = "/"
    cookie["user_id"]["max-age"] = 3600  # 1 hour


# ============================================================
# ==================  PAGE SELECTION LOGIC  ==================
# ============================================================

form = cgi.FieldStorage()
page = form.getvalue("page", "landing")

page_titles = {
    "landing": "Survey Overview",
    "survey": "Survey Questions",
    "results": "Survey Results",
    "demo": "Demo Instructions",
}
page_title = page_titles.get(page, "Survey")


# ============================================================
# =======================  HTML OUTPUT  =======================
# ============================================================

# headers:
print("Content-Type: text/html; charset=utf-8")
print(cookie.output())
print()

# Select the appropriate page
content = landing()
if page == "survey":
    content = survey(DATA_PATH, form)
elif page == "results":
    content = results(DATA_PATH, form)
elif page == "demo":
    content = demo(DATA_PATH)

# Wrap content in a full HTML page with head and CSS
print(render_html_page(page_title, content))
