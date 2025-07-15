#!/usr/bin/env python3
"""
function_discovery.py
Enhanced function search and relationship mapping for AI-optimized development.
Finds all functions, categorizes them (handler, utility, test, etc.), and shows relationships.
"""

import os
import ast
from pathlib import Path
from typing import Dict, List, Set
import importlib.util
import sys

# Import config
sys.path.insert(0, str(Path(__file__).parent))
import config

PROJECT_ROOT = Path(config.PROJECT_ROOT)
SCAN_DIRECTORIES = config.SCAN_DIRECTORIES
HANDLER_KEYWORDS = config.FUNCTION_DISCOVERY['handler_keywords']
TEST_KEYWORDS = config.FUNCTION_DISCOVERY['test_keywords']
MAX_COMPLEXITY = config.FUNCTION_DISCOVERY['max_complexity_threshold']


def extract_functions(file_path: str) -> List[Dict]:
    """Extract all function definitions from a Python file."""
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
                decorators = [
                    d.id if isinstance(d, ast.Name) else d.func.id if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) else str(d)
                    for d in node.decorator_list
                ]
                complexity = len(list(ast.walk(node)))
                is_handler = any(k in name.lower() for k in HANDLER_KEYWORDS)
                is_test = any(k in name.lower() for k in TEST_KEYWORDS)
                functions.append({
                    'name': name,
                    'args': args,
                    'docstring': docstring,
                    'decorators': decorators,
                    'complexity': complexity,
                    'is_handler': is_handler,
                    'is_test': is_test,
                    'file': file_path
                })
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    return functions


def scan_all_functions() -> List[Dict]:
    """Scan all Python files in SCAN_DIRECTORIES and extract functions."""
    all_functions = []
    for scan_dir in SCAN_DIRECTORIES:
        dir_path = PROJECT_ROOT / scan_dir
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob('*.py'):
            all_functions.extend(extract_functions(str(py_file)))
    # Also scan root directory
    for py_file in PROJECT_ROOT.glob('*.py'):
        all_functions.extend(extract_functions(str(py_file)))
    return all_functions


def categorize_functions(functions: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize functions by type for easy discovery."""
    categories = {
        'handlers': [],
        'tests': [],
        'complex': [],
        'undocumented': [],
        'other': []
    }
    for func in functions:
        if func['is_test']:
            categories['tests'].append(func)
        elif func['is_handler']:
            categories['handlers'].append(func)
        elif func['complexity'] > MAX_COMPLEXITY:
            categories['complex'].append(func)
        elif not func['docstring'].strip():
            categories['undocumented'].append(func)
        else:
            categories['other'].append(func)
    return categories


def print_summary(categories: Dict[str, List[Dict]]):
    print("\n=== FUNCTION DISCOVERY SUMMARY ===")
    for cat, funcs in categories.items():
        print(f"\n{cat.upper()} ({len(funcs)}):")
        for func in funcs[:10]:
            print(f"  - {func['name']} (file: {Path(func['file']).name}, complexity: {func['complexity']})")
        if len(funcs) > 10:
            print(f"  ...and {len(funcs)-10} more.")


def main():
    print("[SCAN] Scanning for all functions...")
    all_functions = scan_all_functions()
    print(f"Found {len(all_functions)} functions.")
    categories = categorize_functions(all_functions)
    print_summary(categories)
    print("\nTip: Use this output to quickly find handlers, tests, complex, or undocumented functions.")

if __name__ == "__main__":
    main() 