from __future__ import annotations

import os
from pathlib import Path


_TRUE_VALUES = {"1", "true", "yes", "on", "y", "t"}


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in _TRUE_VALUES


def is_trusted_mode_enabled() -> bool:
    """Trusted mode opt-in for features that execute generated code."""
    return env_flag("METABOT_TRUSTED_MODE", default=False)


def get_interpreter_timeout_seconds() -> int:
    return max(1, int(os.getenv("METABOT_INTERPRETER_TIMEOUT_SECONDS", "15")))


def get_interpreter_cpu_seconds() -> int:
    timeout_seconds = get_interpreter_timeout_seconds()
    return max(1, int(os.getenv("METABOT_INTERPRETER_CPU_SECONDS", str(timeout_seconds))))


def get_interpreter_memory_bytes() -> int:
    memory_mb = max(64, int(os.getenv("METABOT_INTERPRETER_MEMORY_MB", "512")))
    return memory_mb * 1024 * 1024


def get_interpreter_max_file_bytes() -> int:
    file_mb = max(8, int(os.getenv("METABOT_INTERPRETER_MAX_FILE_MB", "64")))
    return file_mb * 1024 * 1024


def is_path_within_directory(path: Path, directory: Path) -> bool:
    resolved_path = path.resolve(strict=False)
    resolved_directory = directory.resolve(strict=False)
    return resolved_path == resolved_directory or resolved_directory in resolved_path.parents


def resolve_session_path(path_value: str | Path, session_dir: Path, must_exist: bool = True) -> Path:
    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = session_dir / candidate

    resolved = candidate.resolve(strict=False)
    if not is_path_within_directory(resolved, session_dir):
        raise ValueError(
            f"Path '{path_value}' is outside the allowed session directory '{session_dir}'."
        )

    if must_exist and not resolved.exists():
        raise ValueError(f"Path '{path_value}' does not exist in the current session.")

    return resolved
