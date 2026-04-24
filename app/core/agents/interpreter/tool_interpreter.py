from __future__ import annotations

# SECURITY WARNING: This tool uses langchain_experimental PythonREPL, which executes
# LLM-generated Python code directly in the server process with no sandboxing.
# Only deploy in trusted environments where the server host is not exposed to
# untrusted users. Do not use in public-facing deployments without additional
# isolation (e.g. Docker, restricted OS user, network policy).

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.tools import BaseTool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_experimental.utilities import PythonREPL
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.memory.database_manager import tools_database
from app.core.session import create_user_session, setup_logger

logger = setup_logger(__name__)


class InterpreterInput(BaseModel):
    input: str = Field(
        description="Input from Interpreter Agent containing the user's question, necessary file paths and other information."
    )


class Interpreter(BaseTool):

    name: str = "INTERPRETER_TOOL"
    description: str = """
    Interprets the results of a SPARQL query based on user's question.

    Args:
        input: Input from Interpreter Agent containing the user's question, necessary file paths and other information.

    Returns:
        None: Outputs the response after interpreting files.
    """
    args_schema: type[BaseModel] = InterpreterInput
    openai_key: Optional[str] = None
    session_id: Optional[str] = None
    llm_instance: Optional[Any] = None

    def __init__(self, openai_key: Optional[str] = None, session_id: Optional[str] = None, llm_instance: Optional[Any] = None):
        super().__init__()
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")
        self.session_id = session_id
        self.llm_instance = llm_instance

    def _run(
        self,
        input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        logger.info(f"Input: {input}")

        file_paths = self.extract_file_paths(input)
        logger.info(f"File paths: {file_paths}")

        session_dir = create_user_session(self.session_id, user_session_dir=True)
        db_manager = tools_database()

        if not file_paths:
            output_merged = db_manager.get("tool_merge_result")
            if output_merged is not None:
                merged_json = json.loads(output_merged)
                file_paths = merged_json.get("output", {}).get("paths", [])
                logger.info(f"File paths from merge result: {file_paths}")

        if not file_paths:
            sparql_output = db_manager.get("tool_sparql")
            if sparql_output is not None:
                sparql_json = json.loads(sparql_output)
                file_paths = sparql_json.get("output", {}).get("paths", [])
                logger.info(f"File paths from SPARQL tool: {file_paths}")

        llm = self.llm_instance or ChatOpenAI(
            api_key=self.openai_key,
            model="gpt-5.4",
            temperature=0,
        )

        system_prompt = (
            "You are a Python data analysis assistant.\n"
            "Write a self-contained Python script that reads the provided file(s), "
            "fulfils the user's request, and prints a concise text summary to stdout.\n\n"
            "Rules:\n"
            "- pandas, numpy, json, pathlib, and plotly are available.\n"
            "- Use the exact column names shown in the file previews — do not guess them.\n"
            "- Print a SHORT summary (counts, stats, top-N rows) — never print an entire dataframe.\n"
            f"- Save any output files (visualizations, processed data) to: {session_dir}\n"
            "- For visualizations use Plotly and write JSON with: "
            f'fig.write_json(str(Path("{session_dir}") / "<same-stem-as-input>.json"))\n'
            "- Do NOT call plt.show(), fig.show(), or any interactive display.\n"
            "- Do NOT install packages inside the script.\n"
            "- Return ONLY the Python code inside a single ```python ... ``` block."
        )

        file_previews = []
        for fp in file_paths:
            try:
                import pandas as pd
                sep = "\t" if str(fp).endswith((".tsv", ".txt")) else ","
                preview = pd.read_csv(fp, sep=sep, nrows=3)
                # Truncate long cell values so wide/URL-heavy columns don't blow context
                preview = preview.map(
                    lambda v: str(v)[:80] + "…" if isinstance(v, str) and len(str(v)) > 80 else v
                )
                file_previews.append(
                    f"File: {fp}\n"
                    f"Columns: {preview.columns.tolist()}\n"
                    f"Dtypes: {preview.dtypes.to_dict()}\n"
                    f"Preview (3 rows):\n{preview.to_string(index=False)}"
                )
            except Exception:
                file_previews.append(f"File: {fp} (could not preview)")

        preview_block = "\n\n".join(file_previews) if file_previews else "(no files)"
        user_message = f"File previews:\n{preview_block}\n\nRequest: {input}"

        logger.info("Requesting analysis code from LLM")
        response = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        )

        code_blocks = re.findall(r"```python\s*(.*?)\s*```", response.content, re.DOTALL)
        if not code_blocks:
            code_blocks = re.findall(r"```\s*(.*?)\s*```", response.content, re.DOTALL)

        if not code_blocks:
            logger.error("LLM did not return a Python code block")
            return "Interpreter could not generate analysis code for this request."

        code = code_blocks[0]
        logger.info(f"Generated code:\n{code}")

        # Snapshot existing files so we can detect what was newly created
        existing_files = set(session_dir.iterdir()) if session_dir.exists() else set()

        repl = PythonREPL()
        execution_output = repl.run(code)
        # Truncate to keep the agent context manageable (~2000 chars ≈ ~500 tokens)
        _MAX_OUTPUT = 2000
        if len(execution_output) > _MAX_OUTPUT:
            execution_output = execution_output[:_MAX_OUTPUT] + f"\n… [output truncated at {_MAX_OUTPUT} chars]"
        logger.info(f"Execution output: {execution_output}")

        # Collect files written by the executed code
        new_files = (
            set(session_dir.iterdir()) - existing_files if session_dir.exists() else set()
        )
        filepaths = [str(f) for f in new_files]
        logger.info(f"Files generated: {filepaths}")

        output_data = {"output": {"paths": filepaths}}
        try:
            db_manager.put(data=json.dumps(output_data), tool_name="tool_interpreter")
        except Exception as e:
            logger.error(f"Error saving to database: {e}")

        suffix = (
            "\n\nThe full path of the files generated are:\n" + "\n".join(filepaths)
            if filepaths
            else ""
        )
        return f"{execution_output}{suffix}"

    def extract_file_paths(self, text: str):
        regex = r"['\"]?([a-zA-Z0-9_/\\-]+(?:\.csv|\.tsv|\.mgf|\.txt|\.xlsx|\.xls))['\"]?"
        matches = re.finditer(regex, text)
        return [match.group(1).replace("'", "").replace('"', "") for match in matches]
