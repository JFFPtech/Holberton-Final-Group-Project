import streamlit as st
import pandas as pd
import plotly.express as px
import csv
import os
import shutil
import subprocess
import sys
from dummy_gen import generate_dummy_data, generate_csv_from_dummy_data  # Import the dummy data generator

# Other imports and setup code...

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
    kaggle_json_src = os.path.join(os.path.dirname(__file__), 'kaggle.json')  # Ensure this path is correct
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

# Streamlit app title
st.title("Ultimate Data Visualization Dashboard")

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
            pass
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
    api.dataset_download_files(dataset_ref, path=download_path, unzip=True)
    for file in os.listdir(download_path):
        if file.endswith(".csv"):
            return os.path.join(download_path, file)
    return None

# Function to search Google Dataset Search
def search_google_datasets(query):
    # Implement API integration for Google Dataset Search
    # Return list of datasets (title and download link)
    pass

# Function to search Data.gov
def search_data_gov_datasets(query):
    # Implement API integration for Data.gov
    # Return list of datasets (title and download link)
    pass

# Function to switch between different data sources
def search_datasets(query, source):
    if source == "Kaggle":
        return search_kaggle_datasets(query)
    elif source == "Google Dataset Search":
        return search_google_datasets(query)
    elif source == "Data.gov":
        return search_data_gov_datasets(query)
    else:
        return []

# Sidebar for selecting data source
st.sidebar.title("Search for Datasets")
data_source = st.sidebar.selectbox("Select Data Source", ["Kaggle", "Google Dataset Search", "Data.gov"])

# Initialize session state
if "search_results" not in st.session_state:
    st.session_state.search_results = []

if "selected_dataset_index" not in st.session_state:
    st.session_state.selected_dataset_index = None

if "scraped_file_name" not in st.session_state:
    st.session_state.scraped_file_name = ""

# User enters a topic to search for datasets
search_topic = st.sidebar.text_input("Enter a topic to search for datasets")

# Search results container
if st.sidebar.button("Search"):
    if search_topic:
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

# Function to handle ChatBot interaction
def chatbot_interface():
    st.sidebar.title("Generate Dummy Data")
    num_rows = st.sidebar.number_input("Number of rows", min_value=1, max_value=1000, value=10)
    columns_input = st.sidebar.text_area("Enter column names (comma-separated)", "Name, Age, Email, Date")

    if st.sidebar.button("Generate Dummy Data"):
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
            st.sidebar.success("Data generated successfully!")
        else:
            st.sidebar.warning("Please enter at least one column name.")

# Call chatbot_interface function
chatbot_interface()

# File uploader to allow the user to upload the CSV file
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

        # Filter numeric columns for value selection
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

        # Select type of visualization
        visualization_type = st.selectbox("Select visualization type:", ["Sunburst Chart", "Bar Chart", "Line Chart", "Scatter Plot"])

        if visualization_type == "Sunburst Chart":
            with st.form(key='sunburst_form'):
                path_columns = st.multiselect("Select columns for path in sunburst chart:", options=df.columns.tolist())
                value_column = st.selectbox("Select column for values in sunburst chart (numeric columns only):", options=numeric_columns)
                submit_button = st.form_submit_button(label='Generate Sunburst Chart')

            if submit_button and path_columns and value_column:
                try:
                    # Ensure only leaf nodes are passed to the sunburst chart
                    grouped_df = df.groupby(path_columns).sum().reset_index()
                    
                    # Check if the values column sums to zero
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

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.write("Please upload a CSV file to proceed.")
