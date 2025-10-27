# AI Tools Configuration
"""
Configuration settings for AI collaboration tools.
Optimized for AI assistants to get concise, actionable information about the codebase.
"""

from pathlib import Path

# Project-specific settings
# Handle both direct execution and runner execution
import os
if os.path.basename(os.getcwd()) == 'ai_development_tools':
    PROJECT_ROOT = ".."  # Running from ai_development_tools directory
else:
    PROJECT_ROOT = "."   # Running from project root via runner
SCAN_DIRECTORIES = [
    'core',
    'communication', 
    'ui',
    'user',
    'tasks',
    'tests',
    'ai'                     # AI chatbot and context building
    # Note: 'scripts' and 'ai_development_tools' excluded per standard_exclusions.py
]

# AI Collaboration Optimization
AI_COLLABORATION = {
    'concise_output': True,           # Generate concise summaries for AI context
    'detailed_files': True,           # Save detailed results to files for reference
    'actionable_insights': True,      # Focus on actionable recommendations
    'context_aware': True,            # Adapt output based on what AI needs to know
    'priority_issues': True,          # Highlight critical issues first
    'integration_mode': True,         # Enable tool integration and data sharing
}

# Function discovery settings
FUNCTION_DISCOVERY = {
    'moderate_complexity_threshold': 50,   # Functions above this complexity need review
    'high_complexity_threshold': 100,      # Functions above this complexity need refactoring
    'critical_complexity_threshold': 200,  # Functions above this complexity are critical
    'min_docstring_length': 10,            # Minimum docstring length to be considered documented
    'handler_keywords': [                  # Keywords that indicate handler/utility functions
        'handle', 'process', 'validate', 'check', 'get', 'set', 'save', 'load',
        'create', 'update', 'delete', 'manage', 'configure', 'setup'
    ],
    'test_keywords': [                     # Keywords that indicate test functions
        'test_', 'test', 'check_', 'verify_', 'assert_'
    ],
    'critical_functions': [                # Functions that are critical for system operation
        'main', 'run', 'start', 'stop', 'init', 'setup', 'validate'
    ]
}

# Validation settings
VALIDATION = {
    'documentation_coverage_threshold': 80.0,  # Minimum acceptable documentation coverage
    'moderate_complexity_warning': 50,         # Functions above this complexity get warnings
    'high_complexity_warning': 100,            # Functions above this complexity need attention
    'critical_complexity_warning': 200,        # Functions above this complexity are critical
    'duplicate_function_warning': True,        # Warn about duplicate function names
    'missing_docstring_warning': True,        # Warn about functions without docstrings
    'critical_issues_first': True,            # Show critical issues before minor ones
}

# Audit settings
AUDIT = {
    'include_generated_files': False,          # Include auto-generated UI files
    'include_test_files': True,               # Include test files in analysis
    'include_legacy_files': False,            # Include deprecated/legacy files
    'max_output_lines': 20,                   # Maximum lines to show in concise reports
    'save_detailed_results': True,            # Save detailed results to files
    'generate_summary': True,                 # Generate executive summary
    'highlight_issues': True,                 # Highlight issues that need attention
}

# Output formatting for AI collaboration
OUTPUT = {
    'use_emojis': False,                      # No emojis for cleaner AI consumption
    'show_progress': False,                   # Minimal progress indicators
    'color_output': False,                    # No colors for AI consumption
    'detailed_reports': False,                # Save detailed reports to files instead
    'concise_format': True,                   # Use concise, scannable format
    'priority_indicators': True,              # Use indicators like [CRITICAL], [WARN], [INFO]
    'action_items': True,                     # Clearly mark actionable items
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

# Quick audit settings optimized for AI
QUICK_AUDIT = {
    'run_function_audit': True,
    'run_dependency_audit': True,
    'run_documentation_audit': True,
    'run_validation': True,
    'save_results': True,
    'results_file': 'ai_development_tools/ai_audit_detailed_results.json',
    'issues_file': 'ai_development_tools/critical_issues.txt',
    'audit_scripts': [
        'function_discovery.py',
        'decision_support.py',
        'audit_function_registry.py',
        'audit_module_dependencies.py',
        'analyze_documentation.py',
        'error_handling_coverage.py',
        'documentation_sync_checker.py'
    ],
    'concise_output': True,
    'prioritize_issues': True
}

# Version sync settings
VERSION_SYNC = {
    'ai_docs': [
        "ai_development_docs/AI_ARCHITECTURE.md",
        "ai_development_docs/AI_CHANGELOG.md",
        "ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md",
        "ai_development_docs/AI_DOCUMENTATION_GUIDE.md",
        "ai_development_docs/AI_REFERENCE.md",
        "ai_development_docs/AI_SESSION_STARTER.md",
        "ai_development_tools/README.md"
    ],
    'generated_ai_docs': [
        "ai_development_docs/AI_FUNCTION_REGISTRY.md",
        "ai_development_docs/AI_MODULE_DEPENDENCIES.md"
    ],
    'docs': [
        "README.md",
        "development_docs/CHANGELOG_DETAIL.md",
        "TODO.md",
        "DEVELOPMENT_WORKFLOW.md",
        "DOCUMENTATION_GUIDE.md",
        "PROJECT_VISION.md",
        "development_docs/DOCUMENTATION_SYNC_CHECKLIST.md",
        "development_docs/PLANS.md",
        "ARCHITECTURE.md",
        "QUICK_REFERENCE.md",
        "HOW_TO_RUN.md"
    ],
    'generated_docs': [
        "development_docs/FUNCTION_REGISTRY_DETAIL.md",
        "development_docs/MODULE_DEPENDENCIES_DETAIL.md",
        "development_docs/DIRECTORY_TREE.md",
        "development_docs/LEGACY_REFERENCE_REPORT.md"
    ],
    'core': [
        "run_mhm.py",
        "core/service.py",
        "core/config.py",
        "requirements.txt",
        ".gitignore"
    ],
    'cursor_rules': [
        ".cursor/rules/*.mdc"
    ],
    'cursor_commands': [
        ".cursor/commands/README.md"
    ],
    'communication_docs': [
        "communication/communication_channels/discord/DISCORD.md"
    ],
    'core_docs': [
        "core/ERROR_HANDLING_GUIDE.md"
    ],
    'logs_docs': [
        "logs/LOGGING_GUIDE.md"
    ],
    'scripts_docs': [
        "scripts/README.md"
    ],
    'tests_docs': [
        "tests/MANUAL_TESTING_GUIDE.md",
        "tests/TESTING_GUIDE.md"
    ],
    'core_system_files': [
        "run_mhm.py",
        "core/service.py",
        "core/config.py"
    ],
    'documentation_patterns': [
        "*.md"
    ],
    'exclude_patterns': [
        "*.pyc",
        "__pycache__",
        ".git",
        ".venv"
    ]
}

# Workflow configuration
WORKFLOW = {
    'audit_first': True,                      # Always run audit before other operations
    'validate_results': True,                 # Validate results before presenting
    'require_user_approval': False,           # AI tools don't need user approval
    'save_intermediate_results': True,        # Save intermediate results for debugging
    'generate_action_items': True,            # Generate clear action items
    'prioritize_by_impact': True,             # Prioritize issues by potential impact
}

# Documentation configuration
DOCUMENTATION = {
    'auto_generate': True,                    # Auto-generate documentation
    'preserve_manual_content': True,          # Preserve manual enhancements
    'update_frequency': 'on_demand',          # Update when requested
    'coverage_target': 95.0,                  # Target documentation coverage
    'quality_threshold': 80.0,                # Minimum quality score
}

# Auto-documentation settings
AUTO_DOCUMENT = {
    'enabled': True,                          # Enable auto-documentation
    'template_generation': True,              # Generate templates for missing docs
    'quality_check': True,                    # Check documentation quality
    'suggest_improvements': True,             # Suggest improvements
    'preserve_manual_work': True,             # Preserve manual enhancements
}

# AI validation configuration
AI_VALIDATION = {
    'completeness_threshold': 90.0,           # Minimum completeness score
    'accuracy_threshold': 85.0,               # Minimum accuracy score
    'consistency_threshold': 80.0,            # Minimum consistency score
    'actionable_threshold': 75.0,             # Minimum actionable score
    'critical_issues_weight': 3.0,            # Weight for critical issues
    'warning_issues_weight': 1.5,             # Weight for warning issues
    'info_issues_weight': 1.0,                # Weight for info issues
}

# Helper functions
def get_project_root():
    """Get the project root directory."""
    return Path(PROJECT_ROOT)

def get_scan_directories():
    """Get the directories to scan for analysis."""
    return SCAN_DIRECTORIES

def get_function_discovery_config():
    """Get function discovery configuration."""
    return FUNCTION_DISCOVERY

def get_validation_config():
    """Get validation configuration."""
    return VALIDATION

def get_audit_config():
    """Get audit configuration."""
    return AUDIT

def get_output_config():
    """Get output formatting configuration."""
    return OUTPUT

def get_workflow_config():
    """Get workflow configuration."""
    return WORKFLOW

def get_documentation_config():
    """Get documentation configuration."""
    return DOCUMENTATION

def get_auto_document_config():
    """Get auto-documentation configuration."""
    return AUTO_DOCUMENT

def get_ai_validation_config():
    """Get AI validation configuration."""
    return AI_VALIDATION

def get_ai_collaboration_config():
    """Get AI collaboration optimization configuration."""
    return AI_COLLABORATION

def get_quick_audit_config():
    """Get quick audit configuration."""
    return QUICK_AUDIT

def get_version_sync_config():
    """Get version sync configuration."""
    return VERSION_SYNC 