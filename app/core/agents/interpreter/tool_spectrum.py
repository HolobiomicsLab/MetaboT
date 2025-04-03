from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional, Union
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from app.core.memory.database_manager import tools_database
import pandas as pd
import json
import os
import matplotlib

matplotlib.use("Agg")
from app.core.session import setup_logger, create_user_session
logger = setup_logger(__name__)

# Define the input schema for the SpectrumPlotter tool.
class SpectrumPlotInput(BaseModel):
    input_data: Union[str, Dict[str, Any]] = Field(
        description="Either a dictionary with USI or a file path to a CSV file containing these values."
    )

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
            # If input_data is a string
            if isinstance(input_data, str):
                # Check if it's a CSV file path
                if input_data.endswith(".csv"):
                    df = pd.read_csv(input_data)
                    # Check required columns
                    if not {'usi'}.issubset(df.columns):
                        return {"error": "CSV file must contain 'usi' column."}
                    first_row = df.iloc[0]
                    usi = first_row['usi']
                else:
                    # Attempt to parse the string as JSON
                    try:
                        parsed = json.loads(input_data)
                    except Exception as e:
                        return {"error": f"Invalid input_data format: {e}"}
                    # If the parsed object contains '__arg1'
                    if isinstance(parsed, dict) and '__arg1' in parsed:
                        inner_val = parsed['__arg1']
                        # If the inner value is a string, try to parse it as JSON
                        if isinstance(inner_val, str):
                            try:
                                inner_json = json.loads(inner_val)
                            except Exception as e:
                                return {"error": f"Invalid nested JSON in '__arg1': {e}"}
                        elif isinstance(inner_val, dict):
                            inner_json = inner_val
                        else:
                            return {"error": "Unexpected type for '__arg1' value."}
                        if 'usi' in inner_json:
                            usi = inner_json['usi']
                        else:
                            return {"error": "Missing 'usi' key in nested JSON."}
                    # Otherwise, if the parsed JSON directly has 'usi'
                    elif 'usi' in parsed:
                        usi = parsed['usi']
                    else:
                        return {"error": "Invalid JSON structure. Must contain 'usi'."}
            # If input_data is already a dictionary
            elif isinstance(input_data, dict):
                if 'usi' in input_data:
                    usi = input_data['usi']
                elif '__arg1' in input_data:
                    inner_val = input_data['__arg1']
                    if isinstance(inner_val, str):
                        try:
                            inner_json = json.loads(inner_val)
                        except Exception as e:
                            return {"error": f"Invalid nested JSON in '__arg1': {e}"}
                    elif isinstance(inner_val, dict):
                        inner_json = inner_val
                    else:
                        return {"error": "Unexpected type for '__arg1' value."}
                    if 'usi' in inner_json:
                        usi = inner_json['usi']
                    else:
                        return {"error": "Missing 'usi' key in nested JSON."}
                else:
                    return {"error": "Invalid input. Provide a dictionary with 'usi' or '__arg1'."}
            else:
                return {
                    "error": "Invalid input type. Provide a dictionary with 'usi' or a valid CSV file path."
                }
        if not usi:
            return {"error": "The 'usi' is required."}
        dash_url = f"https://metabolomics-usi.gnps2.org/dashinterface/?usi1={usi}"
        output_data = {"output": {"paths": dash_url}}
        try:
            db_manager.put(data=json.dumps(output_data), tool_name="tool_spectrum")
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
        return {"result": f"Spectrum plot can be seen in {dash_url}"}