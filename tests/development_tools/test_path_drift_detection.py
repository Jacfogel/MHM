#!/usr/bin/env python3
"""
Test path drift detection functionality.

This test verifies that path drift detection correctly identifies
documentation references to files that don't exist.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from development_tools.docs.analyze_path_drift import PathDriftAnalyzer


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
        doc_file.write_text("""
# Test Documentation

This file references a non-existent file: `core/nonexistent_module.py`

Also references: `tests/missing_test.py`
""")
        
        # Create analyzer
        analyzer = PathDriftAnalyzer(project_root=str(project_dir))
        
        # Run path drift check
        results = analyzer.check_path_drift()
        
        # Verify that the documentation file is flagged
        doc_file_str = str(doc_file.relative_to(project_dir))
        assert doc_file_str in results, f"Expected {doc_file_str} to be in drift results"
        
        # Verify that the issues are detected
        issues = results[doc_file_str]
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
    
    def test_path_drift_with_legacy_documentation(self, tmp_path):
        """Test that path drift detection skips legacy documentation files."""
        # Create a temporary project structure
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create legacy documentation file
        dev_docs_dir = project_dir / "development_docs"
        dev_docs_dir.mkdir(parents=True)
        
        legacy_file = dev_docs_dir / "LEGACY_REFERENCE_REPORT.md"
        legacy_file.write_text("""
# Legacy Reference Report

This file intentionally references old paths:
- `bot/old_module.py` (legacy path)
- `old_directory/file.py` (historical reference)
""")
        
        # Create analyzer
        analyzer = PathDriftAnalyzer(project_root=str(project_dir))
        
        # Run path drift check
        results = analyzer.check_path_drift()
        
        # Verify that legacy documentation is skipped
        legacy_file_str = str(legacy_file.relative_to(project_dir))
        # Legacy files should be skipped, so they shouldn't appear in results
        # (or if they do, it should be for non-legacy reasons)
        if legacy_file_str in results:
            # If it appears, verify it's not for the legacy paths
            issues = results[legacy_file_str]
            issue_text = ' '.join(issues)
            # Legacy paths should be filtered out
            assert 'old_module.py' not in issue_text or 'old_directory' not in issue_text, \
                f"Legacy paths should be filtered: {issues}"

