from __future__ import annotations

from app.core.agents.interpreter.sandbox_runner import execute_user_code, validate_code


def test_validate_code_rejects_dunder_attribute_access():
    try:
        validate_code("x = object().__class__")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Dunder attribute access" in str(exc)


def test_execute_user_code_returns_captured_output_on_exception(tmp_path):
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    input_file = session_dir / "input.csv"
    input_file.write_text("a,b\n1,2\n", encoding="utf-8")

    result = execute_user_code(
        {
            "code": "print('hello before error')\nraise ValueError('boom')",
            "session_dir": str(session_dir),
            "allowed_input_paths": [str(input_file)],
            "timeout_seconds": 5,
            "cpu_seconds": 5,
            "memory_bytes": 128 * 1024 * 1024,
            "file_size_bytes": 10 * 1024 * 1024,
        }
    )

    assert result["success"] is False
    assert "hello before error" in result["stdout"]
    assert result["error"] == "boom"
    assert "ValueError: boom" in result["traceback"]
