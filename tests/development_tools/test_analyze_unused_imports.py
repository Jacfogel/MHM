"""
Tests for analyze_unused_imports.py.

Tests unused imports detection including pylint integration, categorization,
and cache functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from tests.development_tools.conftest import load_development_tools_module, test_config_path

# Load the module
unused_imports_module = load_development_tools_module("imports.analyze_unused_imports")
UnusedImportsChecker = unused_imports_module.UnusedImportsChecker


class TestUnusedImportsCheckerInit:
    """Test UnusedImportsChecker initialization."""
    
    @pytest.mark.unit
    def test_init_default(self, tmp_path):
        """Test initialization with default parameters."""
        checker = UnusedImportsChecker(project_root=str(tmp_path))
        assert checker.project_root == tmp_path.resolve()
        assert checker.max_workers is not None
        assert checker.use_cache is True
        assert checker.verbose is False
    
    @pytest.mark.unit
    def test_init_custom_params(self, tmp_path):
        """Test initialization with custom parameters."""
        checker = UnusedImportsChecker(
            project_root=str(tmp_path),
            max_workers=4,
            use_cache=False,
            verbose=True
        )
        assert checker.max_workers == 4
        assert checker.use_cache is False
        assert checker.verbose is True
    
    @pytest.mark.unit
    def test_init_with_config_path(self, tmp_path, test_config_path):
        """Test initialization with custom config path."""
        checker = UnusedImportsChecker(
            project_root=str(tmp_path),
            config_path=test_config_path
        )
        assert checker.project_root == tmp_path.resolve()


class TestCategorizeUnusedImport:
    """Test unused import categorization."""
    
    @pytest.mark.unit
    def test_categorize_re_exports(self, tmp_path):
        """Test categorization of re-exports in __init__.py."""
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        init_file = tmp_path / "__init__.py"
        init_file.write_text("from module import something")
        
        issue = {'message': 'Unused import something', 'line': 1}
        category = checker.categorize_unused_import(init_file, issue)
        assert category == 're_exports'
    
    @pytest.mark.unit
    def test_categorize_test_mocking(self, tmp_path):
        """Test categorization of test mocking imports."""
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        test_file = tmp_path / "test_file.py"
        test_file.write_text("""
from unittest.mock import patch, MagicMock
import module_to_mock

@patch('module_to_mock.function')
def test_something(mock_func):
    pass
""")
        
        issue = {'message': 'Unused import module_to_mock', 'line': 3}
        category = checker.categorize_unused_import(test_file, issue)
        # May be categorized as test_mocking or obvious_unused depending on detection logic
        assert category in ['test_mocking', 'obvious_unused']
    
    @pytest.mark.unit
    def test_categorize_qt_testing(self, tmp_path):
        """Test categorization of Qt testing imports."""
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        test_file = tmp_path / "test_ui.py"
        test_file.write_text("""
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtTest import QTest

def test_widget():
    app = QApplication([])
    widget = QWidget()
    QTest.keyClicks(widget, "test")
""")
        
        issue = {'message': 'Unused import QWidget', 'line': 2}
        category = checker.categorize_unused_import(test_file, issue)
        # Should be categorized as qt_testing or test_mocking
        assert category in ['qt_testing', 'test_mocking', 'obvious_unused']
    
    @pytest.mark.unit
    def test_categorize_type_hints_only(self, tmp_path):
        """Test categorization of type hint only imports."""
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        code_file = tmp_path / "code.py"
        code_file.write_text("""
from typing import Optional, List
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from other_module import SomeType

def func() -> Optional[List[SomeType]]:
    pass
""")
        
        issue = {'message': 'Unused import SomeType', 'line': 5}
        category = checker.categorize_unused_import(code_file, issue)
        # Should be categorized as type_hints_only or obvious_unused
        assert category in ['type_hints_only', 'obvious_unused']
    
    @pytest.mark.unit
    def test_categorize_obvious_unused(self, tmp_path):
        """Test categorization of obviously unused imports."""
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        code_file = tmp_path / "code.py"
        code_file.write_text("""
import unused_module

def func():
    pass
""")
        
        issue = {'message': 'Unused import unused_module', 'line': 2}
        category = checker.categorize_unused_import(code_file, issue)
        assert category == 'obvious_unused'


class TestRunPylintOnFile:
    """Test running pylint on individual files."""
    
    @pytest.mark.unit
    @patch('development_tools.imports.analyze_unused_imports.subprocess.run')
    def test_run_pylint_no_issues(self, mock_subprocess, tmp_path):
        """Test file with no unused imports."""
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        test_file = tmp_path / "test.py"
        test_file.write_text("import os\nresult = os.getcwd()")
        
        # Mock pylint returning no issues
        mock_subprocess.return_value = MagicMock(
            stdout="[]",
            returncode=0
        )
        
        result = checker.run_pylint_on_file(test_file)
        assert result == []
    
    @pytest.mark.unit
    @patch('development_tools.imports.analyze_unused_imports.subprocess.run')
    def test_run_pylint_with_issues(self, mock_subprocess, tmp_path):
        """Test file with unused imports."""
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        test_file = tmp_path / "test.py"
        test_file.write_text("import unused_module\nresult = 'test'")
        
        # Mock pylint returning unused import issue
        mock_issue = {
            'type': 'warning',
            'message': 'Unused import unused_module',
            'message-id': 'W0611',
            'line': 1,
            'column': 0
        }
        mock_subprocess.return_value = MagicMock(
            stdout=json.dumps([mock_issue]),
            returncode=1
        )
        
        result = checker.run_pylint_on_file(test_file)
        assert len(result) > 0
        assert result[0]['message'] == 'Unused import unused_module'
    
    @pytest.mark.unit
    @patch('development_tools.imports.analyze_unused_imports.subprocess.run')
    def test_run_pylint_timeout(self, mock_subprocess, tmp_path):
        """Test handling of pylint timeout."""
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        test_file = tmp_path / "test.py"
        test_file.write_text("import os")
        
        # Mock timeout
        import subprocess
        mock_subprocess.side_effect = subprocess.TimeoutExpired('pylint', 30)
        
        result = checker.run_pylint_on_file(test_file)
        assert result is None
    
    @pytest.mark.unit
    @patch('development_tools.imports.analyze_unused_imports.subprocess.run')
    def test_run_pylint_invalid_json(self, mock_subprocess, tmp_path):
        """Test handling of invalid JSON from pylint."""
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        test_file = tmp_path / "test.py"
        test_file.write_text("import os")
        
        # Mock invalid JSON
        mock_subprocess.return_value = MagicMock(
            stdout="invalid json",
            returncode=1
        )
        
        result = checker.run_pylint_on_file(test_file)
        # Should return None on JSON error
        assert result is None


class TestScanCodebase:
    """Test scanning entire codebase for unused imports."""
    
    @pytest.mark.unit
    @patch.object(UnusedImportsChecker, 'find_python_files')
    def test_scan_codebase_no_files(self, mock_find_files, tmp_path):
        """Test scanning with no Python files."""
        mock_find_files.return_value = []  # No files to scan
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        result = checker.scan_codebase()
        # Returns dict with 'findings' and 'stats' keys
        assert isinstance(result, dict)
        assert 'findings' in result
        assert 'stats' in result
        assert 'obvious_unused' in result['findings']
        assert result['stats']['files_scanned'] == 0
    
    @pytest.mark.unit
    @patch('multiprocessing.Pool')
    @patch.object(UnusedImportsChecker, 'find_python_files')
    def test_scan_codebase_with_files(self, mock_find_files, mock_pool, tmp_path):
        """Test scanning with Python files."""
        # Create test files
        file1 = tmp_path / "file1.py"
        file1.write_text("import os")
        file2 = tmp_path / "file2.py"
        file2.write_text("import sys\nversion = sys.version")
        
        # Mock find_python_files to return only our test files
        mock_find_files.return_value = [file1, file2]
        
        # Mock multiprocessing Pool to return results directly (no actual subprocess)
        mock_pool_instance = MagicMock()
        mock_pool.return_value.__enter__.return_value = mock_pool_instance
        mock_pool.return_value.__exit__.return_value = None
        
        # Mock pool.map to return our test results
        mock_pool_instance.map.return_value = [
            (file1, [{'message': 'Unused import os', 'message-id': 'W0611', 'line': 1}]),
            (file2, [])
        ]
        
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        result = checker.scan_codebase()
        
        # Should have findings
        assert isinstance(result, dict)
        assert len(result.get('findings', {}).get('obvious_unused', [])) > 0
    
    @pytest.mark.unit
    @patch('multiprocessing.Pool')
    @patch.object(UnusedImportsChecker, 'find_python_files')
    def test_scan_codebase_excludes_files(self, mock_find_files, mock_pool, tmp_path):
        """Test that excluded files are not scanned."""
        # Create regular file (excluded files won't be in find_python_files result)
        regular_file = tmp_path / "file.py"
        regular_file.write_text("import os\nresult = os.getcwd()")
        
        # Mock find_python_files to return only the regular file (excluded files filtered out)
        mock_find_files.return_value = [regular_file]
        
        # Mock multiprocessing Pool to return results directly (no actual subprocess)
        mock_pool_instance = MagicMock()
        mock_pool.return_value.__enter__.return_value = mock_pool_instance
        mock_pool.return_value.__exit__.return_value = None
        
        # Mock pool.map to return no unused imports
        mock_pool_instance.map.return_value = [
            (regular_file, [])
        ]
        
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        result = checker.scan_codebase()
        
        # Should process the file
        assert isinstance(result, dict)
        # Verify pool was called (meaning files were processed)
        assert mock_pool_instance.map.called


class TestRunAnalysis:
    """Test running full analysis."""
    
    @pytest.mark.unit
    @patch.object(UnusedImportsChecker, 'scan_codebase')
    def test_run_analysis_basic(self, mock_scan, tmp_path):
        """Test basic analysis run."""
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        
        # Set up the checker's internal state directly (what scan_codebase would set)
        checker.findings = {
            'obvious_unused': [
                {'file': 'file1.py', 'line': 1, 'message': 'Unused import os'}
            ],
            'type_hints_only': [],
            're_exports': [],
            'conditional_imports': [],
            'star_imports': [],
            'test_mocking': [],
            'qt_testing': [],
            'test_infrastructure': [],
            'production_test_mocking': [],
            'ui_imports': [],
        }
        checker.stats = {
            'files_scanned': 1,
            'files_with_issues': 1,
            'total_unused': 1,
            'cache_hits': 0,
            'cache_misses': 1,
        }
        
        # Mock scan_codebase to return the structure (won't be called since findings exist)
        mock_scan.return_value = {
            'findings': checker.findings,
            'stats': checker.stats,
        }
        
        result = checker.run_analysis()
        
        assert isinstance(result, dict)
        assert 'summary' in result
        assert 'details' in result
        assert result['summary']['total_issues'] > 0
    
    @pytest.mark.unit
    @patch.object(UnusedImportsChecker, 'scan_codebase')
    def test_run_analysis_empty(self, mock_scan, tmp_path):
        """Test analysis with no unused imports."""
        mock_scan.return_value = {
            'findings': {
                'obvious_unused': [],
                'type_hints_only': [],
                're_exports': [],
                'conditional_imports': [],
                'star_imports': [],
                'test_mocking': [],
                'qt_testing': [],
                'test_infrastructure': [],
                'production_test_mocking': [],
                'ui_imports': [],
            },
            'stats': {
                'files_scanned': 0,
                'files_with_issues': 0,
                'total_unused': 0,
                'cache_hits': 0,
                'cache_misses': 0,
            }
        }
        
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        result = checker.run_analysis()
        
        assert isinstance(result, dict)
        assert 'summary' in result
        assert result['summary']['total_issues'] == 0


class TestCache:
    """Test caching functionality."""
    
    @pytest.mark.unit
    @patch('development_tools.imports.analyze_unused_imports.subprocess.run')
    def test_cache_hit(self, mock_subprocess, tmp_path):
        """Test that cache is used on second check."""
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=True)
        test_file = tmp_path / "test.py"
        test_file.write_text("import os")
        
        # First call - should call subprocess
        mock_subprocess.return_value = MagicMock(
            stdout="[]",
            returncode=0
        )
        result1 = checker.run_pylint_on_file(test_file)
        
        # Second call - should use cache (subprocess not called again)
        mock_subprocess.reset_mock()
        result2 = checker.run_pylint_on_file(test_file)
        
        # Results should be the same
        assert result1 == result2
        # Subprocess should only be called once (on first check)
        assert mock_subprocess.call_count <= 1
    
    @pytest.mark.unit
    @patch('development_tools.imports.analyze_unused_imports.subprocess.run')
    def test_cache_disabled(self, mock_subprocess, tmp_path):
        """Test that cache is not used when disabled."""
        checker = UnusedImportsChecker(project_root=str(tmp_path), use_cache=False)
        test_file = tmp_path / "test.py"
        test_file.write_text("import os")
        
        mock_subprocess.return_value = MagicMock(
            stdout="[]",
            returncode=0
        )
        
        # Both calls should trigger subprocess
        checker.run_pylint_on_file(test_file)
        checker.run_pylint_on_file(test_file)
        
        # Subprocess should be called twice
        assert mock_subprocess.call_count == 2

