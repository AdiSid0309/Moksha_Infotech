from strategies.headers.single_line_header import SingleLineHeaderStrategy
from strategies.data.gl_data_extraction import GLSimpleDataExtraction
from utils.validators import find_column
from utils.logger import log_info, log_error
import pandas as pd
import streamlit as st

class GLStrategyManager:
    def __init__(self):
        self.header_strategies = [
            SingleLineHeaderStrategy()
        ]
        self.data_strategy = GLSimpleDataExtraction()

    def detect_headers_and_columns(self, sheet_name , sheet_data):
        """
        Run all header detection strategies sequentially to find headers and columns.
        """
        keywords = ["Debit", "Credit", "Net Amount"]
        secondary_keywords = ["GL Code", "Account Code", "Fund Code", "Fund", "GL", "String", "GL Title",
                              "Type", "Doc Description", "Document Description"]

        for strategy in self.header_strategies:
            is_valid_column = False
            idx = 0
            end_idx = min(len(sheet_data), 100)

            while not is_valid_column:
                result = strategy.detect_headers_and_columns(sheet_name, sheet_data, idx, end_idx, keywords,
                                                             secondary_keywords)
                if result is None:
                    break

                idx, combined_headers = result

                # Store the original row where GL headers were found
                gl_row_headers = [str(value).strip() for value in sheet_data.iloc[idx].values if pd.notna(value)]

                sheet_data.columns = combined_headers
                # st.write(f"gl idx: {idx}")

                columns = {
                    "fund_col": find_column(combined_headers, ["fund", "fund code", "fund number", "fund no", "fund#"]),
                    "glcode_col": find_column(combined_headers,
                                              ["gl", "gl#", "gl code", "gl number", "gl no", "acct code", "account code"]),
                    "accountstring_col": find_column(combined_headers, ["string", "account string"]),
                    "type_col": find_column(combined_headers, ["type"]),
                    "description_col": find_column(combined_headers, ["doc description", "document description",
                                                                      "transaction description", "DocDesc"]),
                    "debit_col": find_column(combined_headers, ["debit"]),
                    "credit_col": find_column(combined_headers, ["credit"]),
                    "net_amount_col": find_column(combined_headers, ["Net Amount", "Amount"]),

                }
                # "gltitle_col": find_column(combined_headers, ["gl title", "acc title"]),
                # st.write(columns)

                if not all(columns.values()):
                    idx += 1
                else:
                    is_valid_column = True
                    return idx, combined_headers, columns, gl_row_headers

        return None

    def process_data(self, sheet_data, columns):
        """
        Extract valid rows using identified columns.
        """
        return self.data_strategy.extract_data(sheet_data, columns)
