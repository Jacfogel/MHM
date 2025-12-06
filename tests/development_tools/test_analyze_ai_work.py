"""
Tests for analyze_ai_work.py.

Tests AI work validation functionality including documentation completeness,
changelog sync, and structural validation.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from tests.development_tools.conftest import load_development_tools_module, demo_project_root

# Load the module
ai_work_module = load_development_tools_module("ai_work.analyze_ai_work")
validate_documentation_completeness = ai_work_module.validate_documentation_completeness
validate_code_consistency = ai_work_module.validate_code_consistency
validate_file_structure = ai_work_module.validate_file_structure
analyze_ai_work = ai_work_module.analyze_ai_work
execute = ai_work_module.execute


class TestAnalyzeAIWork:
    """Test AI work validation functionality."""
    
    @pytest.mark.unit
    def test_validate_documentation_completeness_basic(self, tmp_path):
        """Test basic documentation completeness validation."""
        # Create a code file
        code_file = tmp_path / "test_module.py"
        code_file.write_text("""
def test_function():
    \"\"\"Test function.\"\"\"
    pass

class TestClass:
    \"\"\"Test class.\"\"\"
    def method(self):
        pass
""")
        
        # Create a documentation file that mentions the function
        doc_file = tmp_path / "README.md"
        doc_file.write_text("""
# Test Module

This module contains `test_function` and `TestClass`.
""")
        
        # Run validation
        result = validate_documentation_completeness(
            str(doc_file),
            [str(code_file)]
        )
        
        # Verify results structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'file_exists' in result, "Result should have file_exists"
        assert result['file_exists'], "Documentation file should exist"
        assert 'coverage' in result, "Result should have coverage"
        assert 'missing_items' in result, "Result should have missing_items"
        assert 'warnings' in result, "Result should have warnings"
    
    @pytest.mark.unit
    def test_validate_documentation_completeness_missing_file(self, tmp_path):
        """Test validation when documentation file doesn't exist."""
        code_file = tmp_path / "test_module.py"
        code_file.write_text("def test(): pass")
        
        # Run validation with non-existent doc file
        result = validate_documentation_completeness(
            str(tmp_path / "nonexistent.md"),
            [str(code_file)]
        )
        
        assert result['file_exists'] is False, "File should not exist"
        assert len(result['warnings']) > 0, "Should have warnings"
        assert 'does not exist' in result['warnings'][0], "Warning should mention missing file"
    
    @pytest.mark.unit
    def test_validate_documentation_completeness_empty_files(self, tmp_path):
        """Test validation with empty files."""
        code_file = tmp_path / "empty.py"
        code_file.write_text("")
        
        doc_file = tmp_path / "empty.md"
        doc_file.write_text("")
        
        result = validate_documentation_completeness(
            str(doc_file),
            [str(code_file)]
        )
        
        assert result['file_exists'], "Documentation file should exist"
        assert isinstance(result['coverage'], (int, float)), "Coverage should be numeric"
    
    @pytest.mark.unit
    def test_validate_code_consistency_basic(self, tmp_path):
        """Test basic code consistency validation."""
        # Create a code file
        code_file = tmp_path / "test_module.py"
        code_file.write_text("""
def test_function():
    pass

class TestClass:
    def method(self):
        pass
""")
        
        # Run validation
        result = validate_code_consistency([str(code_file)])
        
        # Verify results structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'import_consistency' in result, "Result should have import_consistency"
        assert 'naming_consistency' in result, "Result should have naming_consistency"
        assert 'function_signatures' in result, "Result should have function_signatures"
        assert 'warnings' in result, "Result should have warnings"
    
    @pytest.mark.unit
    def test_validate_file_structure_basic(self, tmp_path):
        """Test basic file structure validation."""
        # Create files in appropriate locations
        test_file = tmp_path / "tests" / "test_module.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# Test file")
        
        # Run validation
        result = validate_file_structure(
            created_files=[str(test_file)],
            modified_files=[]
        )
        
        # Verify results structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'appropriate_locations' in result, "Result should have appropriate_locations"
        assert 'naming_conventions' in result, "Result should have naming_conventions"
        assert 'warnings' in result, "Result should have warnings"
    
    @pytest.mark.integration
    def test_analyze_ai_work_basic(self, demo_project_root):
        """Test basic AI work analysis."""
        # Run analysis on demo project
        result = analyze_ai_work("documentation", project_root=str(demo_project_root))
        
        # Verify results structure (returns a string report)
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should have content"
    
    @pytest.mark.unit
    def test_analyze_ai_work_empty_project(self, tmp_path):
        """Test analysis with empty project."""
        # Create minimal project structure
        (tmp_path / "README.md").write_text("# Test Project")
        
        result = analyze_ai_work("documentation", project_root=str(tmp_path))
        
        assert isinstance(result, str), "Result should be a string"
    
    @pytest.mark.unit
    def test_execute_function(self, tmp_path):
        """Test execute function."""
        # Create minimal project structure
        (tmp_path / "README.md").write_text("# Test Project")
        
        result = execute(project_root=str(tmp_path))
        
        assert isinstance(result, str), "Result should be a string"
    
    @pytest.mark.unit
    def test_validate_documentation_completeness_malformed_python(self, tmp_path):
        """Test validation with malformed Python code."""
        code_file = tmp_path / "malformed.py"
        code_file.write_text("This is not valid Python: {[}")
        
        doc_file = tmp_path / "README.md"
        doc_file.write_text("# Test")
        
        # Should handle malformed code gracefully
        result = validate_documentation_completeness(
            str(doc_file),
            [str(code_file)]
        )
        
        assert isinstance(result, dict), "Result should be a dictionary"
        # May have warnings about parsing errors
        if result.get('warnings'):
            assert any('error' in str(w).lower() or 'parse' in str(w).lower() 
                      for w in result['warnings']), \
                "Should have warnings about parsing errors"

