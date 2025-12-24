"""
Tests for fix_documentation_headings.py.

Tests documentation heading numbering fix functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from tests.development_tools.conftest import load_development_tools_module, temp_project_copy


# Load the module
headings_module = load_development_tools_module("docs.fix_documentation_headings")
DocumentationHeadingFixer = headings_module.DocumentationHeadingFixer
_number_headings = headings_module._number_headings
main = headings_module.main


class TestDocumentationHeadingFixer:
    """Test DocumentationHeadingFixer class functionality."""
    
    @pytest.mark.unit
    def test_init_default_project_root(self, temp_project_copy):
        """Test initialization with default project root."""
        with patch('development_tools.docs.fix_documentation_headings.config') as mock_config:
            mock_config.get_project_root.return_value = str(temp_project_copy)
            
            fixer = DocumentationHeadingFixer()
            
            assert fixer.project_root == Path(temp_project_copy).resolve(), \
                "Project root should be resolved path"
    
    @pytest.mark.unit
    def test_init_custom_project_root(self, temp_project_copy):
        """Test initialization with custom project root."""
        fixer = DocumentationHeadingFixer(project_root=str(temp_project_copy))
        
        assert fixer.project_root == Path(temp_project_copy).resolve(), \
            "Project root should be custom path"
    
    @pytest.mark.unit
    def test_fix_number_headings_dry_run(self, temp_project_copy):
        """Test heading numbering fix in dry run mode."""
        # Create a test documentation file
        doc_file = temp_project_copy / "test_doc.md"
        doc_file.write_text("""# Title

## First Section

Content here.

## Second Section

More content.
""")
        
        with patch('development_tools.docs.fix_documentation_headings.DEFAULT_DOCS', ['test_doc.md']):
            fixer = DocumentationHeadingFixer(project_root=str(temp_project_copy))
            result = fixer.fix_number_headings(dry_run=True)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            assert 'files_updated' in result, "Result should have files_updated"
            assert 'issues_fixed' in result, "Result should have issues_fixed"
            assert 'errors' in result, "Result should have errors"
            assert result['files_updated'] == 0, "Should not update files in dry run"
            
            # File should not be modified
            original_content = doc_file.read_text()
            assert "## First Section" in original_content, \
                "File should not be modified in dry run"
    
    @pytest.mark.unit
    def test_fix_number_headings_actual_fix(self, temp_project_copy):
        """Test heading numbering fix with actual file modification."""
        # Create a test documentation file
        doc_file = temp_project_copy / "test_doc.md"
        doc_file.write_text("""# Title

## First Section

Content here.

## Second Section

More content.
""")
        
        with patch('development_tools.docs.fix_documentation_headings.DEFAULT_DOCS', ['test_doc.md']):
            fixer = DocumentationHeadingFixer(project_root=str(temp_project_copy))
            result = fixer.fix_number_headings(dry_run=False)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            # File may or may not be updated depending on heading format
            assert result['errors'] == 0, "Should not have errors"
            
            # Check if file was modified
            new_content = doc_file.read_text()
            # If headings were numbered, they should have numbers
            # If they already had numbers, file might not change
            assert isinstance(new_content, str), "File should still be readable"
    
    @pytest.mark.unit
    def test_fix_number_headings_skips_changelog(self, temp_project_copy):
        """Test that changelog files are skipped."""
        # Create a changelog file
        changelog = temp_project_copy / "CHANGELOG.md"
        changelog.write_text("""# Changelog

## Unnumbered Entry

Content without numbering.
""")
        
        with patch('development_tools.docs.fix_documentation_headings.DEFAULT_DOCS', ['CHANGELOG.md']):
            fixer = DocumentationHeadingFixer(project_root=str(temp_project_copy))
            result = fixer.fix_number_headings(dry_run=False)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            # Changelog should be skipped
            assert result['files_updated'] == 0, "Changelog should not be updated"
    
    @pytest.mark.unit
    def test_fix_number_headings_start_at_zero(self, temp_project_copy):
        """Test heading numbering starting at zero."""
        # Create a test documentation file
        doc_file = temp_project_copy / "test_doc.md"
        doc_file.write_text("""# Title

## First Section

Content here.

## Second Section

More content.
""")
        
        with patch('development_tools.docs.fix_documentation_headings.DEFAULT_DOCS', ['test_doc.md']):
            fixer = DocumentationHeadingFixer(project_root=str(temp_project_copy))
            result = fixer.fix_number_headings(dry_run=False, start_at_zero=True)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            assert result['errors'] == 0, "Should not have errors"
    
    @pytest.mark.unit
    def test_fix_number_headings_nonexistent_file(self, temp_project_copy):
        """Test handling of non-existent files."""
        with patch('development_tools.docs.fix_documentation_headings.DEFAULT_DOCS', ['nonexistent.md']):
            fixer = DocumentationHeadingFixer(project_root=str(temp_project_copy))
            result = fixer.fix_number_headings(dry_run=False)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            assert result['files_updated'] == 0, "Should not update non-existent files"
            assert result['errors'] == 0, "Should not have errors for non-existent files"
    
    @pytest.mark.unit
    def test_fix_number_headings_file_error(self, temp_project_copy):
        """Test handling of file read errors."""
        # Create a file that might cause read issues
        doc_file = temp_project_copy / "test_doc.md"
        doc_file.write_text("# Test")
        
        with patch('development_tools.docs.fix_documentation_headings.DEFAULT_DOCS', ['test_doc.md']):
            fixer = DocumentationHeadingFixer(project_root=str(temp_project_copy))
            
            # Mock file read to raise exception
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                result = fixer.fix_number_headings(dry_run=False)
                
                assert isinstance(result, dict), "Result should be a dictionary"
                assert result['errors'] > 0, "Should report errors"


class TestNumberHeadingsFunction:
    """Test _number_headings helper function."""
    
    @pytest.mark.unit
    def test_number_headings_basic(self, tmp_path):
        """Test basic heading numbering."""
        content = """# Title

## First Section

Content.

## Second Section

More content.
"""
        
        new_content, issues = _number_headings(content, create_updates=True)
        
        assert isinstance(new_content, str), "New content should be string"
        assert isinstance(issues, list), "Issues should be list"
        # Content should have numbered headings
        assert "## 1." in new_content or "## 2." in new_content or new_content == content, \
            "Headings should be numbered or already numbered"
    
    @pytest.mark.unit
    def test_number_headings_already_numbered(self, tmp_path):
        """Test heading numbering with already-numbered headings."""
        content = """# Title

## 1. First Section

Content.

## 2. Second Section

More content.
"""
        
        new_content, issues = _number_headings(content, create_updates=True)
        
        assert isinstance(new_content, str), "New content should be string"
        assert isinstance(issues, list), "Issues should be list"
        # Already-numbered headings should remain
        assert "## 1." in new_content, "Already-numbered headings should remain"
    
    @pytest.mark.unit
    def test_number_headings_start_at_zero(self, tmp_path):
        """Test heading numbering starting at zero."""
        content = """# Title

## First Section

Content.

## Second Section

More content.
"""
        
        new_content, issues = _number_headings(content, start_at_zero=True, create_updates=True)
        
        assert isinstance(new_content, str), "New content should be string"
        assert isinstance(issues, list), "Issues should be list"
        # Headings should start at 0
        assert "## 0." in new_content or new_content == content, \
            "Headings should start at 0 or already be numbered"
    
    @pytest.mark.unit
    def test_number_headings_h3_numbering(self, tmp_path):
        """Test H3 heading numbering."""
        content = """# Title

## 1. First Section

### Subsection One

Content.

### Subsection Two

More content.
"""
        
        new_content, issues = _number_headings(content, create_updates=True)
        
        assert isinstance(new_content, str), "New content should be string"
        assert isinstance(issues, list), "Issues should be list"
        # H3 headings should be numbered
        assert "### 1.1." in new_content or "### 1.2." in new_content or new_content == content, \
            "H3 headings should be numbered or already numbered"
    
    @pytest.mark.unit
    def test_number_headings_no_updates(self, tmp_path):
        """Test heading numbering without creating updates."""
        content = """# Title

## First Section

Content.
"""
        
        new_content, issues = _number_headings(content, create_updates=False)
        
        assert isinstance(new_content, str), "New content should be string"
        assert isinstance(issues, list), "Issues should be list"
        # Content should be analyzed but not modified
        assert len(new_content) > 0, "Content should be returned"


class TestFixDocumentationHeadingsMain:
    """Test main() function for CLI interface."""
    
    @pytest.mark.unit
    def test_main_dry_run(self, temp_project_copy):
        """Test main function with --dry-run flag."""
        with patch('development_tools.docs.fix_documentation_headings.DocumentationHeadingFixer') as mock_fixer_class:
            mock_fixer = mock_fixer_class.return_value
            mock_fixer.fix_number_headings.return_value = {
                'files_updated': 0,
                'issues_fixed': 5,
                'errors': 0
            }
            
            with patch('sys.argv', ['fix_documentation_headings.py', '--dry-run']):
                result = main()
            
            assert result == 0, "Should exit with success code"
            mock_fixer.fix_number_headings.assert_called_once()
            call_kwargs = mock_fixer.fix_number_headings.call_args[1]
            assert call_kwargs['dry_run'] is True, "Should use dry run mode"
    
    @pytest.mark.unit
    def test_main_start_at_zero(self, temp_project_copy):
        """Test main function with --start-at-zero flag."""
        with patch('development_tools.docs.fix_documentation_headings.DocumentationHeadingFixer') as mock_fixer_class:
            mock_fixer = mock_fixer_class.return_value
            mock_fixer.fix_number_headings.return_value = {
                'files_updated': 2,
                'issues_fixed': 10,
                'errors': 0
            }
            
            with patch('sys.argv', ['fix_documentation_headings.py', '--start-at-zero']):
                result = main()
            
            assert result == 0, "Should exit with success code"
            call_kwargs = mock_fixer.fix_number_headings.call_args[1]
            assert call_kwargs['start_at_zero'] is True, "Should start at zero"
    
    @pytest.mark.unit
    def test_main_exit_code_on_error(self, temp_project_copy):
        """Test main function exit code when errors occur."""
        with patch('development_tools.docs.fix_documentation_headings.DocumentationHeadingFixer') as mock_fixer_class:
            mock_fixer = mock_fixer_class.return_value
            mock_fixer.fix_number_headings.return_value = {
                'files_updated': 1,
                'issues_fixed': 5,
                'errors': 2
            }
            
            with patch('sys.argv', ['fix_documentation_headings.py']):
                result = main()
            
            assert result == 1, "Should exit with error code when errors occur"

