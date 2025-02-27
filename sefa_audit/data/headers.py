import pandas as pd
import json

# Load headers dynamically from the JSON file
with open("headers.json", "r") as file:
    headers = json.load(file)

# Example: Dynamically iterate over all headers
for header_name, columns in headers.items():
    print(f"Original Columns in {header_name}: {columns}")

    # Example DataFrame for the current header
    df = pd.DataFrame(columns=columns)

    # Rename logic based on keywords
    rename_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if "cfda" in col_lower:
            rename_mapping[col] = "CFDA"
        elif "fund" in col_lower:
            rename_mapping[col] = "FUND_CODE"
        elif "gl" in col_lower and "code" in col_lower:
            rename_mapping[col] = "GL_CODE"
        elif "gl" in col_lower:
            rename_mapping[col] = "GL"

    # Apply renaming dynamically
    df.rename(columns=rename_mapping, inplace=True)

    print(f"Renamed Columns in {header_name}: {df.columns.tolist()}")