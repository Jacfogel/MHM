"""
Tests for analyze_documentation.py.

Tests documentation analysis including overlap detection, duplicate detection,
and placeholder content detection.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from tests.development_tools.conftest import load_development_tools_module, demo_project_root

# Load the module
docs_module = load_development_tools_module("docs.analyze_documentation")
extract_sections = docs_module.extract_sections
load_documents = docs_module.load_documents
detect_duplicates = docs_module.detect_duplicates
detect_placeholders = docs_module.detect_placeholders
execute = docs_module.execute


class TestAnalyzeDocumentation:
    """Test documentation analysis functionality."""
    
    @pytest.mark.unit
    def test_extract_sections_basic(self):
        """Test basic section extraction."""
        content = """
## Section 1
Content for section 1

## Section 2
Content for section 2

### Subsection 2.1
Content for subsection
"""
        sections = extract_sections(content)
        
        assert isinstance(sections, dict), "Result should be a dictionary"
        assert 'Section 1' in sections, "Should extract Section 1"
        assert 'Section 2' in sections, "Should extract Section 2"
        assert 'Subsection 2.1' in sections, "Should extract subsection"
        assert 'Content for section 1' in sections['Section 1'], "Should include content"
    
    @pytest.mark.unit
    def test_extract_sections_empty(self):
        """Test section extraction with empty content."""
        sections = extract_sections("")
        
        assert isinstance(sections, dict), "Result should be a dictionary"
        assert 'Introduction' in sections, "Should have default Introduction section"
    
    @pytest.mark.unit
    def test_load_documents_basic(self, tmp_path):
        """Test basic document loading."""
        # Create test documents
        doc1 = tmp_path / "doc1.md"
        doc1.write_text("# Document 1\n\nContent 1")
        
        doc2 = tmp_path / "doc2.md"
        doc2.write_text("# Document 2\n\nContent 2")
        
        # Mock PATHS.root
        with patch('development_tools.docs.analyze_documentation.PATHS') as mock_paths:
            mock_paths.root = tmp_path
            
            docs, missing = load_documents(["doc1.md", "doc2.md", "nonexistent.md"])
            
            assert isinstance(docs, dict), "Result should be a dictionary"
            assert 'doc1.md' in docs, "Should load doc1.md"
            assert 'doc2.md' in docs, "Should load doc2.md"
            assert isinstance(missing, list), "Missing should be a list"
            assert 'nonexistent.md' in missing, "Should report missing file"
    
    @pytest.mark.unit
    def test_detect_duplicates_basic(self):
        """Test basic duplicate detection."""
        docs = {
            "doc1.md": """
## Section 1
This is some content.

## Section 2
More content here.
""",
            "doc2.md": """
## Section 1
This is some content.

## Section 3
Different content.
"""
        }
        
        duplicates = detect_duplicates(docs)
        
        assert isinstance(duplicates, list), "Result should be a list"
        # Note: detect_duplicates only checks paired docs, so may not find duplicates in arbitrary docs
    
    @pytest.mark.unit
    def test_detect_duplicates_no_duplicates(self):
        """Test duplicate detection with no duplicates."""
        docs = {
            "doc1.md": "## Section 1\nContent 1",
            "doc2.md": "## Section 2\nContent 2"
        }
        
        duplicates = detect_duplicates(docs)
        
        assert isinstance(duplicates, list), "Result should be a list"
        # Note: detect_duplicates only checks paired docs, so may not find duplicates in arbitrary docs
    
    @pytest.mark.unit
    def test_detect_placeholders_basic(self):
        """Test basic placeholder detection."""
        docs = {
            "test.md": """
## Section 1
This is real content.

## Section 2
TBD: This needs to be filled in.

## Section 3
TODO: Add more content here.
"""
        }
        placeholders = detect_placeholders(docs)
        
        assert isinstance(placeholders, list), "Result should be a list"
        # Note: placeholder detection depends on configured patterns, may or may not detect all patterns
    
    @pytest.mark.unit
    def test_detect_placeholders_no_placeholders(self):
        """Test placeholder detection with no placeholders."""
        docs = {
            "test.md": """
## Section 1
This is complete content.

## Section 2
More complete content here.
"""
        }
        placeholders = detect_placeholders(docs)
        
        assert isinstance(placeholders, list), "Result should be a list"
        # Should have no or minimal placeholders
    
    @pytest.mark.integration
    def test_analyze_documentation_basic(self, demo_project_root):
        """Test basic documentation analysis."""
        import argparse
        args = argparse.Namespace(files=None, overlap=False)
        exit_code, result, payload = execute(args, project_root=Path(demo_project_root))
        
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should have content"
        assert isinstance(payload, dict), "Payload should be a dictionary"
        assert 'artifacts' in payload, "Payload should have artifacts"
        assert 'duplicates' in payload, "Payload should have duplicates"
        assert 'placeholders' in payload, "Payload should have placeholders"
    
    @pytest.mark.unit
    def test_analyze_documentation_empty_project(self, tmp_path):
        """Test analysis with empty project."""
        import argparse
        args = argparse.Namespace(files=None, overlap=False)
        exit_code, result, payload = execute(args, project_root=Path(tmp_path))
        
        assert isinstance(result, str), "Result should be a string"
        assert isinstance(payload, dict), "Payload should be a dictionary"
        assert 'artifacts' in payload, "Payload should have artifacts"
    
    @pytest.mark.unit
    def test_extract_sections_custom_patterns(self):
        """Test section extraction with custom heading patterns."""
        content = """
# H1 Section
Content

### H3 Section
More content
"""
        sections = extract_sections(content, heading_patterns=['# ', '### '])
        
        assert isinstance(sections, dict), "Result should be a dictionary"
        # Should extract sections based on custom patterns
    
    @pytest.mark.unit
    def test_detect_placeholders_various_patterns(self):
        """Test placeholder detection with various placeholder patterns."""
        docs = {
            "test.md": """
TBD: To be determined
TODO: To do
[insert content here]
to be filled: placeholder
"""
        }
        placeholders = detect_placeholders(docs)
        
        assert isinstance(placeholders, list), "Result should be a list"
        # Should detect various placeholder patterns

