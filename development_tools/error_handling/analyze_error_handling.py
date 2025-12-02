#!/usr/bin/env python3
# TOOL_TIER: core

"""
Error Handling Coverage Analysis Tool

This script analyzes error handling patterns across the codebase to identify:
- Functions with proper error handling
- Functions missing error handling
- Error handling patterns and consistency
- Coverage of error handling decorators and utilities
"""

import ast
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import re

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
try:
    from ..shared.standard_exclusions import should_exclude_file
    from .. import config  # Go up one level from error_handling/ to development_tools/
except ImportError:
    from development_tools.shared.standard_exclusions import should_exclude_file
    from development_tools import config

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

# Load external config on module import (if not already loaded)
# Load external config on module import (safe to call multiple times)
config.load_external_config()

class ErrorHandlingAnalyzer:
    """Analyzes error handling patterns in Python code."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {
            'total_functions': 0,
            'functions_with_try_except': 0,
            'functions_with_error_handling': 0,
            'functions_with_decorators': 0,
            'functions_missing_error_handling': 0,
            'analyze_error_handling': 0.0,
            'error_patterns': {},
            'missing_error_handling': [],
            'error_handling_quality': {},
            'recommendations': [],
            # Phase 1: Functions with try-except but no decorator
            'phase1_candidates': [],
            'phase1_total': 0,
            'phase1_by_priority': {'high': 0, 'medium': 0, 'low': 0},
            # Phase 2: Generic exception raises
            'phase2_exceptions': [],
            'phase2_total': 0,
            'phase2_by_type': {}
        }
        
        # Load error handling configuration from external config
        error_config = config.get_error_handling_config()
        
        # Build error patterns from config
        decorator_names = error_config.get('decorator_names', ['@handle_errors', 'handle_errors'])
        exception_classes = error_config.get('exception_base_classes', ['BaseError', 'DataError'])
        error_handler_functions = error_config.get('error_handler_functions', [])
        
        # Error handling patterns to look for (built from config)
        self.error_patterns = {
            'try_except': r'try\s*:',
        }
        
        # Add decorator patterns from config
        for decorator in decorator_names:
            if decorator.startswith('@'):
                pattern_name = decorator.replace('@', '').replace('_', '_') + '_decorator'
                self.error_patterns[pattern_name] = rf'{re.escape(decorator)}'
            else:
                pattern_name = decorator.replace('_', '_') + '_usage'
                self.error_patterns[pattern_name] = rf'{re.escape(decorator)}\.'
        
        # Add error handler function patterns from config
        for handler_func in error_handler_functions:
            self.error_patterns[handler_func] = rf'{re.escape(handler_func)}'
        
        # Add exception class patterns from config
        for exc_class in exception_classes:
            self.error_patterns[exc_class] = rf'{exc_class}'
        
        # Functions that should have error handling (from config)
        self.critical_functions = error_config.get('critical_function_keywords', {
            'file_operations': ['open', 'read', 'write', 'save', 'load'],
            'network_operations': ['send', 'receive', 'connect', 'request'],
            'data_operations': ['parse', 'serialize', 'deserialize', 'validate'],
            'user_operations': ['create', 'update', 'delete', 'authenticate'],
            'ai_operations': ['generate', 'process', 'analyze', 'classify']
        })
        
        # Phase 1: Keywords for determining operation type and priority
        # (These are more generic and can stay hardcoded, or be moved to config later)
        self.phase1_keywords = {
            'file_io': ['open', 'read', 'write', 'save', 'load', 'os.remove', 'shutil.move'],
            'network': ['send', 'receive', 'connect', 'request', 'http', 'api', 'discord', 'email'],
            'user_data': ['user_data', 'profile', 'account', 'preferences', 'task', 'schedule', 'checkin'],
            'ai': ['generate', 'process', 'analyze', 'classify', 'chatbot', 'lm_studio'],
            'entry_point': ['main', 'run', 'start', 'handle', 'on_']
        }
        
        # Phase 2: Generic exceptions to audit (from config)
        # Get base exception from config for fallback
        base_exception_default = exception_classes[0] if exception_classes else 'BaseError'
        default_generic_exceptions = {
            'Exception': base_exception_default,
            'ValueError': 'ValidationError or DataError',
            'KeyError': 'DataError or ConfigurationError',
            'TypeError': 'ValidationError or DataError'
        }
        self.generic_exceptions = error_config.get('generic_exceptions', default_generic_exceptions)

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze error handling in a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            file_results = {
                'file_path': str(file_path.relative_to(self.project_root)),
                'functions': [],
                'classes': [],
                'error_patterns_found': set(),
                'missing_error_handling': [],
                'phase2_exceptions': []  # Phase 2: Generic exception raises in this file
            }
            
            # Phase 2: Find generic exception raises using visitor pattern
            class RaiseVisitor(ast.NodeVisitor):
                def __init__(self, analyzer, content, file_path):
                    self.analyzer = analyzer
                    self.content = content
                    self.file_path = file_path
                    self.current_function = None
                    self.exceptions = []
                
                def visit_FunctionDef(self, node):
                    old_func = self.current_function
                    self.current_function = node
                    self.generic_visit(node)
                    self.current_function = old_func
                
                def visit_AsyncFunctionDef(self, node):
                    old_func = self.current_function
                    self.current_function = node
                    self.generic_visit(node)
                    self.current_function = old_func
                
                def visit_Raise(self, node):
                    exc_info = self.analyzer._analyze_raise_statement(node, self.content, self.file_path)
                    if exc_info:
                        # Add function context if we found it
                        if self.current_function:
                            exc_info['function_name'] = self.current_function.name
                            exc_info['function_line'] = self.current_function.lineno
                        self.exceptions.append(exc_info)
            
            visitor = RaiseVisitor(self, content, file_path)
            visitor.visit(tree)
            file_results['phase2_exceptions'] = visitor.exceptions
            
            # Analyze AST nodes
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_analysis = self._analyze_function(node, content, file_path=str(file_path))
                    file_results['functions'].append(func_analysis)
                    
                elif isinstance(node, ast.ClassDef):
                    class_analysis = self._analyze_class(node, content)
                    file_results['classes'].append(class_analysis)
            
            # Check for error handling patterns in file content
            for pattern_name, pattern in self.error_patterns.items():
                if re.search(pattern, content, re.MULTILINE):
                    file_results['error_patterns_found'].add(pattern_name)
            
            return file_results
            
        except Exception as e:
            return {
                'file_path': str(file_path.relative_to(self.project_root)),
                'error': f"Failed to analyze file: {e}",
                'functions': [],
                'classes': [],
                'error_patterns_found': set(),
                'missing_error_handling': []
            }

    def _should_exclude_function(self, func_node: ast.FunctionDef, content: str, file_path: str = None) -> bool:
        """
        Check if a function should be excluded from error handling analysis.
        
        Functions are excluded if they:
        - Are Pydantic validators (@field_validator, @model_validator)
        - Have exclusion comments (e.g., "# ERROR_HANDLING_EXCLUDE")
        - Are special Python methods (__getattr__, __new__, __repr__, etc.)
        - Are logger methods (debug, info, warning, error, critical)
        - Are file auditor logging methods
        - Are part of error handling infrastructure itself
        
        Args:
            func_node: AST node for the function
            content: Full file content (for context checking)
            file_path: Optional file path for more precise exclusions
        """
        # The content parameter now includes context lines before the function
        func_content_lower = content.lower()
        file_path_lower = file_path.lower() if file_path else ""
        func_name = func_node.name
        
        # Check for exclusion comment (the content includes context lines before the function)
        # Match both "# ERROR_HANDLING_EXCLUDE" and "# ERROR_HANDLING_EXCLUDE: description"
        if '# error_handling_exclude' in func_content_lower or '# error handling exclude' in func_content_lower:
            return True
        
        # Exclude special Python methods that shouldn't have error handling
        special_methods = ('__getattr__', '__setattr__', '__delattr__', '__getattribute__',
                          '__new__', '__repr__', '__str__', '__hash__', '__eq__', '__ne__',
                          '__lt__', '__le__', '__gt__', '__ge__', '__bool__', '__len__',
                          '__iter__', '__next__', '__contains__', '__call__')
        if func_name in special_methods:
            return True
        
        # Exclude logger methods (these are logging infrastructure)
        if func_name in ('debug', 'info', 'warning', 'error', 'critical', 'log', 'exception'):
            # Check if this is in a logger class or file_auditor
            if file_path and ('logger.py' in file_path or 'file_auditor.py' in file_path):
                return True
            # Also check if it's a DummyLogger or similar
            if 'dummylogger' in func_content_lower or 'componentlogger' in func_content_lower:
                return True
        
        # Exclude file_auditor logging methods
        if file_path and 'file_auditor.py' in file_path:
            if func_name in ('info', 'warning', 'debug', 'error', 'critical'):
                return True
        
        # Check for Pydantic validators
        for decorator in func_node.decorator_list:
            # Check for @field_validator or @model_validator
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    if decorator.func.id in ('field_validator', 'model_validator'):
                        return True
                elif isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr in ('field_validator', 'model_validator'):
                        return True
            elif isinstance(decorator, ast.Name):
                if decorator.id in ('field_validator', 'model_validator'):
                    return True
        
        # Check for special methods that are part of error handling infrastructure
        # These are in core/error_handling.py and are recovery strategies
        if file_path and 'error_handling.py' in file_path:
            if func_node.name in ('can_handle', 'recover', '_get_default_data', '_get_user_friendly_message', '__init__'):
                # Check if this is in a recovery strategy class
                # Look for class definition before this function
                if 'errorrecoverystrategy' in func_content_lower or 'recovery' in func_content_lower:
                    return True
        
        return False

    def _analyze_raise_statement(self, raise_node: ast.Raise, content: str, file_path: Path) -> Optional[Dict[str, Any]]:
        """Phase 2: Analyze a raise statement for generic exceptions."""
        if not raise_node.exc:
            return None
        
        # Get exception type
        exc_type_name = None
        
        if isinstance(raise_node.exc, ast.Call):
            if isinstance(raise_node.exc.func, ast.Name):
                exc_type_name = raise_node.exc.func.id
            elif isinstance(raise_node.exc.func, ast.Attribute):
                exc_type_name = raise_node.exc.func.attr
        elif isinstance(raise_node.exc, ast.Name):
            exc_type_name = raise_node.exc.id
        
        # Only track generic exceptions
        if exc_type_name not in self.generic_exceptions:
            return None
        
        # Get line number and context
        lines = content.split('\n')
        line_num = raise_node.lineno
        line_content = lines[line_num - 1] if line_num <= len(lines) else ""
        
        # Function context will be set by the visitor pattern
        func_name = None
        func_line = None
        
        # Get context lines around the raise
        context_start = max(0, line_num - 3)
        context_end = min(len(lines), line_num + 2)
        context = '\n'.join(lines[context_start:context_end])
        
        # Determine suggested replacement
        suggested_replacement = self._suggest_exception_replacement(
            exc_type_name, str(file_path), func_name, line_content
        )
        
        return {
            'file_path': str(file_path.relative_to(self.project_root)),
            'line_number': line_num,
            'exception_type': exc_type_name,
            'suggested_replacement': suggested_replacement,
            'function_name': func_name,
            'function_line': func_line,
            'line_content': line_content.strip(),
            'context': context
        }
    
    def _suggest_exception_replacement(self, exc_type: str, file_path: str, func_name: str, line_content: str) -> str:
        """Suggest appropriate exception replacement for generic exception (using config)."""
        file_lower = file_path.lower()
        func_lower = (func_name or '').lower()
        line_lower = line_content.lower()
        
        # Use generic_exceptions mapping from config first
        if exc_type in self.generic_exceptions:
            suggestion = self.generic_exceptions[exc_type]
            # If it's a simple string (not "X or Y"), return it
            if ' or ' not in suggestion:
                return suggestion
        
        # Get exception base classes from config for fallback suggestions
        error_config = config.get_error_handling_config()
        exception_classes = error_config.get('exception_base_classes', ['BaseError', 'DataError'])
        base_exception = exception_classes[0] if exception_classes else 'BaseError'
        
        # More specific heuristics (using config exception classes)
        if exc_type == 'ValueError':
            # Check if it's user input validation
            if any(kw in line_lower for kw in ['invalid', 'missing', 'required', 'format', 'user']):
                # Look for ValidationError in config, fallback to first exception
                validation_error = next((e for e in exception_classes if 'Validation' in e), base_exception)
                return validation_error
            else:
                # Look for DataError in config, fallback to first exception
                data_error = next((e for e in exception_classes if 'Data' in e), base_exception)
                return data_error
        elif exc_type == 'KeyError':
            # Check if it's config access
            if any(kw in line_lower or kw in file_lower for kw in ['config', 'setting', 'option']):
                # Look for ConfigurationError in config, fallback to first exception
                config_error = next((e for e in exception_classes if 'Configuration' in e), base_exception)
                return config_error
            else:
                # Look for DataError in config, fallback to first exception
                data_error = next((e for e in exception_classes if 'Data' in e), base_exception)
                return data_error
        elif exc_type == 'TypeError':
            # Check if it's user input type issue
            if any(kw in line_lower for kw in ['invalid', 'expected', 'user', 'input']):
                # Look for ValidationError in config, fallback to first exception
                validation_error = next((e for e in exception_classes if 'Validation' in e), base_exception)
                return validation_error
            else:
                # Look for DataError in config, fallback to first exception
                data_error = next((e for e in exception_classes if 'Data' in e), base_exception)
                return data_error
        elif exc_type == 'Exception':
            # Try to determine from context
            if any(kw in file_lower for kw in ['file', 'read', 'write', 'save', 'load']):
                # Look for FileOperationError or DataError in config
                file_error = next((e for e in exception_classes if 'File' in e or 'Data' in e), base_exception)
                return file_error
            elif any(kw in file_lower for kw in ['network', 'http', 'api', 'discord', 'email']):
                comm_error = next((e for e in exception_classes if 'Communication' in e), base_exception)
                return comm_error
            elif any(kw in file_lower for kw in ['config', 'setting']):
                config_error = next((e for e in exception_classes if 'Configuration' in e), base_exception)
                return config_error
            elif any(kw in file_lower for kw in ['schedule', 'task', 'reminder']):
                # Look for SchedulerError or generic error
                scheduler_error = next((e for e in exception_classes if 'Scheduler' in e or 'Task' in e), base_exception)
                return scheduler_error
            else:
                return base_exception
        
        return self.generic_exceptions.get(exc_type, base_exception)

    def _analyze_function(self, func_node: ast.FunctionDef, content: str, file_path: str = None) -> Dict[str, Any]:
        """Analyze error handling in a function."""
        func_name = func_node.name
        func_start = func_node.lineno
        func_end = func_node.end_lineno or func_start
        
        # Extract function content (include a few lines before for exclusion comments)
        lines = content.split('\n')
        # Check up to 3 lines before the function for exclusion comments
        context_start = max(0, func_start - 4)  # -4 because lineno is 1-indexed
        func_content = '\n'.join(lines[context_start:func_end])
        
        # Check if function should be excluded from analysis
        if self._should_exclude_function(func_node, func_content, file_path):
            # Return analysis indicating function is excluded
            return {
                'name': func_name,
                'line_start': func_start,
                'line_end': func_end,
                'has_try_except': False,
                'has_error_handling': False,
                'has_decorators': False,
                'error_handling_quality': 'excluded',
                'missing_error_handling': False,
                'error_patterns': set(),
                'recommendations': [],
                'excluded': True,
                'func_content': func_content  # Store for consistency
            }
        
        analysis = {
            'name': func_name,
            'line_start': func_start,
            'line_end': func_end,
            'has_try_except': False,
            'has_error_handling': False,
            'has_decorators': False,
            'error_handling_quality': 'none',
            'missing_error_handling': False,
            'error_patterns': set(),
            'recommendations': [],
            'excluded': False,
            'func_content': func_content  # Store for Phase 1 analysis
        }
        
        # Check for try-except blocks
        for node in ast.walk(func_node):
            if isinstance(node, ast.Try):
                analysis['has_try_except'] = True
                analysis['has_error_handling'] = True
        
        # Check for error handling decorators
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == 'handle_errors':
                analysis['has_decorators'] = True
                analysis['has_error_handling'] = True
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name) and decorator.func.id == 'handle_errors':
                    analysis['has_decorators'] = True
                    analysis['has_error_handling'] = True
        
        # Check for error handling patterns in function content
        for pattern_name, pattern in self.error_patterns.items():
            if re.search(pattern, func_content, re.MULTILINE):
                analysis['error_patterns'].add(pattern_name)
                if pattern_name != 'try_except':  # Don't double-count try-except
                    analysis['has_error_handling'] = True
        
        # Determine error handling quality
        # Phase 1: Check if this is a candidate (try-except without decorator)
        if analysis['has_try_except'] and not analysis['has_decorators']:
            analysis['is_phase1_candidate'] = True
            analysis['error_handling_quality'] = 'basic'
        elif analysis['has_decorators']:
            analysis['is_phase1_candidate'] = False
            analysis['error_handling_quality'] = 'excellent'
        elif analysis['has_try_except'] and len(analysis['error_patterns']) > 1:
            analysis['is_phase1_candidate'] = False
            analysis['error_handling_quality'] = 'good'
        else:
            analysis['is_phase1_candidate'] = False
            analysis['error_handling_quality'] = 'none'
            analysis['missing_error_handling'] = True
        
        # Check if function should have error handling
        if self._should_have_error_handling(func_name, func_content):
            if not analysis['has_error_handling']:
                analysis['missing_error_handling'] = True
                analysis['recommendations'].append("Add error handling decorator or try-except blocks")
        
        return analysis

    def _analyze_class(self, class_node: ast.ClassDef, content: str) -> Dict[str, Any]:
        """Analyze error handling in a class."""
        class_name = class_node.name
        class_start = class_node.lineno
        class_end = class_node.end_lineno or class_start
        
        # Extract class content
        lines = content.split('\n')
        class_content = '\n'.join(lines[class_start-1:class_end])
        
        analysis = {
            'name': class_name,
            'line_start': class_start,
            'line_end': class_end,
            'methods': [],
            'has_error_handling': False,
            'error_patterns': set()
        }
        
        # Check for error handling patterns in class content
        for pattern_name, pattern in self.error_patterns.items():
            if re.search(pattern, class_content, re.MULTILINE):
                analysis['error_patterns'].add(pattern_name)
                if pattern_name != 'try_except':
                    analysis['has_error_handling'] = True
        
        # Analyze methods
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                method_analysis = self._analyze_function(node, content)
                analysis['methods'].append(method_analysis)
                if method_analysis['has_error_handling']:
                    analysis['has_error_handling'] = True
        
        return analysis

    def _should_have_error_handling(self, func_name: str, content: str) -> bool:
        """Determine if a function should have error handling based on its name and content."""
        func_lower = func_name.lower()
        content_lower = content.lower()
        
        # Check for critical operation keywords
        for category, keywords in self.critical_functions.items():
            for keyword in keywords:
                if keyword in func_lower or keyword in content_lower:
                    return True
        
        # Check for file operations
        if any(op in content_lower for op in ['open(', 'read(', 'write(', 'save(', 'load(']):
            return True
        
        # Check for network operations
        if any(op in content_lower for op in ['send(', 'receive(', 'connect(', 'request(']):
            return True
        
        # Check for data operations
        if any(op in content_lower for op in ['parse(', 'serialize(', 'deserialize(', 'validate(']):
            return True
        
        return False
    
    def _determine_operation_type(self, func_name: str, file_path: str, func_content: str = None) -> str:
        """Phase 1: Determine operation type from function name, file path, and content."""
        func_lower = func_name.lower()
        file_lower = file_path.lower()
        content_lower = (func_content or "").lower()
        combined = f"{func_lower} {file_lower} {content_lower}"
        
        # Check for specific operation types (order matters - more specific first)
        if any(kw in combined for kw in ['load', 'save', 'read', 'write', 'file', 'json', 'open(', 'close(']):
            return 'file_io'
        elif any(kw in combined for kw in ['send', 'receive', 'connect', 'request', 'discord', 'email', 'api', 'http']):
            return 'network'
        elif any(kw in combined for kw in ['user', 'account', 'profile', 'preference', 'task', 'schedule', 'checkin']):
            return 'user_data'
        elif any(kw in combined for kw in ['validate', 'check', 'verify', 'invalid', 'missing', 'required']):
            return 'validation'
        elif any(kw in combined for kw in ['schedule', 'task', 'reminder', 'scheduler']):
            return 'scheduling'
        elif any(kw in combined for kw in ['config', 'setting', 'option']):
            return 'configuration'
        elif any(kw in combined for kw in ['ui', 'dialog', 'widget', 'button', 'qt', 'pyqt']):
            return 'ui'
        elif any(kw in combined for kw in ['generate', 'process', 'analyze', 'classify', 'chatbot', 'lm_studio', 'ai']):
            return 'ai'
        
        return "general"
    
    def _is_entry_point(self, func_name: str, file_path: str, func_content: str = None) -> bool:
        """Phase 1: Check if function is an entry point."""
        func_lower = func_name.lower()
        file_lower = file_path.lower()
        content_lower = (func_content or "").lower()
        
        # Check function name
        if any(keyword in func_lower for keyword in ['handle', 'on_', 'command', 'handler', 'main', 'run', 'start']):
            return True
        
        # Check file path for common entry point locations
        if 'command_handlers' in file_lower or 'communication_channels' in file_lower:
            return True
        
        # Check if it's a UI event handler
        if 'ui' in file_lower and ('on_' in func_lower or 'clicked' in func_lower):
            return True
        
        # Check content for entry point patterns
        if content_lower:
            if any(kw in content_lower for kw in ['@app.route', '@command', '@handler', 'command_handler', 'event_handler']):
                return True
        
        # Protected/magic methods are usually not entry points
        if func_name.startswith('_') and not func_name.startswith('__'):
            return False
        if func_name.startswith('__') and func_name.endswith('__'):
            return False
        
        return False
    
    def _determine_phase1_priority(self, operation_type: str, is_entry_point: bool) -> str:
        """Phase 1: Determine priority for candidate."""
        priority_score = 0
        
        if is_entry_point:
            priority_score += 3
        
        if operation_type in ['file_io', 'network', 'user_data', 'ai']:
            priority_score += 2
        
        if priority_score >= 4:
            return "high"
        elif priority_score >= 2:
            return "medium"
        else:
            return "low"

    def _get_module_name(self, file_path: str) -> str:
        """Extract module name from file path with more context."""
        path = Path(file_path)
        parts = path.parts
        
        # Skip the project root and build a more descriptive module name
        if len(parts) <= 1:
            return "root"
        
        # Get meaningful parts of the path
        meaningful_parts = []
        for part in parts[1:]:  # Skip project root
            if part not in ['__pycache__', '.git', 'node_modules', '.venv']:
                meaningful_parts.append(part)
        
        # Create descriptive module names based on the path structure
        if len(meaningful_parts) >= 3:
            # For deeply nested files, use the last 2 parts
            return f"{meaningful_parts[-2]}/{meaningful_parts[-1]}"
        elif len(meaningful_parts) == 2:
            # For files in subdirectories, use parent/child format
            return f"{meaningful_parts[0]}/{meaningful_parts[1]}"
        elif len(meaningful_parts) == 1:
            # For root-level files, use the filename
            return meaningful_parts[0]
        else:
            return "root"

    def analyze_project(self, include_tests: bool = False, include_dev_tools: bool = False) -> Dict[str, Any]:
        """Analyze error handling across the entire project."""
        logger.info("Analyzing error handling coverage...")
        
        # Determine context based on configuration
        if include_tests and include_dev_tools:
            context = 'development'  # Include everything
        elif include_tests or include_dev_tools:
            context = 'development'  # More permissive
        else:
            context = 'production'   # Exclude tests and dev tools
        
        # Find all Python files using context-based exclusions
        # Use same scan directories as analyze_functions for consistency
        try:
            from .. import config  # Go up one level from error_handling/ to development_tools/
        except ImportError:
            from development_tools import config
        
        # Load external config if not already loaded
        config.load_external_config()
        
        # Get scan directories from config (same as analyze_functions)
        scan_directories = config.get_scan_directories()
        
        # Add optional directories based on flags
        if include_tests and 'tests' not in scan_directories:
            scan_directories = list(scan_directories) + ['tests']
        if include_dev_tools and 'development_tools' not in scan_directories:
            scan_directories = list(scan_directories) + ['development_tools']
        
        python_files = []
        
        # Scan configured directories (same approach as analyze_functions)
        for scan_dir in scan_directories:
            dir_path = self.project_root / scan_dir
            if not dir_path.exists():
                continue
            for py_file in dir_path.rglob('*.py'):
                # Use context-based exclusions
                if not should_exclude_file(str(py_file), 'analysis', context):
                    python_files.append(py_file)
        
        # Also scan root directory for .py files (entry points)
        for py_file in self.project_root.glob('*.py'):
            # Use context-based exclusions
            if not should_exclude_file(str(py_file), 'analysis', context):
                python_files.append(py_file)
        
        logger.info(f"Found {len(python_files)} Python files to analyze")
        
        # Analyze each file
        file_results = []
        for file_path in python_files:
            file_analysis = self.analyze_file(file_path)
            file_results.append(file_analysis)
        
        # Aggregate results
        self._aggregate_results(file_results)
        
        # Generate recommendations
        self._generate_recommendations()
        
        return self.results

    def _aggregate_results(self, file_results: List[Dict[str, Any]]):
        """Aggregate results from all files."""
        total_functions = 0
        functions_with_try_except = 0
        functions_with_error_handling = 0
        functions_with_decorators = 0
        functions_missing_error_handling = 0
        
        error_patterns_count = defaultdict(int)
        missing_error_handling = []
        error_handling_quality = defaultdict(int)
        
        # Phase 1: Track candidates (try-except without decorator)
        phase1_candidates = []
        
        # Phase 2: Track generic exception raises
        phase2_exceptions = []
        phase2_by_type = defaultdict(int)
        
        # Module-level analysis
        module_stats = defaultdict(lambda: {
            'total_functions': 0,
            'functions_with_error_handling': 0,
            'functions_missing_error_handling': 0,
            'analyze_error_handling': 0.0,
            'files': set()
        })
        
        for file_result in file_results:
            if 'error' in file_result:
                continue
            
            # Get module name from file path
            file_path = file_result['file_path']
            module_name = self._get_module_name(file_path)
            module_stats[module_name]['files'].add(file_path)
                
            # Count functions
            for func in file_result['functions']:
                # Skip excluded functions from totals
                if func.get('excluded', False):
                    continue
                    
                total_functions += 1
                module_stats[module_name]['total_functions'] += 1
                
                if func['has_try_except']:
                    functions_with_try_except += 1
                
                if func['has_error_handling']:
                    functions_with_error_handling += 1
                    module_stats[module_name]['functions_with_error_handling'] += 1
                else:
                    functions_missing_error_handling += 1
                    module_stats[module_name]['functions_missing_error_handling'] += 1
                
                if func['has_decorators']:
                    functions_with_decorators += 1
                
                if func['missing_error_handling']:
                    missing_error_handling.append({
                        'file': file_result['file_path'],
                        'function': func['name'],
                        'line': func['line_start'],
                        'quality': func['error_handling_quality']
                    })
                
                # Count error handling quality
                error_handling_quality[func['error_handling_quality']] += 1
                
                # Count error patterns
                for pattern in func['error_patterns']:
                    error_patterns_count[pattern] += 1
                
                # Phase 1: Track candidates (try-except without decorator)
                if func.get('is_phase1_candidate', False):
                    # Determine operation type and priority (use function content if available)
                    func_content = func.get('func_content', '')
                    operation_type = self._determine_operation_type(func['name'], file_result['file_path'], func_content)
                    is_entry_point = self._is_entry_point(func['name'], file_result['file_path'], func_content)
                    priority = self._determine_phase1_priority(operation_type, is_entry_point)
                    
                    phase1_candidates.append({
                        'file_path': file_result['file_path'],
                        'function_name': func['name'],
                        'line_start': func['line_start'],
                        'line_end': func['line_end'],
                        'is_async': func.get('is_async', False),
                        'operation_type': operation_type,
                        'is_entry_point': is_entry_point,
                        'priority': priority
                    })
            
            # Phase 2: Collect generic exception raises
            for exc in file_result.get('phase2_exceptions', []):
                phase2_exceptions.append(exc)
                phase2_by_type[exc['exception_type']] += 1
            
            # Count file-level patterns
            for pattern in file_result['error_patterns_found']:
                error_patterns_count[pattern] += 1
        
        # Calculate module-level coverage and get top 5 worst modules
        worst_modules = []
        for module_name, stats in module_stats.items():
            if stats['total_functions'] > 0:
                stats['analyze_error_handling'] = (stats['functions_with_error_handling'] / stats['total_functions'] * 100)
                worst_modules.append({
                    'module': module_name,
                    'coverage': stats['analyze_error_handling'],
                    'missing': stats['functions_missing_error_handling'],
                    'total': stats['total_functions']
                })
        
        # Sort by coverage (worst first) and take top 5
        worst_modules.sort(key=lambda x: x['coverage'])
        top_5_worst = worst_modules[:5]
        
        # Phase 1: Sort candidates by priority
        phase1_candidates.sort(key=lambda x: {'high': 3, 'medium': 2, 'low': 1}.get(x['priority'], 0), reverse=True)
        phase1_by_priority = defaultdict(int)
        for candidate in phase1_candidates:
            phase1_by_priority[candidate['priority']] += 1
        
        # Update results
        self.results.update({
            'total_functions': total_functions,
            'functions_with_try_except': functions_with_try_except,
            'functions_with_error_handling': functions_with_error_handling,
            'functions_with_decorators': functions_with_decorators,
            'functions_missing_error_handling': functions_missing_error_handling,
            'analyze_error_handling': (functions_with_error_handling / total_functions * 100) if total_functions > 0 else 0,
            'error_patterns': dict(error_patterns_count),
            'missing_error_handling': missing_error_handling,
            'error_handling_quality': dict(error_handling_quality),
            'worst_modules': top_5_worst,
            # Phase 1 results
            'phase1_candidates': phase1_candidates,
            'phase1_total': len(phase1_candidates),
            'phase1_by_priority': dict(phase1_by_priority),
            # Phase 2 results
            'phase2_exceptions': phase2_exceptions,
            'phase2_total': len(phase2_exceptions),
            'phase2_by_type': dict(phase2_by_type)
        })

    def _generate_recommendations(self):
        """Generate recommendations for improving error handling (delegates to generate_error_handling_recommendations)."""
        # Import recommendation generator
        try:
            from .generate_error_handling_recommendations import generate_recommendations
        except ImportError:
            from development_tools.error_handling.generate_error_handling_recommendations import generate_recommendations
        
        # Generate recommendations using the dedicated tool
        recommendations = generate_recommendations(self.results)
        self.results['recommendations'] = recommendations

def main():
    """Main function for error handling coverage analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze error handling coverage in the codebase')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--output', type=str, help='Output file path (default: development_tools/error_handling/error_handling_details.json when --json is used)')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--include-tests', action='store_true', help='Include test files in analysis')
    parser.add_argument('--include-dev-tools', action='store_true', help='Include development_tools in analysis')
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        logger.error(f"Project root {project_root} does not exist")
        return 1
    
    # Run analysis
    analyzer = ErrorHandlingAnalyzer(str(project_root))
    results = analyzer.analyze_project(
        include_tests=args.include_tests,
        include_dev_tools=args.include_dev_tools
    )
    
    # Generate reports using dedicated report generator
    try:
        from .generate_error_handling_report import ErrorHandlingReportGenerator
    except ImportError:
        from development_tools.error_handling.generate_error_handling_report import ErrorHandlingReportGenerator
    
    report_generator = ErrorHandlingReportGenerator(results)
    
    if args.json:
        # Determine output file path
        if args.output:
            output_path = Path(args.output)
        else:
            # Default to development_tools/error_handling directory
            tools_dir = project_root / 'development_tools' / 'error_handling'
            tools_dir.mkdir(exist_ok=True)
            output_path = tools_dir / 'error_handling_details.json'
        
        # Save JSON report
        report_generator.save_json_report(output_path)
    else:
        # Print summary
        report_generator.print_summary()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())