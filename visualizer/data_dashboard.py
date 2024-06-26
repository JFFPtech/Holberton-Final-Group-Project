import streamlit as st
import pandas as pd
import csv
import os
import requests
import shutil
import subprocess
import sys
import json
import streamlit.components.v1 as components
from dummy_data_generator import generate_dummy_data, generate_csv_from_dummy_data
import plotly.express as px

# Function to install Kaggle package
def install_kaggle():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "kaggle"])

# Try to import Kaggle API, install if not available
try:
    from kaggle.api.kaggle_api_extended import KaggleApi
except ImportError:
    install_kaggle()
    from kaggle.api.kaggle_api_extended import KaggleApi

# Copy the kaggle.json file to the correct location
def setup_kaggle_api():
    kaggle_json_src = os.path.join(os.path.dirname(__file__), 'kaggle.json')
    kaggle_dir = os.path.expanduser('~/.kaggle')
    kaggle_json_dest = os.path.join(kaggle_dir, 'kaggle.json')
    
    if not os.path.exists(kaggle_json_src):
        raise FileNotFoundError(f"Could not find {kaggle_json_src}. Ensure the kaggle.json file is present in the specified location.")
    
    if not os.path.exists(kaggle_dir):
        os.makedirs(kaggle_dir)
    
    shutil.copy(kaggle_json_src, kaggle_json_dest)
    os.chmod(kaggle_json_dest, 0o600)  # Set appropriate permissions

setup_kaggle_api()

# Initialize Kaggle API
api = KaggleApi()
api.authenticate()

# Data.gov API key
DATA_GOV_API_KEY = 'fzybhxMQcRYVilL2vl3LDyfrBDThL3gBCwi69S55'

# Function to authenticate Data.gov API
def authenticate_datagov(api_key):
    headers = {"X-Api-Key": api_key}
    return headers

headers = authenticate_datagov(DATA_GOV_API_KEY)

# Streamlit app title
st.title("HRVST Data Dashboard")

# Initialize session state
if "search_results" not in st.session_state:
    st.session_state.search_results = []

if "selected_dataset_index" not in st.session_state:
    st.session_state.selected_dataset_index = None

if "scraped_file_name" not in st.session_state:
    st.session_state.scraped_file_name = ""

# Function to parse CSV files
def parse_csv(uploaded_file):
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.splitlines()
    
    # Dynamically detect the delimiter
    delimiter = csv.Sniffer().sniff(lines[0]).delimiter
    
    # Read the CSV file
    reader = csv.reader(lines, delimiter=delimiter)
    
    headers = None
    rows = []
    for row in reader:
        if headers is None:
            headers = row
        else:
            rows.append(row)
    
    if headers is None:
        raise ValueError("Could not detect headers in the CSV file")
    
    # Create DataFrame and handle varying number of columns
    df = pd.DataFrame(rows, columns=headers)
    
    # Drop any completely empty columns
    df.dropna(axis=1, how='all', inplace=True)
    
    return df

# Function to convert columns to numeric
def convert_to_numeric(df):
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except ValueError:
            st.warning(f"Column {col} could not be converted to numeric.")
    return df

# Function to clean data
def clean_data(df):
    # Fill missing values with zeros
    df.fillna(0, inplace=True)
    return df

# Function to search and download Kaggle datasets
def search_kaggle_datasets(query):
    datasets = api.dataset_list(search=query)
    dataset_info = [(dataset.ref, dataset.title) for dataset in datasets]
    return dataset_info

def download_kaggle_dataset(dataset_ref, download_path):
    try:
        api.dataset_download_files(dataset_ref, path=download_path, unzip=True)
        for file in os.listdir(download_path):
            if file.endswith(".csv"):
                return os.path.join(download_path, file)
    except Exception as e:
        st.error(f"Error downloading dataset: {e}")
    return None

# Function to search Data.gov datasets
def search_datagov_datasets(query, headers):
    response = requests.get(f"https://catalog.data.gov/api/3/action/package_search?q={query}", headers=headers)
    response.raise_for_status()
    results = response.json()["result"]["results"]
    dataset_info = [(dataset["id"], dataset["title"]) for dataset in results]
    return dataset_info

# Function to download Data.gov dataset
def download_datagov_dataset(dataset_id, headers, download_path):
    response = requests.get(f"https://catalog.data.gov/api/3/action/package_show?id={dataset_id}", headers=headers)
    response.raise_for_status()
    resources = response.json()["result"]["resources"]
    for resource in resources:
        if resource["format"].lower() == "csv":
            download_url = resource["url"]
            csv_data = requests.get(download_url).content
            with open(download_path, "wb") as file:
                file.write(csv_data)
            return download_path
    return None

# Function to switch between different data sources
def search_datasets(query, source):
    if source == "Kaggle":
        return search_kaggle_datasets(query)
    elif source == "Data.gov":
        return search_datagov_datasets(query, headers)
    else:
        return []

def download_dataset(dataset_ref, download_path, source):
    if source == "Kaggle":
        return download_kaggle_dataset(dataset_ref, download_path)
    elif source == "Data.gov":
        return download_datagov_dataset(dataset_ref, headers, download_path)
    else:
        return None

# Sidebar for selecting data source
st.sidebar.title("Search for Datasets")
data_source = st.sidebar.selectbox("Select Data Source", ["Kaggle", "Data.gov"])

# User enters a topic to search for datasets
search_topic = st.sidebar.text_input("Enter a topic to search for datasets")

# Search results container
if st.sidebar.button("Search"):
    if search_topic:
        with st.spinner("Searching for datasets..."):
            try:
                st.session_state.search_results = search_datasets(search_topic, data_source)
                st.session_state.selected_dataset_index = None
            except Exception as e:
                st.sidebar.error(f"An error occurred while searching: {e}")
    else:
        st.sidebar.warning("Please enter a topic to search for datasets.")

# Display search results
if st.session_state.search_results:
    st.sidebar.write("Search Results:")
    for i, result in enumerate(st.session_state.search_results):
        st.sidebar.write(f"{i+1}. {result[1]}")

    # User selects a dataset to scrape
    st.session_state.selected_dataset_index = st.sidebar.selectbox("Select a dataset to scrape", options=[i for i in range(len(st.session_state.search_results))])
    st.session_state.scraped_file_name = st.sidebar.text_input("Enter file name for the scraped data (without extension)", st.session_state.scraped_file_name)

    if st.sidebar.button("Scrape and Convert to CSV"):
        if st.session_state.selected_dataset_index is not None and st.session_state.scraped_file_name:
            try:
                selected_dataset_ref = st.session_state.search_results[st.session_state.selected_dataset_index][0]
                download_path = f"./{st.session_state.scraped_file_name}"
                with st.spinner("Downloading dataset..."):
                    csv_file_path = download_kaggle_dataset(selected_dataset_ref, download_path)
                
                if csv_file_path:
                    scraped_df = pd.read_csv(csv_file_path)
                    st.write("Here is a preview of the scraped data:")
                    st.write(scraped_df.head())
                    
                    # Allow user to download the scraped data as a CSV
                    csv = scraped_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download scraped data as CSV",
                        data=csv,
                        file_name=f'{st.session_state.scraped_file_name}.csv',
                        mime='text/csv',
                    )
                    
                    # Use scraped data for visualization
                    df = scraped_df
                else:
                    st.error("Failed to download CSV file.")
            except Exception as e:
                st.error(f"An error occurred while scraping: {e}")
        else:
            st.sidebar.warning("Please select a dataset and enter a file name.")

# Tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["Upload Data", "Generate Dummy Data", "Visualize Data"])

# Tab 1: Upload Data
with tab1:
    st.header("Upload CSV Data")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        try:
            df = parse_csv(uploaded_file)
            
            st.write("Here is a preview of your uploaded CSV file:")
            st.write(df.head())

            st.write("The columns in the uploaded CSV file are:")
            st.write(df.columns.tolist())

            # Convert numeric columns to numeric types
            df = convert_to_numeric(df)
            
            # Clean data
            df = clean_data(df)

            # Store in session state for use in other tabs
            st.session_state.df = df
        except Exception as e:
            st.error(f"An error occurred: {e}")

# Tab 2: Generate Dummy Data
with tab2:
    st.header("Generate Dummy Data")
    num_rows = st.number_input("Number of rows", min_value=1, max_value=1000, value=10)
    columns_input = st.text_area("Enter column names (comma-separated)", "Name, Age, Email, Date")

    if st.button("Generate Dummy Data"):
        columns = [col.strip() for col in columns_input.split(",") if col.strip()]
        if columns:
            dummy_df = generate_dummy_data(num_rows, columns)
            st.write("Here is a preview of the generated dummy data:")
            st.write(dummy_df.head())
            
            csv_data = generate_csv_from_dummy_data(dummy_df)
            st.download_button(
                label="Download generated data as CSV",
                data=csv_data,
                file_name="dummy_data.csv",
                mime='text/csv'
            )
            st.success("Data generated successfully!")
        else:
            st.warning("Please enter at least one column name.")

# Tab 3: Visualize Data
with tab3:
    st.header("Visualize Data")

    if 'df' in st.session_state:
        df = st.session_state.df

        # Filter numeric columns for value selection
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

        # Select type of visualization
        visualization_type = st.selectbox("Select visualization type:", ["Sunburst Chart", "Bar Chart", "Line Chart", "Scatter Plot", "Chart.js"])

        if visualization_type == "Sunburst Chart":
            with st.form(key='sunburst_form'):
                path_columns = st.multiselect("Select columns for path in sunburst chart:", options=df.columns.tolist())
                value_column = st.selectbox("Select column for values in sunburst chart (numeric columns only):", options=numeric_columns)
                submit_button = st.form_submit_button(label='Generate Sunburst Chart')

            if submit_button and path_columns and value_column:
                try:
                    grouped_df = df.groupby(path_columns).sum().reset_index()
                    
                    if grouped_df[value_column].sum() == 0:
                        st.warning("The selected values column sums to zero. Please select a different column or ensure the data is correct.")
                    else:
                        fig = px.sunburst(
                            grouped_df,
                            path=path_columns,
                            values=value_column,
                            title="Sunburst Chart",
                            height=600,
                            color_continuous_scale='RdBu',
                            color=value_column,
                            hover_data=path_columns
                        )
                        st.plotly_chart(fig)
                except Exception as e:
                    st.error(f"An error occurred: {e}")

        elif visualization_type == "Bar Chart":
            with st.form(key='bar_chart_form'):
                x_column = st.selectbox("Select column for X axis:", options=df.columns.tolist())
                y_column = st.selectbox("Select column for Y axis (numeric columns only):", options=numeric_columns)
                submit_button = st.form_submit_button(label='Generate Bar Chart')
            
            if submit_button and x_column and y_column:
                try:
                    fig = px.bar(
                        df,
                        x=x_column,
                        y=y_column,
                        title="Bar Chart",
                        height=600,
                        color_continuous_scale='RdBu'
                    )
                    st.plotly_chart(fig)
                except Exception as e:
                    st.error(f"An error occurred: {e}")

        elif visualization_type == "Line Chart":
            with st.form(key='line_chart_form'):
                x_column = st.selectbox("Select column for X axis:", options=df.columns.tolist())
                y_column = st.selectbox("Select column for Y axis (numeric columns only):", options=numeric_columns)
                submit_button = st.form_submit_button(label='Generate Line Chart')
            
            if submit_button and x_column and y_column:
                try:
                    fig = px.line(
                        df,
                        x=x_column,
                        y=y_column,
                        title="Line Chart",
                        height=600,
                        color_continuous_scale='RdBu'
                    )
                    st.plotly_chart(fig)
                except Exception as e:
                    st.error(f"An error occurred: {e}")

        elif visualization_type == "Scatter Plot":
            with st.form(key='scatter_plot_form'):
                x_column = st.selectbox("Select column for X axis:", options=df.columns.tolist())
                y_column = st.selectbox("Select column for Y axis (numeric columns only):", options=numeric_columns)
                submit_button = st.form_submit_button(label='Generate Scatter Plot')
            
            if submit_button and x_column and y_column:
                try:
                    fig = px.scatter(
                        df,
                        x=x_column,
                        y=y_column,
                        title="Scatter Plot",
                        height=600,
                        color_continuous_scale='RdBu'
                    )
                    st.plotly_chart(fig)
                except Exception as e:
                    st.error(f"An error occurred: {e}")

        elif visualization_type == "Chart.js":
            with st.form(key='chartjs_form'):
                chart_type = st.selectbox("Select chart type:", ["bar", "line", "pie"])
                labels_column = st.selectbox("Select column for labels:", options=df.columns.tolist())
                data_column = st.selectbox("Select column for data:", options=numeric_columns)
                submit_button = st.form_submit_button(label='Generate Chart.js Chart')
                
            if submit_button and labels_column and data_column:
                try:
                    # Aggregate data for pie chart
                    if chart_type == "pie":
                        aggregated_data = df.groupby(labels_column)[data_column].sum().reset_index()
                        labels = aggregated_data[labels_column].tolist()
                        data = aggregated_data[data_column].tolist()
                    else:
                        labels = df[labels_column].tolist()
                        data = df[data_column].tolist()

                    # Aggregate smaller slices into 'Others'
                    if chart_type == "pie":
                        threshold = 0.01 * sum(data)  # 1% threshold
                        new_labels = []
                        new_data = []
                        others_value = 0
                        for label, value in zip(labels, data):
                            if value >= threshold:
                                new_labels.append(label)
                                new_data.append(value)
                            else:
                                others_value += value
                        if others_value > 0:
                            new_labels.append('Others')
                            new_data.append(others_value)
                        labels = new_labels
                        data = new_data

                    chart_data = {
                        "type": chart_type,
                        "data": {
                            "labels": labels,
                            "datasets": [{
                                "label": labels_column,
                                "data": data,
                                "backgroundColor": [
                                    'rgba(255, 99, 132, 0.2)',
                                    'rgba(54, 162, 235, 0.2)',
                                    'rgba(255, 206, 86, 0.2)',
                                    'rgba(75, 192, 192, 0.2)',
                                    'rgba(153, 102, 255, 0.2)',
                                    'rgba(255, 159, 64, 0.2)'
                                ],
                                "borderColor": [
                                    'rgba(255, 99, 132, 1)',
                                    'rgba(54, 162, 235, 1)',
                                    'rgba(255, 206, 86, 1)',
                                    'rgba(75, 192, 192, 1)',
                                    'rgba(153, 102, 255, 1)',
                                    'rgba(255, 159, 64, 1)'
                                ],
                                "borderWidth": 1
                            }]
                        },
                        "options": {
                            "responsive": True,
                            "maintainAspectRatio": False,
                            "plugins": {
                                "legend": {
                                    "position": "top",
                                },
                                "tooltip": {
                                    "enabled": True
                                }
                            },
                            "animations": {
                                "tension": {
                                    "duration": 1000,
                                    "easing": "easeInOutBounce",
                                    "from": 1,
                                    "to": 0,
                                    "loop": True
                                }
                            },
                            "scales": {
                                "y": {
                                    "beginAtZero": True
                                }
                            }
                        }
                    }
                    chart_json = json.dumps(chart_data)  # Ensure the data is correctly formatted as JSON
                    chart_html = f"""
                    <canvas id="myChart"></canvas>
                    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                    <script>
                    var ctx = document.getElementById('myChart').getContext('2d');
                    new Chart(ctx, {chart_json});
                    </script>
                    """
                    components.html(chart_html, height=600)
                except Exception as e:
                    st.error(f"An error occurred: {e}")
    else:
        st.write("Please upload a CSV file to proceed.")