import pandas as pd

class GLSimpleDataExtraction:
    def extract_data(self, sheet_data, columns):
        """
        Extract rows with valid CFDA numbers using the provided column mapping.
        """
        extracted_data = []

        # Iterate over rows and extract all values for rows with valid data
        for _, row in sheet_data.iterrows():
            row_data = {
                col: row[col]
                for col in sheet_data.columns
                if (not isinstance(row[col], pd.Series) and pd.notna(row[col])) or
                   (isinstance(row[col], pd.Series) and pd.notna(row[col]).all())
            }
            extracted_data.append(row_data)

        return extracted_data
