QA = [
    "Single audits were performed on an annual basis in accordance with the provisions of 2 CFR part 200, subpart F, including submitting the data collection form and the reporting package to the FAC by the due date.",
    "The auditor’s opinion on whether the financial statements were prepared in accordance with GAAP, or a basis of accounting required by state law, and the auditor’s in-relation-to opinion on the schedule of expenditures of federal awards were unmodified.",
    "The auditor’s Yellow Book report on internal control did not identify any deficiencies in internal control over financial reporting as material weaknesses.",
    "The auditor did not report a substantial doubt about the entity’s ability to continue as a going concern.",
    "None of the federal programs had audit findings from any of the following in either of the preceding two audit periods in which they were classified as Type A programs: Internal control deficiencies that were identified as material weaknesses in the auditor's report on internal control for major programs.",
    "A modified opinion on a major program in the auditor's report on major programs.",
    "Known or likely questioned costs that exceeded '5%' of the total federal awards expended for a Type A program during the audit period."
]


prompt = """
                You are an expert virtual assistant specializing in analyzing Single Audit (SEFA) reports. 
                Your task is to provide clear, concise, and accurate responses in JSON format.

                **Rules/Instruction:**
                - You will receive context from an audit report along with specific questions.
                - For each question, you must provide 'answer' with 'Yes' or 'No' based on the information in the report.
                - After answering, provide a brief 'reason' for your answer, referencing the audit report.
                - Answer from this section only - Under  "Schedule of Findings and Questioned Costs" the subsection "SECTION - I SUMMARY OF AUDITOR'S RESULTS".
                - If the provided report does not have enough information to answer the question, explicitly state that more information is needed.
                - Ensure to strictly use the provided context from the report to form your response. Do not include any information not found in the context.

                **Context:** {context}

                **User Question:** {input}

                **Important Formatting Rule:**
                - Your response must be a **valid JSON object only**, with the following format:

                {{
                    "answer": "<Your answer here>",
                    "reason": "<Your reason here>"
                }}
                                
                 
                
                """


question_1 = "What is the Type of auditor's report issued on compliance for major programs? We need to get only consider the section 'SECTION I - SUMMARY OF AUDITOR'S RESULTS' and subsection 'federal awards' for the answer. Answer 'Yes' if all major programs received unmodified opinions."

question_2 = "Were any material weaknesses identified under Internal control over major programs under federal awards?"

question_3 = "Did the auditor report any substantial doubt about the entity's ability to continue as a going concern under the section 'SECTION I - SUMMARY OF AUDITOR'S RESULTS'?"


#type A programs question

question_4 = "Were any Internal control deficiencies identified as material weaknesses in the auditor's report on internal control for major programs or internal control over financial reporting?"

question_5 = "Did any federal programs classified as Type A receive a modified opinion in the auditor's report on major programs in the section 'Type of auditor's report issued on compliance for major programs: '? Answer 'Yes' if all major programs received unmodified opinions."

question6 = "Did any known or likely questioned costs exceed '5%' of the total federal awards expended for a Type A program during the audit period?"


prompt_risk = """
                You are an expert virtual assistant specializing in analyzing Single Audit (SEFA) reports.
                Your task is to provide clear, concise, and accurate responses in JSON format.
 
                **Rules/Instruction:**
                - You will receive context from an audit report along with specific questions.
                - For each question, you must provide 'answer' with 'Yes' or 'No' based on the information in the report.
                - After answering, provide a brief 'reason' for your answer, referencing the audit report.
                - Answer from this section only - Under  "FEDERAL AWARD FINDINGS AND QUESTIONED COSTS"
                - If the provided report does not have enough information to answer the question, explicitly state that more information is needed.
                - Ensure to strictly use the provided context from the report to form your response. Do not include any information not found in the context.
 
                **Context:** {context}
 
                **User Question:** {input}
 
                **Important Formatting Rule:**
                - Your response must be a **valid JSON object only**, with the following format:
 
                {{
                    "answer": "<Your answer here>",
                    "reason": "<Your reason here>"
                }}
                               
                 
               
                """