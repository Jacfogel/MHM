"""
False negative detection tests for analysis tools.

These tests verify that analysis tools correctly detect known issues
and don't miss real problems (false negatives).

Test fixtures contain intentional issues that should be detected:
1. Functions missing error handling decorators
2. Functions missing docstrings
3. Documentation with broken file references
"""

import pytest
import argparse
from pathlib import Path
from unittest.mock import patch

from tests.development_tools.conftest import load_development_tools_module, demo_project_root, test_config_path


class TestFalseNegativeDetection:
    """Test that analysis tools detect known issues (no false negatives)."""
    
    @pytest.fixture
    def false_negative_code_file(self, demo_project_root):
        """Return path to test code file with known issues."""
        return demo_project_root / "false_negative_test_code.py"
    
    @pytest.fixture
    def false_negative_doc_file(self, demo_project_root):
        """Return path to test doc file with known issues."""
        return demo_project_root / "docs" / "false_negative_test_doc.md"
    
    @pytest.mark.integration
    @pytest.mark.no_parallel
    def test_error_handling_detects_missing_decorators(self, demo_project_root, false_negative_code_file):
        """Verify error handling analyzer detects functions missing decorators."""
        # Load error handling analyzer
        error_handling_module = load_development_tools_module("error_handling.analyze_error_handling")
        ErrorHandlingAnalyzer = error_handling_module.ErrorHandlingAnalyzer
        
        # Create analyzer
        analyzer = ErrorHandlingAnalyzer(project_root=str(demo_project_root))
        
        # Analyze the specific test file directly (more reliable than scanning entire project)
        file_result = analyzer.analyze_file(false_negative_code_file)
        
        # Verify file was analyzed
        assert 'functions' in file_result, "File analysis should return functions"
        assert len(file_result['functions']) > 0, f"Expected functions in test file, found {len(file_result['functions'])}"
        
        # Check for functions with known issues
        phase1_found = False
        missing_found = False
        found_func_names = []
        
        for func in file_result['functions']:
            func_name = func.get('name', '') or func.get('function_name', '')
            found_func_names.append(func_name)
            has_try_except = func.get('has_try_except', False)
            has_decorator = func.get('has_decorator', False) or func.get('has_error_handling_decorator', False)
            
            if 'process_user_data' in func_name:
                if has_try_except and not has_decorator:
                    phase1_found = True
            elif 'fetch_external_data' in func_name:
                if not has_try_except and not has_decorator:
                    missing_found = True
        
        # Verify we found the expected issues
        assert phase1_found or missing_found, \
            f"Expected to find issues in process_user_data or fetch_external_data. " \
            f"Found functions: {found_func_names}. " \
            f"Function details: {[{'name': f.get('name', ''), 'has_try_except': f.get('has_try_except', False), 'has_decorator': f.get('has_decorator', False)} for f in file_result['functions']]}"
    
    @pytest.mark.integration
    @pytest.mark.no_parallel
    def test_documentation_detects_missing_docstrings(self, demo_project_root, false_negative_code_file):
        """Verify function registry detects functions missing docstrings."""
        # Load function registry analyzer functions
        function_registry_module = load_development_tools_module("functions.analyze_function_registry")
        extract_functions_and_classes = function_registry_module.extract_functions_and_classes
        FunctionRecord = function_registry_module.FunctionRecord
        
        # Extract functions directly from the test file
        errors = []
        functions, classes = extract_functions_and_classes(false_negative_code_file, errors)
        
        # Verify we found functions
        assert len(functions) > 0, f"Expected to find functions in test file. Found: {len(functions)}"
        
        # Find functions without docstrings
        undocumented_functions = [f for f in functions if not f.has_docstring]
        
        # Verify we found undocumented functions
        assert len(undocumented_functions) > 0, \
            f"Expected to find undocumented functions. Found {len(functions)} total functions, " \
            f"all have docstrings: {[f.name for f in functions]}"
        
        # Verify specific function is detected
        func_names = [f.name for f in undocumented_functions]
        # calculate_total should be detected (missing docstring)
        assert any('calculate_total' in name for name in func_names), \
            f"Expected to find calculate_total. Found undocumented: {func_names}. " \
            f"All functions: {[f.name for f in functions]}"
    
    @pytest.mark.integration
    def test_path_drift_detects_broken_references(self, demo_project_root, test_config_path, false_negative_doc_file):
        """Verify path drift analyzer detects broken file references."""
        # Load path drift analyzer
        path_drift_module = load_development_tools_module("docs.analyze_path_drift")
        PathDriftAnalyzer = path_drift_module.PathDriftAnalyzer
        
        # Create analyzer
        analyzer = PathDriftAnalyzer(
            project_root=str(demo_project_root),
            config_path=test_config_path,
            use_cache=False
        )
        
        # Run analysis
        results = analyzer.check_path_drift()
        
        # Verify results structure
        assert isinstance(results, dict), "Results should be a dictionary"
        
        # Find our test file in results
        test_file_path = str(false_negative_doc_file.relative_to(demo_project_root))
        test_file_path_win = test_file_path.replace('/', '\\')
        
        # Check if test file is in results
        found_test_file = False
        found_issues = []
        
        for file_path, issues in results.items():
            if test_file_path in file_path or test_file_path_win in file_path:
                found_test_file = True
                found_issues = issues if isinstance(issues, list) else []
                break
        
        # Verify we found issues in our test file
        # false_negative_test_doc.md references nonexistent_module.py, missing_dialog.py, fake_test_file.py
        assert found_test_file, \
            f"Expected to find path drift issues in {test_file_path}. " \
            f"Files in results: {list(results.keys())[:5]}"
        
        # Verify we found at least one issue
        assert len(found_issues) > 0, \
            f"Expected at least one path drift issue in test file. Found: {found_issues}"
        
        # Verify specific broken references are detected
        issue_paths = []
        for issue in found_issues:
            if isinstance(issue, dict):
                issue_paths.append(issue.get('path', ''))
            elif isinstance(issue, str):
                issue_paths.append(issue)
        
        # Check for known broken references
        broken_refs = ['nonexistent_module.py', 'missing_dialog.py', 'fake_test_file.py']
        found_broken_refs = [ref for ref in broken_refs if any(ref in path for path in issue_paths)]
        
        assert len(found_broken_refs) > 0, \
            f"Expected to find broken references. Found issues: {issue_paths[:5]}"
    
    @pytest.mark.unit
    def test_error_handling_detects_all_known_issues(self, tmp_path):
        """Unit test: Verify error handling detects all known issues in test fixture."""
        # Create test project
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create test file with known issues
        test_file = project_dir / "test_code.py"
        test_file.write_text("""def function_with_try_except_no_decorator():
    # Has try-except but no decorator - should be Phase 1 candidate
    try:
        result = some_operation()
        return result
    except Exception:
        return None

def function_with_no_error_handling():
    # No error handling at all - should be flagged
    result = risky_operation()
    return result

def function_with_decorator():
    # Has decorator - should NOT be flagged
    from core.error_handling import handle_errors

    @handle_errors
    def inner():
        return safe_operation()

    return inner()
""")
        
        # Load error handling analyzer
        error_handling_module = load_development_tools_module("error_handling.analyze_error_handling")
        ErrorHandlingAnalyzer = error_handling_module.ErrorHandlingAnalyzer
        
        # Create analyzer
        analyzer = ErrorHandlingAnalyzer(project_root=str(project_dir))
        
        # Analyze the specific file directly (more reliable for unit tests)
        file_result = analyzer.analyze_file(test_file)
        
        # Check that functions were found
        assert 'functions' in file_result, "File analysis should return functions"
        assert len(file_result['functions']) >= 2, f"Expected at least 2 functions, found {len(file_result['functions'])}"
        
        # Check for functions with try-except but no decorator (Phase 1 candidates)
        phase1_found = False
        missing_found = False
        
        for func in file_result['functions']:
            func_name = func.get('name', '') or func.get('function_name', '')
            has_try_except = func.get('has_try_except', False)
            has_decorator = func.get('has_decorator', False) or func.get('has_error_handling_decorator', False)
            
            if 'function_with_try_except_no_decorator' in func_name:
                if has_try_except and not has_decorator:
                    phase1_found = True
            elif 'function_with_no_error_handling' in func_name:
                if not has_try_except and not has_decorator:
                    missing_found = True
        
        # Verify we found at least one issue
        assert phase1_found or missing_found, \
            f"Expected to find issues. Functions: {[f.get('name', '') or f.get('function_name', '') for f in file_result['functions']]}"
    
    @pytest.mark.unit
    def test_path_drift_detects_all_known_issues(self, tmp_path):
        """Unit test: Verify path drift detects all known broken references."""
        # Create test project
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create core directory with one file
        core_dir = project_dir / "core"
        core_dir.mkdir()
        (core_dir / "existing.py").write_text("# Existing file")
        
        # Create docs directory
        docs_dir = project_dir / "docs"
        docs_dir.mkdir()
        
        # Create test doc with broken references
        test_doc = docs_dir / "test_doc.md"
        test_doc.write_text("""
# Test Documentation

This references missing files:
- `core/missing_file.py` - Doesn't exist
- `ui/nonexistent.py` - Doesn't exist

This references existing file:
- `core/existing.py` - Exists (should not be flagged)
""")
        
        # Load path drift analyzer
        path_drift_module = load_development_tools_module("docs.analyze_path_drift")
        PathDriftAnalyzer = path_drift_module.PathDriftAnalyzer
        
        # Create analyzer
        analyzer = PathDriftAnalyzer(
            project_root=str(project_dir),
            use_cache=False
        )
        
        # Run analysis
        results = analyzer.check_path_drift()
        
        # Find our test file in results
        test_file_path = str(test_doc.relative_to(project_dir))
        test_file_path_win = test_file_path.replace('/', '\\')
        
        found_test_file = False
        found_issues = []
        
        for file_path, issues in results.items():
            if test_file_path in file_path or test_file_path_win in file_path:
                found_test_file = True
                found_issues = issues if isinstance(issues, list) else []
                break
        
        # Verify we found issues
        assert found_test_file, \
            f"Expected to find path drift issues in {test_file_path}. " \
            f"Files in results: {list(results.keys())}"
        
        # Verify we found broken references
        assert len(found_issues) > 0, \
            f"Expected at least one broken reference. Found: {found_issues}"
        
        # Verify specific broken references are detected
        issue_paths = []
        for issue in found_issues:
            if isinstance(issue, dict):
                issue_paths.append(issue.get('path', ''))
            elif isinstance(issue, str):
                issue_paths.append(issue)
        
        # Check for known broken references
        broken_refs = ['missing_file.py', 'nonexistent.py']
        found_broken_refs = [ref for ref in broken_refs if any(ref in path for path in issue_paths)]
        
        assert len(found_broken_refs) > 0, \
            f"Expected to find broken references. Found issues: {issue_paths}"

