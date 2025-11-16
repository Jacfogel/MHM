"""Shared constant data and helpers for AI development tools."""
from __future__ import annotations

import re
import sys
from typing import Dict, Tuple

DEFAULT_DOCS: Tuple[str, ...] = (
    'README.md',
    'HOW_TO_RUN.md',
    'DOCUMENTATION_GUIDE.md',
    'DEVELOPMENT_WORKFLOW.md',
    'ARCHITECTURE.md',
    'TODO.md',
    'development_docs/FUNCTION_REGISTRY_DETAIL.md',
    'development_docs/MODULE_DEPENDENCIES_DETAIL.md',
    'ai_development_docs/AI_SESSION_STARTER.md',
    'ai_development_docs/AI_DOCUMENTATION_GUIDE.md',
    'ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md',
    'ai_development_docs/AI_CHANGELOG.md',
    'ai_development_docs/AI_REFERENCE.md',
    'ai_development_docs/AI_LOGGING_GUIDE.md',
    'ai_development_docs/AI_TESTING_GUIDE.md',
    'ai_development_docs/AI_ERROR_HANDLING_GUIDE.md',
)

PAIRED_DOCS: Dict[str, str] = {
    'DEVELOPMENT_WORKFLOW.md': 'ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md',
    'ARCHITECTURE.md': 'ai_development_docs/AI_ARCHITECTURE.md',
    'DOCUMENTATION_GUIDE.md': 'ai_development_docs/AI_DOCUMENTATION_GUIDE.md',
    'development_docs/CHANGELOG_DETAIL.md': 'ai_development_docs/AI_CHANGELOG.md',
    'logs/LOGGING_GUIDE.md': 'ai_development_docs/AI_LOGGING_GUIDE.md',
    'tests/TESTING_GUIDE.md': 'ai_development_docs/AI_TESTING_GUIDE.md',
    'core/ERROR_HANDLING_GUIDE.md': 'ai_development_docs/AI_ERROR_HANDLING_GUIDE.md',
}

LOCAL_MODULE_PREFIXES: Tuple[str, ...] = (
    'ai',
    'ai_development_tools',
    'bot',
    'communication',
    'core',
    'data',
    'scripts',
    'services',
    'tasks',
    'tests',
    'ui',
    'user',
)

STANDARD_LIBRARY_PREFIXES: Tuple[str, ...] = (
    'asyncio',
    'concurrent',
    'contextlib',
    'email',
    'http',
    'importlib',
    'logging',
    'multiprocessing',
    'pathlib',
    'sqlite3',
    'xml',
    'xmlrpc',
    'zipfile',
)

_STD_EXTRA = {
    'argparse',
    'atexit',
    'base64',
    'binascii',
    'bz2',
    'calendar',
    'collections',
    'configparser',
    'copy',
    'csv',
    'dataclasses',
    'datetime',
    'decimal',
    'difflib',
    'functools',
    'gc',
    'glob',
    'gzip',
    'hashlib',
    'inspect',
    'io',
    'itertools',
    'json',
    'math',
    'os',
    'pickle',
    'pkgutil',
    'platform',
    'queue',
    'random',
    're',
    'runpy',
    'shlex',
    'shutil',
    'signal',
    'statistics',
    'string',
    'struct',
    'subprocess',
    'sys',
    'tempfile',
    'threading',
    'time',
    'timeit',
    'typing',
    'unicodedata',
    'uuid',
    'warnings',
    'weakref',
    'zipapp',
    'zlib',
}

try:
    _stdlib = set(sys.stdlib_module_names)
except AttributeError:  # pragma: no cover - Python < 3.10
    _stdlib = set()

_stdlib.update(_STD_EXTRA)
_stdlib.update(prefix.split('.', 1)[0] for prefix in STANDARD_LIBRARY_PREFIXES)
STANDARD_LIBRARY_MODULES = frozenset(_stdlib)

CORRUPTED_ARTIFACT_PATTERNS = (
    ('replacement_character', re.compile(r'\uFFFD')),
    ('triple_question_marks', re.compile(r'\?\?\?')),
)

# Path drift detection constants
THIRD_PARTY_LIBRARIES: Tuple[str, ...] = (
    'PyQt5', 'PyQt6', 'PySide6', 'discord', 'requests', 'aiohttp', 'pandas', 'numpy',
    'matplotlib', 'seaborn', 'scipy', 'sklearn', 'tensorflow', 'torch', 'pytorch',
    'flask', 'django', 'fastapi', 'sqlalchemy', 'alembic', 'psycopg2', 'pymongo',
    'redis', 'celery', 'gunicorn', 'uvicorn', 'pytest', 'black', 'flake8', 'mypy'
)

COMMON_FUNCTION_NAMES: Tuple[str, ...] = (
    'get_logger', 'handle_errors', 'safe_file_operation', 'error_handler', 
    'get_component_logger', 'cleanup_old_logs', 'functions', 'statements',
    'handle_file_error', 'handle_network_error', 'handle_communication_error',
    'handle_configuration_error', 'handle_validation_error', 'handle_ai_error',
    'TestUserFactory', 'TestDataFactory', 'TestPathFactory', 'TestConfigFactory'
)

COMMON_CLASS_NAMES: Tuple[str, ...] = (
    'TestUserFactory', 'TestDataFactory', 'TestPathFactory', 'TestConfigFactory',
    'BaseChannel', 'DiscordBot', 'EmailBot', 'TelegramBot', 'TaskManager',
    'UserManager', 'ScheduleManager', 'CheckinManager', 'MessageRouter'
)

COMMON_VARIABLE_NAMES: Tuple[str, ...] = (
    'task', 'and', 'statements', 'from', 'in', 'to', 'for', 'with', 'as', 'if',
    'else', 'elif', 'while', 'for', 'def', 'class', 'import', 'from', 'return',
    'yield', 'try', 'except', 'finally', 'with', 'as', 'pass', 'break', 'continue'
)

COMMON_CODE_PATTERNS: Tuple[str, ...] = (
    'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PySide6.QtWidgets',
    'ui.dialogs.task_crud_dialog', 'ui.dialogs.account_creator_dialog',
    'ui.widgets.task_settings_widget', 'ui.widgets.channel_selection_widget',
    'communication.discord.bot', 'communication.email.bot', 'core.logger',
    'core.error_handling', 'core.config', 'core.scheduler', 'ai.chatbot'
)

# Common patterns that should be ignored in path drift detection
IGNORED_PATH_PATTERNS: Tuple[str, ...] = (
    'Python Official Tutorial', 'Real Python', 'Troubleshooting', 'README.md#troubleshooting',
    'Navigation', 'Project Vision', 'Quick Start', 'Development Workflow', 
    'Documentation Guide', 'Development Plans', 'Recent Changes', 'Recent Changes (Most Recent First)'
)

# Common command patterns that should be ignored
COMMAND_PATTERNS: Tuple[str, ...] = (
    'python ', 'pip ', 'git ', 'npm ', 'yarn ', 'docker ', 'kubectl '
)

# Common template patterns that should be ignored
TEMPLATE_PATTERNS: Tuple[str, ...] = (
    'test_<', '>.py', '{', '}', '*', '?'
)

# AI Development Tools Constants

# =============================================================================
# PROJECT STRUCTURE
# =============================================================================

# Core project directories (used by multiple tools)
PROJECT_DIRECTORIES: Tuple[str, ...] = (
    '.',  # Root directory
    'ai',
    'communication', 
    'core',
    'tasks',
    'ui',
    'user',
    'tests'
)

# Core modules for coverage and analysis (subset of PROJECT_DIRECTORIES)
CORE_MODULES: Tuple[str, ...] = (
    'core',
    'communication', 
    'ui',
    'tasks',
    'user',
    'ai'
)

# =============================================================================
# TOOL-SPECIFIC CONSTANTS
# =============================================================================

# Files to check for ASCII compliance (AI collaborator facing docs)
ASCII_COMPLIANCE_FILES: Tuple[str, ...] = (
    # AI development docs (most critical for AI collaboration)
    'ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md',
    'ai_development_docs/AI_ARCHITECTURE.md',
    'ai_development_docs/AI_DOCUMENTATION_GUIDE.md',
    'ai_development_docs/AI_CHANGELOG.md',
    'ai_development_docs/AI_ERROR_HANDLING_GUIDE.md',
    'ai_development_docs/AI_LOGGING_GUIDE.md',
    'ai_development_docs/AI_TESTING_GUIDE.md',
    'ai_development_docs/AI_REFERENCE.md',
    'ai_development_docs/AI_SESSION_STARTER.md',
    
    # Core development docs (important for AI collaboration)
    'DEVELOPMENT_WORKFLOW.md',
    'ARCHITECTURE.md',
    'DOCUMENTATION_GUIDE.md',
    
    # Development docs (important for AI collaboration)
    'development_docs/CHANGELOG_DETAIL.md',
    'development_docs/PLANS.md',
    
    # Project management files (important for AI collaboration)
    'TODO.md',
)

# Version sync key directories
VERSION_SYNC_DIRECTORIES: Dict[str, str] = {
    'ai_development_tools': 'ai_development_tools/',
    'ai_development_docs': 'ai_development_docs/',
    'development_docs': 'development_docs/',
    'core': 'core/',
    'communication': 'communication/',
    'ui': 'ui/',
    'tests': 'tests/',
    'logs': 'logs/',
    'scripts': 'scripts/',
    'data': 'data/',
    'resources': 'resources/',
    'styles': 'styles/',
    'tasks': 'tasks/',
    'user': 'user/',
    'ai': 'ai/'
}

# Common alternative directory paths for file resolution
ALTERNATIVE_DIRECTORIES: Tuple[str, ...] = (
    'ai_development_docs', 'development_docs', 'ai_development_tools',
    'core', 'communication', 'ui', 'tests', 'tests/behavior', 'tests/unit',
    'tests/integration', 'tests/ui', 'logs', 'scripts',
    'communication/communication_channels', 'communication/command_handlers',
    'communication/core', 'communication/message_processing'
)

def is_standard_library_module(module_name: str) -> bool:
    """Return True if *module_name* belongs to the Python standard library."""
    if not module_name:
        return False
    base = module_name.split('.', 1)[0]
    if base in STANDARD_LIBRARY_MODULES:
        return True
    if base in sys.builtin_module_names:
        return True
    for prefix in STANDARD_LIBRARY_PREFIXES:
        if module_name == prefix or module_name.startswith(prefix + '.'):
            return True
    return False

def is_local_module(module_name: str) -> bool:
    """Return True if *module_name* is part of the local project namespace."""
    if not module_name:
        return False
    base = module_name.split('.', 1)[0]
    return base in LOCAL_MODULE_PREFIXES

__all__ = [
    'ALTERNATIVE_DIRECTORIES',
    'ASCII_COMPLIANCE_FILES',
    'COMMAND_PATTERNS',
    'COMMON_CLASS_NAMES',
    'COMMON_CODE_PATTERNS',
    'COMMON_FUNCTION_NAMES',
    'COMMON_VARIABLE_NAMES',
    'CORRUPTED_ARTIFACT_PATTERNS',
    'CORE_MODULES',
    'DEFAULT_DOCS',
    'IGNORED_PATH_PATTERNS',
    'LOCAL_MODULE_PREFIXES',
    'PAIRED_DOCS',
    'PROJECT_DIRECTORIES',
    'STANDARD_LIBRARY_MODULES',
    'STANDARD_LIBRARY_PREFIXES',
    'TEMPLATE_PATTERNS',
    'THIRD_PARTY_LIBRARIES',
    'VERSION_SYNC_DIRECTORIES',
    'is_local_module',
    'is_standard_library_module',
]
