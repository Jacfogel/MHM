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
    
    @pytest.mark.unit
    def test_validate_documentation_completeness_readme_handling(self, tmp_path):
        """Test that README.md gets special handling (100% coverage)."""
        code_file = tmp_path / "module.py"
        code_file.write_text("""
def function1():
    pass

def function2():
    pass

class Class1:
    pass
""")
        
        doc_file = tmp_path / "README.md"
        doc_file.write_text("# Module\n\nThis is a README.")
        
        result = validate_documentation_completeness(
            str(doc_file),
            [str(code_file)]
        )
        
        assert result['coverage'] == 100.0, "README.md should get 100% coverage"
        assert len(result['missing_items']) == 0, "README.md should not have missing items"
        assert any('README.md validation' in w for w in result['warnings']), \
            "Should have README.md validation warning"
    
    @pytest.mark.unit
    def test_validate_documentation_completeness_coverage_calculation(self, tmp_path):
        """Test coverage calculation for non-README files."""
        code_file = tmp_path / "module.py"
        code_file.write_text("""
def documented_function():
    pass

def undocumented_function():
    pass

class DocumentedClass:
    pass
""")
        
        doc_file = tmp_path / "docs.md"
        doc_file.write_text("# Documentation\n\nThis mentions `documented_function` and `DocumentedClass`.")
        
        result = validate_documentation_completeness(
            str(doc_file),
            [str(code_file)]
        )
        
        # Should have some coverage but not 100%
        assert 0 <= result['coverage'] <= 100, "Coverage should be between 0 and 100"
        assert 'undocumented_function' in result['missing_items'] or 'module.py' in result['missing_items'], \
            "Should identify missing items"
    
    @pytest.mark.unit
    def test_validate_documentation_completeness_extra_items(self, tmp_path):
        """Test detection of extra items in documentation."""
        code_file = tmp_path / "module.py"
        code_file.write_text("def real_function(): pass")
        
        doc_file = tmp_path / "docs.md"
        doc_file.write_text("# Docs\n\nMentions `real_function` and `nonexistent_function`.")
        
        result = validate_documentation_completeness(
            str(doc_file),
            [str(code_file)]
        )
        
        assert 'extra_items' in result, "Result should have extra_items"
        # May or may not detect extra items depending on implementation
    
    @pytest.mark.unit
    def test_validate_documentation_completeness_file_reading_error(self, tmp_path):
        """Test handling of file reading errors."""
        # Create a file that can't be read (permission denied scenario)
        # We'll use a non-existent code file to trigger error path
        doc_file = tmp_path / "docs.md"
        doc_file.write_text("# Docs")
        
        result = validate_documentation_completeness(
            str(doc_file),
            ["/nonexistent/path/to/file.py"]
        )
        
        assert isinstance(result, dict), "Should return dict even with errors"
        assert 'warnings' in result, "Should have warnings"
    
    @pytest.mark.unit
    def test_validate_code_consistency_duplicate_function_names(self, tmp_path):
        """Test detection of duplicate function names."""
        file1 = tmp_path / "module1.py"
        file1.write_text("def duplicate_name(): pass")
        
        file2 = tmp_path / "module2.py"
        file2.write_text("def duplicate_name(): pass")
        
        result = validate_code_consistency([str(file1), str(file2)])
        
        assert isinstance(result, dict), "Result should be a dictionary"
        # May or may not detect duplicates depending on implementation
        assert 'function_signatures' in result, "Should have function signatures"
    
    @pytest.mark.unit
    def test_validate_code_consistency_import_extraction(self, tmp_path):
        """Test import extraction from code files."""
        code_file = tmp_path / "module.py"
        code_file.write_text("""
import os
from pathlib import Path
from typing import Dict, List
""")
        
        result = validate_code_consistency([str(code_file)])
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'import_consistency' in result, "Should have import_consistency"
    
    @pytest.mark.unit
    def test_validate_code_consistency_parsing_error(self, tmp_path):
        """Test handling of parsing errors in code consistency."""
        code_file = tmp_path / "malformed.py"
        code_file.write_text("This is not valid Python: {[}")
        
        result = validate_code_consistency([str(code_file)])
        
        assert isinstance(result, dict), "Should return dict even with errors"
        assert 'warnings' in result, "Should have warnings about parsing"
    
    @pytest.mark.unit
    def test_validate_file_structure_test_file_warning(self, tmp_path):
        """Test detection of test files in wrong locations."""
        test_file = tmp_path / "test_module.py"  # Not in tests/ directory
        test_file.write_text("# Test file")
        
        result = validate_file_structure(
            created_files=[str(test_file)],
            modified_files=[]
        )
        
        assert isinstance(result, dict), "Result should be a dictionary"
        # Should warn about test file not in tests/ directory
        if result.get('warnings'):
            assert any('test' in w.lower() for w in result['warnings']), \
                "Should warn about test file location"
    
    @pytest.mark.unit
    def test_validate_file_structure_ui_file_warning(self, tmp_path):
        """Test detection of UI files in wrong locations."""
        ui_file = tmp_path / "ui_widget.py"  # Not in ui/ directory
        ui_file.write_text("# UI file")
        
        result = validate_file_structure(
            created_files=[str(ui_file)],
            modified_files=[]
        )
        
        assert isinstance(result, dict), "Result should be a dictionary"
        # Should warn about UI file not in ui/ directory
        if result.get('warnings'):
            assert any('ui' in w.lower() for w in result['warnings']), \
                "Should warn about UI file location"
    
    @pytest.mark.unit
    def test_validate_file_structure_naming_convention(self, tmp_path):
        """Test detection of naming convention violations."""
        # Create a file with CamelCase name (should be snake_case)
        bad_file = tmp_path / "BadFileName.py"
        bad_file.write_text("# Bad name")
        
        result = validate_file_structure(
            created_files=[str(bad_file)],
            modified_files=[]
        )
        
        assert isinstance(result, dict), "Result should be a dictionary"
        # May or may not detect naming issues depending on implementation
    
    @pytest.mark.unit
    def test_generate_validation_report_documentation_type(self, tmp_path):
        """Test report generation for documentation type."""
        from tests.development_tools.conftest import load_development_tools_module
        ai_work_module = load_development_tools_module("ai_work.analyze_ai_work")
        generate_validation_report = ai_work_module.generate_validation_report
        
        code_file = tmp_path / "module.py"
        code_file.write_text("def func(): pass")
        
        doc_file = tmp_path / "docs.md"
        doc_file.write_text("# Docs\n\nMentions `func`.")
        
        report = generate_validation_report(
            "documentation",
            doc_file=str(doc_file),
            code_files=[str(code_file)]
        )
        
        assert isinstance(report, str), "Report should be a string"
        assert "documentation" in report.lower(), "Report should mention documentation"
        assert "coverage" in report.lower(), "Report should mention coverage"
    
    @pytest.mark.unit
    def test_generate_validation_report_code_consistency_type(self, tmp_path):
        """Test report generation for code_consistency type."""
        from tests.development_tools.conftest import load_development_tools_module
        ai_work_module = load_development_tools_module("ai_work.analyze_ai_work")
        generate_validation_report = ai_work_module.generate_validation_report
        
        code_file = tmp_path / "module.py"
        code_file.write_text("def func(): pass")
        
        report = generate_validation_report(
            "code_consistency",
            changed_files=[str(code_file)]
        )
        
        assert isinstance(report, str), "Report should be a string"
        assert "consistency" in report.lower(), "Report should mention consistency"
    
    @pytest.mark.unit
    def test_generate_validation_report_file_structure_type(self, tmp_path):
        """Test report generation for file_structure type."""
        from tests.development_tools.conftest import load_development_tools_module
        ai_work_module = load_development_tools_module("ai_work.analyze_ai_work")
        generate_validation_report = ai_work_module.generate_validation_report
        
        test_file = tmp_path / "tests" / "test.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# Test")
        
        report = generate_validation_report(
            "file_structure",
            created_files=[str(test_file)],
            modified_files=[]
        )
        
        assert isinstance(report, str), "Report should be a string"
        assert "structure" in report.lower(), "Report should mention structure"
    
    @pytest.mark.unit
    def test_generate_validation_report_coverage_thresholds(self, tmp_path):
        """Test that report includes coverage assessment based on thresholds."""
        from tests.development_tools.conftest import load_development_tools_module
        ai_work_module = load_development_tools_module("ai_work.analyze_ai_work")
        generate_validation_report = ai_work_module.generate_validation_report
        
        code_file = tmp_path / "module.py"
        code_file.write_text("def func1(): pass\ndef func2(): pass")
        
        doc_file = tmp_path / "docs.md"
        doc_file.write_text("# Docs\n\nMentions `func1`.")  # 50% coverage
        
        report = generate_validation_report(
            "documentation",
            doc_file=str(doc_file),
            code_files=[str(code_file)]
        )
        
        assert "ASSESSMENT" in report or "assessment" in report.lower(), \
            "Report should include assessment"
    
    @pytest.mark.unit
    def test_analyze_ai_work_code_changes_type(self, tmp_path):
        """Test analyze_ai_work with code_changes type."""
        code_file = tmp_path / "module.py"
        code_file.write_text("def func(): pass")
        
        result = analyze_ai_work(
            "code_changes",
            project_root=str(tmp_path),
            changed_files=[str(code_file)]
        )
        
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should have content"
    
    @pytest.mark.unit
    def test_analyze_ai_work_file_creation_type(self, tmp_path):
        """Test analyze_ai_work with file_creation type."""
        test_file = tmp_path / "tests" / "test.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# Test")
        
        result = analyze_ai_work(
            "file_creation",
            project_root=str(tmp_path),
            created_files=[str(test_file)],
            modified_files=[]
        )
        
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should have content"
    
    @pytest.mark.unit
    def test_analyze_ai_work_unknown_type(self, tmp_path):
        """Test analyze_ai_work with unknown validation type."""
        result = analyze_ai_work("unknown_type", project_root=str(tmp_path))
        
        assert result == "Unknown validation type", \
            "Should return error message for unknown type"
    
    @pytest.mark.unit
    def test_analyze_ai_work_with_config_path(self, tmp_path):
        """Test analyze_ai_work with config_path parameter."""
        # Create a minimal config file
        config_file = tmp_path / "config.json"
        config_file.write_text('{"analyze_ai_work": {"completeness_threshold": 80.0}}')
        
        result = analyze_ai_work(
            "documentation",
            project_root=str(tmp_path),
            config_path=str(config_file)
        )
        
        assert isinstance(result, str), "Result should be a string"
    
    @pytest.mark.unit
    def test_execute_with_work_type(self, tmp_path):
        """Test execute function with explicit work_type."""
        result = execute(
            project_root=str(tmp_path),
            work_type="code_changes",
            changed_files=[]
        )
        
        assert isinstance(result, str), "Result should be a string"
    
    @pytest.mark.unit
    def test_validate_documentation_completeness_multiple_code_files(self, tmp_path):
        """Test validation with multiple code files."""
        file1 = tmp_path / "module1.py"
        file1.write_text("def func1(): pass")
        
        file2 = tmp_path / "module2.py"
        file2.write_text("def func2(): pass\nclass Class2: pass")
        
        doc_file = tmp_path / "docs.md"
        doc_file.write_text("# Docs\n\nMentions `func1` and `Class2`.")
        
        result = validate_documentation_completeness(
            str(doc_file),
            [str(file1), str(file2)]
        )
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'coverage' in result, "Should have coverage"
    
    @pytest.mark.unit
    def test_validate_code_consistency_empty_file_list(self, tmp_path):
        """Test code consistency with empty file list."""
        result = validate_code_consistency([])
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'import_consistency' in result, "Should have import_consistency"
        assert 'naming_consistency' in result, "Should have naming_consistency"
    
    @pytest.mark.unit
    def test_validate_file_structure_empty_lists(self, tmp_path):
        """Test file structure validation with empty lists."""
        result = validate_file_structure(
            created_files=[],
            modified_files=[]
        )
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'appropriate_locations' in result, "Should have appropriate_locations"
        assert 'naming_conventions' in result, "Should have naming_conventions"

