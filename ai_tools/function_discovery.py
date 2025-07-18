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


def is_special_python_method(func_name: str, complexity: int) -> bool:
    """
    Determine if a function is a special Python method that should be excluded from undocumented count.
    
    Args:
        func_name: Name of the function
        complexity: Complexity score of the function
        
    Returns:
        True if the function should be excluded from undocumented count
    """
    # Special methods that should be excluded from undocumented count
    special_methods = {
        '__new__',  # Singleton patterns
        '__post_init__',  # Dataclass post-init
        '__repr__',  # String representation
        '__str__',  # String conversion
        '__hash__',  # Hashing
        '__eq__',  # Equality comparison
        '__lt__', '__le__', '__gt__', '__ge__',  # Comparison methods
        '__len__',  # Length
        '__bool__',  # Boolean conversion
        '__call__',  # Callable
        '__getitem__', '__setitem__', '__delitem__',  # Item access
        '__iter__', '__next__',  # Iteration
        '__contains__',  # Membership testing
        '__add__', '__sub__', '__mul__', '__truediv__',  # Arithmetic
        '__radd__', '__rsub__', '__rmul__', '__rtruediv__',  # Reverse arithmetic
        '__iadd__', '__isub__', '__imul__', '__itruediv__',  # In-place arithmetic
    }
    
    # Context manager methods (these should be documented)
    context_methods = {'__enter__', '__exit__'}
    
    # Simple __init__ methods (complexity < 20) can be excluded
    if func_name == '__init__' and complexity < 20:
        return True
    
    # Exclude special methods but not context managers
    if func_name in special_methods and func_name not in context_methods:
        return True
    
    return False


def extract_decorator_documentation(decorator_list: List[ast.expr]) -> str:
    """
    Extract documentation from decorators like @handle_errors("description").
    
    Args:
        decorator_list: List of decorator AST nodes
        
    Returns:
        Documentation string from decorators, or empty string if none found
    """
    documentation = []
    
    for decorator in decorator_list:
        # Handle @handle_errors("description")
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name) and decorator.func.id == 'handle_errors':
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    documentation.append(f"@handle_errors: {decorator.args[0].value}")
            elif isinstance(decorator.func, ast.Attribute) and decorator.func.attr == 'handle_errors':
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    documentation.append(f"@handle_errors: {decorator.args[0].value}")
        
        # Handle @error_handler("description")
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name) and decorator.func.id == 'error_handler':
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    documentation.append(f"@error_handler: {decorator.args[0].value}")
            elif isinstance(decorator.func, ast.Attribute) and decorator.func.attr == 'error_handler':
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    documentation.append(f"@error_handler: {decorator.args[0].value}")
    
    return "; ".join(documentation)


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
                
                # Get traditional docstring
                traditional_docstring = ast.get_docstring(node) or ""
                
                # Get decorator-based documentation
                decorator_docstring = extract_decorator_documentation(node.decorator_list)
                
                # Combine both types of documentation
                combined_docstring = traditional_docstring
                if decorator_docstring:
                    if combined_docstring:
                        combined_docstring += f" | {decorator_docstring}"
                    else:
                        combined_docstring = decorator_docstring
                
                decorators = [
                    d.id if isinstance(d, ast.Name) else d.func.id if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) else str(d)
                    for d in node.decorator_list
                ]
                complexity = len(list(ast.walk(node)))
                is_handler = any(k in name.lower() for k in HANDLER_KEYWORDS)
                is_test = any(k in name.lower() for k in TEST_KEYWORDS)
                is_special = is_special_python_method(name, complexity)
                
                functions.append({
                    'name': name,
                    'args': args,
                    'docstring': combined_docstring,
                    'traditional_docstring': traditional_docstring,
                    'decorator_docstring': decorator_docstring,
                    'decorators': decorators,
                    'complexity': complexity,
                    'is_handler': is_handler,
                    'is_test': is_test,
                    'is_special': is_special,
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
        'special_methods': [],  # New category for special methods
        'other': []
    }
    for func in functions:
        if func['is_test']:
            categories['tests'].append(func)
        elif func['is_handler']:
            categories['handlers'].append(func)
        elif func['complexity'] > MAX_COMPLEXITY:
            categories['complex'].append(func)
        elif func['is_special']:
            # Special methods go to their own category
            categories['special_methods'].append(func)
        elif not func['docstring'].strip():
            # Only count as undocumented if not special and no documentation (traditional or decorator)
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
    
    # Add summary of special methods excluded from undocumented count
    special_count = len(categories.get('special_methods', []))
    if special_count > 0:
        print(f"\nNote: {special_count} special Python methods excluded from undocumented count")


def main():
    print("[SCAN] Scanning for all functions...")
    all_functions = scan_all_functions()
    print(f"Found {len(all_functions)} functions.")
    categories = categorize_functions(all_functions)
    print_summary(categories)
    print("\nTip: Use this output to quickly find handlers, tests, complex, or undocumented functions.")

if __name__ == "__main__":
    main() 