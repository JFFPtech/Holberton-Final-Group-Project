import pandas as pd

def load_data(file_path):
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip')
        return df
    except pd.errors.ParserError as e:
        print(f"Error parsing CSV file: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

def analyze_data(df):
    if df.empty:
        return {
            'columns': [],
            'num_rows': 0,
            'num_columns': 0
        }
    # Get basic information about the dataset
    columns = df.columns.tolist()
    data_info = {
        'columns': columns,
        'num_rows': len(df),
        'num_columns': len(columns)
    }
    return data_info
