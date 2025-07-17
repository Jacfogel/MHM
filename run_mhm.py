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

@handle_errors("launching MHM Manager", default_return=1)
def main():
    """Launch the MHM Manager UI"""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if the UI app exists
    ui_app_path = os.path.join(script_dir, 'ui', 'ui_app_qt.py')
    if not os.path.exists(ui_app_path):
        print(f"Error: Could not find ui_app_qt.py at {ui_app_path}")
        return 1
    
    # Ensure we use the venv Python explicitly
    venv_python = os.path.join(script_dir, '.venv', 'Scripts', 'python.exe')
    if os.path.exists(venv_python):
        python_executable = venv_python
    else:
        python_executable = sys.executable
    
    print(f"Using Python: {python_executable}")
    
    # Set up environment to ensure venv is used
    env = os.environ.copy()
    venv_scripts_dir = os.path.join(script_dir, '.venv', 'Scripts')
    if os.path.exists(venv_scripts_dir):
        # Add venv Scripts directory to PATH to ensure it's found first
        env['PATH'] = venv_scripts_dir + os.pathsep + env.get('PATH', '')
    
    # Launch the UI directly
    try:
        process = subprocess.Popen(
            [python_executable, ui_app_path],
            env=env,
            cwd=script_dir,  # Set working directory to project root
            shell=False,     # Explicitly prevent shell interpretation
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        # Wait for the process to complete
        process.wait()
        return process.returncode
    except Exception as e:
        print(f"Error launching UI: {e}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0) 