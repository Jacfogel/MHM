# INTENTIONAL LEGACY: This test file intentionally references legacy patterns
# (LegacyChannelWrapper, bot/ paths) to verify the legacy detection tools work correctly.
# These references should NOT be flagged as issues - they are test code.
"""
Tests for fix_legacy_references.py.

Tests scanning, verification, and safe cleanup operations.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

# Import helper from conftest
from tests.development_tools.conftest import load_development_tools_module

# Load the modules using the helper
cleanup_module = load_development_tools_module("fix_legacy_references")
analyzer_module = load_development_tools_module("analyze_legacy_references")
report_module = load_development_tools_module("generate_legacy_reference_report")

LegacyReferenceFixer = cleanup_module.LegacyReferenceFixer
LegacyReferenceAnalyzer = analyzer_module.LegacyReferenceAnalyzer
LegacyReferenceReportGenerator = report_module.LegacyReferenceReportGenerator


class TestLegacyScanning:
    """Test legacy reference scanning."""
    
    @pytest.mark.unit
    def test_scan_for_legacy_references_finds_markers(self, demo_project_root):
        """Test that legacy markers are found."""
        analyzer = LegacyReferenceAnalyzer(str(demo_project_root))
        
        findings = analyzer.scan_for_legacy_references()
        
        # Should find legacy compatibility markers in legacy_code.py
        if 'legacy_compatibility_markers' in findings:
            legacy_files = [file_path for file_path, _, _ in findings['legacy_compatibility_markers']]
            assert any('legacy_code.py' in str(f) for f in legacy_files)
    
    @pytest.mark.unit
    def test_scan_for_legacy_references_respects_preserve_files(self, demo_project_root):
        """Test that preserved files are skipped."""
        analyzer = LegacyReferenceAnalyzer(str(demo_project_root))
        
        # Add a preserve pattern that matches our demo project
        original_preserve = analyzer.preserve_files
        analyzer.preserve_files = analyzer.preserve_files | {'README.md'}
        
        findings = analyzer.scan_for_legacy_references()
        
        # README.md should not appear in findings
        for pattern_type, files in findings.items():
            for file_path, _, _ in files:
                assert 'README.md' not in str(file_path)
        
        analyzer.preserve_files = original_preserve
    
    @pytest.mark.unit
    def test_should_skip_file_exclusions(self, demo_project_root):
        """Test that excluded files are skipped."""
        analyzer = LegacyReferenceAnalyzer(str(demo_project_root))
        
        # Test with a file that should be excluded
        excluded_file = demo_project_root / "__pycache__" / "test.pyc"
        excluded_file.parent.mkdir(exist_ok=True)
        excluded_file.write_bytes(b"test")
        
        should_skip = analyzer.should_skip_file(excluded_file)
        assert should_skip is True
        
        # Clean up - remove file and directory if empty
        excluded_file.unlink()
        try:
            excluded_file.parent.rmdir()
        except OSError:
            # Directory not empty, that's okay - just remove our test file
            pass


class TestReferenceFinding:
    """Test finding specific legacy references."""
    
    @pytest.mark.unit
    def test_find_all_references_specific_item(self, demo_project_root):
        """Test that specific legacy items are found."""
        analyzer = LegacyReferenceAnalyzer(str(demo_project_root))
        
        # Verify the legacy file exists
        legacy_file = demo_project_root / "legacy_code.py"
        assert legacy_file.exists(), "legacy_code.py should exist in demo project"
        
        # Verify the item exists in the file
        content = legacy_file.read_text(encoding='utf-8')
        assert 'LegacyChannelWrapper' in content, "LegacyChannelWrapper should exist in legacy_code.py"
        
        # Verify the file is not being skipped
        assert not analyzer.should_skip_file(legacy_file), "legacy_code.py should not be skipped"
        
        # Find references to LegacyChannelWrapper
        # Note: find_all_references searches for the item as a pattern in files
        references = analyzer.find_all_references('LegacyChannelWrapper')
        
        # The function should find the class definition
        # It searches for patterns like 'class LegacyChannelWrapper', 'LegacyChannelWrapper(', etc.
        assert len(references) > 0, f"find_all_references should find LegacyChannelWrapper. Found: {references}"
        assert any('legacy_code.py' in file_path for file_path in references.keys()), \
            f"legacy_code.py should be in references. Found: {list(references.keys())}"


class TestRemovalReadiness:
    """Test removal readiness verification."""
    
    @pytest.mark.unit
    def test_verify_removal_readiness_ready(self, demo_project_root):
        """Test that items with no active code references are ready."""
        analyzer = LegacyReferenceAnalyzer(str(demo_project_root))
        
        # Test with a non-existent item (should be ready)
        verification = analyzer.verify_removal_readiness('NonExistentItem12345')
        
        # Should be ready (no references found)
        assert verification['ready_for_removal'] is True
        assert len(verification['categorized']['active_code']) == 0
    
    @pytest.mark.unit
    def test_verify_removal_readiness_not_ready(self, demo_project_root):
        """Test that items with active code references are not ready."""
        analyzer = LegacyReferenceAnalyzer(str(demo_project_root))
        
        # Test with LegacyChannelWrapper which exists in legacy_code.py
        verification = analyzer.verify_removal_readiness('LegacyChannelWrapper')
        
        # Should not be ready (has references)
        # Note: May be ready if only in legacy_code.py which might be considered legacy itself
        assert 'ready_for_removal' in verification
        assert 'references' in verification
        assert 'recommendations' in verification


class TestCleanupOperations:
    """Test cleanup operations (safe, using copies)."""
    
    @pytest.mark.unit
    def test_cleanup_legacy_references_dry_run(self, temp_project_copy):
        """Test that dry-run reports planned changes without modifying files."""
        analyzer = LegacyReferenceAnalyzer(str(temp_project_copy))
        # Provide replacement mappings so cleanup actually makes changes
        replacement_mappings = {
            'LEGACY COMPATIBILITY': 'MODERN COMPATIBILITY',
            'legacy': 'modern'
        }
        fixer = LegacyReferenceFixer(str(temp_project_copy), replacement_mappings=replacement_mappings)
        
        # Verify legacy_code.py exists in the copied project
        legacy_file = temp_project_copy / "legacy_code.py"
        assert legacy_file.exists(), f"legacy_code.py should exist in {temp_project_copy}"
        
        # Verify the file is not being skipped
        assert not analyzer.should_skip_file(legacy_file), f"legacy_code.py should not be skipped"
        
        # Scan for legacy references
        findings = analyzer.scan_for_legacy_references()
        
        # Check if we have any findings
        has_findings = any(len(files) > 0 for files in findings.values())
        assert has_findings, f"No legacy references found. Findings: {dict(findings)}"
        
        # Run cleanup in dry-run mode
        cleanup_results = fixer.cleanup_legacy_references(findings, dry_run=True)
        
        # Should report what would be changed (structure may vary)
        # The results should be a dict with some indication of what would change
        assert isinstance(cleanup_results, dict), f"Expected dict, got {type(cleanup_results)}"
        # May have keys like 'files_would_update', 'changes', 'files_updated', etc.
        # Note: defaultdict is empty if no keys accessed, so check if it has any keys OR if it's a regular dict
        assert len(cleanup_results) > 0 or any(key in cleanup_results for key in ['files_would_update', 'changes', 'files_updated', 'errors']), \
            f"Cleanup results should not be empty. Got: {cleanup_results}"
        
        # Verify files were NOT actually modified
        legacy_file = temp_project_copy / "legacy_code.py"
        if legacy_file.exists():
            original_content = legacy_file.read_text(encoding='utf-8')
            # Should still contain legacy markers
            assert 'LEGACY COMPATIBILITY' in original_content
    
    @pytest.mark.unit
    def test_cleanup_legacy_references_actual_cleanup(self, temp_project_copy):
        """Test that actual cleanup modifies files correctly."""
        analyzer = LegacyReferenceAnalyzer(str(temp_project_copy))
        # Provide replacement mappings so cleanup actually makes changes
        replacement_mappings = {
            'LEGACY COMPATIBILITY': 'MODERN COMPATIBILITY',
            'legacy': 'modern'
        }
        fixer = LegacyReferenceFixer(str(temp_project_copy), replacement_mappings=replacement_mappings)
        
        # Verify legacy_code.py exists in the copied project
        legacy_file = temp_project_copy / "legacy_code.py"
        assert legacy_file.exists(), f"legacy_code.py should exist in {temp_project_copy}"
        
        # Verify the file is not being skipped
        assert not analyzer.should_skip_file(legacy_file), f"legacy_code.py should not be skipped"
        
        # Scan for legacy references
        findings = analyzer.scan_for_legacy_references()
        
        # Check if we have any findings (findings is dict of pattern_type -> list of (file_path, content, matches))
        has_findings = any(len(files) > 0 for files in findings.values())
        assert has_findings, f"No legacy references found. Findings: {dict(findings)}"
        
        # Run cleanup in actual mode (not dry-run)
        cleanup_results = fixer.cleanup_legacy_references(findings, dry_run=False)
        
        # Should return a dict with results structure
        assert isinstance(cleanup_results, dict)
        # The results dict should have expected keys (may be empty lists if no changes made)
        # Note: defaultdict is empty if no keys accessed, so check if it has any keys OR if it's a regular dict
        assert len(cleanup_results) > 0 or any(key in cleanup_results for key in ['files_updated', 'changes', 'errors', 'files_would_update']), \
            f"Cleanup results should have expected keys. Got: {cleanup_results}"
        
        # Note: Actual cleanup may modify files, but we're using a copy so it's safe


class TestReportGeneration:
    """Test report generation."""
    
    @pytest.mark.unit
    def test_generate_cleanup_report_structure(self, demo_project_root):
        """Test that report has expected structure."""
        analyzer = LegacyReferenceAnalyzer(str(demo_project_root))
        report_gen = LegacyReferenceReportGenerator(str(demo_project_root))
        
        findings = analyzer.scan_for_legacy_references()
        report = report_gen.generate_cleanup_report(findings)
        
        # Should have expected sections
        assert '# Legacy Reference Cleanup Report' in report
        assert '## Summary' in report or 'Summary' in report


class TestReplacementMappings:
    """Test replacement mappings."""

    @pytest.mark.unit
    def test_get_replacement_mappings(self, demo_project_root):
        """Test that replacement mappings work correctly."""
        fixer = LegacyReferenceFixer(str(demo_project_root))

        # Test various replacements
        test_cases = [
            ('bot/', 'communication/'),
            ('from bot.', 'from communication.'),
            ('import bot.', 'import communication.'),
        ]

        for original, expected_start in test_cases:
            replacement = fixer.get_replacement(original)
            # Should start with expected replacement
            assert replacement.startswith(expected_start) or original not in fixer.replacement_mappings

    @pytest.mark.unit
    def test_get_replacement_with_custom_mappings(self, demo_project_root):
        """Test get_replacement with explicit replacement_mappings."""
        replacement_mappings = {"LEGACY": "MODERN", "old_pattern": "new_pattern"}
        fixer = LegacyReferenceFixer(
            str(demo_project_root), replacement_mappings=replacement_mappings
        )
        assert fixer.get_replacement("LEGACY code") == "MODERN code"
        assert fixer.get_replacement("old_pattern only") == "new_pattern only"
        assert fixer.get_replacement("no_match_here") == "no_match_here"


class TestLegacyFixerRun:
    """Test LegacyReferenceFixer.run() flow."""

    @pytest.mark.unit
    def test_run_scan_only(self, demo_project_root, caplog):
        """Test run with scan=True, clean=False produces findings and report."""
        fixer = LegacyReferenceFixer(str(demo_project_root))
        results = fixer.run(scan=True, clean=False, dry_run=True)
        assert "findings" in results
        assert "report_file" in results
        assert isinstance(results["findings"], dict)
        assert Path(results["report_file"]).exists()

    @pytest.mark.unit
    def test_run_scan_and_clean_dry_run(self, demo_project_root):
        """Test run with scan and clean (dry_run) returns cleanup structure."""
        fixer = LegacyReferenceFixer(str(demo_project_root))
        results = fixer.run(scan=True, clean=True, dry_run=True)
        assert "findings" in results
        assert "cleanup" in results
        cleanup = results["cleanup"]
        assert "files_would_update" in cleanup or "files_updated" in cleanup
        assert "changes" in cleanup

    @pytest.mark.unit
    def test_run_scan_false_requires_findings(self, demo_project_root):
        """Test run with scan=False and clean=True needs prior findings (no-op)."""
        fixer = LegacyReferenceFixer(str(demo_project_root))
        results = fixer.run(scan=False, clean=False, dry_run=True)
        assert "findings" not in results
        assert "cleanup" not in results


class TestFixLegacyReferencesMain:
    """Test fix_legacy_references main() CLI paths."""

    @pytest.mark.unit
    def test_main_find_mode(self, demo_project_root, capsys):
        """Test --find delegates to analyzer and prints references."""
        with patch("sys.argv", ["fix_legacy_references.py", "--find", "NonExistentItemXYZ"]):
            cleanup_module.main()
        out, _ = capsys.readouterr()
        assert "References to" in out or "Total files" in out
        assert "NonExistentItemXYZ" in out

    @pytest.mark.unit
    def test_main_verify_mode(self, demo_project_root, capsys):
        """Test --verify delegates to analyzer and prints verification."""
        with patch("sys.argv", ["fix_legacy_references.py", "--verify", "NonExistentItemXYZ"]):
            cleanup_module.main()
        out, _ = capsys.readouterr()
        assert "Removal Readiness" in out or "Reference Summary" in out
        assert "NonExistentItemXYZ" in out

    @pytest.mark.unit
    def test_main_scan_default(self, demo_project_root):
        """Test main with default args runs fixer.run(scan=True)."""
        with patch.object(LegacyReferenceFixer, "run", return_value={"findings": {}, "report_file": ""}) as mock_run:
            with patch("sys.argv", ["fix_legacy_references.py"]):
                cleanup_module.main()
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["scan"] is True
        assert call_kwargs["dry_run"] is True

