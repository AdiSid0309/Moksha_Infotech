import pandas as pd
import re
import pymupdf
import tabula
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings

BATCH_SIZE = 100

def embed_large_file(file_path, collection):
    """Batch-process PDF with PyMuPDF for text and pdfplumber for tables"""
    documents, metadatas, ids = [], [], []
    chunk_id = 1

    # First pass: Extract text with PyMuPDF (fast)
    with pymupdf.open(file_path) as doc:
        for page_num, page in enumerate(doc, 1):
            text = page.get_text("text").strip()
            if text:
                paragraphs = [p for p in text.split('\n\n') if p.strip()]
                for para in paragraphs:
                    cleaned = re.sub(r'\s+', ' ', para).strip()
                    documents.append(cleaned)
                    metadatas.append({"page": page_num})
                    ids.append(f"chunk_{chunk_id}")
                    chunk_id += 1

                    # Batch add
                    if len(documents) >= BATCH_SIZE:
                        collection.add(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                        documents, metadatas, ids = [], [], []

    # Add remaining items
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

def find_table(query, pattern, collection):
    """Find the exact match using similarity search and return page numbers"""
    exact_match_pages = []

    # Perform similarity search to get a broad set of results
    candidates = collection.query(
        query_texts=[query],
        n_results=500  # Retrieve a broader set of results
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

def create_collection():
    client = chromadb.HttpClient(
        host="localhost",
        port=8000,
        ssl=False,
        settings=Settings(),
        tenant="default_tenant",  # Replace if using multi-tenant setup
        database="default_database"  # Ensure it's the correct database
    )
    # temp_dir = 'D:\Moksha Infotech\Office\CODE\RiskQA\chromadb'
    # client = chromadb.PersistentClient(path=temp_dir)

    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-MiniLM-L12-v2"
    )

    # Create or retrieve the collection
    collection_pdf = client.get_or_create_collection(
        name="pdf_collection",
        embedding_function=embedding_function
    )

    print("✅ Connected to ChromaDB and Collection Created!")
    return collection_pdf

def compliance_table(uploaded_file, collection_pdf):
    file_path = uploaded_file  # Use the uploaded file path
    embed_large_file(file_path, collection_pdf)
    print("PDF loaded into collection")

    query = "APPENDIX IV INTERNAL REFERENCE TABLES"
    pattern = re.compile(r"APPENDIX\s+IV.*INTERNAL\s+REFERENCE\s+TABLES")

    matched_pages = find_table(query, pattern, collection_pdf)  # Query PDF collection
    print(f"Table found at {matched_pages}")

    table = None
    if matched_pages:
        pages = []
        for i in matched_pages:
            pages.append(i)
            pages.append(i + 1)
        print(pages)
        table = extract_table_from_pdf(file_path, pages)
        if table is not None:
            table.rename(columns={"Assistance Listing (CFDA)": "ALN"}, inplace=True)
    else:
        print("No exact match found.")
    return table
