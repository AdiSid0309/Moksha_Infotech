import pandas as pd
import os
import re
from utils.logger import log_info, log_error
from factories.model_factory import ModelFactory
from factories.file_processor_factory import FileProcessorFactory
from config.settings import OUTPUT_FOLDER
from strategies.Group_Map import Group_and_map
from strategies.cal_bb import CAL_BB
from processors.sefa_drawdown_processor import SefaDrawdownProcessor

class SEFAProcessor:
    def __init__(self):
        self.processor_factory = FileProcessorFactory()

        self.df_sefa = None
        self.df_tb = None
        self.df_gl = None
        self.df_bb = None

    def check_required_files(self, calculation_type):
        """
        Check if required files are uploaded for different calculations
        """
        if calculation_type == "expense":
            if self.df_sefa is None:
                raise ValueError("Please upload the SEFA file first.")
            if self.df_tb is None:
                raise ValueError("Please upload the Trial Balance file first.")
            return True
        elif calculation_type == "beginning_balance":
            if self.df_sefa is None:
                raise ValueError("Please upload the SEFA file first.")
            if self.df_bb is None:
                raise ValueError("Please upload the Prior Year Trial Balance file first.")
            return True
        return False

    def upload_file(self, uploaded_file):
        temp_file_path = ""

        if uploaded_file:
            temp_file_path = os.path.join("data", "input", uploaded_file.name)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        return temp_file_path

    def process_uploaded_file(self, uploaded_file, input_file_path, datatype):
        output_file_path = ""

        processor = self.processor_factory.get_processor(os.path.splitext(uploaded_file.name)[1],datatype)
        processor.process(input_file_path)

        output_file_path = os.path.join(OUTPUT_FOLDER, uploaded_file.name.replace(".xlsx", ".json"))

        return output_file_path

    # Split and normalize fund codes in SEFA
    def normalize_fund_codes(self, fund_code):
        if pd.isna(fund_code):
            return []
        return [
            str(int(float(code))) if code.strip().replace('.', '', 1).isdigit() else code.strip()
            for code in re.split(r'[,/&]', str(fund_code))
        ]

    def process_sefa_file(self, sefa_file):
        headers_json = {}
        sefa_drawdown_process = SefaDrawdownProcessor()

        input_file_path = self.upload_file(sefa_file)
        output_file_path = self.process_uploaded_file(sefa_file, input_file_path, "SEFA")
        if os.path.exists(output_file_path):
            self.df_sefa = pd.read_json(output_file_path, dtype={"FUND_CODE": str})
            self.df_sefa = self.df_sefa[self.df_sefa['CFDA'].notna() & (self.df_sefa['CFDA'] != '')]
            self.df_sefa['Normalized_Fund'] = self.df_sefa['FUND_CODE'].apply(lambda x: self.normalize_fund_codes(x))
            unique_fund_codes = sefa_drawdown_process.filter_sefa(self.df_sefa)
            headers_json['SEFA_Headers'] = self.df_sefa.columns.tolist()
            sefa_df = self.df_sefa.reset_index(drop=True)
            return sefa_df

    def process_tb_file(self, tb_file):
        headers_json = {}
        input_file_path = self.upload_file(tb_file)
        output_file_path = self.process_uploaded_file(tb_file, input_file_path, "TB")
        if os.path.exists(output_file_path):
            self.df_tb = pd.read_json(output_file_path)
            headers_json['TB_Headers'] = self.df_tb.columns.tolist()
            tb_df = self.df_tb.reset_index(drop=True)
            return tb_df

    def process_bb_file(self, bb_file):
        headers_json = {}
        sefa_drawdown_process = SefaDrawdownProcessor()

        input_file_path = self.upload_file(bb_file)
        output_file_path = self.process_uploaded_file(bb_file, input_file_path, "BB")
        if os.path.exists(output_file_path):
            self.df_bb = pd.read_json(output_file_path)
            self.df_bb['FUND_CODE'] = self.df_bb['FUND_CODE'].astype(str).str.lstrip('0')
            bb_filtered = sefa_drawdown_process.filter_bb(self.df_bb)
            headers_json['BB_Headers'] = bb_filtered.columns.tolist()
            bb_df = self.df_bb.reset_index(drop=True)
            return bb_df

    def process_gl_file(self, gl_file):
        headers_json = {}
        input_file_path = self.upload_file(gl_file)
        output_file_path = self.process_uploaded_file(gl_file, input_file_path, "GL")
        if os.path.exists(output_file_path):
            self.df_gl = pd.read_json(output_file_path)
            self.df_gl['FUND_CODE'] = self.df_gl['FUND_CODE'].astype(str).str.lstrip('0')
            headers_json['GL_Headers'] = self.df_gl.columns.tolist()
            return self.df_gl

    def calculate_expense_variance(self,sefa,tb,sefa_path, tb_path):
        if self.check_required_files("expense"):
            grp_map = Group_and_map()
            expense_var = grp_map.cal_variance(self.df_sefa, self.df_tb)
            output_path = os.path.join("data", "tb_expense", os.path.basename(tb_path).replace(".xlsx", ".json"))
            expense_var.to_json(output_path, orient="records", indent=4)
            sefa_major = expense_var[['CFDA', 'EXPENDITURES']]
            output_path = os.path.join("data", "sefa_major", os.path.basename(sefa_path).replace(".xlsx", ".json"))
            sefa_major.to_json(output_path, orient="records", indent=4)
            return expense_var, sefa_major

    def calculate_beginning_balance(self, sefa, bb, sefa_path, bb_path):
        if self.check_required_files("beginning_balance"):
            sefa_drawdown_process = SefaDrawdownProcessor()
            sefa_bb = CAL_BB()
            sefa_bb_df = sefa_bb.get_bb(self.df_sefa, self.df_bb)
            output_path = os.path.join("data", "beginning_balance", os.path.basename(sefa_path).replace(".xlsx", ".json"))
            sefa_bb_df.to_json(output_path, orient="records", indent=4)
            return sefa_bb_df