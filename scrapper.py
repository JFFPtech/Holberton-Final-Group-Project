import requests
from bs4 import BeautifulSoup
import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
import argparse
import logging
import sys
import psycopg2
import json
from datetime import timedelta

# Setup logging for both file and console
logging.basicConfig(filename='scraping.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

pg_config = config['postgres']

parser = argparse.ArgumentParser(description='Webscraper')
parser.add_argument('--url', required=True, help='URL of the website to scrape')
parser.add_argument('--output', required=True, help='Output file storing the data')
args = parser.parse_args()

URL = args.url
output_file = args.output

# Determine the schedule interval
schedule_interval = config.get('schedule_interval')
if schedule_interval:
    if schedule_interval.lower() == "daily":
        schedule_interval = timedelta(days=1).total_seconds()
    else:
        schedule_interval = int(schedule_interval)  # assuming seconds if not "daily"
else:
    schedule_interval = None  # No interval provided

# Function to scrape data
def scrape_data():
    try:
        response = requests.get(URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        data = []
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            data.append({'type': 'heading', 'text': heading.text.strip()})
        for paragraph in soup.find_all('p'):
            data.append({'type': 'paragraph', 'text': paragraph.text.strip()})
        logging.info("Data extraction successful.")


        if data:
            df = pd.DataFrame(data)
            df.to_csv(output_file, index=False)
            
            connection = psycopg2.connect(**pg_config)
            cursor = connection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS ScrapedData (id SERIAL PRIMARY KEY, type VARCHAR(255), text TEXT)")
            for item in data:
                logging.debug(f"Inserting data: {item}")  # Debug log for what's being inserted
                cursor.execute("INSERT INTO ScrapedData (type, text) VALUES (%s, %s)", (item['type'], item['text']))
            connection.commit()
            cursor.close()
            connection.close()

            logging.info("Data scraped successfully and saved to %s and PostgreSQL", output_file)
        else:
            logging.warning("No data to save, skipping database and CSV output.")
    except Exception as e:
        logging.error("An error occurred: %s", str(e))
    
    return data

# Execute the scrape at least once immediately
scrape_data()

# Set up and start the scheduler only if an interval is provided
if schedule_interval:
    scheduler = BlockingScheduler()
    scheduler.add_job(scrape_data, IntervalTrigger(seconds=schedule_interval))
    logging.info("Scraping job scheduled to run every %s seconds", schedule_interval)
    scheduler.start()
else:
    logging.info("No scheduling interval provided, running once only.")
