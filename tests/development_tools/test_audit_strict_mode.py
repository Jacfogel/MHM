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
        service.tier3_test_outcome = {
            "parallel": {"classification": "failed"},
            "no_parallel": {"classification": "passed"},
        }
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
        service.tier3_test_outcome = {
            "parallel": {"classification": "failed"},
            "no_parallel": {"classification": "passed"},
        }
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
            "parallel": {"classification": "passed"},
            "no_parallel": {"classification": "passed"},
            "development_tools": {"classification": "failed"},
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
    assert outcome["classification"] == "crashed"
    assert outcome["classification_reason"] == "windows_status_dll_not_found"
    assert outcome["return_code_hex"] == "0xC0000135"


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
    assert outcome["classification"] == "infra_cleanup_error"
    assert outcome["classification_reason"] == "cleanup_dead_symlinks_permission_error"


@pytest.mark.unit
def test_run_test_coverage_classifies_xdist_worker_crash_output():
    """xdist worker crash markers should map to crashed even with generic return code."""
    regenerator = CoverageMetricsRegenerator(project_root=".", parallel=False)
    outcome = regenerator._build_track_outcome(
        return_code=1,
        parsed_results={"failed_count": 0, "error_count": 0, "total_tests": 0},
        output=(
            "Windows fatal exception: access violation\n"
            "[gw0] node down: Not properly terminated\n"
        ),
    )
    assert outcome["state"] == "crashed"
    assert outcome["classification_reason"] == "xdist_worker_crash_output"


@pytest.mark.unit
def test_run_test_coverage_classifies_nonzero_without_tests_as_crash():
    """Non-zero exit with no parsed tests should classify as crashed infra issue."""
    regenerator = CoverageMetricsRegenerator(project_root=".", parallel=False)
    outcome = regenerator._build_track_outcome(
        return_code=5,
        parsed_results={"failed_count": 0, "error_count": 0, "total_tests": 0},
        output="",
    )
    assert outcome["state"] == "crashed"
    assert outcome["classification"] == "crashed"
    assert outcome["classification_reason"] == "nonzero_without_tests"


@pytest.mark.unit
def test_run_test_coverage_classifies_failed_tests_without_crash_markers():
    """Parsed failures without crash markers should remain failed test outcomes."""
    regenerator = CoverageMetricsRegenerator(project_root=".", parallel=False)
    outcome = regenerator._build_track_outcome(
        return_code=1,
        parsed_results={
            "failed_count": 1,
            "error_count": 0,
            "total_tests": 4,
            "failed_tests": ["tests/unit/test_a.py::test_x"],
            "error_tests": [],
        },
        output="================ short test summary info =================\nFAILED tests/unit/test_a.py::test_x",
    )
    assert outcome["state"] == "failed"
    assert outcome["classification"] == "failed"
    assert outcome["classification_reason"] == "pytest_failed_or_errored"


@pytest.mark.unit
def test_audit_full_strict_fails_on_tier3_infra_cleanup_error(temp_project_copy):
    """Strict mode should fail when Tier 3 reports infra cleanup errors."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service._run_quick_audit_tools = MagicMock(return_value=True)
    service._run_standard_audit_tools = MagicMock(return_value=True)

    def _full_strict_infra_cleanup():
        service.tier3_test_outcome = {
            "parallel": {"classification": "infra_cleanup_error"},
            "no_parallel": {"classification": "passed"},
        }
        return True

    service._run_full_audit_tools = MagicMock(side_effect=_full_strict_infra_cleanup)
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
def test_audit_full_non_strict_allows_tier3_infra_cleanup_error(temp_project_copy):
    """Non-strict mode should keep success when Tier 3 reports infra cleanup issues."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service._run_quick_audit_tools = MagicMock(return_value=True)
    service._run_standard_audit_tools = MagicMock(return_value=True)

    def _full_non_strict_infra_cleanup():
        service.tier3_test_outcome = {
            "parallel": {"classification": "infra_cleanup_error"},
            "no_parallel": {"classification": "passed"},
        }
        return True

    service._run_full_audit_tools = MagicMock(side_effect=_full_non_strict_infra_cleanup)
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
            "classification": "failed",
            "passed_count": 10,
            "failed_count": 1,
            "error_count": 0,
            "skipped_count": 0,
            "return_code": 1,
        },
        "no_parallel": {
            "state": "passed",
            "classification": "passed",
            "passed_count": 5,
            "failed_count": 0,
            "error_count": 0,
            "skipped_count": 0,
            "return_code": 0,
        },
        "development_tools": {
            "state": "passed",
            "classification": "passed",
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
            "classification": "failed",
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
                    "parallel": {"state": "passed", "classification": "passed"},
                    "no_parallel": {"state": "passed", "classification": "passed"},
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
def test_run_coverage_regeneration_propagates_track_classification_fields(
    temp_project_copy, monkeypatch
):
    """Main coverage regeneration should preserve per-track classification metadata."""
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
                    "state": "crashed",
                    "parallel": {
                        "state": "passed",
                        "classification": "passed",
                        "classification_reason": "pytest_passed",
                        "actionable_context": "Track completed successfully.",
                        "log_file": "development_tools/tests/logs/pytest_parallel_stdout_x.log",
                        "return_code_hex": "0x00000000",
                    },
                    "no_parallel": {
                        "state": "crashed",
                        "classification": "crashed",
                        "classification_reason": "windows_status_dll_not_found",
                        "actionable_context": "Missing DLL or PATH issue.",
                        "log_file": "development_tools/tests/logs/pytest_no_parallel_stdout_x.log",
                        "return_code_hex": "0xC0000135",
                    },
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
    monkeypatch.setattr(service, "_load_coverage_summary", lambda: {"overall": {"missed": 0}})

    assert service.run_coverage_regeneration() is True
    outcome = service.tier3_test_outcome
    assert outcome.get("no_parallel", {}).get("classification_reason") == "windows_status_dll_not_found"
    assert outcome.get("no_parallel", {}).get("log_file") == "development_tools/tests/logs/pytest_no_parallel_stdout_x.log"


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
                "summary": {"total_issues": 2, "files_affected": 0},
                "details": {
                    "dev_tools_test_outcome": {
                        "state": "failed",
                        "classification": "failed",
                        "return_code": 1,
                        "passed_count": 12,
                        "failed_count": 2,
                        "error_count": 0,
                        "skipped_count": 1,
                        "failed_node_ids": [
                            "tests/development_tools/test_example.py::test_failure"
                        ],
                    }
                },
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
    assert (
        service.tier3_test_outcome.get("development_tools", {}).get("classification")
        == "failed"
    )
    assert service.tier3_test_outcome.get("development_tools", {}).get("failed_count") == 2


@pytest.mark.unit
def test_run_coverage_regeneration_reruns_when_cached_outcome_failed(
    temp_project_copy, monkeypatch
):
    """Precheck cache reuse should be blocked when cached main outcome is failed."""
    service = AIToolsService(project_root=str(temp_project_copy))
    output_file = (
        temp_project_copy
        / "development_tools"
        / "tests"
        / "jsons"
        / "run_test_coverage_results.json"
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(service, "_is_coverage_file_fresh", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        service,
        "_load_cached_result_if_available",
        lambda *args, **kwargs: {
            "details": {
                "tier3_test_outcome": {
                    "parallel": {"classification": "failed"},
                    "no_parallel": {"classification": "passed"},
                }
            }
        },
    )
    monkeypatch.setattr(service, "_load_coverage_summary", lambda: {"overall": {"missed": 0}})

    calls = {"count": 0}

    def _run_script(*args, **kwargs):
        calls["count"] += 1
        output_file.write_text(
            json.dumps(
                {
                    "coverage_outcome": {
                        "state": "clean",
                        "parallel": {"state": "passed", "classification": "passed"},
                        "no_parallel": {"state": "passed", "classification": "passed"},
                        "failed_node_ids": [],
                    }
                }
            ),
            encoding="utf-8",
        )
        return {"success": True, "output": "", "error": ""}

    monkeypatch.setattr(service, "run_script", _run_script)

    assert service.run_coverage_regeneration() is True
    assert calls["count"] == 1


@pytest.mark.unit
def test_run_dev_tools_coverage_reruns_when_cached_outcome_failed(
    temp_project_copy, monkeypatch
):
    """Precheck cache reuse should be blocked when cached dev-tools outcome is failed."""
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

    monkeypatch.setattr(service, "_is_coverage_file_fresh", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        service,
        "_load_cached_result_if_available",
        lambda *args, **kwargs: {
            "details": {"dev_tools_test_outcome": {"classification": "failed"}}
        },
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

    calls = {"count": 0}

    def _run_script(*args, **kwargs):
        calls["count"] += 1
        dev_tools_output_file.write_text(
            json.dumps(
                {
                    "details": {
                        "dev_tools_test_outcome": {
                            "state": "passed",
                            "classification": "passed",
                            "return_code": 0,
                            "passed_count": 1,
                            "failed_count": 0,
                            "error_count": 0,
                            "skipped_count": 0,
                            "failed_node_ids": [],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        return {"success": True, "output": "TOTAL", "error": "", "returncode": 0}

    monkeypatch.setattr(service, "run_script", _run_script)

    result = service.run_dev_tools_coverage()
    assert result.get("success") is True
    assert calls["count"] == 1
