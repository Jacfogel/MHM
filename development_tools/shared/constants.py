# TOOL_TIER: core

"""
Shared constant data and helpers for AI development tools.

Constants are loaded from external config file (development_tools_config.json)
if available, otherwise fall back to generic defaults. This makes the module portable
across different projects.
"""
from __future__ import annotations

import re
import sys

# Import config to load external constants
try:
    from .. import config
except ImportError:
    # Fallback for when run as standalone script
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from development_tools import config

# Load external config on module import (if not already loaded)
# Load external config if available (safe to call multiple times)
try:
    if hasattr(config, "load_external_config"):
        config.load_external_config()
except (AttributeError, ImportError):
    pass

# Default constants (generic fallbacks if config doesn't provide them)
_DEFAULT_DEFAULT_DOCS: tuple[str, ...] = (
    "README.md",
    "TODO.md",
)

_DEFAULT_PAIRED_DOCS: dict[str, str] = {}

_DEFAULT_LOCAL_MODULE_PREFIXES: tuple[str, ...] = (
    "core",
    "tests",
)

# Generic fallbacks for project-specific lists (path-drift / unconverted-links).
# Config overrides for common_function_names, common_class_names, third_party_libraries,
# common_code_patterns. common_variable_names is non-project-specific and stays here only.
_DEFAULT_COMMON_FUNCTION_NAMES: tuple[str, ...] = (
    "get_logger",
    "handle_errors",
    "main",
    "run",
    "setup",
    "teardown",
    "process",
    "execute",
    "parse",
)
_DEFAULT_COMMON_CLASS_NAMES: tuple[str, ...] = (
    "TestCase",
    "BaseTestCase",
    "BaseModel",
    "BaseView",
)
_DEFAULT_THIRD_PARTY_LIBRARIES: tuple[str, ...] = (
    "pytest",
    "requests",
    "aiohttp",
    "black",
    "flake8",
    "mypy",
)
_DEFAULT_COMMON_CODE_PATTERNS: tuple[str, ...] = (
    "unittest.TestCase",
    "pytest.fixture",
    "typing.",
)
# Non-project-specific: Python keywords and common variable names (skip when path-drift checks).
# Not loaded from config.
COMMON_VARIABLE_NAMES: tuple[str, ...] = (
    "task",
    "and",
    "statements",
    "from",
    "in",
    "to",
    "for",
    "with",
    "as",
    "if",
    "else",
    "elif",
    "while",
    "def",
    "class",
    "import",
    "return",
    "yield",
    "try",
    "except",
    "finally",
    "pass",
    "break",
    "continue",
)


def _get_constants_config_safe():
    """Safely get constants config, returning None if config not available."""
    try:
        if hasattr(config, "get_constants_config"):
            return config.get_constants_config()
    except (AttributeError, ImportError, TypeError):
        pass
    return None


def _load_default_docs() -> tuple[str, ...]:
    """Load default docs list from config or return defaults."""
    constants_config = _get_constants_config_safe()
    if constants_config and "default_docs" in constants_config:
        return tuple(constants_config["default_docs"])
    return _DEFAULT_DEFAULT_DOCS


def _load_paired_docs() -> dict[str, str]:
    """Load paired docs mapping from config or return defaults."""
    constants_config = _get_constants_config_safe()
    if constants_config and "paired_docs" in constants_config:
        return dict(constants_config["paired_docs"])
    return _DEFAULT_PAIRED_DOCS.copy()


def _load_local_module_prefixes() -> tuple[str, ...]:
    """Load local module prefixes from config or return defaults."""
    constants_config = _get_constants_config_safe()
    if constants_config and "local_module_prefixes" in constants_config:
        return tuple(constants_config["local_module_prefixes"])
    return _DEFAULT_LOCAL_MODULE_PREFIXES


def _load_project_specific_list(key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    """Load a project-specific list from constants config or return default."""
    constants_config = _get_constants_config_safe()
    if constants_config and key in constants_config:
        val = constants_config[key]
        if isinstance(val, (list, tuple)):
            return tuple(str(x) for x in val)
    return default


# Load constants from config or use defaults
DEFAULT_DOCS: tuple[str, ...] = _load_default_docs()
PAIRED_DOCS: dict[str, str] = _load_paired_docs()
LOCAL_MODULE_PREFIXES: tuple[str, ...] = _load_local_module_prefixes()

# Exclusion sets for deriving scan_directories, core_modules, project_directories from LOCAL_MODULE_PREFIXES.
# Canonical source: LOCAL_MODULE_PREFIXES. Other lists are derived; config can override.
_SCAN_EXCLUDE = frozenset({"data", "development_tools", "notebook", "scripts"})
_CORE_EXCLUDE = frozenset({"data", "development_tools", "scripts", "tests"})
_PROJECT_EXCLUDE = frozenset({"data", "development_tools", "scripts"})

STANDARD_LIBRARY_PREFIXES: tuple[str, ...] = (
    "asyncio",
    "concurrent",
    "contextlib",
    "email",
    "http",
    "importlib",
    "logging",
    "multiprocessing",
    "pathlib",
    "sqlite3",
    "xml",
    "xmlrpc",
    "zipfile",
)

_STD_EXTRA = {
    "argparse",
    "atexit",
    "base64",
    "binascii",
    "bz2",
    "calendar",
    "collections",
    "configparser",
    "copy",
    "csv",
    "dataclasses",
    "datetime",
    "decimal",
    "difflib",
    "functools",
    "gc",
    "glob",
    "gzip",
    "hashlib",
    "inspect",
    "io",
    "itertools",
    "json",
    "math",
    "os",
    "pickle",
    "pkgutil",
    "platform",
    "queue",
    "random",
    "re",
    "runpy",
    "shlex",
    "shutil",
    "signal",
    "statistics",
    "string",
    "struct",
    "subprocess",
    "sys",
    "tempfile",
    "threading",
    "time",
    "timeit",
    "typing",
    "unicodedata",
    "uuid",
    "warnings",
    "weakref",
    "zipapp",
    "zlib",
}

try:
    _stdlib = set(sys.stdlib_module_names)
except AttributeError:  # pragma: no cover - Python < 3.10
    _stdlib = set()

_stdlib.update(_STD_EXTRA)
_stdlib.update(prefix.split(".", 1)[0] for prefix in STANDARD_LIBRARY_PREFIXES)
STANDARD_LIBRARY_MODULES = frozenset(_stdlib)

CORRUPTED_ARTIFACT_PATTERNS = (
    ("replacement_character", re.compile(r"\uFFFD")),
    ("triple_question_marks", re.compile(r"\?\?\?")),
)

# Path drift detection constants (project-specific; loaded from config)
COMMON_FUNCTION_NAMES: tuple[str, ...] = _load_project_specific_list(
    "common_function_names", _DEFAULT_COMMON_FUNCTION_NAMES
)
COMMON_CLASS_NAMES: tuple[str, ...] = _load_project_specific_list(
    "common_class_names", _DEFAULT_COMMON_CLASS_NAMES
)
THIRD_PARTY_LIBRARIES: tuple[str, ...] = _load_project_specific_list(
    "third_party_libraries", _DEFAULT_THIRD_PARTY_LIBRARIES
)
COMMON_CODE_PATTERNS: tuple[str, ...] = _load_project_specific_list(
    "common_code_patterns", _DEFAULT_COMMON_CODE_PATTERNS
)

# Common patterns that should be ignored in path drift detection
# "paths" = config section (paths.scan_directories, etc.), not a Python module
IGNORED_PATH_PATTERNS: tuple[str, ...] = (
    "paths",
    "paths.",
    "Python Official Tutorial",
    "Real Python",
    "Troubleshooting",
    "README.md#troubleshooting",
    "Navigation",
    "Project Vision",
    "Quick Start",
    "Development Workflow",
    "Documentation Guide",
    "Development Plans",
    "Recent Changes",
    "Recent Changes (Most Recent First)",
)

# Common command patterns that should be ignored
COMMAND_PATTERNS: tuple[str, ...] = (
    "python ",
    "pip ",
    "git ",
    "npm ",
    "yarn ",
    "docker ",
    "kubectl ",
)

# Path prefixes that indicate not a file path (unconverted links: don't convert)
_NON_PATH_PREFIXES: tuple[str, ...] = ("*", "http", "#", "mailto")
PATH_STARTSWITH_NON_FILE: tuple[str, ...] = _NON_PATH_PREFIXES + COMMAND_PATTERNS

# Common template patterns that should be ignored
TEMPLATE_PATTERNS: tuple[str, ...] = ("test_<", ">.py", "{", "}", "*", "?")

# AI Development Tools Constants

# =============================================================================
# PROJECT STRUCTURE
# =============================================================================


def get_scan_directories_derived() -> tuple[str, ...]:
    """Derive scan_directories from LOCAL_MODULE_PREFIXES (exclude data, development_tools, notebook, scripts).
    Used when paths.scan_directories is not in config.
    """
    return tuple(d for d in LOCAL_MODULE_PREFIXES if d not in _SCAN_EXCLUDE)


def _derived_core_modules() -> tuple[str, ...]:
    """Derive core_modules from LOCAL_MODULE_PREFIXES (exclude data, development_tools, scripts, tests)."""
    return tuple(d for d in LOCAL_MODULE_PREFIXES if d not in _CORE_EXCLUDE)


def _derived_project_directories() -> tuple[str, ...]:
    """Derive project_directories from LOCAL_MODULE_PREFIXES (exclude data, development_tools, scripts; prepend .)."""
    filtered = tuple(d for d in LOCAL_MODULE_PREFIXES if d not in _PROJECT_EXCLUDE)
    return (".",) + filtered if filtered else (".",)


def _load_project_directories() -> tuple[str, ...]:
    """Load project directories from config or derive from LOCAL_MODULE_PREFIXES."""
    constants_config = _get_constants_config_safe()
    if constants_config and "project_directories" in constants_config:
        configured = constants_config["project_directories"]
        if isinstance(configured, (list, tuple)) and configured:
            return tuple(str(d) for d in configured)
    return _derived_project_directories()


def _load_core_modules() -> tuple[str, ...]:
    """Load core modules from config or derive from LOCAL_MODULE_PREFIXES."""
    constants_config = _get_constants_config_safe()
    if constants_config and "core_modules" in constants_config:
        configured = constants_config["core_modules"]
        if isinstance(configured, (list, tuple)) and configured:
            return tuple(str(d) for d in configured)
    return _derived_core_modules()


# Core project directories (used by multiple tools)
PROJECT_DIRECTORIES: tuple[str, ...] = _load_project_directories()

# Core modules for coverage and analysis (subset of PROJECT_DIRECTORIES)
CORE_MODULES: tuple[str, ...] = _load_core_modules()

# =============================================================================
# TOOL-SPECIFIC CONSTANTS
# =============================================================================


def _load_test_category_markers() -> tuple[str, ...]:
    """Load test category markers from config or return defaults."""
    constants_config = _get_constants_config_safe()
    if constants_config and "test_category_markers" in constants_config:
        return tuple(constants_config["test_category_markers"])
    return ("unit", "integration", "behavior", "ui")


def _load_test_marker_directory_map() -> dict[str, str]:
    """Load test directory-to-marker map from config or return defaults."""
    constants_config = _get_constants_config_safe()
    if constants_config and "test_marker_directory_map" in constants_config:
        configured = constants_config["test_marker_directory_map"]
        if isinstance(configured, dict):
            return {str(key): str(value) for key, value in configured.items()}
    return {
        "unit": "unit",
        "integration": "integration",
        "behavior": "behavior",
        "ui": "ui",
    }


def _load_test_marker_transient_path_markers() -> tuple[str, ...]:
    """Load transient path markers used by test marker scans."""
    constants_config = _get_constants_config_safe()
    if constants_config and "test_marker_transient_path_markers" in constants_config:
        return tuple(constants_config["test_marker_transient_path_markers"])
    return (
        "/tmp/",
        "/tmp_pytest_runtime/",
        "pytest-tmp-",
        "pytest-of-",
    )


def _load_test_marker_ai_path_tokens() -> tuple[str, ...]:
    """Load path tokens used to exclude AI tests from marker analysis."""
    constants_config = _get_constants_config_safe()
    if constants_config and "test_marker_ai_path_tokens" in constants_config:
        return tuple(constants_config["test_marker_ai_path_tokens"])
    return ("ai/test_ai", "test_ai")


TEST_CATEGORY_MARKERS: tuple[str, ...] = _load_test_category_markers()
TEST_MARKER_DIRECTORY_MAP: dict[str, str] = _load_test_marker_directory_map()
TEST_MARKER_TRANSIENT_PATH_MARKERS: tuple[str, ...] = (
    _load_test_marker_transient_path_markers()
)
TEST_MARKER_AI_PATH_TOKENS: tuple[str, ...] = _load_test_marker_ai_path_tokens()

# =============================================================================
# Documentation analysis and path-drift constants (shared across docs scripts)
# =============================================================================
# Used by analyze_documentation, analyze_path_drift, analyze_unconverted_links,
# fix_documentation_ascii, analyze_ascii_compliance to avoid duplicate lists.

# Section headings that are expected to appear in multiple docs (not problematic)
EXPECTED_OVERLAPS: frozenset[str] = frozenset({
    "purpose",
    "overview",
    "introduction",
    "summary",
    "quick start",
    "quick reference",
    "table of contents",
    "contents",
    "navigation",
    "see also",
    "references",
})

# Words that are generic in paths (path-drift: skip when path is just this word)
DOC_COMMON_WORDS: frozenset[str] = frozenset({
    "extraction", "utility", "methods", "module", "package", "function", "class",
    "variable", "constant", "helper", "service", "tool", "analysis", "report",
    "generation", "loading", "wrappers", "orchestration", "commands", "data",
    "config", "shared", "development", "tools", "documentation", "compliance",
    "drift", "sync", "missing", "addresses", "links", "heading", "numbering",
    "unconverted", "ascii", "path", "legacy", "references", "coverage", "test",
    "markers", "imports", "unused", "functions", "registry", "dependencies",
    "patterns", "error", "handling", "exports", "decision", "support", "system",
    "signals", "quick", "status", "validation", "work", "ai",
})

# Python keywords (path-drift: paths containing these are likely code, not file refs)
PYTHON_KEYWORDS_PATH_DRIFT: tuple[str, ...] = (
    "def", "class", "import", "from", "if", "else", "for", "while", "try",
    "except", "finally", "with", "as", "return", "yield", "lambda",
    "and", "or", "not", "in", "is", "True", "False", "None",
)

# Section header words (path-drift: title-case phrases that look like headers)
DOC_SECTION_WORDS: tuple[str, ...] = (
    "overview", "summary", "introduction", "background", "context",
    "recommendations", "suggestions", "guidelines", "best practices",
    "implementation", "status", "progress", "analysis", "review", "findings",
    "conclusion", "next steps", "action items", "todo", "issues", "problems",
    "solutions", "approach", "strategy", "architecture", "design", "structure",
    "organization", "layout",
)

# Example phrases (skip line for path-drift / unconverted-link detection)
EXAMPLE_PHRASES: tuple[str, ...] = (
    "for example", "for instance", "e.g.,", "e.g.", "example:", "examples:",
)

# Example markers (regex patterns; line starting with these is example context)
EXAMPLE_MARKERS: tuple[str, ...] = (
    r"^\[OK\]", r"^\[AVOID\]", r"^\[GOOD\]", r"^\[BAD\]", r"^\[EXAMPLE\]",
)

# Doc files that intentionally reference old paths: now in config path_drift.legacy_documentation_files
# (project-specific; see development_tools_config.json). analyze_path_drift loads and normalizes.

# Path prefixes that indicate not a file path: defined above (see COMMAND_PATTERNS + _NON_PATH_PREFIXES).

# File extensions valid for path-drift file references
PATH_DRIFT_VALID_EXTENSIONS: tuple[str, ...] = (
    ".py", ".md", ".json", ".txt", ".yaml", ".yml", ".toml", ".ini", ".cfg",
)

# Python operators (path-drift: path containing these is likely code)
PATH_DRIFT_OPERATORS: tuple[str, ...] = (
    "==", "!=", "<=", ">=", "+=", "-=", "*=", "/=", "%=", "//=", "**=",
    "&=", "|=", "^=", "<<=", ">>=",
)

# Special Python methods and context manager methods (shared across tools)
SPECIAL_METHODS: frozenset[str] = frozenset(
    {
        "__new__",
        "__post_init__",
        "__repr__",
        "__str__",
        "__hash__",
        "__eq__",
        "__ne__",
        "__lt__",
        "__le__",
        "__gt__",
        "__ge__",
        "__len__",
        "__bool__",
        "__call__",
        "__getitem__",
        "__setitem__",
        "__delitem__",
        "__iter__",
        "__next__",
        "__contains__",
        "__add__",
        "__sub__",
        "__mul__",
        "__truediv__",
        "__radd__",
        "__rsub__",
        "__rmul__",
        "__rtruediv__",
        "__iadd__",
        "__isub__",
        "__imul__",
        "__itruediv__",
        "__getattr__",
        "__setattr__",
        "__delattr__",
        "__getattribute__",
    }
)

CONTEXT_METHODS: frozenset[str] = frozenset({"__enter__", "__exit__"})

# Generated function patterns (function-level exclusions; used by exclusion_utilities)
# File-level patterns are in standard_exclusions (exclusions.generated_files).
AUTO_GENERATED_FILE_PATTERNS: tuple[str, ...] = (
    "_ui.py",
    "_generated.py",
    "_auto.py",
)
EXACT_GENERATED_NAMES: frozenset[str] = frozenset({
    "setupUi",
    "retranslateUi",
    "setup_ui",
    "retranslate_ui",
})
GENERATED_NAME_PATTERNS: tuple[str, ...] = (
    "setup_ui_",
    "retranslate_ui_",
    "_generated_",
    "_auto_",
)

# Unicode -> ASCII replacements for documentation (single canonical source)
ASCII_REPLACEMENTS: dict[str, str] = {
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',
    "\u2011": "-", "\u2013": "-", "\u2014": "-", "\u2015": "--",
    "\u2192": "->", "\u2190": "<-", "\u2191": "^", "\u2193": "v",
    "\u2026": "...",
    "\u2264": "<=", "\u2265": ">=", "\u00d7": "x", "\u00b0": "deg",
    "\u00b1": "+/-", "\u00f7": "/",
    "\u2022": "*", "\u2122": "(TM)", "\u00ae": "(R)", "\u00a9": "(C)",
    "\u00a7": "Section ",
    "\u2705": "[OK]", "\u274c": "[FAIL]", "\u26a0": "[WARNING]",
    "\U0001f41b": "[BUG]", "\U0001f4a1": "[IDEA]", "\U0001f4dd": "[NOTE]",
    "\u202f": " ", "\u00a0": " ", "\u2009": " ", "\u2008": " ", "\u2007": " ",
    "\u2006": " ", "\u2005": " ", "\u2004": " ", "\u2003": " ", "\u2002": " ",
    "\u2001": " ", "\u2000": " ",
}

# Regex pattern for emoji and common Unicode symbols to strip from headings and text
EMOJI_SYMBOL_STRIP_PATTERN: str = (
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map symbols
    "\U0001f1e0-\U0001f1ff"  # flags (iOS)
    "\U00002702-\U000027b0"  # dingbats
    "\U000024c2-\U0001f251"  # enclosed characters
    "\U0001f900-\U0001f9ff"  # supplemental symbols
    "\U0001fa00-\U0001fa6f"  # chess symbols
    "\U0001fa70-\U0001faff"  # symbols and pictographs extended-A
    "\U00002600-\U000026ff"  # miscellaneous symbols
    "\U00002700-\U000027bf"  # dingbats
    "]+"
)


def _load_ascii_compliance_files() -> tuple[str, ...]:
    """Load ASCII compliance files list from config or return defaults.

    ASCII compliance files are now the same as default_docs. If config has a note
    or is empty, use DEFAULT_DOCS as the source of truth.
    """
    constants_config = _get_constants_config_safe()
    if constants_config and "ascii_compliance_files" in constants_config:
        ascii_files = constants_config["ascii_compliance_files"]
        # Check if it's a note (single item that's a string containing "Note:")
        if isinstance(ascii_files, list) and len(ascii_files) == 1:
            if isinstance(ascii_files[0], str) and "note" in ascii_files[0].lower():
                # Use DEFAULT_DOCS
                return _load_default_docs()
        # If it's a real list, use it
        if isinstance(ascii_files, list) and ascii_files:
            return tuple(ascii_files)
    # Default: use DEFAULT_DOCS
    return _load_default_docs()


# Files to check for ASCII compliance (AI collaborator facing docs)
ASCII_COMPLIANCE_FILES: tuple[str, ...] = _load_ascii_compliance_files()


def _load_version_sync_directories() -> dict[str, str]:
    """Load version sync directories from config or return defaults."""
    constants_config = _get_constants_config_safe()
    if constants_config and "fix_version_sync_directories" in constants_config:
        return dict(constants_config["fix_version_sync_directories"])
    # Default: empty (projects should define their own)
    return {}


# Version sync key directories
VERSION_SYNC_DIRECTORIES: dict[str, str] = _load_version_sync_directories()


def is_standard_library_module(module_name: str) -> bool:
    """Return True if *module_name* belongs to the Python standard library."""
    if not module_name:
        return False
    base = module_name.split(".", 1)[0]
    if base in STANDARD_LIBRARY_MODULES:
        return True
    if base in sys.builtin_module_names:
        return True
    for prefix in STANDARD_LIBRARY_PREFIXES:
        if module_name == prefix or module_name.startswith(prefix + "."):
            return True
    return False


def is_local_module(module_name: str) -> bool:
    """Return True if *module_name* is part of the local project namespace."""
    if not module_name:
        return False
    base = module_name.split(".", 1)[0]
    return base in LOCAL_MODULE_PREFIXES


__all__ = [
    "AUTO_GENERATED_FILE_PATTERNS",
    "ASCII_COMPLIANCE_FILES",
    "ASCII_REPLACEMENTS",
    "COMMAND_PATTERNS",
    "DOC_COMMON_WORDS",
    "DOC_SECTION_WORDS",
    "EXAMPLE_MARKERS",
    "EXAMPLE_PHRASES",
    "EXPECTED_OVERLAPS",
    "PATH_DRIFT_OPERATORS",
    "PATH_DRIFT_VALID_EXTENSIONS",
    "PATH_STARTSWITH_NON_FILE",
    "PYTHON_KEYWORDS_PATH_DRIFT",
    "COMMON_CLASS_NAMES",
    "COMMON_CODE_PATTERNS",
    "COMMON_FUNCTION_NAMES",
    "COMMON_VARIABLE_NAMES",
    "CORRUPTED_ARTIFACT_PATTERNS",
    "CORE_MODULES",
    "DEFAULT_DOCS",
    "EXACT_GENERATED_NAMES",
    "GENERATED_NAME_PATTERNS",
    "IGNORED_PATH_PATTERNS",
    "LOCAL_MODULE_PREFIXES",
    "PAIRED_DOCS",
    "PROJECT_DIRECTORIES",
    "STANDARD_LIBRARY_MODULES",
    "STANDARD_LIBRARY_PREFIXES",
    "TEMPLATE_PATTERNS",
    "THIRD_PARTY_LIBRARIES",
    "VERSION_SYNC_DIRECTORIES",
    "is_local_module",
    "is_standard_library_module",
]
