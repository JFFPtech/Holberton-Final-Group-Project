import pandas as pd
import random

def generate_dummy_data(num_rows, columns):
    data = {col: [generate_dummy_value(col) for _ in range(num_rows)] for col in columns}
    df = pd.DataFrame(data)
    return df

def generate_dummy_value(column_name):
    if "name" in column_name.lower():
        return random.choice(["Alice", "Bob", "Charlie", "David", "Eve"])
    elif "age" in column_name.lower():
        return random.randint(18, 70)
    elif "email" in column_name.lower():
        return random.choice(["example1@example.com", "example2@example.com", "example3@example.com"])
    elif "date" in column_name.lower():
        return random.choice(["2021-01-01", "2021-06-15", "2022-03-22", "2023-08-30"])
    else:
        return random.choice(["Value1", "Value2", "Value3", "Value4"])

def generate_csv_from_dummy_data(df):
    return df.to_csv(index=False).encode('utf-8')
