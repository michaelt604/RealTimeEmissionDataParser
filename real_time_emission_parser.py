from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import datetime
import csv
import re
import time
import os
import math
import logging
import traceback
import unicodedata
import signal
import sys

URL = "https://www.ineossarnia.com/real-time-emission-data"
OUTPUT_CSV = "air_quality_log.csv"
ERROR_LOG = "scraper_error.log"

# Setup logging for errors
logging.basicConfig(filename=ERROR_LOG, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def signal_handler(sig, frame):
    print("\n[INFO] Exiting gracefully.")
    sys.exit(0)
    
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
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.c-table-container table'))
        )   #Smart selenium wait for the table to load
        html = driver.page_source
    finally:
        driver.quit()

    return html

def parse_benzene_values(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.select_one('.c-table-container table')
    rows = table.select('tbody tr')

    values = []
    last_update_times = set()

    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 4:
            location = cols[0].text.strip()
            compound = cols[1].text.strip()
            value_str = cols[2].text.strip()
            last_update_str = cols[3].text.strip()
            last_update_str = unicodedata.normalize('NFKC', last_update_str)
            last_update_str = last_update_str.replace('\u202f', ' ')
            
            if compound.lower() == "benzene" and location.startswith("#"):
                match = re.search(r"[\d.]+", value_str)
                if match:
                    values.append(float(match.group()))
                    last_update_times.add(last_update_str)

    if len(values) != 5:
        return None, None

    # Check if all last update timestamps are same
    if len(last_update_times) == 1:
        last_update = last_update_times.pop()
    else:
        last_update = "; ".join(sorted(last_update_times))  # fallback if different

    return values, last_update

def save_to_csv(values, last_update):
    file_exists = os.path.isfile(OUTPUT_CSV)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    headers = [
        "TimeStamp",
        "Station 1 (ug/m³)",
        "Station 2 (ug/m³)",
        "Station 3 (ug/m³)",
        "Station 4 (ug/m³)",
        "Station 5 (ug/m³)",
        "Last Update"
    ]

    with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow([timestamp] + values + [last_update])

    print(f"[SAVED CSV] {timestamp}: {values} | Last Update: {last_update}")

def main():
    try:
        html = fetch_rendered_html()
        values, last_update = parse_benzene_values(html)
        if values is not None:
            save_to_csv(values, last_update)
        else:
            print("[WARN] Did not find exactly 5 benzene values.")
            logging.error("Did not find exactly 5 benzene values.")
    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"[ERROR] Exception occurred:\n{error_msg}")
        logging.error(error_msg)

def run_every_five_minutes():
    print("[INFO] Starting 5-minute polling...")
    while True:
        now = datetime.datetime.now()

        # Floor to the current 5-minute block, then add 5 to ensure it's in the future
        minute_block = now.minute - (now.minute % 5)
        next_run = now.replace(minute=minute_block, second=0, microsecond=0) + datetime.timedelta(minutes=5)
        wait_seconds = max(0, (next_run - now).total_seconds())

        print(f"[WAITING] Sleeping {int(wait_seconds)}s → Next run at {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(wait_seconds)

        main()

def safe_run_forever():
    print("[INFO] RealTimeEmissionDataParser starting (auto-restarts on crash)...")
    while True:
        try:
            run_every_five_minutes()
        except Exception:
            error_msg = traceback.format_exc()
            print(f"[ERROR] Script crashed:\n{error_msg}")
            logging.error(error_msg)
            print("[RESTARTING] Waiting 30 seconds before retrying...")
            time.sleep(30)

if __name__ == "__main__":
    safe_run_forever()

signal.signal(signal.SIGINT, signal_handler)
