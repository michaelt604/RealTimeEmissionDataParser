from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import datetime
import csv
import re
import time
import os
import math
import traceback

URL = "https://www.ineossarnia.com/real-time-emission-data"
OUTPUT_CSV = "air_quality_log.csv"

def fetch_rendered_html():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--log-level=3')  # Suppress ChromeDriver logs
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(URL)
        time.sleep(5)  # Wait for JS to load
        html = driver.page_source
    finally:
        driver.quit()

    return html

def parse_benzene_values(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.select_one('.c-table-container table')
    rows = table.select('tbody tr')

    values = []
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 4:
            location = cols[0].text.strip()
            compound = cols[1].text.strip()
            value_str = cols[2].text.strip()

            if compound.lower() == "benzene" and location.startswith("#"):
                match = re.search(r"[\d.]+", value_str)
                if match:
                    values.append(float(match.group()))

    return values if len(values) == 5 else None

def save_to_csv(values):
    file_exists = os.path.isfile(OUTPUT_CSV)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(OUTPUT_CSV, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["TimeStamp", "Station 1", "Station 2", "Station 3", "Station 4", "Station 5"])
        writer.writerow([timestamp] + values)

    print(f"[SAVED CSV] {timestamp}: {values}")

def main():
    html = fetch_rendered_html()
    values = parse_benzene_values(html)
    if values:
        save_to_csv(values)
    else:
        print("[WARN] Did not find exactly 5 benzene values.")

def run_every_five_minutes():
    print("[INFO] Starting 5-minute polling...")
    while True:
        now = datetime.datetime.now()

        # Floor to the current 5-minute block, then add 5 to ensure it's in the future
        minute_block = now.minute - (now.minute % 5)
        next_run = now.replace(minute=minute_block, second=0, microsecond=0) + datetime.timedelta(minutes=5)

        wait_seconds = (next_run - now).total_seconds()
        wait_seconds = max(0, wait_seconds)

        print(f"[WAITING] Sleeping {int(wait_seconds)}s → Next run at {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(wait_seconds)

        main()

def safe_run_forever():
    print("[INFO] Resilient scraper starting (auto-restarts on crash)...")
    while True:
        try:
            run_every_five_minutes()
        except Exception as e:
            print(f"[ERROR] Script crashed:\n{traceback.format_exc()}")
            print("[RESTARTING] Waiting 30 seconds before retrying...")
            time.sleep(30)

if __name__ == "__main__":
    safe_run_forever()