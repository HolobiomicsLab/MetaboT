from __future__ import annotations


from codeinterpreterapi import CodeInterpreterSession, File, settings

from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool

from typing import Optional

from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)
import json
from ...session import setup_logger, create_user_session

import os
import re
import tempfile
from pathlib import Path
from ...memory.database_manager import tools_database

logger = setup_logger(__name__)


class InterpreterInput(BaseModel):
    input: str = Field(description="Input from Interpreter Agent containing the user's question, necessary file paths and other information.")

class Interpreter(BaseTool):

    name: str = "INTERPRETER_TOOL"
    description: str = """
    Interprets the results of a SPARQL query based on user's question.

    Args:
        input: Input from Interpreter Agent containing the user's question, necessary file paths and other information.

    Returns:
        None: Outputs the response after interpreting files.
    """
    args_schema = InterpreterInput
    openai_key: str = None
    session_id: str = None

    def __init__(self, openai_key: str, session_id: str):
        super().__init__()
        self.openai_key = openai_key
        self.session_id = session_id

    def _run(
        self,
        input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> None:

        logger.info(f"Input: {input}")

        file_paths = self.extract_file_paths(input)
        logger.info(f"File paths: {file_paths}")

        session_dir = create_user_session(self.session_id, user_session_dir=True)

        logger.info(f"session_dir: {session_dir}")

        # if os.getenv("CODEBOX_API_KEY"):
        #     codebox_key = os.getenv("CODEBOX_API_KEY")
        #     settings.CODEBOX_API_KEY = codebox_key

        settings.OPENAI_API_KEY = self.openai_key
        settings.MODEL = "gpt-3.5-turbo"

        with CodeInterpreterSession() as session:

            db_manager = tools_database()

            user_request = (
                "You are an interpreter helping to analyze different questions, files and outputs generated from a series of LLMs."
                f"The details of the current request: {input}"
                "Please interpret the current request to generate a meaningful answer."
                "Here's some instructions that you have to follow for acheiving the task:"
                "1. For any file provided, analyse if and provide clear and brief information about it unless something else is asked."
                "2. Only if a specific visualization (e.g., bar chart, diagram) is requested in the question, use the provided information to generate a .json file containing the JSON code for a Plotly graph. This file should be named identically to the analyzed file."
                "3. After you finish your tasks, your answer should contain both the interpretation asked and the full visualization file name if visualization was requested."
            )

            files = []

            for file in file_paths:
                files.append(File.from_path(file))
                logger.info(f"File added to interpreter Agent: {file}")

            if not files:
                
                logger.info("No files provided from the Interpreter Agent. Manually scrapping the database")
                output_merged = db_manager.get("tool_merge_result")  # Get all file paths from the database associated with the tool_interpreter
                if output_merged is not None:
                    output_merged_json = json.loads(output_merged)
                    merged_filepaths = output_merged_json['output']['paths']

                    for merged_filepath in merged_filepaths:
                        logger.info(f"File added to interpreter Agent from the Output Merged tool: {merged_filepath}")
                        files.append(File.from_path(merged_filepath))

            if not files:

                sparql_output = db_manager.get("tool_sparql")  # Get all file paths from the database associated with the tool_interpreter
                if sparql_output is not None:
                    sparql_output_json = json.loads(sparql_output)
                    sparql_filepaths = sparql_output_json['output']['paths']

                    for sparql_filepath in sparql_filepaths:
                        logger.info(f"File added to interpreter Agent from the SPARQL tool: {sparql_filepath}")
                        files.append(File.from_path(sparql_filepath))
                
            # generate the response
            logger.info(f"Files submitted: {files}")
            response = session.generate_response(user_request, files=files)
            logger.info(f"Interpreter Agent Response: {response}")

            filepaths = []

            # Handling and saving output files
            if response.files:
                for file in response.files:
                    logger.info(f"File: {file.name}")

                    generated_file_path = session_dir / file.name
                    with open(generated_file_path, 'wb') as f:
                        f.write(file.content)
                    filepaths.append(str(generated_file_path))

                    logger.info(f"File saved: {file.name}")
            else:
                logger.info("No files generated by Interpreter Tool.")

            output_data = {
                "output": {
                    "paths": filepaths
                }
            }

            
            try:
                db_manager.put(data=json.dumps(output_data), tool_name="tool_interpreter")
            except Exception as e:
                logger.error(f"Error saving to database: {e}")

            return f"{response}.\n\n The full path of the files generated are:\n" + "\n".join(filepaths)

    def extract_file_paths(self, text: str):
        # Regex to find file paths or filenames with extensions, possibly surrounded by quotes
        regex = r"['\"]?([a-zA-Z0-9_/\\-]+(?:\.csv|\.tsv|\.mgf|\.txt|\.xlsx|\.xls))['\"]?"
        matches = re.finditer(regex, text)
        file_paths = [match.group(1).replace("'", "").replace('"', '') for match in matches]
        return file_paths