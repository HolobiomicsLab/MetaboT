from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.tools import BaseTool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.memory.database_manager import tools_database
from app.core.security import (
    get_interpreter_cpu_seconds,
    get_interpreter_max_file_bytes,
    get_interpreter_memory_bytes,
    get_interpreter_timeout_seconds,
    is_trusted_mode_enabled,
    resolve_session_path,
)
from app.core.session import create_user_session, setup_logger

logger = setup_logger(__name__)

_ALLOWED_INPUT_SUFFIXES = {".csv", ".tsv", ".mgf", ".txt", ".xlsx", ".xls", ".json"}
_ALLOWED_INPUT_SUFFIXES_PATTERN = "|".join(
    sorted(suffix.removeprefix(".") for suffix in _ALLOWED_INPUT_SUFFIXES)
)
_QUOTED_FILE_PATH_PATTERN = re.compile(
    rf"""(?P<quote>["'])(?P<path>[^"']+\.(?:{_ALLOWED_INPUT_SUFFIXES_PATTERN}))(?P=quote)""",
    re.IGNORECASE,
)
_UNQUOTED_FILE_PATH_PATTERN = re.compile(
    rf"""(?P<path>[A-Za-z0-9_./\\-]+\.(?:{_ALLOWED_INPUT_SUFFIXES_PATTERN}))""",
    re.IGNORECASE,
)
_MAX_OUTPUT_CHARS = 2000


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

    def __init__(
        self,
        openai_key: Optional[str] = None,
        session_id: Optional[str] = None,
        llm_instance: Optional[Any] = None,
    ):
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

        if not is_trusted_mode_enabled():
            logger.warning("Rejected interpreter execution because trusted mode is disabled.")
            return (
                "Interpreter execution is disabled in this deployment. "
                "Set METABOT_TRUSTED_MODE=true only in a trusted environment with host-level isolation."
            )

        session_dir = create_user_session(self.session_id, user_session_dir=True)
        session_dir.mkdir(parents=True, exist_ok=True)
        db_manager = tools_database()

        file_paths = self.collect_allowed_file_paths(
            input_text=input,
            session_dir=session_dir,
            db_manager=db_manager,
        )
        logger.info(f"Validated file paths: {file_paths}")

        if not file_paths:
            return (
                "Interpreter could not find any readable session files. "
                "Only files created or uploaded in the current session are allowed."
            )

        llm = self.llm_instance or ChatOpenAI(
            api_key=self.openai_key,
            model="gpt-5.4",
            temperature=0,
        )

        system_prompt = self.build_system_prompt(session_dir=session_dir, file_paths=file_paths)
        preview_block = self.build_preview_block(file_paths)
        user_message = f"File previews:\n{preview_block}\n\nRequest: {input}"

        logger.info("Requesting analysis code from LLM")
        response = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        )

        code = self.extract_python_code(response.content)
        if code is None:
            logger.error("LLM did not return a Python code block")
            return "Interpreter could not generate analysis code for this request."

        logger.info(f"Generated code:\n{code}")

        existing_files = self.capture_session_file_metadata(session_dir)
        execution_result = self.execute_in_subprocess(
            code=code,
            session_dir=session_dir,
            allowed_input_paths=file_paths,
        )
        execution_output = execution_result.get("stdout", "").strip()
        error_output = execution_result.get("error", "").strip()

        if error_output:
            logger.warning(f"Interpreter subprocess reported an error: {error_output}")

        combined_output = execution_output or error_output or "Interpreter execution completed."
        combined_output = self.truncate_output(combined_output)
        logger.info(f"Execution output: {combined_output}")

        current_files = self.capture_session_file_metadata(session_dir)
        changed_or_new_files = sorted(
            str(path)
            for path in self.find_changed_or_new_files(existing_files, current_files)
        )
        logger.info(f"Files generated or updated: {changed_or_new_files}")

        output_data = {"output": {"paths": changed_or_new_files}}
        try:
            db_manager.put(data=json.dumps(output_data), tool_name="tool_interpreter")
        except Exception as e:
            logger.error(f"Error saving to database: {e}")

        suffix = (
            "\n\nThe full path of the files generated or updated are:\n" + "\n".join(changed_or_new_files)
            if changed_or_new_files
            else ""
        )
        return f"{combined_output}{suffix}"

    def collect_allowed_file_paths(self, input_text: str, session_dir: Path, db_manager) -> list[Path]:
        candidate_paths = self.extract_file_paths(input_text)

        if not candidate_paths:
            candidate_paths = self.extract_paths_from_db(db_manager, "tool_merge_result")

        if not candidate_paths:
            candidate_paths = self.extract_paths_from_db(db_manager, "tool_sparql")

        validated_paths: list[Path] = []
        rejected_paths: list[str] = []

        for raw_path in candidate_paths:
            try:
                validated_path = resolve_session_path(raw_path, session_dir=session_dir, must_exist=True)
                if not validated_path.is_file():
                    raise ValueError(f"Path '{raw_path}' is not a file.")
                if validated_path.suffix.lower() not in _ALLOWED_INPUT_SUFFIXES:
                    raise ValueError(
                        f"Unsupported file type '{validated_path.suffix}'. "
                        f"Allowed types are: {sorted(_ALLOWED_INPUT_SUFFIXES)}."
                    )
                if validated_path not in validated_paths:
                    validated_paths.append(validated_path)
            except ValueError as exc:
                rejected_paths.append(str(exc))

        for rejected_path in rejected_paths:
            logger.warning(f"Rejected interpreter input path: {rejected_path}")

        return validated_paths

    def extract_paths_from_db(self, db_manager, tool_name: str) -> list[str]:
        payload = db_manager.get(tool_name)
        if payload is None:
            return []

        try:
            payload_json = json.loads(payload)
        except json.JSONDecodeError as exc:
            logger.warning(f"Could not decode tool payload for {tool_name}: {exc}")
            return []

        return payload_json.get("output", {}).get("paths", [])

    def build_system_prompt(self, session_dir: Path, file_paths: list[Path]) -> str:
        allowed_paths = "\n".join(f"- {path}" for path in file_paths)
        return (
            "You are a Python data analysis assistant.\n"
            "Write a self-contained Python script that reads the provided file(s), "
            "fulfils the user's request, and prints a concise text summary to stdout.\n\n"
            "Rules:\n"
            "- pandas, numpy, json, pathlib, plotly, math, statistics, csv, itertools, collections, and re are available.\n"
            "- Read only the explicitly provided session files listed below.\n"
            "- Save any output files only inside the session directory shown below.\n"
            "- Do not attempt network access, subprocess execution, package installation, or filesystem access outside the session directory.\n"
            "- Use the exact column names shown in the file previews; do not guess them.\n"
            "- Print a SHORT summary (counts, stats, top-N rows); never print an entire dataframe.\n"
            f"- Session directory for outputs: {session_dir}\n"
            f"- Allowed input files:\n{allowed_paths}\n"
            "- For visualizations use Plotly and write JSON with: "
            f'fig.write_json(str(Path("{session_dir}") / "<same-stem-as-input>.json"))\n'
            "- Do NOT call plt.show(), fig.show(), or any interactive display.\n"
            "- Return ONLY the Python code inside a single ```python ... ``` block."
        )

    def build_preview_block(self, file_paths: list[Path]) -> str:
        file_previews = []
        for file_path in file_paths:
            try:
                file_previews.append(self.preview_file(file_path))
            except Exception as exc:
                logger.warning(f"Could not preview {file_path}: {exc}")
                file_previews.append(f"File: {file_path} (could not preview)")
        return "\n\n".join(file_previews) if file_previews else "(no files)"

    def preview_file(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix in {".csv", ".tsv", ".txt"}:
            return self.preview_delimited_file(file_path)
        if suffix in {".xls", ".xlsx"}:
            preview = pd.read_excel(file_path, nrows=3)
            return self.format_dataframe_preview(file_path, preview)
        return self.preview_text_file(file_path)

    def preview_delimited_file(self, file_path: Path) -> str:
        sep = "\t" if file_path.suffix.lower() in {".tsv", ".txt"} else ","
        preview = pd.read_csv(file_path, sep=sep, nrows=3)
        return self.format_dataframe_preview(file_path, preview)

    def format_dataframe_preview(self, file_path: Path, preview: pd.DataFrame) -> str:
        if hasattr(preview, "map"):
            preview = preview.map(self.truncate_cell)
        else:
            preview = preview.applymap(self.truncate_cell)
        return (
            f"File: {file_path}\n"
            f"Columns: {preview.columns.tolist()}\n"
            f"Dtypes: {preview.dtypes.astype(str).to_dict()}\n"
            f"Preview (3 rows):\n{preview.to_string(index=False)}"
        )

    def preview_text_file(self, file_path: Path) -> str:
        preview_lines = []
        with file_path.open("r", encoding="utf-8", errors="replace") as handle:
            for index, line in enumerate(handle):
                if index >= 10:
                    break
                preview_lines.append(line.rstrip("\n")[:200])

        preview_body = "\n".join(preview_lines) if preview_lines else "(empty file)"
        return f"File: {file_path}\nPreview (10 lines max):\n{preview_body}"

    def execute_in_subprocess(
        self,
        code: str,
        session_dir: Path,
        allowed_input_paths: list[Path],
    ) -> dict[str, Any]:
        runner_path = Path(__file__).with_name("sandbox_runner.py")
        timeout_seconds = get_interpreter_timeout_seconds()

        payload = {
            "code": code,
            "session_dir": str(session_dir),
            "allowed_input_paths": [str(path) for path in allowed_input_paths],
            "timeout_seconds": timeout_seconds,
            "cpu_seconds": get_interpreter_cpu_seconds(),
            "memory_bytes": get_interpreter_memory_bytes(),
            "file_size_bytes": get_interpreter_max_file_bytes(),
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as payload_file:
            json.dump(payload, payload_file)
            payload_path = Path(payload_file.name)

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as result_file:
            result_path = Path(result_file.name)

        process = None
        try:
            process = subprocess.Popen(
                [sys.executable, "-I", str(runner_path), "--payload", str(payload_path), "--result", str(result_path)],
                cwd=session_dir,
                env={
                    "HOME": str(session_dir),
                    "PYTHONIOENCODING": "utf-8",
                    "TMPDIR": str(session_dir),
                },
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )

            stdout, stderr = process.communicate(timeout=timeout_seconds + 2)
        except subprocess.TimeoutExpired:
            if process is not None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    process.kill()
                process.wait()
            result_path.unlink(missing_ok=True)
            return {
                "success": False,
                "stdout": "",
                "error": f"Interpreter execution timed out after {timeout_seconds} seconds.",
            }
        finally:
            payload_path.unlink(missing_ok=True)

        result: dict[str, Any] | None = None
        if result_path.exists():
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                logger.warning(f"Could not decode sandbox result: {exc}")
            finally:
                result_path.unlink(missing_ok=True)

        if result is None:
            error_message = stderr.strip() or stdout.strip() or "Interpreter execution failed."
            return {"success": False, "stdout": "", "error": error_message}

        if process.returncode != 0 and not result.get("error"):
            result["error"] = stderr.strip() or "Interpreter subprocess failed."

        return result

    def extract_python_code(self, text: str) -> str | None:
        code_blocks = re.findall(r"```python\s*(.*?)\s*```", text, re.DOTALL)
        if not code_blocks:
            code_blocks = re.findall(r"```\s*(.*?)\s*```", text, re.DOTALL)
        return code_blocks[0] if code_blocks else None

    def extract_file_paths(self, text: str) -> list[str]:
        candidates: list[str] = []
        quoted_spans: list[tuple[int, int]] = []

        for match in _QUOTED_FILE_PATH_PATTERN.finditer(text):
            candidates.append(match.group("path"))
            quoted_spans.append(match.span())

        for match in _UNQUOTED_FILE_PATH_PATTERN.finditer(text):
            if self.is_overlapping_span(match.span(), quoted_spans):
                continue
            candidates.append(match.group("path"))

        return self.deduplicate_paths(candidates)

    def capture_session_file_metadata(self, session_dir: Path) -> dict[Path, tuple[int, int]]:
        metadata: dict[Path, tuple[int, int]] = {}
        for path in session_dir.rglob("*"):
            if not path.is_file():
                continue
            stat = path.stat()
            metadata[path.resolve(strict=False)] = (stat.st_mtime_ns, stat.st_size)
        return metadata

    def find_changed_or_new_files(
        self,
        previous_metadata: dict[Path, tuple[int, int]],
        current_metadata: dict[Path, tuple[int, int]],
    ) -> set[Path]:
        return {
            path
            for path, metadata in current_metadata.items()
            if previous_metadata.get(path) != metadata
        }

    def truncate_output(self, output: str) -> str:
        if len(output) <= _MAX_OUTPUT_CHARS:
            return output
        return output[:_MAX_OUTPUT_CHARS] + f"\n... [output truncated at {_MAX_OUTPUT_CHARS} chars]"

    @staticmethod
    def truncate_cell(value: Any) -> Any:
        if isinstance(value, str) and len(value) > 80:
            return value[:80] + "..."
        return value

    @staticmethod
    def deduplicate_paths(paths: list[str]) -> list[str]:
        deduplicated_paths: list[str] = []
        for path in paths:
            if path not in deduplicated_paths:
                deduplicated_paths.append(path)
        return deduplicated_paths

    @staticmethod
    def is_overlapping_span(span: tuple[int, int], other_spans: list[tuple[int, int]]) -> bool:
        return any(span[0] < other[1] and other[0] < span[1] for other in other_spans)
