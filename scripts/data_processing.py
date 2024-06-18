import pandas as pd
import plotly.express as px
import json

def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            raise ValueError("Dataframe is empty")
        return df
    except pd.errors.ParserError as e:
        print(f"Error tokenizing data: {e}")
        return None
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def analyze_data(df):
    data_info = {
        'columns': df.columns.tolist(),
        'num_rows': df.shape[0],
        'num_columns': df.shape[1]
    }
    return data_info

def create_sunburst_chart(df):
    if 'Country of origin' not in df.columns or 'Country of asylum' not in df.columns or 'Recognized decisions' not in df.columns:
        raise ValueError("Required columns are missing in the dataframe")

    fig = px.sunburst(df, path=['Country of origin', 'Country of asylum'], values='Recognized decisions',
                      title="Recognized Asylum Decisions by Country of Origin and Country of Asylum")
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_json
