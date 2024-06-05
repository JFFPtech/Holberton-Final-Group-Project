import psycopg2
import requests
from bs4 import BeautifulSoup
import csv
import logging
import json

# Setting up logging
logging.basicConfig(filename='scraping.log', level=logging.DEBUG, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# PostgreSQL configuration (replace with your actual RDS details)
pg_config = {
    'dbname': 'scrape-log',
    'user': 'javif',
    'password': 'hb_hrvst_dev_pw',
    'host': 'scrape-log.cpgskewgusdn.us-east-2.rds.amazonaws.com',
    'port': '5432'
}

def scrape_wikipedia(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        logging.info("Successfully fetched the webpage.")
        return soup
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
    except Exception as err:
        logging.error(f"An error occurred: {err}")

def extract_data(soup):
    data = []
    try:
        # Extracting data (example: headings and paragraphs)
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            data.append({'type': 'heading', 'text': heading.text.strip()})
        for paragraph in soup.find_all('p'):
            data.append({'type': 'paragraph', 'text': paragraph.text.strip()})
        logging.info("Data extraction successful.")
    except Exception as e:
        logging.error(f"Error during data extraction: {e}")
    return data

def save_to_csv(data, output_file):
    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['type', 'text'])
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        logging.info(f"Data successfully saved to {output_file}")
    except Exception as e:
        logging.error(f"Error while saving to CSV: {e}")

def save_to_postgresql(data):
    try:
        connection = psycopg2.connect(**pg_config)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ScrapedData (
                id SERIAL PRIMARY KEY,
                type VARCHAR(255),
                text TEXT
            )
        """)
        for row in data:
            cursor.execute("INSERT INTO ScrapedData (type, text) VALUES (%s, %s)", (row['type'], row['text']))
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
    url = config['url']
    output_file = config['output_file']
    
    soup = scrape_wikipedia(url)
    if soup:
        data = extract_data(soup)
        save_to_csv(data, output_file)
        save_to_postgresql(data)

if __name__ == "__main__":
    main()
