from imports import *


# Logging configuration
log_dir = "D:/Moksha Infotech/Office/CODE/sefa_audit"
log_file = os.path.join(log_dir, "audit_logs.log")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logger = logging.getLogger("SEFAAudit")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(log_file, mode='a')
fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)
logger.info("Logging initialized. Starting application.")

# API setup
login(token="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")
load_dotenv(find_dotenv())
openai_api_key = os.getenv("OPENAI_API_KEY")
hf_api_key = "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"

# Session state initialization
for key in ['sefa_df', 'tb_df', 'bb_df', 'gl_df', 'report1_file', 'report2_file', 'compliance_file', 'results']:
    if key not in st.session_state:
        st.session_state[key] = None if key != 'results' else {
            "Expense Variation": None,
            "Beginning Balance": None,
            "Cash Receipt": None,
            "Risk Assessment": None,
            "Major Programs": None,
            "sefa_major": None
        }
if 'files_processed' not in st.session_state:
    st.session_state.files_processed = {k: False for k in ["sefa", "tb", "bb", "gl", "report1", "report2", "compliance"]}
if 'data_processed' not in st.session_state:
    st.session_state.data_processed = False
if 'auditee_info' not in st.session_state:
    st.session_state.auditee_info = {"name": "", "year1": "", "year2": ""}


# Model initialization functions
def initialize_openai():
    return ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=openai_api_key)


def initialize_huggingface():
    client = InferenceClient(token=hf_api_key)
    return client


# Utility functions (unchanged for brevity)
def normalize_fund_codes(fund_code):
    if pd.isna(fund_code):
        return []
    return [int(code.strip()) if code.strip().isdigit() else code.strip() for code in re.split(r'[,/]', str(fund_code))]


def remove_leading_zeros(fund_code):
    if pd.isna(fund_code):
        return fund_code
    parts = re.split(r'[,/]', str(fund_code))
    return ','.join(part.strip().lstrip('0') or '0' for part in parts)


def get_openai_response(llm, prompt):
    return llm([HumanMessage(content=prompt)]).content


def get_huggingface_response(chatbot, prompt):
    messages = [{"role": "user", "content": prompt}]
    completion = chatbot.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.3", messages=messages, max_tokens=20992
    )
    return completion.choices[0].message.content


def process_fund(fund, model_type, unique_gl_codes, sefa_df, tb_filtered, gl_df):
    llm = initialize_openai() if model_type == "openai" else initialize_huggingface()
    gl_filtered = gl_df[(gl_df['FUND_CODE'] == fund) & (gl_df['GL_CODE'].isin(unique_gl_codes)) & (gl_df['Debit'] > 0)]
    sefa_data = sefa_df[sefa_df['Normalized_Fund'].apply(lambda x: fund in x)].values.tolist()
    tb_data = tb_filtered.loc[tb_filtered["FUND_CODE"] == fund].values.tolist()
    gl_data = gl_filtered.loc[gl_filtered['FUND_CODE'] == fund].values.tolist()
    gl_data_length = len(gl_filtered)
    headers_json = {'SEFA_Headers': sefa_df.columns.tolist(), 'GL_Headers': gl_df.columns.tolist()}

    i, batch, responses = 0, 20, []
    while i < gl_data_length:
        batch_start, batch_end = i, min(i + batch, gl_data_length)
        logger.info(f"Processing Fund {fund} - Batch {batch_start} to {batch_end - 1}")
        prompt = f"""You are a helpful CPA, working on fund accounting. Given the details of the federal grant program and the general ledger and trial balance entries we want to get the federal grant received for each program in json format with reason and confidence score

*** Instructions ***
1. We only have to consider the General Ledger entries.
2. no conflicting data, confidence is high
3. Strictly take the amounts from the debit column only from the general ledger entry and avoid any other column for the amounts.
4. Narrate the reasoning process or thinking process in detail
5. If there is an JV entry then consider it also if its description states 'To reclass to correct award' or 'To reclass to PFSAs to CTGP'.
6. Don't focus on the word 'reclass' consider the complete phrase 'To reclass to correct award' if it is available.
7. If there is a single entry for JV simply consider it.
8. Do not do any adjustment related calculation to the provided general ledger entries
9. If no general ledger entries are provided for a program do not infer rather indicate as data not provided
10. Take all the cash receipt amount from the debit column from general ledger only.
11. Strictly use only the Document Description and the Transaction Description column to get the description for the cash receipts and not the Session Description
12. In Transaction description if there are any data related to any type of expense like advertisement, it support, staff, etc. ignore the debit amount for these entries
13. From Document description only consider the debit amount that are related to cash or bank transfer.
14. In the reason for the selected entry in the output also add the reference to the general ledger entry as a evidence
15. do not sum the amount for the program but show it as a comma separated list
16. the output entries should match the GL_CODE and fund code values.
17. in case of conflicts only take the reclass adjustment entries.
18. evaluate the entries in the order of date.
19. please refer to document description column also for the information.
20. strictly provide the output in json format only every time.

** Context: Federal Grant Program Details
(Headers: {headers_json['SEFA_Headers']}):{sefa_data}

** Context: General Ledger
(Headers: {headers_json['GL_Headers']}):{gl_data[batch_start:batch_end]}
Provide the output **strictly in JSON format only**, with no additional text, explanations, markdown (e.g., ```json), or code outside the JSON structure. Every response must be a valid JSON array (even if empty) adhering to this structure:
[
    {{
        "Fund_Code": string,
        "GL_Code": string,
        "Award_Code/Contract_Code": string,
        "Account_String": string,
        "Description": string,
        "Amount": integer,
        "Relevant": bool,
        "reason": string,
        "confidence": number
    }}
]
If no relevant entries are found, return an empty array `[]`.
"""
        response = get_openai_response(llm, prompt) if model_type == "openai" else get_huggingface_response(llm, prompt)
        json_str = response.split("```json", 1)[-1].strip() if "```json" in response else response.strip()
        end_index = json_str.find('```') if '```' in json_str else len(json_str)
        responses.append(json_str[:end_index].strip())
        logger.info(f"Raw response: {response}")
        i += batch
    return responses


def convert_to_serializable(data):
    if isinstance(data, np.int64):
        return int(data)
    elif isinstance(data, np.float64):
        return float(data)
    return data


def extract_json_from_response(response):
    json_objects = []
    logger.info(f"Raw response received: {response}")
    cleaned_response = response.strip()
    if "```json" in cleaned_response:
        cleaned_response = cleaned_response.split("```json", 1)[-1].rsplit("```", 1)[0].strip()
    elif "```" in cleaned_response:
        cleaned_response = cleaned_response.split("```", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        json_data = json.loads(cleaned_response)
        json_objects.extend(json_data if isinstance(json_data, list) else [json_data])
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse full response as JSON: {e}")
        json_strs = re.findall(r'\{(?:[^{}]|\{[^{}]*\})*\}', cleaned_response, re.DOTALL)
        for json_str in json_strs:
            try:
                json_objects.append(json.loads(json_str))
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding individual JSON object: {e} - Raw string: {json_str}")
    return json_objects


def assess_risk(auditee_name, year1, year2, uploaded_file1, uploaded_file2, sefa_df):
    if not (uploaded_file1 and uploaded_file2 and sefa_df is not None):
        logger.error("Risk Assessment failed: Missing required files or SEFA data.")
        return {"error": "All files must be provided."}

    risk = "Not determined"
    data = {"Question": [], "Prior Audit Period": [], "Two Audit Period Ago": []}
    result1, result2 = [], []

    try:
        qa1, qa2 = due_date_process(auditee_name, year1, year2)
        result1.append(qa1)
        result2.append(qa2)

        data["Question"].append(QA[0])
        data["Prior Audit Period"].append(qa1)
        data["Two Audit Period Ago"].append(qa2)

        if qa1 is None or qa2 is None:
            logger.error("Risk Assessment: No data found for due date check.")
            return {"error": "No data found for due date check"}

        if qa1 == "No" or qa2 == "No":
            risk = "High"
            logger.info("Risk assessed as High due to due date issues.")
            return {"risk": risk, "data": pd.DataFrame(data)}

        ans1 = process(uploaded_file1)
        ans2 = process(uploaded_file2)
        result1.extend(ans1)
        result2.extend(ans2)

        for i, (res1, res2) in enumerate(zip(result1[1:], result2[1:]), start=1):
            data["Question"].append(QA[i])
            data["Prior Audit Period"].append(res1)
            data["Two Audit Period Ago"].append(res2)
            risk = "High" if res1 == "No" or res2 == "No" else "Low"
            if risk == "High":
                logger.info("Risk assessed as High due to audit report issues.")
                break

        logger.info(f"Risk Assessment completed: Risk level = {risk}")
        return {"risk": risk, "data": pd.DataFrame(data)}
    except Exception as e:
        logger.error(f"Risk Assessment failed: {str(e)}")
        return {"error": f"Error in risk assessment: {str(e)}"}


def type_a_b(sefa_df, uploaded_file1, uploaded_file2, compliance_file, risk, results):
    try:
        df, total_federal_exp = process_df(sefa_df)
        aln_list = df['CFDA'].tolist()

        amount = amount_to_be_tested(risk, total_federal_exp)

        # Use the uploaded compliance_file to get compliance data
        tb1, collection_pdf1 = get_compliance_db(compliance_file)  # Pass the compliance PDF
        high_risk_aln = get_high_riskALN(tb1)  # Extract high-risk ALNs from the compliance table

        threshold = threshold_for_type(total_federal_exp)
        df['Type A or B'] = df.apply(lambda row: identify_typeA_typeB(row['EXPENDITURES'], threshold), axis=1)

        typeA = typeA_list(df)
        typeB = typeB_list(df)

        newB = typeB.copy()
        newB.rename(columns={'CFDA': 'ALN', 'EXPENDITURES': 'Expenditures'}, inplace=True)
        newB.drop(columns=['Type A or B'], inplace=True)
        newB.to_csv('typeB.csv', index=False)

        typeA_list_program = typeA['CFDA'].astype(str).tolist()
        sefa_major = results.get("sefa_major", pd.DataFrame())
        sefa_major_programs = sefa_major['CFDA'].astype(str).tolist() if 'CFDA' in sefa_major.columns else []
        audited_programs1 = major_programs(uploaded_file1)
        audited_programs2 = major_programs(uploaded_file2)

        low_risk_typeA = []
        high_risk_A_from_report = create_llm_high_risk(uploaded_file1, typeA_list_program)

        for program in typeA_list_program:
            programs_to_check = program.split("/") if "/" in program else [program]
            if (any(p in audited_programs1 or p in audited_programs2 for p in programs_to_check) and
                    program not in high_risk_aln and
                    program not in high_risk_A_from_report and
                    program in sefa_major_programs):
                low_risk_typeA.append(program)

        low_risk_typeA_df = typeA[typeA['CFDA'].astype(str).isin(low_risk_typeA)]
        low_risk_typeA_df.rename(columns={'CFDA': 'ALN', 'EXPENDITURES': 'Expenditures'}, inplace=True)
        low_risk_typeA_df.drop(columns=['Type A or B'], inplace=True)
        low_risk_typeA_df.to_csv('low_risk_typeA.csv', index=False)

        # Pass compliance_file data to func
        high_risk_typeB_df = func(threshold, tb1, collection_pdf1, 'low_risk_typeA.csv', 'typeB.csv')
        high_risk_typeB = [] if high_risk_typeB_df is None else high_risk_typeB_df['program_name'].tolist()

        final_df = df.copy()
        final_df['Risk'] = final_df.apply(
            lambda row: 'Low Risk Type A' if (row['Type A or B'] == 'A' and str(row['CFDA']) in low_risk_typeA) else
                        'High Risk Type A' if (row['Type A or B'] == 'A') else
                        'High Risk Type B' if (row['Type A or B'] == 'B' and row['CFDA'] in high_risk_typeB) else '',
            axis=1
        )

        tested_df = final_df.copy()
        risk_priority = {"High Risk Type A": 1, "High Risk Type B": 2}
        tested_df["Priority"] = tested_df["Risk"].map(risk_priority)
        tested_df = tested_df.sort_values(by=["Priority", "EXPENDITURES"], ascending=[True, False]).drop(columns=["Priority"])

        selected_rows = []
        current_sum = 0
        for _, row in tested_df.iterrows():
            if current_sum >= amount and (row["Risk"] != "High Risk Type A" and row["Risk"] != "High Risk Type B"):
                break
            current_sum += row["EXPENDITURES"]
            selected_rows.append(row)

        selected_df = pd.DataFrame(selected_rows)

        # Rename CFDA to ALN in the selected_df
        selected_df = selected_df.rename(columns={'CFDA': 'ALN'})

        # Create summary rows for total and minimum amounts
        total_expenditures = selected_df['EXPENDITURES'].sum()  # Total federal expenditures being tested
        minimum_amount = amount  # Use the amount variable as the minimum amount

        summary_row1 = pd.DataFrame({
            'ALN': ['Total federal expenditures being tested'],
            'EXPENDITURES': [total_expenditures],
            'Type A or B': ['']
        })

        summary_row2 = pd.DataFrame({
            'ALN': ['Minimum amount of federal expenditures that need to be tested'],
            'EXPENDITURES': [minimum_amount],
            'Type A or B': ['']
        })

        # Create an empty row
        empty_row = pd.DataFrame({
            'ALN': [''],
            'EXPENDITURES': [''],
            'Type A or B': ['']
        })

        # Concatenate the selected_df, empty row, and summary rows
        programs_to_be_tested_df = pd.concat([selected_df, empty_row, summary_row1, summary_row2], ignore_index=True)

        df.to_excel('output.xlsx', index=False)

        return {
            "total_federal_expenditures": total_federal_exp,
            "amount_to_be_tested": amount,
            "high_risk_aln_from_compliance_reports": high_risk_aln,
            "low_risk_typeA_df": low_risk_typeA_df,
            "high_risk_typeB_df": high_risk_typeB_df,
            "final_risk_assessment_df": final_df,
            "programs_to_be_tested_df": programs_to_be_tested_df,
            "total_expenditures_being_tested": current_sum,
            "sefa_major_df": sefa_major
        }
    except Exception as e:
        logger.error(f"Error in type_a_b: {str(e)}")
        return {"error": f"Error processing the SEFA DataFrame: {str(e)}"}


def process_all_data(sefa_processor, model_type):
    results = st.session_state.results
    required_dfs = [st.session_state.sefa_df, st.session_state.tb_df, st.session_state.bb_df, st.session_state.gl_df,
                    st.session_state.report1_file, st.session_state.report2_file, st.session_state.compliance_file]
    if not all(df is not None for df in required_dfs):
        st.error("Please upload all required files (SEFA, Trial Balance, Prior Year Trial Balance, General Ledger, Audit Reports, and Compliance PDF) and provide auditee information.")
        logger.error("Processing halted: Missing required files.")
        return results

    sefa_df, tb_df, bb_df, gl_df = (st.session_state[k] for k in ['sefa_df', 'tb_df', 'bb_df', 'gl_df'])
    report1_file, report2_file, compliance_file = st.session_state.report1_file, st.session_state.report2_file, st.session_state.compliance_file
    auditee_name, year1, year2 = (st.session_state.auditee_info[k] for k in ["name", "year1", "year2"])

    # Expense Variation
    if sefa_df is not None and tb_df is not None:
        sefa_processor.df_sefa, sefa_processor.df_tb = sefa_df, tb_df
        sefa_path = st.session_state.get("sefa_file_name", "sefa_default.xlsx")
        tb_path = st.session_state.get("tb_file_name", "tb_default.xlsx")
        try:
            expense_var, sefa_major = sefa_processor.calculate_expense_variance(sefa=None, tb=None, sefa_path=sefa_path, tb_path=tb_path)
            results["Expense Variation"] = {"expense_var": expense_var}
            results["sefa_major"] = sefa_major
            logger.info("Expense Variation processed successfully.")
        except Exception as e:
            st.error(f"Error in Expense Variation: {str(e)}")
            logger.error(f"Error in Expense Variation: {str(e)}")

    # Beginning Balance
    if sefa_df is not None and bb_df is not None:
        sefa_processor.df_sefa, sefa_processor.df_bb = sefa_df, bb_df
        sefa_path = st.session_state.get("sefa_file_name", "sefa_default.xlsx")
        bb_path = st.session_state.get("bb_file_name", "bb_default.xlsx")
        try:
            results["Beginning Balance"] = sefa_processor.calculate_beginning_balance(sefa=None, bb=None, sefa_path=sefa_path, bb_path=bb_path)
            logger.info("Beginning Balance processed successfully.")
        except Exception as e:
            st.error(f"Error in Beginning Balance: {str(e)}")
            logger.error(f"Error in Beginning Balance: {str(e)}")

    # Cash Receipt
    if sefa_df is not None and tb_df is not None and gl_df is not None:
        sefa_df_copy = sefa_df.copy()
        sefa_df_copy['FUND_CODE'] = sefa_df_copy['FUND_CODE'].apply(remove_leading_zeros)
        sefa_df_copy['Normalized_Fund'] = sefa_df_copy['FUND_CODE'].apply(normalize_fund_codes)
        sefa_df_copy = sefa_df_copy[['Normalized_Fund', 'CFDA']]

        tb_df['FUND_CODE'] = tb_df['FUND_CODE'].apply(remove_leading_zeros).astype('float', errors='ignore')
        gl_df['FUND_CODE'] = gl_df['FUND_CODE'].apply(remove_leading_zeros).astype('float', errors='ignore')

        unique_fund_codes = set(code for codes_list in sefa_df_copy['Normalized_Fund'] for code in codes_list)
        tb_filtered = tb_df[tb_df['FUND_CODE'].isin(unique_fund_codes)]
        tb_filtered = tb_filtered[tb_filtered['MAP DESCRIPTION'].str.contains('cash and cash equivalent', case=False, na=False)]
        unique_gl_codes = tb_filtered['GL_CODE'].unique()
        tb_unique_fund = tb_filtered['FUND_CODE'].unique()
        gl_df = gl_df.drop(['Credit', 'Net Amount'], axis=1, errors='ignore')

        all_responses = {}
        total_funds = len(tb_unique_fund)
        st.write(f"Total number of funds: {total_funds}")
        st.write(f"List of unique fund codes: {tb_unique_fund}")
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, fund in enumerate(tb_unique_fund):
            if fund == 200:
                break
            status_text.text(f"Processing Fund {(idx + 1)} / {total_funds}...")
            all_responses[fund] = process_fund(fund, model_type, unique_gl_codes, sefa_df_copy, tb_filtered, gl_df)
            progress_bar.progress((idx + 1) / total_funds)
            status_text.text("")

        results["Cash Receipt"] = all_responses
        logger.info("Cash Receipt processed successfully.")

    # Risk Assessment (after Cash Receipt)
    if auditee_name and year1 and year2 and sefa_df is not None and report1_file and report2_file:
        try:
            risk_assessment = assess_risk(auditee_name, year1, year2, report1_file, report2_file, sefa_df)
            results["Risk Assessment"] = risk_assessment
            risk = risk_assessment.get("risk", "Low")
            logger.info("Risk Assessment processed successfully.")
        except Exception as e:
            st.error(f"Error in Risk Assessment: {str(e)}")
            logger.error(f"Error in Risk Assessment: {str(e)}")
            risk = "Low"  # Default risk if assessment fails
    else:
        st.warning("Auditee information or required files missing. Proceeding with default risk 'Low' for Major Programs.")
        logger.warning("Risk Assessment skipped: Missing auditee info or files.")
        results["Risk Assessment"] = {"error": "Missing auditee information or required files."}
        risk = "Low"

    # Major Programs (after Risk Assessment)
    if sefa_df is not None and report1_file and report2_file and compliance_file:
        try:
            results["Major Programs"] = type_a_b(sefa_df, report1_file, report2_file, compliance_file, risk, results)
            logger.info("Major Programs processed successfully.")
        except Exception as e:
            st.error(f"Error in Major Programs: {str(e)}")
            logger.error(f"Error in Major Programs: {str(e)}")

    st.session_state.results = results
    return results


def main():
    with st.sidebar:
        selected = option_menu(
            menu_title="SEFA AUDIT PROCESS",
            options=["Step1: Upload", "Step2: Expense Variance", "Step3: Beginning Balance", "Step4: Cash Receipt", "Step5: Risk Assessment", "Step6: Major Programs"],
            icons=['upload', 'calculator', 'calculator', 'receipt', 'shield-check', 'list-check'],
            menu_icon='cast',
            default_index=0,
            orientation='vertical',
            styles={
                "container": {"padding": "0!important"},
                "menu-title": {"font-size": "20px", "text-align": "center"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {"font-size": "15px", "text-align": "left", "margin": "0px", "--hover-color": "#2f9e77"},
                "nav-link-selected": {"background-color": "#02ab21"}
            }
        )

    sefa_processor = SEFAProcessor()

    if selected == "Step1: Upload":
        st.title("Upload Files and Auditee Information")

        st.subheader("Auditee Information")
        auditee_name = st.text_input("Auditee Name", value=st.session_state.auditee_info["name"])
        year1 = st.text_input("Prior Audit Year (e.g., 2023)", value=st.session_state.auditee_info["year1"])
        year2 = st.text_input("Two Periods Ago Audit Year (e.g., 2022)", value=st.session_state.auditee_info["year2"])
        st.session_state.auditee_info.update({"name": auditee_name, "year1": year1, "year2": year2})

        sefa_file = st.file_uploader("Upload SEFA File", type=["xlsx", "csv"])
        if sefa_file and not st.session_state.files_processed["sefa"]:
            st.session_state.sefa_df = sefa_processor.process_sefa_file(sefa_file)
            st.session_state.sefa_file_name = sefa_file.name
            st.session_state.files_processed["sefa"] = True
            st.success("SEFA file uploaded successfully!")
            logger.info("SEFA file uploaded successfully.")

        tb_file = st.file_uploader("Upload Trial Balance File", type=["xlsx", "csv"])
        if tb_file and not st.session_state.files_processed["tb"]:
            st.session_state.tb_df = sefa_processor.process_tb_file(tb_file)
            st.session_state.tb_file_name = tb_file.name
            st.session_state.files_processed["tb"] = True
            st.success("Trial Balance file uploaded successfully!")
            logger.info("Trial Balance file uploaded successfully.")

        bb_file = st.file_uploader("Upload PY TB File", type=["xlsx", "csv"])
        if bb_file and not st.session_state.files_processed["bb"]:
            st.session_state.bb_df = sefa_processor.process_bb_file(bb_file)
            st.session_state.bb_file_name = bb_file.name
            st.session_state.files_processed["bb"] = True
            st.success("Prior Year Trial Balance file uploaded successfully!")
            logger.info("Prior Year Trial Balance file uploaded successfully.")

        gl_file = st.file_uploader("Upload General Ledger File", type=["xlsx", "csv"])
        if gl_file and not st.session_state.files_processed["gl"]:
            st.session_state.gl_df = sefa_processor.process_gl_file(gl_file)
            st.session_state.gl_file_name = gl_file.name
            st.session_state.files_processed["gl"] = True
            st.success("General Ledger file uploaded successfully!")
            logger.info("General Ledger file uploaded successfully.")

        report1_file = st.file_uploader("Upload Prior Audit Report (PDF)", type=["pdf"])
        if report1_file and not st.session_state.files_processed["report1"]:
            st.session_state.report1_file = report1_file.name
            with open(st.session_state.report1_file, "wb") as f:
                f.write(report1_file.getbuffer())
            st.session_state.files_processed["report1"] = True
            st.success("Prior Audit Report uploaded successfully!")
            logger.info("Prior Audit Report uploaded successfully.")

        report2_file = st.file_uploader("Upload Two Periods Ago Audit Report (PDF)", type=["pdf"])
        if report2_file and not st.session_state.files_processed["report2"]:
            st.session_state.report2_file = report2_file.name
            with open(st.session_state.report2_file, "wb") as f:
                f.write(report2_file.getbuffer())
            st.session_state.files_processed["report2"] = True
            st.success("Two Periods Ago Audit Report uploaded successfully!")
            logger.info("Two Periods Ago Audit Report uploaded successfully.")

        compliance_file = st.file_uploader("Upload Compliance Supplement (PDF)", type=["pdf"])
        if compliance_file and not st.session_state.files_processed["compliance"]:
            st.session_state.compliance_file = compliance_file.name
            with open(st.session_state.compliance_file, "wb") as f:
                f.write(compliance_file.getbuffer())
            st.session_state.files_processed["compliance"] = True
            st.success("Compliance Supplement uploaded successfully!")
            logger.info("Compliance Supplement uploaded successfully.")
        elif st.session_state.files_processed["compliance"]:
            st.info("Compliance Supplement already uploaded.")
        model_type = st.selectbox("Select AI Model", ("huggingface",), index=0, help="Choose between OpenAI GPT-4 or HuggingFace models")

        if st.button("Process All Data"):
            if not all(st.session_state.files_processed.values()) or not all(st.session_state.auditee_info.values()):
                st.error("Please upload all required files and fill in auditee information before processing.")
            elif not st.session_state.data_processed:
                process_all_data(sefa_processor, model_type)
                st.session_state.data_processed = True
                st.success("All data processed successfully! Check the respective tabs for results.")
                logger.info("All data processed successfully.")
            else:
                st.info("Data has already been processed.")

    elif selected == "Step2: Expense Variance":
        st.title("Expense Variance Calculation")
        results = st.session_state.results
        if results["Expense Variation"]:
            st.subheader("Expense Variance Results")
            st.dataframe(results["Expense Variation"]["expense_var"])
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                results["Expense Variation"]["expense_var"].to_excel(writer, sheet_name='Expense_Variance', index=False)
                results["sefa_major"].to_excel(writer, sheet_name='SEFA_Major', index=False)
            excel_data = output.getvalue()
            st.download_button(
                label="Download Expense Variance Excel",
                data=excel_data,
                file_name="expense_variance_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("Please process the data from the Upload tab first.")

    elif selected == "Step3: Beginning Balance":
        st.title("Beginning Balance")
        results = st.session_state.results
        if results["Beginning Balance"] is not None:
            st.subheader("Beginning Balance Results")
            st.dataframe(results["Beginning Balance"])
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                results["Beginning Balance"].to_excel(writer, sheet_name='Beginning_Balance', index=False)
            excel_data = output.getvalue()
            st.download_button(
                label="Download Beginning Balance Excel",
                data=excel_data,
                file_name="beginning_balance_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("Please process the data from the Upload tab first.")

    elif selected == "Step4: Cash Receipt":
        st.title("Federal Grant Cash Receipt Analyzer")
        results = st.session_state.results
        if results["Cash Receipt"]:
            with st.expander("Analysis:"):
                serializable_data = {str(k): convert_to_serializable(v) for k, v in results["Cash Receipt"].items()}
                st.json(json.dumps(serializable_data))
            data_list = []
            for fund, responses in results["Cash Receipt"].items():
                for response in responses:
                    json_objects = extract_json_from_response(response)
                    relevant_objects = [obj for obj in json_objects if obj.get("Relevant", False)]
                    data_list.extend(relevant_objects)
            if data_list:
                df = pd.DataFrame(data_list)
                st.dataframe(df)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Cash_Receipt', index=False)
                excel_data = output.getvalue()
                st.download_button(
                    label="Download Excel",
                    data=excel_data,
                    file_name="cash_receipt_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("No relevant cash receipt entries found.")
        else:
            st.info("Please process the data from the Upload tab first.")

    elif selected == "Step5: Risk Assessment":
        st.title("Risk Assessment")
        results = st.session_state.results
        if results.get("Risk Assessment") is not None:
            if "error" in results["Risk Assessment"]:
                st.error(results["Risk Assessment"]["error"])
            else:
                st.subheader("Risk Level")
                st.write(results["Risk Assessment"]["risk"])
                st.subheader("Assessment Details")
                st.dataframe(results["Risk Assessment"]["data"])
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    results["Risk Assessment"]["data"].to_excel(writer, sheet_name='Risk_Assessment', index=False)
                excel_data = output.getvalue()
                st.download_button(
                    label="Download Risk Assessment Excel",
                    data=excel_data,
                    file_name="risk_assessment.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("Please process the data from the Upload tab first to perform the risk assessment.")

    elif selected == "Step6: Major Programs":
        st.title("Major Programs Analysis")
        results = st.session_state.results
        if results["Major Programs"]:
            if "error" in results["Major Programs"]:
                st.error(results["Major Programs"]["error"])
            else:
                st.subheader("Total Federal Expenditures")
                st.write(str(round(results["Major Programs"]["total_federal_expenditures"], 2)))
                st.subheader("Amount to be Tested")
                st.write(str(round(results["Major Programs"]["amount_to_be_tested"], 2)))
                with st.expander("High Risk ALNs from Compliance Reports:"):
                    st.write(results["Major Programs"]["high_risk_aln_from_compliance_reports"])
                st.subheader("SEFA Major Programs (Input)")
                st.dataframe(results["sefa_major"])
                st.subheader("Low Risk Type A Programs")
                st.dataframe(results["Major Programs"]["low_risk_typeA_df"])
                st.subheader("High Risk Type B Programs")
                if results["Major Programs"]["high_risk_typeB_df"] is not None:
                    st.dataframe(results["Major Programs"]["high_risk_typeB_df"])
                else:
                    st.write("No high risk Type B programs identified.")
                st.subheader("Final Risk Assessment")
                st.dataframe(results["Major Programs"]["final_risk_assessment_df"])
                st.subheader("Programs to be Tested")
                st.dataframe(results["Major Programs"]["programs_to_be_tested_df"])
                st.subheader(f"Total Expenditures Being Tested = {str(round(results['Major Programs']['total_expenditures_being_tested'], 2))}")
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    results["sefa_major"].to_excel(writer, sheet_name='SEFA_Major', index=False)
                    results["Major Programs"]["low_risk_typeA_df"].to_excel(writer, sheet_name='Low_Risk_TypeA', index=False)
                    if results["Major Programs"]["high_risk_typeB_df"] is not None:
                        results["Major Programs"]["high_risk_typeB_df"].to_excel(writer, sheet_name='High_Risk_TypeB', index=False)
                    results["Major Programs"]["final_risk_assessment_df"].to_excel(writer, sheet_name='Final_Risk_Assessment', index=False)
                    results["Major Programs"]["programs_to_be_tested_df"].to_excel(writer, sheet_name='Programs_to_be_Tested', index=False)
                excel_data = output.getvalue()
                st.download_button(
                    label="Download Major Programs Excel",
                    data=excel_data,
                    file_name="major_programs_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("Please process the data from the Upload tab first.")


if __name__ == "__main__":
    main()