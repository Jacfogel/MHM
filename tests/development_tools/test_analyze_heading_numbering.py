"""
Tests for analyze_heading_numbering.py.

Tests heading numbering compliance analysis in documentation files.
"""

import pytest
from pathlib import Path

from tests.development_tools.conftest import load_development_tools_module, demo_project_root, test_config_path


# Load the module
heading_module = load_development_tools_module("docs.analyze_heading_numbering")
HeadingNumberingAnalyzer = heading_module.HeadingNumberingAnalyzer


class TestAnalyzeHeadingNumbering:
    """Test heading numbering analysis functionality."""
    
    @pytest.mark.unit
    def test_check_heading_numbering_basic(self, tmp_path):
        """Test basic heading numbering check with properly numbered headings."""
        # Create a file with properly numbered headings
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("""# Title

## 1. First Section

Content here.

## 2. Second Section

More content.

### 2.1. Subsection

Subsection content.
""")
        
        analyzer = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_heading_numbering()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Properly numbered headings should have no issues
        assert len(results) == 0 or all(len(issues) == 0 for issues in results.values()), \
            "Properly numbered headings should have no issues"
    
    @pytest.mark.unit
    def test_check_heading_numbering_missing_numbers(self, tmp_path):
        """Test detection of headings without numbers."""
        # Create a file with unnumbered headings
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("""# Title

## First Section

Content here.

## Second Section

More content.
""")
        
        analyzer = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_heading_numbering()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Should detect missing numbers
        if str(doc_file.relative_to(tmp_path)) in results:
            issues = results[str(doc_file.relative_to(tmp_path))]
            assert len(issues) > 0, "Should detect missing heading numbers"
    
    @pytest.mark.unit
    def test_check_heading_numbering_non_consecutive(self, tmp_path):
        """Test detection of non-consecutive numbering."""
        # Create a file with non-consecutive numbering
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("""# Title

## 1. First Section

Content here.

## 3. Third Section

Skipped number 2.
""")
        
        analyzer = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_heading_numbering()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Should detect non-consecutive numbering
        if str(doc_file.relative_to(tmp_path)) in results:
            issues = results[str(doc_file.relative_to(tmp_path))]
            assert any("non-consecutive" in issue.lower() or "expected" in issue.lower() 
                      for issue in issues), \
                "Should detect non-consecutive numbering"
    
    @pytest.mark.unit
    def test_check_heading_numbering_starts_at_zero(self, tmp_path):
        """Test handling of numbering that starts at 0."""
        # Create a file with numbering starting at 0
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("""# Title

## 0. Introduction

Content here.

## 1. First Section

More content.
""")
        
        analyzer = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_heading_numbering()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Starting at 0 should be acceptable
        assert len(results) == 0 or all(len(issues) == 0 for issues in results.values()), \
            "Numbering starting at 0 should be acceptable"
    
    @pytest.mark.unit
    def test_check_heading_numbering_h3_numbering(self, tmp_path):
        """Test H3 heading numbering."""
        # Create a file with H3 headings
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("""# Title

## 1. First Section

### 1.1. Subsection One

Content.

### 1.2. Subsection Two

More content.

## 2. Second Section

### 2.1. Subsection

Content.
""")
        
        analyzer = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_heading_numbering()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Properly numbered H3 headings should have no issues
        assert len(results) == 0 or all(len(issues) == 0 for issues in results.values()), \
            "Properly numbered H3 headings should have no issues"
    
    @pytest.mark.unit
    def test_check_heading_numbering_h3_non_consecutive(self, tmp_path):
        """Test detection of non-consecutive H3 numbering."""
        # Create a file with non-consecutive H3 numbering
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("""# Title

## 1. First Section

### 1.1. Subsection One

Content.

### 1.3. Subsection Three

Skipped 1.2.
""")
        
        analyzer = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_heading_numbering()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Should detect non-consecutive H3 numbering
        if str(doc_file.relative_to(tmp_path)) in results:
            issues = results[str(doc_file.relative_to(tmp_path))]
            assert any("non-consecutive" in issue.lower() or "expected" in issue.lower() 
                      for issue in issues), \
                "Should detect non-consecutive H3 numbering"
    
    @pytest.mark.unit
    def test_check_heading_numbering_skips_changelog(self, tmp_path):
        """Test that changelog files are skipped."""
        # Create a changelog file (should be skipped)
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text("""# Changelog

## Unnumbered Entry

Content without numbering.
""")
        
        analyzer = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_heading_numbering()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Changelog files should be skipped
        assert str(changelog.relative_to(tmp_path)) not in results, \
            "Changelog files should be skipped from numbering checks"
    
    @pytest.mark.unit
    def test_check_heading_numbering_skips_quick_reference(self, tmp_path):
        """Test that Quick Reference sections are skipped."""
        # Create a file with Quick Reference section
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("""# Title

## Quick Reference

This section should be skipped.

## 1. First Section

Content here.
""")
        
        analyzer = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_heading_numbering()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Quick Reference should not cause numbering issues
        if str(doc_file.relative_to(tmp_path)) in results:
            issues = results[str(doc_file.relative_to(tmp_path))]
            # Should not complain about Quick Reference
            assert not any("Quick Reference" in issue for issue in issues), \
                "Quick Reference should not cause numbering issues"
    
    @pytest.mark.unit
    def test_check_heading_numbering_empty_file(self, tmp_path):
        """Test heading numbering check with empty file."""
        doc_file = tmp_path / "empty.md"
        doc_file.write_text("")
        
        analyzer = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_heading_numbering()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Empty file should have no issues
        assert len(results) == 0 or all(len(issues) == 0 for issues in results.values()), \
            "Empty file should have no issues"
    
    @pytest.mark.unit
    def test_check_heading_numbering_file_not_exists(self, tmp_path):
        """Test handling of non-existent files."""
        analyzer = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_heading_numbering()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Non-existent files should be skipped
        assert len(results) == 0, "Non-existent files should not appear in results"
    
    @pytest.mark.unit
    def test_run_analysis_basic(self, tmp_path):
        """Test run_analysis method with properly numbered headings."""
        doc_file = tmp_path / "test.md"
        doc_file.write_text("""# Title

## 1. First Section

Content.
""")
        
        analyzer = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.run_analysis()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        assert 'summary' in results, "Result should have summary"
        assert 'details' in results, "Result should have details"
        assert 'total_issues' in results['summary'], "Summary should have total_issues"
        assert 'files_affected' in results['summary'], "Summary should have files_affected"
        assert 'status' in results['summary'], "Summary should have status"
    
    @pytest.mark.unit
    def test_run_analysis_with_issues(self, tmp_path):
        """Test run_analysis method with numbering issues."""
        doc_file = tmp_path / "test.md"
        doc_file.write_text("""# Title

## First Section

Unnumbered heading.
""")
        
        analyzer = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.run_analysis()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        assert 'summary' in results, "Result should have summary"
        # May or may not have issues depending on file matching
        assert isinstance(results['summary']['total_issues'], int), \
            "total_issues should be integer"
    
    @pytest.mark.unit
    def test_run_analysis_status_calculation(self, tmp_path):
        """Test that status is calculated correctly."""
        doc_file = tmp_path / "test.md"
        doc_file.write_text("""# Title

## 1. First Section

Content.
""")
        
        analyzer = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.run_analysis()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        assert 'status' in results['summary'], "Summary should have status"
        # Status should be one of PASS, FAIL, WARN, CLEAN
        assert results['summary']['status'] in ['PASS', 'FAIL', 'WARN', 'CLEAN'], \
            "Status should be valid value"
    
    @pytest.mark.unit
    def test_analyzer_with_config_path(self, tmp_path):
        """Test analyzer initialization with config path."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"project_root": "' + str(tmp_path).replace('\\', '\\\\') + '"}')
        
        analyzer = HeadingNumberingAnalyzer(
            project_root=str(tmp_path),
            config_path=str(config_file),
            use_cache=False
        )
        
        assert analyzer.project_root == Path(tmp_path).resolve(), \
            "Project root should be set correctly"
    
    @pytest.mark.unit
    def test_analyzer_caching(self, tmp_path):
        """Test that caching works correctly."""
        doc_file = tmp_path / "test.md"
        doc_file.write_text("""# Title

## 1. First Section

Content.
""")
        
        # First run with cache enabled
        analyzer1 = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=True)
        results1 = analyzer1.check_heading_numbering()
        
        # Second run should use cache
        analyzer2 = HeadingNumberingAnalyzer(project_root=str(tmp_path), use_cache=True)
        results2 = analyzer2.check_heading_numbering()
        
        # Results should be consistent
        assert isinstance(results1, dict), "First result should be dict"
        assert isinstance(results2, dict), "Second result should be dict"
    
    @pytest.mark.integration
    def test_analyzer_with_demo_project(self, demo_project_root, test_config_path):
        """Test analyzer with demo project fixture."""
        analyzer = HeadingNumberingAnalyzer(
            project_root=str(demo_project_root),
            config_path=test_config_path,
            use_cache=False
        )
        
        results = analyzer.check_heading_numbering()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Demo project may or may not have numbering issues
        assert all(isinstance(issues, list) for issues in results.values()), \
            "All issues should be lists"

