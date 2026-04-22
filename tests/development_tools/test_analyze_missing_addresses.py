"""
Tests for analyze_missing_addresses.py.

Tests missing address detection in documentation files.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.development_tools.conftest import (
    load_development_tools_module,
)

# Load the module
missing_addresses_module = load_development_tools_module(
    "docs.analyze_missing_addresses"
)
MissingAddressAnalyzer = missing_addresses_module.MissingAddressAnalyzer


class TestAnalyzeMissingAddresses:
    """Test missing address detection functionality."""

    @pytest.mark.unit
    def test_check_missing_addresses_basic(self, tmp_path):
        """Test basic missing address detection."""
        # Create a documentation file without file address
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text(
            """
# Test Documentation

This is a test document without a file address in the header.
"""
        )

        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_missing_addresses()

        assert isinstance(results, dict), "Result should be a dictionary"
        assert "test_doc.md" in results, "Test document should be in results"
        assert (
            "Missing file address in header" in results["test_doc.md"]
        ), "Missing file address in header should be in results"
        # File may or may not be flagged depending on analyzer logic

    @pytest.mark.unit
    def test_check_missing_addresses_with_address(self, tmp_path):
        """Test detection with file address present."""
        # Create a documentation file with file address
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text(
            """
> **File**: `test_doc.md`

# Test Documentation

This document has a file address.
"""
        )

        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_missing_addresses()

        assert isinstance(results, dict), "Result should be a dictionary"
        assert "test_doc.md" not in results, "Test document should not be in results"
        # File should not be flagged if address is present

    @pytest.mark.unit
    def test_check_missing_addresses_empty_file(self, tmp_path):
        """Test detection with empty file."""
        doc_file = tmp_path / "empty.md"
        doc_file.write_text("")

        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_missing_addresses()

        assert isinstance(results, dict), "Result should be a dictionary"
        assert "empty.md" in results, "Empty document should be in results"
        assert (
            "Missing file address in header" in results["empty.md"]
        ), "Missing file address in header should be in results"

    @pytest.mark.unit
    def test_check_missing_addresses_generated_file(self, tmp_path):
        """Test that generated files are excluded."""
        # Create a generated file (with Generated marker)
        doc_file = tmp_path / "generated.md"
        doc_file.write_text(
            """
**Generated**: This file is auto-generated.

# Generated Documentation

This file should be excluded from missing address checks.
"""
        )

        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_missing_addresses()

        assert isinstance(results, dict), "Result should be a dictionary"
        assert "generated.md" not in results
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
        assert not any(
            ".cursor" in k for k in results
        ), ".cursor/ files should be excluded"
        # .cursor/ files should be excluded

    @pytest.mark.integration
    def test_check_missing_addresses_demo_project(
        self, demo_project_root, test_config_path
    ):
        """Test detection on demo project."""
        analyzer = MissingAddressAnalyzer(
            project_root=str(demo_project_root),
            config_path=test_config_path,
            use_cache=False,
        )
        results = analyzer.check_missing_addresses()

        assert isinstance(results, dict), "Result should be a dictionary"

    @pytest.mark.unit
    def test_is_generated_file_utility(self, tmp_path):
        """Test shared generated-file detection utility."""
        exclusion_utilities = load_development_tools_module(
            "shared.exclusion_utilities"
        )
        is_generated_file = exclusion_utilities.is_generated_file

        generated_file = tmp_path / "generated.md"
        generated_file.write_text("**Generated**: This is generated.")
        assert is_generated_file(str(generated_file)) is True

        regular_file = tmp_path / "regular.md"
        regular_file.write_text("# Regular File")
        assert is_generated_file(str(regular_file)) is False

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
        assert results1 == results2

    @pytest.mark.unit
    def test_check_missing_addresses_no_cache(self, tmp_path):
        """Test with cache disabled."""
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("# Test\n\nNo address.")

        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        results = analyzer.check_missing_addresses()

        assert isinstance(results, dict), "Result should be a dictionary"

    @pytest.mark.unit
    def test_run_analysis_status_clean(self, tmp_path):
        """No missing addresses yields CLEAN summary status."""
        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        payload = analyzer.run_analysis()
        assert payload["summary"]["status"] == "CLEAN"
        assert payload["summary"]["total_issues"] == 0
        assert payload["summary"]["files_affected"] == 0

    @pytest.mark.unit
    def test_run_analysis_status_needs_attention(self, tmp_path):
        """Between one and four issues yields NEEDS_ATTENTION."""
        for i in range(3):
            (tmp_path / f"gap_{i}.md").write_text("# No address header\n")
        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        payload = analyzer.run_analysis()
        assert payload["summary"]["status"] == "NEEDS_ATTENTION"
        assert payload["summary"]["total_issues"] == 3

    @pytest.mark.unit
    def test_run_analysis_status_critical(self, tmp_path):
        """Five or more issues yields CRITICAL."""
        for i in range(5):
            (tmp_path / f"many_{i}.md").write_text("# x\n")
        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        payload = analyzer.run_analysis()
        assert payload["summary"]["status"] == "CRITICAL"
        assert payload["summary"]["total_issues"] == 5

    @pytest.mark.unit
    def test_check_missing_addresses_read_error_recorded(self, tmp_path):
        """Unreadable files surface as error issues and appear in results."""
        doc = tmp_path / "broken.md"
        doc.write_text("placeholder", encoding="utf-8")
        analyzer = MissingAddressAnalyzer(project_root=str(tmp_path), use_cache=False)
        real_open = open

        def selective_open(path, *args, **kwargs):
            if Path(path).name == "broken.md":
                raise OSError("simulated read failure")
            return real_open(path, *args, **kwargs)

        with patch("builtins.open", selective_open):
            results = analyzer.check_missing_addresses()

        assert "broken.md" in results
        assert any("Error reading file" in msg for msg in results["broken.md"])

    @pytest.mark.unit
    def test_main_json_outputs_and_exits_zero(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["analyze_missing_addresses", "--json"])
        with patch.object(
            missing_addresses_module.config,
            "get_project_root",
            return_value=str(tmp_path),
        ):
            code = missing_addresses_module.main()
        assert code == 0
        parsed = json.loads(capsys.readouterr().out)
        assert "summary" in parsed
        assert parsed["summary"]["status"] == "CLEAN"

    @pytest.mark.unit
    def test_main_human_exits_one_when_issues(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["analyze_missing_addresses"])
        (tmp_path / "naked.md").write_text("# no header address\n")
        with patch.object(
            missing_addresses_module.config,
            "get_project_root",
            return_value=str(tmp_path),
        ):
            code = missing_addresses_module.main()
        assert code == 1
        out = capsys.readouterr().out
        assert "Missing Address" in out or "missing" in out.lower()

    @pytest.mark.unit
    def test_main_human_exits_zero_when_clean(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["analyze_missing_addresses"])
        with patch.object(
            missing_addresses_module.config,
            "get_project_root",
            return_value=str(tmp_path),
        ):
            code = missing_addresses_module.main()
        assert code == 0
        assert "have file addresses" in capsys.readouterr().out.lower()
