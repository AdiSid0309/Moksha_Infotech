import re

def split_account_string(account_string):
    # Split the string into an array
    split_array = account_string.split('-')

    # Get the first and second elements
    fund_code = split_array[0] if len(split_array) > 0 else None
    gl_code = split_array[1] if len(split_array) > 1 else None
    
    return fund_code, gl_code

def validate_gl_number(gl_number):
    """
    Validates Gl number format (xxxx), where:
    - xxxx: Four or five digits
    """
    pattern = r"\d{4}|\d{5}$"
    return bool(re.match(pattern, gl_number))
    
def validate_fund_number(fund_number):
    """
    Validates fund number format (xxxx), where:
    - xxx: three or Four digits
    """
    
    if not fund_number: return False
    
    pattern = r"\d{3}|\d{4}$"
    return bool(re.match(pattern, fund_number))

def validate_cfda_number(cfda_number):
    pattern = r"^\d{2}\.\d{2,4}|\d{2}\.\d{2,4}/\d{2}\.\d{2,4}$"
    return bool(re.match(pattern, str(cfda_number)))



def find_column(columns, keywords):
    for col in columns:
        normalized_col = str(col).strip().lower().replace("\n", " ")
        if normalized_col == "":
            continue
        for keyword in keywords:
            pattern = rf'\b{re.escape(keyword)}\b'
            if re.search(pattern, normalized_col, re.IGNORECASE):
                return col
    return None
