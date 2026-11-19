#!/usr/bin/env python3
# TOOL_TIER: core

"""
Generate and update FUNCTION_REGISTRY.md automatically.
Scans all .py files and creates comprehensive function documentation.
Enhanced with automatic template generation for various function types.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.
"""

import sys
from pathlib import Path

# Ensure we can import from development_tools when run as a script (path bootstrap)
_functions_dir = Path(__file__).resolve().parent
_dev_tools_dir = _functions_dir.parent
if str(_dev_tools_dir) not in sys.path:
    sys.path.insert(0, str(_dev_tools_dir))

# Project root for core imports (development_tools/functions/ -> project root)
project_root = _dev_tools_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from development_tools.shared.logging import get_dev_tools_logger
from development_tools.shared.time_helpers import now_timestamp_full

# Import config for project name
try:
    from development_tools import config
except ImportError:
    sys.path.insert(0, str(project_root))
    from development_tools import config

# Load external config on module import
config.load_external_config()

logger = get_dev_tools_logger("development_tools")


def detect_function_type(
    file_path: str, func_name: str, decorators: list[str], args: list[str]
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
    func_type: str, func_name: str, file_path: str, args: list[str]
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
            return f"Test {test_name.title()}"

    elif func_type == "special_method":
        special_method_descriptions = {
            "__init__": "Initialize the object",
            "__new__": "Create a new instance",
            "__post_init__": "Post-initialization setup",
            "__enter__": "Context manager entry",
            "__exit__": "Context manager exit",
        }
        return special_method_descriptions.get(
            func_name, f"Special Python method: {func_name}"
        )

    elif func_type == "constructor":
        return "Initialize the object"

    elif func_type == "main_function":
        return "Main entry point for the module"

    else:
        return "No description"


# Import discovery and pattern analysis from decomposed tools
try:
    from .analyze_functions import scan_all_python_files
except ImportError:
    # Fallback for when run as script
    from development_tools.functions.analyze_functions import scan_all_python_files


def _registry_path() -> Path:
    """Resolve the detailed registry output relative to the host project."""
    root = Path(config.get_project_root()).resolve()
    return Path(config.get_analyze_function_registry_config(root)["registry_path"]).relative_to(root)


def generate_function_registry_content(actual_functions: dict[str, dict]) -> str:
    """Generate the complete FUNCTION_REGISTRY_DETAIL.md content."""

    # Calculate statistics
    total_files = len(actual_functions)
    total_functions = sum(data["total_functions"] for data in actual_functions.values())
    total_classes = sum(data["total_classes"] for data in actual_functions.values())
    total_methods = sum(
        len(cls["methods"])
        for data in actual_functions.values()
        for cls in data["classes"]
    )

    # Function documentation stats
    documented_functions = sum(
        1
        for data in actual_functions.values()
        for func in data["functions"]
        if func["has_docstring"]
    )
    template_functions = sum(
        1
        for data in actual_functions.values()
        for func in data["functions"]
        if func.get("has_template", False)
    )

    # Method documentation stats
    documented_methods = sum(
        1
        for data in actual_functions.values()
        for cls in data["classes"]
        for method in cls["methods"]
        if method["has_docstring"]
    )
    template_methods = sum(
        1
        for data in actual_functions.values()
        for cls in data["classes"]
        for method in cls["methods"]
        if method.get("has_template", False)
    )

    # Class documentation stats
    documented_classes = sum(
        1
        for data in actual_functions.values()
        for cls in data["classes"]
        if cls["docstring"]
    )

    # Total coverage
    total_items = total_functions + total_methods
    documented_items = documented_functions + documented_methods
    template_items = template_functions + template_methods
    coverage_percentage = (
        (documented_items / total_items * 100) if total_items > 0 else 0
    )

    # Get project name from config
    project_name = config.get_project_name("Project")

    # Generate header
    generated_at = now_timestamp_full()
    content = f"""# Function Registry - {project_name} Project

> **File**: `{_registry_path().as_posix()}`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: {generated_at}
> **Source**: `python development_tools/generate_function_registry.py` - Function Registry Generator
> **Audience**: Human developer and AI collaborators  
> **Purpose**: Complete registry of all functions and classes in the {project_name} codebase  
> **Status**: **ACTIVE** - Auto-generated from codebase analysis with template enhancement

> **See [README.md](../README.md) for complete navigation and project overview**
> **See [ARCHITECTURE.md](../ARCHITECTURE.md) for system architecture and design**
> **See [TODO.md](../TODO.md) for current documentation priorities**

## Overview

### **Function Documentation Coverage: {coverage_percentage:.1f}% {'[OK] COMPLETED' if coverage_percentage >= 95 else '[WARNING] NEEDS ATTENTION' if coverage_percentage >= 50 else '[ERROR] CRITICAL GAP'}**
- **Files Scanned**: {total_files}
- **Functions Found**: {total_functions}
- **Methods Found**: {total_methods}
- **Classes Found**: {total_classes}
- **Total Items**: {total_items}
- **Functions Documented**: {documented_functions}
- **Methods Documented**: {documented_methods}
- **Classes Documented**: {documented_classes}
- **Total Documented**: {documented_items}
- **Template-Generated**: {template_items}
- **Last Updated**: {now_timestamp_full().split(" ")[0]}

**Status**: {'[OK] **EXCELLENT** - All functions have proper documentation' if coverage_percentage >= 95 else '[WARNING] **GOOD** - Most functions documented, some gaps remain' if coverage_percentage >= 50 else '[ERROR] **CRITICAL GAP** - Many functions lack documentation'}

**Template Enhancement**: This registry now includes automatic template generation for:
- **Auto-generated Qt functions** (qtTrId, setupUi, retranslateUi)
- **Test functions** (with scenario-based descriptions)
- **Special Python methods** (__init__, __new__, __post_init__, etc.)
- **Constructor methods** and **main functions**

**Note**: This registry is automatically generated from the actual codebase. Functions without docstrings are marked as needing documentation. Template-generated documentation is applied to improve coverage.

## Function Categories

### **Core System Functions** ({sum(data['total_functions'] for file_path, data in actual_functions.items() if file_path.startswith('core/'))})
Core system utilities, configuration, error handling, and data management functions.

### **Communication Functions** ({sum(data['total_functions'] for file_path, data in actual_functions.items() if file_path.startswith('communication/'))})
Bot implementations, channel management, and communication utilities.

### **User Interface Functions** ({sum(data['total_functions'] for file_path, data in actual_functions.items() if file_path.startswith('ui/'))})
UI dialogs, widgets, and user interaction functions.

### **User Management Functions** ({sum(data['total_functions'] for file_path, data in actual_functions.items() if file_path.startswith('user/'))})
User context, preferences, and data management functions.

### **Task Management Functions** ({sum(data['total_functions'] for file_path, data in actual_functions.items() if file_path.startswith('tasks/'))})
Task management and scheduling functions.

### **Test Functions** ({sum(data['total_functions'] for file_path, data in actual_functions.items() if file_path.startswith('tests/'))})
Test functions and testing utilities.

## Module Organization

"""

    # Group files by directory
    dir_files = {}
    for file_path, data in actual_functions.items():
        dir_name = file_path.split("/")[0] if "/" in file_path else "root"
        if dir_name not in dir_files:
            dir_files[dir_name] = []
        dir_files[dir_name].append((file_path, data))

    # Generate content for each directory
    for dir_name in sorted(dir_files.keys()):
        content += f"### `{dir_name}/` - {get_directory_description(dir_name)}\n\n"

        for file_path, data in sorted(dir_files[dir_name], key=lambda x: x[0]):
            content += generate_file_section(file_path, data)

    return content


def get_directory_description(dir_name: str) -> str:
    """Get a description for a directory."""
    descriptions = {
        "core": "Core System Modules",
        "communication": "Communication Channel Implementations",
        "ui": "User Interface Components",
        "user": "User Data and Context",
        "tasks": "Task Management",
        "tests": "Test Files",
        "root": "Root Files",
    }
    return descriptions.get(dir_name, "Unknown Directory")


def generate_file_section(file_path: str, data: dict) -> str:
    """Generate a section for a single file."""
    content = f"#### `{file_path}`\n"

    # Functions
    if data["functions"]:
        content += "**Functions:**\n"
        for func in sorted(data["functions"], key=lambda x: x["name"]):
            args_str = ", ".join(func["args"])
            doc_status = "[OK]" if func["has_docstring"] else "[MISSING]"
            content += f"- {doc_status} `{func['name']}({args_str})` - {func['docstring'] or 'No description'}\n"

    # Classes
    if data["classes"]:
        content += "**Classes:**\n"
        for cls in sorted(data["classes"], key=lambda x: x["name"]):
            doc_status = "[OK]" if cls["docstring"] else "[MISSING]"
            content += f"- {doc_status} `{cls['name']}` - {cls['docstring'] or 'No description'}\n"
            for method in sorted(cls["methods"], key=lambda x: x["name"]):
                args_str = ", ".join(method["args"])
                method_doc_status = "[OK]" if method["has_docstring"] else "[MISSING]"
                content += f"  - {method_doc_status} `{cls['name']}.{method['name']}({args_str})` - {method['docstring'] or 'No description'}\n"

    content += "\n"
    return content


def update_function_registry():
    """Update the detailed function inventory from current codebase analysis."""
    logger.debug("[SCAN] Scanning all Python files...")
    actual_functions = scan_all_python_files()

    logger.info("[GEN] Generating FUNCTION_REGISTRY_DETAIL.md content...")
    detail_content = generate_function_registry_content(actual_functions)

    # Write DETAIL file with rotation
    from development_tools.shared.file_rotation import create_output_file

    project_root = Path(config.get_project_root()).resolve()
    detail_path = _registry_path()
    create_output_file(
        str(detail_path),
        detail_content,
        rotate=True,
        max_versions=7,
        project_root=project_root,
    )

    # Calculate statistics
    total_files = len(actual_functions)
    total_functions = sum(data["total_functions"] for data in actual_functions.values())
    total_methods = sum(
        len(cls["methods"])
        for data in actual_functions.values()
        for cls in data["classes"]
    )

    # Function documentation stats
    documented_functions = sum(
        1
        for data in actual_functions.values()
        for func in data["functions"]
        if func["has_docstring"]
    )
    template_functions = sum(
        1
        for data in actual_functions.values()
        for func in data["functions"]
        if func.get("has_template", False)
    )

    # Method documentation stats
    documented_methods = sum(
        1
        for data in actual_functions.values()
        for cls in data["classes"]
        for method in cls["methods"]
        if method["has_docstring"]
    )
    template_methods = sum(
        1
        for data in actual_functions.values()
        for cls in data["classes"]
        for method in cls["methods"]
        if method.get("has_template", False)
    )

    # Total coverage
    total_items = total_functions + total_methods
    documented_items = documented_functions + documented_methods
    template_items = template_functions + template_methods
    coverage_percentage = (
        (documented_items / total_items * 100) if total_items > 0 else 0
    )

    logger.info("[SUCCESS] Detailed function registry updated successfully!")
    logger.info("[FILES] Generated:")
    logger.info(
        f"   {detail_path.as_posix()} - Complete detailed registry"
    )
    logger.info("[STATS] Statistics:")
    logger.info(f"   Files scanned: {total_files}")
    logger.info(f"   Functions found: {total_functions}")
    logger.info(f"   Methods found: {total_methods}")
    logger.info(f"   Total items: {total_items}")
    logger.info(f"   Functions documented: {documented_functions}")
    logger.info(f"   Methods documented: {documented_methods}")
    logger.info(f"   Total documented: {documented_items}")
    logger.info(f"   Template-generated: {template_items}")
    logger.info(f"   Coverage: {coverage_percentage:.1f}%")
    logger.info(f"   Detail file: {detail_path}")

    # Template breakdown
    if template_items > 0:
        logger.info("[TEMPLATES] Template Breakdown:")
        template_types = {}
        for data in actual_functions.values():
            for func in data["functions"]:
                if func.get("has_template", False):
                    func_type = func.get("func_type", "unknown")
                    template_types[func_type] = template_types.get(func_type, 0) + 1
            for cls in data["classes"]:
                for method in cls["methods"]:
                    if method.get("has_template", False):
                        method_type = method.get("method_type", "unknown")
                        template_types[method_type] = (
                            template_types.get(method_type, 0) + 1
                        )

        for template_type, count in sorted(template_types.items()):
            logger.info(f"   {template_type}: {count}")


if __name__ == "__main__":
    update_function_registry()
