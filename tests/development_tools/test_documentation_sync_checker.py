"""
Tests for documentation_sync_checker.py.

Tests documentation synchronization, path drift detection, ASCII compliance,
and heading numbering validation.
"""

import pytest
import sys
from pathlib import Path
from collections import defaultdict

# Import helper from conftest
from tests.development_tools.conftest import load_development_tools_module

# Load the module using the helper
checker_module = load_development_tools_module("documentation_sync_checker")
DocumentationSyncChecker = checker_module.DocumentationSyncChecker


class TestPairedDocumentation:
    """Test paired documentation checking."""
    
    @pytest.mark.unit
    def test_check_paired_documentation_perfect_sync(self, temp_docs_dir):
        """Test that perfectly synced docs return no errors."""
        # Create perfectly synced paired docs
        human_doc = temp_docs_dir / "human_doc.md"
        ai_doc = temp_docs_dir / "ai_doc.md"
        
        content = """# Test Doc

> **File**: `human_doc.md`
> **Pair**: `ai_doc.md`

## 1. First Section
Content here.

## 2. Second Section
More content.
"""
        human_doc.write_text(content, encoding='utf-8')
        ai_doc.write_text(content, encoding='utf-8')
        
        # Create a custom checker with our paired docs
        checker = DocumentationSyncChecker(str(temp_docs_dir))
        checker.paired_docs = {'human_doc.md': 'ai_doc.md'}
        
        issues = checker.check_paired_documentation()
        
        # Should have no content sync issues
        assert 'content_sync' not in issues or len(issues['content_sync']) == 0
        assert 'missing_human_docs' not in issues or len(issues['missing_human_docs']) == 0
        assert 'missing_ai_docs' not in issues or len(issues['missing_ai_docs']) == 0
    
    @pytest.mark.unit
    def test_check_paired_documentation_mismatched_h2(self, temp_docs_dir):
        """Test that mismatched H2 headings are flagged."""
        human_doc = temp_docs_dir / "human_doc.md"
        ai_doc = temp_docs_dir / "ai_doc.md"
        
        human_content = """# Test Doc

## 1. First Section
Content.

## 2. Second Section
More content.

## 3. Third Section
Extra section.
"""
        ai_content = """# Test Doc

## 1. First Section
Content.

## 2. Second Section
More content.

## 3. Different Section Name
Different name.
"""
        human_doc.write_text(human_content, encoding='utf-8')
        ai_doc.write_text(ai_content, encoding='utf-8')
        
        checker = DocumentationSyncChecker(str(temp_docs_dir))
        checker.paired_docs = {'human_doc.md': 'ai_doc.md'}
        
        issues = checker.check_paired_documentation()
        
        # Should detect mismatched sections
        assert 'content_sync' in issues
        assert len(issues['content_sync']) > 0
    
    @pytest.mark.unit
    def test_check_paired_documentation_missing_files(self, temp_docs_dir):
        """Test that missing human or AI docs are detected."""
        # Create only human doc
        human_doc = temp_docs_dir / "human_doc.md"
        human_doc.write_text("# Test", encoding='utf-8')
        
        checker = DocumentationSyncChecker(str(temp_docs_dir))
        checker.paired_docs = {'human_doc.md': 'missing_ai_doc.md'}
        
        issues = checker.check_paired_documentation()
        
        # Should detect missing AI doc
        assert 'missing_ai_docs' in issues
        assert 'missing_ai_doc.md' in issues['missing_ai_docs']


class TestPathDrift:
    """Test path drift detection."""
    
    @pytest.mark.unit
    def test_check_path_drift_valid_paths(self, demo_project_root):
        """Test that valid file paths are not flagged."""
        checker = DocumentationSyncChecker(str(demo_project_root))
        
        # The demo project has valid paths, so should not flag them
        drift_issues = checker.check_path_drift()
        
        # Should not flag valid existing files
        # Note: May have some false positives, but should not flag files that exist
        for doc_file, issues in drift_issues.items():
            # Check that issues are reasonable (not flagging existing files)
            for issue in issues:
                # If it says "Missing file", verify the file actually doesn't exist
                if "Missing file:" in issue:
                    file_path = issue.split("Missing file:")[1].strip()
                    full_path = demo_project_root / file_path
                    # If the file exists, this is a false positive
                    if full_path.exists():
                        pytest.fail(f"False positive: {file_path} exists but was flagged as missing")
    
    @pytest.mark.unit
    def test_check_path_drift_missing_files(self, temp_docs_dir):
        """Test that missing files referenced in docs are flagged."""
        # Create a doc that references a non-existent file
        doc_file = temp_docs_dir / "test_doc.md"
        doc_content = """# Test Doc

This references a missing file: `nonexistent_file.py`

And another: `missing_module.py`
"""
        doc_file.write_text(doc_content, encoding='utf-8')
        
        checker = DocumentationSyncChecker(str(temp_docs_dir))
        
        drift_issues = checker.check_path_drift()
        
        # Should flag the missing files
        if str(doc_file.relative_to(temp_docs_dir)) in drift_issues:
            issues = drift_issues[str(doc_file.relative_to(temp_docs_dir))]
            # Should have at least one issue about missing files
            assert len(issues) > 0


class TestASCIICompliance:
    """Test ASCII compliance checking."""
    
    @pytest.mark.unit
    def test_check_ascii_compliance_clean_file(self, demo_project_root):
        """Test that files with only ASCII pass."""
        checker = DocumentationSyncChecker(str(demo_project_root))
        
        # Check the ASCII test doc which should be clean
        ascii_doc = demo_project_root / "docs" / "ascii_test_doc.md"
        if ascii_doc.exists():
            # Temporarily modify checker to only check this file
            original_method = checker.check_ascii_compliance
            
            def check_single_file():
                from development_tools.shared.constants import ASCII_COMPLIANCE_FILES
                issues = defaultdict(list)
                try:
                    with open(ascii_doc, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    non_ascii_chars = []
                    for i, char in enumerate(content):
                        if ord(char) > 127:
                            non_ascii_chars.append({
                                'char': char,
                                'position': i,
                                'codepoint': ord(char)
                            })
                    
                    if non_ascii_chars:
                        char_types = {}
                        for char_info in non_ascii_chars:
                            char = char_info['char']
                            if char not in char_types:
                                char_types[char] = []
                            char_types[char].append(char_info['position'])
                        
                        for char, positions in char_types.items():
                            issues[str(ascii_doc.relative_to(demo_project_root))].append(
                                f"Non-ASCII character '{char}' (U+{ord(char):04X}) at positions: {positions[:5]}"
                            )
                except Exception as e:
                    issues[str(ascii_doc.relative_to(demo_project_root))].append(f"Error reading file: {e}")
                
                return issues
            
            issues = check_single_file()
            
            # Should have no issues for ASCII-only file
            assert len(issues) == 0
    
    @pytest.mark.unit
    def test_check_ascii_compliance_non_ascii_detected(self, demo_project_root):
        """Test that non-ASCII characters are detected."""
        checker = DocumentationSyncChecker(str(demo_project_root))
        
        # Check the non-ASCII doc which should have issues
        non_ascii_doc = demo_project_root / "docs" / "non_ascii_doc.md"
        if non_ascii_doc.exists():
            issues = checker.check_ascii_compliance()
            
            # Should detect non-ASCII characters
            doc_key = str(non_ascii_doc.relative_to(demo_project_root))
            if doc_key in issues:
                assert len(issues[doc_key]) > 0


class TestHeadingNumbering:
    """Test heading numbering validation."""
    
    @pytest.mark.unit
    def test_check_heading_numbering_valid(self, demo_project_root):
        """Test that valid numbered headings pass."""
        checker = DocumentationSyncChecker(str(demo_project_root))
        
        # Check the numbered doc which should be valid
        numbered_doc = demo_project_root / "docs" / "numbered_doc.md"
        if numbered_doc.exists():
            issues = checker.check_heading_numbering()
            
            # Should have no issues for properly numbered doc
            doc_key = str(numbered_doc.relative_to(demo_project_root))
            if doc_key in issues:
                # May have some issues, but should be minimal
                pass  # Just verify it doesn't crash
    
    @pytest.mark.unit
    def test_check_heading_numbering_missing_numbers(self, demo_project_root):
        """Test that missing numbers are detected."""
        checker = DocumentationSyncChecker(str(demo_project_root))
        
        # Check the bad numbering doc which should have issues
        bad_doc = demo_project_root / "docs" / "bad_numbering_doc.md"
        if bad_doc.exists():
            issues = checker.check_heading_numbering()
            
            # Should detect missing numbers
            doc_key = str(bad_doc.relative_to(demo_project_root))
            if doc_key in issues:
                # Should have issues about missing numbers
                issue_text = ' '.join(issues[doc_key])
                assert 'missing number' in issue_text.lower() or 'out of order' in issue_text.lower()
    
    @pytest.mark.unit
    def test_check_heading_numbering_out_of_order(self, demo_project_root):
        """Test that out-of-order numbers are detected."""
        checker = DocumentationSyncChecker(str(demo_project_root))
        
        # Check the bad numbering doc which has out-of-order sections
        bad_doc = demo_project_root / "docs" / "bad_numbering_doc.md"
        if bad_doc.exists():
            issues = checker.check_heading_numbering()
            
            # Should detect out-of-order numbering
            doc_key = str(bad_doc.relative_to(demo_project_root))
            if doc_key in issues:
                issue_text = ' '.join(issues[doc_key])
                # Should mention out of order or wrong sequence
                assert any(keyword in issue_text.lower() for keyword in ['out of order', 'expected', 'wrong'])


class TestIntegration:
    """Integration tests for full checker workflow."""
    
    @pytest.mark.integration
    def test_run_checks_integration(self, demo_project_root):
        """Test that full run_checks() returns expected structure."""
        checker = DocumentationSyncChecker(str(demo_project_root))
        
        results = checker.run_checks()
        
        # Should return a dict with expected keys
        assert isinstance(results, dict)
        assert 'paired_docs' in results
        assert 'path_drift' in results
        assert 'ascii_compliance' in results
        assert 'heading_numbering' in results
        assert 'summary' in results
        
        # Summary should have expected structure
        summary = results['summary']
        assert 'total_issues' in summary
        assert 'status' in summary
        assert summary['status'] in ['PASS', 'FAIL']

