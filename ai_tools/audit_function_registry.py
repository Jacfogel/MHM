#!/usr/bin/env python3
"""
Audit script to verify FUNCTION_REGISTRY.md completeness and accuracy.
Scans all .py files and extracts function information for comparison.
"""

import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json

def extract_functions_from_file(file_path: str) -> List[Dict]:
    """Extract all function definitions from a Python file."""
    functions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get function signature
                args = []
                for arg in node.args.args:
                    args.append(arg.arg)
                
                # Get decorators
                decorators = []
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        decorators.append(decorator.id)
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            decorators.append(decorator.func.id)
                
                # Get docstring
                docstring = ast.get_docstring(node) or ""
                
                # Check if it's a test function
                is_test = node.name.startswith('test_') or 'test' in node.name.lower()
                
                # Check if it's a main function
                is_main = node.name == 'main' or node.name == '__main__'
                
                # Get function complexity (rough estimate)
                complexity = len(list(ast.walk(node)))
                
                # Check if it's a handler/utility function
                is_handler = any(keyword in node.name.lower() for keyword in ['handle', 'process', 'validate', 'check', 'get', 'set', 'save', 'load'])
                
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'args': args,
                    'decorators': decorators,
                    'docstring': docstring,
                    'is_test': is_test,
                    'is_main': is_main,
                    'complexity': complexity,
                    'has_docstring': bool(docstring.strip()),
                    'is_handler': is_handler,
                    'arg_count': len(args)
                })
                
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return functions

def extract_classes_from_file(file_path: str) -> List[Dict]:
    """Extract all class definitions from a Python file."""
    classes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Get class methods
                methods = []
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        methods.append({
                            'name': child.name,
                            'line': child.lineno,
                            'args': [arg.arg for arg in child.args.args],
                            'decorators': [d.id if isinstance(d, ast.Name) else 
                                         d.func.id if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) else str(d)
                                         for d in child.decorator_list],
                            'docstring': ast.get_docstring(child)
                        })
                
                classes.append({
                    'name': node.name,
                    'line': node.lineno,
                    'methods': methods,
                    'docstring': ast.get_docstring(node)
                })
                
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return classes

def scan_all_python_files() -> Dict[str, Dict]:
    """Scan all Python files in the project and extract function/class information."""
    project_root = Path(__file__).parent.parent
    results = {}
    
    # Directories to scan
    scan_dirs = ['core', 'bot', 'ui', 'user', 'tasks', 'scripts', 'tests']
    
    for scan_dir in scan_dirs:
        dir_path = project_root / scan_dir
        if not dir_path.exists():
            continue
            
        for py_file in dir_path.rglob('*.py'):
            relative_path = py_file.relative_to(project_root)
            file_key = str(relative_path).replace('\\', '/')
            
            functions = extract_functions_from_file(str(py_file))
            classes = extract_classes_from_file(str(py_file))
            
            results[file_key] = {
                'functions': functions,
                'classes': classes,
                'total_functions': len(functions),
                'total_classes': len(classes)
            }
    
    # Also scan root directory for .py files
    for py_file in project_root.glob('*.py'):
        if py_file.name != 'audit_function_registry.py':  # Skip this script
            file_key = py_file.name
            
            functions = extract_functions_from_file(str(py_file))
            classes = extract_classes_from_file(str(py_file))
            
            results[file_key] = {
                'functions': functions,
                'classes': classes,
                'total_functions': len(functions),
                'total_classes': len(classes)
            }
    
    return results

def parse_function_registry() -> Dict[str, List[str]]:
    """Parse the existing FUNCTION_REGISTRY.md to extract documented functions."""
    registry_path = Path(__file__).parent.parent / 'FUNCTION_REGISTRY.md'
    documented = {}
    
    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract file sections and their functions (new format)
        # Pattern: #### `filename.py` followed by functions section
        sections = re.findall(r'#### `([^`]+)`\n(.*?)(?=#### `|$)', content, re.DOTALL)
        
        for file_path, section_content in sections:
            # Extract function names from the functions section
            # Look for the "Functions:" section and extract function names
            funcs_section = re.search(r'\*\*Functions:\*\*\n(.*?)(?=\*\*Classes:\*\*|$)', section_content, re.DOTALL)
            if funcs_section:
                # Extract function names (lines starting with "- ✅" or "- ❌" followed by function name)
                function_matches = re.findall(r'- [✅❌] `([^`]+)\([^)]*\)`', funcs_section.group(1))
                documented[file_path] = function_matches
            else:
                documented[file_path] = []
            
    except Exception as e:
        print(f"Error parsing FUNCTION_REGISTRY.md: {e}")
    
    return documented

def generate_audit_report():
    """Generate a comprehensive audit report."""
    print("[SCAN] Scanning all Python files...")
    actual_functions = scan_all_python_files()
    
    print("[DOC] Parsing FUNCTION_REGISTRY.md...")
    documented_functions = parse_function_registry()
    
    print("\n" + "="*80)
    print("FUNCTION REGISTRY AUDIT REPORT")
    print("="*80)
    
    # Statistics
    total_files = len(actual_functions)
    total_actual_functions = sum(data['total_functions'] for data in actual_functions.values())
    total_actual_classes = sum(data['total_classes'] for data in actual_functions.values())
    total_documented_functions = sum(len(funcs) for funcs in documented_functions.values())
    
    print(f"\n[STATS] OVERALL STATISTICS:")
    print(f"   Files scanned: {total_files}")
    print(f"   Functions found: {total_actual_functions}")
    print(f"   Classes found: {total_actual_classes}")
    print(f"   Functions documented: {total_documented_functions}")
    print(f"   Coverage: {(total_documented_functions/total_actual_functions*100):.1f}%" if total_actual_functions > 0 else "   Coverage: N/A")
    
    # Missing functions
    print(f"\n[MISS] MISSING FROM REGISTRY:")
    missing_count = 0
    for file_path, data in actual_functions.items():
        if file_path not in documented_functions:
            print(f"   [DIR] {file_path} - ENTIRE FILE MISSING")
            missing_count += data['total_functions']
        else:
            documented_funcs = set(documented_functions[file_path])
            actual_funcs = {f['name'] for f in data['functions']}
            missing_funcs = actual_funcs - documented_funcs
            
            if missing_funcs:
                print(f"   [FILE] {file_path}:")
                for func in sorted(missing_funcs):
                    print(f"      - {func}")
                    missing_count += 1
    
    print(f"\n   Total missing functions: {missing_count}")
    
    # Extra functions (documented but not found)
    print(f"\n[EXTRA] EXTRA IN REGISTRY (not found in files):")
    extra_count = 0
    for file_path, documented_funcs in documented_functions.items():
        if file_path not in actual_functions:
            print(f"   [FILE] {file_path} - FILE NOT FOUND")
            extra_count += len(documented_funcs)
        else:
            documented_funcs_set = set(documented_funcs)
            actual_funcs = {f['name'] for f in actual_functions[file_path]['functions']}
            extra_funcs = documented_funcs_set - actual_funcs
            
            if extra_funcs:
                print(f"   [FILE] {file_path}:")
                for func in sorted(extra_funcs):
                    print(f"      - {func}")
                    extra_count += 1
    
    print(f"\n   Total extra functions: {extra_count}")
    
    # Function analysis for decision-making
    print(f"\n[ANALYSIS] FUNCTION ANALYSIS FOR DECISION-MAKING:")
    
    # Find complex functions that might need attention
    complex_functions = []
    for file_path, data in actual_functions.items():
        for func in data['functions']:
            if func['complexity'] > 50 and not func['is_test']:  # High complexity, not tests
                complex_functions.append({
                    'file': file_path,
                    'name': func['name'],
                    'complexity': func['complexity'],
                    'has_docstring': func['has_docstring']
                })
    
    if complex_functions:
        print(f"   [WARN] HIGH COMPLEXITY FUNCTIONS (may need refactoring):")
        for func in sorted(complex_functions, key=lambda x: x['complexity'], reverse=True)[:10]:
            doc_status = "[DOC]" if func['has_docstring'] else "[NO DOC]"
            print(f"      {doc_status} {func['file']}::{func['name']} (complexity: {func['complexity']})")
    
    # Find functions without docstrings
    undocumented_functions = []
    for file_path, data in actual_functions.items():
        for func in data['functions']:
            if not func['has_docstring'] and not func['is_test'] and not func['is_main']:
                undocumented_functions.append({
                    'file': file_path,
                    'name': func['name'],
                    'is_handler': func['is_handler']
                })
    
    if undocumented_functions:
        print(f"   [DOC] UNDOCUMENTED FUNCTIONS (need docstrings):")
        handlers = [f for f in undocumented_functions if f['is_handler']]
        others = [f for f in undocumented_functions if not f['is_handler']]
        
        if handlers:
            print(f"      [HANDLER] Handlers/Utilities ({len(handlers)}):")
            for func in sorted(handlers, key=lambda x: x['name'])[:5]:
                print(f"         - {func['file']}::{func['name']}")
        
        if others:
            print(f"      [OTHER] Other functions ({len(others)}):")
            for func in sorted(others, key=lambda x: x['name'])[:5]:
                print(f"         - {func['file']}::{func['name']}")
    
    # Find potential duplicate functions
    function_names = {}
    for file_path, data in actual_functions.items():
        for func in data['functions']:
            if func['name'] not in function_names:
                function_names[func['name']] = []
            function_names[func['name']].append(file_path)
    
    duplicates = {name: files for name, files in function_names.items() if len(files) > 1}
    if duplicates:
        print(f"   [DUPE] POTENTIAL DUPLICATE FUNCTION NAMES:")
        for name, files in sorted(duplicates.items())[:5]:
            print(f"      '{name}' found in: {', '.join(files)}")
    
    # Detailed breakdown by directory
    print(f"\n[DIR] BREAKDOWN BY DIRECTORY:")
    dir_stats = {}
    for file_path, data in actual_functions.items():
        dir_name = file_path.split('/')[-2] if '/' in file_path else 'root'
        if dir_name not in dir_stats:
            dir_stats[dir_name] = {'files': 0, 'functions': 0, 'classes': 0}
        dir_stats[dir_name]['files'] += 1
        dir_stats[dir_name]['functions'] += data['total_functions']
        dir_stats[dir_name]['classes'] += data['total_classes']
    
    for dir_name, stats in sorted(dir_stats.items()):
        print(f"   {dir_name}/: {stats['files']} files, {stats['functions']} functions, {stats['classes']} classes")
    
    # Generate updated registry content
    print(f"\n[GEN] GENERATING UPDATED REGISTRY SECTIONS...")
    generate_updated_registry_sections(actual_functions)

def generate_updated_registry_sections(actual_functions: Dict[str, Dict]):
    """Generate updated registry sections for missing files."""
    print("\n" + "="*80)
    print("UPDATED REGISTRY SECTIONS TO ADD:")
    print("="*80)
    
    for file_path, data in sorted(actual_functions.items()):
        if data['functions'] or data['classes']:
            print(f"\n### {file_path}")
            
            # Functions
            if data['functions']:
                print("**Functions:**")
                for func in data['functions']:
                    args_str = ', '.join(func['args'])
                    print(f"- `{func['name']}({args_str})` - {func['docstring'] or 'No description'}")
            
            # Classes
            if data['classes']:
                print("**Classes:**")
                for cls in data['classes']:
                    print(f"- `{cls['name']}` - {cls['docstring'] or 'No description'}")
                    for method in cls['methods']:
                        args_str = ', '.join(method['args'])
                        print(f"  - `{cls['name']}.{method['name']}({args_str})` - {method['docstring'] or 'No description'}")

if __name__ == "__main__":
    generate_audit_report() 