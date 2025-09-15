#!/usr/bin/env python3
"""
decision_support.py
AI Decision Support Dashboard: actionable insights for codebase improvement and safe AI changes.
Highlights high-complexity functions, undocumented handlers, duplicate names, and suggests next steps.
"""

import sys
from pathlib import Path
import importlib.util
import ast

# Import config
sys.path.insert(0, str(Path(__file__).parent))
import config

PROJECT_ROOT = Path(config.PROJECT_ROOT)
SCAN_DIRECTORIES = config.SCAN_DIRECTORIES
MAX_COMPLEXITY = config.FUNCTION_DISCOVERY['max_complexity_threshold']
COMPLEXITY_WARNING = config.VALIDATION['complexity_warning_threshold']
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
        print(f"Error parsing {file_path}: {e}")
    return functions


def scan_all_functions():
    all_functions = []
    for scan_dir in SCAN_DIRECTORIES:
        dir_path = PROJECT_ROOT / scan_dir
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob('*.py'):
            all_functions.extend(extract_functions(str(py_file)))
    for py_file in PROJECT_ROOT.glob('*.py'):
        all_functions.extend(extract_functions(str(py_file)))
    return all_functions


def find_high_complexity(functions):
    return [f for f in functions if f['complexity'] > MAX_COMPLEXITY]

def find_undocumented_handlers(functions):
    return [f for f in functions if f['is_handler'] and not f['docstring'].strip()]

def find_duplicate_names(functions):
    name_map = {}
    for f in functions:
        name_map.setdefault(f['name'], []).append(f['file'])
    return {name: files for name, files in name_map.items() if len(files) > 1}


def print_dashboard(functions):
    print("\n=== AI DECISION SUPPORT DASHBOARD ===")
    print(f"Total functions: {len(functions)}")
    high_complex = find_high_complexity(functions)
    undocumented_handlers = find_undocumented_handlers(functions)
    duplicates = find_duplicate_names(functions)

    print(f"\n[WARN] High Complexity Functions (>{MAX_COMPLEXITY} nodes): {len(high_complex)}")
    for f in high_complex[:10]:
        print(f"  - {f['name']} (file: {Path(f['file']).name}, complexity: {f['complexity']})")
    if len(high_complex) > 10:
        print(f"  ...and {len(high_complex)-10} more.")

    print(f"\n[DOC] Undocumented Handlers: {len(undocumented_handlers)}")
    for f in undocumented_handlers[:10]:
        print(f"  - {f['name']} (file: {Path(f['file']).name})")
    if len(undocumented_handlers) > 10:
        print(f"  ...and {len(undocumented_handlers)-10} more.")

    print(f"\n[DUPE] Duplicate Function Names: {len(duplicates)}")
    for name, files in list(duplicates.items())[:5]:
        print(f"  - {name}: {', '.join(Path(f).name for f in files)}")
    if len(duplicates) > 5:
        print(f"  ...and {len(duplicates)-5} more.")

    print("\n=== SUGGESTED NEXT STEPS ===")
    if high_complex:
        print("- Refactor high-complexity functions for maintainability.")
    if undocumented_handlers:
        print("- Add docstrings to undocumented handler/utility functions.")
    if duplicates:
        print("- Review duplicate function names for possible consolidation or renaming.")
    if not (high_complex or undocumented_handlers or duplicates):
        print("- Codebase is in excellent shape! Proceed with confidence.")
    print("\nTip: Use this dashboard before major refactoring, documentation, or architectural changes.")


def main():
    print("[SCAN] Gathering actionable insights for AI decision-making...")
    functions = scan_all_functions()
    print_dashboard(functions)

if __name__ == "__main__":
    main() 