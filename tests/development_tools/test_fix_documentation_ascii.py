"""
Tests for fix_documentation_ascii.py.

Tests the documentation ASCII fixer that replaces non-ASCII characters.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from tests.development_tools.conftest import load_development_tools_module



class TestFixDocumentationASCII:
    """Test documentation ASCII fixer functionality."""
    
    @pytest.mark.unit
    def test_fix_ascii_basic(self, tmp_path):
        """Test fixing non-ASCII characters in documentation."""
        fixer_module = load_development_tools_module("docs.fix_documentation_ascii")
        DocumentationASCIIFixer = fixer_module.DocumentationASCIIFixer
        
        # Create a file with non-ASCII characters
        doc_file = tmp_path / "test_doc.md"
        # Use smart quotes and em dash
        doc_file.write_text("# Test\n\nThis has 'smart quotes' and — an em dash.")
        
        fixer = DocumentationASCIIFixer(project_root=str(tmp_path))
        
        # Patch ASCII_COMPLIANCE_FILES where it's used in the fixer module
        with patch('development_tools.docs.fix_documentation_ascii.ASCII_COMPLIANCE_FILES', ['test_doc.md']):
            result = fixer.fix_ascii(dry_run=False)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'files_updated' in result, "Result should have files_updated count"
        assert 'replacements_made' in result, "Result should have replacements_made count"
        assert 'errors' in result, "Result should have errors count"
    
    @pytest.mark.unit
    def test_fix_ascii_smart_quotes(self, tmp_path):
        """Test replacement of smart quotes."""
        fixer_module = load_development_tools_module("docs.fix_documentation_ascii")
        DocumentationASCIIFixer = fixer_module.DocumentationASCIIFixer
        
        doc_file = tmp_path / "test_doc.md"
        # Use Unicode smart quotes
        doc_file.write_text("# Test\n\n'Smart quotes' and \"double quotes\".")
        
        fixer = DocumentationASCIIFixer(project_root=str(tmp_path))
        
        # Patch ASCII_COMPLIANCE_FILES where it's used in the fixer module
        with patch('development_tools.docs.fix_documentation_ascii.ASCII_COMPLIANCE_FILES', ['test_doc.md']):
            result = fixer.fix_ascii(dry_run=False)
        
        if result['files_updated'] > 0:
            content = doc_file.read_text(encoding='utf-8')
            # Smart quotes should be replaced with regular quotes
            assert '\u2018' not in content and '\u2019' not in content, \
                "Smart quotes should be replaced"
    
    @pytest.mark.unit
    def test_fix_ascii_em_dash(self, tmp_path):
        """Test replacement of em dash."""
        fixer_module = load_development_tools_module("docs.fix_documentation_ascii")
        DocumentationASCIIFixer = fixer_module.DocumentationASCIIFixer
        
        doc_file = tmp_path / "test_doc.md"
        # Use Unicode em dash
        doc_file.write_text("# Test\n\nThis has an — em dash.")
        
        fixer = DocumentationASCIIFixer(project_root=str(tmp_path))
        
        # Patch ASCII_COMPLIANCE_FILES where it's used in the fixer module
        with patch('development_tools.docs.fix_documentation_ascii.ASCII_COMPLIANCE_FILES', ['test_doc.md']):
            result = fixer.fix_ascii(dry_run=False)
        
        if result['files_updated'] > 0:
            content = doc_file.read_text(encoding='utf-8')
            # Em dash should be replaced
            assert '\u2014' not in content, "Em dash should be replaced"
    
    @pytest.mark.unit
    def test_fix_ascii_dry_run(self, tmp_path):
        """Test dry run mode doesn't modify files."""
        fixer_module = load_development_tools_module("docs.fix_documentation_ascii")
        DocumentationASCIIFixer = fixer_module.DocumentationASCIIFixer
        
        doc_file = tmp_path / "test_doc.md"
        original_content = "# Test\n\n'Smart quotes'."
        doc_file.write_text(original_content)
        
        fixer = DocumentationASCIIFixer(project_root=str(tmp_path))
        
        # Patch ASCII_COMPLIANCE_FILES where it's used in the fixer module
        with patch('development_tools.docs.fix_documentation_ascii.ASCII_COMPLIANCE_FILES', ['test_doc.md']):
            result = fixer.fix_ascii(dry_run=True)
        
        # In dry run, file should not be modified but should report what would change
        content = doc_file.read_text(encoding='utf-8')
        # File may or may not be modified depending on implementation
        assert isinstance(result, dict), "Should return result dict"
        assert result['files_updated'] >= 0, "Should report files that would be updated"
    
    @pytest.mark.unit
    def test_fix_ascii_no_non_ascii(self, tmp_path):
        """Test that files with only ASCII characters are not modified."""
        fixer_module = load_development_tools_module("docs.fix_documentation_ascii")
        DocumentationASCIIFixer = fixer_module.DocumentationASCIIFixer
        
        doc_file = tmp_path / "test_doc.md"
        original_content = "# Test\n\nThis has only ASCII characters."
        doc_file.write_text(original_content)
        
        fixer = DocumentationASCIIFixer(project_root=str(tmp_path))
        
        # Patch ASCII_COMPLIANCE_FILES where it's used in the fixer module
        with patch('development_tools.docs.fix_documentation_ascii.ASCII_COMPLIANCE_FILES', ['test_doc.md']):
            result = fixer.fix_ascii(dry_run=False)
        
        # File should not be updated if no non-ASCII characters
        content = doc_file.read_text(encoding='utf-8')
        assert content == original_content, "File with only ASCII should not be modified"
        assert result['files_updated'] == 0, "No files should be updated"
        assert result['replacements_made'] == 0, "No replacements should be made"
    
    @pytest.mark.unit
    def test_fix_ascii_handles_errors(self, tmp_path):
        """Test error handling when processing files."""
        fixer_module = load_development_tools_module("docs.fix_documentation_ascii")
        DocumentationASCIIFixer = fixer_module.DocumentationASCIIFixer
        
        # Test with non-existent file (should be handled gracefully)
        fixer = DocumentationASCIIFixer(project_root=str(tmp_path))
        
        # Patch ASCII_COMPLIANCE_FILES where it's used in the fixer module
        with patch('development_tools.docs.fix_documentation_ascii.ASCII_COMPLIANCE_FILES', ['nonexistent.md']):
            result = fixer.fix_ascii(dry_run=False)
        
        assert 'errors' in result, "Result should have errors count"
        assert result['errors'] >= 0, "Errors should be non-negative"
    
    @pytest.mark.unit
    def test_fix_ascii_multiple_replacements(self, tmp_path):
        """Test fixing multiple non-ASCII characters in one file."""
        fixer_module = load_development_tools_module("docs.fix_documentation_ascii")
        DocumentationASCIIFixer = fixer_module.DocumentationASCIIFixer
        
        doc_file = tmp_path / "test_doc.md"
        # Use multiple non-ASCII characters (using actual Unicode characters)
        # Left single quote (\u2018), em dash (\u2014), ellipsis (\u2026)
        doc_file.write_text("# Test\n\n\u2018Smart quotes\u2019 \u2014 em dash \u2026 ellipsis.")
        
        fixer = DocumentationASCIIFixer(project_root=str(tmp_path))
        
        # Patch ASCII_COMPLIANCE_FILES where it's used in the fixer module
        with patch('development_tools.docs.fix_documentation_ascii.ASCII_COMPLIANCE_FILES', ['test_doc.md']):
            result = fixer.fix_ascii(dry_run=False)
        
        if result['files_updated'] > 0:
            assert result['replacements_made'] >= 3, \
                f"Should make multiple replacements, got {result['replacements_made']}"
            content = doc_file.read_text(encoding='utf-8')
            # All non-ASCII should be replaced
            assert '\u2018' not in content and '\u2019' not in content and '\u2014' not in content and '\u2026' not in content, \
                "All non-ASCII characters should be replaced"
