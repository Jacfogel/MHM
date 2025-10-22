#!/usr/bin/env python3
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
from typing import Dict, List, Any
from collections import defaultdict
import re

from .standard_exclusions import should_exclude_file

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
            'error_handling_coverage': 0.0,
            'error_patterns': {},
            'missing_error_handling': [],
            'error_handling_quality': {},
            'recommendations': []
        }
        
        # Error handling patterns to look for
        self.error_patterns = {
            'try_except': r'try\s*:',
            'handle_errors_decorator': r'@handle_errors',
            'error_handler_usage': r'error_handler\.',
            'safe_file_operation': r'safe_file_operation',
            'handle_file_error': r'handle_file_error',
            'handle_network_error': r'handle_network_error',
            'handle_communication_error': r'handle_communication_error',
            'handle_configuration_error': r'handle_configuration_error',
            'handle_validation_error': r'handle_validation_error',
            'handle_ai_error': r'handle_ai_error',
            'MHMError': r'MHMError',
            'DataError': r'DataError',
            'ConfigurationError': r'ConfigurationError',
            'CommunicationError': r'CommunicationError',
            'ValidationError': r'ValidationError',
            'AIError': r'AIError'
        }
        
        # Functions that should have error handling
        self.critical_functions = {
            'file_operations': ['open', 'read', 'write', 'save', 'load'],
            'network_operations': ['send', 'receive', 'connect', 'request'],
            'data_operations': ['parse', 'serialize', 'deserialize', 'validate'],
            'user_operations': ['create', 'update', 'delete', 'authenticate'],
            'ai_operations': ['generate', 'process', 'analyze', 'classify']
        }

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
                'missing_error_handling': []
            }
            
            # Analyze AST nodes
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_analysis = self._analyze_function(node, content)
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

    def _analyze_function(self, func_node: ast.FunctionDef, content: str) -> Dict[str, Any]:
        """Analyze error handling in a function."""
        func_name = func_node.name
        func_start = func_node.lineno
        func_end = func_node.end_lineno or func_start
        
        # Extract function content
        lines = content.split('\n')
        func_content = '\n'.join(lines[func_start-1:func_end])
        
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
            'recommendations': []
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
        if analysis['has_decorators']:
            analysis['error_handling_quality'] = 'excellent'
        elif analysis['has_try_except'] and len(analysis['error_patterns']) > 1:
            analysis['error_handling_quality'] = 'good'
        elif analysis['has_try_except']:
            analysis['error_handling_quality'] = 'basic'
        else:
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
        print("Analyzing error handling coverage...")
        
        # Determine context based on configuration
        if include_tests and include_dev_tools:
            context = 'development'  # Include everything
        elif include_tests or include_dev_tools:
            context = 'development'  # More permissive
        else:
            context = 'production'   # Exclude tests and dev tools
        
        # Find all Python files using context-based exclusions
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', '.venv']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    # Use context-based exclusions
                    if not should_exclude_file(str(file_path), 'analysis', context):
                        python_files.append(file_path)
        
        print(f"Found {len(python_files)} Python files to analyze")
        
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
        
        # Module-level analysis
        module_stats = defaultdict(lambda: {
            'total_functions': 0,
            'functions_with_error_handling': 0,
            'functions_missing_error_handling': 0,
            'error_handling_coverage': 0.0,
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
            
            # Count file-level patterns
            for pattern in file_result['error_patterns_found']:
                error_patterns_count[pattern] += 1
        
        # Calculate module-level coverage and get top 5 worst modules
        worst_modules = []
        for module_name, stats in module_stats.items():
            if stats['total_functions'] > 0:
                stats['error_handling_coverage'] = (stats['functions_with_error_handling'] / stats['total_functions'] * 100)
                worst_modules.append({
                    'module': module_name,
                    'coverage': stats['error_handling_coverage'],
                    'missing': stats['functions_missing_error_handling'],
                    'total': stats['total_functions']
                })
        
        # Sort by coverage (worst first) and take top 5
        worst_modules.sort(key=lambda x: x['coverage'])
        top_5_worst = worst_modules[:5]
        
        # Update results
        self.results.update({
            'total_functions': total_functions,
            'functions_with_try_except': functions_with_try_except,
            'functions_with_error_handling': functions_with_error_handling,
            'functions_with_decorators': functions_with_decorators,
            'functions_missing_error_handling': functions_missing_error_handling,
            'error_handling_coverage': (functions_with_error_handling / total_functions * 100) if total_functions > 0 else 0,
            'error_patterns': dict(error_patterns_count),
            'missing_error_handling': missing_error_handling,
            'error_handling_quality': dict(error_handling_quality),
            'worst_modules': top_5_worst
        })

    def _generate_recommendations(self):
        """Generate recommendations for improving error handling."""
        recommendations = []
        
        # Coverage recommendations
        if self.results['error_handling_coverage'] < 80:
            recommendations.append(f"Improve error handling coverage (currently {self.results['error_handling_coverage']:.1f}%)")
        
        # Missing error handling recommendations
        if self.results['functions_missing_error_handling'] > 0:
            recommendations.append(f"Add error handling to {self.results['functions_missing_error_handling']} functions")
        
        # Quality recommendations
        if self.results['error_handling_quality'].get('none', 0) > 0:
            recommendations.append("Replace basic try-except with @handle_errors decorator where appropriate")
        
        # Pattern recommendations
        if self.results['error_patterns'].get('try_except', 0) > self.results['error_patterns'].get('handle_errors_decorator', 0):
            recommendations.append("Consider using @handle_errors decorator instead of manual try-except blocks")
        
        # Specific missing error handling
        critical_missing = [f for f in self.results['missing_error_handling'] if f['quality'] == 'none']
        if critical_missing:
            recommendations.append(f"Priority: Add error handling to {len(critical_missing)} critical functions")
        
        self.results['recommendations'] = recommendations

    def print_summary(self):
        """Print a summary of error handling analysis."""
        print("\n" + "=" * 80)
        print("ERROR HANDLING COVERAGE ANALYSIS")
        print("=" * 80)
        
        print(f"Total Functions: {self.results['total_functions']}")
        print(f"Functions with Try-Except: {self.results['functions_with_try_except']}")
        print(f"Functions with Error Handling: {self.results['functions_with_error_handling']}")
        print(f"Functions with Decorators: {self.results['functions_with_decorators']}")
        print(f"Functions Missing Error Handling: {self.results['functions_missing_error_handling']}")
        print(f"Error Handling Coverage: {self.results['error_handling_coverage']:.1f}%")
        
        print("\nError Handling Quality Distribution:")
        for quality, count in self.results['error_handling_quality'].items():
            print(f"  {quality.title()}: {count}")
        
        print("\nError Patterns Found:")
        for pattern, count in self.results['error_patterns'].items():
            print(f"  {pattern}: {count}")
        
        if self.results['missing_error_handling']:
            print(f"\nFunctions Missing Error Handling ({len(self.results['missing_error_handling'])}):")
            for func in self.results['missing_error_handling'][:10]:  # Show first 10
                print(f"  {func['file']}:{func['function']} (line {func['line']})")
            if len(self.results['missing_error_handling']) > 10:
                print(f"  ... and {len(self.results['missing_error_handling']) - 10} more")
        
        if self.results['recommendations']:
            print("\nRecommendations:")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"  {i}. {rec}")

def main():
    """Main function for error handling coverage analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze error handling coverage in the codebase')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--include-tests', action='store_true', help='Include test files in analysis')
    parser.add_argument('--include-dev-tools', action='store_true', help='Include ai_development_tools in analysis')
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"Error: Project root {project_root} does not exist")
        return 1
    
    # Run analysis
    analyzer = ErrorHandlingAnalyzer(str(project_root))
    results = analyzer.analyze_project(
        include_tests=args.include_tests,
        include_dev_tools=args.include_dev_tools
    )
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        analyzer.print_summary()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
