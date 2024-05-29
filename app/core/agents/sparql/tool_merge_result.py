from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool

from typing import Optional

from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)
import json

from app.core.agents.sparql.base import KgbotBaseTool
from app.core.utils import setup_logger
import tempfile
import os

import pandas as pd
logger = setup_logger(__name__)

class MergerInput(BaseModel):
    file_path_1: str = Field(
        description="A string represents the full path to the output of the SPARQL query from ENPKG endpoint, provided by SPARQL_QUERY_RUNNER tool."
    )
    file_path_2: str = Field(
        description="A string represents the full path to the output of the SPARQL query from Wikidata endpoint provided by WIKIDATA_QUERY_TOOL."
    )

class OutputMerger(KgbotBaseTool):
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
    requires_params = False  # This tool does not require additional initialization parameters

    def __init__(self, **kwargs):
        super().__init__()

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

        # Remove duplicates
        common_ids = common_ids.drop_duplicates()
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.csv', newline='',
                                         dir=os.getcwd()) as temp_file:
            common_ids.to_csv(temp_file.name, index=False)
            return temp_file.name

