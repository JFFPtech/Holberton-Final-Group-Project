import sys
import os
import json
import subprocess
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

# Add the parent directory of the current script to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.data_processing import load_data, analyze_data

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Define the base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Path to the data file
data_file = os.path.join(BASE_DIR, '..', 'data', 'uploaded_data.csv')

@app.route('/')
def index():
    data_info = None
    if os.path.exists(data_file):
        df = load_data(data_file)
        data_info = analyze_data(df)
    return render_template('index.html', data_info=data_info)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    file.save(data_file)
    flash('File uploaded successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form['url']
    try:
        subprocess.run(['python', os.path.join(BASE_DIR, '..', 'scripts', 'scrape.py'), '--url', url], check=True)
        flash('Scraping successful!', 'success')
    except subprocess.CalledProcessError:
        flash('Scraping failed. Please check the URL and try again.', 'danger')
    return redirect(url_for('index'))

@app.route('/graph', methods=['POST'])
def graph():
    df = load_data(data_file)
    if df.empty:
        return jsonify({"error": "No data available to visualize."})
    column_x = request.form['column_x']
    column_y = request.form['column_y']
    fig = px.bar(df, x=column_x, y=column_y, title=f'{column_y} by {column_x}')
    graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)
    return graph_json

if __name__ == '__main__':
    app.run(debug=True)
