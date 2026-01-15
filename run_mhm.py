"""
MHM - Mental Health Manager
Main entry point for the application.

This launches the MHM Manager UI where you can:
- Start/stop/restart the backend service
- Access user management interface
- Monitor service status
"""

import sys
import os
import subprocess
from pathlib import Path
from core.error_handling import handle_errors


@handle_errors("resolving Python interpreter", default_return=sys.executable)
def resolve_python_interpreter(script_dir):
    """
    Return the preferred Python executable for the given project directory.

    Checks for virtual environment Python first, then falls back to system Python.

    Args:
        script_dir (str): The project directory path

    Returns:
        str: Path to Python executable
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
def prepare_launch_environment(script_dir):
    """
    Create an environment dict that prefers the project's virtualenv.

    Sets up PATH and PYTHONPATH to ensure the virtual environment is used
    and project imports work correctly.

    Args:
        script_dir (str): The project directory path

    Returns:
        dict: Environment dictionary with PATH and PYTHONPATH configured
    """
    env = os.environ.copy()
    path_entries = []
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

    # Set PYTHONPATH to include the project root so imports work
    env["PYTHONPATH"] = script_dir

    return env


@handle_errors("launching MHM Manager", default_return=1)
def main():
    """
    Launch the MHM Manager UI.

    Main entry point for the MHM Manager application. Resolves the Python
    interpreter, sets up the environment, and launches the UI application.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Check if the UI app exists
    ui_app_path = Path(script_dir) / "ui" / "ui_app_qt.py"
    if not ui_app_path.exists():
        print(f"Error: Could not find ui_app_qt.py at {ui_app_path}")
        return 1

    # Ensure we use the venv Python explicitly
    python_executable = resolve_python_interpreter(script_dir)

    print(f"Using Python: {python_executable}")

    # Set up environment to ensure venv is used
    env = prepare_launch_environment(script_dir)

    # Launch the UI directly
    try:
        process = subprocess.Popen(
            [python_executable, str(ui_app_path)],
            env=env,
            cwd=script_dir,  # Set working directory to project root
            shell=False,  # Explicitly prevent shell interpretation
            creationflags=(
                getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
            ),
        )
        # Don't wait - let the launcher exit and let the UI run independently
        print("UI launched successfully. Launcher exiting.")
        return 0
    except Exception as e:
        print(f"Error launching UI: {e}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
