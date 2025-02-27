import pandas as pd
import os
from strategies.sefa_strategy_manager import SEFAStrategyManager
from utils.logger import log_info, log_error
from processors.base_processor import BaseProcessor
import streamlit as st

class SEFAExcelProcessor(BaseProcessor):
    def process(self, file_path):
        try:
            log_info(f"Starting processing of file: {file_path}")
            combined_data = []
            manager = SEFAStrategyManager()

            # Read all sheets in the Excel file
            df = pd.read_excel(file_path, sheet_name=None, header=None)

            for sheet_name, sheet_data in df.items():
                log_info(f"Processing sheet: {sheet_name}")

                # Step 1: Detect headers and find required columns
                result = manager.detect_headers_and_columns(sheet_name, sheet_data)
                if result is None:
                    log_info(f"Failed to detect headers or required columns in sheet '{sheet_name}'. Skipping.")
                    continue

                anchor_row_index, headers, columns, cfda_row_headers = result

                log_info(f"Detected Headers: {list(headers)}")
                log_info(f"CFDA Row Headers: {cfda_row_headers}")
                log_info(f"Columns Found: {columns}")

                # Step 2: Set headers and clean data
                sheet_data.columns = headers
                log_info(f"Column names before renaming: {sheet_data.columns}")
                sheet_data = sheet_data.dropna(subset=sheet_data.columns.difference(['CFDA']), how='all')


                # Step 3: Rename columns based on logic
                rename_mapping = {}
                for col in sheet_data.columns:
                    col_lower = col.lower()
                    if col_lower in ['cfda', 'federal cfda', 'cfda #', 'cfda no.', 'assistance', 'assistance listing no.',  'federal catalog number', 'cfdanumber', 'cfda number']:
                        rename_mapping[col] = "CFDA"
                    elif col_lower in ['beg grant ar / (unearned revenue)', "grant receivable", "deferred revenues"]:
                        rename_mapping[col] = "Beginning_Balance"
                    elif col_lower in ["grant id number", "fund", "fund code", "fund number", "fund codes", "program #", "fund /program #", 'fund no.', 'fund - dept id', 'fund/program', 'uihs fund']:
                        rename_mapping[col] = "FUND_CODE"
                    elif col_lower in ['current fiscal year expenditures', 'expenditures', 'total expenditures',
                                       'expenditures (total, fund)', 'federal expenditures', 'total federal expenditures', 'net expenses', 'cy']:
                        rename_mapping[col] = "EXPENDITURES"
                    elif col_lower in ['grantor/program title', 'program name', 'program title']:
                        rename_mapping[col] = "Programs"
                    elif col_lower in ['federal revenues']:
                        rename_mapping[col] = "Federal_Revenues"

                sheet_data.rename(columns=rename_mapping, inplace=True)
                # Ensure CFDA is a string type
                sheet_data["CFDA"] = sheet_data["CFDA"].astype(str)

                # Keep rows where CFDA contains at least one digit
                sheet_data = sheet_data[sheet_data["CFDA"].str[0].str.isdigit()]

                log_info(f"Number of valid rows after cleanup: {len(sheet_data)}")

                # Step 3: Extract valid rows
                extracted_data = manager.process_data(sheet_data, columns)
                combined_data.extend(extracted_data)

                break
            # Step 4: Save results
            if combined_data:
                # st.write(combined_data)
                result_df = self.post_process_data(combined_data)
                result_df = result_df.loc[:, ~result_df.columns.str.match(r'^(Unnamed.*|None.*)$')]
                result_df['CFDA'] = result_df['CFDA'].astype(str)
                result_df = result_df[result_df['CFDA'].str.contains(r'^\d{2}\.', na=False, regex=True)]
                output_path = os.path.join("data", "output", os.path.basename(file_path).replace(".xlsx", ".json"))
                result_df.to_json(output_path, orient="records", indent=4)
                log_info(f"Processed file saved to: {output_path}")
                return result_df, cfda_row_headers
            else:
                log_error("No valid data found to process.")
                return None, None
        except Exception as e:
            log_error(f"Error processing file {file_path}: {str(e)}")
            return None, None

    def post_process_data(self, combined_data):
        result_df = pd.DataFrame(combined_data).reset_index(drop=True)
        return result_df
