import os
from datetime import datetime, timedelta, timezone

import pandas
import requests

SOURCE_URL = "https://docs.google.com/spreadsheets/u/1/d/e/2PACX-1vSJ-xfssimBAcxkv2-yf1tjW7klzc2grFfpR3HZnUaYxMmOi6V7YLSd8vUyOF3sD54CFhPkVbRD1Uz8/pubhtml/sheet?headers=false&gid=652332328"

PST_TIME = datetime.now(timezone(-timedelta(hours=8)))
FILENAME_HTML = PST_TIME.strftime("data/html/%Y-%m-%d.html")
FILENAME_CSV = PST_TIME.strftime("data/csv/%Y-%m-%d.csv")
FILENAME_DAILY = "data/daily.csv"


def main():
    print("downloading file")
    resp = requests.get(SOURCE_URL)
    if resp.status_code != 200:
        print("error downloading file")
        return

    html_content = resp.text
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


main()
