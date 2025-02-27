from strategies.headers.base_header_strategy import BaseHeaderStrategy
from utils.logger import log_info, log_error
import pandas as pd

class MultiRowHeaderStrategy(BaseHeaderStrategy):
    def detect_headers_and_columns(self, sheet_name, sheet_data, start_idx, end_idx, keywords, secondary_keywords):
        for idx in range(start_idx, end_idx - 1):
            row1 = sheet_data.iloc[idx]
            row2 = sheet_data.iloc[idx + 1]

            combined_values = []
            for val1, val2 in zip(row1.values, row2.values):
                if pd.isna(val1) and pd.isna(val2):
                    combined_values.append("")
                elif pd.isna(val1):
                    combined_values.append(str(val2).strip())
                elif pd.isna(val2):
                    combined_values.append(str(val1).strip())
                else:
                    combined_values.append(f"{str(val1).strip()} {str(val2).strip()}")

            found_keywords = [
                val for val in combined_values
                if isinstance(val, str) and any(
                    keyword.lower() in val.lower() for keyword in keywords + secondary_keywords)
            ]

            if found_keywords:
                return idx, combined_values
        return None



# from strategies.headers.base_header_strategy import BaseHeaderStrategy
# from utils.logger import log_info, log_error
#
#
# class MultiRowHeaderStrategy(BaseHeaderStrategy):
#     def detect_headers_and_columns(self, sheet_name, sheet_data, start_idx, end_idx, primary_keywords, secondary_keywords=[], max_offset=5):
#         """
#         Detect and combine multi-row headers starting from the anchor row.
#
#         Args:
#             dataframe (pd.DataFrame): The input DataFrame.
#             keywords (list): List of keywords to match required columns.
#             max_rows (int): Number of rows to combine.
#
#         Returns:
#             tuple: (anchor_row_index, headers, columns) or (None, None, None)
#         """
#
#         # Step 1: Identify primary anchor row
#         anchor_row_index = None
#         anchor_row_index = self.detect_anchor_row(sheet_name, sheet_data, start_idx, end_idx, primary_keywords)
#
#         if anchor_row_index is None:
#             return None, None
#
#         # Step 2: Search for secondary anchor keywords within ±max_offset rows
#         header_indices = set([anchor_row_index])  # Start with the primary anchor row
#
#         start_idx = anchor_row_index - max_offset
#         end_idx = anchor_row_index + max_offset
#
#         for keyword in secondary_keywords:
#             keyword_arr = set([keyword])
#             current_idx = self.detect_anchor_row(sheet_name, sheet_data, start_idx, end_idx, keyword_arr)
#             if current_idx is not None:
#                 header_indices.add(current_idx)
#
#         # Step 3: Combine detected header rows
#         header_rows = sheet_data.iloc[sorted(header_indices)]
#         combined_headers = (
#             header_rows.fillna("")  # Replace NaN with empty string
#                 .astype(str)  # Convert to string
#                 .agg(' '.join, axis=0)  # Combine rows into a single header
#                 .str.replace(r'\s+', ' ', regex=True)  # Clean multiple spaces
#                 .str.strip()
#         )
#         log_info(f"Combined Header: {list(combined_headers)}")
#
#         return current_idx, combined_headers
#
