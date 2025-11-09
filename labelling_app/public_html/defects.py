#!C:\Python312\python.exe

"""Main entry point for the CGI script. Handles selecting the appropriate page of the survey and tracking user sessions."""

import cgi
import http.cookies
import os
import sys
import uuid
from pathlib import Path

from scripts.landing import show_landing_page
from scripts.results import show_results_page
from scripts.survey import show_survey_page

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "survey_data" / "ipython_0.0.0"
CSS_PATH = BASE_DIR / "css/defects.css"

# Ensure the file to collect responses exists
with open(DATA_PATH / "responses.csv", mode="a", newline="", encoding="utf-8"):
    pass

# Ensure UTF-8 encoding
sys.stdout.reconfigure(encoding="utf-8")

# Initialize a cookie to track the user sessions
cookie = http.cookies.SimpleCookie()
if "HTTP_COOKIE" in os.environ:
    cookie.load(os.environ["HTTP_COOKIE"])

if "user_id" in cookie:
    user_id = cookie["user_id"].value
else:
    user_id = str(uuid.uuid4())  # generate a random user id
    cookie["user_id"] = user_id
    cookie["user_id"]["path"] = "/"
    cookie["user_id"]["max-age"] = 3600  # cookie lasts for 1 hour

# Header for the CGI script
print("Content-Type: text/html; charset=utf-8")
print(cookie.output())
print()

# Get the page parameter to determine which part of the survey to show
form = cgi.FieldStorage()
page = form.getvalue("page", "landing")

print(f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Survey Results</title>
        <link rel="stylesheet" type="text/css" href="/labelling_app/css/defects.css">
    </head>
    <body>""")

if page == "survey":
    show_survey_page(DATA_PATH, form)
elif page == "results":
    show_results_page(DATA_PATH, form)
else:
    show_landing_page()

print("""</body></html>""")
