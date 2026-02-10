#!/usr/bin/env python3
# TOOL_TIER: core

"""
Standard Exclusion Patterns for Development Tools

This module provides standardized exclusion patterns that can be reused
across all development tools to ensure consistent file filtering.

Exclusion patterns are loaded from external config file
(`development_tools/config/development_tools_config.json`)
if available, otherwise fall back to generic defaults. This makes the module portable
across different projects.

Usage:
    from development_tools.shared.standard_exclusions import get_exclusions

    # Get exclusions for a specific tool type
    exclusions = get_exclusions('coverage')
    exclusions = get_exclusions('analysis')
    exclusions = get_exclusions('documentation')
"""

from typing import Tuple, Dict, List

# Import config to load external exclusions
try:
    from .. import config
except ImportError:
    # Fallback for when run as standalone script
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from development_tools import config

# Load external config on module import (if not already loaded)
# load_external_config is safe to call multiple times
try:
    if hasattr(config, "load_external_config"):
        config.load_external_config()
except (AttributeError, ImportError):
    # Config may not be fully loaded yet, will be loaded when needed
    pass

# Default universal exclusions (generic patterns - should work for most projects)
# These are fallbacks if external config doesn't provide exclusions
_DEFAULT_BASE_EXCLUSIONS = [
    # Python cache and compiled files
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyi",
    ".ruff_cache",
    ".pytest_tmp_cache",
    ".pytest-tmp-*",
    ".tmp_devtools_pyfiles",
    ".tmp_pytest",
    ".tmp_pytest_runner",
    # Virtual environments
    "venv",
    ".venv",
    "env",
    ".env",
    "node_modules",
    # Git and version control
    ".git",
    ".gitignore",
    ".gitattributes",
    # IDE and editor files
    ".vscode",
    ".idea",
    "*.swp",
    "*.swo",
    "*~",
    ".cursorignore",
    # OS generated files
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    # Archive and backup directories
    "archive",
    "backup*",
    "backups",
    # Scripts directory (should be excluded in all contexts)
    "scripts",
    "scripts/*",
    "*/scripts/*",
    # Test artifacts
    ".pytest_cache",
    "tests/__pycache__",
    "tests/.pytest_cache",
    "tests/logs/",
    "tests/data/",
    "tests/temp/",
    "tests/fixtures/",
    "tests/ai/results",
    "tests/coverage_html",
    "mhm.egg-info",
    # Pytest temporary directories (created during parallel test runs)
    "pytest-tmp-*",
    "pytest-of-*",
    "*/pytest-tmp-*",
    "*/pytest-of-*",
    # Generated files (should be excluded everywhere)
    "*/generated/*",
    "*/ui/generated/*",
    "*/pyscript*",
    "*/shibokensupport/*",
    "*/signature_bootstrap.py",
]


def _get_exclusions_config_safe():
    """Safely get exclusions config, returning None if config not available."""
    try:
        if hasattr(config, "get_exclusions_config"):
            return config.get_exclusions_config()
    except (AttributeError, ImportError, TypeError):
        pass
    return None


def _load_base_exclusions() -> List[str]:
    """Load universal exclusions from config or return defaults."""
    exclusions_config = _get_exclusions_config_safe()
    if exclusions_config and "base_exclusions" in exclusions_config:
        return exclusions_config["base_exclusions"]
    return _DEFAULT_BASE_EXCLUSIONS.copy()


# Universal exclusions - start from config or fall back to defaults
BASE_EXCLUSIONS = _load_base_exclusions()

# Default tool-specific exclusions (empty by default - projects can override via config)
_DEFAULT_TOOL_EXCLUSIONS = {}


def _load_tool_exclusions() -> Dict[str, List[str]]:
    """Load tool-specific exclusions from config or return defaults."""
    exclusions_config = _get_exclusions_config_safe()
    if exclusions_config and "tool_exclusions" in exclusions_config:
        return exclusions_config["tool_exclusions"]
    return _DEFAULT_TOOL_EXCLUSIONS.copy()


# Tool-specific exclusions - load from config or fall back to defaults
TOOL_EXCLUSIONS = _load_tool_exclusions()

# Default context-specific exclusions (generic patterns)
_DEFAULT_CONTEXT_EXCLUSIONS = {
    "recent_changes": [],
    "production": [
        # Production should exclude development files (generic patterns)
        "development_tools/*",
        "*/development_tools/*",
        "tests/*",
        "*/tests/*",
        "*/test_*",
        "scripts/*",
        "*/scripts/*",
        "archive/*",
        "*/archive/*",
    ],
    "development": [
        # Development can include most files but exclude sensitive data
        "*/data/*",
        "*/logs/*",
        "*/backup*",
        "*/backups/*",
    ],
    "testing": [
        # Testing should exclude generated files and data
        "*/generated/*",
        "*/ui/generated/*",
        "*/data/*",
        "*/logs/*",
        "*/backup*",
        "*/backups/*",
    ],
}


def _load_context_exclusions() -> Dict[str, List[str]]:
    """Load context-specific exclusions from config or return defaults.

    recent_changes will be built from generated files after they're loaded.
    """
    exclusions_config = _get_exclusions_config_safe()
    result = _DEFAULT_CONTEXT_EXCLUSIONS.copy()

    if exclusions_config and "context_exclusions" in exclusions_config:
        context_exclusions = exclusions_config["context_exclusions"]

        # Update contexts (recent_changes will be built from generated files later)
        for key, value in context_exclusions.items():
            if key != "recent_changes":
                result[key] = value

    return result


# Context-specific exclusions - will be finalized after generated files are defined
_CONTEXT_EXCLUSIONS_TEMP = _load_context_exclusions()


def get_exclusions(tool_type: str = None, context: str = "development") -> list:
    """
    Get exclusion patterns for a specific tool type and context.

    Args:
        tool_type: Type of tool ('coverage', 'analysis', 'documentation', 'fix_version_sync', 'file_operations')
        context: Context ('production', 'development', 'testing')

    Returns:
        List of exclusion patterns
    """
    exclusions = BASE_EXCLUSIONS.copy()

    # Add tool-specific exclusions
    if tool_type and tool_type in TOOL_EXCLUSIONS:
        exclusions.extend(TOOL_EXCLUSIONS[tool_type])

    # Add context-specific exclusions
    if context and context in CONTEXT_EXCLUSIONS:
        exclusions.extend(CONTEXT_EXCLUSIONS[context])

    return exclusions


def should_exclude_file(
    file_path, tool_type: str = None, context: str = "development"
) -> bool:
    """
    Check if a file should be excluded based on standard patterns.

    Args:
        file_path: Path to the file to check (str or Path object)
        tool_type: Type of tool
        context: Context

    Returns:
        True if file should be excluded
    """
    import fnmatch
    from pathlib import Path

    exclusions = get_exclusions(tool_type, context)

    # Convert Path object to string if needed
    file_path_str = str(file_path)
    normalized_path = file_path_str.replace("\\", "/")

    # Explicitly check for pytest temp directories first (most common exclusion during scanning)
    # These are created during parallel test execution and should always be excluded
    if "pytest-tmp-" in normalized_path or "pytest-of-" in normalized_path:
        # These are pytest worker/temp directories and should not be scanned by audit tools.
        return True

    # Check generated files patterns (ui/generated/*, etc.)
    for pattern in GENERATED_FILE_PATTERNS:
        if fnmatch.fnmatch(normalized_path, pattern) or fnmatch.fnmatch(
            normalized_path, f"*/{pattern}"
        ):
            return True

    # Check standard exclusions
    for pattern in exclusions:
        # Handle wildcard patterns with fnmatch
        if fnmatch.fnmatch(normalized_path, pattern) or pattern in normalized_path:
            return True

    return False


def get_coverage_exclusions() -> list:
    """Get exclusions specifically for coverage analysis."""
    return get_exclusions("coverage", "development")


def get_analysis_exclusions() -> list:
    """Get exclusions specifically for code analysis."""
    return get_exclusions("analysis", "development")


def get_documentation_exclusions() -> list:
    """Get exclusions specifically for documentation tools."""
    return get_exclusions("documentation", "development")


def get_version_sync_exclusions() -> list:
    """Get exclusions specifically for version synchronization."""
    return get_exclusions("fix_version_sync", "development")


def get_file_operations_exclusions() -> list:
    """Get exclusions specifically for file operations."""
    return get_exclusions("file_operations", "development")


# =============================================================================
# GENERATED FILES & EXCLUSIONS
# =============================================================================


def _load_generated_files() -> Tuple[str, ...]:
    """Load generated files list from config or return defaults.

    Generated files can include both specific file paths and glob patterns.
    Patterns (containing *) are handled via pattern matching, while exact paths
    are handled via direct comparison.
    """
    exclusions_config = _get_exclusions_config_safe()
    if exclusions_config and "generated_files" in exclusions_config:
        return tuple(exclusions_config["generated_files"])
    # Default: empty (projects should define their own)
    return ()


# All generated files (loaded from config)
# Contains both specific file paths and glob patterns (e.g., "ui/generated/*")
GENERATED_FILES: Tuple[str, ...] = _load_generated_files()


# Separate generated files into exact paths and patterns for different use cases
def _split_generated_files() -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """Split generated files into exact paths and patterns."""
    exact_paths = []
    patterns = []
    for item in GENERATED_FILES:
        if "*" in item or "?" in item or "[" in item:
            patterns.append(item)
        else:
            exact_paths.append(item)
    return tuple(exact_paths), tuple(patterns)


GENERATED_FILE_PATHS, GENERATED_FILE_PATTERNS = _split_generated_files()

# ALL_GENERATED_FILES contains only exact paths
# (patterns are handled separately via should_exclude_file)
ALL_GENERATED_FILES: Tuple[str, ...] = GENERATED_FILE_PATHS

# Finalize context exclusions now that generated files are defined
# Build recent_changes from generated files (always, regardless of config)
# Include both exact paths and patterns
_CONTEXT_EXCLUSIONS_TEMP["recent_changes"] = list(ALL_GENERATED_FILES) + list(
    GENERATED_FILE_PATTERNS
)
CONTEXT_EXCLUSIONS = _CONTEXT_EXCLUSIONS_TEMP


def _load_base_exclusion_shortlist() -> Tuple[str, ...]:
    """Load standard exclusion patterns from config or return defaults."""
    exclusions_config = _get_exclusions_config_safe()
    if exclusions_config and "base_exclusion_shortlist" in exclusions_config:
        return tuple(exclusions_config["base_exclusion_shortlist"])
    # Default generic patterns
    return (
        "logs/",
        "data/",
        "coverage_html/",
        "__pycache__/",
        ".pytest_cache/",
        ".ruff_cache/",
        "venv/",
        ".venv/",
        "htmlcov/",
        "archive/",
        "ui/generated/",
        "mhm.egg-info/",
        "*.log",
        ".coverage",
        "coverage.xml",
        "*.html",
    )


# Standard exclusion patterns (used by multiple tools)
BASE_EXCLUSION_SHORTLIST: Tuple[str, ...] = _load_base_exclusion_shortlist()

# =============================================================================
# TOOL-SPECIFIC EXCLUSIONS
# =============================================================================


def _load_historical_preserve_files() -> Tuple[str, ...]:
    """Load historical preserve files from config or return defaults."""
    exclusions_config = _get_exclusions_config_safe()
    if exclusions_config and "historical_preserve_files" in exclusions_config:
        return tuple(exclusions_config["historical_preserve_files"])
    # Default: empty (projects should define their own)
    return ()


# Legacy cleanup preserve files
HISTORICAL_PRESERVE_FILES: Tuple[str, ...] = _load_historical_preserve_files()

# Documentation sync checker placeholders
DOC_SYNC_PLACEHOLDERS: Dict[str, str] = {
    "logs": "    (log files)",
    "data": "    (data files)",
    "htmlcov": "    (HTML coverage reports)",
    "backups": "    (backup files)",
    "archive": "    (archived files)",
    "jsons": "    (JSON files created by development tools)",
    "development_tools/tests/logs": "    (test coverage log files)",
}

# Example usage
if __name__ == "__main__":
    print("Coverage exclusions:")
    for pattern in get_coverage_exclusions():
        print(f"  {pattern}")

    print("\nAnalysis exclusions:")
    for pattern in get_analysis_exclusions():
        print(f"  {pattern}")
