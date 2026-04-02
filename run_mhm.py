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
from core.launch_env import prepare_launch_environment, resolve_python_interpreter


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
        subprocess.Popen(
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
