from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional, Union
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
import tkinter as tk
from app.core.memory.database_manager import tools_database
import pandas as pd
import json
import os
import matplotlib
import requests
import matplotlib.pyplot as plt
import spectrum_utils.plot as sup
import spectrum_utils.spectrum as sus

matplotlib.use("Agg")
from app.core.session import setup_logger, create_user_session
logger = setup_logger(__name__)

# Define the input schema for the SpectrumPlotter tool.
class SpectrumPlotInput(BaseModel):
    input_data: Union[str, Dict[str, Any]] = Field(
        description="Either a dictionary with USI or a file path to a CSV file containing these values."
    )



# Define the SpectrumPlotter tool.
class SpectrumPlotter(BaseTool):
    name: str = "SPECTRUM_PLOTTER"
    description: str = """
    Provides the url with a plot of a spectrum given its USI.

    Args:
        usi (str): The Universal Spectrum Identifier.
        

    Returns:
       An url with spectrum plot.
    """
    args_schema = SpectrumPlotInput
    session_id: str = None
    openai_key: str = None

    def __init__(self, openai_key: str, session_id: str):
        super().__init__()
        self.openai_key = openai_key
        self.session_id = session_id
    # version 2
    def _run(
            self,
            input_data: Union[str, Dict[str, Any]] = None,
            usi: Optional[str] = None,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        session_dir = create_user_session(self.session_id, user_session_dir=True)
        db_manager = tools_database()
        os.makedirs(session_dir, exist_ok=True)

        # If input_data is provided, it should be used instead of the other parameters
        if input_data:
            if isinstance(input_data, str) and input_data.endswith(".csv"):
                # Read CSV and extract the first row of required columns
                df = pd.read_csv(input_data)

                # Check required columns
                if not {'usi'}.issubset(df.columns):
                    return {"error": "CSV file must contain 'usi' column."}

                first_row = df.iloc[0]
                usi = first_row['usi']

            elif isinstance(input_data, dict) and 'usi' in input_data:
                usi = input_data['usi']
            else:
                return {
                    "error": "Invalid input. Provide a dictionary with 'usi' or a valid CSV file path."}

        if not usi:
            return {"error": "The 'usi' is required."}

        dash_url = f"https://metabolomics-usi.gnps2.org/dashinterface/?usi1={usi}"


        output_data = {"output": {"paths": dash_url}}

        try:
            db_manager.put(data=json.dumps(output_data), tool_name="tool_spectrum")
        except Exception as e:
            logger.error(f"Error saving to database: {e}")

        return {"result": f"Spectrum plot can be seen in   {dash_url}"}

