"""
Tests for error handling recommendations generation.

Tests recommendation generation functionality in analyze_error_handling.py,
including coverage recommendations, missing error handling recommendations,
and quality recommendations.
"""

import pytest
from pathlib import Path

from tests.development_tools.conftest import load_development_tools_module

# Load the module
error_handling_module = load_development_tools_module("error_handling.analyze_error_handling")
ErrorHandlingAnalyzer = error_handling_module.ErrorHandlingAnalyzer


class TestGenerateRecommendations:
    """Test _generate_recommendations method in ErrorHandlingAnalyzer."""
    
    def _create_analyzer_with_results(self, analysis_results):
        """Create an ErrorHandlingAnalyzer instance with pre-populated results."""
        analyzer = ErrorHandlingAnalyzer(str(Path.cwd()))
        analyzer.results = analysis_results
        return analyzer
    
    @pytest.mark.unit
    def test_generate_recommendations_low_coverage(self):
        """Test recommendations for low error handling coverage."""
        analysis_results = {
            'analyze_error_handling': 50.0,  # Below 80% threshold
            'functions_missing_error_handling': 10
        }
        
        analyzer = self._create_analyzer_with_results(analysis_results)
        analyzer._generate_recommendations()
        recommendations = analyzer.results.get('recommendations', [])
        
        assert len(recommendations) > 0
        assert any('coverage' in rec.lower() or '50.0' in rec for rec in recommendations)
    
    @pytest.mark.unit
    def test_generate_recommendations_high_coverage(self):
        """Test recommendations when coverage is high."""
        analysis_results = {
            'analyze_error_handling': 95.0,  # Above 80% threshold
            'functions_missing_error_handling': 0
        }
        
        analyzer = self._create_analyzer_with_results(analysis_results)
        analyzer._generate_recommendations()
        recommendations = analyzer.results.get('recommendations', [])
        
        # Should not have coverage recommendation
        assert not any('coverage' in rec.lower() and 'improve' in rec.lower() for rec in recommendations)
    
    @pytest.mark.unit
    def test_generate_recommendations_missing_error_handling(self):
        """Test recommendations for missing error handling."""
        analysis_results = {
            'analyze_error_handling': 80.0,
            'functions_missing_error_handling': 5
        }
        
        analyzer = self._create_analyzer_with_results(analysis_results)
        analyzer._generate_recommendations()
        recommendations = analyzer.results.get('recommendations', [])
        
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
        
        analyzer = self._create_analyzer_with_results(analysis_results)
        analyzer._generate_recommendations()
        recommendations = analyzer.results.get('recommendations', [])
        
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
        
        analyzer = self._create_analyzer_with_results(analysis_results)
        analyzer._generate_recommendations()
        recommendations = analyzer.results.get('recommendations', [])
        
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
        
        analyzer = self._create_analyzer_with_results(analysis_results)
        analyzer._generate_recommendations()
        recommendations = analyzer.results.get('recommendations', [])
        
        # Should have priority recommendation for critical functions
        assert any('priority' in rec.lower() or 'critical' in rec.lower() for rec in recommendations)
        assert any('2' in rec and 'function' in rec.lower() for rec in recommendations)
    
    @pytest.mark.unit
    def test_generate_recommendations_empty_results(self):
        """Test recommendations with empty analysis results."""
        analysis_results = {}
        
        analyzer = self._create_analyzer_with_results(analysis_results)
        analyzer._generate_recommendations()
        recommendations = analyzer.results.get('recommendations', [])
        
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
        
        analyzer = self._create_analyzer_with_results(analysis_results)
        analyzer._generate_recommendations()
        recommendations = analyzer.results.get('recommendations', [])
        
        # Should have minimal or no recommendations
        assert isinstance(recommendations, list)


class TestRecommendationContent:
    """Test recommendation content quality."""
    
    def _create_analyzer_with_results(self, analysis_results):
        """Create an ErrorHandlingAnalyzer instance with pre-populated results."""
        analyzer = ErrorHandlingAnalyzer(str(Path.cwd()))
        analyzer.results = analysis_results
        return analyzer
    
    @pytest.mark.unit
    def test_recommendations_are_strings(self):
        """Test that all recommendations are strings."""
        analysis_results = {
            'analyze_error_handling': 50.0,
            'functions_missing_error_handling': 5
        }
        
        analyzer = self._create_analyzer_with_results(analysis_results)
        analyzer._generate_recommendations()
        recommendations = analyzer.results.get('recommendations', [])
        
        assert all(isinstance(rec, str) for rec in recommendations)
    
    @pytest.mark.unit
    def test_recommendations_not_empty(self):
        """Test that recommendations are not empty strings."""
        analysis_results = {
            'analyze_error_handling': 50.0,
            'functions_missing_error_handling': 5
        }
        
        analyzer = self._create_analyzer_with_results(analysis_results)
        analyzer._generate_recommendations()
        recommendations = analyzer.results.get('recommendations', [])
        
        assert all(len(rec) > 0 for rec in recommendations)
    
    @pytest.mark.unit
    def test_recommendations_include_numbers(self):
        """Test that recommendations include relevant numbers."""
        analysis_results = {
            'analyze_error_handling': 50.0,
            'functions_missing_error_handling': 5
        }
        
        analyzer = self._create_analyzer_with_results(analysis_results)
        analyzer._generate_recommendations()
        recommendations = analyzer.results.get('recommendations', [])
        
        # Should include coverage percentage or function count
        assert any(any(char.isdigit() for char in rec) for rec in recommendations)
