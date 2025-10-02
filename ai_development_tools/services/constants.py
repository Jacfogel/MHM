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
    'QUICK_REFERENCE.md',
    'TODO.md',
    'development_docs/FUNCTION_REGISTRY_DETAIL.md',
    'development_docs/MODULE_DEPENDENCIES_DETAIL.md',
    'ai_development_docs/AI_SESSION_STARTER.md',
    'ai_development_docs/AI_DOCUMENTATION_GUIDE.md',
    'ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md',
    'ai_development_docs/AI_CHANGELOG.md',
    'ai_development_docs/AI_REFERENCE.md',
)

PAIRED_DOCS: Dict[str, str] = {
    'DEVELOPMENT_WORKFLOW.md': 'ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md',
    'ARCHITECTURE.md': 'ai_development_docs/AI_ARCHITECTURE.md',
    'DOCUMENTATION_GUIDE.md': 'ai_development_docs/AI_DOCUMENTATION_GUIDE.md',
    'development_docs/CHANGELOG_DETAIL.md': 'ai_development_docs/AI_CHANGELOG.md',
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
    'CORRUPTED_ARTIFACT_PATTERNS',
    'DEFAULT_DOCS',
    'LOCAL_MODULE_PREFIXES',
    'PAIRED_DOCS',
    'STANDARD_LIBRARY_MODULES',
    'STANDARD_LIBRARY_PREFIXES',
    'is_local_module',
    'is_standard_library_module',
]
