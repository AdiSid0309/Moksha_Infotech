import pandas as pd
import re
import pymupdf
import tabula
import time
import math
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
from .compliance import create_collection, compliance_table


def find_aln(query, pattern, collection):
    """Find the exact match using similarity search and return page numbers"""
    exact_match_pages = []

    # Perform similarity search to get a broad set of results
    candidates = collection.query(
        query_texts=[query],
        n_results=1000  # Retrieve a broader set of results
    )

    for i, doc in enumerate(candidates["documents"][0]):
        metadata = candidates["metadatas"][0][i]  # Get metadata for page number
        if metadata is None:
            continue
        else:
            page_number = metadata.get("page", "Unknown")

            if re.search(pattern, doc):
                exact_match_pages.append(page_number)
                print(f"{query} found on page: {page_number}")  # Print the page number

    return exact_match_pages


def load_csv(csv_path):
    """Loads CSV containing program data."""
    print(f"Loading CSV file: {csv_path}")
    return pd.read_csv(csv_path)


def identify_high_risk_type_b_programs(threshold, low_risk_a_data, high_risk_b_data):
    """Identifies high-risk Type B programs based on Type A program risk assessment."""
    print(type(threshold))
    TYPE_A_THRESHOLD = threshold  # Define the threshold for Type A programs (e.g., $750,000)  --change this --done
    TYPE_B_THRESHOLD = TYPE_A_THRESHOLD * 0.25
    print("Processing Low-Risk Type A programs...")
    num_low_risk_a = len(low_risk_a_data)
    print(f"Number of low-risk Type A programs: {num_low_risk_a}")
    min_type_b_count = math.ceil(num_low_risk_a * 0.25)
    print(f"Minimum Type B programs needed: {min_type_b_count}")
    high_risk_b_programs = high_risk_b_data[high_risk_b_data["Expenditures"] > TYPE_B_THRESHOLD]
    high_risk_b_programs = high_risk_b_programs.sort_values(by="Expenditures", ascending=False)
    print(f"Filtered {len(high_risk_b_programs)} high-risk Type B programs above threshold.")
    return high_risk_b_programs, min_type_b_count


def extract_table_from_pdf(pdf_path, pages):
    """Extract tables from the specified PDF using Tabula and clean the extracted data."""
    # Extract tables from both pages
    tables = tabula.read_pdf(pdf_path, pages=pages, multiple_tables=True)

    if tables:
        # Extract the first table
        df_page_1 = tables[0]

        # If there is a second table, handle it
        if len(tables) > 1:
            # Extract the second table
            df_page_2 = tables[1]

            # Store column names from the first and second tables
            column_names1 = df_page_1.columns
            column_names2 = df_page_2.columns

            # Create a DataFrame with the column names as a row for df_page_2
            column_names_row = pd.DataFrame([column_names2], columns=column_names2)

            # Add this new row to the top of df_page_2
            df_page_2 = pd.concat([column_names_row, df_page_2], ignore_index=True)

            # Apply the column names from df_page_1 to df_page_2
            df_page_2.columns = column_names1

            # Concatenate the two dataframes into a single DataFrame
            df_merged = pd.concat([df_page_1, df_page_2], ignore_index=True)
        else:
            # If there's only one table, just use it
            df_merged = df_page_1

        # Fixing wrapped text: Merge rows where the first column is empty
        merged_rows = []
        temp_row = None

        for row in df_merged.itertuples(index=False, name=None):
            if pd.isna(row[0]):  # If the first column is NaN, it's a continuation of the previous row
                if temp_row is not None:
                    temp_row = list(temp_row)  # Convert tuple to list
                    temp_row = [
                        (temp_row[i] + " " + str(row[i]).strip()) if pd.notna(row[i]) else temp_row[i]
                        for i in range(len(row))
                    ]
            else:
                if temp_row is not None:
                    merged_rows.append(temp_row)  # Save previous merged row
                temp_row = list(row)  # Start a new row

        if temp_row:
            merged_rows.append(temp_row)  # Append the last row

        # Create cleaned DataFrame
        df_cleaned = pd.DataFrame(merged_rows, columns=df_merged.columns)

        # Save to CSV/Excel
        df_cleaned.to_csv(f"{pdf_path}.csv", index=False)

        return df_cleaned
    else:
        print("❌ No tables found.")


def func(threshold, table, collection_pdf, low_risk_a_data, high_risk_b_data):
    # Load Data
    low_risk_a_data = load_csv(low_risk_a_data)
    high_risk_b_data = load_csv(high_risk_b_data)

    # Identify high-risk Type B programs
    high_risk_b_programs, num_low_risk_a = identify_high_risk_type_b_programs(threshold, low_risk_a_data, high_risk_b_data)

    selected_high_risk_b_programs = []
    print(num_low_risk_a)
    if num_low_risk_a > 0:
        for index, row in high_risk_b_programs.iterrows():
            # Define the query and regex pattern
            query = f"ASSISTANCE LISTING {row['ALN']}"
            print(query)
            pattern = re.compile(rf"ASSISTANCE\s+LISTING\s+{re.escape(str(row['ALN']))}")

            # Check if ALN is in the compliance table
            if str(row['ALN']) in table['ALN'].values:
                print(f"{row['ALN']} is a high risk type b")
                selected_high_risk_b_programs.append({"program_name": row['ALN'], "expenditure": row['Expenditures'], "risk": "High Risk type B"})
            else:
                # Find the pages where the pattern exists in the compliance PDF
                matched_pages_pdf = find_aln(query, pattern, collection_pdf)
                if matched_pages_pdf:
                    # If found in PDF but not in table, further logic could be added here if needed
                    pass
                else:
                    selected_high_risk_b_programs.append({"program_name": row['ALN'], "expenditure": row['Expenditures'], "risk": "High Risk type B"})
            if len(selected_high_risk_b_programs) >= num_low_risk_a:
                break

        risk_df = pd.DataFrame(selected_high_risk_b_programs)

        risk_df.to_csv("HIGH_RISK_B.CSV", index=False)
        return risk_df
    return None