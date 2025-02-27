import abc
from utils.logger import log_info, log_error
import re

class BaseHeaderStrategy(abc.ABC):
    """
    Base class for header detection strategies.
    Concrete classes must implement detect_headers_and_columns.
    """

    def detect_anchor_row(self, sheet_name, sheet_data, start_idx, end_idx, keywords):
        # Track anchor row for CFDA header
        anchor_row_index = None
        if start_idx is None: start_idx = 0
        if end_idx is None: end_idx = len(sheet_data)

        # Step 1: Search for 'CFDA' anchor row
        for idx, row in sheet_data.iterrows():
            if start_idx > idx:
                continue
            
            if end_idx < idx:
                break
            
            row_str = row.astype(str).fillna("")  # Convert all cells to string
            if any(re.search(rf'\b{re.escape(keyword)}\b', cell, re.IGNORECASE) for cell in row_str for keyword in keywords):
                log_info(f"Found '{keywords}' anchor at row {idx}")
                anchor_row_index = idx
                return anchor_row_index

        if anchor_row_index is None:
            log_error(f"No '{keywords}' anchor found in sheet '{sheet_name}'. Skipping sheet.")
            return None
        
        
    @abc.abstractmethod
    def detect_headers_and_columns(self, sheet_name, sheet_data, keywords):
        pass
