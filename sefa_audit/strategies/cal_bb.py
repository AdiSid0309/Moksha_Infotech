# import pandas as pd
# import streamlit as st
# from utils.logger import log_info, log_error
#
# class CAL_BB:
#     def __init__(self):
#         pass
#     def get_bb(self, sefa_df, bb_df):
#         # log_info("True")
#         # st.write(sefa_df.columns)
#         if 'Balance' not in bb_df.columns:
#             raise KeyError("The column 'Beginning_Balance' is missing in the DataFrame.")
#
#         if 'FUND_CODE' not in bb_df.columns:
#             raise KeyError("The column 'FUND_CODE' is missing in the DataFrame.")
#         if 'FUND_CODE' in sefa_df.columns:
#             # Create a new list to store split fund codes
#
#             final_amounts = []
#             # st.write("true")
#
#             # Iterate through the DataFrame
#             for _, row in sefa_df.iterrows():
#                 final_amount = 0  # Initialize total amount to 0
#                 # Check if FUND_CODE is iterable (e.g., a list of codes)
#                 # st.write(row['Normalized_Fund'])
#                 # st.write(row['Normalized_Fund'])
#                 if isinstance(row['Normalized_Fund'], list):
#                     for fund in row['Normalized_Fund']:
#                         # for i in fund:
#                         #     st.write(i)
#                         # Filter rows in tb_df based on FUND_CODE
#                         filtered_df = bb_df[bb_df['FUND_CODE'] == fund]
#                         # st.write("true")
#                         # st.write("from cal_bb")
#                         # st.dataframe(filtered_df)
#                         for _, tb_row in filtered_df.iterrows():
#                             map_d_value = tb_row['Map Description']
#                             if map_d_value in [
#                                 'Grant Receivable',
#                                 'Unearned revenue',
#                                 'Deferred Revenues',
#                                 'Grants Receivable',
#                                 'Unearned revenues',
#                                 'Deferred Revenues',
#                                 'Unearned grant revenue',
#                             ]:
#                                 final_amount += tb_row['Balance']
#                 # st.write(final_amount)
#                 final_amounts.append(final_amount)
#             sefa_df['BEGINNING_BALANCE'] = final_amounts
#         selected_columns = ['CFDA', 'Normalized_Fund', 'BEGINNING_BALANCE']
#         variance_df = sefa_df[selected_columns]
#         return variance_df
import pandas as pd
import streamlit as st
from utils.logger import log_info, log_error


class CAL_BB:
    def __init__(self):
        pass

    def get_bb(self, sefa_df, bb_df):
        if 'Balance' not in bb_df.columns:
            raise KeyError("The column 'Beginning_Balance' is missing in the DataFrame.")

        if 'FUND_CODE' not in bb_df.columns:
            raise KeyError("The column 'FUND_CODE' is missing in the DataFrame.")

        if 'FUND_CODE' in sefa_df.columns:
            final_amounts = []

            # Iterate through the DataFrame
            for _, row in sefa_df.iterrows():
                final_amount = 0  # Initialize total amount to 0
                if isinstance(row['Normalized_Fund'], list):
                    for fund in row['Normalized_Fund']:
                        # Filter rows in bb_df based on FUND_CODE
                        filtered_df = bb_df[bb_df['FUND_CODE'] == fund]
                        for _, tb_row in filtered_df.iterrows():
                            map_d_value = tb_row['Map Description']
                            if map_d_value in [
                                'Grant Receivable',
                                'Unearned revenue',
                                'Deferred Revenues',
                                'Grants Receivable',
                                'Unearned revenues',
                                'Deferred Revenues',
                                'Unearned grant revenue',
                            ]:
                                final_amount += tb_row['Balance']
                final_amounts.append(final_amount)
            sefa_df['BEGINNING_BALANCE'] = final_amounts

        # Select columns
        selected_columns = ['CFDA', 'Normalized_Fund', 'BEGINNING_BALANCE']
        variance_df = sefa_df[selected_columns]

        # Convert Normalized_Fund lists to tuples for deduplication
        variance_df['Normalized_Fund'] = variance_df['Normalized_Fund'].apply(tuple)

        # Drop duplicates based on CFDA and Normalized_Fund
        variance_df = variance_df.drop_duplicates(subset=['CFDA', 'Normalized_Fund'], keep='first')

        # Convert Normalized_Fund back to lists if needed
        variance_df['Normalized_Fund'] = variance_df['Normalized_Fund'].apply(list)

        return variance_df