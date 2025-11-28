#!/usr/bin/env python3
# TOOL_TIER: supporting
# TOOL_PORTABILITY: mhm-specific

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
    from .services.standard_exclusions import should_exclude_file
except ImportError:
    import config
    from development_tools.services.standard_exclusions import should_exclude_file

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

PROJECT_ROOT = Path(config.PROJECT_ROOT)
SCAN_DIRECTORIES = config.SCAN_DIRECTORIES
MODERATE_COMPLEXITY = config.FUNCTION_DISCOVERY['moderate_complexity_threshold']
HIGH_COMPLEXITY = config.FUNCTION_DISCOVERY['high_complexity_threshold']
CRITICAL_COMPLEXITY = config.FUNCTION_DISCOVERY['critical_complexity_threshold']
HANDLER_KEYWORDS = config.FUNCTION_DISCOVERY['handler_keywords']


def extract_functions(file_path: str):
    functions = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                name = node.name
                args = [arg.arg for arg in node.args.args]
                docstring = ast.get_docstring(node) or ""
                complexity = len(list(ast.walk(node)))
                is_handler = any(k in name.lower() for k in HANDLER_KEYWORDS)
                functions.append({
                    'name': name,
                    'args': args,
                    'docstring': docstring,
                    'complexity': complexity,
                    'is_handler': is_handler,
                    'file': file_path
                })
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
    return functions


def scan_all_functions(include_tests: bool = False, include_dev_tools: bool = False):
    all_functions = []
    
    # Determine context based on configuration
    if include_tests and include_dev_tools:
        context = 'development'  # Include everything
    elif include_tests or include_dev_tools:
        context = 'development'  # More permissive
    else:
        context = 'production'   # Exclude tests and dev tools
    
    # Use all directories and let context-based exclusions handle filtering
    scan_dirs = list(SCAN_DIRECTORIES) + ['tests', 'development_tools']
    
    for scan_dir in scan_dirs:
        dir_path = PROJECT_ROOT / scan_dir
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob('*.py'):
            # Use context-based exclusions
            if not should_exclude_file(str(py_file), 'analysis', context):
                all_functions.extend(extract_functions(str(py_file)))
    
    for py_file in PROJECT_ROOT.glob('*.py'):
        # Use context-based exclusions
        if not should_exclude_file(str(py_file), 'analysis', context):
            all_functions.extend(extract_functions(str(py_file)))
    
    return all_functions


def find_complexity_functions(functions):
    """Find functions by complexity level."""
    moderate = [f for f in functions if f['complexity'] >= MODERATE_COMPLEXITY and f['complexity'] < HIGH_COMPLEXITY]
    high = [f for f in functions if f['complexity'] >= HIGH_COMPLEXITY and f['complexity'] < CRITICAL_COMPLEXITY]
    critical = [f for f in functions if f['complexity'] >= CRITICAL_COMPLEXITY]
    return moderate, high, critical

def find_undocumented_handlers(functions):
    return [f for f in functions if f['is_handler'] and not f['docstring'].strip()]

def find_duplicate_names(functions):
    name_map = {}
    for f in functions:
        name_map.setdefault(f['name'], []).append(f['file'])
    return {name: files for name, files in name_map.items() if len(files) > 1}


def print_dashboard(functions):
    logger.info("=== AI DECISION SUPPORT DASHBOARD ===")
    logger.info(f"Total functions: {len(functions)}")
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
    total_complex = len(moderate_complex) + len(high_complex) + len(critical_complex)
    if total_complex > 0:
        logger.warning(f"[COMPLEXITY] Functions needing attention: {total_complex}")
        if critical_complex:
            logger.warning(f"  [CRITICAL] Critical Complexity (>{CRITICAL_COMPLEXITY-1} nodes): {len(critical_complex)}")
            for f in critical_complex[:5]:
                logger.warning(f"    - {f['name']} (file: {Path(f['file']).name}, complexity: {f['complexity']})")
            if len(critical_complex) > 5:
                logger.warning(f"    ...and {len(critical_complex)-5} more.")
        
        if high_complex:
            logger.warning(f"  [HIGH] High Complexity ({HIGH_COMPLEXITY}-{CRITICAL_COMPLEXITY-1} nodes): {len(high_complex)}")
            for f in high_complex[:5]:
                logger.warning(f"    - {f['name']} (file: {Path(f['file']).name}, complexity: {f['complexity']})")
            if len(high_complex) > 5:
                logger.warning(f"    ...and {len(high_complex)-5} more.")
        
        if moderate_complex:
            logger.info(f"  [MODERATE] Moderate Complexity ({MODERATE_COMPLEXITY}-{HIGH_COMPLEXITY-1} nodes): {len(moderate_complex)}")
            for f in moderate_complex[:3]:
                logger.info(f"    - {f['name']} (file: {Path(f['file']).name}, complexity: {f['complexity']})")
            if len(moderate_complex) > 3:
                logger.info(f"    ...and {len(moderate_complex)-3} more.")

    if undocumented_handlers:
        logger.warning(f"[DOC] Undocumented Handlers: {len(undocumented_handlers)}")
        for f in undocumented_handlers[:10]:
            logger.warning(f"  - {f['name']} (file: {Path(f['file']).name})")
        if len(undocumented_handlers) > 10:
            logger.warning(f"  ...and {len(undocumented_handlers)-10} more.")

    if duplicates:
        logger.warning(f"[DUPE] Duplicate Function Names: {len(duplicates)}")
        for name, files in list(duplicates.items())[:5]:
            logger.warning(f"  - {name}: {', '.join(Path(f).name for f in files)}")
        if len(duplicates) > 5:
            logger.warning(f"  ...and {len(duplicates)-5} more.")

    logger.info("=== SUGGESTED NEXT STEPS ===")
    if critical_complex:
        logger.warning("- [CRITICAL] Refactor critical complexity functions immediately.")
    if high_complex:
        logger.warning("- [HIGH] Refactor high complexity functions for maintainability.")
    if moderate_complex:
        logger.info("- [MODERATE] Review moderate complexity functions when time permits.")
    if undocumented_handlers:
        logger.warning("- Add docstrings to undocumented handler/utility functions.")
    if duplicates:
        logger.warning("- Review duplicate function names for possible consolidation or renaming.")
    if not (total_complex or undocumented_handlers or duplicates):
        logger.info("- Codebase is in excellent shape! Proceed with confidence.")
    logger.info("Tip: Use this dashboard before major refactoring, documentation, or architectural changes.")


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
