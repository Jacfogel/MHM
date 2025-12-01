# TOOL_TIER: core

# AI Tools Configuration
"""
Configuration settings for AI collaboration tools.
Optimized for AI assistants to get concise, actionable information about the codebase.

NOTE: This module contains MHM-specific default values. For other projects, override these
via development_tools_config.json in the project root. All getter functions check external
config first, then fall back to these defaults.
"""

from pathlib import Path
import json
import os
from typing import Optional, Dict, Any

# External config cache (loaded from file if provided)
_external_config: Optional[Dict[str, Any]] = None
_config_file_path: Optional[Path] = None

def load_external_config(config_path: Optional[str] = None) -> bool:
    """
    Load configuration from an external JSON file.
    
    Args:
        config_path: Path to config file (JSON format). If None, looks for 
                     'development_tools_config.json' in project root.
    
    Returns:
        True if config was loaded successfully, False otherwise.
    """
    global _external_config, _config_file_path
    
    if config_path:
        config_file = Path(config_path).resolve()
    else:
        # Try to find config in development_tools/config/ first, then project root
        project_root = _get_default_project_root()
        # First check in development_tools/config/
        config_file = project_root / 'development_tools' / 'config' / 'development_tools_config.json'
        if not config_file.exists():
            # Fallback to project root for backward compatibility
            config_file = project_root / 'development_tools_config.json'
    
    if not config_file.exists():
        _external_config = None
        _config_file_path = None
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            _external_config = json.load(f)
        _config_file_path = config_file
        return True
    except Exception as e:
        # Log error but don't fail - fall back to defaults
        _external_config = None
        _config_file_path = None
        return False

def _get_external_value(key: str, default: Any) -> Any:
    """Get value from external config if available, otherwise return default."""
    if _external_config is None:
        return default
    # Support nested keys like "paths.project_root"
    keys = key.split('.')
    value = _external_config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value

def get_external_value(key: str, default: Any) -> Any:
    """Public API to get value from external config."""
    return _get_external_value(key, default)

def _get_default_project_root() -> Path:
    """Get default project root based on current working directory."""
    if os.path.basename(os.getcwd()) == 'development_tools':
        return Path("..")
    else:
        return Path(".")

# Project-specific settings
# Handle both direct execution and runner execution
# NOTE: Hardcoded defaults are minimal/generic. Projects should provide development_tools_config.json
# for complete configuration. These defaults are fallbacks only.
_DEFAULT_PROJECT_ROOT = _get_default_project_root()
PROJECT_ROOT = str(_DEFAULT_PROJECT_ROOT)
# Generic default scan directories (should be overridden via config file)
SCAN_DIRECTORIES = []  # Empty by default - requires config file

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

# Error handling settings (for analyze_error_handling.py)
# NOTE: Defaults are generic. Projects should provide error_handling section in config file.
ERROR_HANDLING = {
    'decorator_names': ['@handle_errors', 'handle_errors', 'error_handler'],
    'exception_base_classes': ['BaseError', 'DataError', 'ConfigurationError', 'CommunicationError', 'ValidationError', 'AIError'],
    'error_handler_functions': ['handle_file_error', 'handle_network_error', 'handle_communication_error', 'handle_configuration_error', 'handle_validation_error', 'handle_ai_error', 'safe_file_operation'],
    'generic_exceptions': {
        'Exception': 'BaseError',
        'ValueError': 'ValidationError or DataError',
        'KeyError': 'DataError or ConfigurationError',
        'TypeError': 'ValidationError or DataError'
    },
    'critical_function_keywords': {
        'file_operations': ['open', 'read', 'write', 'save', 'load'],
        'network_operations': ['send', 'receive', 'connect', 'request'],
        'data_operations': ['parse', 'serialize', 'deserialize', 'validate'],
        'user_operations': ['create', 'update', 'delete', 'authenticate'],
        'ai_operations': ['generate', 'process', 'analyze', 'classify']
    }
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
# NOTE: Paths are relative to project root. Projects should provide config file.
QUICK_AUDIT = {
    'run_function_audit': True,
    'run_dependency_audit': True,
    'run_documentation_audit': True,
    'run_validation': True,
    'save_results': True,
    'results_file': 'development_tools/reports/analysis_detailed_results.json',  # Generic path - override via config
    'issues_file': 'development_tools/critical_issues.txt',  # Generic path - override via config
    'audit_scripts': [],  # Empty by default - requires config file
    'concise_output': True,
    'prioritize_issues': True
}

# Version sync settings
# NOTE: Projects should provide config file. All paths are relative to project root.
VERSION_SYNC = {
    'ai_docs': [],  # Empty by default - requires config file
    'docs': [],  # Empty by default - requires config file
    'cursor_rules': [".cursor/rules/*.mdc"],  # Generic pattern
    'communication_docs': [],  # Empty by default - requires config file
    'core_docs': [],  # Empty by default - requires config file
    'logs_docs': [],  # Empty by default - requires config file
    'scripts_docs': [],  # Empty by default - requires config file
    'tests_docs': [],  # Empty by default - requires config file
    'documentation_patterns': ["*.md"],  # Generic pattern
    'exclude_patterns': ["*.pyc", "__pycache__", ".git", ".venv"]  # Generic patterns
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
    """Get the project root directory (from external config if available, otherwise default)."""
    external_root = _get_external_value('paths.project_root', None)
    if external_root:
        return Path(external_root)
    # Fall back to default logic
    if _external_config is None:
        # Use default detection
        if os.path.basename(os.getcwd()) == 'development_tools':
            return Path("..")
        else:
            return Path(".")
    return Path(PROJECT_ROOT)

def get_scan_directories():
    """
    Get the directories to scan for analysis (from external config if available, otherwise default).
    
    NOTE: Default is empty list. Projects must provide scan_directories in config file.
    """
    external_dirs = _get_external_value('paths.scan_directories', None)
    if external_dirs:
        return external_dirs
    return SCAN_DIRECTORIES  # Empty by default - requires config file

def get_project_name(default: str = 'Project') -> str:
    """Get project name from config (from external config if available, otherwise default)."""
    return _get_external_value('project.name', default)

def get_project_key_files(default: Optional[list] = None) -> list:
    """Get project key files from config (from external config if available, otherwise default)."""
    if default is None:
        default = ['requirements.txt']
    key_files = _get_external_value('project.key_files', default)
    return key_files if isinstance(key_files, list) else default

def get_project_core_system_files(default: Optional[list] = None) -> list:
    """Get project core system files from config (from external config if available, otherwise default).
    
    Checks project.core_system_files first, then falls back to project.key_files if not found.
    """
    if default is None:
        default = ['run_mhm.py', 'core/service.py', 'core/config.py', 'requirements.txt', '.gitignore']
    core_files = _get_external_value('project.core_system_files', None)
    # If core_system_files is empty or invalid, fall back to key_files
    if not core_files or not isinstance(core_files, list) or len(core_files) == 0:
        core_files = _get_external_value('project.key_files', default)
    return core_files if isinstance(core_files, list) else default

def get_analyze_functions_config():
    """Get analyze functions configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('analyze_functions', None)
    if external_config:
        result = FUNCTION_DISCOVERY.copy()
        result.update(external_config)
        return result
    return FUNCTION_DISCOVERY

def get_validation_config():
    """Get validation configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('validation', None)
    if external_config:
        result = VALIDATION.copy()
        result.update(external_config)
        return result
    return VALIDATION

def get_error_handling_config():
    """Get error handling configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('error_handling', None)
    if external_config:
        result = ERROR_HANDLING.copy()
        # Deep merge for nested dicts
        if 'generic_exceptions' in external_config and 'generic_exceptions' in result:
            result['generic_exceptions'].update(external_config.get('generic_exceptions', {}))
        if 'critical_function_keywords' in external_config and 'critical_function_keywords' in result:
            result['critical_function_keywords'].update(external_config.get('critical_function_keywords', {}))
        # Update other keys
        for key, value in external_config.items():
            if key not in ('generic_exceptions', 'critical_function_keywords'):
                result[key] = value
        return result
    return ERROR_HANDLING

def get_audit_config():
    """Get audit configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('audit', None)
    if external_config:
        result = AUDIT.copy()
        result.update(external_config)
        return result
    return AUDIT

def get_output_config():
    """Get output formatting configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('output', None)
    if external_config:
        result = OUTPUT.copy()
        result.update(external_config)
        return result
    return OUTPUT

def get_workflow_config():
    """Get workflow configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('workflow', None)
    if external_config:
        result = WORKFLOW.copy()
        result.update(external_config)
        return result
    return WORKFLOW

def get_documentation_config():
    """Get documentation configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('documentation', None)
    if external_config:
        result = DOCUMENTATION.copy()
        result.update(external_config)
        return result
    return DOCUMENTATION

def get_auto_document_config():
    """Get auto-documentation configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('auto_document', None)
    if external_config:
        result = AUTO_DOCUMENT.copy()
        result.update(external_config)
        return result
    return AUTO_DOCUMENT

def get_ai_validation_config():
    """Get AI validation configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('ai_validation', None)
    if external_config:
        result = AI_VALIDATION.copy()
        result.update(external_config)
        return result
    return AI_VALIDATION

def get_ai_collaboration_config():
    """Get AI collaboration optimization configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('ai_collaboration', None)
    if external_config:
        result = AI_COLLABORATION.copy()
        result.update(external_config)
        return result
    return AI_COLLABORATION

def get_fix_version_sync_config():
    """Get fix version sync configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('fix_version_sync', None)
    if external_config:
        # Merge external config with defaults (external takes precedence)
        result = VERSION_SYNC.copy()
        result.update(external_config)
        return result
    return VERSION_SYNC

def get_quick_audit_config():
    """Get quick audit configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('quick_audit', None)
    if external_config:
        # Merge external config with defaults (external takes precedence)
        result = QUICK_AUDIT.copy()
        result.update(external_config)
        return result
    return QUICK_AUDIT

def get_paths_config():
    """
    Get paths configuration (docs, logs, data directories).
    Returns dict with keys: docs_dir, logs_dir, data_dir, ai_docs_dir, development_docs_dir
    
    NOTE: Defaults are generic. Projects should provide config file for proper paths.
    """
    paths = {
        'docs_dir': _get_external_value('paths.docs_dir', 'docs'),  # Generic default
        'logs_dir': _get_external_value('paths.logs_dir', 'logs'),
        'data_dir': _get_external_value('paths.data_dir', 'data'),
        'ai_docs_dir': _get_external_value('paths.ai_docs_dir', 'docs/ai'),  # Generic default
        'development_docs_dir': _get_external_value('paths.development_docs_dir', 'docs'),  # Generic default
    }
    return paths

def get_exclusions_config():
    """
    Get exclusions configuration from external config.
    Returns dict with exclusion patterns organized by category.
    
    NOTE: Returns empty dict if no external config. standard_exclusions.py will use
    its internal defaults as fallback.
    """
    exclusions = _get_external_value('exclusions', {})
    return exclusions if isinstance(exclusions, dict) else {}

def get_constants_config():
    """
    Get constants configuration from external config.
    Returns dict with project-specific constants (default_docs, paired_docs, etc.).
    
    NOTE: Returns empty dict if no external config. constants.py will use
    its internal defaults as fallback.
    """
    constants = _get_external_value('constants', {})
    return constants if isinstance(constants, dict) else {}

# Documentation analysis configuration
# NOTE: Defaults are minimal. See development_tools_config.json.example for full examples.
DOCUMENTATION_ANALYSIS = {
    'heading_patterns': ['## ', '### '],  # Generic markdown patterns
    'placeholder_patterns': [r'TBD', r'TODO'],  # Minimal generic patterns
    'placeholder_flags': ['IGNORECASE'],
    'topic_keywords': {},  # Empty - projects should define their own
    'ignore_rules': [],
}

def get_documentation_analysis_config():
    """Get documentation analysis configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('documentation_analysis', None)
    if external_config:
        result = DOCUMENTATION_ANALYSIS.copy()
        # Deep merge for nested dicts
        if 'topic_keywords' in external_config and 'topic_keywords' in result:
            result['topic_keywords'].update(external_config.get('topic_keywords', {}))
        # Update other keys
        for key, value in external_config.items():
            if key != 'topic_keywords':
                result[key] = value
        return result
    return DOCUMENTATION_ANALYSIS

# Audit function registry configuration
# NOTE: Defaults are minimal. See development_tools_config.json.example for full examples.
AUDIT_FUNCTION_REGISTRY = {
    'registry_path': 'development_docs/FUNCTION_REGISTRY_DETAIL.md',  # Generic default path
    'high_complexity_min': 50,  # Generic threshold
    'top_complexity': 10,
    'top_undocumented': 5,
    'top_duplicates': 5,
    'error_sample_limit': 5,
    'max_complexity_json': 200,
    'max_undocumented_json': 200,
    'max_duplicates_json': 200,
}

def get_analyze_function_registry_config():
    """Get audit function registry configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('analyze_function_registry', None)
    if external_config:
        result = AUDIT_FUNCTION_REGISTRY.copy()
        result.update(external_config)
        return result
    return AUDIT_FUNCTION_REGISTRY

# Audit module dependencies configuration
AUDIT_MODULE_DEPENDENCIES = {
    'dependency_doc_path': 'development_docs/MODULE_DEPENDENCIES_DETAIL.md',  # Generic default
}

def get_analyze_module_dependencies_config():
    """Get audit module dependencies configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('analyze_module_dependencies', None)
    if external_config:
        result = AUDIT_MODULE_DEPENDENCIES.copy()
        result.update(external_config)
        return result
    return AUDIT_MODULE_DEPENDENCIES

# Audit package exports configuration
AUDIT_PACKAGE_EXPORTS = {
    'export_patterns': [],  # Patterns to identify exports
    'expected_exports': {},  # Expected exports by module
}

def get_analyze_package_exports_config():
    """Get audit package exports configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('analyze_package_exports', None)
    if external_config:
        result = AUDIT_PACKAGE_EXPORTS.copy()
        # Deep merge for nested dicts
        if 'expected_exports' in external_config and 'expected_exports' in result:
            result['expected_exports'].update(external_config.get('expected_exports', {}))
        # Update other keys
        for key, value in external_config.items():
            if key != 'expected_exports':
                result[key] = value
        return result
    return AUDIT_PACKAGE_EXPORTS

# Config validator configuration
CONFIG_VALIDATOR = {
    'config_schema': {},  # Expected config schema structure (empty = auto-detect)
    'validation_rules': {},  # Custom validation rules
}

def get_analyze_config_config():
    """Get config validator configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('analyze_config', None)
    if external_config:
        result = CONFIG_VALIDATOR.copy()
        # Deep merge for nested dicts
        if 'validation_rules' in external_config and 'validation_rules' in result:
            result['validation_rules'].update(external_config.get('validation_rules', {}))
        # Update other keys
        for key, value in external_config.items():
            if key != 'validation_rules':
                result[key] = value
        return result
    return CONFIG_VALIDATOR

# Validate AI work configuration
# NOTE: Defaults are minimal. See development_tools_config.json.example for full examples.
VALIDATE_AI_WORK = {
    'completeness_threshold': 90.0,  # Generic thresholds
    'accuracy_threshold': 85.0,
    'consistency_threshold': 80.0,
    'actionable_threshold': 75.0,
    'rule_sets': {},  # Empty - projects should define their own
    'rule_set_paths': [],
}

def get_analyze_ai_work_config():
    """Get validate AI work configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('analyze_ai_work', None)
    if external_config:
        result = VALIDATE_AI_WORK.copy()
        # Deep merge for nested dicts
        if 'rule_sets' in external_config and 'rule_sets' in result:
            result['rule_sets'].update(external_config.get('rule_sets', {}))
        # Update other keys
        for key, value in external_config.items():
            if key not in ('rule_sets',):
                result[key] = value
        return result
    return VALIDATE_AI_WORK

# Unused imports checker configuration
UNUSED_IMPORTS = {
    'pylint_command': ['python', '-m', 'pylint'],  # Pylint command as list
    'ignore_patterns': [],  # Patterns to ignore
    'type_stub_locations': [],  # Locations for type stubs (.pyi files)
    'timeout_seconds': 30,  # Timeout per file
}

def get_unused_imports_config():
    """Get unused imports checker configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('unused_imports', None)
    if external_config:
        result = UNUSED_IMPORTS.copy()
        result.update(external_config)
        return result
    return UNUSED_IMPORTS

# Quick status configuration
QUICK_STATUS = {
    'core_files': [],  # Will use project.key_files if empty
    'key_directories': [],  # Will use paths.scan_directories if empty
    'data_source_plugins': {},  # Plugin hooks for data sources (Discord, schedulers, etc.)
}

def get_quick_status_config():
    """Get quick status configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('quick_status', None)
    if external_config:
        result = QUICK_STATUS.copy()
        # Deep merge for nested dicts
        if 'data_source_plugins' in external_config and 'data_source_plugins' in result:
            result['data_source_plugins'].update(external_config.get('data_source_plugins', {}))
        # Update other keys
        for key, value in external_config.items():
            if key != 'data_source_plugins':
                result[key] = value
        return result
    return QUICK_STATUS

# System signals configuration
SYSTEM_SIGNALS = {
    'core_files': [],  # Will use project.key_files if empty
    'data_source_plugins': {},  # Plugin hooks for data sources
}

def get_system_signals_config():
    """Get system signals configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('system_signals', None)
    if external_config:
        result = SYSTEM_SIGNALS.copy()
        # Deep merge for nested dicts
        if 'data_source_plugins' in external_config and 'data_source_plugins' in result:
            result['data_source_plugins'].update(external_config.get('data_source_plugins', {}))
        # Update other keys
        for key, value in external_config.items():
            if key != 'data_source_plugins':
                result[key] = value
        return result
    return SYSTEM_SIGNALS

# Auto document functions configuration
# NOTE: Defaults are minimal. See development_tools_config.json.example for full examples.
AUTO_DOCUMENT_FUNCTIONS = {
    'template_paths': {},  # Empty - projects should define their own
    'doc_targets': {},  # Empty - projects should define their own
    'formatting_rules': {},  # Empty - projects should define their own
    'function_type_detection': {  # Minimal generic patterns
        'test_function': {'name_patterns': ['test_']},
        'special_method': {'name_pattern': '__.*__'},
        'constructor': {'name': '__init__'},
        'main_function': {'name': 'main'},
    },
}

def get_generate_function_docstrings_config():
    """Get generate function docstrings configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value('generate_function_docstrings', None)
    if external_config:
        result = AUTO_DOCUMENT_FUNCTIONS.copy()
        # Deep merge for nested dicts
        for key in ['template_paths', 'doc_targets', 'formatting_rules', 'function_type_detection']:
            if key in external_config and key in result:
                if isinstance(result[key], dict):
                    result[key].update(external_config.get(key, {}))
                else:
                    result[key] = external_config.get(key, result[key])
        # Update other keys
        for key, value in external_config.items():
            if key not in ('template_paths', 'doc_targets', 'formatting_rules', 'function_type_detection'):
                result[key] = value
        return result
    return AUTO_DOCUMENT_FUNCTIONS 
