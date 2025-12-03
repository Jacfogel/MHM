#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
decision_support.py
AI Decision Support Dashboard: actionable insights for codebase improvement and safe AI changes.
Highlights high-complexity functions, undocumented handlers, duplicate names, and suggests next steps.
"""

import sys
from pathlib import Path
import ast

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
try:
    from . import config
    from ..functions.analyze_functions import scan_all_functions, categorize_functions
except ImportError:
    import sys
    from pathlib import Path
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from development_tools import config
    from development_tools.functions.analyze_functions import scan_all_functions, categorize_functions

from core.logger import get_component_logger

# Ensure external config is loaded
config.load_external_config()

logger = get_component_logger("development_tools")

# Load config values using the new configurable functions
FUNCTION_DISCOVERY_CONFIG = config.get_analyze_functions_config()
MODERATE_COMPLEXITY = FUNCTION_DISCOVERY_CONFIG.get('moderate_complexity_threshold', 50)
HIGH_COMPLEXITY = FUNCTION_DISCOVERY_CONFIG.get('high_complexity_threshold', 100)
CRITICAL_COMPLEXITY = FUNCTION_DISCOVERY_CONFIG.get('critical_complexity_threshold', 200)
HANDLER_KEYWORDS = FUNCTION_DISCOVERY_CONFIG.get('handler_keywords', ['handle', 'process', 'validate'])


def find_complexity_functions(functions):
    """Find functions by complexity level.
    
    Excludes test functions from complexity counts.
    Test functions are tracked separately and should not inflate complexity metrics.
    
    Note: Handler functions are NOT excluded - keyword-based detection is too broad
    and catches many utility functions that should be included in complexity metrics.
    """
    # Filter out test functions only - they should be tracked separately, not in complexity counts
    non_test_functions = [f for f in functions if not f.get('is_test', False)]
    
    moderate = [f for f in non_test_functions if f['complexity'] >= MODERATE_COMPLEXITY and f['complexity'] < HIGH_COMPLEXITY]
    high = [f for f in non_test_functions if f['complexity'] >= HIGH_COMPLEXITY and f['complexity'] < CRITICAL_COMPLEXITY]
    critical = [f for f in non_test_functions if f['complexity'] >= CRITICAL_COMPLEXITY]
    return moderate, high, critical

def find_undocumented_handlers(functions):
    return [f for f in functions if f['is_handler'] and not f['docstring'].strip()]

def find_duplicate_names(functions):
    name_map = {}
    for f in functions:
        name_map.setdefault(f['name'], []).append(f['file'])
    return {name: files for name, files in name_map.items() if len(files) > 1}


def print_dashboard(functions):
    # Print dashboard to stdout so it's visible when run directly
    print("=== AI DECISION SUPPORT DASHBOARD ===")
    moderate_complex, high_complex, critical_complex = find_complexity_functions(functions)
    undocumented_handlers = find_undocumented_handlers(functions)
    duplicates = find_duplicate_names(functions)
    
    # Output parseable metrics for extraction by operations.py
    # Use print() to ensure output is captured by subprocess (print goes to stdout)
    # These lines must appear in stdout for _extract_decision_insights to parse them
    print(f"Total functions: {len(functions)}")
    print(f"Moderate complexity: {len(moderate_complex)}")
    print(f"High complexity: {len(high_complex)}")
    print(f"Critical complexity: {len(critical_complex)}")
    print(f"Undocumented functions: {len(undocumented_handlers)}")

    # Complexity analysis with differentiated levels
    # Print to stdout so it's visible when run directly
    total_complex = len(moderate_complex) + len(high_complex) + len(critical_complex)
    if total_complex > 0:
        print(f"[COMPLEXITY] Functions needing attention: {total_complex}")
        if critical_complex:
            print(f"  [CRITICAL] Critical Complexity (>{CRITICAL_COMPLEXITY-1} nodes): {len(critical_complex)}")
            for f in critical_complex[:5]:
                print(f"    - {f['name']} (file: {Path(f['file']).name}, complexity: {f['complexity']})")
            if len(critical_complex) > 5:
                print(f"    ...and {len(critical_complex)-5} more.")
        
        if high_complex:
            print(f"  [HIGH] High Complexity ({HIGH_COMPLEXITY}-{CRITICAL_COMPLEXITY-1} nodes): {len(high_complex)}")
            for f in high_complex[:5]:
                print(f"    - {f['name']} (file: {Path(f['file']).name}, complexity: {f['complexity']})")
            if len(high_complex) > 5:
                print(f"    ...and {len(high_complex)-5} more.")
        
        if moderate_complex:
            print(f"  [MODERATE] Moderate Complexity ({MODERATE_COMPLEXITY}-{HIGH_COMPLEXITY-1} nodes): {len(moderate_complex)}")
            for f in moderate_complex[:3]:
                print(f"    - {f['name']} (file: {Path(f['file']).name}, complexity: {f['complexity']})")
            if len(moderate_complex) > 3:
                print(f"    ...and {len(moderate_complex)-3} more.")

    if undocumented_handlers:
        print(f"[DOC] Undocumented Handlers: {len(undocumented_handlers)}")
        for f in undocumented_handlers[:10]:
            print(f"  - {f['name']} (file: {Path(f['file']).name})")
        if len(undocumented_handlers) > 10:
            print(f"  ...and {len(undocumented_handlers)-10} more.")

    if duplicates:
        print(f"[DUPE] Duplicate Function Names: {len(duplicates)}")
        for name, files in list(duplicates.items())[:5]:
            print(f"  - {name}: {', '.join(Path(f).name for f in files)}")
        if len(duplicates) > 5:
            print(f"  ...and {len(duplicates)-5} more.")

    print("=== SUGGESTED NEXT STEPS ===")
    if critical_complex:
        print("- [CRITICAL] Refactor critical complexity functions immediately.")
    if high_complex:
        print("- [HIGH] Refactor high complexity functions for maintainability.")
    if moderate_complex:
        print("- [MODERATE] Review moderate complexity functions when time permits.")
    if undocumented_handlers:
        print("- Add docstrings to undocumented handler/utility functions.")
    if duplicates:
        print("- Review duplicate function names for possible consolidation or renaming.")
    if not (total_complex or undocumented_handlers or duplicates):
        print("- Codebase is in excellent shape! Proceed with confidence.")
    print("Tip: Use this dashboard before major refactoring, documentation, or architectural changes.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate decision support insights for AI collaboration')
    parser.add_argument('--include-tests', action='store_true', help='Include test files in analysis')
    parser.add_argument('--include-dev-tools', action='store_true', help='Include development_tools in analysis')
    args = parser.parse_args()
    
    logger.info("[SCAN] Gathering actionable insights for AI decision-making...")
    functions = scan_all_functions(
        include_tests=args.include_tests,
        include_dev_tools=args.include_dev_tools
    )
    print_dashboard(functions)
    
    # Return success status
    return 0

if __name__ == "__main__":
    main() 