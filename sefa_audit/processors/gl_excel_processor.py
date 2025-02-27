import pandas as pd
import os
from strategies.gl_strategy_manager import GLStrategyManager
from utils.logger import log_info, log_error
from processors.base_processor import BaseProcessor
import traceback
import streamlit as st
from io import BytesIO

class GLExcelProcessor(BaseProcessor):
    def process(self, file_path):
        try:
            log_info(f"Starting processing of file: {file_path}")
            combined_data = []
            manager = GLStrategyManager()

            # Read all sheets in the Excel file
            file_bytes = BytesIO(file_path.read())
            df = pd.read_excel(file_bytes, sheet_name=None, header=None, parse_dates=True)

            for sheet_name, sheet_data in df.items():
                log_info(f"Processing sheet: {sheet_name}")

                # Step 1: Detect headers and find required columns
                result = manager.detect_headers_and_columns(sheet_name, sheet_data)
                # st.write(result)
                if result is None:
                    log_info(f"Failed to detect headers or required columns in sheet '{sheet_name}'. Skipping.")
                    continue

                anchor_row_index, headers, columns, fund_row_headers = result
                # st.write(f"gl idx: {anchor_row_index}")
                log_info(f"Detected Headers: {list(headers)}")
                log_info(f"Fund Row Headers: {fund_row_headers}")
                log_info(f"Columns Found: {columns}")

                # Step 2: Set headers and clean data
                sheet_data.columns = headers
                sheet_data = sheet_data.iloc[anchor_row_index + 2:].reset_index(drop=True)
                sheet_data = sheet_data.dropna(how="all")
                # Step 2.1: Split "String" column into FUND_CODE and GL_CODE
                # if "String" in sheet_data.columns and not any(col in sheet_data.columns for col in ["Fund Code", "GL Code"]):
                #     sheet_data[['Fund', 'Gl', 'Award_Code']] = sheet_data["String"].str.split("-", n=2, expand=True)
                prefixes = [col.split()[0] for col in ["Fund Code", "GL Code"]]

                if not any(any(prefix in column for column in sheet_data.columns) for prefix in prefixes):
                    print("No matching prefixes found")
                    if any(col in sheet_data.columns for col in ["String", "Account String", "Account Code", "Account No"]) and not any(col in sheet_data.columns for col in ["Fund Code", "GL Code", "Fund", "Account Code", "GL"]):
                        # Select the first available column
                        target_col = next(col for col in ["String", "Account Code", "Account String", "Account No"] if col in sheet_data.columns)

                        # Determine max_splits: Use min(3, actual number of "-")
                        max_splits = min(2, sheet_data[target_col].str.count("-").max())
                        log_info(f"Splitting '{target_col}' with max_splits: {max_splits}")

                        # Perform the split
                        split_columns = sheet_data[target_col].str.split("-", n=max_splits, expand=True)

                        # Define column names dynamically
                        column_names = ["Fund", "Gl", "Award_Code"][:len(split_columns.columns)]

                        # Assign split values back to DataFrame
                        sheet_data[column_names] = split_columns

                # Rename columns based on provided logic
                rename_mapping = {}
                for col in sheet_data.columns:
                    col_lower = col.lower()
                    if "cfda" in col_lower:
                        rename_mapping[col] = "CFDA"
                    elif col_lower in ["fund", "fund code", "fund number"]:
                        rename_mapping[col] = "FUND_CODE"
                    elif col_lower in ['gl code', 'gl_code', 'acct code', 'acct_code', 'account code']:
                        rename_mapping[col] = "GL_CODE"
                    elif "gl" in col_lower:
                        rename_mapping[col] = "GL"

                sheet_data.rename(columns=rename_mapping, inplace=True)
                # Step 2.2: Convert columns containing "date" to datetime format
                # for col in sheet_data.columns:
                #     if "date" in col.lower():
                #         log_info(f"Converting column '{col}' to datetime format")
                #         sheet_data[col] = pd.to_datetime(sheet_data[col], errors='coerce', format="%m-%d-%Y")
                #         log_info(sheet_data[col].head())
                # Step 2.2: Convert columns containing "date" to datetime format and format them to 'YYYY-MM-DD'
                for col in sheet_data.columns:
                    if "date" in col.lower():
                        log_info(f"Converting column '{col}' to datetime format")
                        sheet_data[col] = pd.to_datetime(sheet_data[col], errors='coerce', format="%m-%d-%Y")

                        # Ensure all date columns are formatted as 'YYYY-MM-DD'
                        sheet_data[col] = sheet_data[col].dt.strftime('%Y-%m-%d')
                        log_info(sheet_data[col].head())

                # sheet_data['Effective Date'] = pd.to_datetime('1899-12-30') + pd.to_timedelta(sheet_data['Effective Date'], unit='D')
                log_info(f"Number of valid rows after cleanup: {len(sheet_data)}")

                # Step 3: Extract valid rows
                extracted_data = manager.process_data(sheet_data, columns)
                combined_data.extend(extracted_data)
                break

            # Step 4: Save results
            if combined_data:
                result_df = self.post_process_data(combined_data)
                output_path = os.path.join("data", "output", os.path.basename(file_path).replace(".xlsx", ".json"))
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                result_df.to_json(output_path, orient="records", indent=4)
                log_info(f"Processed file saved to: {output_path}")
                return result_df, fund_row_headers
            else:
                log_error("No valid data found to process.")
                return None, None

        except Exception as e:
            # traceback.print_exc()
            log_error(f"Error processing file {file_path}: {str(e)}")
            return None, None

    def post_process_data(self, combined_data):
        result_df = pd.DataFrame(combined_data)

        return result_df
