import requests
import pandas as pd
import logging
import sys
import argparse
import json
import os
import argparse
import json

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


        # Check if response is not empty
        if response.text:
            data = response.json()  # Assuming JSON response
        else:
            logging.error("Empty response received from %s", url)
            return


        directory = os.path.dirname(output_file)
        os.makedirs(directory, exist_ok=True)

        # Save data to JSON file
        with open(output_file, 'w') as file:
            json.dump(data, file, indent=4)
        
        logging.info("Data scraped successfully and saved to %s", output_file)
    except json.JSONDecodeError:
        logging.error("An error occurred while decoding the JSON response: %s", response.text)
    except Exception as e:
        logging.error("An error occurred: %s", str(e))

def main():
    parser = argparse.ArgumentParser(description='Scrape data from a URL and save it to a file.')
    parser.add_argument('url', help='The URL to scrape data from.')
    parser.add_argument('output_file', help='The file to save the scraped data to.')
    args = parser.parse_args()

    scrape_data(args.url, args.output_file)
    parser = argparse.ArgumentParser(description='Scrape data from a URL and save it to a file.')
    parser.add_argument('url', help='The URL to scrape data from.')
    parser.add_argument('output_file', help='The file to save the scraped data to.')
    args = parser.parse_args()

    scrape_data(args.url, args.output_file)

if __name__ == '__main__':
    main()
