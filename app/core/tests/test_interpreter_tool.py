from __future__ import annotations

import json
import time
from pathlib import Path

from app.core.agents.interpreter.tool_interpreter import Interpreter


class StubDBManager:
    def __init__(self, payloads: dict[str, str] | None = None):
        self.payloads = payloads or {}

    def get(self, tool_name: str):
        return self.payloads.get(tool_name)


class StubLLMResponse:
    def __init__(self, content):
        self.content = content


class StubLLM:
    def __init__(self, content=None, error: Exception | None = None):
        self.content = content
        self.error = error

    def invoke(self, messages):
        if self.error is not None:
            raise self.error
        return StubLLMResponse(self.content)


def build_interpreter() -> Interpreter:
    return Interpreter(llm_instance=object())


def test_extract_file_paths_allows_dots_in_file_stem():
    interpreter = build_interpreter()

    paths = interpreter.extract_file_paths("Use /tmp/session/foo.v1.csv for the analysis.")

    assert paths == ["/tmp/session/foo.v1.csv"]


def test_extract_file_paths_supports_quoted_paths_with_spaces():
    interpreter = build_interpreter()

    paths = interpreter.extract_file_paths('Filepath: "/tmp/session/my file.v1.csv"')

    assert paths == ["/tmp/session/my file.v1.csv"]


def test_extract_file_paths_supports_multiple_paths():
    interpreter = build_interpreter()

    paths = interpreter.extract_file_paths(
        'Compare "/tmp/session/my file.v1.csv" with /tmp/session/other_file.tsv'
    )

    assert paths == ["/tmp/session/my file.v1.csv", "/tmp/session/other_file.tsv"]


def test_collect_allowed_file_paths_falls_back_to_db_when_no_explicit_paths(tmp_path):
    interpreter = build_interpreter()
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    input_file = session_dir / "from_db.csv"
    input_file.write_text("a,b\n1,2\n", encoding="utf-8")
    db_manager = StubDBManager(
        {
            "tool_sparql": json.dumps(
                {"output": {"paths": [str(input_file)]}}
            )
        }
    )

    paths = interpreter.collect_allowed_file_paths(
        input_text="Interpret the latest results.",
        session_dir=session_dir,
        db_manager=db_manager,
    )

    assert paths == [input_file.resolve()]


def test_collect_allowed_file_paths_rejects_invalid_path_without_suppressing_valid_explicit_path(tmp_path):
    interpreter = build_interpreter()
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    valid_file = session_dir / "valid file.csv"
    valid_file.write_text("a,b\n1,2\n", encoding="utf-8")
    outside_file = tmp_path / "outside.csv"
    outside_file.write_text("a,b\n9,9\n", encoding="utf-8")

    paths = interpreter.collect_allowed_file_paths(
        input_text=f'Use "{outside_file}" and "{valid_file}"',
        session_dir=session_dir,
        db_manager=StubDBManager(),
    )

    assert paths == [valid_file.resolve()]


def test_extract_paths_from_db_handles_unexpected_payload_shape():
    interpreter = build_interpreter()

    paths = interpreter.extract_paths_from_db(
        StubDBManager({"tool_sparql": json.dumps(["not-a-dict"])}),
        "tool_sparql",
    )

    assert paths == []


def test_extract_paths_from_db_supports_top_level_paths_list():
    interpreter = build_interpreter()

    paths = interpreter.extract_paths_from_db(
        StubDBManager({"tool_sparql": json.dumps({"paths": ["a.csv"]})}),
        "tool_sparql",
    )

    assert paths == ["a.csv"]


def test_find_changed_or_new_files_includes_new_file(tmp_path):
    interpreter = build_interpreter()
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    before = interpreter.capture_session_file_metadata(session_dir)

    created_file = session_dir / "created.csv"
    created_file.write_text("a,b\n1,2\n", encoding="utf-8")
    after = interpreter.capture_session_file_metadata(session_dir)

    changed_files = interpreter.find_changed_or_new_files(before, after)

    assert changed_files == {created_file.resolve()}


def test_find_changed_or_new_files_includes_overwritten_file(tmp_path):
    interpreter = build_interpreter()
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    existing_file = session_dir / "updated.csv"
    existing_file.write_text("a,b\n1,2\n", encoding="utf-8")
    before = interpreter.capture_session_file_metadata(session_dir)

    time.sleep(0.001)
    existing_file.write_text("a,b\n30,400\n", encoding="utf-8")
    after = interpreter.capture_session_file_metadata(session_dir)

    changed_files = interpreter.find_changed_or_new_files(before, after)

    assert changed_files == {existing_file.resolve()}


def test_find_changed_or_new_files_ignores_unchanged_files(tmp_path):
    interpreter = build_interpreter()
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    existing_file = session_dir / "unchanged.csv"
    existing_file.write_text("a,b\n1,2\n", encoding="utf-8")
    before = interpreter.capture_session_file_metadata(session_dir)
    after = interpreter.capture_session_file_metadata(session_dir)

    changed_files = interpreter.find_changed_or_new_files(before, after)

    assert changed_files == set()


def test_run_returns_user_friendly_error_when_llm_invoke_fails(tmp_path, monkeypatch):
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    input_file = session_dir / "input.csv"
    input_file.write_text("a,b\n1,2\n", encoding="utf-8")
    interpreter = Interpreter(llm_instance=StubLLM(error=RuntimeError("boom")))

    monkeypatch.setenv("METABOT_TRUSTED_MODE", "true")
    monkeypatch.setattr(
        "app.core.agents.interpreter.tool_interpreter.create_user_session",
        lambda session_id, user_session_dir=False, input_dir=False: session_dir,
    )
    monkeypatch.setattr(
        "app.core.agents.interpreter.tool_interpreter.tools_database",
        lambda: StubDBManager(),
    )

    result = interpreter._run(f'Filepath: "{input_file}"')

    assert result == "Interpreter could not generate analysis code for this request."


def test_run_normalizes_non_string_llm_content(tmp_path, monkeypatch):
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    input_file = session_dir / "input.csv"
    input_file.write_text("a,b\n1,2\n", encoding="utf-8")
    interpreter = Interpreter(llm_instance=StubLLM(content=["```python\nprint('ok')\n```"]))

    monkeypatch.setenv("METABOT_TRUSTED_MODE", "true")
    monkeypatch.setattr(
        "app.core.agents.interpreter.tool_interpreter.create_user_session",
        lambda session_id, user_session_dir=False, input_dir=False: session_dir,
    )
    monkeypatch.setattr(
        "app.core.agents.interpreter.tool_interpreter.tools_database",
        lambda: StubDBManager(),
    )
    monkeypatch.setattr(
        Interpreter,
        "execute_in_subprocess",
        lambda self, code, session_dir, allowed_input_paths: {"stdout": "ok", "error": ""},
    )

    result = interpreter._run(f'Filepath: "{input_file}"')

    assert result == "ok"
