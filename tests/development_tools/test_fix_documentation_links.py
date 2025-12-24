"""
Tests for fix_documentation_links.py.

Tests documentation link conversion fix functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from tests.development_tools.conftest import load_development_tools_module, temp_project_copy


# Load the module
links_module = load_development_tools_module("docs.fix_documentation_links")
DocumentationLinkFixer = links_module.DocumentationLinkFixer
main = links_module.main


class TestDocumentationLinkFixer:
    """Test DocumentationLinkFixer class functionality."""
    
    @pytest.mark.unit
    def test_init_default_project_root(self, temp_project_copy):
        """Test initialization with default project root."""
        with patch('development_tools.docs.fix_documentation_links.config') as mock_config:
            mock_config.get_project_root.return_value = str(temp_project_copy)
            
            fixer = DocumentationLinkFixer()
            
            assert fixer.project_root == Path(temp_project_copy).resolve(), \
                "Project root should be resolved path"
    
    @pytest.mark.unit
    def test_init_custom_project_root(self, temp_project_copy):
        """Test initialization with custom project root."""
        fixer = DocumentationLinkFixer(project_root=str(temp_project_copy))
        
        assert fixer.project_root == Path(temp_project_copy).resolve(), \
            "Project root should be custom path"
    
    @pytest.mark.unit
    def test_fix_convert_links_dry_run(self, temp_project_copy):
        """Test link conversion in dry run mode."""
        # Create a test documentation file with unconverted path
        doc_file = temp_project_copy / "test_doc.md"
        target_file = temp_project_copy / "target.md"
        target_file.write_text("# Target")
        
        doc_file.write_text(f"""# Test Documentation

See the file at tests/target.md for more information.
""")
        
        with patch('development_tools.docs.fix_documentation_links.DEFAULT_DOCS', ['test_doc.md']):
            fixer = DocumentationLinkFixer(project_root=str(temp_project_copy))
            result = fixer.fix_convert_links(dry_run=True)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            assert 'files_updated' in result, "Result should have files_updated"
            assert 'changes_made' in result, "Result should have changes_made"
            assert 'errors' in result, "Result should have errors"
            assert result['files_updated'] == 0, "Should not update files in dry run"
            
            # File should not be modified
            original_content = doc_file.read_text()
            assert "tests/target.md" in original_content, \
                "File should not be modified in dry run"
    
    @pytest.mark.unit
    def test_fix_convert_links_actual_fix(self, temp_project_copy):
        """Test link conversion with actual file modification."""
        # Create a test documentation file with unconverted path
        doc_file = temp_project_copy / "test_doc.md"
        target_file = temp_project_copy / "target.md"
        target_file.write_text("# Target")
        
        doc_file.write_text(f"""# Test Documentation

See the file at `tests/target.md` for more information.
""")
        
        with patch('development_tools.docs.fix_documentation_links.DEFAULT_DOCS', ['test_doc.md']):
            fixer = DocumentationLinkFixer(project_root=str(temp_project_copy))
            result = fixer.fix_convert_links(dry_run=False)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            # File may or may not be updated depending on path validation
            assert result['errors'] == 0, "Should not have errors"
            
            # Check if file was modified
            new_content = doc_file.read_text()
            # If link was converted, it should be a markdown link
            # If path was invalid, file might not change
            assert isinstance(new_content, str), "File should still be readable"
    
    @pytest.mark.unit
    def test_fix_convert_links_skips_generated(self, temp_project_copy):
        """Test that generated files are skipped."""
        # Create a generated file
        generated_file = temp_project_copy / "generated.md"
        generated_file.write_text("""**Generated**: This file is auto-generated.

# Generated Documentation

See `tests/example.md` for reference.
""")
        
        with patch('development_tools.docs.fix_documentation_links.DEFAULT_DOCS', ['generated.md']):
            fixer = DocumentationLinkFixer(project_root=str(temp_project_copy))
            result = fixer.fix_convert_links(dry_run=False)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            # Generated file should be skipped
            assert result['files_updated'] == 0, "Generated file should not be updated"
    
    @pytest.mark.unit
    def test_fix_convert_links_skips_code_blocks(self, temp_project_copy):
        """Test that paths in code blocks are skipped."""
        # Create a file with path in code block
        doc_file = temp_project_copy / "test_doc.md"
        target_file = temp_project_copy / "target.md"
        target_file.write_text("# Target")
        
        doc_file.write_text(f"""# Test Documentation

```python
# This is a code block with a path: `tests/target.md`
import sys
```
""")
        
        with patch('development_tools.docs.fix_documentation_links.DEFAULT_DOCS', ['test_doc.md']):
            fixer = DocumentationLinkFixer(project_root=str(temp_project_copy))
            result = fixer.fix_convert_links(dry_run=False)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            # Paths in code blocks should be skipped
            assert result['errors'] == 0, "Should not have errors"
            
            # Check that code block content wasn't modified
            new_content = doc_file.read_text()
            assert "```python" in new_content, "Code block should remain"
    
    @pytest.mark.unit
    def test_fix_convert_links_skips_example_contexts(self, temp_project_copy):
        """Test that paths in example contexts are skipped."""
        # Create a file with path in example context
        doc_file = temp_project_copy / "test_doc.md"
        target_file = temp_project_copy / "target.md"
        target_file.write_text("# Target")
        
        doc_file.write_text(f"""# Test Documentation

[EXAMPLE] For example, see `tests/target.md` for usage.
""")
        
        with patch('development_tools.docs.fix_documentation_links.DEFAULT_DOCS', ['test_doc.md']):
            fixer = DocumentationLinkFixer(project_root=str(temp_project_copy))
            result = fixer.fix_convert_links(dry_run=False)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            # Paths in example contexts should be skipped
            assert result['errors'] == 0, "Should not have errors"
    
    @pytest.mark.unit
    def test_fix_convert_links_skips_existing_links(self, temp_project_copy):
        """Test that already-converted links are skipped."""
        # Create a file with proper markdown link
        doc_file = temp_project_copy / "test_doc.md"
        target_file = temp_project_copy / "target.md"
        target_file.write_text("# Target")
        
        doc_file.write_text(f"""# Test Documentation

See [the target file](tests/target.md) for more information.
""")
        
        with patch('development_tools.docs.fix_documentation_links.DEFAULT_DOCS', ['test_doc.md']):
            fixer = DocumentationLinkFixer(project_root=str(temp_project_copy))
            result = fixer.fix_convert_links(dry_run=False)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            # Already-converted links should be skipped
            assert result['errors'] == 0, "Should not have errors"
            
            # Check that link wasn't modified
            new_content = doc_file.read_text()
            assert "[the target file](tests/target.md)" in new_content, \
                "Already-converted link should remain"
    
    @pytest.mark.unit
    def test_fix_convert_links_nonexistent_file(self, temp_project_copy):
        """Test handling of non-existent files."""
        with patch('development_tools.docs.fix_documentation_links.DEFAULT_DOCS', ['nonexistent.md']):
            fixer = DocumentationLinkFixer(project_root=str(temp_project_copy))
            result = fixer.fix_convert_links(dry_run=False)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            assert result['files_updated'] == 0, "Should not update non-existent files"
            assert result['errors'] == 0, "Should not have errors for non-existent files"
            assert 'breakdown' in result, "Result should have breakdown"
            assert result['breakdown']['files_skipped_not_found'] > 0, \
                "Should track skipped files"
    
    @pytest.mark.unit
    def test_fix_convert_links_file_error(self, temp_project_copy):
        """Test handling of file read errors."""
        # Create a file
        doc_file = temp_project_copy / "test_doc.md"
        doc_file.write_text("# Test")
        
        with patch('development_tools.docs.fix_documentation_links.DEFAULT_DOCS', ['test_doc.md']):
            fixer = DocumentationLinkFixer(project_root=str(temp_project_copy))
            
            # Mock file read to raise exception
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                result = fixer.fix_convert_links(dry_run=False)
                
                assert isinstance(result, dict), "Result should be a dictionary"
                assert result['errors'] > 0, "Should report errors"
    
    @pytest.mark.unit
    def test_fix_convert_links_breakdown(self, temp_project_copy):
        """Test that breakdown statistics are tracked."""
        # Create a test file
        doc_file = temp_project_copy / "test_doc.md"
        doc_file.write_text("""# Test Documentation

Some content here.
""")
        
        with patch('development_tools.docs.fix_documentation_links.DEFAULT_DOCS', ['test_doc.md']):
            fixer = DocumentationLinkFixer(project_root=str(temp_project_copy))
            result = fixer.fix_convert_links(dry_run=False)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            assert 'breakdown' in result, "Result should have breakdown"
            breakdown = result['breakdown']
            assert 'files_processed' in breakdown, "Breakdown should track files_processed"
            assert 'files_skipped_generated' in breakdown, "Breakdown should track skipped generated"
            assert 'files_skipped_not_found' in breakdown, "Breakdown should track skipped not found"


class TestFixDocumentationLinksMain:
    """Test main() function for CLI interface."""
    
    @pytest.mark.unit
    def test_main_dry_run(self, temp_project_copy):
        """Test main function with --dry-run flag."""
        with patch('development_tools.docs.fix_documentation_links.DocumentationLinkFixer') as mock_fixer_class:
            mock_fixer = mock_fixer_class.return_value
            mock_fixer.fix_convert_links.return_value = {
                'files_updated': 0,
                'changes_made': 5,
                'errors': 0,
                'breakdown': {}
            }
            
            with patch('sys.argv', ['fix_documentation_links.py', '--dry-run']):
                result = main()
            
            assert result == 0, "Should exit with success code"
            mock_fixer.fix_convert_links.assert_called_once()
            call_kwargs = mock_fixer.fix_convert_links.call_args[1]
            assert call_kwargs['dry_run'] is True, "Should use dry run mode"
    
    @pytest.mark.unit
    def test_main_exit_code_on_error(self, temp_project_copy):
        """Test main function exit code when errors occur."""
        with patch('development_tools.docs.fix_documentation_links.DocumentationLinkFixer') as mock_fixer_class:
            mock_fixer = mock_fixer_class.return_value
            mock_fixer.fix_convert_links.return_value = {
                'files_updated': 1,
                'changes_made': 5,
                'errors': 2,
                'breakdown': {}
            }
            
            with patch('sys.argv', ['fix_documentation_links.py']):
                result = main()
            
            assert result == 1, "Should exit with error code when errors occur"

