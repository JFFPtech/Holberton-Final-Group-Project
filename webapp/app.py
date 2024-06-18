import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from flask import Flask, render_template, request, redirect, flash, jsonify
from werkzeug.utils import secure_filename
from scripts.data_processing import load_data, analyze_data, create_sunburst_chart

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'data'
ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    data_info = None
    graph_json = None

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_data.csv'))
            df = load_data(os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_data.csv'))
            if df is not None:
                data_info = analyze_data(df)
                graph_json = create_sunburst_chart(df)
            else:
                flash('Error loading data')
                return redirect(request.url)

    return render_template('index.html', data_info=data_info, graph_json=graph_json)

if __name__ == "__main__":
    app.run(debug=True)
