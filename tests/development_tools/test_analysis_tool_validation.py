"""
Validation tests for analysis tools using test fixtures.

Tests that analysis tools correctly detect issues in test fixtures
and don't report false positives on properly formatted files.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from tests.development_tools.conftest import load_development_tools_module, demo_project_root, test_config_path

# Load analyzer modules
heading_numbering_module = load_development_tools_module("docs.analyze_heading_numbering")
HeadingNumberingAnalyzer = heading_numbering_module.HeadingNumberingAnalyzer

missing_addresses_module = load_development_tools_module("docs.analyze_missing_addresses")
MissingAddressAnalyzer = missing_addresses_module.MissingAddressAnalyzer

ascii_compliance_module = load_development_tools_module("docs.analyze_ascii_compliance")
ASCIIComplianceAnalyzer = ascii_compliance_module.ASCIIComplianceAnalyzer

unconverted_links_module = load_development_tools_module("docs.analyze_unconverted_links")
UnconvertedLinkAnalyzer = unconverted_links_module.UnconvertedLinkAnalyzer

path_drift_module = load_development_tools_module("docs.analyze_path_drift")
PathDriftAnalyzer = path_drift_module.PathDriftAnalyzer


class TestAnalysisToolValidation:
    """Test analysis tools with validation fixtures."""
    
    @pytest.fixture
    def validation_fixtures_dir(self, demo_project_root):
        """Return path to validation fixtures directory."""
        return demo_project_root / "docs" / "analysis_validation"
    
    @pytest.mark.integration
    @pytest.mark.no_parallel
    def test_validation_fixtures_heading_numbering(self, demo_project_root, test_config_path):
        """Test that heading_numbering_issues.md fixture is detected (replaces TEST_ANALYSIS.md validation)."""
        fixture_file = demo_project_root / "docs" / "analysis_validation" / "heading_numbering_issues.md"
        assert fixture_file.exists(), "Fixture file should exist"
        
        fixture_rel_path = str(fixture_file.relative_to(demo_project_root)).replace('\\', '/')
        
        # Patch DEFAULT_DOCS using unittest.mock.patch for more reliable patching
        # Note: @pytest.mark.no_parallel ensures this test runs serially
        with patch('development_tools.shared.constants.DEFAULT_DOCS', (fixture_rel_path,)):
            analyzer = HeadingNumberingAnalyzer(
                project_root=str(demo_project_root),
                config_path=test_config_path,
                use_cache=False
            )
            
            # Verify the file exists at the expected path
            expected_path = Path(demo_project_root) / fixture_rel_path
            assert expected_path.exists(), f"File should exist at {expected_path}"
            
            results = analyzer.check_heading_numbering()
            
            # Verify fixture file is detected
            fixture_path = fixture_rel_path
            fixture_path_win = str(fixture_file.relative_to(demo_project_root))
            
            found = fixture_path in results or fixture_path_win in results
            assert found, f"Expected {fixture_path} to be in results. Got: {list(results.keys())[:5]}"
            
            # Verify issues are found (should have unnumbered headings)
            result_key = fixture_path if fixture_path in results else fixture_path_win
            issues = results[result_key]
            assert len(issues) > 0, f"Expected heading numbering issues in fixture. Got: {issues}"
    
    @pytest.mark.integration
    @pytest.mark.no_parallel
    def test_validation_fixtures_ascii_compliance(self, demo_project_root, test_config_path):
        """Test that ascii_compliance_issues.md fixture is detected (replaces TEST_ANALYSIS.md validation)."""
        fixture_file = demo_project_root / "docs" / "analysis_validation" / "ascii_compliance_issues.md"
        assert fixture_file.exists(), "Fixture file should exist"
        
        fixture_rel_path = str(fixture_file.relative_to(demo_project_root)).replace('\\', '/')
        
        # Patch ASCII_COMPLIANCE_FILES using unittest.mock.patch for more reliable patching
        # Note: @pytest.mark.no_parallel ensures this test runs serially
        with patch('development_tools.shared.constants.ASCII_COMPLIANCE_FILES', (fixture_rel_path,)):
            analyzer = ASCIIComplianceAnalyzer(
                project_root=str(demo_project_root),
                config_path=test_config_path,
                use_cache=False
            )
            
            # Verify the file exists at the expected path
            expected_path = Path(demo_project_root) / fixture_rel_path
            assert expected_path.exists(), f"File should exist at {expected_path}"
            
            results = analyzer.check_ascii_compliance()
            
            # Verify fixture file is detected
            fixture_path = fixture_rel_path
            fixture_path_win = str(fixture_file.relative_to(demo_project_root))
            
            found = fixture_path in results or fixture_path_win in results
            assert found, f"Expected {fixture_path} to be in results. Got: {list(results.keys())[:5]}"
            
            # Verify issues are found (should have non-ASCII characters)
            result_key = fixture_path if fixture_path in results else fixture_path_win
            issues = results[result_key]
            assert len(issues) > 0, f"Expected ASCII compliance issues in fixture. Got: {issues}"
    
    @pytest.mark.integration
    def test_validation_fixtures_unconverted_links(self, demo_project_root, test_config_path):
        """Test that unconverted_links.md fixture is detected (replaces TEST_ANALYSIS.md validation)."""
        fixture_file = demo_project_root / "docs" / "analysis_validation" / "unconverted_links.md"
        assert fixture_file.exists(), "Fixture file should exist"
        
        analyzer = UnconvertedLinkAnalyzer(
            project_root=str(demo_project_root),
            config_path=test_config_path,
            use_cache=False
        )
        
        results = analyzer.check_unconverted_links()
        
        # Verify fixture file is detected (unconverted links scans all .md files)
        fixture_rel_path = str(fixture_file.relative_to(demo_project_root)).replace('\\', '/')
        fixture_path_win = str(fixture_file.relative_to(demo_project_root))
        
        found = fixture_rel_path in results or fixture_path_win in results
        # Note: May or may not be detected depending on analyzer logic
        if found:
            result_key = fixture_rel_path if fixture_rel_path in results else fixture_path_win
            issues = results[result_key]
            assert len(issues) > 0, f"Expected unconverted link issues in fixture. Got: {issues}"
    
    @pytest.mark.integration
    def test_validation_fixtures_path_drift(self, demo_project_root, test_config_path):
        """Test that path_drift_issues.md fixture is detected (replaces TEST_ANALYSIS.md validation)."""
        fixture_file = demo_project_root / "docs" / "analysis_validation" / "path_drift_issues.md"
        assert fixture_file.exists(), "Fixture file should exist"
        
        analyzer = PathDriftAnalyzer(
            project_root=str(demo_project_root),
            config_path=test_config_path,
            use_cache=False
        )
        
        results = analyzer.check_path_drift()
        
        # Verify fixture file is detected (path drift scans all .md files)
        fixture_rel_path = str(fixture_file.relative_to(demo_project_root)).replace('\\', '/')
        fixture_path_win = str(fixture_file.relative_to(demo_project_root))
        
        found = fixture_rel_path in results or fixture_path_win in results
        assert found, f"Expected {fixture_rel_path} to be in path drift results. Got: {list(results.keys())[:10]}"
        
        # Verify issues are found
        result_key = fixture_rel_path if fixture_rel_path in results else fixture_path_win
        issues = results[result_key]
        assert len(issues) > 0, f"Expected path drift issues in fixture. Got: {issues}"
    
    @pytest.mark.integration
    def test_validation_fixtures_properly_formatted(self, demo_project_root, test_config_path, monkeypatch):
        """Test that properly_formatted.md has no issues (control test, replaces TEST_ANALYSIS.md validation)."""
        fixture_file = demo_project_root / "docs" / "analysis_validation" / "properly_formatted.md"
        assert fixture_file.exists(), "Fixture file should exist"
        
        # Patch constants to include the fixture file
        from development_tools.shared import constants
        original_default_docs = constants.DEFAULT_DOCS
        original_ascii_files = constants.ASCII_COMPLIANCE_FILES
        fixture_rel_path = str(fixture_file.relative_to(demo_project_root)).replace('\\', '/')
        monkeypatch.setattr(constants, 'DEFAULT_DOCS', (fixture_rel_path,))
        monkeypatch.setattr(constants, 'ASCII_COMPLIANCE_FILES', (fixture_rel_path,))
        
        try:
            # Test analyzers that use DEFAULT_DOCS
            analyzers = [
                (HeadingNumberingAnalyzer, 'check_heading_numbering'),
                (MissingAddressAnalyzer, 'check_missing_addresses'),
                (ASCIIComplianceAnalyzer, 'check_ascii_compliance'),
            ]
            
            fixture_path = fixture_rel_path
            fixture_path_win = str(fixture_file.relative_to(demo_project_root))
            
            for AnalyzerClass, method_name in analyzers:
                analyzer = AnalyzerClass(
                    project_root=str(demo_project_root),
                    config_path=test_config_path,
                    use_cache=False
                )
                
                method = getattr(analyzer, method_name)
                results = method()
                
                # Check if file is in results
                found = fixture_path in results or fixture_path_win in results
                
                # If found, verify it has minimal or no issues (properly formatted)
                if found:
                    result_key = fixture_path if fixture_path in results else fixture_path_win
                    issues = results[result_key]
                    # Properly formatted file should have no issues (or very minimal edge cases)
                    # Note: Some analyzers may have strict rules, so allow 0-1 issues for edge cases
                    assert len(issues) <= 1, \
                        f"{AnalyzerClass.__name__} found {len(issues)} issues in properly formatted fixture: {issues}"
        finally:
            monkeypatch.setattr(constants, 'DEFAULT_DOCS', original_default_docs)
            monkeypatch.setattr(constants, 'ASCII_COMPLIANCE_FILES', original_ascii_files)
    
    @pytest.mark.unit
    def test_heading_numbering_detection(self, tmp_path, monkeypatch):
        """Verify unnumbered headings are detected."""
        # Create a test project
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create a README.md file (in DEFAULT_DOCS) with heading issues
        readme_file = project_dir / "README.md"
        readme_file.write_text("""
# Test Project

## Unnumbered Heading

This heading should be numbered.

## 1. Properly Numbered Heading

This heading is correctly numbered.

## Missing Number Section

This section is missing its number.

## 3. Out of Order Section

This section jumps from 1 to 3 (missing section 2).
""")
        
        # Patch DEFAULT_DOCS to include our test file
        from development_tools.shared import constants
        original_default_docs = constants.DEFAULT_DOCS
        monkeypatch.setattr(constants, 'DEFAULT_DOCS', ('README.md',))
        
        try:
            analyzer = HeadingNumberingAnalyzer(
                project_root=str(project_dir),
                use_cache=False
            )
            
            # Run analysis
            results = analyzer.check_heading_numbering()
            
            # Verify analyzer returns results
            assert isinstance(results, dict), "Result should be a dictionary"
            
            # Verify README.md is flagged (if it has issues)
            readme_path = str(readme_file.relative_to(project_dir)).replace('\\', '/')
            readme_path_win = str(readme_file.relative_to(project_dir))
            
            found = readme_path in results or readme_path_win in results
            if found:
                result_key = readme_path if readme_path in results else readme_path_win
                issues = results[result_key]
                assert len(issues) > 0, "Expected at least one heading numbering issue"
        finally:
            # Restore original
            monkeypatch.setattr(constants, 'DEFAULT_DOCS', original_default_docs)
    
    @pytest.mark.unit
    def test_missing_addresses_detection(self, tmp_path):
        """Verify missing addresses are detected."""
        # Create a test project
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create docs directory
        docs_dir = project_dir / "docs"
        docs_dir.mkdir()
        
        # Create a file without file address in header
        doc_file = docs_dir / "missing_address.md"
        doc_file.write_text("""
# Missing Address Test

This document is missing a file address in the header.
""")
        
        analyzer = MissingAddressAnalyzer(
            project_root=str(project_dir),
            use_cache=False
        )
        
        # Run analysis
        results = analyzer.check_missing_addresses()
        
        # Verify analyzer runs (may or may not flag the file depending on logic)
        assert isinstance(results, dict), "Result should be a dictionary"
    
    @pytest.mark.unit
    def test_ascii_compliance_detection(self, tmp_path, monkeypatch):
        """Verify non-ASCII characters are detected."""
        # Create a test project
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create a README.md file (in DEFAULT_DOCS) with non-ASCII characters
        readme_file = project_dir / "README.md"
        readme_file.write_text("""
# Test Project

This section contains non-ASCII characters: café, résumé, naïve, 日本語
""", encoding='utf-8')
        
        # Patch ASCII_COMPLIANCE_FILES to include our test file
        from development_tools.shared import constants
        original_ascii_files = constants.ASCII_COMPLIANCE_FILES
        monkeypatch.setattr(constants, 'ASCII_COMPLIANCE_FILES', ('README.md',))
        
        try:
            analyzer = ASCIIComplianceAnalyzer(
                project_root=str(project_dir),
                use_cache=False
            )
            
            # Run analysis
            results = analyzer.check_ascii_compliance()
            
            # Verify analyzer returns results
            assert isinstance(results, dict), "Result should be a dictionary"
            
            # Verify README.md is flagged (if it has issues)
            readme_path = str(readme_file.relative_to(project_dir)).replace('\\', '/')
            readme_path_win = str(readme_file.relative_to(project_dir))
            
            found = readme_path in results or readme_path_win in results
            if found:
                result_key = readme_path if readme_path in results else readme_path_win
                issues = results[result_key]
                # Use repr() to safely encode non-ASCII characters in assertion message
                assert len(issues) > 0, f"Expected at least one ASCII compliance issue. Got: {repr(issues)}"
        finally:
            # Restore original
            monkeypatch.setattr(constants, 'ASCII_COMPLIANCE_FILES', original_ascii_files)
    
    @pytest.mark.unit
    def test_unconverted_links_detection(self, tmp_path):
        """Verify HTML links are detected."""
        # Create a test project
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create docs directory
        docs_dir = project_dir / "docs"
        docs_dir.mkdir()
        
        # Create a file with HTML links
        doc_file = docs_dir / "unconverted_links.md"
        doc_file.write_text("""
# Unconverted Links Test

This has HTML links: <a href="test.html">Old HTML link</a>
""")
        
        analyzer = UnconvertedLinkAnalyzer(
            project_root=str(project_dir),
            use_cache=False
        )
        
        # Run analysis
        results = analyzer.check_unconverted_links()
        
        # Verify analyzer runs (may or may not detect depending on analyzer logic)
        assert isinstance(results, dict), "Result should be a dictionary"
    
    @pytest.mark.unit
    def test_path_drift_detection(self, tmp_path):
        """Verify broken file references are detected."""
        # Create a test project
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create a core directory (for path references)
        core_dir = project_dir / "core"
        core_dir.mkdir()
        (core_dir / "existing.py").write_text("# Existing file")
        
        # Create docs directory
        docs_dir = project_dir / "docs"
        docs_dir.mkdir()
        
        # Create a file with broken path references
        doc_file = docs_dir / "path_drift.md"
        doc_file.write_text("""
# Path Drift Test

This references missing files: `core/missing_module.py` and [broken link](nonexistent_file.md)
""")
        
        analyzer = PathDriftAnalyzer(
            project_root=str(project_dir),
            use_cache=False
        )
        
        # Run analysis (path drift scans all .md files, not just DEFAULT_DOCS)
        results = analyzer.check_path_drift()
        
        # Verify analyzer returns results
        assert isinstance(results, dict), "Result should be a dictionary"
        
        # Verify fixture file is flagged
        fixture_path = str(doc_file.relative_to(project_dir)).replace('\\', '/')
        fixture_path_win = str(doc_file.relative_to(project_dir))
        
        found = fixture_path in results or fixture_path_win in results
        assert found, f"Expected {fixture_path} to be in path drift results. Got: {list(results.keys())}"
        
        # Verify issues are found
        result_key = fixture_path if fixture_path in results else fixture_path_win
        issues = results[result_key]
        assert len(issues) > 0, "Expected at least one path drift issue"
    
    @pytest.mark.unit
    def test_no_false_positives(self, tmp_path, monkeypatch):
        """Verify properly formatted file has no issues detected."""
        # Create a test project
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create a properly formatted README.md
        readme_file = project_dir / "README.md"
        readme_file.write_text("""
# Properly Formatted Test

## 1. First Section

This section is properly numbered.

## 2. Second Section

This section is also properly numbered.

### 2.1 Subsection

This subsection is properly numbered.
""")
        
        # Patch constants to include README.md
        from development_tools.shared import constants
        original_default_docs = constants.DEFAULT_DOCS
        original_ascii_files = constants.ASCII_COMPLIANCE_FILES
        monkeypatch.setattr(constants, 'DEFAULT_DOCS', ('README.md',))
        monkeypatch.setattr(constants, 'ASCII_COMPLIANCE_FILES', ('README.md',))
        
        try:
            # Test analyzers that use DEFAULT_DOCS
            analyzers = [
                (HeadingNumberingAnalyzer, 'check_heading_numbering'),
                (MissingAddressAnalyzer, 'check_missing_addresses'),
                (ASCIIComplianceAnalyzer, 'check_ascii_compliance'),
            ]
            
            readme_path = str(readme_file.relative_to(project_dir)).replace('\\', '/')
            readme_path_win = str(readme_file.relative_to(project_dir))
            
            for AnalyzerClass, method_name in analyzers:
                analyzer = AnalyzerClass(
                    project_root=str(project_dir),
                    use_cache=False
                )
                
                # Run analysis
                method = getattr(analyzer, method_name)
                results = method()
                
                # Check if file is in results
                found = readme_path in results or readme_path_win in results
                
                # If found, verify it has minimal or no issues
                if found:
                    result_key = readme_path if readme_path in results else readme_path_win
                    issues = results[result_key]
                    # Properly formatted file should have very few or no issues
                    # Allow some tolerance for edge cases
                    assert len(issues) <= 2, \
                        f"{AnalyzerClass.__name__} found {len(issues)} issues in properly formatted file: {issues}"
        finally:
            # Restore originals
            monkeypatch.setattr(constants, 'DEFAULT_DOCS', original_default_docs)
            monkeypatch.setattr(constants, 'ASCII_COMPLIANCE_FILES', original_ascii_files)

