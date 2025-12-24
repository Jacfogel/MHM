"""
Tests for generate_error_handling_recommendations.py.

Tests recommendation generation functionality including coverage recommendations,
missing error handling recommendations, and quality recommendations.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from tests.development_tools.conftest import load_development_tools_module

# Load the module
recommendations_module = load_development_tools_module("error_handling.generate_error_handling_recommendations")
generate_recommendations = recommendations_module.generate_recommendations
main = recommendations_module.main


class TestGenerateRecommendations:
    """Test generate_recommendations function."""
    
    @pytest.mark.unit
    def test_generate_recommendations_low_coverage(self):
        """Test recommendations for low error handling coverage."""
        analysis_results = {
            'analyze_error_handling': 50.0,  # Below 80% threshold
            'functions_missing_error_handling': 10
        }
        
        recommendations = generate_recommendations(analysis_results)
        
        assert len(recommendations) > 0
        assert any('coverage' in rec.lower() or '50.0' in rec for rec in recommendations)
    
    @pytest.mark.unit
    def test_generate_recommendations_high_coverage(self):
        """Test recommendations when coverage is high."""
        analysis_results = {
            'analyze_error_handling': 95.0,  # Above 80% threshold
            'functions_missing_error_handling': 0
        }
        
        recommendations = generate_recommendations(analysis_results)
        
        # Should not have coverage recommendation
        assert not any('coverage' in rec.lower() and 'improve' in rec.lower() for rec in recommendations)
    
    @pytest.mark.unit
    def test_generate_recommendations_missing_error_handling(self):
        """Test recommendations for missing error handling."""
        analysis_results = {
            'analyze_error_handling': 80.0,
            'functions_missing_error_handling': 5
        }
        
        recommendations = generate_recommendations(analysis_results)
        
        assert any('5' in rec and 'function' in rec.lower() for rec in recommendations)
    
    @pytest.mark.unit
    def test_generate_recommendations_quality_none(self):
        """Test recommendations for functions with no error handling quality."""
        analysis_results = {
            'analyze_error_handling': 80.0,
            'functions_missing_error_handling': 0,
            'error_handling_quality': {
                'none': 3,
                'basic': 2,
                'good': 10
            }
        }
        
        recommendations = generate_recommendations(analysis_results)
        
        assert any('decorator' in rec.lower() for rec in recommendations)
    
    @pytest.mark.unit
    def test_generate_recommendations_try_except_vs_decorator(self):
        """Test recommendations when try-except is more common than decorator."""
        analysis_results = {
            'analyze_error_handling': 80.0,
            'functions_missing_error_handling': 0,
            'error_patterns': {
                'try_except': 10,
                'handle_errors_decorator': 2  # Fewer decorators than try-except
            }
        }
        
        recommendations = generate_recommendations(analysis_results)
        
        # Should recommend using decorator instead of try-except
        assert any('decorator' in rec.lower() and 'try-except' in rec.lower() for rec in recommendations)
    
    @pytest.mark.unit
    def test_generate_recommendations_critical_missing(self):
        """Test recommendations for critical missing error handling."""
        analysis_results = {
            'analyze_error_handling': 80.0,
            'functions_missing_error_handling': 0,
            'missing_error_handling': [
                {'function': 'func1', 'quality': 'none'},
                {'function': 'func2', 'quality': 'none'},
                {'function': 'func3', 'quality': 'basic'}
            ]
        }
        
        recommendations = generate_recommendations(analysis_results)
        
        # Should have priority recommendation for critical functions
        assert any('priority' in rec.lower() or 'critical' in rec.lower() for rec in recommendations)
        assert any('2' in rec and 'function' in rec.lower() for rec in recommendations)
    
    @pytest.mark.unit
    def test_generate_recommendations_empty_results(self):
        """Test recommendations with empty analysis results."""
        analysis_results = {}
        
        recommendations = generate_recommendations(analysis_results)
        
        # Should return empty list or minimal recommendations
        assert isinstance(recommendations, list)
    
    @pytest.mark.unit
    def test_generate_recommendations_all_good(self):
        """Test recommendations when everything is good."""
        analysis_results = {
            'analyze_error_handling': 95.0,
            'functions_missing_error_handling': 0,
            'error_handling_quality': {
                'none': 0,
                'basic': 0,
                'good': 100
            },
            'error_patterns': {
                'try_except': 5,
                'handle_errors_decorator': 10  # More decorators than try-except
            }
        }
        
        recommendations = generate_recommendations(analysis_results)
        
        # Should have minimal or no recommendations
        assert isinstance(recommendations, list)


class TestMainFunction:
    """Test main() function."""
    
    @pytest.mark.unit
    @patch('builtins.open', new_callable=mock_open)
    @patch('sys.argv', ['generate_error_handling_recommendations.py', '--input', 'input.json'])
    def test_main_with_input_output(self, mock_file):
        """Test main function with input and output files."""
        # Mock input file content
        analysis_results = {
            'analyze_error_handling': 50.0,
            'functions_missing_error_handling': 5
        }
        
        # Setup mock to return different content for read vs write
        mock_file.return_value.read.return_value = json.dumps(analysis_results)
        
        # Mock file operations
        with patch('pathlib.Path.exists', return_value=True):
            result = main()
        
        # Should complete successfully
        assert result is None or result == 0
    
    @pytest.mark.unit
    @patch('builtins.open', new_callable=mock_open)
    @patch('sys.argv', ['generate_error_handling_recommendations.py', '--input', 'input.json'])
    @patch('builtins.print')
    def test_main_without_output(self, mock_print, mock_file):
        """Test main function without output file (prints to stdout)."""
        analysis_results = {
            'analyze_error_handling': 50.0,
            'functions_missing_error_handling': 5
        }
        
        mock_file.return_value.read.return_value = json.dumps(analysis_results)
        
        with patch('pathlib.Path.exists', return_value=True):
            main()
        
        # Should have printed recommendations
        assert mock_print.called
    
    @pytest.mark.unit
    @patch('sys.argv', ['generate_error_handling_recommendations.py'])
    def test_main_missing_input(self):
        """Test main function with missing required input argument."""
        # Should raise SystemExit or ArgumentError
        with pytest.raises((SystemExit, ValueError, KeyError)):
            main()
    
    @pytest.mark.unit
    @patch('builtins.open', new_callable=mock_open)
    @patch('sys.argv', ['generate_error_handling_recommendations.py', '--input', 'input.json', '--output', 'output.json'])
    def test_main_write_output_file(self, mock_file):
        """Test main function writes to output file."""
        analysis_results = {
            'analyze_error_handling': 50.0,
            'functions_missing_error_handling': 5
        }
        
        mock_file.return_value.read.return_value = json.dumps(analysis_results)
        
        with patch('pathlib.Path.exists', return_value=True):
            main()
        
        # Should have written to output file
        assert mock_file.called


class TestRecommendationContent:
    """Test recommendation content quality."""
    
    @pytest.mark.unit
    def test_recommendations_are_strings(self):
        """Test that all recommendations are strings."""
        analysis_results = {
            'analyze_error_handling': 50.0,
            'functions_missing_error_handling': 5
        }
        
        recommendations = generate_recommendations(analysis_results)
        
        assert all(isinstance(rec, str) for rec in recommendations)
    
    @pytest.mark.unit
    def test_recommendations_not_empty(self):
        """Test that recommendations are not empty strings."""
        analysis_results = {
            'analyze_error_handling': 50.0,
            'functions_missing_error_handling': 5
        }
        
        recommendations = generate_recommendations(analysis_results)
        
        assert all(len(rec) > 0 for rec in recommendations)
    
    @pytest.mark.unit
    def test_recommendations_include_numbers(self):
        """Test that recommendations include relevant numbers."""
        analysis_results = {
            'analyze_error_handling': 50.0,
            'functions_missing_error_handling': 5
        }
        
        recommendations = generate_recommendations(analysis_results)
        
        # Should include coverage percentage or function count
        assert any(any(char.isdigit() for char in rec) for rec in recommendations)

