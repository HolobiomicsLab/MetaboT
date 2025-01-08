import os
import pandas as pd
from datetime import datetime
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from pathlib import Path
from app.core.utils import setup_logger, create_user_session

logger = setup_logger(__name__)

class FileAnalyzer(BaseTool):
    name: str = "FILE_ANALYZER"
    description: str = """
    Analyzes files in a specified directory and provides a summary of their content.
    """
    # args_schema = BaseModel  # Using BaseModel directly since no specific input fields are necessary
    folder_path: Path = None
    openai_key: str = None
    session_id: str = None

    def __init__(self, session_id: str):
        super().__init__()
        self.session_id = session_id
        self.folder_path = create_user_session(session_id, input_dir=True)

        logger.info(f"Initialized with folder path: {self.folder_path}")

    def _run(self, *args, **kwargs):
        return self.summarize()

    def summarize(self):
        files_summary = []
        if not os.path.exists(self.folder_path):
            logger.error(f"Folder path {self.folder_path} does not exist.")
            return "Folder path does not exist."

        files_list = os.listdir(self.folder_path)
        overview = "List of files: " + ", ".join(files_list) + "\n\n"

        for filename in files_list:
            file_path = os.path.join(self.folder_path, filename)
            if not os.path.isfile(file_path):
                continue

            file_info = self.file_details(file_path, filename)
            files_summary.append(self.format_summary(file_path, filename, file_info))

        summary = overview + "\n".join(files_summary)
        logger.info(summary)  # Logging the summary
        return summary
    
    def file_details(self, file_path, filename):
        file_size = os.path.getsize(file_path)
        file_info = {
            'file_size': file_size,
            'rows': None,
            'columns': None,
            'headers': None,
            'first_line': None,
            'features': None
        }

        if filename.endswith(('.csv', '.tsv', '.xls', '.xlsx')):
            file_info.update(self.analyze_spreadsheet(file_path, filename))
        elif filename.endswith('.mgf'):
            file_info.update(self.analyze_mgf(file_path))
        else:
            file_info.update(self.basic_file_info(file_path))

        return file_info

    def analyze_spreadsheet(self, file_path, filename):
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif filename.endswith('.tsv'):
                df = pd.read_csv(file_path, delimiter='\t')
            else:
                df = pd.read_excel(file_path)
            
            first_line = df.head(1).to_dict(orient='records')[0] if not df.empty else {}
            return {
                'rows': df.shape[0],
                'columns': df.shape[1],
                'headers': list(df.columns),
                'first_line': first_line
            }
        except Exception as e:
            return {'error': str(e)}
        
    def analyze_mgf(self, file_path):
        try:
            with open(file_path, 'r') as file:
                content = file.read()
            features = content.count('FEATURE_ID')
            rows = content.count('\n') + 1

            return {
                'rows': rows,
                'features': features
            }
        except Exception as e:
            return {'error': str(e)}

    def basic_file_info(self, file_path):
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()
            
            return {
                'rows': len(lines)
            }
        except Exception as e:
            return {'error': str(e)}

    def format_summary(self, file_path, filename, info):
        summary = f"Summary of file {filename}:\n"
        summary += f"Path: {file_path}\n"
        summary += f"Size: {info['file_size']} bytes\n"
        if info.get('rows') is not None:
            summary += f"Rows: {info['rows']}\n"
        if info.get('columns') is not None:
            summary += f"Columns: {info['columns']}\n"
        if info.get('headers') is not None:
            summary += f"Headers: {', '.join(info['headers'])}\n"
        if info.get('features') is not None:
            summary += f"Features: {info['features']}\n"
        if info.get('first_line') is not None:
            summary += f"First Line: {info['first_line']}\n"
        if info.get('error') is not None:
            summary += f"Error: {info['error']}\n"
        summary += "\n"

        logger.info(summary)
        return summary