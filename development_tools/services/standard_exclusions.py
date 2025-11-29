#!/usr/bin/env python3
# TOOL_TIER: core

"""
Standard Exclusion Patterns for Development Tools

This module provides standardized exclusion patterns that can be reused
across all development tools to ensure consistent file filtering.

Exclusion patterns are loaded from external config file (development_tools_config.json)
if available, otherwise fall back to generic defaults. This makes the module portable
across different projects.

Usage:
    from development_tools.services.standard_exclusions import get_exclusions
    
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
if config._external_config is None:
    config.load_external_config()

# Default universal exclusions (generic patterns - should work for most projects)
# These are fallbacks if external config doesn't provide exclusions
_DEFAULT_UNIVERSAL_EXCLUSIONS = [
    # Python cache and compiled files
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '*.pyi',
    
    # Virtual environments
    'venv',
    '.venv',
    'env',
    '.env',
    'node_modules',
    
    # Git and version control
    '.git',
    '.gitignore',
    '.gitattributes',
    
    # IDE and editor files
    '.vscode',
    '.idea',
    '*.swp',
    '*.swo',
    '*~',
    '.cursorignore',
    
    # OS generated files
    '.DS_Store',
    'Thumbs.db',
    'desktop.ini',
    
    # Archive and backup directories
    'archive',
    'backup*',
    'backups',
    
    # Test artifacts
    '.pytest_cache',
    'tests/__pycache__',
    'tests/.pytest_cache',
    'tests/logs/',
    'tests/data/',
    'tests/temp/',
    'tests/fixtures/',
    
    # Generated files (should be excluded everywhere)
    '*/generated/*',
    '*/ui/generated/*',
    '*/pyscript*',
    '*/shibokensupport/*',
    '*/signature_bootstrap.py',
]

def _load_universal_exclusions() -> List[str]:
    """Load universal exclusions from config or return defaults."""
    exclusions_config = config.get_exclusions_config()
    if exclusions_config and 'universal_exclusions' in exclusions_config:
        return exclusions_config['universal_exclusions']
    return _DEFAULT_UNIVERSAL_EXCLUSIONS.copy()

# Universal exclusions - loaded from config or defaults
UNIVERSAL_EXCLUSIONS = _load_universal_exclusions()

# Default tool-specific exclusions (empty by default - projects can override via config)
_DEFAULT_TOOL_EXCLUSIONS = {}

def _load_tool_exclusions() -> Dict[str, List[str]]:
    """Load tool-specific exclusions from config or return defaults."""
    exclusions_config = config.get_exclusions_config()
    if exclusions_config and 'tool_exclusions' in exclusions_config:
        return exclusions_config['tool_exclusions']
    return _DEFAULT_TOOL_EXCLUSIONS.copy()

# Tool-specific exclusions - loaded from config or defaults
TOOL_EXCLUSIONS = _load_tool_exclusions()

# Default context-specific exclusions (generic patterns)
_DEFAULT_CONTEXT_EXCLUSIONS = {
    'recent_changes': [],
    'production': [
        # Production should exclude development files (generic patterns)
        'development_tools/*',
        '*/development_tools/*',
        'tests/*',
        '*/tests/*',
        '*/test_*',
        'scripts/*',
        '*/scripts/*',
        'archive/*',
        '*/archive/*',
    ],
    'development': [
        # Development can include most files but exclude sensitive data
        '*/data/*',
        '*/logs/*',
        '*/backup*',
        '*/backups/*',
    ],
    'testing': [
        # Testing should exclude generated files and data
        '*/generated/*',
        '*/ui/generated/*',
        '*/data/*',
        '*/logs/*',
        '*/backup*',
        '*/backups/*',
    ]
}

def _load_context_exclusions() -> Dict[str, List[str]]:
    """Load context-specific exclusions from config or return defaults."""
    exclusions_config = config.get_exclusions_config()
    if exclusions_config and 'context_exclusions' in exclusions_config:
        # Merge with defaults to ensure all contexts exist
        result = _DEFAULT_CONTEXT_EXCLUSIONS.copy()
        result.update(exclusions_config['context_exclusions'])
        return result
    return _DEFAULT_CONTEXT_EXCLUSIONS.copy()

# Context-specific exclusions - loaded from config or defaults
CONTEXT_EXCLUSIONS = _load_context_exclusions()

def get_exclusions(tool_type: str = None, context: str = 'development') -> list:
    """
    Get exclusion patterns for a specific tool type and context.
    
    Args:
        tool_type: Type of tool ('coverage', 'analysis', 'documentation', 'version_sync', 'file_operations')
        context: Context ('production', 'development', 'testing')
    
    Returns:
        List of exclusion patterns
    """
    exclusions = UNIVERSAL_EXCLUSIONS.copy()
    
    # Add tool-specific exclusions
    if tool_type and tool_type in TOOL_EXCLUSIONS:
        exclusions.extend(TOOL_EXCLUSIONS[tool_type])
    
    # Add context-specific exclusions
    if context and context in CONTEXT_EXCLUSIONS:
        exclusions.extend(CONTEXT_EXCLUSIONS[context])
    
    return exclusions

def should_exclude_file(file_path, tool_type: str = None, context: str = 'development') -> bool:
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
    exclusions = get_exclusions(tool_type, context)
    
    # Convert Path object to string if needed
    file_path_str = str(file_path)
    
    for pattern in exclusions:
        # Handle wildcard patterns with fnmatch
        if fnmatch.fnmatch(file_path_str, pattern) or pattern in file_path_str:
            return True
    
    return False

def get_coverage_exclusions() -> list:
    """Get exclusions specifically for coverage analysis."""
    return get_exclusions('coverage', 'development')

def get_analysis_exclusions() -> list:
    """Get exclusions specifically for code analysis."""
    return get_exclusions('analysis', 'development')

def get_documentation_exclusions() -> list:
    """Get exclusions specifically for documentation tools."""
    return get_exclusions('documentation', 'development')

def get_version_sync_exclusions() -> list:
    """Get exclusions specifically for version synchronization."""
    return get_exclusions('version_sync', 'development')

def get_file_operations_exclusions() -> list:
    """Get exclusions specifically for file operations."""
    return get_exclusions('file_operations', 'development')

# =============================================================================
# GENERATED FILES & EXCLUSIONS
# =============================================================================

def _load_generated_ai_files() -> Tuple[str, ...]:
    """Load generated AI files list from config or return defaults."""
    exclusions_config = config.get_exclusions_config()
    if exclusions_config and 'generated_ai_files' in exclusions_config:
        return tuple(exclusions_config['generated_ai_files'])
    # Default: empty (projects should define their own)
    return ()

def _load_generated_doc_files() -> Tuple[str, ...]:
    """Load generated doc files list from config or return defaults."""
    exclusions_config = config.get_exclusions_config()
    if exclusions_config and 'generated_doc_files' in exclusions_config:
        return tuple(exclusions_config['generated_doc_files'])
    # Default: empty (projects should define their own)
    return ()

# Generated AI status files (loaded from config)
GENERATED_AI_FILES: Tuple[str, ...] = _load_generated_ai_files()

# Generated documentation files (loaded from config)
GENERATED_DOC_FILES: Tuple[str, ...] = _load_generated_doc_files()

# All generated files (combination of AI and doc files)
ALL_GENERATED_FILES: Tuple[str, ...] = GENERATED_AI_FILES + GENERATED_DOC_FILES

def _load_standard_exclusion_patterns() -> Tuple[str, ...]:
    """Load standard exclusion patterns from config or return defaults."""
    exclusions_config = config.get_exclusions_config()
    if exclusions_config and 'standard_exclusion_patterns' in exclusions_config:
        return tuple(exclusions_config['standard_exclusion_patterns'])
    # Default generic patterns
    return (
        'logs/',
        'data/',
        'resources/',
        'coverage_html/',
        '__pycache__/',
        '.pytest_cache/',
        'venv/',
        '.venv/',
        'htmlcov/',
        'archive/',
        'ui/generated/',
        '*.log',
        '.coverage',
        'coverage.xml',
        '*.html'
    )

# Standard exclusion patterns (used by multiple tools)
STANDARD_EXCLUSION_PATTERNS: Tuple[str, ...] = _load_standard_exclusion_patterns()

# =============================================================================
# TOOL-SPECIFIC EXCLUSIONS
# =============================================================================

def _load_unused_imports_init_files() -> Tuple[str, ...]:
    """Load unused imports init files from config or return defaults."""
    exclusions_config = config.get_exclusions_config()
    if exclusions_config and 'unused_imports_init_files' in exclusions_config:
        return tuple(exclusions_config['unused_imports_init_files'])
    # Default: empty (projects should define their own)
    return ()

def _load_legacy_preserve_files() -> Tuple[str, ...]:
    """Load legacy preserve files from config or return defaults."""
    exclusions_config = config.get_exclusions_config()
    if exclusions_config and 'legacy_preserve_files' in exclusions_config:
        return tuple(exclusions_config['legacy_preserve_files'])
    # Default: empty (projects should define their own)
    return ()

# Unused imports checker specific files
UNUSED_IMPORTS_INIT_FILES: Tuple[str, ...] = _load_unused_imports_init_files()

# Legacy cleanup preserve files
LEGACY_PRESERVE_FILES: Tuple[str, ...] = _load_legacy_preserve_files()

# Documentation sync checker placeholders
DOC_SYNC_PLACEHOLDERS: Dict[str, str] = {
    '__pycache__': '    (Python cache files)',
    '.pytest_cache': '    (pytest cache files)',
    '.venv': '    (virtual environment files)',
    'backups': '    (backup files)',
    'htmlcov': '    (HTML coverage reports)',
    'archive': '    (archived files)'
}

# Example usage
if __name__ == "__main__":
    print("Coverage exclusions:")
    for pattern in get_coverage_exclusions():
        print(f"  {pattern}")
    
    print("\nAnalysis exclusions:")
    for pattern in get_analysis_exclusions():
        print(f"  {pattern}")
