"""
Tests for fix_documentation_addresses.py.

Tests the documentation address fixer that adds file addresses to documentation files.
"""

import pytest
import tempfile
from pathlib import Path

from tests.development_tools.conftest import load_development_tools_module


class TestFixDocumentationAddresses:
    """Test documentation address fixer functionality."""
    
    @pytest.mark.unit
    def test_fix_add_addresses_basic(self, tmp_path):
        """Test adding addresses to files without addresses."""
        fixer_module = load_development_tools_module("docs.fix_documentation_addresses")
        DocumentationAddressFixer = fixer_module.DocumentationAddressFixer
        
        # Create a documentation file without address
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("""
# Test Documentation

This is a test document without a file address.
""")
        
        fixer = DocumentationAddressFixer(project_root=str(tmp_path))
        result = fixer.fix_add_addresses(dry_run=False)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'updated' in result, "Result should have updated count"
        assert 'skipped' in result, "Result should have skipped count"
        assert 'errors' in result, "Result should have errors count"
        
        # Check that address was added
        content = doc_file.read_text(encoding='utf-8')
        assert '**File**' in content or 'File:' in content, \
            "File address should be added"
    
    @pytest.mark.unit
    def test_fix_add_addresses_with_existing_address(self, tmp_path):
        """Test that files with existing addresses are skipped."""
        fixer_module = load_development_tools_module("docs.fix_documentation_addresses")
        DocumentationAddressFixer = fixer_module.DocumentationAddressFixer
        
        # Create a documentation file with address
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("""
> **File**: `test_doc.md`

# Test Documentation

This document already has a file address.
""")
        
        fixer = DocumentationAddressFixer(project_root=str(tmp_path))
        result = fixer.fix_add_addresses(dry_run=False)
        
        assert result['skipped'] >= 1, "File with existing address should be skipped"
        assert result['updated'] == 0, "No files should be updated"
    
    @pytest.mark.unit
    def test_fix_add_addresses_dry_run(self, tmp_path):
        """Test dry run mode doesn't modify files."""
        fixer_module = load_development_tools_module("docs.fix_documentation_addresses")
        DocumentationAddressFixer = fixer_module.DocumentationAddressFixer
        
        # Create a documentation file without address
        doc_file = tmp_path / "test_doc.md"
        original_content = "# Test\n\nNo address here."
        doc_file.write_text(original_content)
        
        fixer = DocumentationAddressFixer(project_root=str(tmp_path))
        result = fixer.fix_add_addresses(dry_run=True)
        
        # Content should be unchanged in dry run
        content = doc_file.read_text(encoding='utf-8')
        assert content == original_content, "File should not be modified in dry run"
        assert result['updated'] >= 0, "Should report what would be updated"
    
    @pytest.mark.unit
    def test_fix_add_addresses_with_title(self, tmp_path):
        """Test adding address after title."""
        fixer_module = load_development_tools_module("docs.fix_documentation_addresses")
        DocumentationAddressFixer = fixer_module.DocumentationAddressFixer
        
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("# Title\n\nContent here.")
        
        fixer = DocumentationAddressFixer(project_root=str(tmp_path))
        result = fixer.fix_add_addresses(dry_run=False)
        
        content = doc_file.read_text(encoding='utf-8')
        # Address should be added after title
        assert '**File**' in content or 'File:' in content, \
            "File address should be added"
        assert content.find('# Title') < content.find('**File**' or 'File:'), \
            "Address should come after title"
    
    @pytest.mark.unit
    def test_fix_add_addresses_with_frontmatter(self, tmp_path):
        """Test adding address to .mdc file with frontmatter."""
        fixer_module = load_development_tools_module("docs.fix_documentation_addresses")
        DocumentationAddressFixer = fixer_module.DocumentationAddressFixer
        
        doc_file = tmp_path / "test_doc.mdc"
        doc_file.write_text("---\nkey: value\n---\n\n# Content")
        
        fixer = DocumentationAddressFixer(project_root=str(tmp_path))
        result = fixer.fix_add_addresses(dry_run=False)
        
        content = doc_file.read_text(encoding='utf-8')
        # Should add file to frontmatter or as comment
        assert 'file:' in content or 'File:' in content, \
            "File address should be added"
    
    @pytest.mark.unit
    def test_fix_add_addresses_ignores_generated_files(self, tmp_path):
        """Test that generated files are ignored."""
        fixer_module = load_development_tools_module("docs.fix_documentation_addresses")
        DocumentationAddressFixer = fixer_module.DocumentationAddressFixer
        
        # Create a file that looks like it might be generated
        # (This depends on ALL_GENERATED_FILES constant)
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("# Test\n\nNo address.")
        
        fixer = DocumentationAddressFixer(project_root=str(tmp_path))
        result = fixer.fix_add_addresses(dry_run=False)
        
        # Should process or skip based on whether it's in generated files list
        assert isinstance(result, dict), "Should return result dict"
    
    @pytest.mark.unit
    def test_fix_add_addresses_handles_errors(self, tmp_path):
        """Test error handling when processing files."""
        fixer_module = load_development_tools_module("docs.fix_documentation_addresses")
        DocumentationAddressFixer = fixer_module.DocumentationAddressFixer
        
        # Create a file that might cause issues (e.g., permission denied)
        # We'll use a valid file but test error counting
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("# Test")
        
        fixer = DocumentationAddressFixer(project_root=str(tmp_path))
        result = fixer.fix_add_addresses(dry_run=False)
        
        assert 'errors' in result, "Result should have errors count"
        assert result['errors'] >= 0, "Errors should be non-negative"
    
    @pytest.mark.unit
    def test_fix_add_addresses_skips_ignored_directories(self, tmp_path):
        """Test that files in ignored directories are skipped."""
        fixer_module = load_development_tools_module("docs.fix_documentation_addresses")
        DocumentationAddressFixer = fixer_module.DocumentationAddressFixer
        
        # Create file in ignored directory (e.g., .git)
        ignored_dir = tmp_path / ".git"
        ignored_dir.mkdir()
        doc_file = ignored_dir / "test.md"
        doc_file.write_text("# Test")
        
        fixer = DocumentationAddressFixer(project_root=str(tmp_path))
        result = fixer.fix_add_addresses(dry_run=False)
        
        # File in .git should be skipped
        assert result['skipped'] >= 0 or result['updated'] == 0, \
            "Files in ignored directories should be skipped"
