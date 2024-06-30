import requests
import pandas as pd
import logging
import sys
import argparse
import json
import os
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

def scrape_data(url, output_file):
    try:
        response = requests.get(url)
        response.raise_for_status()

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract data based on the structure of the website
        data = {
            'title': soup.title.string if soup.title else 'No title',
            'meta_description': soup.find('meta', attrs={'name': 'description'})['content'] if soup.find('meta', attrs={'name': 'description'}) else 'No description',
            'headings': [heading.text for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])],
            'paragraphs': [p.text for p in soup.find_all('p')],
            # Add more fields as needed based on what you want to scrape
        }

        directory = os.path.dirname(output_file)
        os.makedirs(directory, exist_ok=True)

        # Save data to JSON file
        with open(output_file, 'w') as file:
            json.dump(data, file, indent=4)

        logging.info("Data scraped successfully and saved to %s", output_file)
    except requests.exceptions.RequestException as e:
        logging.error("An error occurred during the request: %s", str(e))
    except Exception as e:
        logging.error("An error occurred: %s", str(e))

def main():
    parser = argparse.ArgumentParser(description='Scrape data from a URL and save it to a file.')
    parser.add_argument('url', help='The URL to scrape data from.')
    parser.add_argument('output_file', help='The file to save the scraped data to.')
    args = parser.parse_args()

    scrape_data(args.url, args.output_file)

if __name__ == '__main__':
    main()
