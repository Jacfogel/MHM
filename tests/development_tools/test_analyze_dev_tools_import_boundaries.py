"""Tests for analyze_dev_tools_import_boundaries.py."""

import pytest

from tests.development_tools.conftest import load_development_tools_module

boundary_module = load_development_tools_module("imports.analyze_dev_tools_import_boundaries")
DevToolsImportBoundaryChecker = boundary_module.DevToolsImportBoundaryChecker


@pytest.mark.unit
def test_checker_detects_non_approved_core_import(tmp_path):
    """Checker flags core.config imports."""
    checker = DevToolsImportBoundaryChecker(project_root_path=str(tmp_path))
    # Create a fake dev_tools structure with a file importing core.config
    dev_tools = tmp_path / "development_tools"
    dev_tools.mkdir()
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "core" / "logger.py").write_text("", encoding="utf-8")
    (tmp_path / "core" / "config.py").write_text("", encoding="utf-8")

    bad_file = dev_tools / "bad_import.py"
    bad_file.write_text("from core.config import get_project_root\n", encoding="utf-8")

    result = checker.analyze()

    assert result["summary"]["total_issues"] >= 1
    violations = result["details"]["violations"]
    assert any(
        v["module"] == "core.config" and "development_tools" in v["file"]
        for v in violations
    )


@pytest.mark.unit
def test_checker_flags_core_logger(tmp_path):
    """Checker flags core.logger (no core imports allowed in development_tools)."""
    checker = DevToolsImportBoundaryChecker(project_root_path=str(tmp_path))
    dev_tools = tmp_path / "development_tools"
    dev_tools.mkdir()
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "core" / "logger.py").write_text("", encoding="utf-8")

    bad_file = dev_tools / "bad_import.py"
    bad_file.write_text("from core.logger import get_component_logger\n", encoding="utf-8")

    result = checker.analyze()

    assert result["summary"]["total_issues"] >= 1
    violations = result["details"]["violations"]
    assert any(v["module"] == "core.logger" for v in violations)


@pytest.mark.unit
def test_extract_import_modules_handles_syntax_error(tmp_path):
    """_extract_import_modules returns empty list for unparseable file."""
    checker = DevToolsImportBoundaryChecker(project_root_path=str(tmp_path))
    bad_syntax = tmp_path / "bad.py"
    bad_syntax.write_text("from x import \n", encoding="utf-8")

    modules = checker._extract_import_modules(bad_syntax)

    assert modules == []


@pytest.mark.unit
def test_analyze_returns_standard_format(tmp_path):
    """analyze() returns standard summary/details structure."""
    checker = DevToolsImportBoundaryChecker(project_root_path=str(tmp_path))
    result = checker.analyze()

    assert "summary" in result
    assert "details" in result
    assert "total_issues" in result["summary"]
    assert "files_affected" in result["summary"]
    assert "violations" in result["details"]
    assert isinstance(result["details"]["violations"], list)
