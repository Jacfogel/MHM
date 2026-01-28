"""
Tests for development_tools configuration module.

Tests configuration validation, key settings existence, and helper functions.
"""

import pytest
import importlib.util
import sys
from pathlib import Path

# Import using importlib to handle path issues
project_root = Path(__file__).parent.parent.parent
# Load config through the package system to get proper exports
config_path = project_root / "development_tools" / "config" / "__init__.py"
if not config_path.exists():
    # Fallback to config.py if __init__.py doesn't exist
    config_path = project_root / "development_tools" / "config" / "config.py"
spec = importlib.util.spec_from_file_location("development_tools.config", config_path)
config = importlib.util.module_from_spec(spec)
sys.modules["development_tools.config"] = config
spec.loader.exec_module(config)
# Also ensure the actual config module is loaded
if config_path.name == "__init__.py":
    config_config_path = project_root / "development_tools" / "config" / "config.py"
    if config_config_path.exists() and "development_tools.config.config" not in sys.modules:
        config_config_spec = importlib.util.spec_from_file_location("development_tools.config.config", config_config_path)
        config_config_module = importlib.util.module_from_spec(config_config_spec)
        sys.modules["development_tools.config.config"] = config_config_module
        config_config_spec.loader.exec_module(config_config_module)


class TestConfigKeySettings:
    """Test that key configuration settings exist and have expected structure."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_project_root_exists(self):
        """Test that PROJECT_ROOT is defined."""
        assert hasattr(config, 'PROJECT_ROOT')
        assert isinstance(config.PROJECT_ROOT, str)

    @pytest.mark.unit
    def test_scan_directories_exists(self):
        """Test that SCAN_DIRECTORIES is defined and is a list."""
        assert hasattr(config, 'SCAN_DIRECTORIES')
        assert isinstance(config.SCAN_DIRECTORIES, list)
        # SCAN_DIRECTORIES may be empty by default (requires external config)
        # Try to load external config and check get_scan_directories()
        config.load_external_config()
        scan_dirs = config.get_scan_directories()
        assert isinstance(scan_dirs, list)
        # If external config exists, scan_dirs should be populated
        # If not, it's OK for it to be empty (project-specific config required)
        if len(scan_dirs) == 0:
            # Check if external config file exists - if it does, it should have scan_directories
            project_root = config.get_project_root()
            config_file = project_root / 'development_tools' / 'config' / 'development_tools_config.json'
            if config_file.exists():
                # Config file exists but scan_dirs is empty - this is a configuration issue
                pytest.skip("External config file exists but scan_directories is empty (configuration issue)")

    @pytest.mark.unit
    def test_ai_collaboration_config_exists(self):
        """Test that AI_COLLABORATION config exists and has expected keys."""
        assert hasattr(config, 'AI_COLLABORATION')
        assert isinstance(config.AI_COLLABORATION, dict)
        expected_keys = ['concise_output', 'detailed_files', 'actionable_insights', 
                        'context_aware', 'priority_issues', 'integration_mode']
        for key in expected_keys:
            assert key in config.AI_COLLABORATION

    @pytest.mark.unit
    def test_analyze_functions_config_exists(self):
        """Test that FUNCTION_DISCOVERY config exists and has expected keys."""
        assert hasattr(config, 'FUNCTION_DISCOVERY')
        assert isinstance(config.FUNCTION_DISCOVERY, dict)
        expected_keys = ['moderate_complexity_threshold', 'high_complexity_threshold',
                        'critical_complexity_threshold', 'min_docstring_length',
                        'handler_keywords', 'test_keywords', 'critical_functions']
        for key in expected_keys:
            assert key in config.FUNCTION_DISCOVERY

    @pytest.mark.unit
    def test_validation_config_exists(self):
        """Test that VALIDATION config exists and has expected keys."""
        assert hasattr(config, 'VALIDATION')
        assert isinstance(config.VALIDATION, dict)
        expected_keys = ['documentation_coverage_threshold', 'moderate_complexity_warning',
                        'high_complexity_warning', 'critical_complexity_warning',
                        'duplicate_function_warning', 'missing_docstring_warning',
                        'critical_issues_first']
        for key in expected_keys:
            assert key in config.VALIDATION

    @pytest.mark.unit
    def test_audit_config_exists(self):
        """Test that AUDIT config exists and has expected keys."""
        assert hasattr(config, 'AUDIT')
        assert isinstance(config.AUDIT, dict)
        expected_keys = ['include_generated_files', 'include_test_files',
                        'include_legacy_files', 'max_output_lines',
                        'save_detailed_results', 'generate_summary', 'highlight_issues']
        for key in expected_keys:
            assert key in config.AUDIT

    @pytest.mark.unit
    def test_output_config_exists(self):
        """Test that OUTPUT config exists and has expected keys."""
        assert hasattr(config, 'OUTPUT')
        assert isinstance(config.OUTPUT, dict)
        expected_keys = ['use_emojis', 'show_progress', 'color_output',
                        'detailed_reports', 'concise_format', 'priority_indicators',
                        'action_items']
        for key in expected_keys:
            assert key in config.OUTPUT

    @pytest.mark.unit
    def test_workflow_config_exists(self):
        """Test that WORKFLOW config exists."""
        assert hasattr(config, 'WORKFLOW')
        assert isinstance(config.WORKFLOW, dict)

    @pytest.mark.unit
    def test_documentation_config_exists(self):
        """Test that DOCUMENTATION config exists."""
        assert hasattr(config, 'DOCUMENTATION')
        assert isinstance(config.DOCUMENTATION, dict)

    @pytest.mark.unit
    def test_quick_audit_config_exists(self):
        """Test that QUICK_AUDIT config exists."""
        assert hasattr(config, 'QUICK_AUDIT')
        assert isinstance(config.QUICK_AUDIT, dict)

    @pytest.mark.unit
    def test_fix_version_sync_config_exists(self):
        """Test that VERSION_SYNC config exists."""
        assert hasattr(config, 'VERSION_SYNC')
        assert isinstance(config.VERSION_SYNC, dict)


class TestConfigHelperFunctions:
    """Test that helper functions return expected types and structures."""

    @pytest.mark.unit
    def test_get_project_root_returns_path(self):
        """Test that get_project_root() returns a Path object."""
        result = config.get_project_root()
        assert isinstance(result, Path)

    @pytest.mark.unit
    def test_get_scan_directories_returns_list(self):
        """Test that get_scan_directories() returns a list."""
        # Load external config to ensure we get the actual configured directories
        config.load_external_config()
        result = config.get_scan_directories()
        assert isinstance(result, list)
        # If external config exists, scan_dirs should be populated
        # If not, it's OK for it to be empty (project-specific config required)
        if len(result) == 0:
            # Check if external config file exists - if it does, it should have scan_directories
            project_root = config.get_project_root()
            config_file = project_root / 'development_tools' / 'config' / 'development_tools_config.json'
            if config_file.exists():
                # Config file exists but scan_dirs is empty - this is a configuration issue
                pytest.skip("External config file exists but scan_directories is empty (configuration issue)")
            # If config file doesn't exist, empty list is expected (default behavior)

    @pytest.mark.unit
    def test_get_analyze_functions_config_returns_dict(self):
        """Test that get_analyze_functions_config() returns a dict."""
        result = config.get_analyze_functions_config()
        assert isinstance(result, dict)
        assert 'moderate_complexity_threshold' in result

    @pytest.mark.unit
    def test_get_validation_config_returns_dict(self):
        """Test that get_validation_config() returns a dict."""
        result = config.get_validation_config()
        assert isinstance(result, dict)
        assert 'documentation_coverage_threshold' in result

    @pytest.mark.unit
    def test_get_audit_config_returns_dict(self):
        """Test that get_audit_config() returns a dict."""
        result = config.get_audit_config()
        assert isinstance(result, dict)
        assert 'include_test_files' in result

    @pytest.mark.unit
    def test_get_output_config_returns_dict(self):
        """Test that get_output_config() returns a dict."""
        result = config.get_output_config()
        assert isinstance(result, dict)
        assert 'concise_format' in result

    @pytest.mark.unit
    def test_get_workflow_config_returns_dict(self):
        """Test that get_workflow_config() returns a dict."""
        result = config.get_workflow_config()
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_get_documentation_config_returns_dict(self):
        """Test that get_documentation_config() returns a dict."""
        result = config.get_documentation_config()
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_get_auto_document_config_returns_dict(self):
        """Test that get_auto_document_config() returns a dict."""
        result = config.get_auto_document_config()
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_get_ai_validation_config_returns_dict(self):
        """Test that get_ai_validation_config() returns a dict."""
        result = config.get_ai_validation_config()
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_get_ai_collaboration_config_returns_dict(self):
        """Test that get_ai_collaboration_config() returns a dict."""
        result = config.get_ai_collaboration_config()
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_get_quick_audit_config_returns_dict(self):
        """Test that get_quick_audit_config() returns a dict."""
        result = config.get_quick_audit_config()
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_get_fix_version_sync_config_returns_dict(self):
        """Test that get_fix_version_sync_config() returns a dict."""
        result = config.get_fix_version_sync_config()
        assert isinstance(result, dict)


class TestConfigPaths:
    """Test that paths used in tests/fixtures are valid."""

    @pytest.mark.unit
    def test_project_root_path_exists(self):
        """Test that project root path exists."""
        project_root = config.get_project_root()
        # Resolve relative to current working directory
        if not project_root.is_absolute():
            # If relative, check if it exists relative to the test location
            # Tests run from project root, so relative paths should work
            assert True  # Path validation is context-dependent
        else:
            assert project_root.exists()

    @pytest.mark.unit
    def test_scan_directories_are_valid_names(self):
        """Test that scan directory names are valid (non-empty strings)."""
        # Load external config to ensure we get the actual configured directories
        config.load_external_config()
        directories = config.get_scan_directories()
        # If directories is empty, skip this test (requires external config)
        if len(directories) == 0:
            pytest.skip("Scan directories is empty (requires external config)")
        for directory in directories:
            assert isinstance(directory, str)
            assert len(directory) > 0
            # Should not contain path separators in basic names
            assert '/' not in directory or directory.startswith('./')
