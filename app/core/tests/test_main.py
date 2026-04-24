from __future__ import annotations

import sys
from pathlib import Path

import app.core.main as main_module


class DummyLogger:
    def __init__(self):
        self.info_messages = []
        self.error_messages = []

    def info(self, message, *args):
        if args:
            message = message % args
        self.info_messages.append(message)

    def error(self, message, *args):
        if args:
            message = message % args
        self.error_messages.append(message)


def test_prepare_session_files_copies_valid_file(tmp_path, monkeypatch):
    input_dir = tmp_path / "input_files"
    input_dir.mkdir()
    source_file = tmp_path / "source.csv"
    source_file.write_text("a,b\n1,2\n", encoding="utf-8")
    dummy_logger = DummyLogger()
    input_dir_path = input_dir

    monkeypatch.setattr(main_module, "create_user_session", lambda session_id, input_dir=False: input_dir_path)
    monkeypatch.setattr(main_module, "logger", dummy_logger)

    staged_dir = main_module._prepare_session_files("session-id", [str(source_file)])

    copied_file = input_dir / source_file.name
    assert staged_dir == input_dir
    assert copied_file.read_text(encoding="utf-8") == source_file.read_text(encoding="utf-8")


def test_prepare_session_files_rejects_directory(tmp_path, monkeypatch):
    input_dir = tmp_path / "input_files"
    input_dir.mkdir()
    source_dir = tmp_path / "source_dir"
    source_dir.mkdir()
    input_dir_path = input_dir

    monkeypatch.setattr(main_module, "create_user_session", lambda session_id, input_dir=False: input_dir_path)

    try:
        main_module._prepare_session_files("session-id", [str(source_dir)])
        assert False, "Expected SessionFilePreparationError"
    except main_module.SessionFilePreparationError as exc:
        assert "not a file" in str(exc)


def test_prepare_session_files_rejects_colliding_basenames(tmp_path, monkeypatch):
    input_dir = tmp_path / "input_files"
    input_dir.mkdir()
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first_file = first_dir / "results.csv"
    second_file = second_dir / "results.csv"
    first_file.write_text("a,b\n1,2\n", encoding="utf-8")
    second_file.write_text("a,b\n3,4\n", encoding="utf-8")
    dummy_logger = DummyLogger()
    input_dir_path = input_dir

    monkeypatch.setattr(main_module, "create_user_session", lambda session_id, input_dir=False: input_dir_path)
    monkeypatch.setattr(main_module, "logger", dummy_logger)

    try:
        main_module._prepare_session_files("session-id", [str(first_file), str(second_file)])
        assert False, "Expected SessionFilePreparationError"
    except main_module.SessionFilePreparationError as exc:
        assert "would overwrite" in str(exc)


def test_prepare_session_files_rejects_same_file_destination(tmp_path, monkeypatch):
    input_dir = tmp_path / "input_files"
    input_dir.mkdir()
    staged_file = input_dir / "already_staged.csv"
    staged_file.write_text("a,b\n1,2\n", encoding="utf-8")
    input_dir_path = input_dir

    monkeypatch.setattr(main_module, "create_user_session", lambda session_id, input_dir=False: input_dir_path)

    try:
        main_module._prepare_session_files("session-id", [str(staged_file)])
        assert False, "Expected SessionFilePreparationError"
    except main_module.SessionFilePreparationError as exc:
        assert "already staged" in str(exc)


def test_main_passes_cli_api_key_and_reconfigures_logger(monkeypatch):
    original_argv = sys.argv[:]
    state = {"session_initialized": False, "setup_logger_states": []}
    captured = {}

    def fake_setup_logger(name):
        state["setup_logger_states"].append(state["session_initialized"])
        return DummyLogger()

    def fake_initialize_session_context(session_id):
        state["session_initialized"] = True

    def fake_llm_creation(api_key=None, params_file=None):
        captured["llm_api_key"] = api_key
        return {"llm_o": object()}

    def fake_create_workflow(models, session_id=None, endpoint_url=None, evaluation=False, api_key=None):
        captured["workflow_api_key"] = api_key
        captured["session_id"] = session_id
        return "workflow"

    def fake_process_workflow(workflow, question):
        captured["workflow"] = workflow
        captured["question"] = question

    monkeypatch.setattr(sys, "argv", ["prog", "-c", "hello", "--api-key", "cli-key"])
    monkeypatch.setattr(main_module, "logger", DummyLogger())
    monkeypatch.setattr(main_module, "setup_logger", fake_setup_logger)
    monkeypatch.setattr(main_module, "initialize_session_context", fake_initialize_session_context)
    monkeypatch.setattr(main_module, "create_user_session", lambda session_id=None, user_session_dir=False, input_dir=False: "session-123")
    monkeypatch.setattr(main_module, "langsmith_setup", lambda: None)
    monkeypatch.setattr(main_module, "llm_creation", fake_llm_creation)
    monkeypatch.setattr(main_module, "create_workflow", fake_create_workflow)
    monkeypatch.setattr(main_module, "process_workflow", fake_process_workflow)

    try:
        main_module.main()
    finally:
        monkeypatch.setattr(sys, "argv", original_argv)

    assert captured["llm_api_key"] == "cli-key"
    assert captured["workflow_api_key"] == "cli-key"
    assert state["setup_logger_states"] == [True]
    assert captured["session_id"] == "session-123"
    assert captured["workflow"] == "workflow"
    assert captured["question"] == "hello"


def test_main_prints_user_friendly_error_for_bad_staged_file(monkeypatch, capsys):
    original_argv = sys.argv[:]

    monkeypatch.setattr(sys, "argv", ["prog", "-c", "hello", "-f", "/missing/file.csv"])
    monkeypatch.setattr(main_module, "logger", DummyLogger())
    monkeypatch.setattr(main_module, "setup_logger", lambda name: DummyLogger())
    monkeypatch.setattr(main_module, "initialize_session_context", lambda session_id: None)
    monkeypatch.setattr(main_module, "create_user_session", lambda session_id=None, user_session_dir=False, input_dir=False: "session-123")
    monkeypatch.setattr(main_module, "langsmith_setup", lambda: None)
    monkeypatch.setattr(main_module, "llm_creation", lambda api_key=None, params_file=None: {"llm_o": object()})
    monkeypatch.setattr(
        main_module,
        "_prepare_session_files",
        lambda session_id, file_paths: (_ for _ in ()).throw(
            main_module.SessionFilePreparationError(Path(file_paths[0]), f"File not found: {file_paths[0]}")
        ),
    )
    monkeypatch.setattr(main_module, "create_workflow", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("workflow should not run")))

    try:
        main_module.main()
    finally:
        monkeypatch.setattr(sys, "argv", original_argv)

    captured = capsys.readouterr()
    assert "Error: File not found: /missing/file.csv" in captured.out
