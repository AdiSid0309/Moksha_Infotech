from strategies.headers.single_line_header import SingleLineHeaderStrategy
from strategies.data.bb_data_extraction import BBSimpleDataExtraction
from utils.validators import find_column
from utils.logger import log_info, log_error
import pandas as pd
import streamlit as st

class BBStrategyManager:
    def __init__(self):
        self.header_strategies = [
            SingleLineHeaderStrategy()
        ]
        self.data_strategy = BBSimpleDataExtraction()

    def detect_headers_and_columns(self, sheet_name, sheet_data):
        """
        Run all header detection strategies sequentially to find headers and columns.
        """
        keywords = ["Map Number", "Map No.", "Map Description"]
        secondary_keywords = ["Fund Title", "Type", "Fund", "GL", "String", "GL Title", "Amount"]

        for strategy in self.header_strategies:
            is_valid_column = False
            idx = 0
            end_idx = min(len(sheet_data), 100)
            # st.write(end_idx)

            while not is_valid_column:
                result = strategy.detect_headers_and_columns(sheet_name, sheet_data, idx, end_idx, keywords,
                                                             secondary_keywords)
                # st.write(result)
                if result is None:
                    break

                idx, combined_headers = result
                # st.write(idx, combined_headers)
                # Store the original row where Fund was found
                fund_row_headers = [str(value).strip() for value in sheet_data.iloc[idx].values if pd.notna(value)]

                sheet_data.columns = combined_headers


                columns = {
                    "fund_col": find_column(combined_headers, ["fund", "fund code", "fund number", "fund no", "fund#"]),
                    "gl_col": find_column(combined_headers, ["gl", "gl#", "gl code", "gl number", "gl no"]),
                    "accountstring_col": find_column(combined_headers, ["string", "account string", "account code"]),
                    "gltitle_col": find_column(combined_headers, ["gl title"]),
                    "amount_col": find_column(combined_headers, ["amount", "balance"]),
                    "mapno_col": find_column(combined_headers, ["map no", "map number"]),
                    "mapdescription_col": find_column(combined_headers, ["map description", "description"]),
                }
                # st.write(columns)
                if not columns['mapno_col']:
                    idx += 1
                else:
                    is_valid_column = True
                    # st.write(is_valid_column)
                    return idx, combined_headers, columns, fund_row_headers

        return None

    def process_data(self, sheet_data, columns):
        """
        Extract valid rows using identified columns.
        """
        return self.data_strategy.extract_data(sheet_data, columns)

