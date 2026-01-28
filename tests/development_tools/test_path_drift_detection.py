#!/usr/bin/env python3
# INTENTIONAL LEGACY: This test file intentionally references legacy paths (bot/old_module.py)
# in test data to verify path drift detection works correctly. These references should NOT
# be flagged as issues - they are test code.
"""
Test path drift detection functionality.

This test verifies that path drift detection correctly identifies
documentation references to files that don't exist.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

# Import helper from conftest
from tests.development_tools.conftest import load_development_tools_module

# Load the module using the helper
path_drift_module = load_development_tools_module("docs.analyze_path_drift")
PathDriftAnalyzer = path_drift_module.PathDriftAnalyzer


@pytest.mark.unit
class TestPathDriftDetection:
    """Test path drift detection."""
    
    def test_path_drift_detects_missing_file(self, tmp_path):
        """Test that path drift detection finds references to non-existent files."""
        # Create a temporary project structure
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create a documentation file with a reference to a non-existent file
        docs_dir = project_dir / "docs"
        docs_dir.mkdir()
        
        doc_file = docs_dir / "README.md"
        # Write content without leading spaces to avoid issues with path extraction
        doc_file.write_text(
            "# Test Documentation\n\n"
            "This file references a non-existent file: `core/nonexistent_module.py`\n\n"
            "Also references: `tests/missing_test.py`\n"
        )
        
        # Create analyzer with cache disabled for testing
        analyzer = PathDriftAnalyzer(project_root=str(project_dir), use_cache=False)
        
        # Run path drift check
        results = analyzer.check_path_drift()

        # Verify that the documentation file is flagged
        # Normalize path separators for cross-platform compatibility
        doc_file_str = str(doc_file.relative_to(project_dir)).replace('\\', '/')
        doc_file_win = str(doc_file.relative_to(project_dir))
        # Check both normalized and original path formats
        found = doc_file_str in results or doc_file_win in results
        doc_paths = analyzer.scan_documentation_paths()
        assert found, f"Expected {doc_file_str} (or Windows path) to be in drift results. Got: {list(results.keys())}. Doc paths: {dict(doc_paths)}"

        # Get the key that was actually used (could be either format)
        result_key = doc_file_str if doc_file_str in results else doc_file_win
        issues = results[result_key]
        assert len(issues) > 0, "Expected at least one path drift issue"
        
        # Check that the non-existent files are mentioned
        issue_text = ' '.join(issues)
        assert 'nonexistent_module.py' in issue_text or 'missing_test.py' in issue_text, \
            f"Expected non-existent file to be mentioned in issues: {issues}"
    
    def test_path_drift_ignores_existing_files(self, tmp_path):
        """Test that path drift detection doesn't flag existing files."""
        # Create a temporary project structure
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create actual files
        core_dir = project_dir / "core"
        core_dir.mkdir()
        existing_file = core_dir / "existing_module.py"
        existing_file.write_text("# Existing module")
        
        # Create documentation that references the existing file
        docs_dir = project_dir / "docs"
        docs_dir.mkdir()
        
        doc_file = docs_dir / "README.md"
        doc_file.write_text(f"""
# Test Documentation

This file references an existing file: `core/existing_module.py`
""")
        
        # Create analyzer
        analyzer = PathDriftAnalyzer(project_root=str(project_dir))
        
        # Run path drift check
        results = analyzer.check_path_drift()
        
        # Verify that the documentation file is NOT flagged (or flagged for other reasons only)
        doc_file_str = str(doc_file.relative_to(project_dir))
        if doc_file_str in results:
            # If it's flagged, make sure it's not for the existing file
            issues = results[doc_file_str]
            issue_text = ' '.join(issues)
            assert 'existing_module.py' not in issue_text, \
                f"Existing file should not be flagged: {issues}"
    
    def test_path_drift_with_reference_report(self, tmp_path):
        """Test that path drift detection skips compatibility reference docs."""
        # Create a temporary project structure
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create compatibility reference report file
        dev_docs_dir = project_dir / "development_docs"
        dev_docs_dir.mkdir(parents=True)
        
        legacy_file = dev_docs_dir / "LEGACY_REFERENCE_REPORT.md"
        legacy_file.write_text("""
# Reference Report

This file intentionally references old paths:
- `bot/old_module.py` (compatibility path)
- `old_directory/file.py` (historical reference)
""")
        
        # Create analyzer
        analyzer = PathDriftAnalyzer(project_root=str(project_dir))
        
        # Run path drift check
        results = analyzer.check_path_drift()
        
        # Verify that compatibility reference docs are skipped
        legacy_file_str = str(legacy_file.relative_to(project_dir))
        # These files should be skipped, so they shouldn't appear in results
        # (or if they do, it should be for non-compatibility reasons)
        if legacy_file_str in results:
            # If it appears, verify it's not for the compatibility paths
            issues = results[legacy_file_str]
            issue_text = ' '.join(issues)
            # Compatibility paths should be filtered out
            assert 'old_module.py' not in issue_text or 'old_directory' not in issue_text, \
                f"Compatibility paths should be filtered: {issues}"
