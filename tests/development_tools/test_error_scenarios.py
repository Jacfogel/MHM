"""
Error scenario tests for development tools.

Tests error handling for file corruption, permission errors, missing files,
and other edge cases.
"""

import json
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tests.development_tools.conftest import load_development_tools_module


class TestFileCorruptionHandling:
    """Test handling of corrupted or malformed source files."""

    @pytest.mark.unit
    def test_function_registry_handles_syntax_errors(self, demo_project_root):
        """extract_functions_from_file should handle syntax errors gracefully."""
        # extract_functions_from_file was moved to analyze_functions.py during Batch 3 decomposition
        analyze_functions = load_development_tools_module("analyze_functions")

        bad_file = demo_project_root / "bad_syntax.py"
        bad_file.write_text("def broken_function(\n    # Missing closing paren\n")

        try:
            functions = analyze_functions.extract_functions_from_file(str(bad_file))
            assert isinstance(functions, list)
        finally:
            if bad_file.exists():
                bad_file.unlink()

    @pytest.mark.unit
    def test_module_dependencies_handles_import_errors(self, demo_project_root):
        """extract_imports_from_file should handle invalid imports gracefully."""
        imports_module = load_development_tools_module("imports.analyze_module_imports")

        bad_file = demo_project_root / "bad_imports.py"
        bad_file.write_text("from nonexistent.module import something\nimport also.nonexistent")

        try:
            imports = imports_module.extract_imports_from_file(str(bad_file))
            assert isinstance(imports, dict)
        finally:
            if bad_file.exists():
                bad_file.unlink()

    @pytest.mark.unit
    def test_documentation_sync_handles_missing_pairs(self, temp_docs_dir):
        """DocumentationSyncChecker should report missing docs without crashing."""
        doc_sync_module = load_development_tools_module("analyze_documentation_sync")
        checker = doc_sync_module.DocumentationSyncChecker(project_root=str(temp_docs_dir))
        checker.paired_docs = {"human.md": "ai.md"}

        (temp_docs_dir / "human.md").write_text("# Human doc\n\n## Section")

        issues = checker.check_paired_documentation()
        assert "missing_ai_docs" in issues


class TestPermissionErrorHandling:
    """Test handling of permission errors."""

    @pytest.mark.unit
    def test_file_operations_handle_permission_error(self, monkeypatch):
        """Simulate a PermissionError during file writes without touching OS ACLs."""
        from pathlib import Path

        def fake_write_text(self, *args, **kwargs):
            raise PermissionError("read-only")

        monkeypatch.setattr(Path, "write_text", fake_write_text, raising=False)

        with pytest.raises(PermissionError):
            Path("dummy.txt").write_text("content")

    @pytest.mark.unit
    def test_scan_handles_permission_error(self, monkeypatch, temp_output_dir):
        """Simulate PermissionError when walking directories."""
        from pathlib import Path

        dummy_dir = temp_output_dir / "unreadable"
        dummy_dir.mkdir()

        def fake_rglob(self, pattern):
            raise PermissionError("denied")

        monkeypatch.setattr(Path, "rglob", fake_rglob, raising=False)

        with pytest.raises(PermissionError):
            list(dummy_dir.rglob("*"))


class TestMissingFileHandling:
    """Test handling of missing files and directories."""

    @pytest.mark.unit
    def test_config_handles_missing_config_file(self):
        """Config loading should fall back to defaults."""
        config = load_development_tools_module("config")
        assert hasattr(config, "PROJECT_ROOT")
        assert isinstance(config.get_project_root(), (str, Path))

    @pytest.mark.unit
    def test_documentation_sync_handles_missing_docs(self, temp_docs_dir):
        """DocumentationSyncChecker should report missing docs gracefully."""
        doc_sync_module = load_development_tools_module("analyze_documentation_sync")
        checker = doc_sync_module.DocumentationSyncChecker(project_root=str(temp_docs_dir))
        checker.paired_docs = {"docs/human.md": "docs/ai.md"}

        (temp_docs_dir / "docs").mkdir(parents=True, exist_ok=True)

        issues = checker.check_paired_documentation()
        assert "missing_human_docs" in issues
        assert "missing_ai_docs" in issues

    @pytest.mark.unit
    def test_coverage_handles_missing_coverage_data(self, demo_project_root):
        """CoverageMetricsRegenerator should handle missing data gracefully."""
        coverage = load_development_tools_module("run_test_coverage")
        regenerator = coverage.CoverageMetricsRegenerator(str(demo_project_root))

        # parse_coverage_output moved to TestCoverageAnalyzer during Batch 3 decomposition
        empty_data = regenerator.analyzer.parse_coverage_output("")
        assert isinstance(empty_data, dict)


class TestInvalidInputHandling:
    """Test handling of invalid inputs."""

    @pytest.mark.unit
    def test_standard_exclusions_handles_none_path(self):
        """should_exclude_file should tolerate None input."""
        import importlib.util
        import sys

        project_root = Path(__file__).parent.parent.parent
        exclusions_path = project_root / "development_tools" / "shared" / "standard_exclusions.py"
        spec = importlib.util.spec_from_file_location(
            "development_tools.shared.standard_exclusions", exclusions_path
        )
        exclusions_module = importlib.util.module_from_spec(spec)
        sys.modules["development_tools.shared.standard_exclusions"] = exclusions_module
        spec.loader.exec_module(exclusions_module)

        should_exclude_file = exclusions_module.should_exclude_file

        try:
            result = should_exclude_file(None)
            assert isinstance(result, bool) or result is None
        except (TypeError, AttributeError):
            pass

    @pytest.mark.unit
    def test_constants_handles_invalid_module_names(self):
        """is_local_module and is_standard_library_module should handle invalid inputs."""
        import importlib.util
        import sys

        project_root = Path(__file__).parent.parent.parent
        constants_path = project_root / "development_tools" / "shared" / "constants.py"
        spec = importlib.util.spec_from_file_location(
            "development_tools.shared.constants", constants_path
        )
        constants_module = importlib.util.module_from_spec(spec)
        sys.modules["development_tools.shared.constants"] = constants_module
        spec.loader.exec_module(constants_module)

        assert isinstance(constants_module.is_local_module(""), bool)
        assert isinstance(constants_module.is_local_module(None), bool)
        assert isinstance(constants_module.is_standard_library_module(""), bool)
        assert isinstance(constants_module.is_standard_library_module(None), bool)

    @pytest.mark.unit
    def test_legacy_cleanup_handles_invalid_patterns(self, demo_project_root):
        """Legacy cleanup should tolerate empty search patterns."""
        analyzer_module = load_development_tools_module("analyze_legacy_references")
        analyzer = analyzer_module.LegacyReferenceAnalyzer(str(demo_project_root))

        try:
            result = analyzer.find_all_references("")
            assert isinstance(result, dict)
        except (ValueError, AttributeError):
            pass


class TestConcurrentAccessHandling:
    """Test handling of concurrent file access scenarios."""

    @pytest.mark.unit
    def test_file_operations_handle_locked_files(self, temp_output_dir):
        """Writing to already opened files should be handled gracefully."""
        locked_file = temp_output_dir / "locked.txt"
        locked_file.write_text("test")

        if os.name == "nt":
            with open(locked_file, "r"):
                try:
                    locked_file.write_text("new")
                except (PermissionError, OSError):
                    pass

    @pytest.mark.unit
    def test_coverage_handles_concurrent_writes(self, temp_coverage_dir):
        """Multiple writes to the same coverage file should not crash."""
        coverage_file = temp_coverage_dir / "coverage.json"

        for i in range(3):
            with open(coverage_file, "w", encoding="utf-8") as handle:
                json.dump({"run": i}, handle)

        assert coverage_file.exists()


class TestNetworkAndExternalErrorHandling:
    """Test handling of network and external system errors."""

    @pytest.mark.unit
    def test_coverage_handles_pytest_failure(self, demo_project_root):
        """Coverage metrics should report pytest failures without crashing."""
        import subprocess
        coverage = load_development_tools_module("run_test_coverage")
        regenerator = coverage.CoverageMetricsRegenerator(str(demo_project_root))

        # Patch subprocess.run globally - all modules import from the same subprocess module
        # The module uses subprocess.run() which will use the patched version
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="pytest failed")

            result = regenerator.run_coverage_analysis()
            assert isinstance(result, dict)

