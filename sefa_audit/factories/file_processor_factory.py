from processors.sefa_excel_processor import SEFAExcelProcessor
from processors.tb_excel_processor import TBExcelProcessor
from processors.bb_excel_processor import BBExcelProcessor
from processors.gl_excel_processor import GLExcelProcessor
from processors.sefa_csv_processor import SEFACsvProcessor
from processors.tb_csv_processor import TBCsvProcessor
from processors.bb_csv_processor import BBCsvProcessor
from processors.gl_csv_processor import GLCsvProcessor

class FileProcessorFactory:
    @staticmethod
    def get_processor(file_type, doctype):
        if file_type in ['.xlsx', '.xls']:
            if doctype == 'SEFA':
                return SEFAExcelProcessor()
            if doctype == 'TB':
                return TBExcelProcessor()
            if doctype == 'BB':
                return BBExcelProcessor()
            if doctype == 'GL':
                return GLExcelProcessor()
    
        if file_type in ['.csv']:
            if doctype == 'SEFA':
                return SEFACsvProcessor()
            if doctype == 'TB':
                return TBCsvProcessor()
            if doctype == 'BB':
                return BBCsvProcessor()
            if doctype == 'GL':
                return GLCsvProcessor()
                    
        raise ValueError("Unsupported file type!")
