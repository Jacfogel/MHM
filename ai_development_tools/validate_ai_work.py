#!/usr/bin/env python3
"""
Validation script for AI-generated work.
Helps verify completeness and accuracy before presenting to user.
"""

import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json
import config

def validate_documentation_completeness(doc_file: str, code_files: List[str]) -> Dict:
    """Validate that documentation covers all relevant code."""
    results = {
        'file_exists': False,
        'coverage': 0.0,
        'missing_items': [],
        'extra_items': [],
        'warnings': []
    }
    
    # Check if documentation file exists
    doc_path = Path(doc_file)
    results['file_exists'] = doc_path.exists()
    
    if not results['file_exists']:
        results['warnings'].append(f"Documentation file {doc_file} does not exist")
        return results
    
    # Read documentation content
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            doc_content = f.read()
    except Exception as e:
        results['warnings'].append(f"Error reading {doc_file}: {e}")
        return results
    
    # Extract mentioned items from documentation
    mentioned_items = set()
    
    # Look for function/class names in backticks
    function_matches = re.findall(r'`([a-zA-Z_][a-zA-Z0-9_]*)`', doc_content)
    mentioned_items.update(function_matches)
    
    # Look for file paths
    file_matches = re.findall(r'`([^`]+\.py)`', doc_content)
    mentioned_items.update(file_matches)
    
    # Extract actual items from code files
    actual_items = set()
    for code_file in code_files:
        code_path = Path(code_file)
        if code_path.exists():
            try:
                with open(code_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Extract function names
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        actual_items.add(node.name)
                    elif isinstance(node, ast.ClassDef):
                        actual_items.add(node.name)
                
                # Add file name
                actual_items.add(code_path.name)
                
            except Exception as e:
                results['warnings'].append(f"Error parsing {code_file}: {e}")
    
    # Calculate coverage
    if actual_items:
        covered_items = mentioned_items.intersection(actual_items)
        results['coverage'] = len(covered_items) / len(actual_items) * 100
        results['missing_items'] = list(actual_items - mentioned_items)
        results['extra_items'] = list(mentioned_items - actual_items)
    
    return results

def validate_code_consistency(changed_files: List[str]) -> Dict:
    """Validate that code changes are consistent across files."""
    results = {
        'import_consistency': True,
        'naming_consistency': True,
        'function_signatures': [],
        'warnings': []
    }
    
    # Check for consistent imports
    import_patterns = {}
    for file_path in changed_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")
            
            import_patterns[file_path] = imports
            
            # Extract function signatures
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args]
                    results['function_signatures'].append({
                        'file': file_path,
                        'name': node.name,
                        'args': args
                    })
                    
        except Exception as e:
            results['warnings'].append(f"Error parsing {file_path}: {e}")
    
    # Check for naming consistency
    function_names = {}
    for sig in results['function_signatures']:
        name = sig['name']
        if name not in function_names:
            function_names[name] = []
        function_names[name].append(sig['file'])
    
    # Find duplicate function names
    duplicates = {name: files for name, files in function_names.items() if len(files) > 1}
    if duplicates:
        results['naming_consistency'] = False
        results['warnings'].append(f"Duplicate function names found: {duplicates}")
    
    return results

def validate_file_structure(created_files: List[str], modified_files: List[str]) -> Dict:
    """Validate that file structure changes are appropriate."""
    results = {
        'appropriate_locations': True,
        'naming_conventions': True,
        'warnings': []
    }
    
    # Check file locations
    for file_path in created_files + modified_files:
        path = Path(file_path)
        
        # Check if file is in appropriate directory
        if path.suffix == '.py':
            if 'test' in path.name.lower() and 'tests' not in str(path):
                results['warnings'].append(f"Test file {file_path} not in tests/ directory")
                results['appropriate_locations'] = False
            
            if path.name.startswith('ui_') and 'ui' not in str(path):
                results['warnings'].append(f"UI file {file_path} not in ui/ directory")
                results['appropriate_locations'] = False
    
    # Check naming conventions
    for file_path in created_files + modified_files:
        path = Path(file_path)
        
        if path.suffix == '.py':
            # Check for snake_case
            if '_' not in path.stem and path.stem.lower() != path.stem:
                results['warnings'].append(f"Python file {file_path} should use snake_case")
                results['naming_conventions'] = False
    
    return results

def generate_validation_report(validation_type: str, **kwargs) -> str:
    """Generate a comprehensive validation report."""
    report = []
    report.append(f"Validation Type: {validation_type}")
    report.append("")
    
    if validation_type == "documentation":
        results = validate_documentation_completeness(
            kwargs.get('doc_file', ''),
            kwargs.get('code_files', [])
        )
        
        report.append(f"Documentation File: {kwargs.get('doc_file', 'N/A')}")
        report.append(f"File Exists: {results['file_exists']}")
        report.append(f"Coverage: {results['coverage']:.1f}%")
        
        if results['missing_items']:
            report.append(f"Missing Items: {len(results['missing_items'])}")
            for item in results['missing_items'][:5]:
                report.append(f"   - {item}")
        
        if results['extra_items']:
            report.append(f"Extra Items: {len(results['extra_items'])}")
            for item in results['extra_items'][:5]:
                report.append(f"   - {item}")
    
    elif validation_type == "code_consistency":
        results = validate_code_consistency(kwargs.get('changed_files', []))
        
        report.append(f"Code Consistency Check")
        report.append(f"Import Consistency: {results['import_consistency']}")
        report.append(f"Naming Consistency: {results['naming_consistency']}")
        report.append(f"Functions Found: {len(results['function_signatures'])}")
        
        if results['warnings']:
            report.append(f"Warnings: {len(results['warnings'])}")
            for warning in results['warnings'][:3]:
                report.append(f"   - {warning}")
    
    elif validation_type == "file_structure":
        results = validate_file_structure(
            kwargs.get('created_files', []),
            kwargs.get('modified_files', [])
        )
        
        report.append(f"File Structure Validation")
        report.append(f"Appropriate Locations: {results['appropriate_locations']}")
        report.append(f"Naming Conventions: {results['naming_conventions']}")
        
        if results['warnings']:
            report.append(f"Warnings: {len(results['warnings'])}")
            for warning in results['warnings'][:3]:
                report.append(f"   - {warning}")
    
    # Overall assessment
    report.append("")
    report.append("OVERALL ASSESSMENT:")
    
    if validation_type == "documentation":
        if results['coverage'] >= 80:
            report.append("GOOD - Documentation covers most items")
        elif results['coverage'] >= 50:
            report.append("FAIR - Documentation needs improvement")
        else:
            report.append("POOR - Documentation is incomplete")
    
    elif validation_type == "code_consistency":
        if results['naming_consistency'] and not results['warnings']:
            report.append("GOOD - Code is consistent")
        else:
            report.append("NEEDS ATTENTION - Inconsistencies found")
    
    elif validation_type == "file_structure":
        if results['appropriate_locations'] and results['naming_conventions']:
            report.append("GOOD - File structure is appropriate")
        else:
            report.append("NEEDS ATTENTION - File structure issues found")
    
    return "\n".join(report)

def validate_ai_work(work_type: str, **kwargs) -> str:
    """Main validation function for AI work."""
    if work_type == "documentation":
        return generate_validation_report("documentation", **kwargs)
    elif work_type == "code_changes":
        return generate_validation_report("code_consistency", **kwargs)
    elif work_type == "file_creation":
        return generate_validation_report("file_structure", **kwargs)
    else:
        return "Unknown validation type"

if __name__ == "__main__":
    # Example usage
    print(validate_ai_work("documentation", 
                          doc_file="README.md", 
                          code_files=["core/config.py", "core/service.py"])) 