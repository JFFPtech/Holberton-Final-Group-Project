from flask import Flask, request, render_template, redirect, url_for, flash
import requests
from bs4 import BeautifulSoup
import pandas as pd
import psycopg2
import json
import logging
import os

# Setup logging
logging.basicConfig(filename='scraping.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

pg_config = config['postgres']

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
                cursor.execute("INSERT INTO ScrapedData (type, text) VALUES (%s, %s)", (item['type'], item['text']))
            connection.commit()
            cursor.close()
            connection.close()

            logging.info("Data scraped successfully and saved to %s and PostgreSQL", output_file)
        else:
            logging.warning("No data to save, skipping database and CSV output.")
    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        raise
    finally:
        if 'connection' in locals() and connection:
            connection.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form['url']
    output_file = 'scraped_data.csv'
    try:
        scrape_data(url, output_file, pg_config)
        flash('Data scraped successfully!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Error scraping data: {str(e)}")
        flash('An error occurred while scraping the data.', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
