from strategies.headers.base_header_strategy import BaseHeaderStrategy
from utils.logger import log_info, log_error
import pandas as pd
import streamlit as st

class SingleLineHeaderStrategy(BaseHeaderStrategy):
    def detect_headers_and_columns(self, sheet_name, sheet_data, start_idx, end_idx, keywords, secondary_keywords):
        for idx in range(start_idx, end_idx):
            row = sheet_data.iloc[idx]
            found_keywords = [
                str(val).strip()
                for val in row.values
                if isinstance(val, str) and any(
                    keyword.lower() in val.lower() for keyword in keywords + secondary_keywords)
            ]

            if found_keywords:
                # log_info(f"found keywords: {found_keywords}")
                # st.write(idx, [str(val).strip() if pd.notna(val) else "" for val in row.values])
                return idx, [str(val).strip() if pd.notna(val) else "" for val in row.values]
        return None

# from strategies.headers.base_header_strategy import BaseHeaderStrategy
# from utils.logger import log_info, log_error
# import pandas as pd
#
#
# class SingleLineHeaderStrategy(BaseHeaderStrategy):
#     def detect_headers_and_columns(self, sheet_name, sheet_data, start_idx, end_idx, keywords, secondary_keywords=[]):
#         """
#         Detect single-line headers by scanning row-by-row and find required columns.
#
#         Args:
#             dataframe (pd.DataFrame): The DataFrame to scan.
#             keywords (list): List of keywords to identify header rows.
#
#         Returns:
#             tuple: (row_index, headers, columns) or (None, None, None)
#         """
#         idx = None
#         idx = self.detect_anchor_row(sheet_name, sheet_data, start_idx, end_idx, keywords)
#
#         if idx is None:
#             return None, None
#
#         # Step 2: Combine multi-line headers
#         header_rows = sheet_data.iloc[[idx]]
#         combined_headers = (
#             header_rows.fillna("")  # Replace NaN with empty string
#                 .astype(str)  # Convert to string
#                 .apply(lambda row: row.str.replace("\n", "") if isinstance(row, pd.Series) else row)  # Normalize multi-line cells
#                 .agg(' '.join, axis=0)  # Combine rows into a single header
#                 .str.replace(r'\s+', ' ', regex=True)  # Clean multiple spaces
#                 .str.strip()  # Remove leading/trailing spaces
#         )
#
#         log_info(f"Combined Header: {list(combined_headers)}")
#
#         return idx, list(combined_headers)