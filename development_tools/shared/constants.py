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


# Load constants from config or use defaults
DEFAULT_DOCS: tuple[str, ...] = _load_default_docs()
PAIRED_DOCS: dict[str, str] = _load_paired_docs()
LOCAL_MODULE_PREFIXES: tuple[str, ...] = _load_local_module_prefixes()

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

# Path drift detection constants
THIRD_PARTY_LIBRARIES: tuple[str, ...] = (
    "PyQt5",
    "PyQt6",
    "PySide6",
    "discord",
    "requests",
    "aiohttp",
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "scipy",
    "sklearn",
    "tensorflow",
    "torch",
    "pytorch",
    "fastapi",
    "sqlalchemy",
    "alembic",
    "psycopg2",
    "pymongo",
    "redis",
    "celery",
    "gunicorn",
    "uvicorn",
    "pytest",
    "black",
    "flake8",
    "mypy",
)

COMMON_FUNCTION_NAMES: tuple[str, ...] = (
    "get_logger",
    "handle_errors",
    "safe_file_operation",
    "get_component_logger",
    "cleanup_old_logs",
    "functions",
    "statements",
    "handle_file_error",
    "handle_network_error",
    "handle_communication_error",
    "handle_configuration_error",
    "handle_validation_error",
    "handle_ai_error",
    "TestUserFactory",
    "TestDataFactory",
    "TestPathFactory",
    "TestConfigFactory",
)

COMMON_CLASS_NAMES: tuple[str, ...] = (
    "TestUserFactory",
    "TestDataFactory",
    "TestPathFactory",
    "TestConfigFactory",
    "BaseChannel",
    "DiscordBot",
    "EmailBot",
    "TelegramBot",
    "TaskManager",
    "UserManager",
    "ScheduleManager",
    "CheckinManager",
    "MessageRouter",
)

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
    "for",
    "def",
    "class",
    "import",
    "from",
    "return",
    "yield",
    "try",
    "except",
    "finally",
    "with",
    "as",
    "pass",
    "break",
    "continue",
)

COMMON_CODE_PATTERNS: tuple[str, ...] = (
    "PyQt5.QtWidgets",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PySide6.QtWidgets",
    "ui.dialogs.task_crud_dialog",
    "ui.dialogs.account_creator_dialog",
    "ui.widgets.task_settings_widget",
    "ui.widgets.channel_selection_widget",
    "communication.discord.bot",
    "communication.email.bot",
    "core.logger",
    "core.error_handling",
    "core.config",
    "core.scheduler",
    "ai.chatbot",
)

# Common patterns that should be ignored in path drift detection
IGNORED_PATH_PATTERNS: tuple[str, ...] = (
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

# Common template patterns that should be ignored
TEMPLATE_PATTERNS: tuple[str, ...] = ("test_<", ">.py", "{", "}", "*", "?")

# AI Development Tools Constants

# =============================================================================
# PROJECT STRUCTURE
# =============================================================================


def _load_project_directories() -> tuple[str, ...]:
    """Load project directories from config or return defaults."""
    constants_config = _get_constants_config_safe()
    if constants_config and "project_directories" in constants_config:
        return tuple(constants_config["project_directories"])
    # Default: just root
    return (".",)


def _load_core_modules() -> tuple[str, ...]:
    """Load core modules from config or return defaults."""
    constants_config = _get_constants_config_safe()
    if constants_config and "core_modules" in constants_config:
        return tuple(constants_config["core_modules"])
    # Default: empty
    return ()


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
    "ASCII_COMPLIANCE_FILES",
    "COMMAND_PATTERNS",
    "COMMON_CLASS_NAMES",
    "COMMON_CODE_PATTERNS",
    "COMMON_FUNCTION_NAMES",
    "COMMON_VARIABLE_NAMES",
    "CORRUPTED_ARTIFACT_PATTERNS",
    "CORE_MODULES",
    "DEFAULT_DOCS",
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
