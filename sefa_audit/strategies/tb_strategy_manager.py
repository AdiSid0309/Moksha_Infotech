from strategies.headers.single_line_header import SingleLineHeaderStrategy
from strategies.data.tb_data_extraction import TBSimpleDataExtraction
from utils.validators import find_column
from utils.logger import log_info, log_error
import pandas as pd
import streamlit as st

class TBStrategyManager:
    def __init__(self):
        self.header_strategies = [
            SingleLineHeaderStrategy()
        ]
        self.data_strategy = TBSimpleDataExtraction()

    # def detect_headers_and_columns(self, sheet_name, sheet_data):
    #     """
    #     Run all header detection strategies sequentially to find headers and columns.
    #     Only proceed if 'Map No.' is found.
    #     """
    #     keywords = ["Map Number", "Map No.", "Map Description", "Map No"]
    #     secondary_keywords = ["Fund Title", "Type", "Fund", "GL", "String", "GL Title", "Amount"]
    #
    #     for strategy in self.header_strategies:
    #         is_valid_column = False
    #         idx = 0
    #         end_idx = min(len(sheet_data), 100)
    #
    #         while not is_valid_column:
    #             result = strategy.detect_headers_and_columns(sheet_name, sheet_data, idx, end_idx, keywords,
    #                                                          secondary_keywords)
    #             if result is None:
    #                 break
    #
    #             idx, combined_headers = result
    #
    #             # Store the original row where Fund was found
    #             fund_row_headers = [str(value).strip() for value in sheet_data.iloc[idx].values if pd.notna(value)]
    #
    #             sheet_data.columns = combined_headers
    #
    #             columns = {
    #                 "fund_col": find_column(combined_headers, ["fund", "fund code", "fund number", "fund no", "fund#"]),
    #                 "gl_col": find_column(combined_headers, ["gl", "gl#", "gl code", "gl number", "gl no", "account number", "account#", "account_number", "account no", "account code"]),
    #                 "accountstring_col": find_column(combined_headers, ["string", "account string"]),
    #                 "gltitle_col": find_column(combined_headers, ["gl title"]),
    #                 "amount_col": find_column(combined_headers, ["amount", "balance"]),
    #                 "mapno_col": find_column(combined_headers, ["map no", "map number", "map no."]),
    #                 "mapdescription_col": find_column(combined_headers, ["map description", "description"]),
    #             }
    #
    #             # Check if 'Map No.' column is present
    #             if columns['mapno_col'] is None:
    #                 log_info(f"Skipping sheet '{sheet_name}' as 'Map No.' column is missing.")
    #                 return None
    #
    #             if not ((columns['gl_col'] or columns['accountstring_col']) and
    #                     columns['amount_col'] and columns['mapdescription_col']):
    #                 idx += 1
    #             else:
    #                 is_valid_column = True
    #                 return idx, combined_headers, columns, fund_row_headers
    #
    #     return None

    def detect_headers_and_columns(self, sheet_name, sheet_data):
        """
        Run all header detection strategies sequentially to find headers and columns.
        """
        keywords = ["Map Number", "Map No.", "Map Description", "Map No"]
        secondary_keywords = ["Fund Title", "Type", "Fund", "GL", "String", "GL Title", "Amount"]

        for strategy in self.header_strategies:
            is_valid_column = False
            idx = 0
            end_idx = min(len(sheet_data), 50)

            while not is_valid_column:
                result = strategy.detect_headers_and_columns(sheet_name, sheet_data, idx, end_idx, keywords,
                                                             secondary_keywords)
                if result is None:
                    break

                idx, combined_headers = result
                # st.write(idx, combined_headers)
                # Store the original row where Fund was found
                fund_row_headers = [str(value).strip() for value in sheet_data.iloc[idx].values if pd.notna(value)]

                sheet_data.columns = combined_headers
                # st.write(sheet_data.columns)
                columns = {
                    "fund_col": find_column(combined_headers, ["fund", "fund code", "fund number", "fund no", "fund#"]),
                    "gl_col": find_column(combined_headers, ["gl", "gl#", "gl code", "gl number", "gl no", "account number", "account#", "account_number", "account no", "account code"]),
                    "accountstring_col": find_column(combined_headers, ["string", "account string"]),
                    "gltitle_col": find_column(combined_headers, ["gl title"]),
                    "amount_col": find_column(combined_headers, ["amount", "balance"]),
                    "mapno_col": find_column(combined_headers, ["map no", "map number", "map no."]),
                    "mapdescription_col": find_column(combined_headers, ["map description", "description"]),
                }

                # if not ((columns['gl_col'] or columns['accountstring_col']) and
                #         columns['amount_col'] and columns['mapno_col'] and
                #         columns['mapdescription_col']):
                #     idx += 1
                if not columns['mapno_col']:
                    idx += 1
                else:
                    is_valid_column = True
                    # st.write(idx, combined_headers, columns, fund_row_headers)
                    return idx, combined_headers, columns, fund_row_headers

        return None

    def process_data(self, sheet_data, columns):
        """
        Extract valid rows using identified columns.
        """
        return self.data_strategy.extract_data(sheet_data, columns)
