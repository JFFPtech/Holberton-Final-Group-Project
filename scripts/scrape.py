import requests
import pandas as pd
import logging
import sys

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
        data = response.json()  # Assuming JSON response
        
        # Process data and save to CSV
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)
        
        logging.info("Data scraped successfully and saved to %s", output_file)
    except Exception as e:
        logging.error("An error occurred: %s", str(e))

def main():
    url = 'URL_TO_UNHCR_DATA'
    output_file = '../data/uploaded_data.csv'
    scrape_data(url, output_file)

if __name__ == '__main__':
    main()
