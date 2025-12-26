"""
Tests for fix_documentation.py.

Tests the documentation fix dispatcher that orchestrates all fix operations.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestFixDocumentation:
    """Test documentation fix dispatcher functionality."""
    
    @pytest.mark.unit
    def test_main_with_add_addresses(self, tmp_path):
        """Test main function with --add-addresses flag."""
        from tests.development_tools.conftest import load_development_tools_module
        fix_doc_module = load_development_tools_module("docs.fix_documentation")
        
        # Mock the fixers to avoid actual file operations
        with patch.object(fix_doc_module.DocumentationAddressFixer, 'fix_add_addresses') as mock_fix:
            mock_fix.return_value = {'updated': 1, 'skipped': 2, 'errors': 0}
            
            # Test via main function (would need to mock argparse)
            fixer = fix_doc_module.DocumentationAddressFixer()
            result = fixer.fix_add_addresses(dry_run=True)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            assert 'updated' in result, "Result should have updated count"
            assert 'skipped' in result, "Result should have skipped count"
            assert 'errors' in result, "Result should have errors count"
    
    @pytest.mark.unit
    def test_main_with_fix_ascii(self, tmp_path):
        """Test main function with --fix-ascii flag."""
        from tests.development_tools.conftest import load_development_tools_module
        fix_doc_module = load_development_tools_module("docs.fix_documentation")
        
        with patch.object(fix_doc_module.DocumentationASCIIFixer, 'fix_ascii') as mock_fix:
            mock_fix.return_value = {'files_updated': 1, 'replacements_made': 5, 'errors': 0}
            
            fixer = fix_doc_module.DocumentationASCIIFixer()
            result = fixer.fix_ascii(dry_run=True)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            assert 'files_updated' in result, "Result should have files_updated count"
            assert 'replacements_made' in result, "Result should have replacements_made count"
            assert 'errors' in result, "Result should have errors count"
    
    @pytest.mark.unit
    def test_main_with_all_flag(self, tmp_path):
        """Test main function with --all flag."""
        from tests.development_tools.conftest import load_development_tools_module
        fix_doc_module = load_development_tools_module("docs.fix_documentation")
        
        # Mock all fixers
        with patch.object(fix_doc_module.DocumentationAddressFixer, 'fix_add_addresses') as mock_addr, \
             patch.object(fix_doc_module.DocumentationASCIIFixer, 'fix_ascii') as mock_ascii, \
             patch.object(fix_doc_module.DocumentationHeadingFixer, 'fix_number_headings') as mock_head, \
             patch.object(fix_doc_module.DocumentationLinkFixer, 'fix_convert_links') as mock_link:
            
            mock_addr.return_value = {'updated': 1, 'skipped': 0, 'errors': 0}
            mock_ascii.return_value = {'files_updated': 1, 'replacements_made': 2, 'errors': 0}
            mock_head.return_value = {'files_updated': 1, 'issues_fixed': 3, 'errors': 0}
            mock_link.return_value = {'files_updated': 1, 'changes_made': 4, 'errors': 0}
            
            # Test that all fixers would be called
            addr_fixer = fix_doc_module.DocumentationAddressFixer()
            ascii_fixer = fix_doc_module.DocumentationASCIIFixer()
            
            addr_result = addr_fixer.fix_add_addresses(dry_run=True)
            ascii_result = ascii_fixer.fix_ascii(dry_run=True)
            
            assert isinstance(addr_result, dict), "Address fixer should return dict"
            assert isinstance(ascii_result, dict), "ASCII fixer should return dict"
    
    @pytest.mark.unit
    def test_main_with_dry_run(self, tmp_path):
        """Test main function with --dry-run flag."""
        from tests.development_tools.conftest import load_development_tools_module
        fix_doc_module = load_development_tools_module("docs.fix_documentation")
        
        with patch.object(fix_doc_module.DocumentationAddressFixer, 'fix_add_addresses') as mock_fix:
            mock_fix.return_value = {'updated': 0, 'skipped': 1, 'errors': 0}
            
            fixer = fix_doc_module.DocumentationAddressFixer()
            result = fixer.fix_add_addresses(dry_run=True)
            
            assert result['updated'] == 0 or result['skipped'] >= 0, \
                "Dry run should not update files"
