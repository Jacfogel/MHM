"""
Tests for development_tools standard_exclusions module.

Tests file exclusion patterns, tool-specific exclusions, and context-specific exclusions.
"""

import pytest
import importlib.util
import sys
from pathlib import Path

# Import using importlib to handle path issues
project_root = Path(__file__).parent.parent.parent
exclusions_path = project_root / "development_tools" / "shared" / "standard_exclusions.py"
spec = importlib.util.spec_from_file_location("development_tools.shared.standard_exclusions", exclusions_path)
exclusions_module = importlib.util.module_from_spec(spec)
sys.modules["development_tools.shared.standard_exclusions"] = exclusions_module
spec.loader.exec_module(exclusions_module)

should_exclude_file = exclusions_module.should_exclude_file
get_exclusions = exclusions_module.get_exclusions
get_coverage_exclusions = exclusions_module.get_coverage_exclusions
get_analysis_exclusions = exclusions_module.get_analysis_exclusions
get_documentation_exclusions = exclusions_module.get_documentation_exclusions


class TestUniversalExclusions:
    """Test that universal exclusion patterns work correctly."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_pycache_excluded(self):
        """Test that __pycache__ directories are excluded."""
        assert should_exclude_file('__pycache__/file.py') is True
        assert should_exclude_file('some/path/__pycache__/module.pyc') is True

    @pytest.mark.unit
    def test_venv_excluded(self):
        """Test that virtual environment directories are excluded."""
        assert should_exclude_file('venv/lib/file.py') is True
        assert should_exclude_file('.venv/lib/file.py') is True
        assert should_exclude_file('env/lib/file.py') is True

    @pytest.mark.unit
    def test_git_excluded(self):
        """Test that .git directories are excluded."""
        assert should_exclude_file('.git/config') is True
        assert should_exclude_file('.git/HEAD') is True

    @pytest.mark.unit
    def test_pyc_files_excluded(self):
        """Test that .pyc files are excluded."""
        assert should_exclude_file('module.pyc') is True
        assert should_exclude_file('path/to/module.pyo') is True

    @pytest.mark.unit
    def test_tests_data_excluded(self):
        """Test that tests/data directories are excluded."""
        assert should_exclude_file('tests/data/file.json') is True
        assert should_exclude_file('tests/data/tmp/file.txt') is True

    @pytest.mark.unit
    def test_scripts_excluded(self):
        """Test that scripts directory is excluded."""
        assert should_exclude_file('scripts/file.py') is True
        assert should_exclude_file('scripts/subdir/file.py') is True


class TestIncludedPaths:
    """Test that representative paths that should be included are not excluded."""

    @pytest.mark.unit
    def test_core_files_included(self):
        """Test that core module files are included."""
        assert should_exclude_file('core/service.py') is False
        assert should_exclude_file('core/config.py') is False

    @pytest.mark.unit
    def test_communication_files_included(self):
        """Test that communication module files are included."""
        assert should_exclude_file('communication/channel.py') is False
        assert should_exclude_file('communication/manager.py') is False

    @pytest.mark.unit
    def test_ui_files_included(self):
        """Test that UI module files are included."""
        assert should_exclude_file('ui/main_window.py') is False
        assert should_exclude_file('ui/dialogs.py') is False

    @pytest.mark.unit
    def test_regular_python_files_included(self):
        """Test that regular Python files are included."""
        assert should_exclude_file('tasks/task_manager.py') is False
        assert should_exclude_file('user/profile.py') is False


class TestToolSpecificExclusions:
    """Test that tool-specific exclusions work correctly."""

    @pytest.mark.unit
    def test_coverage_exclusions(self):
        """Test that coverage-specific exclusions are applied."""
        exclusions = get_coverage_exclusions()
        assert isinstance(exclusions, list)
        assert len(exclusions) > 0

    @pytest.mark.unit
    def test_analysis_exclusions(self):
        """Test that analysis-specific exclusions are applied."""
        exclusions = get_analysis_exclusions()
        assert isinstance(exclusions, list)
        assert len(exclusions) > 0

    @pytest.mark.unit
    def test_documentation_exclusions(self):
        """Test that documentation-specific exclusions are applied."""
        exclusions = get_documentation_exclusions()
        assert isinstance(exclusions, list)
        assert len(exclusions) > 0

    @pytest.mark.unit
    def test_get_exclusions_with_tool_type(self):
        """Test that get_exclusions() works with tool_type parameter."""
        coverage_exclusions = get_exclusions('coverage', 'development')
        analysis_exclusions = get_exclusions('analysis', 'development')
        assert isinstance(coverage_exclusions, list)
        assert isinstance(analysis_exclusions, list)


class TestContextSpecificExclusions:
    """Test that context-specific exclusions work correctly."""

    @pytest.mark.unit
    def test_production_context_exclusions(self):
        """Test that production context exclusions are applied."""
        exclusions = get_exclusions(None, 'production')
        assert isinstance(exclusions, list)
        # Production should exclude development files
        assert should_exclude_file('development_tools/file.py', context='production') is True
        assert should_exclude_file('tests/file.py', context='production') is True

    @pytest.mark.unit
    def test_development_context_exclusions(self):
        """Test that development context exclusions are applied."""
        exclusions = get_exclusions(None, 'development')
        assert isinstance(exclusions, list)
        # Development should include most files
        assert should_exclude_file('core/service.py', context='development') is False

    @pytest.mark.unit
    def test_testing_context_exclusions(self):
        """Test that testing context exclusions are applied."""
        exclusions = get_exclusions(None, 'testing')
        assert isinstance(exclusions, list)
        assert isinstance(exclusions, list)


class TestPathObjectHandling:
    """Test that should_exclude_file() handles both string and Path objects correctly."""

    @pytest.mark.unit
    def test_string_path_excluded(self):
        """Test that string paths are handled correctly."""
        assert should_exclude_file('__pycache__/file.py') is True
        assert should_exclude_file('core/service.py') is False

    @pytest.mark.unit
    def test_path_object_excluded(self):
        """Test that Path objects are handled correctly."""
        path_obj = Path('__pycache__/file.py')
        assert should_exclude_file(path_obj) is True
        
        path_obj = Path('core/service.py')
        assert should_exclude_file(path_obj) is False

    @pytest.mark.unit
    def test_path_object_with_absolute_path(self):
        """Test that absolute Path objects are handled correctly."""
        # Create a Path object (may be absolute or relative depending on context)
        path_obj = Path('venv/lib/file.py')
        assert should_exclude_file(path_obj) is True

    @pytest.mark.unit
    def test_mixed_path_formats(self):
        """Test that various path formats are handled correctly."""
        # Windows-style path
        win_path = 'tests\\data\\file.json'
        assert should_exclude_file(win_path) is True
        
        # Unix-style path
        unix_path = 'tests/data/file.json'
        assert should_exclude_file(unix_path) is True
        
        # Path object
        path_obj = Path('tests/data/file.json')
        assert should_exclude_file(path_obj) is True

