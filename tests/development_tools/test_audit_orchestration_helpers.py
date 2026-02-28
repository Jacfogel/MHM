"""Targeted helper tests for audit_orchestration mixin behavior."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module

service_module = load_development_tools_module("shared.service")
audit_module = load_development_tools_module("shared.service.audit_orchestration")
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_get_status_file_mtimes_uses_default_paths(tmp_path: Path):
    """Fallback status-file paths should be resolved when config import is unavailable."""
    status_dir = tmp_path / "development_tools"
    status_dir.mkdir(parents=True, exist_ok=True)
    (status_dir / "AI_STATUS.md").write_text("status", encoding="utf-8")
    (status_dir / "consolidated_report.md").write_text("report", encoding="utf-8")

    mtimes = audit_module._get_status_file_mtimes(tmp_path)
    assert mtimes["AI_STATUS.md"] > 0
    assert mtimes["AI_PRIORITIES.md"] == 0.0
    assert mtimes["consolidated_report.md"] > 0


@pytest.mark.unit
def test_is_audit_in_progress_detects_global_and_lock_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Global flag and any lock file should mark audit as in progress."""
    monkeypatch.setattr(audit_module, "_AUDIT_IN_PROGRESS_GLOBAL", False)
    monkeypatch.setattr(audit_module, "_AUDIT_LOCK_FILE", None)

    assert audit_module._is_audit_in_progress(tmp_path) is False

    monkeypatch.setattr(audit_module, "_AUDIT_IN_PROGRESS_GLOBAL", True)
    assert audit_module._is_audit_in_progress(tmp_path) is True

    monkeypatch.setattr(audit_module, "_AUDIT_IN_PROGRESS_GLOBAL", False)
    (tmp_path / ".coverage_dev_tools_in_progress.lock").write_text("", encoding="utf-8")
    assert audit_module._is_audit_in_progress(tmp_path) is True


@pytest.mark.unit
@pytest.mark.parametrize(
    ("tier3_outcome", "expected_state"),
    [
        ({"state": "coverage_failed"}, "coverage_failed"),
        ({"parallel": {"classification": "infra_cleanup_error"}}, "infra_cleanup_error"),
        ({"parallel": {"classification": "crashed"}}, "crashed"),
        ({"parallel": {"classification": "failed"}}, "test_failures"),
        ({"parallel": {"classification": "passed"}}, "clean"),
        ({"parallel": {"classification": "unknown"}}, "coverage_failed"),
        ({}, "coverage_failed"),
    ],
)
def test_effective_tier3_state_resolution(
    temp_project_copy: Path, tier3_outcome: dict, expected_state: str
):
    """Tier 3 summary state should classify by track severity precedence."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service.tier3_test_outcome = tier3_outcome
    assert service._effective_tier3_state() == expected_state


@pytest.mark.unit
def test_get_expected_tools_for_tier_matrix(temp_project_copy: Path):
    """Expected tool list should match tier intent and quick_status rules."""
    service = AIToolsService(project_root=str(temp_project_copy))

    tier1 = service._get_expected_tools_for_tier(1)
    tier2 = service._get_expected_tools_for_tier(2)
    tier3 = service._get_expected_tools_for_tier(3)

    assert "quick_status" in tier1
    assert "quick_status" not in tier2
    assert "analyze_functions" in tier2
    assert "run_test_coverage" in tier3
    assert "analyze_pyright" in tier3


@pytest.mark.unit
def test_save_timing_data_writes_expected_metadata(temp_project_copy: Path):
    """Timing data file should include audit metadata, statuses, and cache info."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_timings = {"analyze_system_signals": 1.25}
    service._tool_execution_status = {"analyze_system_signals": "success"}
    service._tool_cache_metadata = {
        "analyze_system_signals": {"cache_mode": "fresh", "cache_reason": "n/a"}
    }
    service._audit_wall_clock_start = time.perf_counter() - 2.0

    service._save_timing_data(tier=2, audit_success=True)

    timing_file = temp_project_copy / "development_tools" / "reports" / "tool_timings.json"
    assert timing_file.exists()

    payload = json.loads(timing_file.read_text(encoding="utf-8"))
    assert "runs" in payload and payload["runs"]

    run = payload["runs"][-1]
    assert run["tier"] == "standard"
    assert run["tier_number"] == 2
    assert run["audit_success"] is True
    assert run["tool_timings"]["analyze_system_signals"] == 1.25
    assert "wall_clock_total_seconds" in run
    assert isinstance(run["expected_tools"], list)
    assert "analyze_functions" in run["expected_tools"]
    assert run["tool_execution_status"]["analyze_system_signals"] == "success"
    assert run["tool_cache_metadata"]["analyze_system_signals"]["cache_mode"] == "fresh"
