import hmac
import os
import time
from datetime import datetime, timedelta, timezone

import lxml.html.clean
import pandas
import requests

SOURCE_URL = "https://docs.google.com/spreadsheets/u/1/d/e/2PACX-1vSJ-xfssimBAcxkv2-yf1tjW7klzc2grFfpR3HZnUaYxMmOi6V7YLSd8vUyOF3sD54CFhPkVbRD1Uz8/pubhtml/sheet?headers=false&gid=652332328"

LOGGER_DEPLOYMENT_ID = os.environ.get("LOGGER_DEPLOYMENT_ID")
LOGGER_SECRET = os.environ.get("LOGGER_SECRET")
LOGGER_URL = "https://script.google.com/macros/s/{deploymentID}/exec?date={date}&studentCases={studentCases}&staffCases={staffCases}&sig={sig}&time={time}"

PST_TIME = datetime.now(timezone(-timedelta(hours=8)))
FILENAME_HTML = PST_TIME.strftime("data/html/%Y-%m-%d.html")
FILENAME_CSV = PST_TIME.strftime("data/csv/%Y-%m-%d.csv")
FILENAME_DAILY = "data/daily.csv"

cleaner = lxml.html.clean.Cleaner(
    style=True, page_structure=False
)


def main():
    print("downloading file")
    resp = requests.get(SOURCE_URL)
    if resp.status_code != 200:
        print("error downloading file")
        return

    html_content = cleaner.clean_html(resp.text)
    with open(FILENAME_HTML, "w") as f:
        f.write(html_content)
    print("saved file")

    print("converting to csv")
    dfs = pandas.read_html(html_content, skiprows=3, index_col=0, header=(0, 1))
    csv = dfs[0].to_csv(index=False)
    with open(FILENAME_CSV, "w") as f:
        f.write(csv)
    with open(FILENAME_DAILY, "w") as f:
        f.write(csv)
    print("saved csv")

    print("logging to spreadsheet")
    df = pandas.read_html(html_content, skiprows=3, index_col=1, header=(0, 1))[0]
    current_month_year = PST_TIME.strftime("%B %Y")
    student_cases = df.get((current_month_year, "Students"))
    staff_cases = df.get((current_month_year, "Staff"))

    if student_cases is None or staff_cases is None:
        print("error finding cases")
        return

    current_date = PST_TIME.strftime("%m/%d/%Y")
    student_case_numbers = student_cases.get("DISTRICT TOTAL:")
    staff_case_numbers = staff_cases.get("DISTRICT TOTAL:")
    timestamp = round(time.time())
    signature = hmac.new(
        LOGGER_SECRET.encode(),
        f"{timestamp}|{current_date}|{student_case_numbers}|{staff_case_numbers}".encode(),
        "sha256",
    ).hexdigest()

    url = LOGGER_URL.format(
        deploymentID=LOGGER_DEPLOYMENT_ID,
        date=current_date,
        studentCases=student_case_numbers,
        staffCases=staff_case_numbers,
        sig=signature,
        time=timestamp,
    )
    logger_resp = requests.get(url)

    print(
        "logged to spreadsheet"
        if logger_resp.status_code == 200
        else "error logging to spreadsheet"
    )


main()
