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
    existing_file.write_text("a,b\n3,4\n", encoding="utf-8")
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
