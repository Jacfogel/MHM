#!/usr/bin/env python3
# TOOL_TIER: core

"""
analyze_functions.py
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
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.error_handling import handle_errors
from core.logger import get_component_logger

# Handle both relative and absolute imports
try:
    from .. import config  # Go up one level from functions/ to development_tools/
    from ..shared.standard_exclusions import should_exclude_file
    from ..shared.exclusion_utilities import (
        is_auto_generated_code,
        is_special_python_method,
        is_test_function,
    )
except ImportError:
    from development_tools import config
    from development_tools.shared.standard_exclusions import should_exclude_file
    from development_tools.shared.exclusion_utilities import (
        is_auto_generated_code,
        is_special_python_method,
        is_test_function,
    )

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


def _get_analyze_functions_config() -> Dict:
    """Get analyze functions config from config module."""
    return config.get_analyze_functions_config()


# Load config values
PROJECT_ROOT = _get_project_root()
SCAN_DIRECTORIES = _get_scan_directories()
FUNCTION_DISCOVERY_CONFIG = _get_analyze_functions_config()
HANDLER_KEYWORDS = FUNCTION_DISCOVERY_CONFIG.get(
    "handler_keywords", ["handle", "process", "validate"]
)
TEST_KEYWORDS = FUNCTION_DISCOVERY_CONFIG.get("test_keywords", ["test_", "test"])
MODERATE_COMPLEXITY = FUNCTION_DISCOVERY_CONFIG.get("moderate_complexity_threshold", 50)
HIGH_COMPLEXITY = FUNCTION_DISCOVERY_CONFIG.get("high_complexity_threshold", 100)
CRITICAL_COMPLEXITY = FUNCTION_DISCOVERY_CONFIG.get(
    "critical_complexity_threshold", 200
)


# Note: is_auto_generated_code, is_special_python_method, and is_test_function
# are now imported from shared.exclusion_utilities for consistency across tools.


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
            if (
                isinstance(decorator.func, ast.Name)
                and decorator.func.id == "handle_errors"
            ):
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    documentation.append(f"@handle_errors: {decorator.args[0].value}")
            elif (
                isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "handle_errors"
            ):
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    documentation.append(f"@handle_errors: {decorator.args[0].value}")

        # Handle @error_handler("description")
        elif isinstance(decorator, ast.Call):
            if (
                isinstance(decorator.func, ast.Name)
                and decorator.func.id == "error_handler"
            ):
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    documentation.append(f"@error_handler: {decorator.args[0].value}")
            elif (
                isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "error_handler"
            ):
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    documentation.append(f"@error_handler: {decorator.args[0].value}")

    return "; ".join(documentation)


def detect_function_type(
    file_path: str, func_name: str, decorators: List[str], args: List[str]
) -> str:
    """Detect the type of function for template generation."""
    file_lower = file_path.lower()
    func_lower = func_name.lower()

    # Auto-generated Qt functions
    if file_lower.startswith("ui/generated/") and func_name == "qtTrId":
        return "qt_translation"

    # Auto-generated UI setup functions
    if file_lower.startswith("ui/generated/") and func_name in [
        "setupUi",
        "retranslateUi",
    ]:
        return "ui_generated"

    # Test functions
    if func_lower.startswith("test_") or "test" in func_lower:
        return "test_function"

    # Special Python methods
    if func_name.startswith("__") and func_name.endswith("__"):
        return "special_method"

    # Constructor methods
    if func_name == "__init__":
        return "constructor"

    # Main functions
    if func_name == "main":
        return "main_function"

    return "regular_function"


def generate_function_template(
    func_type: str, func_name: str, file_path: str, args: List[str]
) -> str:
    """Generate appropriate documentation template based on function type."""

    if func_type == "qt_translation":
        return "Auto-generated Qt translation function for internationalization support"

    elif func_type == "ui_generated":
        if func_name == "setupUi":
            return f"Auto-generated Qt UI setup function for {file_path.split('/')[-1].replace('_pyqt.py', '')}"
        elif func_name == "retranslateUi":
            return f"Auto-generated Qt UI translation function for {file_path.split('/')[-1].replace('_pyqt.py', '')}"
        else:
            return f"Auto-generated Qt UI function for {file_path.split('/')[-1].replace('_pyqt.py', '')}"

    elif func_type == "test_function":
        # Extract test scenario from function name
        test_name = func_name.replace("test_", "").replace("_", " ")
        if "real_behavior" in func_name:
            return f"REAL BEHAVIOR TEST: {test_name.title()}"
        elif "integration" in func_name:
            return f"INTEGRATION TEST: {test_name.title()}"
        elif "unit" in func_name:
            return f"UNIT TEST: {test_name.title()}"
        else:
            return f"TEST: {test_name.title()}"

    elif func_type == "special_method":
        return "Special Python method"

    elif func_type == "constructor":
        return "Initialize the object"

    elif func_type == "main_function":
        return "Main entry point for the module"

    else:
        return "No description"


@handle_errors("extracting functions from file", default_return=[])
def extract_functions(file_path: str) -> List[Dict]:
    """Extract all function definitions from a Python file."""
    # Note: Exclusion logic is handled in scan_all_python_files() before calling this function.
    # This function processes any file passed to it (including test fixtures and files in tests/),
    # so we don't apply exclusions here. This allows tests to pass file paths directly.

    # Normalize path to handle both string and Path objects, and Windows/Unix path separators
    from pathlib import Path

    file_path_obj = Path(file_path)
    # Resolve the path (handles relative paths, symlinks, etc.)
    # This is safe even if the file doesn't exist yet - resolve() just normalizes the path
    try:
        file_path = str(file_path_obj.resolve())
    except (OSError, RuntimeError):
        # If resolve fails (e.g., broken symlink), use the path as-is
        file_path = str(file_path_obj)

    functions = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
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
                decorator_docstring = extract_decorator_documentation(
                    node.decorator_list
                )

                # Combine both types of documentation
                combined_docstring = traditional_docstring
                if decorator_docstring:
                    if combined_docstring:
                        combined_docstring += f" | {decorator_docstring}"
                    else:
                        combined_docstring = decorator_docstring

                decorators = [
                    (
                        d.id
                        if isinstance(d, ast.Name)
                        else (
                            d.func.id
                            if isinstance(d, ast.Call) and isinstance(d.func, ast.Name)
                            else str(d)
                        )
                    )
                    for d in node.decorator_list
                ]
                complexity = len(list(ast.walk(node)))
                is_handler = any(k in name.lower() for k in HANDLER_KEYWORDS)
                is_test = is_test_function(name, file_path)
                is_special = is_special_python_method(name, complexity)

                functions.append(
                    {
                        "name": name,
                        "args": args,
                        "docstring": combined_docstring,
                        "traditional_docstring": traditional_docstring,
                        "decorator_docstring": decorator_docstring,
                        "decorators": decorators,
                        "complexity": complexity,
                        "is_handler": is_handler,
                        "is_test": is_test,
                        "is_special": is_special,
                        "file": file_path,
                    }
                )
    except Exception as e:
        # Log errors to help debug test failures
        logger.error(f"Error parsing {file_path}: {e}", exc_info=True)
    return functions


@handle_errors("extracting functions from file for registry", default_return=[])
def extract_functions_from_file(file_path: str) -> List[Dict]:
    """Extract all function definitions from a Python file (registry format with templates)."""
    # Note: Exclusion logic is handled in scan_all_python_files() before calling this function.
    # This function processes any file passed to it (including test fixtures and files in tests/),
    # so we don't apply exclusions here. This allows tests to pass file paths directly.

    # Normalize path to handle both string and Path objects, and Windows/Unix path separators
    from pathlib import Path

    file_path_obj = Path(file_path)
    # Resolve the path (handles relative paths, symlinks, etc.)
    # This is safe even if the file doesn't exist yet - resolve() just normalizes the path
    try:
        file_path = str(file_path_obj.resolve())
    except (OSError, RuntimeError):
        # If resolve fails (e.g., broken symlink), use the path as-is
        file_path = str(file_path_obj)

    functions = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
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

                # Detect function type
                func_type = detect_function_type(file_path, node.name, decorators, args)

                # Generate template if no docstring exists
                if not docstring.strip() and func_type != "regular_function":
                    docstring = generate_function_template(
                        func_type, node.name, file_path, args
                    )

                # Check if it's a test function
                is_test = node.name.startswith("test_") or "test" in node.name.lower()

                # Check if it's a main function
                is_main = node.name == "main" or node.name == "__main__"

                # Get function complexity (rough estimate)
                complexity = len(list(ast.walk(node)))

                # Check if it's a handler/utility function
                is_handler = any(
                    keyword in node.name.lower()
                    for keyword in [
                        "handle",
                        "process",
                        "validate",
                        "check",
                        "get",
                        "set",
                        "save",
                        "load",
                    ]
                )

                functions.append(
                    {
                        "name": node.name,
                        "line": node.lineno,
                        "args": args,
                        "decorators": decorators,
                        "docstring": docstring,
                        "func_type": func_type,
                        "is_test": is_test,
                        "is_main": is_main,
                        "complexity": complexity,
                        "has_docstring": bool(docstring.strip()),
                        "is_handler": is_handler,
                        "arg_count": len(args),
                        "has_template": func_type != "regular_function"
                        and not ast.get_docstring(node),
                    }
                )

    except Exception as e:
        # Only log errors for non-excluded files (excluded files are skipped above)
        logger.error(f"Error parsing {file_path}: {e}")

    return functions


@handle_errors("extracting classes from file", default_return=[])
def extract_classes_from_file(file_path: str) -> List[Dict]:
    """Extract all class definitions from a Python file."""
    # Note: Exclusion logic is handled in scan_all_python_files() before calling this function.
    # This function processes any file passed to it (including test fixtures and files in tests/),
    # so we don't apply exclusions here. This allows tests to pass file paths directly.

    # Normalize path to handle both string and Path objects, and Windows/Unix path separators
    from pathlib import Path

    file_path_obj = Path(file_path)
    # Resolve the path (handles relative paths, symlinks, etc.)
    # This is safe even if the file doesn't exist yet - resolve() just normalizes the path
    try:
        file_path = str(file_path_obj.resolve())
    except (OSError, RuntimeError):
        # If resolve fails (e.g., broken symlink), use the path as-is
        file_path = str(file_path_obj)

    classes = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Get class methods
                methods = []
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        # Get method arguments
                        args = [arg.arg for arg in child.args.args]

                        # Get decorators
                        decorators = []
                        for d in child.decorator_list:
                            if isinstance(d, ast.Name):
                                decorators.append(d.id)
                            elif isinstance(d, ast.Call) and isinstance(
                                d.func, ast.Name
                            ):
                                decorators.append(d.func.id)
                            else:
                                decorators.append(str(d))

                        # Get original docstring
                        original_docstring = ast.get_docstring(child)

                        # Detect method type
                        method_type = detect_function_type(
                            file_path, child.name, decorators, args
                        )

                        # Generate template if no docstring exists
                        docstring = original_docstring or ""
                        if not docstring.strip() and method_type != "regular_function":
                            docstring = generate_function_template(
                                method_type, child.name, file_path, args
                            )

                        methods.append(
                            {
                                "name": child.name,
                                "line": child.lineno,
                                "args": args,
                                "decorators": decorators,
                                "docstring": docstring,
                                "method_type": method_type,
                                "has_docstring": bool(docstring.strip()),
                                "has_template": method_type != "regular_function"
                                and not original_docstring,
                            }
                        )

                class_docstring = ast.get_docstring(node) or ""
                classes.append(
                    {
                        "name": node.name,
                        "line": node.lineno,
                        "methods": methods,
                        "docstring": class_docstring,
                        "has_docstring": bool(class_docstring.strip()),
                    }
                )

    except Exception as e:
        # Only log errors for non-excluded files (excluded files are skipped above)
        logger.error(f"Error parsing {file_path}: {e}")

    return classes


@handle_errors("scanning all Python files", default_return={})
def scan_all_python_files() -> Dict[str, Dict]:
    """Scan all Python files in the project and extract function/class information."""
    # Import config - check if we're running as part of a package to avoid __package__ != __spec__.parent warnings
    if __name__ != "__main__" and __package__ and "." in __package__:
        from .. import config  # Go up one level from functions/ to development_tools/
    else:
        from development_tools import config
    # Ensure external config is loaded
    config.load_external_config()
    from development_tools.shared.standard_exclusions import should_exclude_file

    project_root = Path(config.get_project_root())
    results = {}

    # Directories to scan from configuration
    scan_dirs = config.get_scan_directories()

    for scan_dir in scan_dirs:
        dir_path = project_root / scan_dir
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob("*.py"):
            # Use production context exclusions to match audit behavior
            if should_exclude_file(str(py_file), "analysis", "production"):
                continue

            relative_path = py_file.relative_to(project_root)
            file_key = str(relative_path).replace("\\", "/")

            functions = extract_functions_from_file(str(py_file))
            classes = extract_classes_from_file(str(py_file))

            results[file_key] = {
                "functions": functions,
                "classes": classes,
                "total_functions": len(functions),
                "total_classes": len(classes),
            }

    # Also scan root directory for .py files
    # Get key files from config (entry points that should be included)
    key_files = config.get_project_key_files([])
    key_file_names = [Path(f).name for f in key_files] if key_files else []

    # Always exclude generator scripts
    exclude_generators = [
        "generate_function_registry.py",
        "generate_module_dependencies.py",
    ]

    for py_file in project_root.glob("*.py"):
        if py_file.name in exclude_generators:
            continue
        # Include key files (entry points) in registry even though they might be in exclusions
        # They are important entry points and should be documented
        if key_file_names and py_file.name in key_file_names:
            file_key = py_file.name
            functions = extract_functions_from_file(str(py_file))
            classes = extract_classes_from_file(str(py_file))
            results[file_key] = {
                "functions": functions,
                "classes": classes,
                "total_functions": len(functions),
                "total_classes": len(classes),
            }
            continue
        # Use production context exclusions to match audit behavior
        if should_exclude_file(str(py_file), "analysis", "production"):
            continue
        file_key = py_file.name

        functions = extract_functions_from_file(str(py_file))
        classes = extract_classes_from_file(str(py_file))

        results[file_key] = {
            "functions": functions,
            "classes": classes,
            "total_functions": len(functions),
            "total_classes": len(classes),
        }

    return results


@handle_errors("scanning all functions", default_return=[])
def scan_all_functions(
    include_tests: bool = False,
    include_dev_tools: bool = False,
    scan_directories: List[str] = None,
    project_root: Path = None,
) -> List[Dict]:
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
    if include_tests and "tests" not in scan_dirs:
        scan_dirs.append("tests")
    if include_dev_tools and "development_tools" not in scan_dirs:
        scan_dirs.append("development_tools")

    # Determine context based on configuration
    if include_tests and include_dev_tools:
        context = "development"  # Include everything
    elif include_tests or include_dev_tools:
        context = "development"  # More permissive
    else:
        context = "production"  # Exclude tests and dev tools

    # Scan configured directories
    for scan_dir in scan_dirs:
        dir_path = root / scan_dir
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob("*.py"):
            # Use context-based exclusions
            if not should_exclude_file(str(py_file), "analysis", context):
                all_functions.extend(extract_functions(str(py_file)))

    # Also scan root directory
    for py_file in root.glob("*.py"):
        # Use context-based exclusions
        if not should_exclude_file(str(py_file), "analysis", context):
            all_functions.extend(extract_functions(str(py_file)))

    return all_functions


@handle_errors("categorizing functions", default_return={})
def categorize_functions(functions: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize functions by type for easy discovery."""
    categories = {
        "handlers": [],
        "tests": [],
        "moderate_complex": [],  # 50-99 nodes
        "high_complex": [],  # 100-199 nodes
        "critical_complex": [],  # 200+ nodes
        "undocumented": [],
        "special_methods": [],  # Special Python methods
        "other": [],
    }
    for func in functions:
        if func["is_test"]:
            categories["tests"].append(func)
        elif func["is_handler"]:
            categories["handlers"].append(func)
        elif func["complexity"] >= CRITICAL_COMPLEXITY:
            categories["critical_complex"].append(func)
        elif func["complexity"] >= HIGH_COMPLEXITY:
            categories["high_complex"].append(func)
        elif func["complexity"] >= MODERATE_COMPLEXITY:
            categories["moderate_complex"].append(func)
        elif func["is_special"]:
            # Special methods go to their own category
            categories["special_methods"].append(func)
        elif not func["docstring"].strip():
            # Only count as undocumented if not special and no documentation (traditional or decorator)
            categories["undocumented"].append(func)
        else:
            categories["other"].append(func)
    return categories


@handle_errors("printing function summary", default_return=None)
def print_summary(categories: Dict[str, List[Dict]]):
    logger.info("=== FUNCTION DISCOVERY SUMMARY ===")

    # Print complexity categories with clear descriptions
    complexity_categories = {
        "critical_complex": f"CRITICAL COMPLEXITY (>{CRITICAL_COMPLEXITY-1} nodes)",
        "high_complex": f"HIGH COMPLEXITY ({HIGH_COMPLEXITY}-{CRITICAL_COMPLEXITY-1} nodes)",
        "moderate_complex": f"MODERATE COMPLEXITY ({MODERATE_COMPLEXITY}-{HIGH_COMPLEXITY-1} nodes)",
        "handlers": "HANDLERS/UTILITIES",
        "tests": "TESTS",
        "undocumented": "UNDOCUMENTED",
        "special_methods": "SPECIAL METHODS",
        "other": "OTHER",
    }

    for cat, funcs in categories.items():
        if cat in complexity_categories:
            logger.info(f"{complexity_categories[cat]} ({len(funcs)}):")
        else:
            logger.info(f"{cat.upper()} ({len(funcs)}):")

        for func in funcs[:10]:
            logger.info(
                f"  - {func['name']} (file: {Path(func['file']).name}, complexity: {func['complexity']})"
            )
        if len(funcs) > 10:
            logger.info(f"  ...and {len(funcs)-10} more.")

    # Add summary of special methods excluded from undocumented count
    special_count = len(categories.get("special_methods", []))
    if special_count > 0:
        logger.info(
            f"Note: {special_count} special Python methods excluded from undocumented count"
        )

    # Add complexity summary
    total_complex = (
        len(categories.get("moderate_complex", []))
        + len(categories.get("high_complex", []))
        + len(categories.get("critical_complex", []))
    )
    if total_complex > 0:
        logger.info(f"Complexity Summary: {total_complex} functions need attention")
        logger.info(
            f"  - Moderate: {len(categories.get('moderate_complex', []))} functions"
        )
        logger.info(f"  - High: {len(categories.get('high_complex', []))} functions")
        logger.info(
            f"  - Critical: {len(categories.get('critical_complex', []))} functions"
        )


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
    complex_functions = (
        len(categories.get("moderate_complex", []))
        + len(categories.get("high_complex", []))
        + len(categories.get("critical_complex", []))
    )

    if complex_functions > total_functions * 0.8:  # More than 80% complex
        logger.warning(
            f"High percentage of complex functions ({complex_functions}/{total_functions})"
        )
        return False

    # Check for reasonable critical complexity count
    critical_count = len(categories.get("critical_complex", []))
    if critical_count > total_functions * 0.3:  # More than 30% critical
        logger.warning(
            f"High percentage of critical complexity functions ({critical_count}/{total_functions})"
        )
        return False

    return True


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Discover and categorize functions in the codebase"
    )
    parser.add_argument(
        "--include-tests", action="store_true", help="Include test files in analysis"
    )
    parser.add_argument(
        "--include-dev-tools",
        action="store_true",
        help="Include development_tools in analysis",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    logger.info("[SCAN] Scanning for all functions...")
    all_functions = scan_all_functions(
        include_tests=args.include_tests, include_dev_tools=args.include_dev_tools
    )
    logger.info(f"Found {len(all_functions)} functions.")
    categories = categorize_functions(all_functions)

    # Validate results before showing
    if not validate_results(categories):
        logger.warning("Results may be inflated. Check auto-generated code detection.")

    if args.json:
        # Output JSON for programmatic use
        # Prepare examples for JSON output (top 5 by complexity)
        undocumented_list = categories.get("undocumented", [])
        undocumented_examples = []
        if undocumented_list:
            # Sort by complexity (descending) and take top 5
            sorted_undoc = sorted(
                undocumented_list, key=lambda x: x.get("complexity", 0), reverse=True
            )[:5]
            undocumented_examples = [
                {
                    "name": func.get("name", "unknown"),
                    "function": func.get("name", "unknown"),
                    "file": func.get("file", ""),
                    "complexity": func.get("complexity", 0),
                }
                for func in sorted_undoc
            ]

        # Calculate total issues (complexity issues + undocumented)
        moderate_complexity = len(categories.get("moderate_complex", []))
        high_complexity = len(categories.get("high_complex", []))
        critical_complexity = len(categories.get("critical_complex", []))
        undocumented = len(undocumented_list)
        total_issues = (
            moderate_complexity + high_complexity + critical_complexity + undocumented
        )

        # Return standard format
        metrics = {
            "summary": {
                "total_issues": total_issues,
                "files_affected": 0,  # Not file-based
            },
            "details": {
                "total_functions": len(all_functions),
                "moderate_complexity": moderate_complexity,
                "high_complexity": high_complexity,
                "critical_complexity": critical_complexity,
                "undocumented": undocumented,
                "undocumented_examples": undocumented_examples,
                "handlers": len(categories.get("handlers", [])),
                "tests": len(categories.get("tests", [])),
                "utilities": len(categories.get("utilities", [])),
            },
        }
        print(json.dumps(metrics, indent=2))
    else:
        print_summary(categories)
        logger.info(
            "Tip: Use this output to quickly find handlers, tests, complex, or undocumented functions."
        )


if __name__ == "__main__":
    main()
