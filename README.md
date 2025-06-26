# RealTimeEmissionDataParser

Pulls and saves benzene pollution ratings from [INEOS Sarnia real-time emission data](https://www.ineossarnia.com/real-time-emission-data) for historical tracking.

---

## Features

- Scrapes benzene values from 5 monitoring stations every 5 minutes
- Saves timestamped data to a CSV file (`air_quality_log.csv`)
- Logs errors and exceptions to `scraper_error.log`
- Resilient: auto-restarts on crash
- Runs headlessly using Selenium and ChromeDriver
- UTF-8 encoded CSV with units included
- Includes last update timestamp from source data

---

## Usage

### Requirements

- Windows 10+ (tested)
- No Python installation needed if using the prebuilt `.exe`
- Internet connection for live scraping
- Chrome browser installed (required by ChromeDriver)

### Running the program

#### Using the `.exe` release

1. Download the latest `.exe` from [Releases](https://github.com/yourusername/RealTimeEmissionDataParser/releases)
2. Run the `.exe` (double-click or via terminal)
3. The scraper runs indefinitely, polling every 5 minutes
4. Press `Ctrl+C` in console or close window to stop

#### Running from source (Python)

1. Clone this repo
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
