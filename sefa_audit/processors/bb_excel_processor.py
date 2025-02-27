import pandas as pd
import os
from strategies.bb_strategy_manager import BBStrategyManager
from utils.logger import log_info, log_error
from processors.base_processor import BaseProcessor
import streamlit as st


class BBExcelProcessor(BaseProcessor):
    def process(self, file_path):
        try:
            print(f"Starting processing of file: {file_path}")
            combined_data = []
            manager = BBStrategyManager()

            # Read all sheets in the Excel file
            df = pd.read_excel(file_path, sheet_name=None, header=None)

            for sheet_name, sheet_data in df.items():
                print(f"Processing sheet: {sheet_name}")

                # Step 1: Detect headers and find required columns
                result = manager.detect_headers_and_columns(sheet_name, sheet_data)
                if result is None:
                    print(f"Failed to detect headers or required columns in sheet '{sheet_name}'. Skipping.")
                    continue

                anchor_row_index, headers, columns, fund_row_headers = result

                print(f"Detected Headers: {list(headers)}")
                print(f"Fund Row Headers: {fund_row_headers}")
                print(f"Columns Found: {columns}")

                # Step 2: Set headers and clean data
                sheet_data.columns = headers
                sheet_data = sheet_data.iloc[anchor_row_index + 2:].reset_index(drop=True)
                sheet_data = sheet_data.dropna(how="all")
                # log_info('true')

                # if any(col in sheet_data.columns for col in ["String", "Account String", "Account Code", "Account No"]) and not any(col in sheet_data.columns for col in ["Fund Code", "GL Code", "Fund", "GL"]):
                #     # Select the first available column
                #     target_col = next(col for col in ["String", "Account Code", "Account String", "Account No"] if col in sheet_data.columns)
                #
                #     # Determine max_splits: Use min(3, actual number of "-")
                #     max_splits = min(2, sheet_data[target_col].str.count("-").max())
                #     log_info(f"Splitting '{target_col}' with max_splits: {max_splits}")
                #
                #     # Perform the split
                #     split_columns = sheet_data[target_col].str.split("-", n=max_splits, expand=True)
                #
                #     # Define column names dynamically
                #     column_names = ["Fund", "Gl", "Award_Code"][:len(split_columns.columns)]
                #
                #     # Assign split values back to DataFrame
                #     sheet_data[column_names] = split_columns

                prefixes = [col.split()[0] for col in ["Fund Code", "GL Code"]]

                # Normalize column names to ensure case-insensitive matching
                sheet_data.columns = sheet_data.columns.str.strip().str.upper()

                # Check if any target column is present and none of the prefixes are in the columns
                if any(col in sheet_data.columns for col in ["STRING", "ACCOUNT STRING", "ACCOUNT CODE", "ACCOUNT NO"]) and not any(col in sheet_data.columns for col in ["FUND CODE", "GL CODE"]):
                    try:
                        # Select the first available target column
                        target_col = next(col for col in ["STRING", "ACCOUNT CODE", "ACCOUNT STRING", "ACCOUNT NO"] if col in sheet_data.columns)
                    except StopIteration:
                        # Handle case where no target column is found
                        st.write("No target column found for splitting.")
                        target_col = None

                    if target_col:
                        # Ensure no null or NaN values in the target column
                        sheet_data[target_col].fillna("", inplace=True)

                        # Determine max_splits: Use min(1, actual number of "-")
                        max_splits = min(1, sheet_data[target_col].str.count("-").max())
                        log_info(f"Splitting '{target_col}' with max_splits: {max_splits}")
                        # st.write(f"max_splits: {max_splits}")

                        if max_splits == 1:
                            # Perform the split using the selected target column
                            split_columns = sheet_data[target_col].str.split("-", n=max_splits, expand=True)
                            column_names = ["FUND", "GL"][:split_columns.shape[1]]
                            sheet_data[column_names] = split_columns.astype(str)
                            # sheet_data[['Fund', 'Gl']] = sheet_data[target_col].str.split("-", n=max_splits, expand=True)

                        else:
                            split_columns = sheet_data[target_col].str.split("-", n=max_splits, expand=True)
                            column_names = ["FUND", "GL", "AWARD_CODE"][:split_columns.shape[1]]
                            sheet_data[column_names] = split_columns
                            # sheet_data[['Fund', 'Gl', 'Award_Code']] = sheet_data[target_col].str.split("-", n=max_splits, expand=True)

                # st.write("true")
                # Filter TB data for rows containing "cash and cash equivalent" in "Map Description"
                rename_mapping = {}
                for col in sheet_data.columns:
                    col_lower = col.lower()
                    if "cfda" in col_lower:
                        rename_mapping[col] = "CFDA"
                        # Rename for specific fund-related columns
                    elif col_lower in ["fund", "fund code", "fund number"]:
                        rename_mapping[col] = "FUND_CODE"
                    elif col_lower in ['gl', 'gl code', 'gl_code', 'acct no.']:
                        rename_mapping[col] = "GL_CODE"
                    elif col_lower in ["balance", "2022 balance", "amount", "2021 balance"]:
                        rename_mapping[col] = "Balance"
                    elif col_lower in ["map no", 'map number', 'map no.']:
                        rename_mapping[col] = "Map_No"
                    elif col_lower in ['map description']:
                        rename_mapping[col] = "Map Description"
                # Apply renaming
                sheet_data.rename(columns=rename_mapping, inplace=True)
                print(f"Columns renamed for BB: {sheet_data.columns}")

                print(f"Number of valid rows after cleanup: {len(sheet_data)}")

                # Step 3: Extract valid rows
                extracted_data = manager.process_data(sheet_data, columns)
                combined_data.extend(extracted_data)
                break
            # st.write(extracted_data)
            # Step 4: Save results
            if combined_data:
                # st.write("true")
                result_df = self.post_process_data(combined_data)
                output_path = os.path.join("data", "output", os.path.basename(file_path).replace(".xlsx", ".json"))
                result_df.to_json(output_path, orient="records", indent=4)
                print(f"Processed file saved to: {output_path}")
                return result_df, fund_row_headers
            else:
                print("No valid data found to process.")
                return None, None

        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            return None, None

    def post_process_data(self, combined_data):
        result_df = pd.DataFrame(combined_data).drop_duplicates().reset_index(drop=True)
        # st.write("Normalized Prior Year Trial Balance from BB_Excel_Processor:")
        # st.dataframe(result_df)
        return result_df

