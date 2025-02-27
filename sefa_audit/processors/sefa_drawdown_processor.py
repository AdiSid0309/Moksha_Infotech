import streamlit
from utils.logger import log_info, log_error
import json
import io

class SefaDrawdownProcessor():
    # Filter SEFA Dataframe and return Unique FUND CODES
    def filter_sefa(self, sefa_df):
        # Save body (data) of all three files without column names
        sefa_body = sefa_df.values.tolist()
        unique_fund_codes = sefa_df['FUND_CODE'].unique()
        # print(unique_fund_codes)
        with open('data/output/sefa_body.json', 'w') as sefa_file:
            json.dump(sefa_body, sefa_file, indent=4)
        return unique_fund_codes

    # Filter TB DataFrame
    def filter_tb(self,tb_df):
        # Save the filtered TB body (values only) to a JSON file
        tb_filtered = tb_df[tb_df['Map Description'].str.contains('cash and cash equivalent', case=False, na=False)]
        tb_filtered_body = tb_df.values.tolist()
        # Get unique GL codes from the filtered TB data
        unique_gl_codes = tb_filtered['GL_CODE'].unique()
        with open('data/output/tb_body.json', 'w') as tb_filtered_file:
            json.dump(tb_filtered_body, tb_filtered_file, indent=4)
        return tb_filtered, unique_gl_codes

    # Filter TB DataFrame
    def filter_bb(self, bb_df):
        # Save the filtered TB body (values only) to a JSON file
        bb_filtered = bb_df[
            bb_df['Map Description'].str.contains('grant receivable', case=False, na=False)|
            bb_df['Map Description'].str.contains('unearned revenue', case=False, na=False)|
            bb_df['Map Description'].str.contains('deferred revenues', case=False, na=False)|
            bb_df['Map Description'].str.contains('unearned grant revenue', case=False, na=False)|
            bb_df['Map Description'].str.contains('deferred revenue', case=False, na=False)
        ]
        # log_info("true")
        # streamlit.write("true")
        bb_filtered_body = bb_df.values.tolist()
        # Get unique GL codes from the filtered TB data
        # unique_gl_codes = bb_filtered['GL_CODE'].unique()
        with open('data/output/bb_body.json', 'w') as bb_filtered_file:
            json.dump(bb_filtered_body, bb_filtered_file, indent=4)
        return bb_filtered

    # Filter GL DataFrame based on TB codes
    def filter_gl(self,gl_df, unique_gl_codes):
        # Filter GL data based on the unique GL codes and Debit > 0
        rename_mapping = {}
        for col in gl_df.columns:
            # streamlit.write(col)
            col_lower = col.lower()
            if "cfda" in col_lower:
                rename_mapping[col] = "CFDA"
                # Rename for specific fund-related columns
            elif col_lower in ["fund", "fund code", "fund number"]:
                rename_mapping[col] = "FUND_CODE"
            elif "gl" in col_lower and "code" in col_lower:
                rename_mapping[col] = "GL_CODE"
            elif "gl" in col_lower:
                rename_mapping[col] = "GL"
        # Apply renaming
        gl_df.rename(columns=rename_mapping, inplace=True)
        gl_filtered = gl_df[(gl_df['GL_CODE'].isin(unique_gl_codes)) & (gl_df['Debit'] > 0)]
        # Save the filtered GL body (values only) to a JSON file
        gl_filtered_body = gl_filtered.values.tolist()
        with open('data/output/gl_body.json', 'w') as gl_filtered_file:
            json.dump(gl_filtered_body, gl_filtered_file, indent=4)
        return gl_filtered

    # Map function to process GL records
    def map_function(self,batch, headers_json, sefa_data, tb_data, gl_data, model):
        prompt = f"** Context: Federal Grant Program Details {headers_json['SEFA_Headers']} {sefa_data} " \
                 f"** Context: Trial Balance {headers_json['TB_Headers']} {tb_data} " \
                 f"** Context: General Ledger {headers_json['GL_Headers']} {gl_data[:batch]} " \
                 f"map all 3 context and using this mapping provide cash receipt for Federal grant Program from gl" \
                 f"Respond with 'yes' or 'no' for each record. Also give the reason in the response for each record why transaction can be associated with the federal program. Also give the confidence score for the same            Generate the output as JSON." \
                 f"Only show the JSON" \
                 f"the output should be in the following format" \
                 f"{{'Fund_Code': string, 'GL_Code': string, 'Account_String': string, 'Description': string, 'Relevant': bool, 'reason': string, 'confidence': number}}" \
                 f"give me total for cash reciept."
        return model.predict(prompt)

    def process(self, headers_json, gl_filtered, sefa_df, tb_filtered, unique_fund_codes, batch_size, model):

        if gl_filtered is not None and not gl_filtered.empty:
            gl_records = gl_filtered.to_dict(orient='records')
            relevant_responses = []
            for fund in unique_fund_codes:
                print(fund)
                if fund == '714':
                    break
                # streamlit.dataframe(sefa_df.loc[sefa_df['FUND'] == "953"])
                tb_filtered = tb_filtered.drop('Map No.', axis=1)
                sefa_data = sefa_df.loc[sefa_df['FUND_CODE'] == "26"]
                tb_data = tb_filtered.loc[tb_filtered['FUND_CODE'] == "26"]
                gl_data = gl_filtered.loc[gl_filtered['FUND_CODE'] == "26"]
                i = 0
                while i < len(gl_data):
                    responses = self.map_function(batch_size, headers_json, sefa_data, tb_data, gl_data, model)

                    if responses.startswith("```json"):
                        responses = responses[7:]  # Remove the initial ```json
                    if responses.endswith("```"):
                        responses = responses[:-3]  # Remove the ending ```

                    # Find the first [ and last ]
                    start_idx = responses.find('[')
                    end_idx = responses.rfind(']') + 1

                    if start_idx != -1 and end_idx != -1:
                        json_str = responses[start_idx:end_idx]
                        # Parse the JSON string into a Python object
                        response_list = json.loads(json_str)
                        # Then extend with the parsed object
                        relevant_responses.extend(response_list)


                    i += batch_size
                streamlit.write(f"relevant_responses:{relevant_responses}")
                log_info(f"relevant_responses:{relevant_responses}")

                relevant_gl_codes = [
                    response.get("GL_Code")
                    for response in relevant_responses
                    if isinstance(response, dict) and response.get("Relevant", True)
                ]
                relevant_gl_codes = list(set(relevant_gl_codes))

                gl_selected = gl_filtered[gl_filtered['GL_CODE'].isin(relevant_gl_codes)]
                streamlit.write("gl_selected from func===========")
                streamlit.dataframe(gl_selected)

            return gl_selected
