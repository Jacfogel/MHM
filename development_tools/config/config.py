# TOOL_TIER: core

# AI Tools Configuration
"""
Configuration settings for the development tools suite.
Defaults are intentionally generic and portable; project-specific values should be supplied
via an external config file. All getter functions check external config first, then fall back
to these defaults.

Default config path: development_tools/config/development_tools_config.json
"""

from pathlib import Path
import json
import os
from typing import Any

# External config cache (loaded from file if provided)
_external_config: dict[str, Any] | None = None
_config_file_path: Path | None = None


def load_external_config(config_path: str | None = None) -> bool:
    """
    Load configuration from an external JSON file.

    Args:
        config_path: Path to config file (JSON format). If None, looks for
                     'development_tools/config/development_tools_config.json'.

    Returns:
        True if config was loaded successfully, False otherwise.
    """
    global _external_config, _config_file_path

    if config_path:
        config_file = Path(config_path).resolve()
    else:
        # Try to find config in development_tools/config/
        project_root = _get_default_project_root()
        config_file = (
            project_root
            / "development_tools"
            / "config"
            / "development_tools_config.json"
        )

    if not config_file.exists():
        _external_config = None
        _config_file_path = None
        return False

    try:
        with open(config_file, encoding="utf-8") as f:
            _external_config = json.load(f)
        _config_file_path = config_file
        return True
    except Exception:
        # Log error but don't fail - fall back to defaults
        _external_config = None
        _config_file_path = None
        return False


def _get_external_value(key: str, default: Any) -> Any:
    """Get value from external config if available, otherwise return default."""
    if _external_config is None:
        return default
    # Support nested keys like "paths.project_root"
    keys = key.split(".")
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
    if os.path.basename(os.getcwd()) == "development_tools":
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
    "concise_output": True,  # Generate concise summaries for AI context
    "detailed_files": True,  # Save detailed results to files for reference
    "actionable_insights": True,  # Focus on actionable recommendations
    "context_aware": True,  # Adapt output based on what AI needs to know
    "priority_issues": True,  # Highlight critical issues first
    "integration_mode": True,  # Enable tool integration and data sharing
}

# Function discovery settings
FUNCTION_DISCOVERY = {
    "moderate_complexity_threshold": 50,  # Functions above this complexity need review
    "high_complexity_threshold": 100,  # Functions above this complexity need refactoring
    "critical_complexity_threshold": 200,  # Functions above this complexity are critical
    "min_docstring_length": 10,  # Minimum docstring length to be considered documented
    "handler_keywords": [  # Keywords that indicate handler/utility functions
        "handle",
        "process",
        "validate",
        "check",
        "get",
        "set",
        "save",
        "load",
        "create",
        "update",
        "delete",
        "manage",
        "configure",
        "setup",
    ],
    "test_keywords": [  # Keywords that indicate test functions
        "test_",
        "test",
        "check_",
        "verify_",
        "assert_",
    ],
    "critical_functions": [  # Functions that are critical for system operation
        "main",
        "run",
        "start",
        "stop",
        "init",
        "setup",
        "validate",
    ],
}

# Validation settings
VALIDATION = {
    "documentation_coverage_threshold": 80.0,  # Minimum acceptable documentation coverage
    "moderate_complexity_warning": 50,  # Functions above this complexity get warnings
    "high_complexity_warning": 100,  # Functions above this complexity need attention
    "critical_complexity_warning": 200,  # Functions above this complexity are critical
    "duplicate_function_warning": True,  # Warn about duplicate function names
    "missing_docstring_warning": True,  # Warn about functions without docstrings
    "critical_issues_first": True,  # Show critical issues before minor ones
}

# Error handling settings (for analyze_error_handling.py)
# NOTE: Defaults are generic. Projects should provide error_handling section in config file.
ERROR_HANDLING = {
    "decorator_names": ["@handle_errors", "handle_errors", "error_handler"],
    "exception_base_classes": [
        "BaseError",
        "DataError",
        "ConfigurationError",
        "CommunicationError",
        "ValidationError",
        "AIError",
    ],
    "error_handler_functions": [
        "handle_file_error",
        "handle_network_error",
        "handle_communication_error",
        "handle_configuration_error",
        "handle_validation_error",
        "handle_ai_error",
        "safe_file_operation",
    ],
    "generic_exceptions": {
        "Exception": "BaseError",
        "ValueError": "ValidationError or DataError",
        "KeyError": "DataError or ConfigurationError",
        "TypeError": "ValidationError or DataError",
    },
    "critical_function_keywords": {
        "file_operations": ["open", "read", "write", "save", "load"],
        "network_operations": ["send", "receive", "connect", "request"],
        "data_operations": ["parse", "serialize", "deserialize", "validate"],
        "user_operations": ["create", "update", "delete", "authenticate"],
        "ai_operations": ["generate", "process", "analyze", "classify"],
    },
    "phase1_keywords": {
        "file_io": ["open", "read", "write", "save", "load", "os.remove", "shutil.move"],
        "network": ["send", "receive", "connect", "request", "http", "api", "discord", "email"],
        "user_data": ["user_data", "profile", "account", "preferences", "task", "schedule", "checkin"],
        "ai": ["generate", "process", "analyze", "classify", "chatbot", "lm_studio"],
        "entry_point": ["main", "run", "start", "handle", "on_"],
    },
}

# Audit settings
AUDIT = {
    "include_generated_files": False,  # Include auto-generated UI files
    "include_test_files": True,  # Include test files in analysis
    "include_legacy_files": False,  # Include deprecated/legacy files
    "max_output_lines": 20,  # Maximum lines to show in concise reports
    "save_detailed_results": True,  # Save detailed results to files
    "generate_summary": True,  # Generate executive summary
    "highlight_issues": True,  # Highlight issues that need attention
}

# Output formatting for AI collaboration
OUTPUT = {
    "use_emojis": False,  # No emojis for cleaner AI consumption
    "show_progress": False,  # Minimal progress indicators
    "color_output": False,  # No colors for AI consumption
    "detailed_reports": False,  # Save detailed reports to files instead
    "concise_format": True,  # Use concise, scannable format
    "priority_indicators": True,  # Use indicators like [CRITICAL], [WARN], [INFO]
    "action_items": True,  # Clearly mark actionable items
}

# File patterns
# exclude_patterns removed from file_patterns; use exclusions.base_exclusions (LIST_OF_LISTS §9a)
FILE_PATTERNS = {
    "python_files": "*.py",
    "documentation_files": "*.md",
    "ui_files": "*.ui",
    "config_files": "*.json",
}

# Quick audit settings optimized for AI
# NOTE: Paths are relative to project root. Projects should provide config file.
QUICK_AUDIT = {
    "run_function_audit": True,
    "run_dependency_audit": True,
    "run_documentation_audit": True,
    "run_validation": True,
    "save_results": True,
    "results_file": "development_tools/reports/analysis_detailed_results.json",  # Generic path - override via config
    "audit_scripts": [],  # Empty by default - requires config file
    "concise_output": True,
    "prioritize_issues": True,
}

# Audit tier default: built from audit_tiers.py (canonical source for which tools run in each tier).
# Do not duplicate tool lists here; get_audit_tiers_config() builds from audit_tiers when no external config.
def _build_audit_tiers_default():
    try:
        from development_tools.shared.audit_tiers import (
            TIER1_TOOL_NAMES,
            get_expected_tools_for_tier,
        )
        return {
            "quick": {
                "tools": list(TIER1_TOOL_NAMES),
                "description": "Lightweight analysis - core metrics only",
            },
            "standard": {
                "tools": get_expected_tools_for_tier(2),
                "description": "Standard analysis - includes quality checks",
            },
            "full": {
                "tools": get_expected_tools_for_tier(3),
                "description": "Comprehensive analysis - includes coverage, dependencies, and improvement reports",
            },
        }
    except ImportError:
        return {
            "quick": {"tools": [], "description": "Lightweight analysis - core metrics only"},
            "standard": {"tools": [], "description": "Standard analysis - includes quality checks"},
            "full": {"tools": [], "description": "Comprehensive analysis"},
        }


AUDIT_TIERS = _build_audit_tiers_default()

# Version sync settings
# NOTE: Projects should provide config file. All paths are relative to project root.
VERSION_SYNC = {
    "ai_docs": [],  # Empty by default - requires config file
    "docs": [],  # Empty by default - requires config file
    "cursor_rules": [".cursor/rules/*.mdc"],  # Generic pattern
    "documentation_patterns": ["*.md"],  # Generic pattern
    # Category lists (communication_docs, core_docs, logs_docs, scripts_docs, tests_docs)
    # are derived from docs by path prefix in fix_version_sync.py; config override optional.
    # Exclusions: fix_version_sync uses get_exclusions("fix_version_sync", "development").
}

# Workflow configuration
WORKFLOW = {
    "audit_first": True,  # Always run audit before other operations
    "validate_results": True,  # Validate results before presenting
    "require_user_approval": False,  # AI tools don't need user approval
    "save_intermediate_results": True,  # Save intermediate results for debugging
    "generate_action_items": True,  # Generate clear action items
    "prioritize_by_impact": True,  # Prioritize issues by potential impact
}

# Documentation configuration
DOCUMENTATION = {
    "auto_generate": True,  # Auto-generate documentation
    "preserve_manual_content": True,  # Preserve manual enhancements
    "update_frequency": "on_demand",  # Update when requested
    "coverage_target": 95.0,  # Target documentation coverage
    "quality_threshold": 80.0,  # Minimum quality score
}

# Auto-documentation settings
AUTO_DOCUMENT = {
    "enabled": True,  # Enable auto-documentation
    "template_generation": True,  # Generate templates for missing docs
    "quality_check": True,  # Check documentation quality
    "suggest_improvements": True,  # Suggest improvements
    "preserve_manual_work": True,  # Preserve manual enhancements
}

# AI validation configuration
AI_VALIDATION = {
    "completeness_threshold": 90.0,  # Minimum completeness score
    "accuracy_threshold": 85.0,  # Minimum accuracy score
    "consistency_threshold": 80.0,  # Minimum consistency score
    "actionable_threshold": 75.0,  # Minimum actionable score
    "critical_issues_weight": 3.0,  # Weight for critical issues
    "warning_issues_weight": 1.5,  # Weight for warning issues
    "info_issues_weight": 1.0,  # Weight for info issues
}


# Helper functions
def get_project_root():
    """Get the project root directory (from external config if available, otherwise default)."""
    external_root = _get_external_value("paths.project_root", None)
    if external_root:
        return Path(external_root)
    # Fall back to default logic
    if _external_config is None:
        # Use default detection
        if os.path.basename(os.getcwd()) == "development_tools":
            return Path("..")
        else:
            return Path(".")
    return Path(PROJECT_ROOT)


def get_scan_directories():
    """
    Get the directories to scan for analysis.

    Uses paths.scan_directories if set; otherwise derives from constants.local_module_prefixes
    (excludes data, development_tools, notebook, scripts). See LIST_OF_LISTS.md §6.
    """
    external_dirs = _get_external_value("paths.scan_directories", None)
    if external_dirs and isinstance(external_dirs, (list, tuple)):
        return list(external_dirs)
    try:
        from development_tools.shared.constants import get_scan_directories_derived
        return list(get_scan_directories_derived())
    except ImportError:
        return list(SCAN_DIRECTORIES)


def get_project_name(default: str = "Project") -> str:
    """Get project name from config (from external config if available, otherwise default)."""
    return _get_external_value("project.name", default)


def get_project_key_files(default: list | None = None) -> list:
    """Get project key files from config (from external config if available, otherwise default)."""
    if default is None:
        default = ["requirements.txt"]
    key_files = _get_external_value("project.key_files", default)
    return key_files if isinstance(key_files, list) else default


def get_project_core_system_files(default: list | None = None) -> list:
    """Get project core system files from config (from external config if available, otherwise default).

    Checks project.core_system_files first, then falls back to project.key_files if not found.
    """
    if default is None:
        default = ["README.md", "requirements.txt", ".gitignore"]
    core_files = _get_external_value("project.core_system_files", None)
    # If core_system_files is empty or invalid, fall back to key_files
    if not core_files or not isinstance(core_files, list) or len(core_files) == 0:
        core_files = _get_external_value("project.key_files", default)
    return core_files if isinstance(core_files, list) else default


def get_analyze_functions_config():
    """Get analyze functions configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("analyze_functions", None)
    if external_config:
        result = FUNCTION_DISCOVERY.copy()
        result.update(external_config)
        return result
    return FUNCTION_DISCOVERY


def get_validation_config():
    """Get validation configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("validation", None)
    if external_config:
        result = VALIDATION.copy()
        result.update(external_config)
        return result
    return VALIDATION


def get_error_handling_config():
    """Get error handling configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("error_handling", None)
    if external_config:
        result = ERROR_HANDLING.copy()
        # Deep merge for nested dicts
        if "generic_exceptions" in external_config and "generic_exceptions" in result:
            result["generic_exceptions"].update(
                external_config.get("generic_exceptions", {})
            )
        if (
            "critical_function_keywords" in external_config
            and "critical_function_keywords" in result
        ):
            result["critical_function_keywords"].update(
                external_config.get("critical_function_keywords", {})
            )
        if (
            "phase1_keywords" in external_config
            and "phase1_keywords" in result
        ):
            result["phase1_keywords"].update(
                external_config.get("phase1_keywords", {})
            )
        # Update other keys
        for key, value in external_config.items():
            if key not in ("generic_exceptions", "critical_function_keywords", "phase1_keywords"):
                result[key] = value
        return result
    return ERROR_HANDLING


def get_audit_config():
    """Get audit configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("audit", None)
    if external_config:
        result = AUDIT.copy()
        result.update(external_config)
        return result
    return AUDIT


def get_output_config():
    """Get output formatting configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("output", None)
    if external_config:
        result = OUTPUT.copy()
        result.update(external_config)
        return result
    return OUTPUT


def get_workflow_config():
    """Get workflow configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("workflow", None)
    if external_config:
        result = WORKFLOW.copy()
        result.update(external_config)
        return result
    return WORKFLOW


def get_documentation_config():
    """Get documentation configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("documentation", None)
    if external_config:
        result = DOCUMENTATION.copy()
        result.update(external_config)
        return result
    return DOCUMENTATION


def get_auto_document_config():
    """Get auto-documentation configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("auto_document", None)
    if external_config:
        result = AUTO_DOCUMENT.copy()
        result.update(external_config)
        return result
    return AUTO_DOCUMENT


def get_ai_validation_config():
    """Get AI validation configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("ai_validation", None)
    if external_config:
        result = AI_VALIDATION.copy()
        result.update(external_config)
        return result
    return AI_VALIDATION


def get_ai_collaboration_config():
    """Get AI collaboration optimization configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("ai_collaboration", None)
    if external_config:
        result = AI_COLLABORATION.copy()
        result.update(external_config)
        return result
    return AI_COLLABORATION


def get_fix_version_sync_config():
    """Get fix version sync configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("fix_version_sync", None)
    if external_config:
        # Merge external config with defaults (external takes precedence)
        result = VERSION_SYNC.copy()
        result.update(external_config)
        return result
    return VERSION_SYNC


def get_quick_audit_config():
    """Get quick audit configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("quick_audit", None)
    if external_config:
        # Merge external config with defaults (external takes precedence)
        result = QUICK_AUDIT.copy()
        result.update(external_config)
        return result
    return QUICK_AUDIT


def get_audit_tiers_config():
    """Get audit tier configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("audit_tiers", None)
    if external_config:
        # Merge external config with defaults (external takes precedence)
        result = AUDIT_TIERS.copy()
        # Deep merge for nested dicts
        for tier in ["quick", "standard", "full"]:
            if tier in external_config:
                if tier in result:
                    result[tier] = {**result[tier], **external_config[tier]}
                else:
                    result[tier] = external_config[tier]
        return result
    return AUDIT_TIERS


def get_paths_config():
    """
    Get paths configuration (docs, logs, data directories).
    Returns dict with keys:
    docs_dir, logs_dir, data_dir, ai_docs_dir, development_docs_dir, tests_dir, tests_data_dir

    NOTE: Defaults are generic. Projects should provide config file for proper paths.
    """
    tests_dir = _get_external_value("paths.tests_dir", "tests")
    paths = {
        "docs_dir": _get_external_value("paths.docs_dir", "docs"),  # Generic default
        "logs_dir": _get_external_value("paths.logs_dir", "logs"),
        "data_dir": _get_external_value("paths.data_dir", "data"),
        "ai_docs_dir": _get_external_value(
            "paths.ai_docs_dir", "docs/ai"
        ),  # Generic default
        "development_docs_dir": _get_external_value(
            "paths.development_docs_dir", "docs"
        ),  # Generic default
        "tests_dir": tests_dir,
        "tests_data_dir": _get_external_value(
            "paths.tests_data_dir", f"{tests_dir}/data"
        ),
    }
    return paths


def get_data_freshness_config():
    """
    Get data freshness audit configuration (e.g. known deleted files to check for in caches).
    Returns dict with key: known_deleted_files (list of path strings).
    """
    default = {
        "known_deleted_files": [
            "development_tools/shared/operations.py",
            "development_docs/SESSION_SUMMARY_2025-12-07.md",
        ],
    }
    external = _get_external_value("data_freshness", None)
    if not isinstance(external, dict):
        return default
    files = external.get("known_deleted_files")
    if isinstance(files, list):
        default["known_deleted_files"] = [str(p) for p in files]
    return default


def get_exclusions_config():
    """
    Get exclusions configuration from external config.
    Returns dict with exclusion patterns organized by category.

    NOTE: Returns empty dict if no external config. standard_exclusions.py will use
    its internal defaults as fallback.
    """
    exclusions = _get_external_value("exclusions", {})
    return exclusions if isinstance(exclusions, dict) else {}


def get_constants_config():
    """
    Get constants configuration from external config.
    Returns dict with project-specific constants (default_docs, paired_docs, etc.).

    NOTE: Returns empty dict if no external config. constants.py will use
    its internal defaults as fallback.
    """
    constants = _get_external_value("constants", {})
    return constants if isinstance(constants, dict) else {}


def get_test_markers_config():
    """
    Get pytest test marker analysis configuration from external config.

    Returns:
        Dict with optional keys:
        - categories
        - directory_to_marker (derived from categories as identity map when absent; see LIST_OF_LISTS §9a)
        - transient_data_path_markers
        - ai_path_tokens
    """
    test_markers = _get_external_value("test_markers", {})
    if not isinstance(test_markers, dict):
        return {}
    result = dict(test_markers)
    # Derive directory_to_marker from categories when absent or empty (identity map)
    if "directory_to_marker" not in result or not result["directory_to_marker"]:
        categories = result.get("categories", ("unit", "integration", "behavior", "ui"))
        if isinstance(categories, (list, tuple)) and categories:
            result["directory_to_marker"] = {str(c): str(c) for c in categories if str(c).strip()}
    return result


# Documentation analysis configuration
# NOTE: Defaults are minimal. See development_tools_config.json.example for full examples.
DOCUMENTATION_ANALYSIS = {
    "heading_patterns": ["## ", "### "],  # Generic markdown patterns
    "placeholder_patterns": [r"TBD", r"TODO"],  # Minimal generic patterns
    "placeholder_flags": ["IGNORECASE"],
    "topic_keywords": {},  # Empty - projects should define their own
    "ignore_rules": [],
}


def get_documentation_analysis_config():
    """Get documentation analysis configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("documentation_analysis", None)
    if external_config:
        result = DOCUMENTATION_ANALYSIS.copy()
        # Deep merge for nested dicts
        if "topic_keywords" in external_config and "topic_keywords" in result:
            result["topic_keywords"].update(external_config.get("topic_keywords", {}))
        # Update other keys
        for key, value in external_config.items():
            if key != "topic_keywords":
                result[key] = value
        return result
    return DOCUMENTATION_ANALYSIS


# Audit function registry configuration
# NOTE: Defaults are minimal. See development_tools_config.json.example for full examples.
AUDIT_FUNCTION_REGISTRY = {
    "registry_path": "development_docs/FUNCTION_REGISTRY_DETAIL.md",  # Generic default path
    "high_complexity_min": 50,  # Generic threshold
    "top_complexity": 10,
    "top_undocumented": 5,
    "top_duplicates": 5,
    "error_sample_limit": 5,
    "max_complexity_json": 200,
    "max_undocumented_json": 200,
    "max_duplicates_json": 200,
}


def get_analyze_function_registry_config():
    """Get audit function registry configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("analyze_function_registry", None)
    if external_config:
        result = AUDIT_FUNCTION_REGISTRY.copy()
        result.update(external_config)
        return result
    return AUDIT_FUNCTION_REGISTRY


# Function pattern analysis (entry points, data access, communication, decorators)
# Projects can override via analyze_function_patterns in development_tools_config.json
ANALYZE_FUNCTION_PATTERNS = {
    "entry_point_names": ["handle_message", "generate_response", "main", "__init__"],
    "data_access_keywords": ["get_user", "save_user", "load_user", "save_", "load_"],
    "communication_keywords": ["send_", "receive_", "connect_", "disconnect_", "message"],
    "decorator_names": ["handle_errors", "handle_error", "log_execution"],
}


def get_analyze_function_patterns_config():
    """Get function pattern analysis configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("analyze_function_patterns", None)
    if external_config:
        result = ANALYZE_FUNCTION_PATTERNS.copy()
        for key in ("entry_point_names", "data_access_keywords", "communication_keywords", "decorator_names"):
            if key in external_config and isinstance(external_config[key], (list, tuple)):
                result[key] = list(external_config[key])
        return result
    return ANALYZE_FUNCTION_PATTERNS.copy()


# Duplicate function analysis configuration
ANALYZE_DUPLICATE_FUNCTIONS = {
    "use_mtime_cache": True,
    "min_name_similarity": 0.6,
    "min_overall_similarity": 0.7,
    "max_pairs": 50,
    "max_groups": 50,
    "max_candidate_pairs": 20000,
    "max_token_group_size": 200,
    "consider_body_similarity": False,
    "run_body_similarity_on_full_audit": True,
    "body_similarity_min_name_threshold": 0.35,  # lower than min_name_similarity; near-miss pairs get body check
    "max_body_candidate_pairs": 5000,
    "body_similarity_scope": "same_file",  # same_file | same_module | hash_bucket
    "stop_name_tokens": [
        "get",
        "set",
        "update",
        "create",
        "delete",
        "handle",
        "process",
        "load",
        "save",
        "run",
        "init",
        "main",
        "check",
        "build",
        "fetch",
        "sync",
        "prepare",
    ],
    "weights": {
        "name": 0.45,
        "args": 0.2,
        "locals": 0.2,
        "imports": 0.15,
        "body": 0.0,  # used only when consider_body_similarity is True
    },
}


def get_analyze_duplicate_functions_config():
    """Get duplicate function analysis configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("analyze_duplicate_functions", None)
    if external_config:
        result = ANALYZE_DUPLICATE_FUNCTIONS.copy()
        result.update(external_config)
        if "weights" in external_config and isinstance(result.get("weights"), dict):
            result["weights"] = {
                **ANALYZE_DUPLICATE_FUNCTIONS.get("weights", {}),
                **external_config.get("weights", {}),
            }
        return result
    return ANALYZE_DUPLICATE_FUNCTIONS


# Module refactor candidates (large/high-complexity modules)
ANALYZE_MODULE_REFACTOR_CANDIDATES = {
    "max_lines_per_module": 500,
    "max_functions_per_module": 40,
    "max_total_complexity_per_module": 2000,
    "high_plus_critical_threshold": 5,
}


def get_analyze_module_refactor_candidates_config():
    """Get module refactor candidates config (from external config if available, otherwise default)."""
    external_config = _get_external_value("analyze_module_refactor_candidates", None)
    if external_config:
        result = ANALYZE_MODULE_REFACTOR_CANDIDATES.copy()
        result.update(external_config)
        return result
    return ANALYZE_MODULE_REFACTOR_CANDIDATES


# Audit module dependencies configuration
AUDIT_MODULE_DEPENDENCIES = {
    "dependency_doc_path": "development_docs/MODULE_DEPENDENCIES_DETAIL.md",  # Generic default
}


def get_analyze_module_dependencies_config():
    """Get audit module dependencies configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("analyze_module_dependencies", None)
    if external_config:
        result = AUDIT_MODULE_DEPENDENCIES.copy()
        result.update(external_config)
        return result
    return AUDIT_MODULE_DEPENDENCIES


# Audit package exports configuration
AUDIT_PACKAGE_EXPORTS = {
    "export_patterns": [],  # Patterns to identify exports
    "expected_exports": {},  # Expected exports by module
}


def get_analyze_package_exports_config():
    """Get audit package exports configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("analyze_package_exports", None)
    if external_config:
        result = AUDIT_PACKAGE_EXPORTS.copy()
        # Deep merge for nested dicts
        if "expected_exports" in external_config and "expected_exports" in result:
            result["expected_exports"].update(
                external_config.get("expected_exports", {})
            )
        # Update other keys
        for key, value in external_config.items():
            if key != "expected_exports":
                result[key] = value
        return result
    return AUDIT_PACKAGE_EXPORTS


# Config validator configuration (project-specific lists can override via development_tools_config.json)
CONFIG_VALIDATOR = {
    "config_schema": {},  # Expected config schema structure (empty = auto-detect)
    "validation_rules": {},  # Custom validation rules
    "expected_config_functions": [
        "get_available_channels",
        "get_channel_class_mapping",
        "get_user_data_dir",
        "get_backups_dir",
        "get_user_file_path",
        "validate_core_paths",
        "validate_ai_configuration",
        "validate_communication_channels",
        "validate_logging_configuration",
        "validate_scheduler_configuration",
        "validate_file_organization_settings",
        "validate_environment_variables",
        "validate_all_configuration",
        "validate_and_raise_if_invalid",
        "print_configuration_report",
        "ensure_user_directory",
        "validate_email_config",
        "validate_discord_config",
        "validate_minimum_config",
    ],
    "required_sections": [
        "PROJECT_ROOT",
        "SCAN_DIRECTORIES",
        "FUNCTION_DISCOVERY",
        "VALIDATION",
        "AUDIT",
        "OUTPUT",
        "QUICK_AUDIT",
        "VERSION_SYNC",
        "WORKFLOW",
        "DOCUMENTATION",
        "AUTO_DOCUMENT",
        "AI_VALIDATION",
    ],
}


def get_analyze_config_config():
    """Get config validator configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("analyze_config", None)
    if external_config:
        result = CONFIG_VALIDATOR.copy()
        # Deep merge for nested dicts
        if "validation_rules" in external_config and "validation_rules" in result:
            result["validation_rules"].update(
                external_config.get("validation_rules", {})
            )
        # Update other keys (lists from config replace defaults)
        for key, value in external_config.items():
            if key != "validation_rules":
                result[key] = value
        return result
    return CONFIG_VALIDATOR.copy()


# Validate AI work configuration
# NOTE: Defaults are minimal. See development_tools_config.json.example for full examples.
VALIDATE_AI_WORK = {
    "completeness_threshold": 90.0,  # Generic thresholds
    "accuracy_threshold": 85.0,
    "consistency_threshold": 80.0,
    "actionable_threshold": 75.0,
    "rule_sets": {},  # Empty - projects should define their own
    "rule_set_paths": [],
}


def get_analyze_ai_work_config():
    """Get validate AI work configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("analyze_ai_work", None)
    if external_config:
        result = VALIDATE_AI_WORK.copy()
        # Deep merge for nested dicts
        if "rule_sets" in external_config and "rule_sets" in result:
            result["rule_sets"].update(external_config.get("rule_sets", {}))
        # Update other keys
        for key, value in external_config.items():
            if key not in ("rule_sets",):
                result[key] = value
        return result
    return VALIDATE_AI_WORK


# Shared tool commands (canonical for ruff_command; unused_imports and static_analysis derive from here)
# See LIST_OF_LISTS.md §9a.
_DEFAULT_RUFF_COMMAND = ["python", "-m", "ruff"]


def _get_ruff_command() -> list:
    """Get ruff command from tool_commands, or default. Used by unused_imports and static_analysis."""
    tool_cmds = _get_external_value("tool_commands", None)
    if isinstance(tool_cmds, dict) and "ruff_command" in tool_cmds:
        cmd = tool_cmds["ruff_command"]
        if isinstance(cmd, (list, tuple)) and cmd:
            return list(cmd)
    return list(_DEFAULT_RUFF_COMMAND)


# Unused imports checker configuration
UNUSED_IMPORTS = {
    "preferred_backend": "ruff",  # prefer ruff F401, fallback to pylint
    "ruff_command": _DEFAULT_RUFF_COMMAND,  # Overridden by tool_commands.ruff_command or unused_imports.ruff_command
    "pylint_command": ["python", "-m", "pylint"],  # Pylint command as list
    "batch_size": 200,  # Files per backend invocation
    "pylint_batch_size": 25,  # Smaller fallback batches to avoid timeout spikes
    "ignore_patterns": [],  # Patterns to ignore
    "type_stub_locations": [],  # Locations for type stubs (.pyi files)
    "timeout_seconds": 30,  # Timeout per file
}


def get_unused_imports_config():
    """Get unused imports checker configuration (from external config if available, otherwise default).
    ruff_command: uses tool_commands.ruff_command if set, else unused_imports.ruff_command, else default.
    """
    external_config = _get_external_value("unused_imports", None)
    result = UNUSED_IMPORTS.copy()
    result["ruff_command"] = _get_ruff_command()
    if external_config:
        result.update(external_config)
        if "ruff_command" not in external_config:
            result["ruff_command"] = _get_ruff_command()
    return result


# Static analysis configuration (ruff + pyright)
STATIC_ANALYSIS = {
    "pyright_command": ["python", "-m", "pyright"],
    "pyright_args": ["--outputjson"],
    "pyright_project_path": "pyrightconfig.json",
    "ruff_command": _DEFAULT_RUFF_COMMAND,  # Overridden by tool_commands.ruff_command or static_analysis.ruff_command
    "ruff_args": ["check", ".", "--output-format", "json"],
    "ruff_config_path": "development_tools/config/ruff.toml",
    "ruff_sync_root_compat": True,
    "timeout_seconds": 600,
}


def get_static_analysis_config():
    """Get static analysis tool configuration (from external config if available, otherwise default).
    ruff_command: uses tool_commands.ruff_command if set, else static_analysis.ruff_command, else default.
    """
    external_config = _get_external_value("static_analysis", None)
    result = STATIC_ANALYSIS.copy()
    result["ruff_command"] = _get_ruff_command()
    if external_config:
        result.update(external_config)
        if "ruff_command" not in external_config:
            result["ruff_command"] = _get_ruff_command()
    return result


# Static check: channel_loggers (logging style enforcement)
# Directory exclusion uses shared should_exclude_file; excluded_dirs and allowed_logging_import_paths are project-specific.
STATIC_CHECK_CHANNEL_LOGGERS_DEFAULT = {
    "excluded_dirs": ["tests", "scripts", "ai_tools", "development_tools"],
    "allowed_logging_import_paths": [
        "core/logger.py",
        "core/error_handling.py",
        "core/service.py",
        "run_tests.py",
    ],
}


def get_static_check_channel_loggers_config():
    """Get channel_loggers static check config (excluded_dirs, allowed_logging_import_paths).
    Directory exclusion: use should_exclude_file for generic paths; excluded_dirs for project-specific skip.
    """
    external = _get_external_value("static_checks.channel_loggers", None)
    if isinstance(external, dict):
        result = STATIC_CHECK_CHANNEL_LOGGERS_DEFAULT.copy()
        if "excluded_dirs" in external and isinstance(external["excluded_dirs"], (list, tuple)):
            result["excluded_dirs"] = list(external["excluded_dirs"])
        if "allowed_logging_import_paths" in external and isinstance(
            external["allowed_logging_import_paths"], (list, tuple)
        ):
            result["allowed_logging_import_paths"] = [
                str(p) for p in external["allowed_logging_import_paths"]
            ]
        return result
    return STATIC_CHECK_CHANNEL_LOGGERS_DEFAULT.copy()


# Coverage runtime worker defaults for orchestration helpers.
COVERAGE_RUNTIME = {
    "main_workers": None,
    "dev_tools_workers": None,
    "main_workers_when_concurrent": 6,
    "dev_tools_workers_when_concurrent": 6,
}


def get_coverage_runtime_config():
    """Get coverage worker/runtime config (external overrides default values)."""
    external_config = _get_external_value("coverage", None)
    result = COVERAGE_RUNTIME.copy()
    if isinstance(external_config, dict):
        for key in (
            "main_workers",
            "dev_tools_workers",
            "main_workers_when_concurrent",
            "dev_tools_workers_when_concurrent",
        ):
            if key in external_config:
                result[key] = external_config[key]
    return result


# Quick status configuration
QUICK_STATUS = {
    "core_files": [],  # Will use project.key_files if empty
    "key_directories": [],  # Will use paths.scan_directories if empty
    "data_source_plugins": {},  # Plugin hooks for data sources (Discord, schedulers, etc.)
}


def get_quick_status_config():
    """Get quick status configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("quick_status", None)
    if external_config:
        result = QUICK_STATUS.copy()
        # Deep merge for nested dicts
        if "data_source_plugins" in external_config and "data_source_plugins" in result:
            result["data_source_plugins"].update(
                external_config.get("data_source_plugins", {})
            )
        # Update other keys
        for key, value in external_config.items():
            if key != "data_source_plugins":
                result[key] = value
        return result
    return QUICK_STATUS


# Status configuration
# NOTE: Defaults are minimal. See development_tools_config.json.example for full examples.
STATUS = {
    "check_key_files": True,
    "check_audit_results": True,
    "generate_status_files": True,
    "status_files": {
        "ai_status": "development_tools/AI_STATUS.md",
        "ai_priorities": "development_tools/AI_PRIORITIES.md",
        "consolidated_report": "development_tools/consolidated_report.md",
    },
}


def get_status_config():
    """Get status configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("status", None)
    if external_config:
        result = STATUS.copy()
        # Deep merge for nested dicts
        if "status_files" in external_config and "status_files" in result:
            result["status_files"].update(external_config.get("status_files", {}))
        # Update other keys
        for key, value in external_config.items():
            if key != "status_files":
                result[key] = value
        return result
    return STATUS


# System signals configuration
SYSTEM_SIGNALS = {
    "core_files": [],  # Will use project.key_files if empty
    "data_source_plugins": {},  # Plugin hooks for data sources
}


def get_system_signals_config():
    """Get system signals configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("system_signals", None)
    if external_config:
        result = SYSTEM_SIGNALS.copy()
        # Deep merge for nested dicts
        if "data_source_plugins" in external_config and "data_source_plugins" in result:
            result["data_source_plugins"].update(
                external_config.get("data_source_plugins", {})
            )
        # Update other keys
        for key, value in external_config.items():
            if key != "data_source_plugins":
                result[key] = value
        return result
    return SYSTEM_SIGNALS


# Backup policy configuration
BACKUP_POLICY = {
    "categories": {
        "A": {
            "description": "Recovery-critical runtime data",
            "max_age_days": 30,
            "min_keep": 4,
            "max_keep": 10,
            "local_retention_enabled": True,
        },
        "B": {
            "description": "Engineering artifacts",
            "max_age_days": 90,
            "min_keep": 7,
            "max_keep": 30,
            "local_retention_enabled": True,
        },
        "C": {
            "description": "Git-canonical tracked assets",
            "max_age_days": None,
            "min_keep": 0,
            "max_keep": 0,
            "local_retention_enabled": False,
        },
    },
    "artifact_rules": [],
    "restore_drill": {
        "temp_restore_root": "development_tools/reports/backup_drills",
        "report_json_path": "development_tools/reports/backup_restore_drill_report.json",
        "report_markdown_path": "development_tools/reports/backup_restore_drill_report.md",
        "verification_checks": {
            "required_paths": ["users"],
            "min_file_count": 1,
        },
    },
    "ownership_map": {
        "core": "User backup creation/restore + runtime backup scheduling",
        "development_tools": "Engineering artifact retention/inventory/reporting",
        "git": "Canonical source history for tracked code/docs/changelogs",
    },
}


def get_backup_policy_config():
    """Get backup policy configuration (from external config if available, otherwise default)."""
    external_config = _get_external_value("backup_policy", None)
    if external_config:
        result = BACKUP_POLICY.copy()
        # Deep merge for top-level nested sections
        for nested_key in ("categories", "restore_drill", "ownership_map"):
            merged_nested = dict(result.get(nested_key, {}))
            if isinstance(external_config.get(nested_key), dict):
                merged_nested.update(external_config.get(nested_key, {}))
                result[nested_key] = merged_nested
        if isinstance(external_config.get("artifact_rules"), list):
            result["artifact_rules"] = external_config["artifact_rules"]
        return result
    return BACKUP_POLICY


BACKUP_HEALTH_DEFAULTS = {"recent_days": 14}


def get_backup_health_config():
    """Get backup health check configuration (recent_days threshold for 'recent enough' checks)."""
    external_config = _get_external_value("backup_health", None)
    if external_config and isinstance(external_config, dict):
        result = BACKUP_HEALTH_DEFAULTS.copy()
        if "recent_days" in external_config:
            result["recent_days"] = int(external_config["recent_days"])
        return result
    return BACKUP_HEALTH_DEFAULTS.copy()


# Auto document functions configuration
# NOTE: Defaults are minimal. See development_tools_config.json.example for full examples.
AUTO_DOCUMENT_FUNCTIONS = {
    "template_paths": {},  # Empty - projects should define their own
    "doc_targets": {},  # Empty - projects should define their own
    "formatting_rules": {},  # Empty - projects should define their own
    "function_type_detection": {  # Minimal generic patterns
        "test_function": {"name_patterns": ["test_"]},
        "special_method": {"name_pattern": "__.*__"},
        "constructor": {"name": "__init__"},
        "main_function": {"name": "main"},
    },
}


def get_fix_function_docstrings_config():
    """Get fix-function-docstrings configuration (external override or defaults)."""
    external_config = _get_external_value("fix_function_docstrings", None)
    if external_config:
        result = AUTO_DOCUMENT_FUNCTIONS.copy()
        # Deep merge for nested dicts
        for key in [
            "template_paths",
            "doc_targets",
            "formatting_rules",
            "function_type_detection",
        ]:
            if key in external_config and key in result:
                if isinstance(result[key], dict):
                    result[key].update(external_config.get(key, {}))
                else:
                    result[key] = external_config.get(key, result[key])
        # Update other keys
        for key, value in external_config.items():
            if key not in (
                "template_paths",
                "doc_targets",
                "formatting_rules",
                "function_type_detection",
            ):
                result[key] = value
        return result
    return AUTO_DOCUMENT_FUNCTIONS


# Domain mapper configuration (test coverage / selective test execution)
# Maps source domains to test directories and pytest markers.
DOMAIN_MAPPER_DEFAULTS = {
    "source_to_test_mapping": {
        "core": [["tests/core/", "tests/unit/"], ["unit", "critical"]],
        "communication": [["tests/communication/"], ["communication", "integration"]],
        "ui": [["tests/ui/"], ["ui"]],
        "tasks": [[], ["tasks"]],
        "ai": [["tests/ai/"], ["ai"]],
        "user": [[], ["user_management"]],
        "notebook": [[], ["notebook"]],
        "development_tools": [["tests/development_tools/"], []],
    },
    "domain_dependencies": {
        "core": ["communication", "ui", "tasks", "ai", "user", "notebook"],
        "communication": ["ui", "tasks", "ai", "user"],
        "tasks": ["communication", "ui"],
        "user": ["communication", "ui", "ai"],
        "ai": ["communication", "ui"],
        "ui": [],
        "notebook": ["communication", "ui"],
        "development_tools": [],
    },
    "keyword_map": {
        "development_tools": [
            "development_tools",
            "dev_tools",
            "audit",
            "coverage",
            "verification",
            "status",
        ],
        "communication": [
            "communication",
            "discord",
            "email",
            "webhook",
            "channel",
            "command",
            "interaction",
            "router",
        ],
        "ai": ["ai", "chatbot", "prompt", "context", "llm"],
        "tasks": ["task"],
        "ui": ["ui", "dialog", "widget", "qt", "pyside"],
        "user": ["user", "profile", "account", "preferences"],
        "notebook": ["notebook", "note", "journal", "list"],
        "core": [
            "core",
            "service",
            "scheduler",
            "config",
            "logger",
            "logging",
            "observability",
            "error",
            "backup",
            "file",
            "cleanup",
            "checkin",
            "analytics",
            "response",
        ],
    },
}


def get_domain_mapper_config():
    """Get domain mapper configuration (external override or defaults)."""
    external_config = _get_external_value("domain_mapper", None)
    if external_config and isinstance(external_config, dict):
        result = {
            "source_to_test_mapping": DOMAIN_MAPPER_DEFAULTS["source_to_test_mapping"].copy(),
            "domain_dependencies": DOMAIN_MAPPER_DEFAULTS["domain_dependencies"].copy(),
            "keyword_map": DOMAIN_MAPPER_DEFAULTS["keyword_map"].copy(),
        }
        for key in ("source_to_test_mapping", "domain_dependencies", "keyword_map"):
            if key in external_config and isinstance(external_config[key], dict):
                result[key].update(external_config[key])
        return result
    return DOMAIN_MAPPER_DEFAULTS.copy()
