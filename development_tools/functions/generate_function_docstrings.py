#!/usr/bin/env python3
# TOOL_TIER: experimental

"""
Auto Document Functions - Automatically add docstrings to Python functions

This tool analyzes the codebase and automatically generates appropriate docstrings
for functions that lack documentation. It uses the same template generation logic as
the function registry generator to ensure consistency.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.
"""

import ast
import sys
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
try:
    from .. import config
except ImportError:
    from development_tools import config

from core.logger import get_component_logger
from core.time_utilities import now_timestamp_filename

logger = get_component_logger("development_tools")

# Load config at module level
AUTO_DOC_CONFIG = config.get_generate_function_docstrings_config()


def detect_function_type(
    file_path: str,
    func_name: str,
    decorators: List[str],
    args: List[str],
    function_type_detection: Optional[Dict[str, Any]] = None,
) -> str:
    """Detect the type of function for template generation using config rules."""
    if function_type_detection is None or not isinstance(function_type_detection, dict):
        function_type_detection = AUTO_DOC_CONFIG.get("function_type_detection", {})
    if not isinstance(function_type_detection, dict):
        function_type_detection = {}

    file_lower = file_path.lower()
    func_lower = func_name.lower()

    # Check config rules in order
    # Qt translation
    qt_translation = function_type_detection.get("qt_translation", {})
    if qt_translation:
        file_pattern = qt_translation.get("file_pattern", "")
        name = qt_translation.get("name", "")
        if (
            file_pattern
            and file_lower.startswith(file_pattern.lower())
            and func_name == name
        ):
            return "qt_translation"

    # UI generated
    ui_generated = function_type_detection.get("ui_generated", {})
    if ui_generated:
        file_pattern = ui_generated.get("file_pattern", "")
        names = ui_generated.get("names", [])
        if (
            file_pattern
            and file_lower.startswith(file_pattern.lower())
            and func_name in names
        ):
            return "ui_generated"

    # Test function
    test_function = function_type_detection.get("test_function", {})
    if test_function:
        name_patterns = test_function.get("name_patterns", [])
        for pattern in name_patterns:
            if pattern in func_lower or func_lower.startswith(pattern):
                return "test_function"

    # Special method
    special_method = function_type_detection.get("special_method", {})
    if special_method:
        name_pattern = special_method.get("name_pattern", "")
        if name_pattern:
            if re.match(name_pattern, func_name):
                return "special_method"

    # Constructor
    constructor = function_type_detection.get("constructor", {})
    if constructor:
        name = constructor.get("name", "")
        if func_name == name:
            return "constructor"

    # Main function
    main_function = function_type_detection.get("main_function", {})
    if main_function:
        name = main_function.get("name", "")
        if func_name == name:
            return "main_function"

    return "regular_function"


def generate_function_template(
    func_type: str,
    func_name: str,
    file_path: str,
    args: List[str],
    formatting_rules: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate appropriate documentation template based on function type using config."""
    if formatting_rules is None or not isinstance(formatting_rules, dict):
        formatting_rules = AUTO_DOC_CONFIG.get("formatting_rules", {})
    if not isinstance(formatting_rules, dict):
        formatting_rules = {}

    # Check for custom template in formatting_rules
    if func_type in formatting_rules:
        template = formatting_rules[func_type]
        # Simple template substitution
        template = template.replace("{func_name}", func_name)
        template = template.replace("{file_path}", file_path)
        return template

    # Fallback to default templates
    if func_type == "qt_translation":
        return '"""Auto-generated Qt translation function for internationalization support."""'

    elif func_type == "ui_generated":
        if func_name == "setupUi":
            ui_name = file_path.split("/")[-1].replace("_pyqt.py", "")
            return f'"""Auto-generated Qt UI setup function for {ui_name}."""'
        elif func_name == "retranslateUi":
            ui_name = file_path.split("/")[-1].replace("_pyqt.py", "")
            return f'"""Auto-generated Qt UI translation function for {ui_name}."""'
        else:
            ui_name = file_path.split("/")[-1].replace("_pyqt.py", "")
            return f'"""Auto-generated Qt UI function for {ui_name}."""'

    elif func_type == "test_function":
        # Extract test scenario from function name
        test_name = func_name.replace("test_", "").replace("_", " ")
        if "real_behavior" in func_name:
            return f'"""REAL BEHAVIOR TEST: {test_name.title()}."""'
        elif "integration" in func_name:
            return f'"""INTEGRATION TEST: {test_name.title()}."""'
        elif "unit" in func_name:
            return f'"""UNIT TEST: {test_name.title()}."""'
        else:
            return f'"""Test {test_name.title()}."""'

    elif func_type == "special_method":
        if func_name == "__init__":
            return '"""Initialize the object."""'
        elif func_name == "__new__":
            return '"""Create a new instance."""'
        elif func_name == "__post_init__":
            return '"""Post-initialization setup."""'
        elif func_name == "__enter__":
            return '"""Context manager entry."""'
        elif func_name == "__exit__":
            return '"""Context manager exit."""'
        else:
            return f'"""Special Python method: {func_name}."""'

    elif func_type == "constructor":
        return '"""Initialize the object."""'

    elif func_type == "main_function":
        return '"""Main entry point for the module."""'

    else:
        return '"""No description."""'


def add_docstring_to_function(
    file_path: str, func_name: str, line_number: int, docstring: str
) -> bool:
    """Add a docstring to a specific function in a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Start from the AST line number and look for the actual function definition
        start_line = line_number - 1  # Convert to 0-based index

        # Look for the function definition, which might be after decorators
        func_line = None
        for i in range(
            start_line, min(start_line + 5, len(lines))
        ):  # Look within 5 lines
            line = lines[i].strip()
            if line.startswith(f"def {func_name}("):
                func_line = i
                break
            elif line.startswith("@"):  # Skip decorators
                continue
            elif line.startswith("def "):  # Found a different function
                break

        if func_line is None:
            logger.warning(
                f"Could not find function {func_name} starting from line {line_number} in {file_path}"
            )
            return False

        # Check if function already has a docstring
        next_line_idx = func_line + 1
        if next_line_idx < len(lines):
            next_line = lines[next_line_idx].strip()
            if next_line.startswith('"""') or next_line.startswith("'''"):
                logger.info(
                    f"Function {func_name} in {file_path} already has a docstring"
                )
                return False

        # Find the start of the function body (first indented line after function definition)
        body_start = func_line + 1
        while body_start < len(lines):
            line = lines[body_start].strip()
            if line and not line.startswith("#"):  # Skip comments
                if line.startswith('"""') or line.startswith("'''"):
                    # Already has a docstring
                    logger.info(
                        f"Function {func_name} in {file_path} already has a docstring"
                    )
                    return False
                elif (
                    line.startswith("pass")
                    or line.startswith("return")
                    or line.startswith("raise")
                ):
                    # Function body starts here
                    break
                elif line and not line.startswith(" ") and not line.startswith("\t"):
                    # Non-indented line, not part of function body
                    break
            body_start += 1

        # Check if this is a one-liner function (function definition and body on same line)
        func_def_line = lines[func_line].strip()
        if ":" in func_def_line and (
            "return" in func_def_line
            or "pass" in func_def_line
            or "raise" in func_def_line
        ):
            # This is a one-liner function, we can't add a docstring inside it
            logger.info(
                f"Function {func_name} in {file_path} is a one-liner, cannot add docstring"
            )
            return False

        # Insert docstring at the beginning of the function body
        indent = len(lines[func_line]) - len(lines[func_line].lstrip())
        docstring_line = (
            " " * (indent + 4) + docstring + "\n"
        )  # Add 4 spaces for function body

        lines.insert(body_start, docstring_line)

        # Write back to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        logger.info(f"Added docstring to {func_name} in {file_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to add docstring to {func_name} in {file_path}: {e}")
        return False


def scan_and_document_functions(project_root_path: Optional[Path] = None):
    """Scan all Python files and add docstrings where missing."""
    global AUTO_DOC_CONFIG

    if project_root_path:
        project_root = project_root_path
    else:
        project_root = config.get_project_root()

    results = {
        "files_processed": 0,
        "functions_documented": 0,
        "functions_skipped": 0,
        "errors": 0,
    }

    # Get function type detection rules from config
    function_type_detection = AUTO_DOC_CONFIG.get("function_type_detection", {})
    formatting_rules = AUTO_DOC_CONFIG.get("formatting_rules", {})

    # Directories to scan from configuration
    scan_dirs = config.get_scan_directories()

    for scan_dir in scan_dirs:
        dir_path = project_root / scan_dir
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob("*.py"):
            relative_path = py_file.relative_to(project_root)
            file_key = str(relative_path).replace("\\", "/")

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Get function signature
                        args = [arg.arg for arg in node.args.args]

                        # Get decorators
                        decorators = []
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Name):
                                decorators.append(decorator.id)
                            elif isinstance(decorator, ast.Call):
                                if isinstance(decorator.func, ast.Name):
                                    decorators.append(decorator.func.id)

                        # Check if function already has a docstring
                        if ast.get_docstring(node):
                            results["functions_skipped"] += 1
                            continue

                        # Detect function type using config
                        func_type = detect_function_type(
                            file_key,
                            node.name,
                            decorators,
                            args,
                            function_type_detection,
                        )

                        # Only add templates for specific function types
                        if func_type in [
                            "qt_translation",
                            "ui_generated",
                            "test_function",
                            "special_method",
                            "constructor",
                            "main_function",
                        ]:
                            docstring = generate_function_template(
                                func_type, node.name, file_key, args, formatting_rules
                            )

                            if add_docstring_to_function(
                                str(py_file), node.name, node.lineno, docstring
                            ):
                                results["functions_documented"] += 1
                            else:
                                results["errors"] += 1

                results["files_processed"] += 1

            except Exception as e:
                logger.error(f"Failed to process {file_key}: {e}")
                results["errors"] += 1

    return results


def execute(
    project_root: Optional[str] = None, config_path: Optional[str] = None, **kwargs
) -> Dict:
    """Execute auto document functions (for use by run_development_tools)."""
    global AUTO_DOC_CONFIG

    # Load config if project_root or config_path provided
    if project_root or config_path:
        if config_path:
            config.load_external_config(config_path)
        # Reload config (project_root is handled via config file)
        AUTO_DOC_CONFIG = config.get_generate_function_docstrings_config()

    if project_root:
        project_root_path = Path(project_root).resolve()
    else:
        project_root_path = config.get_project_root()

    # Process functions
    results = scan_and_document_functions(project_root_path)

    return results


def main():
    """Main function to run the automatic documentation process."""
    logger.info("[AUTO-DOC] Starting automatic function documentation...")

    # Create backup before making changes
    project_root = Path(__file__).parent.parent
    backup_dir = project_root.parent / f"backup_auto_doc_{now_timestamp_filename()}"

    logger.info(f"Creating backup at {backup_dir}")
    try:
        import shutil

        shutil.copytree(project_root, backup_dir)
        logger.info("Backup created successfully")
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return

    # Process functions
    results = scan_and_document_functions()

    # Print results
    logger.info(f"[AUTO-DOC] Documentation process complete!")
    logger.info(f"[STATS] Results:")
    logger.info(f"   Files processed: {results['files_processed']}")
    logger.info(f"   Functions documented: {results['functions_documented']}")
    logger.info(
        f"   Functions skipped (already documented): {results['functions_skipped']}"
    )
    logger.info(f"   Errors: {results['errors']}")

    if results["functions_documented"] > 0:
        logger.info(
            f"[SUCCESS] Added docstrings to {results['functions_documented']} functions!"
        )
        logger.info(f"[NOTE] Backup available at: {backup_dir}")
    else:
        logger.info(
            f"[INFO] No new docstrings were added (all functions already documented or not eligible)"
        )


if __name__ == "__main__":
    main()
