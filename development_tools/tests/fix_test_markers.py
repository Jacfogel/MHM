#!/usr/bin/env python3
# TOOL_TIER: supporting
# TOOL_PORTABILITY: portable

"""
fix_test_markers.py
Add missing pytest category markers to test files based on directory structure.
This tool performs the fixing operation (add_markers) extracted from analyze_test_markers.py.
"""

import sys
from pathlib import Path
from typing import Dict, Optional

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
try:
    from . import config
    from .analyze_test_markers import TestMarkerAnalyzer
except ImportError:
    from development_tools import config
    from development_tools.tests.analyze_test_markers import TestMarkerAnalyzer

from core.logger import get_component_logger

# Ensure external config is loaded
config.load_external_config()

logger = get_component_logger("development_tools")


def add_markers(dry_run: bool = False, project_root: Optional[Path] = None) -> Dict:
    """
    Add missing markers to test files based on directory structure.
    
    Args:
        dry_run: If True, show what would be changed without making changes
        project_root: Optional project root path
        
    Returns:
        Dictionary with 'updated', 'skipped', and 'dry_run' keys
    """
    analyzer = TestMarkerAnalyzer(project_root=project_root)
    return analyzer.add_markers(dry_run=dry_run)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Add missing pytest category markers to test files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    result = add_markers(dry_run=args.dry_run)
    
    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        if args.dry_run:
            print(f"Would update {len(result['updated'])} files:")
        else:
            print(f"Updated {len(result['updated'])} files:")
        for f, marker in result['updated']:
            print(f"  {marker}: {f}")
        print(f"\nSkipped {len(result['skipped'])} files (already have markers or not in standard directories)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

