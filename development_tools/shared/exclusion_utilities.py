#!/usr/bin/env python3
# TOOL_TIER: core

"""
Shared Exclusion Utilities for Analysis Tools

This module provides standardized exclusion utilities that can be reused
across all development tools to ensure consistent function and code filtering.

These utilities complement the file-level exclusions in standard_exclusions.py
by providing function-level and code-level exclusion logic.

Usage:
    from development_tools.shared.exclusion_utilities import (
        is_auto_generated_code,
        is_special_python_method,
        is_test_function
    )

    if is_auto_generated_code(file_path, func_name):
        # Skip this function
"""

from typing import Optional
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("development_tools")

# Default test keywords (can be overridden via config)
_DEFAULT_TEST_KEYWORDS = ["test_", "test"]


def _get_test_keywords():
    """Get test keywords from config or return defaults."""
    try:
        from .. import config

        config.load_external_config()
        function_config = config.get_analyze_functions_config()
        return function_config.get("test_keywords", _DEFAULT_TEST_KEYWORDS)
    except (ImportError, AttributeError):
        return _DEFAULT_TEST_KEYWORDS


@handle_errors("checking if code is auto-generated", default_return=False)
def is_auto_generated_code(file_path: str, func_name: str) -> bool:
    """
    Determine if a function is in auto-generated code that should be excluded from analysis.

    This function identifies:
    - PyQt auto-generated files and functions
    - Files in generated directories
    - Functions with auto-generated naming patterns

    Args:
        file_path: Path to the file containing the function
        func_name: Name of the function

    Returns:
        True if the function should be excluded from analysis
    """
    # Exclude PyQt auto-generated files
    if "generated" in file_path and "_pyqt.py" in file_path:
        return True

    # Exclude specific auto-generated function patterns
    auto_generated_patterns = {
        "setupUi",  # PyQt UI setup functions
        "retranslateUi",  # PyQt translation functions
        "setup_ui",  # Alternative PyQt setup
        "retranslate_ui",  # Alternative PyQt translation
    }

    if func_name in auto_generated_patterns:
        return True

    # Exclude files in generated directories
    if "/generated/" in file_path or "\\generated\\" in file_path:
        return True

    # Exclude files with auto-generated patterns in name
    auto_generated_file_patterns = [
        "_pyqt.py",  # PyQt generated files
        "_ui.py",  # UI generated files
        "_generated.py",  # Explicitly generated files
        "_auto.py",  # Auto-generated files
    ]

    for pattern in auto_generated_file_patterns:
        if file_path.endswith(pattern):
            return True

    # Exclude functions with auto-generated naming patterns
    auto_generated_func_patterns = [
        "setup_ui_",  # UI setup functions
        "retranslate_ui_",  # UI translation functions
        "_generated_",  # Functions with generated in name
        "_auto_",  # Functions with auto in name
    ]

    for pattern in auto_generated_func_patterns:
        if pattern in func_name:
            return True

    return False


@handle_errors("checking if method is special Python method", default_return=False)
def is_special_python_method(func_name: str, complexity: Optional[int] = None) -> bool:
    """
    Determine if a function is a special Python method that should be excluded from undocumented count.

    Special methods are Python's "magic methods" that have well-defined behavior
    and typically don't need documentation. However, context managers (__enter__, __exit__)
    should be documented as they define custom behavior.

    Simple __init__ methods (complexity < 20) are also excluded as they typically
    just assign parameters to instance variables.

    Args:
        func_name: Name of the function
        complexity: Optional complexity score (used for __init__ exclusion)

    Returns:
        True if the function should be excluded from undocumented count
    """
    # Special methods that should be excluded from undocumented count
    special_methods = {
        "__new__",  # Singleton patterns
        "__post_init__",  # Dataclass post-init
        "__repr__",  # String representation
        "__str__",  # String conversion
        "__hash__",  # Hashing
        "__eq__",  # Equality comparison
        "__lt__",
        "__le__",
        "__gt__",
        "__ge__",  # Comparison methods
        "__len__",  # Length
        "__bool__",  # Boolean conversion
        "__call__",  # Callable
        "__getitem__",
        "__setitem__",
        "__delitem__",  # Item access
        "__iter__",
        "__next__",  # Iteration
        "__contains__",  # Membership testing
        "__add__",
        "__sub__",
        "__mul__",
        "__truediv__",  # Arithmetic
        "__radd__",
        "__rsub__",
        "__rmul__",
        "__rtruediv__",  # Reverse arithmetic
        "__iadd__",
        "__isub__",
        "__imul__",
        "__itruediv__",  # In-place arithmetic
    }

    # Context manager methods (these should be documented)
    context_methods = {"__enter__", "__exit__"}

    # Simple __init__ methods (complexity < 20) can be excluded
    if func_name == "__init__" and complexity is not None and complexity < 20:
        return True

    # Exclude special methods but not context managers
    if func_name in special_methods and func_name not in context_methods:
        return True

    return False


@handle_errors("checking if function is a test function", default_return=False)
def is_test_function(func_name: str, file_path: Optional[str] = None) -> bool:
    """
    Determine if a function is a test function that should be excluded from certain analyses.

    Test functions are identified by:
    - Function name starting with 'test_' or containing 'test' keyword
    - File path containing 'test' (if file_path provided)

    Args:
        func_name: Name of the function
        file_path: Optional file path for additional context

    Returns:
        True if the function should be excluded from analysis
    """
    test_keywords = _get_test_keywords()

    # Check function name against test keywords
    func_name_lower = func_name.lower()
    for keyword in test_keywords:
        if keyword in func_name_lower:
            return True

    # If file path provided, check if it's in a test file
    if file_path:
        file_path_lower = file_path.lower()
        if (
            "test_" in file_path_lower
            or "/tests/" in file_path_lower
            or "\\tests\\" in file_path_lower
        ):
            return True

    return False
