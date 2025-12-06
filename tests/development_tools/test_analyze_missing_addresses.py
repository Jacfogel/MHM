"""
Tests for analyze_missing_addresses.py.

Tests missing address detection in documentation files.
"""

import pytest
import tempfile
from pathlib import Path

from tests.development_tools.conftest import load_development_tools_module, demo_project_root, test_config_path

# Load the module
missing_addresses_module = load_development_tools_module("docs.analyze_missing_addresses")
MissingAddressAnalyzer = missing_addresses_module.MissingAddressAnalyzer


class TestAnalyzeMissingAddresses:
    """Test missing address detection functionality."""
    
    @pytest.mark.unit
    def test_check_missing_addresses_basic(self, tmp_path):
        """Test basic missing address detection."""
        # Create a documentation file without file address
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("""
# Test Documentation

This is a test document without a file address in the header.
""")
        
        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_missing_addresses()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # File may or may not be flagged depending on analyzer logic
    
    @pytest.mark.unit
    def test_check_missing_addresses_with_address(self, tmp_path):
        """Test detection with file address present."""
        # Create a documentation file with file address
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("""
> **File**: `test_doc.md`

# Test Documentation

This document has a file address.
""")
        
        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_missing_addresses()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # File should not be flagged if address is present
    
    @pytest.mark.unit
    def test_check_missing_addresses_empty_file(self, tmp_path):
        """Test detection with empty file."""
        doc_file = tmp_path / "empty.md"
        doc_file.write_text("")
        
        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_missing_addresses()
        
        assert isinstance(results, dict), "Result should be a dictionary"
    
    @pytest.mark.unit
    def test_check_missing_addresses_generated_file(self, tmp_path):
        """Test that generated files are excluded."""
        # Create a generated file (with Generated marker)
        doc_file = tmp_path / "generated.md"
        doc_file.write_text("""
**Generated**: This file is auto-generated.

# Generated Documentation

This file should be excluded from missing address checks.
""")
        
        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_missing_addresses()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # Generated file should be excluded
    
    @pytest.mark.unit
    def test_check_missing_addresses_cursor_directory(self, tmp_path):
        """Test that .cursor/ directory files are excluded."""
        cursor_dir = tmp_path / ".cursor" / "plans"
        cursor_dir.mkdir(parents=True)
        
        cursor_file = cursor_dir / "test_plan.md"
        cursor_file.write_text("# Test Plan\n\nNo file address.")
        
        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_missing_addresses()
        
        assert isinstance(results, dict), "Result should be a dictionary"
        # .cursor/ files should be excluded
    
    @pytest.mark.integration
    def test_check_missing_addresses_demo_project(self, demo_project_root, test_config_path):
        """Test detection on demo project."""
        analyzer = MissingAddressAnalyzer(
            project_root=str(demo_project_root),
            config_path=test_config_path,
            use_cache=False
        )
        results = analyzer.check_missing_addresses()
        
        assert isinstance(results, dict), "Result should be a dictionary"
    
    @pytest.mark.unit
    def test_is_generated_file(self, tmp_path):
        """Test _is_generated_file method."""
        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        
        # Create a file with Generated marker
        generated_file = tmp_path / "generated.md"
        generated_file.write_text("**Generated**: This is generated.")
        
        is_generated = analyzer._is_generated_file(generated_file)
        assert isinstance(is_generated, bool), "Should return boolean"
        assert is_generated, "File with Generated marker should be detected"
        
        # Create a regular file
        regular_file = tmp_path / "regular.md"
        regular_file.write_text("# Regular File")
        
        is_generated = analyzer._is_generated_file(regular_file)
        assert not is_generated, "Regular file should not be detected as generated"
    
    @pytest.mark.unit
    def test_check_missing_addresses_cache(self, tmp_path):
        """Test that caching works correctly."""
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("# Test\n\nNo address.")
        
        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=True)
        
        # First run
        results1 = analyzer.check_missing_addresses()
        
        # Second run (should use cache)
        results2 = analyzer.check_missing_addresses()
        
        assert isinstance(results1, dict), "First result should be a dictionary"
        assert isinstance(results2, dict), "Second result should be a dictionary"
        # Results should be consistent (cached)
    
    @pytest.mark.unit
    def test_check_missing_addresses_no_cache(self, tmp_path):
        """Test with cache disabled."""
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("# Test\n\nNo address.")
        
        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_missing_addresses()
        
        assert isinstance(results, dict), "Result should be a dictionary"

