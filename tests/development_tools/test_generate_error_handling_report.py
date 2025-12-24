"""
Tests for generate_error_handling_report.py.

Tests error handling report generation functionality including summary printing,
JSON report saving, and main function execution.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from tests.development_tools.conftest import load_development_tools_module

# Load the module
report_module = load_development_tools_module("error_handling.generate_error_handling_report")
ErrorHandlingReportGenerator = report_module.ErrorHandlingReportGenerator
main = report_module.main


class TestErrorHandlingReportGenerator:
    """Test ErrorHandlingReportGenerator class."""
    
    @pytest.mark.unit
    def test_init(self):
        """Test initialization with analysis results."""
        analysis_results = {
            'total_functions': 100,
            'functions_with_error_handling': 95,
            'analyze_error_handling': 95.0
        }
        
        generator = ErrorHandlingReportGenerator(analysis_results)
        
        assert generator.results == analysis_results
    
    @pytest.mark.unit
    def test_print_summary_basic(self):
        """Test printing basic summary."""
        analysis_results = {
            'total_functions': 100,
            'functions_with_try_except': 50,
            'functions_with_error_handling': 95,
            'functions_with_decorators': 80,
            'functions_missing_error_handling': 5,
            'analyze_error_handling': 95.0,
            'error_handling_quality': {'good': 80, 'basic': 15, 'none': 5},
            'error_patterns': {'try_except': 50, 'handle_errors_decorator': 80},
            'phase1_total': 10,
            'phase1_by_priority': {'high': 5, 'medium': 3, 'low': 2},
            'phase1_candidates': [],
            'phase2_total': 0,
            'phase2_by_type': {},
            'phase2_exceptions': [],
            'missing_error_handling': []
        }
        
        generator = ErrorHandlingReportGenerator(analysis_results)
        # Should execute without error
        generator.print_summary()
        
        # Verify generator has results
        assert generator.results == analysis_results
    
    @pytest.mark.unit
    def test_print_summary_with_phase1_candidates(self):
        """Test printing summary with Phase 1 candidates."""
        analysis_results = {
            'total_functions': 100,
            'functions_with_try_except': 50,
            'functions_with_error_handling': 95,
            'functions_with_decorators': 80,
            'functions_missing_error_handling': 5,
            'analyze_error_handling': 95.0,
            'error_handling_quality': {'good': 80, 'basic': 15, 'none': 5},
            'error_patterns': {'try_except': 50, 'handle_errors_decorator': 80},
            'phase1_total': 10,
            'phase1_by_priority': {'high': 5, 'medium': 3, 'low': 2},
            'phase1_candidates': [
                {'priority': 'high', 'file_path': 'test.py', 'function_name': 'test_func', 
                 'line_start': 10, 'operation_type': 'file_io'}
            ] * 15,  # 15 candidates, should show first 10
            'phase2_total': 0,
            'phase2_by_type': {},
            'phase2_exceptions': [],
            'missing_error_handling': []
        }
        
        generator = ErrorHandlingReportGenerator(analysis_results)
        # Should execute without error
        generator.print_summary()
        
        # Verify candidates are in results
        assert len(generator.results['phase1_candidates']) == 15
    
    @pytest.mark.unit
    def test_print_summary_with_phase2_exceptions(self):
        """Test printing summary with Phase 2 exceptions."""
        analysis_results = {
            'total_functions': 100,
            'functions_with_try_except': 50,
            'functions_with_error_handling': 95,
            'functions_with_decorators': 80,
            'functions_missing_error_handling': 5,
            'analyze_error_handling': 95.0,
            'error_handling_quality': {'good': 80, 'basic': 15, 'none': 5},
            'error_patterns': {'try_except': 50, 'handle_errors_decorator': 80},
            'phase1_total': 0,
            'phase1_by_priority': {'high': 0, 'medium': 0, 'low': 0},
            'phase1_candidates': [],
            'phase2_total': 5,
            'phase2_by_type': {'Exception': 3, 'ValueError': 2},
            'phase2_exceptions': [
                {'file_path': 'test.py', 'line_number': 20, 'exception_type': 'Exception',
                 'suggested_replacement': 'BaseError', 'function_name': 'test_func', 'function_line': 15}
            ] * 15,  # 15 exceptions, should show first 10
            'missing_error_handling': []
        }
        
        generator = ErrorHandlingReportGenerator(analysis_results)
        # Should execute without error
        generator.print_summary()
        
        # Verify exceptions are in results
        assert len(generator.results['phase2_exceptions']) == 15
    
    @pytest.mark.unit
    def test_print_summary_with_missing_error_handling(self):
        """Test printing summary with missing error handling."""
        analysis_results = {
            'total_functions': 100,
            'functions_with_try_except': 50,
            'functions_with_error_handling': 95,
            'functions_with_decorators': 80,
            'functions_missing_error_handling': 5,
            'analyze_error_handling': 95.0,
            'error_handling_quality': {'good': 80, 'basic': 15, 'none': 5},
            'error_patterns': {'try_except': 50, 'handle_errors_decorator': 80},
            'phase1_total': 0,
            'phase1_by_priority': {'high': 0, 'medium': 0, 'low': 0},
            'phase1_candidates': [],
            'phase2_total': 0,
            'phase2_by_type': {},
            'phase2_exceptions': [],
            'missing_error_handling': [
                {'file': 'test.py', 'function': 'test_func', 'line': 10}
            ] * 15  # 15 missing, should show first 10
        }
        
        generator = ErrorHandlingReportGenerator(analysis_results)
        # Should execute without error
        generator.print_summary()
        
        # Verify missing error handling is in results
        assert len(generator.results['missing_error_handling']) == 15
    
    @pytest.mark.unit
    def test_print_summary_with_recommendations(self):
        """Test printing summary with recommendations."""
        analysis_results = {
            'total_functions': 100,
            'functions_with_try_except': 50,
            'functions_with_error_handling': 95,
            'functions_with_decorators': 80,
            'functions_missing_error_handling': 5,
            'analyze_error_handling': 95.0,
            'error_handling_quality': {'good': 80, 'basic': 15, 'none': 5},
            'error_patterns': {'try_except': 50, 'handle_errors_decorator': 80},
            'phase1_total': 0,
            'phase1_by_priority': {'high': 0, 'medium': 0, 'low': 0},
            'phase1_candidates': [],
            'phase2_total': 0,
            'phase2_by_type': {},
            'phase2_exceptions': [],
            'missing_error_handling': [],
            'recommendations': ['Recommendation 1', 'Recommendation 2']
        }
        
        generator = ErrorHandlingReportGenerator(analysis_results)
        # Should execute without error
        generator.print_summary()
        
        # Verify recommendations are in results
        assert len(generator.results['recommendations']) == 2
    
    @pytest.mark.unit
    @patch('development_tools.shared.file_rotation.FileRotator')
    def test_save_json_report(self, mock_rotator_class, tmp_path):
        """Test saving JSON report."""
        
        analysis_results = {
            'total_functions': 100,
            'analyze_error_handling': 95.0
        }
        
        output_path = tmp_path / "error_handling_report.json"
        generator = ErrorHandlingReportGenerator(analysis_results)
        generator.save_json_report(output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Verify JSON content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'generated_by' in data
        assert 'error_handling_results' in data
        assert data['error_handling_results'] == analysis_results
    
    @pytest.mark.unit
    @patch('development_tools.shared.file_rotation.FileRotator')
    def test_save_json_report_with_existing_file(self, mock_rotator_class, tmp_path):
        """Test saving JSON report when file already exists (should rotate)."""
        
        # Create existing file
        output_path = tmp_path / "error_handling_report.json"
        output_path.write_text('{"old": "data"}')
        
        analysis_results = {'total_functions': 100}
        generator = ErrorHandlingReportGenerator(analysis_results)
        generator.save_json_report(output_path)
        
        # Verify file was rotated
        mock_rotator_class.assert_called()
    
    @pytest.mark.unit
    @patch('builtins.open', new_callable=mock_open)
    @patch('sys.argv', ['generate_error_handling_report.py', '--input', 'input.json', '--format', 'json'])
    @patch('pathlib.Path.exists', return_value=True)
    def test_main_json_format(self, mock_exists, mock_file):
        """Test main function with JSON format."""
        analysis_results = {'total_functions': 100}
        mock_file.return_value.read.return_value = json.dumps(analysis_results)
        
        result = main()
        
        assert result == 0
    
    @pytest.mark.unit
    @patch('sys.argv', ['generate_error_handling_report.py', '--input', 'input.json', '--format', 'summary'])
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    def test_main_summary_format(self, mock_file, mock_exists):
        """Test main function with summary format."""
        analysis_results = {'total_functions': 100, 'analyze_error_handling': 95.0,
                           'functions_with_error_handling': 95, 'functions_with_decorators': 80,
                           'functions_with_try_except': 50, 'functions_missing_error_handling': 5,
                           'error_handling_quality': {}, 'error_patterns': {},
                           'phase1_total': 0, 'phase1_by_priority': {}, 'phase1_candidates': [],
                           'phase2_total': 0, 'phase2_by_type': {}, 'phase2_exceptions': [],
                           'missing_error_handling': []}
        mock_file.return_value.read.return_value = json.dumps(analysis_results)
        
        result = main()
        
        assert result == 0
    
    @pytest.mark.unit
    @patch('sys.argv', ['generate_error_handling_report.py', '--input', 'input.json', '--format', 'both'])
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    def test_main_both_formats(self, mock_file, mock_exists, tmp_path):
        """Test main function with both formats."""
        analysis_results = {'total_functions': 100, 'analyze_error_handling': 95.0,
                           'functions_with_error_handling': 95, 'functions_with_decorators': 80,
                           'functions_with_try_except': 50, 'functions_missing_error_handling': 5,
                           'error_handling_quality': {}, 'error_patterns': {},
                           'phase1_total': 0, 'phase1_by_priority': {}, 'phase1_candidates': [],
                           'phase2_total': 0, 'phase2_by_type': {}, 'phase2_exceptions': [],
                           'missing_error_handling': []}
        mock_file.return_value.read.return_value = json.dumps(analysis_results)
        
        result = main()
        
        assert result == 0
    
    @pytest.mark.unit
    @patch('sys.argv', ['generate_error_handling_report.py'])
    def test_main_missing_input(self):
        """Test main function with missing required input argument."""
        with pytest.raises((SystemExit, KeyError)):
            main()

