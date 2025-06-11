#!/usr/bin/env python3
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

def main():
    """Launch the MHM Manager UI"""
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ui_app_path = os.path.join(script_dir, 'ui', 'ui_app.py')
        
        # Check if the UI app exists
        if not os.path.exists(ui_app_path):
            print(f"Error: Could not find ui_app.py at {ui_app_path}")
            return 1
        
        # Launch the UI
        subprocess.run([sys.executable, ui_app_path])
        return 0
        
    except KeyboardInterrupt:
        print("\nExiting...")
        return 0
    except Exception as e:
        print(f"Error launching MHM Manager: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 