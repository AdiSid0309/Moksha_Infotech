import os
import dotenv
import requests
from datetime import datetime, timedelta

def fetch_data(auditee_name):
    """Fetch data from FAC API"""
    dotenv.load_dotenv()
    api_key = os.getenv('fac_gov')
    url = f'https://api.fac.gov/general?auditee_name=ilike.{auditee_name}'
    headers = {
        'accept-profile': 'api_v1_1_0',
        'x-api-key': api_key,
        'content-type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error: {response.status_code}')
        return None

def get_two_years_data(data, year1, year2):
    """Get data for two years"""
    print([finding for finding in data if finding['audit_year'] in [year1, year2]])
    return [finding for finding in data if finding['audit_year'] in [year1, year2]]

def get_fiscal_year(data):
    """Get fiscal year end date for two years"""
    return {finding['audit_year']: finding['fy_end_date'] for finding in data}

def due_date(fy_end_date):
    """Calculate due date for submission"""
    fy_end_date = datetime.strptime(fy_end_date, '%Y-%m-%d')
    return (fy_end_date + timedelta(days=9*30.44)).strftime('%Y-%m-%d')

def check_within_due_date(submitted_date, due_date):
    """Check if submitted date is within due date"""
    submitted_date = datetime.strptime(submitted_date, '%Y-%m-%d')
    due_date = datetime.strptime(due_date, '%Y-%m-%d')
    return submitted_date <= due_date

def validate(auditee_name, year1, year2):
    """Validate due date for two years"""
    data = fetch_data(auditee_name)
    if not data:
        return None, None
    
    try:
        two_years_data = get_two_years_data(data, year1, year2)
        fiscal_years = get_fiscal_year(two_years_data)
        due_date1 = due_date(fiscal_years[year1])
        due_date2 = due_date(fiscal_years[year2])
        submitted_dates = {finding['audit_year']: finding['submitted_date'] for finding in two_years_data}
        within_due_date1 = check_within_due_date(submitted_dates[year1], due_date1)
        within_due_date2 = check_within_due_date(submitted_dates[year2], due_date2)
        return within_due_date1, within_due_date2
    except Exception as e:
        print(f'Error: {e}')
        return None, None

def get_answers(auditee_name, year1, year2):
    """Get answers for GAAP, Material Weakness, and Going Concern"""
    data = fetch_data(auditee_name)
    if not data:
        return None, None, None, None, None, None
    
    two_years_data = get_two_years_data(data, year1, year2)
    gaap, material_weakness, going_concern = [], [], []
    
    for finding in two_years_data:
        gaap.append(finding['gaap_results'])
        material_weakness.append(finding['is_internal_control_material_weakness_disclosed'])
        going_concern.append(finding['is_going_concern_included'])
    
    gaap1 = "Yes" if gaap[0] == "unmodified_opinion" else "No"
    gaap2 = "Yes" if gaap[1] == "unmodified_opinion" else "No"
    
    material_weakness1 = "Yes" if material_weakness[0] == "No" else "No"
    material_weakness2 = "Yes" if material_weakness[1] == "No" else "No"
    
    going_concern1 = "Yes" if going_concern[0] == "No" else "No"
    going_concern2 = "Yes" if going_concern[1] == "No" else "No"
    
    return gaap1, gaap2, material_weakness1, material_weakness2, going_concern1, going_concern2

def due_date_process(auditee_name, one_year_ago, two_years_ago):
    """Process due date check"""
    ans1, ans2 = validate(auditee_name, one_year_ago, two_years_ago)
    if ans1 is None or ans2 is None:
        return None, None
    
    return ("Yes" if ans1 else "No"), ("Yes" if ans2 else "No")
