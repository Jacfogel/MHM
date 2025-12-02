#!/usr/bin/env python3
# TOOL_TIER: core

"""
analyze_function_patterns.py
Analyzes function patterns in the codebase for AI consumption.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
try:
    from .. import config  # Go up one level from functions/ to development_tools/
except ImportError:
    from development_tools import config

# Ensure external config is loaded
config.load_external_config()

logger = get_component_logger("development_tools")


def analyze_function_patterns(actual_functions: Dict[str, Dict]) -> Dict[str, Any]:
    """Analyze function patterns for AI consumption - enhanced with more pattern detection."""
    patterns = {
        'handlers': [],
        'managers': [],
        'factories': [],
        'context_managers': [],
        'widgets': [],
        'dialogs': [],
        'validators': [],
        'decorators': [],
        'schemas': [],
        'entry_points': [],
        'data_access': [],
        'communication': [],
        'error_handlers': [],
        'schedulers': []
    }
    
    for file_path, data in actual_functions.items():
        file_lower = file_path.lower()
        
        # Analyze classes for patterns
        for cls in data['classes']:
            class_name = cls['name']
            methods = [m['name'] for m in cls['methods']]
            decorators = [d for d in cls.get('decorators', [])]
            
            # Handler pattern
            if class_name.endswith('Handler') and ('can_handle' in methods or 'handle' in methods):
                patterns['handlers'].append({
                    'file': file_path,
                    'class': class_name,
                    'methods': len(methods),
                    'has_doc': cls.get('has_docstring', False)
                })
            
            # Manager pattern
            elif class_name.endswith('Manager') or 'Manager' in class_name:
                if any(m in methods for m in ['start', 'stop', 'initialize', 'shutdown', 'get_instance']):
                    patterns['managers'].append({
                        'file': file_path,
                        'class': class_name,
                        'methods': len(methods),
                        'has_doc': cls.get('has_docstring', False)
                    })
            
            # Factory pattern
            elif 'Factory' in class_name:
                if any(m in methods for m in ['create', 'register', 'get', 'build']):
                    patterns['factories'].append({
                        'file': file_path,
                        'class': class_name,
                        'methods': len(methods),
                        'has_doc': cls.get('has_docstring', False)
                    })
            
            # Widget pattern
            elif 'Widget' in class_name or file_lower.endswith('_widget.py'):
                patterns['widgets'].append({
                    'file': file_path,
                    'class': class_name,
                    'methods': len(methods),
                    'has_doc': cls.get('has_docstring', False)
                })
            
            # Dialog pattern
            elif 'Dialog' in class_name or file_lower.endswith('_dialog.py'):
                patterns['dialogs'].append({
                    'file': file_path,
                    'class': class_name,
                    'methods': len(methods),
                    'has_doc': cls.get('has_docstring', False)
                })
            
            # Validator pattern
            elif 'Validator' in class_name or 'validate' in class_name.lower():
                if any('validate' in m.lower() for m in methods):
                    patterns['validators'].append({
                        'file': file_path,
                        'class': class_name,
                        'methods': len(methods),
                        'has_doc': cls.get('has_docstring', False)
                    })
            
            # Schema pattern (Pydantic models)
            elif 'Schema' in class_name or 'Model' in class_name:
                if any(d in decorators for d in ['BaseModel', 'pydantic']):
                    patterns['schemas'].append({
                        'file': file_path,
                        'class': class_name,
                        'methods': len(methods),
                        'has_doc': cls.get('has_docstring', False)
                    })
            
            # Context manager pattern
            if '__enter__' in methods and '__exit__' in methods:
                patterns['context_managers'].append({
                    'file': file_path,
                    'class': class_name,
                    'methods': len(methods),
                    'has_doc': cls.get('has_docstring', False)
                })
        
        # Analyze functions for patterns
        for func in data['functions']:
            func_name = func['name']
            func_lower = func_name.lower()
            decorators = func.get('decorators', [])
            
            # Entry points
            if func_name in ['handle_message', 'generate_response', 'main', '__init__']:
                patterns['entry_points'].append({
                    'file': file_path,
                    'function': func_name,
                    'has_doc': func.get('has_docstring', False)
                })
            
            # Data access
            elif any(keyword in func_lower for keyword in ['get_user', 'save_user', 'load_user', 'save_', 'load_']):
                if 'test' not in file_lower:
                    patterns['data_access'].append({
                        'file': file_path,
                        'function': func_name,
                        'has_doc': func.get('has_docstring', False)
                    })
            
            # Communication
            elif any(keyword in func_lower for keyword in ['send_', 'receive_', 'connect_', 'disconnect_', 'message']):
                if 'test' not in file_lower:
                    patterns['communication'].append({
                        'file': file_path,
                        'function': func_name,
                        'has_doc': func.get('has_docstring', False)
                    })
            
            # Error handlers
            elif 'handle_errors' in func_lower or 'handle_error' in func_lower:
                if 'test' not in file_lower:
                    patterns['error_handlers'].append({
                        'file': file_path,
                        'function': func_name,
                        'has_doc': func.get('has_docstring', False)
                    })
            
            # Schedulers
            elif 'schedule' in func_lower and ('add' in func_lower or 'create' in func_lower or 'run' in func_lower):
                if 'test' not in file_lower:
                    patterns['schedulers'].append({
                        'file': file_path,
                        'function': func_name,
                        'has_doc': func.get('has_docstring', False)
                    })
            
            # Decorators - check if function is used as a decorator
            # Look for functions that are commonly used as decorators
            if func_name in ['handle_errors', 'handle_error', 'log_execution']:
                patterns['decorators'].append({
                    'file': file_path,
                    'function': func_name,
                    'has_doc': func.get('has_docstring', False)
                })
    
    return patterns


def main():
    """Main entry point for pattern analysis."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Analyze function patterns in the codebase')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--input', type=str, help='Input file path (JSON format with function data)')
    
    args = parser.parse_args()
    
    # Load function data
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            actual_functions = json.load(f)
    else:
        # Import from analyze_functions to get discovery results
        from .analyze_functions import scan_all_python_files
        actual_functions = scan_all_python_files()
    
    # Analyze patterns
    patterns = analyze_function_patterns(actual_functions)
    
    if args.json:
        print(json.dumps(patterns, indent=2))
    else:
        logger.info("Function Patterns Analysis:")
        for pattern_type, items in patterns.items():
            if items:
                logger.info(f"  {pattern_type}: {len(items)} found")
                for item in items[:5]:  # Show first 5
                    if 'class' in item:
                        logger.info(f"    - {item['class']} ({item['file']})")
                    else:
                        logger.info(f"    - {item['function']} ({item['file']})")
                if len(items) > 5:
                    logger.info(f"    ... and {len(items) - 5} more")


if __name__ == "__main__":
    main()

