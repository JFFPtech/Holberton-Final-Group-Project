import argparse
import logging
import sys
from utils import load_config, setup_logging, fetch_from_api, fetch_from_scraper
from selenium_scraper import get_rendered_html, find_api_endpoints_via_network, extract_data_from_html

def get_args():
    parser = argparse.ArgumentParser(description='Multi-Source Web Scraper')
    parser.add_argument('--query', required=True, help='Search query topic or subject')
    return parser.parse_args()

def search_sources(query, driver_path):
    config_path = '../config/config.json'
    config = load_config(config_path)
    sources = config['sources']
    results = []

    for source in sources:
        try:
            if source['type'] == 'api':
                data = fetch_from_api(source['endpoint'], source['query_param'], query)
            elif source['type'] == 'scraper':
                data = fetch_from_scraper(source['url_pattern'], query, driver_path)
            results.append({
                'source': source['name'],
                'data': data
            })
        except Exception as e:
            logging.error(f"Failed to fetch data from {source['name']}: {e}")

    return results

def main():
    config_path = '../config/config.json'
    log_path = '../logs/scraping.log'
    setup_logging(log_path)

    args = get_args()
    query = args.query
    driver_path = '../chromedriver/chromedriver.exe'

    results = search_sources(query, driver_path)
    for result in results:
        print(f"Source: {result['source']}")
        print("Data:", result['data'])

if __name__ == '__main__':
    main()
