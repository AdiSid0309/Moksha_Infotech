from utils.validators import validate_gl_number,validate_fund_number,split_account_string 
import pandas as pd
import streamlit as st


class TBSimpleDataExtraction:
    def extract_data(self, sheet_data, columns):
        extracted_data = []

        for _, row in sheet_data.iterrows():
            row_data = {}
            for col in sheet_data.columns:
                value = row[col]

                # Ensure value is not a Series
                if isinstance(value, pd.Series):
                    print(f"Warning: Column '{col}' returned a Series instead of a scalar. Skipping this column.")
                    continue  # Skip problematic columns

                # Only add non-null values
                if pd.notna(value):
                    row_data[col] = value

            extracted_data.append(row_data)

        return extracted_data

