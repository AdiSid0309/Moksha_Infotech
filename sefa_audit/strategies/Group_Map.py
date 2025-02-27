# import pandas as pd
#
#
# class Group_and_map():
#     def __init__(self):
#         pass
#
#     def cal_variance(self, sefa_df, tb_df):
#         if 'FUND_CODE' in sefa_df.columns:
#             has_programs = 'Programs' in sefa_df.columns  # Check if "Programs" column exists
#
#             # Convert Normalized_Fund lists to tuples for grouping
#             sefa_df['Normalized_Fund'] = sefa_df['Normalized_Fund'].apply(lambda x: tuple(x) if isinstance(x, list) else x)
#
#             # Aggregate expenditures by CFDA and Fund
#             grouped_sefa = sefa_df.groupby(['CFDA', 'Normalized_Fund'], dropna=False)['EXPENDITURES'].sum().reset_index()
#
#             # Compute TB_Balance
#             tb_balance_map = {}
#             for _, row in tb_df.iterrows():
#                 fund = row['FUND_CODE']
#                 map_value = str(row['Map_No'])
#                 if map_value[0] >= '5':  # Check if the first character is >= '5'
#                     tb_balance_map[fund] = round(tb_balance_map.get(fund, 0) + row['Amount'], 2)
#
#
#             grouped_sefa['TB_Balance'] = grouped_sefa['Normalized_Fund'].apply(lambda funds: sum(tb_balance_map.get(fund, 0) for fund in funds) if isinstance(funds, tuple) else 0)
#
#             # Compute Variance
#             grouped_sefa['Variances'] = grouped_sefa['EXPENDITURES'] - grouped_sefa['TB_Balance']
#             grouped_sefa['Variances'] = grouped_sefa['Variances'].apply(lambda x: 0 if abs(x) < 1 else x)
#             grouped_sefa['TB_Balance'] = grouped_sefa['TB_Balance'].round(2)
#             grouped_sefa['Variances'] = grouped_sefa['Variances'].round(2)
#
#             return grouped_sefa[['CFDA', 'Normalized_Fund', 'EXPENDITURES', 'TB_Balance', 'Variances']]
#         else:
#             return sefa_df


import pandas as pd

class Group_and_map():
    def __init__(self):
        pass

    def cal_variance(self, sefa_df, tb_df):
        if 'FUND_CODE' in sefa_df.columns:
            # Convert Normalized_Fund lists to tuples (since it's always a list)
            sefa_df = sefa_df.copy()
            sefa_df['Normalized_Fund'] = sefa_df['Normalized_Fund'].apply(lambda x: tuple(x))

            # Keep all SEFA columns, group by CFDA and Normalized_Fund for expenditures
            grouped_sefa = sefa_df.groupby(['CFDA', 'Normalized_Fund'], dropna=False).agg({
                'EXPENDITURES': 'sum',
                # Include other columns by taking first occurrence if needed
                **{col: 'first' for col in sefa_df.columns if col not in ['CFDA', 'Normalized_Fund', 'EXPENDITURES']}
            }).reset_index()

            # Compute TB totals for funds where Map_No starts with '5' or above
            tb_balance_map = {}
            for _, row in tb_df.iterrows():
                fund = str(row['FUND_CODE'])  # Convert to string for consistency
                map_value = str(row['Map_No'])
                if map_value[0] >= '5':  # Filter Map_No >= '5'
                    tb_balance_map[fund] = round(tb_balance_map.get(fund, 0) + row['Amount'], 2)

            # Explode Normalized_Fund tuples into individual funds
            exploded_sefa = grouped_sefa.explode('Normalized_Fund')
            exploded_sefa['Normalized_Fund'] = exploded_sefa['Normalized_Fund'].astype(str)

            # Map TB totals to exploded data
            exploded_sefa['TB_Balance'] = exploded_sefa['Normalized_Fund'].map(tb_balance_map).fillna(0)

            # Group back to original tuples and sum TB_Balance
            final_df = exploded_sefa.groupby(['CFDA', 'Normalized_Fund'], as_index=False).agg({
                'EXPENDITURES': 'first',  # Keep original sum
                'TB_Balance': 'sum',      # Sum TB totals for all funds in tuple
                # Keep other columns
                **{col: 'first' for col in exploded_sefa.columns
                   if col not in ['CFDA', 'Normalized_Fund', 'EXPENDITURES', 'TB_Balance']}
            })

            # Calculate Variance (EXPENDITURES - TB_Balance)
            final_df['Variances'] = final_df['EXPENDITURES'] - final_df['TB_Balance']
            # Set variance to 0 if absolute value < 1 (per document)
            final_df['Variances'] = final_df['Variances'].where(final_df['Variances'].abs() >= 1, 0)

            # Round numbers
            final_df['EXPENDITURES'] = final_df['EXPENDITURES'].round(2)
            final_df['TB_Balance'] = final_df['TB_Balance'].round(2)
            final_df['Variances'] = final_df['Variances'].round(2)

            # Reorder columns to put CFDA, Normalized_Fund, EXPENDITURES, TB_Balance, Variances first
            base_cols = ['CFDA', 'Normalized_Fund', 'EXPENDITURES', 'TB_Balance', 'Variances']
            return final_df[base_cols]
        else:
            return sefa_df

# Example usage:
# sefa_df = pd.DataFrame({
#     'CFDA': ['10.001', '10.001'],
#     'FUND_CODE': ['1', '2'],
#     'Normalized_Fund': [['1', '2'], ['3']],
#     'EXPENDITURES': [100, 200],
#     'Other_Column': ['A', 'B']
# })
# tb_df = pd.DataFrame({
#     'FUND_CODE': [1, 2, 3],
#     'Map_No': ['501', '401', '502'],
#     'Amount': [100, 200, 300]
# })
# gm = Group_and_map()
# result = gm.cal_variance(sefa_df, tb_df)