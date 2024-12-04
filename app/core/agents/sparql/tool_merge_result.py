from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool

from typing import Optional

from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)

import json

from app.core.session import setup_logger, create_user_session
from app.core.memory.database_manager import tools_database

import tempfile
import os
from pathlib import Path
import pandas as pd

logger = setup_logger(__name__)

class MergerInput(BaseModel):
    file_path_1: str = Field(
        description="A string represents the full path to the output of the SPARQL query from ENPKG endpoint, provided by SPARQL_QUERY_RUNNER tool."
    )
    file_path_2: str = Field(
        description="A string represents the full path to the output of the SPARQL query from Wikidata endpoint provided by WIKIDATA_QUERY_TOOL."
    )

class OutputMerger(BaseTool):
    name: str = "OUTPUT_MERGE"
    description: str = """
    Reads two CSV files containing Wikidata IDs, finds common IDs between them, removes duplicates,
    and saves these common IDs to a new CSV file.

    Args:
       file_path_1 (str): The path to the first CSV file containing Wikidata IDs provided by SPARQL_QUERY_RUNNER tool.
       file_path_2 (str): The path to the second CSV file containing Wikidata IDs provided by WIKIDATA_QUERY_TOOL. 
    Returns:
        output_file_path (str): The path to the temporary CSV file where the output with common Wikidata IDs will be saved.

    """
    args_schema = MergerInput
    session_id: str = None

    def __init__(self, session_id: str):
        super().__init__()
        self.session_id = session_id

    def _run(
            self, file_path_1: str, file_path_2: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        df1 = pd.read_csv(file_path_1)
        df2 = pd.read_csv(file_path_2)

        # Clean data: strip any whitespace from the Wikidata ID strings
        df1.iloc[:, 0] = df1.iloc[:, 0].str.strip()
        df2.iloc[:, 0] = df2.iloc[:, 0].str.strip()

        # Convert data to string in case they are not
        df1.iloc[:, 0] = df1.iloc[:, 0].astype(str)
        df2.iloc[:, 0] = df2.iloc[:, 0].astype(str)

        # Find common IDs
        common_ids = df1[df1.iloc[:, 0].isin(df2.iloc[:, 0])]
        session_dir = create_user_session(self.session_id, user_session_dir=True)
        logger.info(f"Session directory: {session_dir}")

        # Remove duplicates
        common_ids = common_ids.drop_duplicates()
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.csv', newline='', dir=session_dir) as temp_file:
            common_ids.to_csv(temp_file.name, index=False)

            output_data = {
                "output": {
                    "paths": [str(temp_file.name)]
                }
            }

            db_manager = tools_database()
            try:
                db_manager.put(data=json.dumps(output_data), tool_name="tool_merge_result")
            except Exception as e:
                logger.error(f"Error saving to database: {e}")

            return temp_file.name