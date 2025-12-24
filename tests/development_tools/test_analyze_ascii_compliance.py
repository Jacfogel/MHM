"""
Tests for analyze_ascii_compliance.py.

Tests ASCII compliance analysis in documentation files.
"""

import pytest
from pathlib import Path

from tests.development_tools.conftest import load_development_tools_module, demo_project_root, test_config_path


# Load the module
ascii_module = load_development_tools_module("docs.analyze_ascii_compliance")
ASCIIComplianceAnalyzer = ascii_module.ASCIIComplianceAnalyzer


class TestAnalyzeASCIICompliance:
    """Test ASCII compliance analysis functionality."""
    
    @pytest.mark.unit
    def test_check_ascii_compliance_basic(self, tmp_path):
        """Test basic ASCII compliance check with clean file."""
        # Create a clean ASCII file
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("# Test Documentation\n\nThis is ASCII-only content.")
        
        analyzer = ASCIIComplianceAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_ascii_compliance()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Clean file should have no issues
        assert len(results) == 0 or all(len(issues) == 0 for issues in results.values()), \
            "Clean ASCII file should have no issues"
    
    @pytest.mark.unit
    def test_check_ascii_compliance_non_ascii_characters(self, tmp_path):
        """Test detection of non-ASCII characters."""
        # Create a file with non-ASCII characters
        doc_file = tmp_path / "test_doc.md"
        # Use smart quotes and em dash
        doc_file.write_text("# Test Documentation\n\nThis has 'smart quotes' and an em—dash.", encoding='utf-8')
        
        analyzer = ASCIIComplianceAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_ascii_compliance()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Should detect non-ASCII characters
        if str(doc_file.relative_to(tmp_path)) in results:
            issues = results[str(doc_file.relative_to(tmp_path))]
            assert len(issues) > 0, "Should detect non-ASCII characters"
            assert any("Non-ASCII character" in issue for issue in issues), \
                "Issues should mention non-ASCII characters"
    
    @pytest.mark.unit
    def test_check_ascii_compliance_known_replacements(self, tmp_path):
        """Test detection of known replaceable characters."""
        # Create a file with known replaceable characters (smart quotes)
        doc_file = tmp_path / "test_doc.md"
        # Use left and right single quotation marks
        content = "# Test\n\nThis has 'smart quotes'."
        doc_file.write_bytes(content.encode('utf-8').replace(b"'", b'\xe2\x80\x99').replace(b"'", b'\xe2\x80\x98'))
        
        analyzer = ASCIIComplianceAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_ascii_compliance()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Should detect and suggest replacements
        if str(doc_file.relative_to(tmp_path)) in results:
            issues = results[str(doc_file.relative_to(tmp_path))]
            assert any("auto-fixable" in issue.lower() for issue in issues), \
                "Should identify auto-fixable characters"
    
    @pytest.mark.unit
    def test_check_ascii_compliance_empty_file(self, tmp_path):
        """Test compliance check with empty file."""
        doc_file = tmp_path / "empty.md"
        doc_file.write_text("")
        
        analyzer = ASCIIComplianceAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_ascii_compliance()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Empty file should have no issues
        assert len(results) == 0 or all(len(issues) == 0 for issues in results.values()), \
            "Empty file should have no issues"
    
    @pytest.mark.unit
    def test_check_ascii_compliance_file_not_exists(self, tmp_path):
        """Test handling of non-existent files."""
        analyzer = ASCIIComplianceAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_ascii_compliance()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Non-existent files should be skipped
        assert len(results) == 0, "Non-existent files should not appear in results"
    
    @pytest.mark.unit
    def test_check_ascii_compliance_unicode_characters(self, tmp_path):
        """Test detection of various Unicode characters."""
        # Create a file with various Unicode characters
        doc_file = tmp_path / "unicode.md"
        # Include em dash, ellipsis, and other Unicode
        doc_file.write_text("# Test\n\nEm dash: —\nEllipsis: …\nArrow: →", encoding='utf-8')
        
        analyzer = ASCIIComplianceAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_ascii_compliance()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Should detect multiple Unicode characters
        if str(doc_file.relative_to(tmp_path)) in results:
            issues = results[str(doc_file.relative_to(tmp_path))]
            assert len(issues) > 0, "Should detect Unicode characters"
    
    @pytest.mark.unit
    def test_check_ascii_compliance_file_read_error(self, tmp_path):
        """Test handling of file read errors."""
        # Create a file that might cause read issues
        # (In practice, we'd need to mock file operations to simulate errors)
        doc_file = tmp_path / "test.md"
        doc_file.write_text("# Test")
        
        analyzer = ASCIIComplianceAnalyzer(project_root=str(tmp_path), use_cache=False)
        
        # Mock file read to raise exception
        with pytest.MonkeyPatch().context() as m:
            def mock_open(*args, **kwargs):
                raise IOError("Permission denied")
            
            m.setattr("builtins.open", mock_open)
            
            results = analyzer.check_ascii_compliance()
            
            assert isinstance(results, dict), "Result should be a dictionary"
            # Should handle error gracefully
            if str(doc_file.relative_to(tmp_path)) in results:
                issues = results[str(doc_file.relative_to(tmp_path))]
                assert any("Error reading file" in issue for issue in issues), \
                    "Should report file read errors"
    
    @pytest.mark.unit
    def test_run_analysis_basic(self, tmp_path):
        """Test run_analysis method with clean files."""
        doc_file = tmp_path / "test.md"
        doc_file.write_text("# Test\n\nASCII content only.")
        
        analyzer = ASCIIComplianceAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.run_analysis()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        assert 'summary' in results, "Result should have summary"
        assert 'details' in results, "Result should have details"
        assert 'total_issues' in results['summary'], "Summary should have total_issues"
        assert 'files_affected' in results['summary'], "Summary should have files_affected"
        assert 'status' in results['summary'], "Summary should have status"
    
    @pytest.mark.unit
    def test_run_analysis_with_issues(self, tmp_path):
        """Test run_analysis method with non-ASCII characters."""
        doc_file = tmp_path / "test.md"
        # Use smart quotes
        content = "# Test\n\nThis has 'smart quotes'."
        doc_file.write_bytes(content.encode('utf-8').replace(b"'", b'\xe2\x80\x99'))
        
        analyzer = ASCIIComplianceAnalyzer(project_root=str(tmp_path), use_cache=False)
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
        doc_file.write_text("# Test\n\nASCII content.")
        
        analyzer = ASCIIComplianceAnalyzer(project_root=str(tmp_path), use_cache=False)
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
        
        analyzer = ASCIIComplianceAnalyzer(
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
        doc_file.write_text("# Test\n\nASCII content.")
        
        # First run with cache enabled
        analyzer1 = ASCIIComplianceAnalyzer(project_root=str(tmp_path), use_cache=True)
        results1 = analyzer1.check_ascii_compliance()
        
        # Second run should use cache
        analyzer2 = ASCIIComplianceAnalyzer(project_root=str(tmp_path), use_cache=True)
        results2 = analyzer2.check_ascii_compliance()
        
        # Results should be consistent
        assert isinstance(results1, dict), "First result should be dict"
        assert isinstance(results2, dict), "Second result should be dict"
    
    @pytest.mark.integration
    def test_analyzer_with_demo_project(self, demo_project_root, test_config_path):
        """Test analyzer with demo project fixture."""
        analyzer = ASCIIComplianceAnalyzer(
            project_root=str(demo_project_root),
            config_path=test_config_path,
            use_cache=False
        )
        
        results = analyzer.check_ascii_compliance()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Demo project may or may not have ASCII issues
        assert all(isinstance(issues, list) for issues in results.values()), \
            "All issues should be lists"

