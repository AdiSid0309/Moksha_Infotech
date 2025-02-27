from strategies.headers.single_line_header import SingleLineHeaderStrategy
from strategies.headers.multi_row_header import MultiRowHeaderStrategy
from strategies.headers.ai_header import AiHeaderStrategy
from strategies.data.sefa_simple_data_extraction import SEFASimpleDataExtraction
from utils.validators import find_column
from utils.logger import log_info, log_error
import pandas as pd
import streamlit as st

class SEFAStrategyManager:
    def __init__(self):

        self.header_strategies = [
            AiHeaderStrategy(),
            SingleLineHeaderStrategy(),
            MultiRowHeaderStrategy()
        ]
        self.data_strategy = SEFASimpleDataExtraction()

    def detect_headers_and_columns(self, sheet_name, sheet_data):
        """
        Run all header detection strategies sequentially to find headers and columns.
        """
        keywords = ["CFDA", "AL", "ALN", "CFDA#", "Assistance", "CFDANumber", "CFDA No", "CDFA Number", "Assistance Listing No.", "Listing No."]
        secondary_keywords = ["Total Expenditures", "Expenditures", "Award Number", "Entity Identification",
                              "Contract Number", "Subrecipients", "Title", "Program Name"]

        for strategy in self.header_strategies:
            is_valid_column = False
            idx = 0
            end_idx = min(len(sheet_data), 100)

            while not is_valid_column:
                result = strategy.detect_headers_and_columns(sheet_name, sheet_data, idx, end_idx, keywords,
                                                             secondary_keywords)
                if result is None:
                    break

                idx, combined_headers, mapping = result

                # Store the original row where CFDA was found
                cfda_row_headers = [str(value).strip() for value in sheet_data.iloc[idx].values if pd.notna(value)]
                sheet_data.columns = combined_headers

                # columns = {
                #     "cfda_col": find_column(combined_headers,
                #                             ["cfda", "assistance", 'cdfa number', "al", "cfda#", "cfdanumber", "aln number", "assistance listing no.", "federal catalog number", "cfda no.", 'assistance', 'assistance listing no. federal grants', 'listing no.', 'federal grants']),
                #     "expenditure_col": find_column(combined_headers,
                #                                    ["total expenditures", "federal expenditures", "expenditure",
                #                                     "expenditures", "amount", "current fiscal year expenditures"]),
                #     "title_col": find_column(combined_headers,
                #                              ["program name", "program cluster", "title", "program title"]),
                #     "class_code_col": find_column(combined_headers, ["code", "class code", "class codes", "code no."]),
                #     "fund_col": find_column(combined_headers, ["fund", "program code", "fund codes", "fund no.", 'fund /program #', 'fund - dept id', 'uihs fund']),
                #     "contractnumber_col": find_column(combined_headers, ["contract number", "contract no"]),
                # }
                # st.write(columns)
                if not (mapping['cfda_col'] and mapping['expenditure_col']):
                    idx += 1
                else:
                    is_valid_column = True
                    return idx, combined_headers, mapping, cfda_row_headers

        return None

    def process_data(self, sheet_data, columns):
        """
        Extract valid rows using identified columns.
        """
        return self.data_strategy.extract_data(sheet_data, columns)
