#!/usr/bin/env python3
"""
Standard Exclusion Patterns for MHM Development Tools

This module provides standardized exclusion patterns that can be reused
across all development tools to ensure consistent file filtering.

Usage:
    from ai_development_tools.standard_exclusions import get_exclusions
    
    # Get exclusions for a specific tool type
    exclusions = get_exclusions('coverage')
    exclusions = get_exclusions('analysis')
    exclusions = get_exclusions('documentation')
"""

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

def should_exclude_file(file_path: str, tool_type: str = None, context: str = 'development') -> bool:
    """
    Check if a file should be excluded based on standard patterns.
    
    Args:
        file_path: Path to the file to check
        tool_type: Type of tool
        context: Context
    
    Returns:
        True if file should be excluded
    """
    import fnmatch
    exclusions = get_exclusions(tool_type, context)
    
    for pattern in exclusions:
        # Handle wildcard patterns with fnmatch
        if fnmatch.fnmatch(file_path, pattern) or pattern in file_path:
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

# Example usage
if __name__ == "__main__":
    print("Coverage exclusions:")
    for pattern in get_coverage_exclusions():
        print(f"  {pattern}")
    
    print("\nAnalysis exclusions:")
    for pattern in get_analysis_exclusions():
        print(f"  {pattern}")
