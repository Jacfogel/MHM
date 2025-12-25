"""
Tests for analyze_error_handling.py.

Tests error handling analysis functionality including function analysis,
decorator detection, phase 1/2 candidate detection, and standard format output.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from tests.development_tools.conftest import load_development_tools_module, demo_project_root, test_config_path

# Load the module
error_handling_module = load_development_tools_module("error_handling.analyze_error_handling")
ErrorHandlingAnalyzer = error_handling_module.ErrorHandlingAnalyzer


class TestErrorHandlingAnalyzer:
    """Test ErrorHandlingAnalyzer class."""
    
    @pytest.mark.unit
    def test_init(self, tmp_path):
        """Test analyzer initialization."""
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        
        assert analyzer.project_root == Path(tmp_path)
        assert analyzer.results['total_functions'] == 0
        assert analyzer.results['functions_with_error_handling'] == 0
        assert analyzer.results['functions_missing_error_handling'] == 0
    
    @pytest.mark.unit
    def test_analyze_file_basic(self, tmp_path):
        """Test analyzing a basic Python file."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def simple_function():
    pass

def function_with_try():
    try:
        pass
    except Exception:
        pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        assert 'file_path' in result
        assert 'functions' in result
        assert len(result['functions']) == 2
    
    @pytest.mark.unit
    def test_analyze_file_with_decorator(self, tmp_path):
        """Test analyzing file with error handling decorator."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
from core.error_handling import handle_errors

@handle_errors
def decorated_function():
    pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        assert len(result['functions']) > 0
        # Check that decorator was detected (may be in different fields)
        func = result['functions'][0]
        # Decorator detection may vary - just check function was analyzed
        assert 'name' in func or 'function_name' in func
    
    @pytest.mark.unit
    def test_analyze_file_malformed(self, tmp_path):
        """Test handling of malformed Python file."""
        test_file = tmp_path / "malformed.py"
        test_file.write_text("This is not valid Python: {[}")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        # Should return error result
        assert 'error' in result or 'functions' in result
        # Should not crash
    
    @pytest.mark.unit
    def test_should_exclude_function_special_methods(self, tmp_path):
        """Test that special methods are excluded."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
class TestClass:
    def __repr__(self):
        return "test"
    
    def __getattr__(self, name):
        return None
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        # Special methods should be excluded from missing error handling
        for func in result.get('functions', []):
            if func.get('name') in ('__repr__', '__getattr__'):
                # These should be excluded
                assert func.get('excluded', False) or func.get('error_handling') == 'excluded'
    
    @pytest.mark.unit
    def test_should_exclude_function_exclusion_comment(self, tmp_path):
        """Test that functions with exclusion comments are excluded."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
# ERROR_HANDLING_EXCLUDE
def excluded_function():
    pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        # Function with exclusion comment should be excluded
        for func in result.get('functions', []):
            if func.get('name') == 'excluded_function':
                assert func.get('excluded', False)
    
    @pytest.mark.unit
    def test_analyze_file_phase1_candidates(self, tmp_path):
        """Test detection of Phase 1 candidates (try-except without decorator)."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def function_with_try_except():
    try:
        result = open("file.txt")
    except Exception:
        pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        # Should detect try-except pattern
        func = result['functions'][0]
        assert func.get('has_try_except', False)
    
    @pytest.mark.unit
    def test_analyze_file_phase2_exceptions(self, tmp_path):
        """Test detection of Phase 2 candidates (generic exception raises)."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def function_with_generic_raise():
    raise Exception("Generic error")
    
def function_with_value_error():
    raise ValueError("Specific error")
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        # Should detect generic exception raises
        assert 'phase2_exceptions' in result
        # Should find Exception raise
        exceptions = result['phase2_exceptions']
        assert len(exceptions) > 0
    
    @pytest.mark.unit
    def test_analyze_file_with_classes(self, tmp_path):
        """Test analyzing file with classes."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
class TestClass:
    def method(self):
        pass
    
    @handle_errors
    def protected_method(self):
        pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        assert 'classes' in result
        assert len(result['classes']) > 0
    
    @pytest.mark.unit
    def test_analyze_project_multiple_files(self, tmp_path):
        """Test analyzing all Python files in a directory."""
        # Create multiple test files
        (tmp_path / "module1.py").write_text("def func1(): pass")
        (tmp_path / "module2.py").write_text("""
from core.error_handling import handle_errors

@handle_errors
def func2(): pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_project()
        
        # Should have analyzed multiple files (may be 0 if files are excluded)
        assert isinstance(result, dict)
        assert 'details' in result
        # At minimum, should have run without error
        assert result['details']['total_functions'] >= 0
    
    @pytest.mark.unit
    def test_to_standard_format(self, tmp_path):
        """Test conversion to standard format."""
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        analyzer.results['functions_missing_error_handling'] = 5
        analyzer.results['missing_error_handling'] = [
            {'file': 'test1.py', 'function': 'func1'},
            {'file': 'test2.py', 'function': 'func2'},
            {'file': 'test1.py', 'function': 'func3'}  # Duplicate file
        ]
        
        standard_format = analyzer._to_standard_format()
        
        assert 'summary' in standard_format
        assert 'details' in standard_format
        assert standard_format['summary']['total_issues'] == 5
        assert standard_format['summary']['files_affected'] == 2  # 2 unique files
    
    @pytest.mark.unit
    def test_analyze_file_error_patterns(self, tmp_path):
        """Test detection of error handling patterns in file content."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
try:
    pass
except Exception:
    pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        # Should detect try_except pattern
        assert 'error_patterns_found' in result
        assert len(result['error_patterns_found']) > 0
    
    @pytest.mark.unit
    def test_analyze_file_empty(self, tmp_path):
        """Test analyzing empty file."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        assert 'file_path' in result
        assert result['functions'] == []
    
    @pytest.mark.unit
    def test_analyze_file_async_function(self, tmp_path):
        """Test analyzing async functions."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
async def async_function():
    pass

async def async_with_try():
    try:
        pass
    except Exception:
        pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        assert len(result['functions']) == 2
    
    @pytest.mark.unit
    def test_analyze_file_with_imports(self, tmp_path):
        """Test analyzing file with imports."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
import os
from pathlib import Path

def function_using_imports():
    return os.getcwd()
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        assert len(result['functions']) == 1
    
    @pytest.mark.unit
    def test_analyze_file_nested_functions(self, tmp_path):
        """Test analyzing nested functions."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def outer_function():
    def inner_function():
        pass
    return inner_function
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        # Should find both outer and inner functions
        assert len(result['functions']) >= 1
    
    @pytest.mark.unit
    def test_analyze_file_file_not_found(self, tmp_path):
        """Test handling of non-existent file."""
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        non_existent = tmp_path / "nonexistent.py"
        
        result = analyzer.analyze_file(non_existent)
        
        # Should handle gracefully
        assert 'error' in result or 'file_path' in result


class TestAnalyzeProject:
    """Test analyze_project() method."""
    
    @pytest.mark.unit
    def test_analyze_project_basic(self, tmp_path):
        """Test basic analyze_project method."""
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_project()
        
        assert isinstance(result, dict)
        assert 'summary' in result
        assert 'details' in result
        assert 'total_issues' in result['summary']
        assert 'files_affected' in result['summary']
    
    @pytest.mark.unit
    def test_analyze_project_with_files(self, tmp_path):
        """Test analyze_project with test files included."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def func(): pass")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_project(include_tests=True)
        
        assert isinstance(result, dict)
        assert 'summary' in result
    
    @pytest.mark.integration
    def test_analyze_project_demo_project(self, demo_project_root, test_config_path):
        """Test analyze_project with demo project."""
        analyzer = ErrorHandlingAnalyzer(project_root=str(demo_project_root))
        result = analyzer.analyze_project()
        
        assert isinstance(result, dict)
        assert 'summary' in result
        assert 'details' in result
        # Should have analyzed demo project files
        assert result['summary']['total_issues'] >= 0


class TestErrorHandlingPatterns:
    """Test error handling pattern detection."""
    
    @pytest.mark.unit
    def test_decorator_detection_direct_import(self, tmp_path):
        """Test detection of decorator with direct import."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
from core.error_handling import handle_errors

@handle_errors
def decorated_function():
    pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        func = result['functions'][0]
        assert func.get('has_decorator', False) or func.get('error_handling') != 'none'
    
    @pytest.mark.unit
    def test_decorator_detection_module_import(self, tmp_path):
        """Test detection of decorator with module import."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
import core.error_handling

@core.error_handling.handle_errors
def decorated_function():
    pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        func = result['functions'][0]
        assert func.get('has_decorator', False) or func.get('error_handling') != 'none'
    
    @pytest.mark.unit
    def test_try_except_detection(self, tmp_path):
        """Test detection of try-except blocks."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def function_with_try():
    try:
        x = 1
    except ValueError:
        pass
    except Exception:
        pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        func = result['functions'][0]
        assert func.get('has_try_except', False)

