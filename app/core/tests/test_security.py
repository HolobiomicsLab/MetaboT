import pytest

from app.core.security import resolve_session_path
from app.core.utils import load_config


def test_load_config_excludes_interpreter_by_default(monkeypatch):
    monkeypatch.delenv("METABOT_TRUSTED_MODE", raising=False)

    config = load_config()

    assert "Interpreter_agent" not in config["supervisor"]["members"]
    assert all(agent["name"] != "Interpreter_agent" for agent in config["agents"])


def test_load_config_includes_interpreter_in_trusted_mode(monkeypatch):
    monkeypatch.setenv("METABOT_TRUSTED_MODE", "true")

    config = load_config()

    assert "Interpreter_agent" in config["supervisor"]["members"]
    assert any(agent["name"] == "Interpreter_agent" for agent in config["agents"])


def test_resolve_session_path_allows_current_session_files(tmp_path):
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    allowed_file = session_dir / "input.csv"
    allowed_file.write_text("a,b\n1,2\n", encoding="utf-8")

    resolved = resolve_session_path(allowed_file, session_dir=session_dir)

    assert resolved == allowed_file.resolve()


def test_resolve_session_path_rejects_outside_files(tmp_path):
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    outside_file = tmp_path / "outside.csv"
    outside_file.write_text("a,b\n1,2\n", encoding="utf-8")

    with pytest.raises(ValueError):
        resolve_session_path(outside_file, session_dir=session_dir)
