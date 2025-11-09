#!C:\Python312\python.exe
"""Main entry point for the CGI script. Handles selecting the appropriate page of the survey and tracking user sessions."""

import cgi
import http.cookies
import os
import sys
import uuid
from pathlib import Path

# Import page modules
from scripts.demo import show_demo_page
from scripts.landing import show_landing_page
from scripts.results import show_results_page
from scripts.survey import show_survey_page

# --- Configuration ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "survey_data" / "ipython_0.0.0"
CSS_RELATIVE_PATH = "../css/defects.css"  # relative to /public_html

# --- Ensure responses.csv exists ---
responses_file = DATA_PATH / "responses.csv"
if not responses_file.exists():
    with open(responses_file, mode="a", newline="", encoding="utf-8") as f:
        f.write("respondent;submission id;answer\n")

# --- UTF-8 output ---
sys.stdout.reconfigure(encoding="utf-8")

# --- Handle cookies / user ID ---
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

# --- Prepare output headers ---
print("Content-Type: text/html; charset=utf-8")
print(cookie.output())
print()

# --- Determine which page to show ---
form = cgi.FieldStorage()
page = form.getvalue("page", "landing")

# Choose a dynamic title
page_titles = {
    "landing": "Survey Overview",
    "survey": "Survey Questions",
    "results": "Survey Results",
    "demo": "Demo Instructions",
}
page_title = page_titles.get(page, "Survey")

# --- HTML page wrapper ---
print(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <link rel="stylesheet" type="text/css" href="{CSS_RELATIVE_PATH}">
</head>
<body>
""")

# --- Route to correct page ---
if page == "survey":
    show_survey_page(DATA_PATH, form)
elif page == "results":
    show_results_page(DATA_PATH, form)
elif page == "demo":
    show_demo_page()
else:
    show_landing_page()

print("</body></html>")
print("</body></html>")
