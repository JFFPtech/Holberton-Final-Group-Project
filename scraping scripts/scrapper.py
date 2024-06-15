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
import os
from datetime import timedelta

# Setup logging for both file and console
logging.basicConfig(filename='scraping.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def get_pg_config(config):
    return config['postgres']

def get_args():
    parser = argparse.ArgumentParser(description='Webscraper')
    parser.add_argument('--url', required=True, help='URL of the website to scrape')
    parser.add_argument('--output', required=True, help='Output file storing the data')
    return parser.parse_args()

def determine_schedule_interval(config):
    schedule_interval = config.get('schedule_interval')
    if schedule_interval:
        if schedule_interval.lower() == "daily":
            return timedelta(days=1).total_seconds()
        elif schedule_interval.lower() == "none":
            return None
        else:
            return int(schedule_interval)  # assuming seconds if not "daily" or "none"
    return None  # No interval provided

def scrape_data(url, output_file, pg_config):
    try:
        response = requests.get(url)
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
                logging.debug(f"Inserting data: {item}")
                cursor.execute("INSERT INTO ScrapedData (type, text) VALUES (%s, %s)", (item['type'], item['text']))
            connection.commit()
            cursor.close()
            connection.close()

            logging.info("Data scraped successfully and saved to %s and PostgreSQL", output_file)
        else:
            logging.warning("No data to save, skipping database and CSV output.")
    except Exception as e:
        logging.error("An error occurred: %s", str(e))
    finally:
        if 'connection' in locals() and connection:
            connection.close()

def main():
    config = load_config()
    pg_config = get_pg_config(config)
    args = get_args()

    url = args.url
    output_file = args.output

    schedule_interval = determine_schedule_interval(config)

    # Execute the scrape at least once immediately
    scrape_data(url, output_file, pg_config)

    # Set up and start the scheduler only if an interval is provided
    if schedule_interval:
        scheduler = BlockingScheduler()
        scheduler.add_job(lambda: scrape_data(url, output_file, pg_config), IntervalTrigger(seconds=schedule_interval))
        logging.info("Scraping job scheduled to run every %s seconds", schedule_interval)
        scheduler.start()
    else:
        logging.info("No scheduling interval provided, running once only.")

if __name__ == '__main__':
    main()
