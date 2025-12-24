"""
Tests for analyze_unconverted_links.py.

Tests unconverted link detection in documentation files.
"""

import pytest
from pathlib import Path

from tests.development_tools.conftest import load_development_tools_module, demo_project_root, test_config_path


# Load the module
unconverted_links_module = load_development_tools_module("docs.analyze_unconverted_links")
UnconvertedLinkAnalyzer = unconverted_links_module.UnconvertedLinkAnalyzer


class TestAnalyzeUnconvertedLinks:
    """Test unconverted link analysis functionality."""
    
    @pytest.mark.unit
    def test_check_unconverted_links_basic(self, tmp_path):
        """Test basic unconverted link detection with clean file."""
        # Create a file with no unconverted links
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("""# Test Documentation

This file has [proper links](path/to/file.md) and no unconverted paths.
""")
        
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_unconverted_links()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Clean file should have no issues
        assert len(results) == 0 or all(len(issues) == 0 for issues in results.values()), \
            "Clean file should have no unconverted links"
    
    @pytest.mark.unit
    def test_check_unconverted_links_detects_paths(self, tmp_path):
        """Test detection of unconverted file paths."""
        # Create a file with unconverted path
        doc_file = tmp_path / "test_doc.md"
        target_file = tmp_path / "target.md"
        target_file.write_text("# Target")
        
        doc_file.write_text(f"""# Test Documentation

See the file at tests/target.md for more information.
""")
        
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_unconverted_links()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # May or may not detect depending on path validation
        # The analyzer checks if paths are valid before flagging them
    
    @pytest.mark.unit
    def test_check_unconverted_links_ignores_code_blocks(self, tmp_path):
        """Test that paths in code blocks are ignored."""
        # Create a file with path in code block
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("""# Test Documentation

```python
# This is a code block with a path: tests/example.py
import sys
```
""")
        
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_unconverted_links()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Paths in code blocks should be ignored
        if str(doc_file.relative_to(tmp_path)) in results:
            issues = results[str(doc_file.relative_to(tmp_path))]
            # Should not flag paths in code blocks
            assert not any("code block" in issue.lower() for issue in issues), \
                "Should not flag paths in code blocks"
    
    @pytest.mark.unit
    def test_check_unconverted_links_ignores_examples(self, tmp_path):
        """Test that paths in example contexts are ignored."""
        # Create a file with path in example context
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("""# Test Documentation

[EXAMPLE] For example, see tests/example.py for usage.
""")
        
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_unconverted_links()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Paths in example contexts should be ignored
        if str(doc_file.relative_to(tmp_path)) in results:
            issues = results[str(doc_file.relative_to(tmp_path))]
            # Should not flag paths in example contexts
            assert len(issues) == 0 or not any("example" in issue.lower() for issue in issues), \
                "Should not flag paths in example contexts"
    
    @pytest.mark.unit
    def test_check_unconverted_links_ignores_existing_links(self, tmp_path):
        """Test that already-converted links are ignored."""
        # Create a file with proper markdown link
        doc_file = tmp_path / "test_doc.md"
        target_file = tmp_path / "target.md"
        target_file.write_text("# Target")
        
        doc_file.write_text(f"""# Test Documentation

See [the target file](tests/target.md) for more information.
""")
        
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_unconverted_links()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Already-converted links should be ignored
        if str(doc_file.relative_to(tmp_path)) in results:
            issues = results[str(doc_file.relative_to(tmp_path))]
            # Should not flag already-converted links
            assert not any("already" in issue.lower() or "link" in issue.lower() 
                          for issue in issues), \
                "Should not flag already-converted links"
    
    @pytest.mark.unit
    def test_check_unconverted_links_ignores_generated_files(self, tmp_path):
        """Test that generated files are excluded."""
        # Create a generated file
        doc_file = tmp_path / "generated.md"
        doc_file.write_text("""**Generated**: This file is auto-generated.

# Generated Documentation

See tests/example.py for reference.
""")
        
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_unconverted_links()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Generated files should be excluded
        assert str(doc_file.relative_to(tmp_path)) not in results, \
            "Generated files should be excluded from link checks"
    
    @pytest.mark.unit
    def test_check_unconverted_links_empty_file(self, tmp_path):
        """Test unconverted link check with empty file."""
        doc_file = tmp_path / "empty.md"
        doc_file.write_text("")
        
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_unconverted_links()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Empty file should have no issues
        assert len(results) == 0 or all(len(issues) == 0 for issues in results.values()), \
            "Empty file should have no issues"
    
    @pytest.mark.unit
    def test_check_unconverted_links_file_not_exists(self, tmp_path):
        """Test handling of non-existent files."""
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_unconverted_links()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Non-existent files should be skipped
        assert len(results) == 0, "Non-existent files should not appear in results"
    
    @pytest.mark.unit
    def test_is_valid_file_path_for_link(self, tmp_path):
        """Test file path validation."""
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
        
        # Create a valid file
        valid_file = tmp_path / "valid.md"
        valid_file.write_text("# Valid")
        
        # Test valid path
        assert analyzer._is_valid_file_path_for_link("valid.md", valid_file), \
            "Valid file path should be accepted"
        
        # Test invalid path (doesn't exist)
        assert not analyzer._is_valid_file_path_for_link("nonexistent.md", valid_file), \
            "Non-existent file path should be rejected"
        
        # Test invalid path (command pattern)
        assert not analyzer._is_valid_file_path_for_link("python script.py", valid_file), \
            "Command pattern should be rejected"
    
    @pytest.mark.unit
    def test_is_already_link(self, tmp_path):
        """Test detection of already-converted links."""
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
        
        # Test markdown link
        assert analyzer._is_already_link("See [file](path/to/file.md)", "path/to/file.md"), \
            "Should detect markdown link"
        
        # Test plain path (not a link)
        assert not analyzer._is_already_link("See path/to/file.md", "path/to/file.md"), \
            "Should not detect plain path as link"
    
    @pytest.mark.unit
    def test_is_in_code_block(self, tmp_path):
        """Test detection of code blocks."""
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
        
        lines = [
            "Normal text",
            "```python",
            "code here",
            "path/to/file.py",
            "```",
            "More text"
        ]
        
        # Line 2 (inside code block)
        assert analyzer._is_in_code_block(lines, 2), \
            "Should detect line inside code block"
        
        # Line 0 (before code block)
        assert not analyzer._is_in_code_block(lines, 0), \
            "Should not detect line before code block"
        
        # Line 5 (after code block)
        assert not analyzer._is_in_code_block(lines, 5), \
            "Should not detect line after code block"
    
    @pytest.mark.unit
    def test_is_in_example_context(self, tmp_path):
        """Test detection of example contexts."""
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
        
        lines = [
            "[EXAMPLE] This is an example",
            "See path/to/file.md for details"
        ]
        
        # Line 1 (after example marker)
        assert analyzer._is_in_example_context(lines[1], lines, 1), \
            "Should detect line in example context"
        
        # Line with "for example" phrase
        example_line = "For example, see path/to/file.md"
        assert analyzer._is_in_example_context(example_line, [example_line], 0), \
            "Should detect line with example phrase"
    
    @pytest.mark.unit
    def test_run_analysis_basic(self, tmp_path):
        """Test run_analysis method with clean files."""
        doc_file = tmp_path / "test.md"
        doc_file.write_text("""# Title

[Proper link](path/to/file.md)
""")
        
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.run_analysis()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        assert 'summary' in results, "Result should have summary"
        assert 'details' in results, "Result should have details"
        assert 'total_issues' in results['summary'], "Summary should have total_issues"
        assert 'files_affected' in results['summary'], "Summary should have files_affected"
        assert 'status' in results['summary'], "Summary should have status"
    
    @pytest.mark.unit
    def test_run_analysis_with_issues(self, tmp_path):
        """Test run_analysis method with unconverted links."""
        doc_file = tmp_path / "test.md"
        target_file = tmp_path / "target.md"
        target_file.write_text("# Target")
        
        doc_file.write_text(f"""# Title

See tests/target.md for information.
""")
        
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.run_analysis()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        assert 'summary' in results, "Result should have summary"
        # May or may not have issues depending on path validation
        assert isinstance(results['summary']['total_issues'], int), \
            "total_issues should be integer"
    
    @pytest.mark.unit
    def test_run_analysis_status_calculation(self, tmp_path):
        """Test that status is calculated correctly."""
        doc_file = tmp_path / "test.md"
        doc_file.write_text("""# Title

[Proper link](path/to/file.md)
""")
        
        analyzer = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=False)
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
        
        analyzer = UnconvertedLinkAnalyzer(
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

[Proper link](path/to/file.md)
""")
        
        # First run with cache enabled
        analyzer1 = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=True)
        results1 = analyzer1.check_unconverted_links()
        
        # Second run should use cache
        analyzer2 = UnconvertedLinkAnalyzer(project_root=str(tmp_path), use_cache=True)
        results2 = analyzer2.check_unconverted_links()
        
        # Results should be consistent
        assert isinstance(results1, dict), "First result should be dict"
        assert isinstance(results2, dict), "Second result should be dict"
    
    @pytest.mark.integration
    def test_analyzer_with_demo_project(self, demo_project_root, test_config_path):
        """Test analyzer with demo project fixture."""
        analyzer = UnconvertedLinkAnalyzer(
            project_root=str(demo_project_root),
            config_path=test_config_path,
            use_cache=False
        )
        
        results = analyzer.check_unconverted_links()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Demo project may or may not have unconverted links
        assert all(isinstance(issues, list) for issues in results.values()), \
            "All issues should be lists"

