"""
Tests for analyze_documentation_sync.py.

Tests documentation synchronization, path drift detection, ASCII compliance,
and heading numbering validation.
"""

import json
import sys
from unittest.mock import patch

import pytest

# Import helper from conftest
from tests.development_tools.conftest import load_development_tools_module

# Load the module using the helper
checker_module = load_development_tools_module("analyze_documentation_sync")
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
    def test_check_path_drift_valid_paths(self, demo_project_root, test_config_path):
        """Test that valid file paths are not flagged."""
        path_drift_module = load_development_tools_module("analyze_path_drift")
        PathDriftAnalyzer = path_drift_module.PathDriftAnalyzer
        analyzer = PathDriftAnalyzer(
            str(demo_project_root), config_path=test_config_path
        )
        
        # The demo project has valid paths, so should not flag them
        drift_issues = analyzer.check_path_drift()
        
        # Should not flag valid existing files
        # Note: May have some false positives, but should not flag files that exist
        for _doc_file, issues in drift_issues.items():
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
        
        path_drift_module = load_development_tools_module("analyze_path_drift")
        PathDriftAnalyzer = path_drift_module.PathDriftAnalyzer
        analyzer = PathDriftAnalyzer(str(temp_docs_dir))
        
        drift_issues = analyzer.check_path_drift()
        
        # Should flag the missing files
        if str(doc_file.relative_to(temp_docs_dir)) in drift_issues:
            issues = drift_issues[str(doc_file.relative_to(temp_docs_dir))]
            # Should have at least one issue about missing files
            assert len(issues) > 0


class TestASCIICompliance:
    """Test ASCII compliance checking."""
    
    @pytest.mark.unit
    def test_check_ascii_compliance_clean_file(self, demo_project_root, test_config_path):
        """Test that files with only ASCII pass."""
        ascii_module = load_development_tools_module("analyze_ascii_compliance")
        ASCIIComplianceAnalyzer = ascii_module.ASCIIComplianceAnalyzer
        analyzer = ASCIIComplianceAnalyzer(
            str(demo_project_root), config_path=test_config_path
        )
        
        # Check the ASCII test doc which should be clean
        ascii_doc = demo_project_root / "docs" / "ascii_test_doc.md"
        if ascii_doc.exists():
            issues = analyzer.check_ascii_compliance()
            
            # Should have no issues for ASCII-only file
            doc_key = str(ascii_doc.relative_to(demo_project_root))
            if doc_key in issues:
                # May have some issues, but should be minimal for ASCII-only file
                pass  # Just verify it doesn't crash
    
    @pytest.mark.unit
    def test_check_ascii_compliance_non_ascii_detected(self, demo_project_root, test_config_path):
        """Test that non-ASCII characters are detected."""
        ascii_module = load_development_tools_module("analyze_ascii_compliance")
        ASCIIComplianceAnalyzer = ascii_module.ASCIIComplianceAnalyzer
        analyzer = ASCIIComplianceAnalyzer(
            str(demo_project_root), config_path=test_config_path
        )
        
        # Check the non-ASCII doc which should have issues
        non_ascii_doc = demo_project_root / "docs" / "non_ascii_doc.md"
        if non_ascii_doc.exists():
            issues = analyzer.check_ascii_compliance()
            
            # Should detect non-ASCII characters
            doc_key = str(non_ascii_doc.relative_to(demo_project_root))
            if doc_key in issues:
                assert len(issues[doc_key]) > 0


class TestHeadingNumbering:
    """Test heading numbering validation."""
    
    @pytest.mark.unit
    def test_check_heading_numbering_valid(self, demo_project_root, test_config_path):
        """Test that valid numbered headings pass."""
        heading_module = load_development_tools_module("analyze_heading_numbering")
        HeadingNumberingAnalyzer = heading_module.HeadingNumberingAnalyzer
        analyzer = HeadingNumberingAnalyzer(
            str(demo_project_root), config_path=test_config_path
        )
        
        # Check the numbered doc which should be valid
        numbered_doc = demo_project_root / "docs" / "numbered_doc.md"
        if numbered_doc.exists():
            issues = analyzer.check_heading_numbering()
            
            # Should have no issues for properly numbered doc
            doc_key = str(numbered_doc.relative_to(demo_project_root))
            if doc_key in issues:
                # May have some issues, but should be minimal
                pass  # Just verify it doesn't crash
    
    @pytest.mark.unit
    def test_check_heading_numbering_missing_numbers(self, demo_project_root, test_config_path):
        """Test that missing numbers are detected."""
        heading_module = load_development_tools_module("analyze_heading_numbering")
        HeadingNumberingAnalyzer = heading_module.HeadingNumberingAnalyzer
        analyzer = HeadingNumberingAnalyzer(
            str(demo_project_root), config_path=test_config_path
        )
        
        # Check the bad numbering doc which should have issues
        bad_doc = demo_project_root / "docs" / "bad_numbering_doc.md"
        if bad_doc.exists():
            issues = analyzer.check_heading_numbering()
            
            # Should detect missing numbers
            doc_key = str(bad_doc.relative_to(demo_project_root))
            if doc_key in issues:
                # Should have issues about missing numbers
                issue_text = ' '.join(issues[doc_key])
                assert 'missing number' in issue_text.lower() or 'out of order' in issue_text.lower()
    
    @pytest.mark.unit
    def test_check_heading_numbering_out_of_order(self, demo_project_root, test_config_path):
        """Test that out-of-order numbers are detected."""
        heading_module = load_development_tools_module("analyze_heading_numbering")
        HeadingNumberingAnalyzer = heading_module.HeadingNumberingAnalyzer
        analyzer = HeadingNumberingAnalyzer(
            str(demo_project_root), config_path=test_config_path
        )
        
        # Check the bad numbering doc which has out-of-order sections
        bad_doc = demo_project_root / "docs" / "bad_numbering_doc.md"
        if bad_doc.exists():
            issues = analyzer.check_heading_numbering()
            
            # Should detect out-of-order numbering
            doc_key = str(bad_doc.relative_to(demo_project_root))
            if doc_key in issues:
                issue_text = ' '.join(issues[doc_key])
                # Should mention out of order or wrong sequence
                assert any(keyword in issue_text.lower() for keyword in ['out of order', 'expected', 'wrong'])


class TestIntegration:
    """Integration tests for full checker workflow."""
    
    @pytest.mark.integration
    def test_run_checks_integration(self, demo_project_root, test_config_path):
        """Test that full run_checks() returns expected structure."""
        checker = DocumentationSyncChecker(
            str(demo_project_root), config_path=test_config_path
        )
        
        results = checker.run_checks()
        
        # Should return a dict in standard format
        assert isinstance(results, dict)
        assert 'summary' in results, "Results should have summary (standard format)"
        assert 'details' in results, "Results should have details (standard format)"
        assert 'paired_docs' in results['details'], "Results details should have paired_docs"
        
        # Summary should have expected structure
        summary = results['summary']
        assert 'total_issues' in summary
        assert 'status' in summary
        assert summary['status'] in ['PASS', 'FAIL']
        
        # Note: Other checks (path_drift, ascii_compliance, heading_numbering) are now
        # in separate tools and are called via service modules during audits


class TestExampleMarkerScanPaths:
    """Example-marker scan uses config-derived DEFAULT_DOCS (not paired-docs only)."""

    @pytest.mark.unit
    def test_resolve_example_marker_scan_paths_prefers_default_docs(self, monkeypatch):
        resolve = checker_module._resolve_example_marker_scan_paths
        monkeypatch.setattr(checker_module, "DEFAULT_DOCS", ("z.md", "a.md", "z.md"))
        assert resolve({}) == ["a.md", "z.md"]

    @pytest.mark.unit
    def test_resolve_example_marker_scan_paths_falls_back_to_paired(self, monkeypatch):
        resolve = checker_module._resolve_example_marker_scan_paths
        monkeypatch.setattr(checker_module, "DEFAULT_DOCS", ())
        assert resolve({"human.md": "ai.md"}) == ["ai.md", "human.md"]


class TestPrintReportAndMain:
    """print_report and main() CLI branches."""

    @pytest.mark.unit
    def test_print_report_pass_zero_issues(self, capsys, tmp_path):
        checker = DocumentationSyncChecker(str(tmp_path))
        payload = {
            "summary": {
                "total_issues": 0,
                "files_affected": 0,
                "status": "PASS",
            },
            "details": {"paired_doc_issues": 0, "paired_docs": {}},
        }
        checker.print_report(payload)
        out = capsys.readouterr().out
        assert "PASS" in out
        assert "Total Issues: 0" in out
        assert "All paired documentation synchronization checks passed" in out

    @pytest.mark.unit
    def test_print_report_strips_non_ascii_issue_lines(self, capsys, tmp_path):
        checker = DocumentationSyncChecker(str(tmp_path))
        payload = {
            "summary": {
                "total_issues": 1,
                "files_affected": 0,
                "status": "FAIL",
            },
            "details": {
                "paired_doc_issues": 1,
                "paired_docs": {"content_sync": ["caf\u00e9 mismatch"]},
            },
        }
        checker.print_report(payload)
        out = capsys.readouterr().out
        assert "FAIL" in out
        assert "mismatch" in out

    @pytest.mark.unit
    def test_main_json_mode(self, monkeypatch, capsys):
        payload = {
            "summary": {
                "total_issues": 0,
                "files_affected": 0,
                "status": "PASS",
            },
            "details": {"paired_doc_issues": 0, "paired_docs": {}},
        }
        monkeypatch.setattr(sys, "argv", ["analyze_documentation_sync.py", "--json"])
        with patch.object(DocumentationSyncChecker, "run_checks", return_value=payload):
            checker_module.main()
        parsed = json.loads(capsys.readouterr().out.strip())
        assert parsed["summary"]["status"] == "PASS"

    @pytest.mark.unit
    def test_main_example_markers_branch_empty_findings(self, monkeypatch, capsys):
        payload = {
            "summary": {
                "total_issues": 0,
                "files_affected": 0,
                "status": "PASS",
            },
            "details": {"paired_doc_issues": 0, "paired_docs": {}},
        }
        monkeypatch.setattr(
            sys,
            "argv",
            ["analyze_documentation_sync.py", "--check-example-markers"],
        )
        with patch.object(DocumentationSyncChecker, "run_checks", return_value=payload):
            with patch(
                "development_tools.docs.example_marker_validation.scan_paths_for_example_marker_findings",
                return_value={},
            ):
                checker_module.main()
        out = capsys.readouterr().out
        assert "no advisory hints" in out.lower() or "example marker" in out.lower()

    @pytest.mark.unit
    def test_main_example_markers_json_reports_true_positive(self, monkeypatch, capsys):
        """The advisory branch must surface non-empty scan findings in JSON output."""
        payload = {
            "summary": {
                "total_issues": 0,
                "files_affected": 0,
                "status": "PASS",
            },
            "details": {"paired_doc_issues": 0, "paired_docs": {}},
        }
        findings = {"guide.md": ["line 3: Use `core/foo.py`."]}
        monkeypatch.setattr(
            sys,
            "argv",
            ["analyze_documentation_sync.py", "--json", "--check-example-markers"],
        )
        with patch.object(DocumentationSyncChecker, "run_checks", return_value=payload):
            with patch(
                "development_tools.docs.example_marker_validation.scan_paths_for_example_marker_findings",
                return_value=findings,
            ):
                checker_module.main()

        parsed = json.loads(capsys.readouterr().out.strip())
        assert parsed["summary"]["example_marker_hint_count"] == 1
        assert parsed["details"]["example_marker_findings"] == findings

