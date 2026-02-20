"""Focused tests for tool wrapper paths in shared/service/tool_wrappers.py."""

import pytest

from tests.development_tools.conftest import load_development_tools_module


service_module = load_development_tools_module("shared.service")
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_run_analyze_package_exports_success_populates_summary(temp_project_copy, monkeypatch):
    """Wrapper should aggregate package export reports and cache standardized summary."""
    service = AIToolsService(project_root=str(temp_project_copy))

    target_module = load_development_tools_module("functions.analyze_package_exports")

    monkeypatch.setattr(
        target_module,
        "analyze_imports_for_packages",
        lambda packages: {pkg: {} for pkg in packages},
        raising=True,
    )
    monkeypatch.setattr(
        target_module,
        "scan_package_modules_for_packages",
        lambda packages: {pkg: {} for pkg in packages},
        raising=True,
    )
    monkeypatch.setattr(
        target_module,
        "parse_function_registry_for_packages",
        lambda packages: {pkg: set() for pkg in packages},
        raising=True,
    )

    def fake_report(package, *args, **kwargs):
        return {
            "package": package,
            "missing_exports": ["x"] if package in {"core", "ui"} else [],
            "potentially_unnecessary": ["y"] if package == "core" else [],
            "already_exported": [],
        }

    monkeypatch.setattr(target_module, "generate_audit_report", fake_report, raising=True)

    result = service.run_analyze_package_exports()

    assert result["success"] is True
    data = result["data"]
    assert data["summary"]["total_issues"] == 3
    assert data["summary"]["files_affected"] == 2
    assert "analyze_package_exports" in service.results_cache


@pytest.mark.unit
def test_run_analyze_package_exports_handles_import_stage_failure(temp_project_copy, monkeypatch):
    """Wrapper should fail cleanly when pre-index generation raises."""
    service = AIToolsService(project_root=str(temp_project_copy))
    target_module = load_development_tools_module("functions.analyze_package_exports")

    def raise_error(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(target_module, "analyze_imports_for_packages", raise_error, raising=True)

    result = service.run_analyze_package_exports()

    assert result["success"] is False
    assert "boom" in result["error"]
