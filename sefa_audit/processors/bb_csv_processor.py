import pandas as pd
import os
from strategies.tb_strategy_manager import TBStrategyManager
from utils.logger import log_info, log_error
from processors.base_processor import BaseProcessor


class BBCsvProcessor(BaseProcessor):
    def process(self, file_path):
        try:
            log_info(f"Starting processing of file: {file_path}")
            combined_data = []
            manager = TBStrategyManager()

            # Read all sheets in the Excel file
            df = pd.read_csv(file_path, header=None)

            # Step 1: Detect headers and find required columns
            anchor_row_index, headers, columns = manager.detect_headers_and_columns("TB", sheet_data)

            if headers is None or columns is None:
                log_error(f"Failed to detect headers or required columns in sheet 'TB'. Skipping.")

            log_info(f"Detected Headers: {list(headers)}")
            log_info(f"Columns Found: {columns}")

            # Step 2: Set headers and clean data
            sheet_data.columns = headers
            sheet_data = sheet_data.iloc[anchor_row_index + 2:].reset_index(drop=True)
            sheet_data = sheet_data.dropna(how="all")
            log_info(f"Number of valid rows after cleanup: {len(sheet_data)}")

            # Step 3: Extract valid rows
            extracted_data = manager.process_data(sheet_data, columns)
            combined_data.extend(extracted_data)

            # Step 4: Save results
            if combined_data:
                result_df = pd.DataFrame(combined_data).drop_duplicates().reset_index(drop=True)

                # Step 1: Replace non-numeric characters (e.g., $, ,) with an empty string
                result_df['Amount'] = (
                    result_df['Amount']
                        .astype(str)  # Ensure all values are strings for processing
                        .str.replace(r"[^0-9.\-]", "", regex=True)  # Remove all characters except digits, ., and -
                )

                log_info(f"Post Processed df: {result_df}")

                # Step 2: Convert cleaned strings to float
                result_df['Amount'] = pd.to_numeric(result_df['Amount'], errors="coerce")

                # Step 3: Fill NaN values (optional, based on your use case)
                result_df['Fund_Code'] = result_df['Fund_Code'].astype(str)
                result_df['Fund_Code'] = result_df['Fund_Code'].replace("nan", "").replace("None", "")

                result_df['GL_Code'] = result_df['GL_Code'].astype(str)
                result_df['GL_Code'] = result_df['GL_Code'].replace("nan", "").replace("None", "")

                result_df['Account_String'] = result_df['Account_String'].astype(str)
                result_df['Account_String'] = result_df['Account_String'].replace("nan", "").replace("None", "")

                result_df['GL_Title'] = result_df['GL_Title'].astype(str)
                result_df['GL_Title'] = result_df['GL_Title'].replace("nan", "").replace("None", "")

                result_df['Map_No'] = result_df['Map_No'].astype(str)
                result_df['Map_No'] = result_df['Map_No'].replace("nan", "").replace("None", "")

                result_df['Map_Description'] = result_df['Map_Description'].astype(str)
                result_df['Map_Description'] = result_df['Map_Description'].replace("nan", "").replace("None", "")

                output_path = os.path.join("data", "output", os.path.basename(file_path).replace(".xlsx", ".json"))
                result_df.to_json(output_path, orient="records", indent=4)
                log_info(f"Processed file saved to: {output_path}")
            else:
                log_error("No valid data found to process.")

        except Exception as e:
            log_error(f"Error processing file {file_path}: {str(e)}")
