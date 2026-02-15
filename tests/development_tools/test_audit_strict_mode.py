"""Tests for strict mode and Tier 3 test outcome semantics."""

from unittest.mock import MagicMock
import json

import pytest

from tests.development_tools.conftest import load_development_tools_module

service_module = load_development_tools_module("shared.service")
coverage_module = load_development_tools_module("tests.run_test_coverage")
AIToolsService = service_module.AIToolsService
CoverageMetricsRegenerator = coverage_module.CoverageMetricsRegenerator


@pytest.mark.unit
def test_audit_full_non_strict_allows_tier3_test_failures(temp_project_copy):
    """Non-strict mode should keep success when Tier 3 reports test_failures."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service._run_quick_audit_tools = MagicMock(return_value=True)
    service._run_standard_audit_tools = MagicMock(return_value=True)
    def _full_non_strict():
        service.tier3_test_outcome = {"state": "test_failures"}
        return True
    service._run_full_audit_tools = MagicMock(side_effect=_full_non_strict)
    service._save_audit_results_aggregated = MagicMock(return_value=None)
    service._reload_all_cache_data = MagicMock(return_value=None)
    service._sync_todo_with_changelog = MagicMock(return_value=None)
    service._validate_referenced_paths = MagicMock(return_value=None)
    service._check_and_trim_changelog_entries = MagicMock(return_value=None)
    service._check_documentation_quality = MagicMock(return_value=None)
    service._check_ascii_compliance = MagicMock(return_value=None)
    service._generate_ai_status_document = MagicMock(return_value="# AI Status")
    service._generate_ai_priorities_document = MagicMock(return_value="# AI Priorities")
    service._generate_consolidated_report = MagicMock(return_value="# Consolidated")

    assert service.run_audit(full=True, strict=False) is True


@pytest.mark.unit
def test_audit_full_strict_fails_on_tier3_test_failures(temp_project_copy):
    """Strict mode should return failure when Tier 3 reports test_failures."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service._run_quick_audit_tools = MagicMock(return_value=True)
    service._run_standard_audit_tools = MagicMock(return_value=True)
    def _full_strict():
        service.tier3_test_outcome = {"state": "test_failures"}
        return True
    service._run_full_audit_tools = MagicMock(side_effect=_full_strict)
    service._save_audit_results_aggregated = MagicMock(return_value=None)
    service._reload_all_cache_data = MagicMock(return_value=None)
    service._sync_todo_with_changelog = MagicMock(return_value=None)
    service._validate_referenced_paths = MagicMock(return_value=None)
    service._check_and_trim_changelog_entries = MagicMock(return_value=None)
    service._check_documentation_quality = MagicMock(return_value=None)
    service._check_ascii_compliance = MagicMock(return_value=None)
    service._generate_ai_status_document = MagicMock(return_value="# AI Status")
    service._generate_ai_priorities_document = MagicMock(return_value="# AI Priorities")
    service._generate_consolidated_report = MagicMock(return_value="# Consolidated")

    assert service.run_audit(full=True, strict=True) is False


@pytest.mark.unit
def test_audit_full_strict_fails_when_dev_tools_tests_fail(temp_project_copy):
    """Strict mode should fail when development-tools track reports failed tests."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service._run_quick_audit_tools = MagicMock(return_value=True)
    service._run_standard_audit_tools = MagicMock(return_value=True)

    def _full_strict_dev_tools():
        service.tier3_test_outcome = {
            "state": "clean",
            "development_tools": {"state": "failed"},
        }
        return True

    service._run_full_audit_tools = MagicMock(side_effect=_full_strict_dev_tools)
    service._save_audit_results_aggregated = MagicMock(return_value=None)
    service._reload_all_cache_data = MagicMock(return_value=None)
    service._sync_todo_with_changelog = MagicMock(return_value=None)
    service._validate_referenced_paths = MagicMock(return_value=None)
    service._check_and_trim_changelog_entries = MagicMock(return_value=None)
    service._check_documentation_quality = MagicMock(return_value=None)
    service._check_ascii_compliance = MagicMock(return_value=None)
    service._generate_ai_status_document = MagicMock(return_value="# AI Status")
    service._generate_ai_priorities_document = MagicMock(return_value="# AI Priorities")
    service._generate_consolidated_report = MagicMock(return_value="# Consolidated")

    assert service.run_audit(full=True, strict=True) is False


@pytest.mark.unit
def test_run_test_coverage_classifies_windows_crash():
    """Crash return code 3221226505 should map to crashed."""
    regenerator = CoverageMetricsRegenerator(project_root=".", parallel=False)
    outcome = regenerator._build_track_outcome(
        return_code=3221226505,
        parsed_results={},
        output="",
    )
    assert outcome["state"] == "crashed"


@pytest.mark.unit
def test_run_test_coverage_classifies_cleanup_permission_error():
    """cleanup_dead_symlinks PermissionError should map to infra_cleanup_error."""
    regenerator = CoverageMetricsRegenerator(project_root=".", parallel=False)
    outcome = regenerator._build_track_outcome(
        return_code=1,
        parsed_results={"failed_count": 0, "error_count": 0, "total_tests": 0},
        output="PermissionError: [WinError 5] cleanup_dead_symlinks failed",
    )
    assert outcome["state"] == "infra_cleanup_error"


@pytest.mark.unit
def test_run_coverage_regeneration_fails_when_coverage_outcome_failed(
    temp_project_copy, monkeypatch
):
    """Coverage outcome 'coverage_failed' must fail tool execution even if wrapper returns success."""
    service = AIToolsService(project_root=str(temp_project_copy))
    output_file = (
        temp_project_copy
        / "development_tools"
        / "tests"
        / "jsons"
        / "run_test_coverage_results.json"
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(
            {
                "coverage_outcome": {
                    "state": "coverage_failed",
                    "parallel": {"state": "unknown"},
                    "no_parallel": {"state": "unknown"},
                    "failed_node_ids": [],
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        service,
        "run_script",
        lambda *args, **kwargs: {"success": True, "output": "", "error": ""},
    )

    assert service.run_coverage_regeneration() is False


@pytest.mark.unit
def test_tier3_outcome_includes_development_tools_line(temp_project_copy):
    """Tier 3 report section should include a separate development tools track line."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service.tier3_test_outcome = {
        "state": "test_failures",
        "parallel": {
            "state": "failed",
            "passed_count": 10,
            "failed_count": 1,
            "error_count": 0,
            "skipped_count": 0,
            "return_code": 1,
        },
        "no_parallel": {
            "state": "passed",
            "passed_count": 5,
            "failed_count": 0,
            "error_count": 0,
            "skipped_count": 0,
            "return_code": 0,
        },
        "development_tools": {
            "state": "passed",
            "passed_count": 20,
            "failed_count": 0,
            "error_count": 0,
            "skipped_count": 1,
            "return_code": 0,
        },
        "failed_node_ids": ["tests/unit/test_example.py::test_failure"],
    }

    lines = []
    service._append_tier3_test_outcome_lines(lines)
    rendered = "\n".join(lines)
    assert "Development Tools Track" in rendered
    assert "passed=20" in rendered


@pytest.mark.unit
def test_run_coverage_regeneration_preserves_development_tools_outcome(
    temp_project_copy, monkeypatch
):
    """Main coverage regeneration should not overwrite dev-tools track outcome."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service.tier3_test_outcome = {
        "development_tools": {
            "state": "failed",
            "passed_count": 2,
            "failed_count": 1,
            "error_count": 0,
            "skipped_count": 0,
            "return_code": 1,
            "failed_node_ids": ["tests/development_tools/test_x.py::test_y"],
        }
    }

    output_file = (
        temp_project_copy
        / "development_tools"
        / "tests"
        / "jsons"
        / "run_test_coverage_results.json"
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(
            {
                "coverage_outcome": {
                    "state": "clean",
                    "parallel": {"state": "passed"},
                    "no_parallel": {"state": "passed"},
                    "failed_node_ids": [],
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        service,
        "run_script",
        lambda *args, **kwargs: {"success": True, "output": "", "error": ""},
    )
    monkeypatch.setattr(service, "_load_coverage_summary", lambda: {})

    assert service.run_coverage_regeneration() is True
    assert service.tier3_test_outcome.get("development_tools", {}).get("state") == "failed"


@pytest.mark.unit
def test_run_dev_tools_coverage_sets_development_tools_outcome(
    temp_project_copy, monkeypatch
):
    """Dev tools coverage execution should populate tier3_test_outcome.development_tools."""
    service = AIToolsService(project_root=str(temp_project_copy))

    dev_tools_coverage_file = (
        temp_project_copy
        / "development_tools"
        / "tests"
        / "jsons"
        / "coverage_dev_tools.json"
    )
    dev_tools_coverage_file.parent.mkdir(parents=True, exist_ok=True)
    dev_tools_coverage_file.write_text('{"files": {}, "totals": {}}', encoding="utf-8")

    dev_tools_output_file = (
        temp_project_copy
        / "development_tools"
        / "tests"
        / "jsons"
        / "run_test_coverage_dev_tools_results.json"
    )
    dev_tools_output_file.write_text(
        json.dumps(
            {
                "dev_tools_test_outcome": {
                    "state": "failed",
                    "return_code": 1,
                    "passed_count": 12,
                    "failed_count": 2,
                    "error_count": 0,
                    "skipped_count": 1,
                    "failed_node_ids": [
                        "tests/development_tools/test_example.py::test_failure"
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        service,
        "run_script",
        lambda *args, **kwargs: {"success": True, "output": "TOTAL", "error": ""},
    )
    monkeypatch.setattr(
        service,
        "_load_dev_tools_coverage",
        lambda: setattr(
            service,
            "dev_tools_coverage_results",
            {"summary": {"total_issues": 0, "files_affected": 0}, "details": {}},
        ),
    )

    result = service.run_dev_tools_coverage()
    assert result.get("success") is True
    assert service.tier3_test_outcome.get("development_tools", {}).get("state") == "failed"
    assert service.tier3_test_outcome.get("development_tools", {}).get("failed_count") == 2
