#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
function_discovery.py
Enhanced function search and relationship mapping for AI-optimized development.
Finds all functions, categorizes them (handler, utility, test, etc.), and shows relationships.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.error_handling import handle_errors
from core.logger import get_component_logger

# Handle both relative and absolute imports
try:
    from . import config
    from .services.standard_exclusions import should_exclude_file
except ImportError:
    from development_tools import config
    from development_tools.services.standard_exclusions import should_exclude_file

# Ensure external config is loaded
config.load_external_config()

logger = get_component_logger("development_tools")

# Load configuration from config module (which loads from external config if available)
def _get_project_root() -> Path:
    """Get project root from config."""
    return Path(config.get_project_root())

def _get_scan_directories() -> List[str]:
    """Get scan directories from config."""
    return config.get_scan_directories()

def _get_function_discovery_config() -> Dict:
    """Get function discovery config from config module."""
    return config.get_function_discovery_config()

# Load config values
PROJECT_ROOT = _get_project_root()
SCAN_DIRECTORIES = _get_scan_directories()
FUNCTION_DISCOVERY_CONFIG = _get_function_discovery_config()
HANDLER_KEYWORDS = FUNCTION_DISCOVERY_CONFIG.get('handler_keywords', ['handle', 'process', 'validate'])
TEST_KEYWORDS = FUNCTION_DISCOVERY_CONFIG.get('test_keywords', ['test_', 'test'])
MODERATE_COMPLEXITY = FUNCTION_DISCOVERY_CONFIG.get('moderate_complexity_threshold', 50)
HIGH_COMPLEXITY = FUNCTION_DISCOVERY_CONFIG.get('high_complexity_threshold', 100)
CRITICAL_COMPLEXITY = FUNCTION_DISCOVERY_CONFIG.get('critical_complexity_threshold', 200)


@handle_errors("checking if code is auto-generated", default_return=False)
def is_auto_generated_code(file_path: str, func_name: str) -> bool:
    """
    Determine if a function is in auto-generated code that should be excluded from complexity analysis.
    
    Args:
        file_path: Path to the file containing the function
        func_name: Name of the function
        
    Returns:
        True if the function should be excluded from complexity analysis
    """
    # Exclude PyQt auto-generated files
    if 'generated' in file_path and '_pyqt.py' in file_path:
        return True
    
    # Exclude specific auto-generated function patterns
    auto_generated_patterns = {
        'setupUi',  # PyQt UI setup functions
        'retranslateUi',  # PyQt translation functions
        'setup_ui',  # Alternative PyQt setup
        'retranslate_ui',  # Alternative PyQt translation
    }
    
    if func_name in auto_generated_patterns:
        return True
    
    # Exclude files in generated directories
    if '/generated/' in file_path or '\\generated\\' in file_path:
        return True
    
    # Exclude files with auto-generated patterns in name
    auto_generated_file_patterns = [
        '_pyqt.py',  # PyQt generated files
        '_ui.py',    # UI generated files
        '_generated.py',  # Explicitly generated files
        '_auto.py',  # Auto-generated files
    ]
    
    for pattern in auto_generated_file_patterns:
        if file_path.endswith(pattern):
            return True
    
    # Exclude functions with auto-generated naming patterns
    auto_generated_func_patterns = [
        'setup_ui_',  # UI setup functions
        'retranslate_ui_',  # UI translation functions
        '_generated_',  # Functions with generated in name
        '_auto_',  # Functions with auto in name
    ]
    
    for pattern in auto_generated_func_patterns:
        if pattern in func_name:
            return True
    
    return False


@handle_errors("checking if method is special Python method", default_return=False)
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


@handle_errors("extracting decorator documentation", default_return="")
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


@handle_errors("extracting functions from file", default_return=[])
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
                
                # Skip auto-generated code
                if is_auto_generated_code(file_path, name):
                    continue
                
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
        logger.error(f"Error parsing {file_path}: {e}")
    return functions


@handle_errors("scanning all functions", default_return=[])
def scan_all_functions(include_tests: bool = False, include_dev_tools: bool = False, 
                       scan_directories: List[str] = None, project_root: Path = None) -> List[Dict]:
    """
    Scan all Python files in scan directories and extract functions.
    
    Args:
        include_tests: Whether to include test files
        include_dev_tools: Whether to include development tools files
        scan_directories: Optional list of directories to scan (overrides config)
        project_root: Optional project root path (overrides config)
    
    Returns:
        List of function dictionaries
    """
    all_functions = []
    
    # Use provided project_root or config default
    root = project_root if project_root else PROJECT_ROOT
    
    # Use provided scan_directories or config default
    if scan_directories is None:
        scan_dirs = list(SCAN_DIRECTORIES)
    else:
        scan_dirs = list(scan_directories)
    
    # Add optional directories based on flags
    if include_tests and 'tests' not in scan_dirs:
        scan_dirs.append('tests')
    if include_dev_tools and 'development_tools' not in scan_dirs:
        scan_dirs.append('development_tools')
    
    # Determine context based on configuration
    if include_tests and include_dev_tools:
        context = 'development'  # Include everything
    elif include_tests or include_dev_tools:
        context = 'development'  # More permissive
    else:
        context = 'production'   # Exclude tests and dev tools
    
    # Scan configured directories
    for scan_dir in scan_dirs:
        dir_path = root / scan_dir
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob('*.py'):
            # Use context-based exclusions
            if not should_exclude_file(str(py_file), 'analysis', context):
                all_functions.extend(extract_functions(str(py_file)))
    
    # Also scan root directory
    for py_file in root.glob('*.py'):
        # Use context-based exclusions
        if not should_exclude_file(str(py_file), 'analysis', context):
            all_functions.extend(extract_functions(str(py_file)))
    
    return all_functions


@handle_errors("categorizing functions", default_return={})
def categorize_functions(functions: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize functions by type for easy discovery."""
    categories = {
        'handlers': [],
        'tests': [],
        'moderate_complex': [],      # 50-99 nodes
        'high_complex': [],          # 100-199 nodes  
        'critical_complex': [],      # 200+ nodes
        'undocumented': [],
        'special_methods': [],      # Special Python methods
        'other': []
    }
    for func in functions:
        if func['is_test']:
            categories['tests'].append(func)
        elif func['is_handler']:
            categories['handlers'].append(func)
        elif func['complexity'] >= CRITICAL_COMPLEXITY:
            categories['critical_complex'].append(func)
        elif func['complexity'] >= HIGH_COMPLEXITY:
            categories['high_complex'].append(func)
        elif func['complexity'] >= MODERATE_COMPLEXITY:
            categories['moderate_complex'].append(func)
        elif func['is_special']:
            # Special methods go to their own category
            categories['special_methods'].append(func)
        elif not func['docstring'].strip():
            # Only count as undocumented if not special and no documentation (traditional or decorator)
            categories['undocumented'].append(func)
        else:
            categories['other'].append(func)
    return categories


@handle_errors("printing function summary", default_return=None)
def print_summary(categories: Dict[str, List[Dict]]):
    logger.info("=== FUNCTION DISCOVERY SUMMARY ===")
    
    # Print complexity categories with clear descriptions
    complexity_categories = {
        'critical_complex': f"CRITICAL COMPLEXITY (>{CRITICAL_COMPLEXITY-1} nodes)",
        'high_complex': f"HIGH COMPLEXITY ({HIGH_COMPLEXITY}-{CRITICAL_COMPLEXITY-1} nodes)", 
        'moderate_complex': f"MODERATE COMPLEXITY ({MODERATE_COMPLEXITY}-{HIGH_COMPLEXITY-1} nodes)",
        'handlers': "HANDLERS/UTILITIES",
        'tests': "TESTS",
        'undocumented': "UNDOCUMENTED",
        'special_methods': "SPECIAL METHODS",
        'other': "OTHER"
    }
    
    for cat, funcs in categories.items():
        if cat in complexity_categories:
            logger.info(f"{complexity_categories[cat]} ({len(funcs)}):")
        else:
            logger.info(f"{cat.upper()} ({len(funcs)}):")
            
        for func in funcs[:10]:
            logger.info(f"  - {func['name']} (file: {Path(func['file']).name}, complexity: {func['complexity']})")
        if len(funcs) > 10:
            logger.info(f"  ...and {len(funcs)-10} more.")
    
    # Add summary of special methods excluded from undocumented count
    special_count = len(categories.get('special_methods', []))
    if special_count > 0:
        logger.info(f"Note: {special_count} special Python methods excluded from undocumented count")
    
    # Add complexity summary
    total_complex = (len(categories.get('moderate_complex', [])) + 
                    len(categories.get('high_complex', [])) + 
                    len(categories.get('critical_complex', [])))
    if total_complex > 0:
        logger.info(f"Complexity Summary: {total_complex} functions need attention")
        logger.info(f"  - Moderate: {len(categories.get('moderate_complex', []))} functions")
        logger.info(f"  - High: {len(categories.get('high_complex', []))} functions") 
        logger.info(f"  - Critical: {len(categories.get('critical_complex', []))} functions")


def validate_results(categories: Dict[str, List[Dict]]) -> bool:
    """
    Validate that the results are reasonable and not inflated.
    
    Args:
        categories: Categorized function results
        
    Returns:
        True if results are reasonable, False if they seem inflated
    """
    total_functions = sum(len(funcs) for funcs in categories.values())
    
    # Check for reasonable function counts
    if total_functions > 10000:  # Unreasonably high
        logger.warning(f"Total functions ({total_functions}) seems unreasonably high")
        return False
    
    # Check for inflated complexity counts
    complex_functions = (len(categories.get('moderate_complex', [])) + 
                        len(categories.get('high_complex', [])) + 
                        len(categories.get('critical_complex', [])))
    
    if complex_functions > total_functions * 0.8:  # More than 80% complex
        logger.warning(f"High percentage of complex functions ({complex_functions}/{total_functions})")
        return False
    
    # Check for reasonable critical complexity count
    critical_count = len(categories.get('critical_complex', []))
    if critical_count > total_functions * 0.3:  # More than 30% critical
        logger.warning(f"High percentage of critical complexity functions ({critical_count}/{total_functions})")
        return False
    
    return True

def main():
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Discover and categorize functions in the codebase')
    parser.add_argument('--include-tests', action='store_true', help='Include test files in analysis')
    parser.add_argument('--include-dev-tools', action='store_true', help='Include development_tools in analysis')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    args = parser.parse_args()
    
    logger.info("[SCAN] Scanning for all functions...")
    all_functions = scan_all_functions(
        include_tests=args.include_tests,
        include_dev_tools=args.include_dev_tools
    )
    logger.info(f"Found {len(all_functions)} functions.")
    categories = categorize_functions(all_functions)
    
    # Validate results before showing
    if not validate_results(categories):
        logger.warning("Results may be inflated. Check auto-generated code detection.")
    
    if args.json:
        # Output JSON for programmatic use
        metrics = {
            'total_functions': len(all_functions),
            'moderate_complexity': len(categories.get('moderate_complex', [])),
            'high_complexity': len(categories.get('high_complex', [])),
            'critical_complexity': len(categories.get('critical_complex', [])),
            'undocumented': len(categories.get('undocumented', [])),
            'handlers': len(categories.get('handlers', [])),
            'tests': len(categories.get('tests', [])),
            'utilities': len(categories.get('utilities', []))
        }
        print(json.dumps(metrics, indent=2))
    else:
        print_summary(categories)
        logger.info("Tip: Use this output to quickly find handlers, tests, complex, or undocumented functions.")

if __name__ == "__main__":
    main() 
