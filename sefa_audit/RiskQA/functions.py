import PyPDF2
import re
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
import json
from .compliance import compliance_table, create_collection
import pandas as pd
from .constants import question_1, question_2, question_3, question_4, question_5, question6, prompt, prompt_risk

def get_compliance_db(compliance_file):
    """Get the collection for the compliance PDF and the compliance table."""
    collection_pdf = create_collection()  # Create a single collection for the PDF
    table = compliance_table(compliance_file, collection_pdf)  # Pass the file and collection
    table.rename(columns={"Assistance Listing (CFDA)": "ALN"}, inplace=True)
    return table, collection_pdf

def get_high_riskALN(table):
    """Get the high-risk ALN numbers from the compliance table."""
    high_risk_aln = table['ALN'].astype(str).tolist()
    print("High Risk ALN Numbers: ", high_risk_aln)
    return high_risk_aln

def extract_text_from_pdf(file, password=None):
    """Extract text from a PDF file."""
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_section(text):
    """Extract the section between 'Identification of major programs' and 'SECTION II'."""
    pattern = r"Financial Statements:?\nType of audito(.*?)Dollar threshold "
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    section_text = "Type of audito"
    if match:
        section_text += match.group(1)
        print(section_text)
        return section_text
    return ""

def extract_federal_numbers(text):
    """Extract the federal numbers from 'Identification of major programs' to 'Dollar threshold'."""
    pattern = r"Identification of major(.*?)Dollar threshold "
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

    if match:
        federal_text = match.group(1)
        print(federal_text)

        pattern = re.compile(r'\d+\.\d+')
        numbers = pattern.findall(federal_text)

        print(numbers)

        try:
            cleaned_numbers = [str(float(match)) for match in numbers]
            print(cleaned_numbers)
            return cleaned_numbers
        except Exception as e:
            print(f"An error occurred: {e}")
            return numbers

    return []

def extract_findings(text):
    """Extract the findings text from 'SECTION I - SUMMARY OF AUDITOR'S RESULTS' to 'SECTION II'."""
    pattern = r"Dollar threshold\s*(.*)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        findings_text = match.group(1)
        print(findings_text)
        return findings_text
    return ""

def format_response(response):
    """Format the response."""
    try:
        if isinstance(response, dict):
            return json.dumps(response, indent=4)
        if isinstance(response, str):
            return json.loads(response)
    except Exception as e:
        print(f"An error occurred: {e}")
        return response

def create_llm(text, findings_text):
    """Create the LLM model and get responses."""
    llm = HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.3", temperature=0.1)
    chat_model = ChatHuggingFace(llm=llm)

    prompt_template = PromptTemplate(
        template=prompt,
        input_variables=["context", "input"]
    )

    combine_docs_chain = create_stuff_documents_chain(chat_model, prompt_template)

    doc = Document(page_content=text)
    doc2 = Document(page_content=findings_text)

    result = []

    response1 = combine_docs_chain.invoke({
        "context": [doc],
        "input": question_1
    })
    response1 = format_response(response1)
    print("Question 1: ", question_1)
    print(response1)

    if response1["answer"] == "Yes" or response1["answer"] == "Unmodified":
        result.append("Yes")
    else:
        result.append("No")

    response2 = combine_docs_chain.invoke({
        "context": [doc],
        "input": question_2
    })
    response2 = format_response(response2)
    print("Question 2: ", question_2)
    print(response2)
    if response2["answer"] == "No" or response2["answer"] == "None":
        result.append("Yes")
    else:
        result.append("No")

    response3 = combine_docs_chain.invoke({
        "context": [doc],
        "input": question_3
    })
    response3 = format_response(response3)
    print("Question 3: ", question_3)
    print(response3)
    if response3["answer"] == "No" or response3["answer"] == "None":
        result.append("Yes")
    else:
        result.append("No")

    response4 = combine_docs_chain.invoke({
        "context": [doc],
        "input": question_4
    })
    response4 = format_response(response4)
    print("Question 4: ", question_4)
    print(response4)
    if response4["answer"] == "No" or response4["answer"] == "None":
        result.append("Yes")
    else:
        result.append("No")

    response5 = combine_docs_chain.invoke({
        "context": [doc],
        "input": question_5
    })
    response5 = format_response(response5)
    print("Question 5: ", question_5)
    print(response5)
    if response5["answer"] == "Yes" or response5["answer"] == "Unmodified":
        result.append("Yes")
    else:
        result.append("No")

    response6 = combine_docs_chain.invoke({
        "context": [doc2],
        "input": question6
    })
    response6 = format_response(response6)
    print("Question 6: ", question6)
    print(response6)
    if response6["answer"] == "No" or response6["answer"] == "None":
        result.append("Yes")
    else:
        result.append("No")

    return result

def create_llm_high_risk(file, aln_numbers):
    """Create the LLM model for high-risk ALN checks."""
    findings_text = process_sefa(file)
    llm = HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.3", temperature=0.1)
    chat_model = ChatHuggingFace(llm=llm)

    prompt_template = PromptTemplate(
        template=prompt_risk,
        input_variables=["context", "input"]
    )

    combine_docs_chain = create_stuff_documents_chain(chat_model, prompt_template)

    doc = Document(page_content=findings_text)

    result = []

    for aln_number in aln_numbers:
        question1 = f"Are there any 'Material Weakness' identified under the section 'FEDERAL AWARD FINDINGS AND QUESTIONED COSTS' for the ALN number: {aln_number}? Do not consider Significant Deficiencies. Only specify for this ALN number"
        question_2 = f"Are there any 'Modified Opinions' for the ALN number: {aln_number} under the section 'FEDERAL AWARD FINDINGS AND QUESTIONED COSTS'? Only specify for this ALN number"
        question_3 = f"Are there known or likely questioned costs for the ALN number: {aln_number} that exceed '5%' of the total federal awards expended during the audit period? Only specify for this ALN number"

        for question in [question1, question_2, question_3]:
            response = combine_docs_chain.invoke({
                "context": [doc],
                "input": question
            })
            response = format_response(response)
            print("Question : ", question)
            print(response)

            if response["answer"] == "Yes":
                result.append(aln_number)
                break

    return result

def process(file):
    """Process the PDF file."""
    try:
        text = extract_text_from_pdf(file)
        section_text = extract_section(text)
        findings_text = extract_findings(text)

        result = create_llm(section_text, findings_text)
        print(result)
        return result
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def major_programs(file):
    """Process the PDF file for major programs."""
    try:
        text = extract_text_from_pdf(file)
        federal_text = extract_federal_numbers(text)
        return federal_text
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def process_sefa(file):
    """Process the SEFA PDF file."""
    try:
        text = extract_text_from_pdf(file)
        findings_text = extract_findings(text)
        return findings_text
    except Exception as e:
        print(f"An error occurred: {e}")
        return None