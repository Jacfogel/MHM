#!/usr/bin/env python3
"""
Standard Exclusion Patterns for MHM Development Tools

This module provides standardized exclusion patterns that can be reused
across all development tools to ensure consistent file filtering.

Usage:
    from ai_development_tools.services.standard_exclusions import get_exclusions
    
    # Get exclusions for a specific tool type
    exclusions = get_exclusions('coverage')
    exclusions = get_exclusions('analysis')
    exclusions = get_exclusions('documentation')
"""

from typing import Tuple, Dict

# Universal exclusions - should be excluded from almost everything
UNIVERSAL_EXCLUSIONS = [
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
    
    # Scripts directory (not part of main codebase)
    'scripts',
    'scripts/*',
    'scripts/**/*',
    
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
    
    # Entry points (should be excluded everywhere)
    'run_mhm.py',
    '*/run_mhm.py',
    'run_tests.py',
    '*/run_tests.py',
]

# Tool-specific exclusions (minimal - only truly tool-specific patterns)
TOOL_EXCLUSIONS = {
    # Most exclusions are now handled by UNIVERSAL_EXCLUSIONS and CONTEXT_EXCLUSIONS
    # Only keep truly tool-specific exclusions here
}

# Context-specific exclusions
CONTEXT_EXCLUSIONS = {
    'recent_changes': [
        # Exclude generated files from recent changes
        'ai_development_tools/AI_PRIORITIES.md',
        'ai_development_tools/AI_STATUS.md',
        'ai_development_tools/consolidated_report.txt',
        'ai_development_tools/ai_audit_detailed_results.json',
        'ai_development_docs/AI_MODULE_DEPENDENCIES.md',
        'ai_development_docs/AI_FUNCTION_REGISTRY.md',
        'development_docs/DIRECTORY_TREE.md',
        'development_docs/FUNCTION_REGISTRY_DETAIL.md',
        'development_docs/LEGACY_REFERENCE_REPORT.md',
        'development_docs/MODULE_DEPENDENCIES_DETAIL.md',
        'ui/generated/*',
        '*/ui/generated/*',
        # Windows path variants
        'ai_development_tools\\AI_PRIORITIES.md',
        'ai_development_tools\\AI_STATUS.md',
        'ai_development_tools\\consolidated_report.txt',
        'ai_development_tools\\ai_audit_detailed_results.json',
        'ai_development_docs\\AI_MODULE_DEPENDENCIES.md',
        'ai_development_docs\\AI_FUNCTION_REGISTRY.md',
        'development_docs\\DIRECTORY_TREE.md',
        'development_docs\\FUNCTION_REGISTRY_DETAIL.md',
        'development_docs\\LEGACY_REFERENCE_REPORT.md',
        'development_docs\\MODULE_DEPENDENCIES_DETAIL.md',
        'ui\\generated\\*',
        '*\\ui\\generated\\*',
    ],
    'production': [
        # Production should exclude development files
        'ai_development_tools/*',
        '*/ai_development_tools/*',
        'ai_development_docs/*',
        '*/ai_development_docs/*',
        'development_docs/*',
        '*/development_docs/*',
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

# Generated AI status files (always excluded from recent changes)
GENERATED_AI_FILES: Tuple[str, ...] = (
    'ai_development_tools/AI_PRIORITIES.md',
    'ai_development_tools/AI_STATUS.md', 
    'ai_development_tools/consolidated_report.txt',
    'ai_development_tools/ai_audit_detailed_results.json',
)

# Generated documentation files (excluded from most tools)
GENERATED_DOC_FILES: Tuple[str, ...] = (
    'development_docs/UNUSED_IMPORTS_REPORT.md',
    'development_docs/TEST_COVERAGE_EXPANSION_PLAN.md',
    'development_docs/MODULE_DEPENDENCIES_DETAIL.md',
    'development_docs/LEGACY_REFERENCE_REPORT.md',
    'development_docs/FUNCTION_REGISTRY_DETAIL.md',
    'development_docs/DIRECTORY_TREE.md',
    'development_docs/CHANGELOG_DETAIL.md',
    'ai_development_docs/AI_MODULE_DEPENDENCIES.md',
    'ai_development_docs/AI_FUNCTION_REGISTRY.md'
)

# All generated files (combination of AI and doc files)
ALL_GENERATED_FILES: Tuple[str, ...] = GENERATED_AI_FILES + GENERATED_DOC_FILES

# Standard exclusion patterns (used by multiple tools)
STANDARD_EXCLUSION_PATTERNS: Tuple[str, ...] = (
    'logs/',
    'data/',
    'resources/',
    'coverage_html/',
    '__pycache__/',
    '.pytest_cache/',
    'venv/',
    '.venv/',
    'htmlcov/',
    'scripts/',
    'archive/',
    'ui/generated/',
    '*.log',
    '.coverage',
    'coverage.xml',
    '*.html'
)

# =============================================================================
# TOOL-SPECIFIC EXCLUSIONS
# =============================================================================

# Unused imports checker specific files
UNUSED_IMPORTS_INIT_FILES: Tuple[str, ...] = (
    'ai_development_tools/__init__.py',
    'ai_development_tools/services/__init__.py',
)

# Legacy cleanup preserve files
LEGACY_PRESERVE_FILES: Tuple[str, ...] = (
    'CHANGELOG_DETAIL.md',
    'AI_CHANGELOG.md',
    'archive/',
    'development_docs/',
    'ai_development_docs/',
    'logs/',
    'TODO.md',
    'PLANS.md',
    'FUNCTION_REGISTRY',
    'MODULE_DEPENDENCIES',
    'LEGACY_REFERENCE_REPORT.md',
)

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
