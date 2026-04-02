# launch_env.py - Shared venv / PYTHONPATH setup for subprocess launches
"""
Launch helpers used by the UI launcher, headless service, and run_mhm.

Kept under ``core`` so any code path that imports ``core`` (including dev tools)
does not need the repo root on ``sys.path`` as a top-level ``run_mhm`` module.
"""

import os
import sys
from pathlib import Path

from core.error_handling import handle_errors


@handle_errors("resolving Python interpreter", default_return=sys.executable)
def resolve_python_interpreter(script_dir: str) -> str:
    """
    Return the preferred Python executable for the given project directory.

    Checks for virtual environment Python first, then falls back to system Python.
    """
    script_path = Path(script_dir)
    candidates = [
        script_path / ".venv" / "Scripts" / "python.exe",
        script_path / ".venv" / "bin" / "python",
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return sys.executable


@handle_errors("preparing launch environment", default_return=None)
def prepare_launch_environment(script_dir: str) -> dict[str, str] | None:
    """
    Create an environment dict that prefers the project's virtualenv.

    Sets up PATH and PYTHONPATH so the venv is used and project imports work.
    """
    env = os.environ.copy()
    path_entries: list[str] = []
    script_path = Path(script_dir)

    venv_scripts_dir = script_path / ".venv" / "Scripts"
    if venv_scripts_dir.exists():
        path_entries.append(str(venv_scripts_dir))

    venv_bin_dir = script_path / ".venv" / "bin"
    if venv_bin_dir.exists():
        path_entries.append(str(venv_bin_dir))

    if path_entries:
        existing_path = env.get("PATH", "")
        path_components = path_entries + ([existing_path] if existing_path else [])
        env["PATH"] = os.pathsep.join(path_components)

    env["PYTHONPATH"] = script_dir
    return env
