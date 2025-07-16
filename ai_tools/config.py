# AI Tools Configuration
"""
Configuration settings for AI collaboration tools.
Customize these settings to optimize the tools for your project.
"""

# Project-specific settings
PROJECT_ROOT = "."
SCAN_DIRECTORIES = [
    'core',
    'bot', 
    'ui',
    'user',
    'tasks',
    'scripts',
    'tests'
]

# Function discovery settings
FUNCTION_DISCOVERY = {
    'max_complexity_threshold': 50,  # Functions above this complexity need attention
    'min_docstring_length': 10,      # Minimum docstring length to be considered documented
    'handler_keywords': [            # Keywords that indicate handler/utility functions
        'handle', 'process', 'validate', 'check', 'get', 'set', 'save', 'load',
        'create', 'update', 'delete', 'manage', 'configure', 'setup'
    ],
    'test_keywords': [               # Keywords that indicate test functions
        'test_', 'test', 'check_', 'verify_', 'assert_'
    ]
}

# Validation settings
VALIDATION = {
    'documentation_coverage_threshold': 80.0,  # Minimum acceptable documentation coverage
    'complexity_warning_threshold': 30,        # Functions above this complexity get warnings
    'duplicate_function_warning': True,        # Warn about duplicate function names
    'missing_docstring_warning': True,        # Warn about functions without docstrings
}

# Audit settings
AUDIT = {
    'include_generated_files': False,          # Include auto-generated UI files
    'include_test_files': True,               # Include test files in analysis
    'include_legacy_files': False,            # Include deprecated/legacy files
    'max_output_lines': 50,                   # Maximum lines to show in reports
}

# Output formatting
OUTPUT = {
    'use_emojis': True,                       # Use emojis in output for better readability
    'show_progress': True,                    # Show progress indicators
    'color_output': True,                     # Use colored output (if supported)
    'detailed_reports': True,                 # Generate detailed reports
}

# File patterns
FILE_PATTERNS = {
    'python_files': '*.py',
    'documentation_files': '*.md',
    'ui_files': '*.ui',
    'config_files': '*.json',
    'exclude_patterns': [
        '__pycache__',
        '.git',
        'venv',
        'env',
        'node_modules',
        '*.pyc',
        '*.pyo'
    ]
}

# Quick audit settings
QUICK_AUDIT = {
    'run_function_audit': True,
    'run_dependency_audit': True,
    'run_documentation_audit': True,
    'run_validation': True,
    'generate_summary': True,
    'save_results': True,
    'results_file': 'ai_audit_results.json'
} 