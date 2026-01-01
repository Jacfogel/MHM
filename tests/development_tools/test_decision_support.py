"""
Tests for decision_support.py.

Tests decision support dashboard functionality including complexity analysis,
undocumented handlers detection, and duplicate name detection.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from tests.development_tools.conftest import load_development_tools_module

# Load the module
decision_support_module = load_development_tools_module("reports.decision_support")
find_complexity_functions = decision_support_module.find_complexity_functions
find_undocumented_handlers = decision_support_module.find_undocumented_handlers
find_duplicate_names = decision_support_module.find_duplicate_names
print_dashboard = decision_support_module.print_dashboard
main = decision_support_module.main


class TestFindComplexityFunctions:
    """Test complexity function detection."""
    
    @pytest.mark.unit
    def test_find_complexity_functions_empty(self):
        """Test with empty function list."""
        moderate, high, critical = find_complexity_functions([])
        assert moderate == []
        assert high == []
        assert critical == []
    
    @pytest.mark.unit
    def test_find_complexity_functions_moderate(self):
        """Test detection of moderate complexity functions."""
        functions = [
            {'name': 'func1', 'complexity': 50, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
            {'name': 'func2', 'complexity': 75, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
            {'name': 'func3', 'complexity': 99, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
        ]
        moderate, high, critical = find_complexity_functions(functions)
        assert len(moderate) == 3
        assert len(high) == 0
        assert len(critical) == 0
        assert all(f['name'] in ['func1', 'func2', 'func3'] for f in moderate)
    
    @pytest.mark.unit
    def test_find_complexity_functions_high(self):
        """Test detection of high complexity functions."""
        functions = [
            {'name': 'func1', 'complexity': 100, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
            {'name': 'func2', 'complexity': 150, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
            {'name': 'func3', 'complexity': 199, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
        ]
        moderate, high, critical = find_complexity_functions(functions)
        assert len(moderate) == 0
        assert len(high) == 3
        assert len(critical) == 0
        assert all(f['name'] in ['func1', 'func2', 'func3'] for f in high)
    
    @pytest.mark.unit
    def test_find_complexity_functions_critical(self):
        """Test detection of critical complexity functions."""
        functions = [
            {'name': 'func1', 'complexity': 200, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
            {'name': 'func2', 'complexity': 300, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
        ]
        moderate, high, critical = find_complexity_functions(functions)
        assert len(moderate) == 0
        assert len(high) == 0
        assert len(critical) == 2
        assert all(f['name'] in ['func1', 'func2'] for f in critical)
    
    @pytest.mark.unit
    def test_find_complexity_functions_excludes_tests(self):
        """Test that test functions are excluded from complexity counts."""
        functions = [
            {'name': 'test_func', 'complexity': 200, 'is_test': True, 'is_handler': False, 'is_special': False, 'docstring': ''},
            {'name': 'normal_func', 'complexity': 200, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
        ]
        moderate, high, critical = find_complexity_functions(functions)
        assert len(critical) == 1
        assert critical[0]['name'] == 'normal_func'
    
    @pytest.mark.unit
    def test_find_complexity_functions_mixed_levels(self):
        """Test detection with mixed complexity levels."""
        functions = [
            {'name': 'moderate1', 'complexity': 50, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
            {'name': 'moderate2', 'complexity': 75, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
            {'name': 'high1', 'complexity': 100, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
            {'name': 'high2', 'complexity': 150, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
            {'name': 'critical1', 'complexity': 200, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
            {'name': 'critical2', 'complexity': 300, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': 'Doc'},
        ]
        moderate, high, critical = find_complexity_functions(functions)
        assert len(moderate) == 2
        assert len(high) == 2
        assert len(critical) == 2


class TestFindUndocumentedHandlers:
    """Test undocumented handler detection."""
    
    @pytest.mark.unit
    def test_find_undocumented_handlers_empty(self):
        """Test with empty function list."""
        result = find_undocumented_handlers([])
        assert result == []
    
    @pytest.mark.unit
    def test_find_undocumented_handlers_documented(self):
        """Test that documented handlers are not included."""
        functions = [
            {'name': 'handle_request', 'is_handler': True, 'docstring': 'Handles requests.'},
            {'name': 'process_data', 'is_handler': True, 'docstring': 'Processes data.'},
        ]
        result = find_undocumented_handlers(functions)
        assert result == []
    
    @pytest.mark.unit
    def test_find_undocumented_handlers_undocumented(self):
        """Test detection of undocumented handlers."""
        functions = [
            {'name': 'handle_request', 'is_handler': True, 'docstring': ''},
            {'name': 'process_data', 'is_handler': True, 'docstring': '   '},
            {'name': 'normal_func', 'is_handler': False, 'docstring': ''},
        ]
        result = find_undocumented_handlers(functions)
        assert len(result) == 2
        assert all(f['name'] in ['handle_request', 'process_data'] for f in result)
    
    @pytest.mark.unit
    def test_find_undocumented_handlers_non_handlers_excluded(self):
        """Test that non-handler functions are excluded."""
        functions = [
            {'name': 'normal_func', 'is_handler': False, 'docstring': ''},
            {'name': 'another_func', 'is_handler': False, 'docstring': '   '},
        ]
        result = find_undocumented_handlers(functions)
        assert result == []


class TestFindDuplicateNames:
    """Test duplicate name detection."""
    
    @pytest.mark.unit
    def test_find_duplicate_names_empty(self):
        """Test with empty function list."""
        result = find_duplicate_names([])
        assert result == {}
    
    @pytest.mark.unit
    def test_find_duplicate_names_no_duplicates(self):
        """Test with no duplicate names."""
        functions = [
            {'name': 'func1', 'file': 'file1.py'},
            {'name': 'func2', 'file': 'file2.py'},
            {'name': 'func3', 'file': 'file3.py'},
        ]
        result = find_duplicate_names(functions)
        assert result == {}
    
    @pytest.mark.unit
    def test_find_duplicate_names_with_duplicates(self):
        """Test detection of duplicate function names."""
        functions = [
            {'name': 'func1', 'file': 'file1.py'},
            {'name': 'func1', 'file': 'file2.py'},
            {'name': 'func2', 'file': 'file3.py'},
            {'name': 'func2', 'file': 'file4.py'},
            {'name': 'func2', 'file': 'file5.py'},
        ]
        result = find_duplicate_names(functions)
        assert 'func1' in result
        assert 'func2' in result
        assert len(result['func1']) == 2
        assert len(result['func2']) == 3
        assert 'file1.py' in result['func1']
        assert 'file2.py' in result['func1']
        assert 'file3.py' in result['func2']
        assert 'file4.py' in result['func2']
        assert 'file5.py' in result['func2']


class TestPrintDashboard:
    """Test dashboard printing."""
    
    @pytest.mark.unit
    def test_print_dashboard_empty(self, capsys):
        """Test dashboard with empty function list."""
        print_dashboard([])
        output = capsys.readouterr().out
        assert "=== AI DECISION SUPPORT DASHBOARD ===" in output
        assert "Total functions: 0" in output
        assert "Codebase is in excellent shape!" in output
    
    @pytest.mark.unit
    def test_print_dashboard_with_complexity(self, capsys):
        """Test dashboard with complexity functions."""
        functions = [
            {'name': 'critical_func', 'complexity': 250, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': '', 'file': 'test.py'},
            {'name': 'high_func', 'complexity': 150, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': '', 'file': 'test.py'},
            {'name': 'moderate_func', 'complexity': 75, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': '', 'file': 'test.py'},
        ]
        print_dashboard(functions)
        output = capsys.readouterr().out
        assert "Total functions: 3" in output
        assert "[CRITICAL]" in output
        assert "[HIGH]" in output
        assert "[MODERATE]" in output
        assert "critical_func" in output
        assert "high_func" in output
        assert "moderate_func" in output
    
    @pytest.mark.unit
    def test_print_dashboard_with_undocumented_handlers(self, capsys):
        """Test dashboard with undocumented handlers."""
        functions = [
            {'name': 'handle_request', 'is_handler': True, 'docstring': '', 'complexity': 10, 'is_test': False, 'is_special': False, 'file': 'test.py'},
            {'name': 'process_data', 'is_handler': True, 'docstring': '   ', 'complexity': 10, 'is_test': False, 'is_special': False, 'file': 'test.py'},
        ]
        print_dashboard(functions)
        output = capsys.readouterr().out
        assert "[DOC] Undocumented Handlers: 2" in output
        assert "handle_request" in output
        assert "process_data" in output
    
    @pytest.mark.unit
    def test_print_dashboard_with_duplicates(self, capsys):
        """Test dashboard with duplicate names."""
        functions = [
            {'name': 'func1', 'file': 'file1.py', 'complexity': 10, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': ''},
            {'name': 'func1', 'file': 'file2.py', 'complexity': 10, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': ''},
            {'name': 'func2', 'file': 'file3.py', 'complexity': 10, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': ''},
            {'name': 'func2', 'file': 'file4.py', 'complexity': 10, 'is_test': False, 'is_handler': False, 'is_special': False, 'docstring': ''},
        ]
        print_dashboard(functions)
        output = capsys.readouterr().out
        assert "[DUPE] Duplicate Function Names: 2" in output
        assert "func1" in output
        assert "func2" in output


class TestMain:
    """Test main function."""
    
    @pytest.mark.unit
    @patch.object(decision_support_module, 'scan_all_functions')
    @patch('development_tools.reports.decision_support.print_dashboard')
    @patch('sys.argv', ['decision_support.py'])
    def test_main_default_args(self, mock_print, mock_scan):
        """Test main function with default arguments."""
        mock_scan.return_value = []
        result = main()
        assert result == 0
        mock_scan.assert_called_once_with(include_tests=False, include_dev_tools=False)
        mock_print.assert_called_once_with([])
    
    @pytest.mark.unit
    @patch.object(decision_support_module, 'scan_all_functions')
    @patch('development_tools.reports.decision_support.print_dashboard')
    @patch('sys.argv', ['decision_support.py', '--include-tests'])
    def test_main_include_tests(self, mock_print, mock_scan):
        """Test main function with --include-tests flag."""
        mock_scan.return_value = []
        result = main()
        assert result == 0
        mock_scan.assert_called_once_with(include_tests=True, include_dev_tools=False)
        mock_print.assert_called_once_with([])
    
    @pytest.mark.unit
    @patch.object(decision_support_module, 'scan_all_functions')
    @patch('development_tools.reports.decision_support.print_dashboard')
    @patch('sys.argv', ['decision_support.py', '--include-dev-tools'])
    def test_main_include_dev_tools(self, mock_print, mock_scan):
        """Test main function with --include-dev-tools flag."""
        mock_scan.return_value = []
        result = main()
        assert result == 0
        mock_scan.assert_called_once_with(include_tests=False, include_dev_tools=True)
        mock_print.assert_called_once_with([])
    
    @pytest.mark.unit
    @patch.object(decision_support_module, 'scan_all_functions')
    @patch('development_tools.reports.decision_support.print_dashboard')
    @patch('sys.argv', ['decision_support.py', '--include-tests', '--include-dev-tools'])
    def test_main_both_flags(self, mock_print, mock_scan):
        """Test main function with both flags."""
        mock_scan.return_value = []
        result = main()
        assert result == 0
        mock_scan.assert_called_once_with(include_tests=True, include_dev_tools=True)
        mock_print.assert_called_once_with([])

