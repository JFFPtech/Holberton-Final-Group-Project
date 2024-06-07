import psycopg2
import requests
from bs4 import BeautifulSoup
import csv
import logging
import json
import os

# Setting up logging
logging.basicConfig(filename='scraping.log', level=logging.DEBUG, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# PostgreSQL configuration (loaded from environment variables)
pg_config = {
    'dbname': os.getenv('DB_NAME', 'default_dbname'),
    'user': os.getenv('DB_USER', 'default_user'),
    'password': os.getenv('DB_PASSWORD', 'default_password'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

def scrape_wikipedia(url, ssh_identifier):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        logging.info("Successfully fetched the webpage.")
        return soup
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None

def extract_data(soup, url, ssh_identifier):
    data = []
    if soup:
        try:
            for heading in soup.find_all(['h1', 'h2', 'h3']):
                data.append({'ssh_identifier': ssh_identifier, 'url': url, 'type': 'heading', 'text': heading.text.strip()})
            for paragraph in soup.find_all('p'):
                data.append({'ssh_identifier': ssh_identifier, 'url': url, 'type': 'paragraph', 'text': paragraph.text.strip()})
            logging.info("Data extraction successful.")
        except Exception as e:
            logging.error(f"Error during data extraction: {e}")
    return data

def save_to_postgresql(data):
    connection = None
    try:
        connection = psycopg2.connect(**pg_config)
        cursor = connection.cursor()
        for row in data:
            cursor.execute("INSERT INTO ScrapedData (ssh_identifier, url, type, text) VALUES (%s, %s, %s, %s)", (row['ssh_identifier'], row['url'], row['type'], row['text']))
        connection.commit()
        logging.info("Data successfully saved to PostgreSQL database.")
    except Exception as e:
        logging.error(f"Error while connecting to PostgreSQL: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            logging.info("PostgreSQL connection is closed")

def main():
    ssh_identifier = os.getenv('SSH_IDENTIFIER', 'default_ssh_id')  # This should be set in your environment variables
    url = config['url']
    soup = scrape_wikipedia(url, ssh_identifier)
    if soup:
        data = extract_data(soup, url, ssh_identifier)
        save_to_postgresql(data)

if __name__ == "__main__":
    main()
