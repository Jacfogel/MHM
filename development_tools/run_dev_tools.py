#!/usr/bin/env python3
# TOOL_TIER: core

"""
Shorthand alias for run_development_tools.py

This file provides a convenient shorter name for the development tools CLI.
It simply imports and calls the main function from run_development_tools.py.
"""

import sys
from pathlib import Path

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import and run the main function from run_development_tools
from development_tools.run_development_tools import main

if __name__ == '__main__':
    sys.exit(main())

