import json
import logging
import sys
from urllib.parse import urlparse
import urllib.robotparser
import requests

def load_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)

def setup_logging(log_path):
    logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logging.getLogger().addHandler(console_handler)

def can_scrape(url):
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    rp.read()
    
    return rp.can_fetch("*", url)

def fetch_api_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        try:
            return response.json()  # Assuming the API returns JSON data
        except json.JSONDecodeError:
            logging.error("API response is not in JSON format")
            return None
    except requests.exceptions.RequestException as e:
        logging.error("API request failed: %s", e)
        return None
