import pandas as pd
import json

# if high risk then 40% min else 20% min
def amount_to_be_tested(risk_type,total_federal_exp):
  if risk_type == 'High':
    return total_federal_exp * 0.4
  else:
    return total_federal_exp * 0.2
  



# threshold for type A and type B from table
def threshold_for_type(total_federal_exp):
  if total_federal_exp >= 750000 and total_federal_exp <= 25e6:
    return 750000
  elif total_federal_exp > 25e6 and total_federal_exp <= 100e6:
    return total_federal_exp * 0.03
  elif total_federal_exp > 100e6 and total_federal_exp <= 1e9:
    return 3e6
  elif total_federal_exp > 1e9 and total_federal_exp <= 10e9:
    return total_federal_exp * 0.003
  elif total_federal_exp > 10e9 and total_federal_exp <= 20e9:
    return 30e6
  elif total_federal_exp > 20e9:
    return total_federal_exp * 0.0015
  


# identify type A or type B
def identify_typeA_typeB( exp_total, threshold):
  if exp_total > threshold:
    return 'A'
  else:
    return 'B'
  

# def process_df(df):
#   # df = pd.read_excel(path)
#   df = df.dropna(axis=1, how='all')
#   df = df.dropna(axis=0, how='all')
#   # print(df)
#   # start_index = df[df.iloc[:, 1].astype(str).str.contains('Federal Program', na=False, case=False)].index[0]
#   start_index = next(iter(df[df.astype(str).apply(lambda row: row.str.contains('Federal Program', na=False, case=False)).any(axis=1)].index), None)
#   # end_index = df[df.iloc[:, 1].astype(str).str.contains('Total Expenditure of Federal Awards', na=False, case=False)].index[0]
#   end_index = next(iter(df[df.astype(str).apply(lambda row: row.str.contains('Total Expenditure of Federal Awards', na=False, case=False)).any(axis=1)].index), None)
#   df_table = df.loc[start_index:end_index].reset_index(drop=True)
#   df_table.columns = df_table.iloc[0]
#   df_table = df_table.drop(columns=df_table.columns[0])
#   df_table = df_table[['Federal Program', 'Assistance Listing Number', 'Expenditure Total by ALN', 'Type A or B' ]]
#   df_table.drop([0], inplace=True)
#   df_filtered = df_table[df_table['Type A or B'].notna()]
#   df_filtered = df_filtered[['Federal Program', 'Assistance Listing Number', 'Expenditure Total by ALN' ]]
#   total_federal_exp = df_filtered['Expenditure Total by ALN'].sum()
#   return df_filtered, total_federal_exp

def process_df(df):
  print(df.columns)
  new_df = df[['CFDA', 'EXPENDITURES']]
  new_df = new_df[new_df['CFDA'] != 'NONFED']
  new_df = new_df.groupby('CFDA', as_index=False).agg({'EXPENDITURES': 'sum'})
  new_df = new_df[new_df['EXPENDITURES'] > 0]
  new_df = new_df[new_df['EXPENDITURES'].notna()]
  new_df = new_df.reset_index(drop=True)
  total_federal_exp = new_df['EXPENDITURES'].sum()
  return new_df, total_federal_exp
 


def typeA_list(df):
  print(df[df['Type A or B'] == 'A'])
  return df[df['Type A or B'] == 'A']



def typeB_list(df):
  print(df[df['Type A or B'] == 'B'])
  return df[df['Type A or B'] == 'B']






