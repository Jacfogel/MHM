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
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)


def resolve_python_interpreter(script_dir):
    """
    Return the preferred Python executable for the given project directory.
    
    Checks for virtual environment Python first, then falls back to system Python.
    
    Args:
        script_dir (str): The project directory path
        
    Returns:
        str: Path to Python executable
    """
    candidates = [
        os.path.join(script_dir, '.venv', 'Scripts', 'python.exe'),
        os.path.join(script_dir, '.venv', 'bin', 'python'),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return sys.executable


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

    venv_scripts_dir = os.path.join(script_dir, '.venv', 'Scripts')
    if os.path.exists(venv_scripts_dir):
        path_entries.append(venv_scripts_dir)

    venv_bin_dir = os.path.join(script_dir, '.venv', 'bin')
    if os.path.exists(venv_bin_dir):
        path_entries.append(venv_bin_dir)

    if path_entries:
        existing_path = env.get('PATH', '')
        path_components = path_entries + ([existing_path] if existing_path else [])
        env['PATH'] = os.pathsep.join(path_components)

    # Set PYTHONPATH to include the project root so imports work
    env['PYTHONPATH'] = script_dir

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
    ui_app_path = os.path.join(script_dir, 'ui', 'ui_app_qt.py')
    if not os.path.exists(ui_app_path):
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
            [python_executable, ui_app_path],
            env=env,
            cwd=script_dir,  # Set working directory to project root
            shell=False,     # Explicitly prevent shell interpretation
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0) if os.name == 'nt' else 0
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