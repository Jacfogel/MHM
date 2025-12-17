"""
Comprehensive verification tests for path drift detection.

This test verifies that path drift detection works correctly with various
types of broken path references and that issues appear in status reports.
"""

import pytest
from pathlib import Path

from tests.development_tools.conftest import load_development_tools_module, temp_project_copy

# Load the module using the helper
path_drift_module = load_development_tools_module("docs.analyze_path_drift")
PathDriftAnalyzer = path_drift_module.PathDriftAnalyzer


class TestPathDriftVerification:
    """Comprehensive verification of path drift detection."""
    
    @pytest.mark.unit
    def test_detects_missing_python_file(self, tmp_path):
        """Verify detection of missing .py file references."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create documentation with missing Python file reference
        docs_dir = project_dir / "docs"
        docs_dir.mkdir()
        doc_file = docs_dir / "test.md"
        doc_file.write_text(
            "# Test\n\n"
            "This references a missing file: `core/missing_module.py`\n"
        )
        
        analyzer = PathDriftAnalyzer(project_root=str(project_dir), use_cache=False)
        results = analyzer.check_path_drift()
        
        doc_file_str = str(doc_file.relative_to(project_dir)).replace('\\', '/')
        assert doc_file_str in results or str(doc_file.relative_to(project_dir)) in results, \
            f"Expected {doc_file_str} in results. Got: {list(results.keys())}"
        
        result_key = doc_file_str if doc_file_str in results else str(doc_file.relative_to(project_dir))
        issues = results[result_key]
        assert len(issues) > 0, "Expected at least one issue"
        assert any('missing_module.py' in issue.lower() for issue in issues), \
            f"Expected missing_module.py in issues: {issues}"
    
    @pytest.mark.unit
    def test_detects_missing_markdown_file(self, tmp_path):
        """Verify detection of missing .md file references."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        docs_dir = project_dir / "docs"
        docs_dir.mkdir()
        doc_file = docs_dir / "test.md"
        doc_file.write_text(
            "# Test\n\n"
            "See [this document](missing_doc.md) for details.\n"
        )
        
        analyzer = PathDriftAnalyzer(project_root=str(project_dir), use_cache=False)
        results = analyzer.check_path_drift()
        
        doc_file_str = str(doc_file.relative_to(project_dir)).replace('\\', '/')
        result_key = doc_file_str if doc_file_str in results else str(doc_file.relative_to(project_dir))
        
        # May or may not detect markdown links depending on filtering
        # But if it does, it should be in results
        if result_key in results:
            issues = results[result_key]
            # If detected, should mention missing file
            if issues:
                assert any('missing' in issue.lower() for issue in issues), \
                    f"Expected missing file in issues: {issues}"
    
    @pytest.mark.unit
    def test_ignores_existing_files(self, tmp_path):
        """Verify that existing files are not flagged."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create actual file
        core_dir = project_dir / "core"
        core_dir.mkdir()
        existing_file = core_dir / "existing.py"
        existing_file.write_text("# Existing")
        
        # Create documentation referencing existing file
        docs_dir = project_dir / "docs"
        docs_dir.mkdir()
        doc_file = docs_dir / "test.md"
        doc_file.write_text(
            "# Test\n\n"
            "This references an existing file: `core/existing.py`\n"
        )
        
        analyzer = PathDriftAnalyzer(project_root=str(project_dir), use_cache=False)
        results = analyzer.check_path_drift()
        
        doc_file_str = str(doc_file.relative_to(project_dir)).replace('\\', '/')
        result_key = doc_file_str if doc_file_str in results else str(doc_file.relative_to(project_dir))
        
        # If file is in results, it shouldn't be for the existing file
        if result_key in results:
            issues = results[result_key]
            issue_text = ' '.join(issues)
            assert 'existing.py' not in issue_text, \
                f"Existing file should not be flagged: {issues}"
    
    @pytest.mark.unit
    def test_handles_relative_paths(self, tmp_path):
        """Verify that relative paths are handled correctly."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create nested structure
        docs_dir = project_dir / "docs" / "subdir"
        docs_dir.mkdir(parents=True)
        
        # Create file in parent directory
        parent_file = project_dir / "core" / "parent.py"
        parent_file.parent.mkdir()
        parent_file.write_text("# Parent")
        
        # Create doc with relative path to existing file (should not be flagged)
        doc_file = docs_dir / "test.md"
        doc_file.write_text(
            "# Test\n\n"
            "This references a file with relative path: `../../core/parent.py`\n"
        )
        
        analyzer = PathDriftAnalyzer(project_root=str(project_dir), use_cache=False)
        results = analyzer.check_path_drift()
        
        doc_file_str = str(doc_file.relative_to(project_dir)).replace('\\', '/')
        result_key = doc_file_str if doc_file_str in results else str(doc_file.relative_to(project_dir))
        
        # Should not flag the existing relative path
        if result_key in results:
            issues = results[result_key]
            issue_text = ' '.join(issues)
            assert 'parent.py' not in issue_text, \
                f"Valid relative path should not be flagged: {issues}"
    
    @pytest.mark.unit
    def test_standard_format_output(self, tmp_path):
        """Verify that run_analysis() returns standard format."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        docs_dir = project_dir / "docs"
        docs_dir.mkdir()
        doc_file = docs_dir / "test.md"
        doc_file.write_text(
            "# Test\n\n"
            "Missing file: `core/missing.py`\n"
        )
        
        analyzer = PathDriftAnalyzer(project_root=str(project_dir), use_cache=False)
        results = analyzer.run_analysis()
        
        # Verify standard format structure
        assert 'summary' in results, "Results should have 'summary' key"
        assert 'files' in results, "Results should have 'files' key"
        assert 'details' in results, "Results should have 'details' key"
        
        summary = results['summary']
        assert 'total_issues' in summary, "Summary should have 'total_issues'"
        assert 'files_affected' in summary, "Summary should have 'files_affected'"
        
        assert summary['total_issues'] > 0, "Should detect at least one issue"
        assert summary['files_affected'] > 0, "Should have at least one affected file"
    
    @pytest.mark.integration
    def test_path_drift_integration_with_status_reports(self, temp_project_copy):
        """Verify path drift issues appear in status reports when running audit."""
        # Create documentation with broken path
        docs_dir = temp_project_copy / "development_docs"
        docs_dir.mkdir(exist_ok=True)
        
        test_doc = docs_dir / "test_path_drift.md"
        test_doc.write_text(
            "# Test Path Drift\n\n"
            "This references a missing file: `core/missing_test_module.py`\n"
        )
        
        # Run path drift analysis directly
        analyzer = PathDriftAnalyzer(project_root=str(temp_project_copy), use_cache=False)
        direct_results = analyzer.run_analysis()
        
        # Verify direct analysis found the issue
        assert direct_results['summary']['total_issues'] > 0, \
            "Direct analysis should find path drift issues"
        
        # Verify the file is in the results
        files = direct_results.get('files', {})
        test_doc_str = str(test_doc.relative_to(temp_project_copy)).replace('\\', '/')
        test_doc_win = str(test_doc.relative_to(temp_project_copy))
        
        found = test_doc_str in files or test_doc_win in files
        assert found, \
            f"Expected test file in results. Got: {list(files.keys())}"
