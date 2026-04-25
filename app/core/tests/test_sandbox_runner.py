from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.core.agents.interpreter import sandbox_runner
from app.core.agents.interpreter.sandbox_runner import validate_code


def test_validate_code_rejects_dunder_attribute_access():
    with pytest.raises(ValueError) as excinfo:
        validate_code("x = object().__class__")
    assert "Dunder attribute access" in str(excinfo.value)


def test_execute_user_code_returns_captured_output_on_exception_from_subprocess(tmp_path):
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    input_file = session_dir / "input.csv"
    input_file.write_text("a,b\n1,2\n", encoding="utf-8")

    payload_path = tmp_path / "payload.json"
    result_path = tmp_path / "result.json"
    payload_path.write_text(
        json.dumps(
            {
                "code": "print('hello before error')\nraise ValueError('boom')",
                "session_dir": str(session_dir),
                "allowed_input_paths": [str(input_file)],
                "timeout_seconds": 5,
                "cpu_seconds": 5,
                "memory_bytes": 128 * 1024 * 1024,
                "file_size_bytes": 10 * 1024 * 1024,
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            str(Path(sandbox_runner.__file__).resolve()),
            "--payload",
            str(payload_path),
            "--result",
            str(result_path),
        ],
        cwd=session_dir,
        env={
            "HOME": str(session_dir),
            "PYTHONIOENCODING": "utf-8",
            "TMPDIR": str(session_dir),
        },
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert result_path.exists(), completed.stderr or completed.stdout

    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["success"] is False
    assert "hello before error" in result["stdout"]
    assert result["error"] == "boom"
    assert "ValueError: boom" in result["traceback"]
