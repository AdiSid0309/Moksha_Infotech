# import pandas as pd
# from langchain.llms import OpenAI
# from langchain_community.chat_models import ChatOpenAI
# from langchain.schema import HumanMessage
# import os
# from strategies.headers.base_header_strategy import BaseHeaderStrategy
# import re
# import abc
# from utils.logger import log_info, log_error
# import json
# import streamlit as st
#
# # Set API keys
# openai_api_key = os.getenv("OPENAI_API_KEY")
# # Helper functions
#
#
# class AiHeaderStrategy(BaseHeaderStrategy):
#     def __init__(self):
#         self.llm = ChatOpenAI(model="gpt-4", temperature=0)
#
#     def get_openai_response(self, llm, prompt):
#         return self.llm([HumanMessage(content=prompt)]).content
#
#     def detect_headers_and_columns(self, sheet_name, sheet_data, start_idx, end_idx, keywords, secondary_keywords=[], max_offset=5):
#         anchor_row_index = self.detect_anchor_row(sheet_name, sheet_data, start_idx, end_idx, keywords)
#         if anchor_row_index is None or anchor_row_index == 0:
#             return None
#
#         # Adjusted slicing to include the row above the anchor row
#         start_slice = max(0, anchor_row_index - 2)
#         processed_data = sheet_data.iloc[start_slice:].copy()
#         processed_data.reset_index(drop=True, inplace=True)
#
#         # Calculate new anchor position
#         new_anchor_pos = anchor_row_index - start_slice
#
#         # Get both rows: current and previous row (above main row)
#         header_row_above = processed_data.iloc[new_anchor_pos - 1].fillna("") if new_anchor_pos > 0 else pd.Series([""] * len(sheet_data.columns))
#         header_row = processed_data.iloc[new_anchor_pos].fillna("")
#
#         # Combine headers by merging both rows
#         combined_headers = header_row_above.astype(str) + " " + header_row.astype(str)
#         combined_headers = combined_headers.str.strip().replace("", None)
#
#         # Retain only non-empty columns
#         non_empty_cols = combined_headers[combined_headers.notna()].index
#         processed_data = processed_data[non_empty_cols]
#
#         # Set headers and clean data
#         processed_data.columns = combined_headers.dropna()
#         rows_to_drop = [new_anchor_pos]
#         if new_anchor_pos > 0:
#             rows_to_drop.append(new_anchor_pos - 1)
#         processed_data = processed_data.drop(rows_to_drop).reset_index(drop=True)
#
#         # Prepare header info for AI analysis
#         next_row = processed_data.iloc[0] if len(processed_data) > 0 else pd.Series()
#         header_info = {
#             'main_row': header_row.tolist(),
#             'above_row': header_row_above.tolist(),
#             'combined_headers': combined_headers.tolist(),
#             'next_row': next_row.tolist()
#         }
#
#         # Generate AI prompt
#         prompt = f"""Analyze these Excel column headers:
#         Above row: {header_info['above_row']}
#         Main row: {header_info['main_row']}
#         Combined headers: {header_info['combined_headers']}
#         Next row: {header_info['next_row']}
#
#         Create JSON with:
#         1. combined_headers (list)
#         2. mapping (cfda_col, expenditure_col, title_col, fund_col)
#         3. for expenditure column select only one column that is for current year and relevant column and rename it to 'Expenditures'
#         4. if the expenditure column has sub columns then select current year column(cy) or the column with latest updates and do not create a list for the values.
#         5. include empty columns as ''.
#         """
#         log_info(prompt)
#         print("==========================================================================================")
#         # Process AI response
#         response = self.get_openai_response(self.llm, prompt)
#         log_info(response)
#         try:
#             json_str = re.search(r'\{.*\}', response, re.DOTALL).group()
#             analysis = json.loads(json_str)
#             combined_headers = analysis['combined_headers']
#
#             # Process headers to replace empty strings and deduplicate
#             processed_headers = []
#             seen_headers = {}
#             for idx, header in enumerate(combined_headers):
#                 # Replace empty or whitespace-only headers
#                 if not str(header).strip():
#                     header = f"Unnamed_{idx}"
#                 else:
#                     header = str(header).strip()
#
#                 # Deduplicate headers
#                 if header in seen_headers:
#                     seen_headers[header] += 1
#                     new_header = f"{header}_{seen_headers[header]}"
#                 else:
#                     seen_headers[header] = 0
#                     new_header = header
#                 processed_headers.append(new_header)
#             return (anchor_row_index, processed_headers, analysis.get('mapping', {}))
#
#         except Exception as e:
#             log_error(f"Failed to parse AI response: {e}")
#             return None

import pandas as pd
import os
from huggingface_hub import InferenceClient
from utils.logger import log_info, log_error
import json
import re
from strategies.headers.base_header_strategy import BaseHeaderStrategy
from huggingface_hub import login
# API setup
login(token="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")
# Set API keys
hf_api_key = "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"  # Ensure this is set in your environment or hardcode it for testing


class AiHeaderStrategy(BaseHeaderStrategy):
    def __init__(self):
        # Initialize the Hugging Face InferenceClient with the Mistral model
        self.client = InferenceClient(model="mistralai/Mistral-7B-Instruct-v0.3", token=hf_api_key)

    def get_mistral_response(self, prompt):
        # Prepare the message in the format expected by Mistral
        messages = [{"role": "user", "content": prompt}]

        # Call the Mistral model via InferenceClient
        try:
            response = self.client.chat.completions.create(
                model="mistralai/Mistral-7B-Instruct-v0.3",
                messages=messages,
                max_tokens=20992  # Adjust as needed
            )
            return response.choices[0].message.content
        except Exception as e:
            log_error(f"Error calling Mistral model: {e}")
            return None

    def detect_headers_and_columns(self, sheet_name, sheet_data, start_idx, end_idx, keywords, secondary_keywords=[], max_offset=5):
        anchor_row_index = self.detect_anchor_row(sheet_name, sheet_data, start_idx, end_idx, keywords)
        if anchor_row_index is None or anchor_row_index == 0:
            return None

        # Adjusted slicing to include the row above the anchor row
        start_slice = max(0, anchor_row_index - 2)
        processed_data = sheet_data.iloc[start_slice:].copy()
        processed_data.reset_index(drop=True, inplace=True)

        # Calculate new anchor position
        new_anchor_pos = anchor_row_index - start_slice

        # Get both rows: current and previous row (above main row)
        header_row_above = processed_data.iloc[new_anchor_pos - 1].fillna("") if new_anchor_pos > 0 else pd.Series([""] * len(sheet_data.columns))
        header_row = processed_data.iloc[new_anchor_pos].fillna("")

        # Combine headers by merging both rows
        combined_headers = header_row_above.astype(str) + " " + header_row.astype(str)
        combined_headers = combined_headers.str.strip().replace("", None)

        # Retain only non-empty columns
        non_empty_cols = combined_headers[combined_headers.notna()].index
        processed_data = processed_data[non_empty_cols]

        # Set headers and clean data
        processed_data.columns = combined_headers.dropna()
        rows_to_drop = [new_anchor_pos]
        if new_anchor_pos > 0:
            rows_to_drop.append(new_anchor_pos - 1)
        processed_data = processed_data.drop(rows_to_drop).reset_index(drop=True)

        # Prepare header info for AI analysis
        next_row = processed_data.iloc[0] if len(processed_data) > 0 else pd.Series()
        header_info = {
            'main_row': header_row.tolist(),
            'above_row': header_row_above.tolist(),
            'combined_headers': combined_headers.tolist(),
            'next_row': next_row.tolist()
        }

        # Generate AI prompt
        prompt = f"""Analyze these Excel column headers:
                Above row: {header_info['above_row']}
                Main row: {header_info['main_row']}
                Combined headers: {header_info['combined_headers']}
                Next row: {header_info['next_row']}

                Create JSON with:
                1. combined_headers (list)
                2. mapping (cfda_col, expenditure_col, title_col, fund_col)
                3. for expenditure column select only one column that is for current year and relevant column and rename it to 'Expenditures'
                4. if the expenditure column has sub columns then select current year column(cy) or the column with latest updates and do not create a list for the values.
                5. include empty columns as ''.
                """
        log_info(prompt)
        print("==========================================================================================")

        # Process AI response
        response = self.get_mistral_response(prompt)
        log_info(response)
        if not response:
            return None

        try:
            json_str = re.search(r'\{.*\}', response, re.DOTALL).group()
            analysis = json.loads(json_str)
            combined_headers = analysis['combined_headers']

            # Process headers to replace empty strings and deduplicate
            processed_headers = []
            seen_headers = {}
            for idx, header in enumerate(combined_headers):
                # Replace empty or whitespace-only headers
                if not str(header).strip():
                    header = f"Unnamed_{idx}"
                else:
                    header = str(header).strip()

                # Deduplicate headers
                if header in seen_headers:
                    seen_headers[header] += 1
                    new_header = f"{header}_{seen_headers[header]}"
                else:
                    seen_headers[header] = 0
                    new_header = header
                processed_headers.append(new_header)
            return (anchor_row_index, processed_headers, analysis.get('mapping', {}))

        except Exception as e:
            log_error(f"Failed to parse AI response: {e}")
            return None