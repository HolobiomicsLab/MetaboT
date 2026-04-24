from __future__ import annotations

import argparse
import ast
import builtins
import contextlib
import io
import json
import os
import signal
import sys
import tempfile
import traceback
from pathlib import Path


ALLOWED_IMPORT_ROOTS = {
    "collections",
    "csv",
    "itertools",
    "json",
    "math",
    "numpy",
    "pandas",
    "pathlib",
    "plotly",
    "re",
    "statistics",
}

REAL_IMPORT = builtins.__import__
REAL_OPEN = builtins.open
REAL_IO_OPEN = io.open
REAL_OS_OPEN = os.open


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--result", required=True)
    return parser.parse_args()


def write_result(result_path: Path, payload: dict) -> None:
    with REAL_OPEN(result_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)


def validate_code(code: str) -> None:
    tree = ast.parse(code, mode="exec")
    blocked_names = {"__import__", "eval", "exec", "compile", "globals", "locals", "vars", "breakpoint"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] not in ALLOWED_IMPORT_ROOTS:
                    raise ValueError(f"Import of '{alias.name}' is not allowed.")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".", 1)[0] not in ALLOWED_IMPORT_ROOTS:
                raise ValueError(f"Import from '{module}' is not allowed.")
        elif isinstance(node, ast.Name) and node.id in blocked_names:
            raise ValueError(f"Use of '{node.id}' is not allowed.")


def apply_resource_limits(config: dict) -> None:
    try:
        import resource
    except ImportError:
        return

    cpu_seconds = int(config["cpu_seconds"])
    memory_bytes = int(config["memory_bytes"])
    file_size_bytes = int(config["file_size_bytes"])

    limits = [
        ("RLIMIT_CPU", (cpu_seconds, cpu_seconds)),
        ("RLIMIT_AS", (memory_bytes, memory_bytes)),
        ("RLIMIT_DATA", (memory_bytes, memory_bytes)),
        ("RLIMIT_FSIZE", (file_size_bytes, file_size_bytes)),
        ("RLIMIT_NOFILE", (64, 64)),
        ("RLIMIT_NPROC", (1, 1)),
    ]

    for limit_name, limit_value in limits:
        if not hasattr(resource, limit_name):
            continue
        try:
            resource.setrlimit(getattr(resource, limit_name), limit_value)
        except (OSError, ValueError):
            continue


def configure_timeout(timeout_seconds: int) -> None:
    def handle_timeout(signum, frame):
        raise TimeoutError(f"Interpreter execution timed out after {timeout_seconds} seconds.")

    signal.signal(signal.SIGALRM, handle_timeout)
    signal.alarm(timeout_seconds)


def disable_network() -> None:
    import socket

    def blocked(*args, **kwargs):
        raise PermissionError("Outbound network access is disabled for the interpreter.")

    socket.socket = blocked
    socket.create_connection = blocked
    socket.fromfd = blocked
    socket.socketpair = blocked
    socket.getaddrinfo = blocked
    socket.gethostbyname = blocked


def patch_filesystem_access(session_dir: Path, allowed_input_paths: list[str]):
    allowed_reads = {Path(path).resolve(strict=False) for path in allowed_input_paths}
    created_paths: set[Path] = set()

    tempfile.tempdir = str(session_dir)

    def resolve_candidate(path_value) -> Path:
        if isinstance(path_value, bytes):
            path_value = os.fsdecode(path_value)
        if isinstance(path_value, int):
            raise PermissionError("File descriptor access is not allowed in the interpreter sandbox.")

        candidate = Path(path_value)
        if not candidate.is_absolute():
            candidate = session_dir / candidate

        return candidate.resolve(strict=False)

    def ensure_allowed(path_value, mode: str) -> Path:
        resolved = resolve_candidate(path_value)
        write_mode = any(flag in mode for flag in ("w", "a", "x", "+"))

        if write_mode:
            if not is_within_directory(resolved, session_dir):
                raise PermissionError("Writes are restricted to the active session directory.")
            resolved.parent.mkdir(parents=True, exist_ok=True)
            created_paths.add(resolved)
            return resolved

        if resolved in allowed_reads or resolved in created_paths:
            return resolved

        raise PermissionError("Reads are restricted to validated session input files.")

    def safe_open(file, mode="r", *args, **kwargs):
        resolved = ensure_allowed(file, mode)
        return REAL_OPEN(resolved, mode, *args, **kwargs)

    def safe_io_open(file, mode="r", *args, **kwargs):
        resolved = ensure_allowed(file, mode)
        return REAL_IO_OPEN(resolved, mode, *args, **kwargs)

    def safe_os_open(file, flags, mode=0o777, *args, **kwargs):
        write_flags = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
        open_mode = "r+" if flags & write_flags else "r"
        resolved = ensure_allowed(file, open_mode)
        return REAL_OS_OPEN(os.fspath(resolved), flags, mode, *args, **kwargs)

    builtins.open = safe_open
    io.open = safe_io_open
    os.open = safe_os_open
    Path.open = lambda self, *args, **kwargs: safe_open(self, *args, **kwargs)

    return safe_open


def is_within_directory(path: Path, directory: Path) -> bool:
    resolved_path = path.resolve(strict=False)
    resolved_directory = directory.resolve(strict=False)
    return resolved_path == resolved_directory or resolved_directory in resolved_path.parents


def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    caller = (globals or {}).get("__name__", "")
    root = name.split(".", 1)[0]
    if caller == "__sandbox__" and root not in ALLOWED_IMPORT_ROOTS:
        raise ImportError(f"Import of '{root}' is not allowed in the interpreter sandbox.")
    return REAL_IMPORT(name, globals, locals, fromlist, level)


def build_safe_builtins(safe_open):
    return {
        "__import__": guarded_import,
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "bytes": bytes,
        "dict": dict,
        "enumerate": enumerate,
        "Exception": Exception,
        "FileNotFoundError": FileNotFoundError,
        "filter": filter,
        "float": float,
        "int": int,
        "isinstance": isinstance,
        "KeyError": KeyError,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "next": next,
        "open": safe_open,
        "PermissionError": PermissionError,
        "print": print,
        "range": range,
        "round": round,
        "RuntimeError": RuntimeError,
        "set": set,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "TimeoutError": TimeoutError,
        "tuple": tuple,
        "ValueError": ValueError,
        "zip": zip,
    }


def execute_user_code(config: dict) -> dict:
    session_dir = Path(config["session_dir"]).resolve(strict=False)
    session_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(session_dir)

    if hasattr(os, "geteuid") and os.geteuid() == 0:
        raise PermissionError(
            "The interpreter runner must not execute as root. "
            "Run MetaboT under a restricted OS user before enabling trusted mode."
        )

    validate_code(config["code"])
    apply_resource_limits(config)
    configure_timeout(int(config["timeout_seconds"]))
    disable_network()
    safe_open = patch_filesystem_access(session_dir, config["allowed_input_paths"])

    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    safe_builtins = build_safe_builtins(safe_open)
    sandbox_globals = {"__builtins__": safe_builtins, "__name__": "__sandbox__"}

    try:
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            exec(compile(config["code"], "<metabot-interpreter>", "exec"), sandbox_globals, sandbox_globals)
        return {
            "success": True,
            "stdout": stdout_buffer.getvalue(),
            "stderr": stderr_buffer.getvalue(),
            "error": "",
        }
    finally:
        signal.alarm(0)


def main() -> int:
    args = parse_args()
    payload_path = Path(args.payload)
    result_path = Path(args.result)

    try:
        with REAL_OPEN(payload_path, "r", encoding="utf-8") as handle:
            config = json.load(handle)
        result = execute_user_code(config)
        write_result(result_path, result)
        return 0 if result.get("success") else 1
    except Exception as exc:
        write_result(
            result_path,
            {
                "success": False,
                "stdout": "",
                "stderr": "",
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
