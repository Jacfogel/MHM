"""
Tests for generate_function_docstrings.py.

Tests function docstring generation functionality including function type detection,
template generation, and docstring insertion.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from tests.development_tools.conftest import load_development_tools_module, demo_project_root, test_config_path

# Load the module
docstrings_module = load_development_tools_module("functions.generate_function_docstrings")
detect_function_type = docstrings_module.detect_function_type
generate_function_template = docstrings_module.generate_function_template
add_docstring_to_function = docstrings_module.add_docstring_to_function
scan_and_document_functions = docstrings_module.scan_and_document_functions


class TestDetectFunctionType:
    """Test detect_function_type function."""
    
    @pytest.mark.unit
    def test_detect_regular_function(self):
        """Test detecting regular function."""
        func_type = detect_function_type(
            file_path="module.py",
            func_name="regular_function",
            decorators=[],
            args=[],
            function_type_detection={}
        )
        
        assert func_type == "regular_function"
    
    @pytest.mark.unit
    def test_detect_test_function(self):
        """Test detecting test function."""
        func_type = detect_function_type(
            file_path="test_module.py",
            func_name="test_something",
            decorators=[],
            args=[],
            function_type_detection={
                'test_function': {
                    'name_patterns': ['test_']
                }
            }
        )
        
        assert func_type == "test_function"
    
    @pytest.mark.unit
    def test_detect_special_method(self):
        """Test detecting special method."""
        func_type = detect_function_type(
            file_path="module.py",
            func_name="__init__",
            decorators=[],
            args=[],
            function_type_detection={
                'special_method': {
                    'name_pattern': r'^__\w+__$'
                }
            }
        )
        
        assert func_type == "special_method"
    
    @pytest.mark.unit
    def test_detect_constructor(self):
        """Test detecting constructor."""
        func_type = detect_function_type(
            file_path="module.py",
            func_name="__init__",
            decorators=[],
            args=[],
            function_type_detection={
                'constructor': {
                    'name': '__init__'
                }
            }
        )
        
        assert func_type == "constructor"
    
    @pytest.mark.unit
    def test_detect_main_function(self):
        """Test detecting main function."""
        func_type = detect_function_type(
            file_path="module.py",
            func_name="main",
            decorators=[],
            args=[],
            function_type_detection={
                'main_function': {
                    'name': 'main'
                }
            }
        )
        
        assert func_type == "main_function"
    
    @pytest.mark.unit
    def test_detect_ui_generated(self):
        """Test detecting UI generated function."""
        func_type = detect_function_type(
            file_path="ui/widget_pyqt.py",
            func_name="setupUi",
            decorators=[],
            args=[],
            function_type_detection={
                'ui_generated': {
                    'file_pattern': 'ui/',
                    'names': ['setupUi', 'retranslateUi']
                }
            }
        )
        
        assert func_type == "ui_generated"


class TestGenerateFunctionTemplate:
    """Test generate_function_template function."""
    
    @pytest.mark.unit
    def test_generate_template_regular_function(self):
        """Test generating template for regular function."""
        template = generate_function_template(
            func_type="regular_function",
            func_name="test_func",
            file_path="module.py",
            args=[],
            formatting_rules={}
        )
        
        assert isinstance(template, str)
        assert len(template) > 0
    
    @pytest.mark.unit
    def test_generate_template_test_function(self):
        """Test generating template for test function."""
        template = generate_function_template(
            func_type="test_function",
            func_name="test_something",
            file_path="test_module.py",
            args=[],
            formatting_rules={}
        )
        
        assert isinstance(template, str)
        assert "test" in template.lower() or "TEST" in template
    
    @pytest.mark.unit
    def test_generate_template_special_method(self):
        """Test generating template for special method."""
        template = generate_function_template(
            func_type="special_method",
            func_name="__init__",
            file_path="module.py",
            args=[],
            formatting_rules={}
        )
        
        assert isinstance(template, str)
        assert "__init__" in template.lower() or "initialize" in template.lower()
    
    @pytest.mark.unit
    def test_generate_template_with_custom_formatting(self):
        """Test generating template with custom formatting rules."""
        template = generate_function_template(
            func_type="regular_function",
            func_name="test_func",
            file_path="module.py",
            args=[],
            formatting_rules={
                'regular_function': '"""Function {func_name} in {file_path}."""'
            }
        )
        
        assert "test_func" in template
        assert "module.py" in template
    
    @pytest.mark.unit
    def test_generate_template_ui_generated(self):
        """Test generating template for UI generated function."""
        template = generate_function_template(
            func_type="ui_generated",
            func_name="setupUi",
            file_path="ui/widget_pyqt.py",
            args=[],
            formatting_rules={}
        )
        
        assert isinstance(template, str)
        assert "ui" in template.lower() or "Qt" in template


class TestAddDocstringToFunction:
    """Test add_docstring_to_function function."""
    
    @pytest.mark.unit
    def test_add_docstring_basic(self, tmp_path):
        """Test adding docstring to a basic function."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def test_func():
    return True
""")
        
        result = add_docstring_to_function(
            file_path=str(test_file),
            func_name="test_func",
            line_number=2,
            docstring='"""Test function."""'
        )
        
        assert result is True
        
        # Verify docstring was added
        content = test_file.read_text()
        assert '"""Test function."""' in content
    
    @pytest.mark.unit
    def test_add_docstring_with_decorator(self, tmp_path):
        """Test adding docstring to function with decorator."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
@handle_errors
def test_func():
    return True
""")
        
        result = add_docstring_to_function(
            file_path=str(test_file),
            func_name="test_func",
            line_number=2,
            docstring='"""Test function."""'
        )
        
        assert result is True
        
        # Verify docstring was added after decorator
        content = test_file.read_text()
        assert '"""Test function."""' in content
    
    @pytest.mark.unit
    def test_add_docstring_already_has_docstring(self, tmp_path):
        """Test adding docstring when function already has one."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def test_func():
    \"\"\"Existing docstring.\"\"\"
    return True
""")
        
        result = add_docstring_to_function(
            file_path=str(test_file),
            func_name="test_func",
            line_number=2,
            docstring='"""New docstring."""'
        )
        
        assert result is False  # Should not add if already has docstring
        
        # Verify original docstring is still there
        content = test_file.read_text()
        assert '"""Existing docstring."""' in content
        assert '"""New docstring."""' not in content
    
    @pytest.mark.unit
    def test_add_docstring_one_liner(self, tmp_path):
        """Test adding docstring to one-liner function (should fail)."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("def test_func(): return True\n")
        
        result = add_docstring_to_function(
            file_path=str(test_file),
            func_name="test_func",
            line_number=1,
            docstring='"""Test function."""'
        )
        
        assert result is False  # Should not add to one-liner
    
    @pytest.mark.unit
    def test_add_docstring_function_not_found(self, tmp_path):
        """Test adding docstring when function is not found."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("def other_func(): pass\n")
        
        result = add_docstring_to_function(
            file_path=str(test_file),
            func_name="nonexistent_func",
            line_number=1,
            docstring='"""Test function."""'
        )
        
        assert result is False
    
    @pytest.mark.unit
    def test_add_docstring_file_not_found(self):
        """Test adding docstring when file doesn't exist."""
        result = add_docstring_to_function(
            file_path="/nonexistent/path/file.py",
            func_name="test_func",
            line_number=1,
            docstring='"""Test function."""'
        )
        
        assert result is False


class TestScanAndDocumentFunctions:
    """Test scan_and_document_functions function."""
    
    @pytest.mark.unit
    def test_scan_and_document_basic(self, tmp_path):
        """Test scanning and documenting functions."""
        # Create a test file with function missing docstring
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def undocumented_func():
    return True
""")
        
        # Mock config to scan our test directory
        with patch('development_tools.functions.generate_function_docstrings.config.get_scan_directories', return_value=[str(tmp_path)]):
            results = scan_and_document_functions(project_root_path=tmp_path)
        
        assert isinstance(results, dict)
        assert 'files_processed' in results
        assert 'functions_documented' in results
    
    @pytest.mark.unit
    def test_scan_and_document_empty_project(self, tmp_path):
        """Test scanning empty project."""
        results = scan_and_document_functions(project_root_path=tmp_path)
        
        assert isinstance(results, dict)
        assert results['files_processed'] >= 0
    
    @pytest.mark.integration
    def test_scan_and_document_demo_project(self, demo_project_root, test_config_path):
        """Test scanning demo project."""
        # This may document functions in the demo project
        results = scan_and_document_functions(project_root_path=demo_project_root)
        
        assert isinstance(results, dict)
        assert 'files_processed' in results
        assert 'functions_documented' in results
        assert 'functions_skipped' in results
        assert 'errors' in results

