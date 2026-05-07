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
        is_generated_file,
        is_generated_function,
        is_special_python_method,
        is_test_function
    )

    if is_generated_file(file_path):
        # Skip this file
    if is_generated_function(func_name):
        # Skip this function
"""

import ast
import re
from dataclasses import dataclass
from typing import Literal

from development_tools.shared.logging import get_dev_tools_logger
from development_tools.shared.error_helpers import handle_errors
from development_tools.shared.constants import (
    SPECIAL_METHODS,
    CONTEXT_METHODS,
    AUTO_GENERATED_FILE_PATTERNS,
    EXACT_GENERATED_NAMES,
    GENERATED_NAME_PATTERNS,
)

logger = get_dev_tools_logger("development_tools")

# Default test keywords (can be overridden via config)
_DEFAULT_TEST_KEYWORDS = ["test_", "test"]


MarkerAction = Literal["ignore", "intentional"]
MarkerNode = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


@dataclass(frozen=True)
class DevtoolsMarker:
    """Parsed code-level development-tools marker."""

    action: MarkerAction
    tool: str
    value: str
    line: int
    raw: str


_DEVTOOLS_MARKER_RE = re.compile(
    r"#\s*devtools:\s*(ignore|intentional)\[([^\]]+)\]\s*(?::\s*(.*))?$",
    re.IGNORECASE,
)


def _normalize_marker_tool(tool_name: str) -> str:
    return tool_name.strip().lower().replace("_", "-").replace(" ", "-")


def _function_marker_start_lineno(node: MarkerNode) -> int:
    """Return the first line where node-level marker comments may be attached."""
    candidates = [getattr(node, "lineno", 1) or 1]
    for decorator in getattr(node, "decorator_list", []) or []:
        lineno = getattr(decorator, "lineno", None)
        if isinstance(lineno, int) and lineno > 0:
            candidates.append(lineno)
    return min(candidates)


def _marker_window(
    content: str,
    node: MarkerNode | None = None,
    *,
    context_before: int = 8,
) -> tuple[int, list[str]]:
    lines = content.splitlines()
    if node is None:
        return 1, lines[:20]

    start_lineno = _function_marker_start_lineno(node)
    end_lineno = getattr(node, "end_lineno", start_lineno) or start_lineno
    context_start = max(1, start_lineno - context_before)
    return context_start, lines[context_start - 1 : end_lineno]


def parse_devtools_markers(
    content: str,
    tool_name: str | None = None,
    node: MarkerNode | None = None,
    *,
    include_legacy_aliases: bool = True,
) -> list[DevtoolsMarker]:
    """Parse canonical ``# devtools: ...`` markers near a module/function/class.

    Canonical forms:
    - ``# devtools: ignore[duplicate-functions]: reason``
    - ``# devtools: intentional[duplicate-functions]: group_id``

    Existing duplicate-function aliases are also parsed when
    ``include_legacy_aliases`` is true.
    """
    if not content:
        return []

    requested_tool = _normalize_marker_tool(tool_name) if tool_name else None
    start_line, window_lines = _marker_window(content, node)
    markers: list[DevtoolsMarker] = []

    for offset, line in enumerate(window_lines):
        line_no = start_line + offset
        match = _DEVTOOLS_MARKER_RE.search(line)
        if match:
            action = match.group(1).lower()
            marker_tool = _normalize_marker_tool(match.group(2))
            value = (match.group(3) or "").strip()
            if requested_tool is None or marker_tool == requested_tool:
                markers.append(
                    DevtoolsMarker(
                        action=action,  # type: ignore[arg-type]
                        tool=marker_tool,
                        value=value,
                        line=line_no,
                        raw=line.strip(),
                    )
                )
            continue

        if not include_legacy_aliases:
            continue
        if requested_tool not in (None, "duplicate-functions"):
            continue

        lower = line.lower()
        if "# duplicate_functions_exclude" in lower or "# duplicate functions exclude" in lower:
            value = ""
            if ":" in line:
                value = line.split(":", 1)[1].strip()
            markers.append(
                DevtoolsMarker(
                    action="ignore",
                    tool="duplicate-functions",
                    value=value,
                    line=line_no,
                    raw=line.strip(),
                )
            )
        for alias in (
            "# duplicate_functions_intentional",
            "# not_duplicate",
            "# duplicate functions intentional",
        ):
            if alias in lower:
                value = ""
                marker_index = lower.find(alias)
                tail = line[marker_index + len(alias) :]
                if tail.lstrip().startswith(":"):
                    value = tail.split(":", 1)[1].split("#", 1)[0].strip().lower()
                markers.append(
                    DevtoolsMarker(
                        action="intentional",
                        tool="duplicate-functions",
                        value=value,
                        line=line_no,
                        raw=line.strip(),
                    )
                )
                break

    return markers


def has_devtools_ignore_marker(
    content: str, tool_name: str, node: MarkerNode | None = None
) -> bool:
    """Return True when a matching canonical or legacy ignore marker exists."""
    return any(
        marker.action == "ignore"
        for marker in parse_devtools_markers(content, tool_name, node)
    )


def get_devtools_intentional_marker(
    content: str, tool_name: str, node: MarkerNode | None = None
) -> str | None:
    """Return the first matching intentional marker value, or None if absent."""
    for marker in parse_devtools_markers(content, tool_name, node):
        if marker.action == "intentional":
            return marker.value
    return None


def _get_test_keywords():
    """Get test keywords from config or return defaults."""
    try:
        from .. import config

        config.load_external_config()
        function_config = config.get_analyze_functions_config()
        return function_config.get("test_keywords", _DEFAULT_TEST_KEYWORDS)
    except (ImportError, AttributeError):
        return _DEFAULT_TEST_KEYWORDS


@handle_errors("checking if file is generated", default_return=False)
def is_generated_file(file_path: str) -> bool:
    """
    Determine if a file is auto-generated and should be excluded from analysis.

    This function identifies:
    - Files explicitly marked as generated in header comments
    - Files located in generated directories
    - Files with auto-generated naming patterns
    - PyQt auto-generated files

    Args:
        file_path: Path to the file

    Returns:
        True if the file should be excluded from analysis
    """

    # --- Detect explicit "generated" markers in file header ---
    try:
        with open(file_path, encoding="utf-8") as f:
            first_lines = "".join(f.readlines()[:10]).lower()
            if (
                "generated" in first_lines
                or "auto-generated" in first_lines
                or "generated by" in first_lines
            ):
                return True
    except Exception:
        # If the file can't be read, do not assume it's generated
        pass

    normalized_path = file_path.replace("\\", "/").lower()

    # Exclude files in generated directories
    if "/generated/" in normalized_path:
        return True

    # Exclude PyQt auto-generated files
    if "_pyqt.py" in normalized_path:
        return True

    # Exclude files with auto-generated patterns in name (canonical: constants.AUTO_GENERATED_FILE_PATTERNS)
    for pattern in AUTO_GENERATED_FILE_PATTERNS:
        if normalized_path.endswith(pattern):
            return True

    return False


@handle_errors("checking if function is generated", default_return=False)
def is_generated_function(func_name: str) -> bool:
    """
    Determine if a function name matches auto-generated patterns.

    This function identifies:
    - PyQt-generated UI functions
    - Functions with common auto-generated naming conventions

    Args:
        func_name: Name of the function

    Returns:
        True if the function should be excluded from analysis
    """

    if not func_name:
        return False

    # Exact matches for known generated functions (canonical: constants.EXACT_GENERATED_NAMES)
    if func_name in EXACT_GENERATED_NAMES:
        return True

    # Substring-based patterns (canonical: constants.GENERATED_NAME_PATTERNS)
    return any(pattern in func_name for pattern in GENERATED_NAME_PATTERNS)


@handle_errors("checking if method is special Python method", default_return=False)
def is_special_python_method(func_name: str, complexity: int | None = None) -> bool:
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
    # Simple __init__ methods (complexity < 20) can be excluded
    if func_name == "__init__" and complexity is not None and complexity < 20:
        return True

    # Exclude special methods but not context managers
    return bool(func_name in SPECIAL_METHODS and func_name not in CONTEXT_METHODS)


@handle_errors("checking if function is a test function", default_return=False)
def is_test_function(func_name: str, file_path: str | None = None) -> bool:
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
