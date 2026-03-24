"""Targeted helper tests for audit_orchestration mixin behavior."""

from __future__ import annotations

import json
import time
import concurrent.futures
from pathlib import Path
from typing import cast

import pytest

from development_tools.shared.service.audit_orchestration import ToolExecutionError
from tests.development_tools.conftest import load_development_tools_module

service_module = load_development_tools_module("shared.service")
audit_module = load_development_tools_module("shared.service.audit_orchestration")
lock_state_module = load_development_tools_module("shared.lock_state")
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_get_status_file_mtimes_uses_default_paths(tmp_path: Path):
    """Fallback status-file paths should be resolved when config import is unavailable."""
    status_dir = tmp_path / "development_tools"
    status_dir.mkdir(parents=True, exist_ok=True)
    (status_dir / "AI_STATUS.md").write_text("status", encoding="utf-8")
    (status_dir / "CONSOLIDATED_REPORT.md").write_text("report", encoding="utf-8")

    mtimes = audit_module._get_status_file_mtimes(tmp_path)
    assert mtimes["AI_STATUS.md"] > 0
    assert mtimes["AI_PRIORITIES.md"] == 0.0
    assert mtimes["CONSOLIDATED_REPORT.md"] > 0


@pytest.mark.unit
def test_is_audit_in_progress_detects_global_and_lock_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Global flag and active lock files should mark audit as in progress."""
    monkeypatch.setattr(audit_module, "_AUDIT_IN_PROGRESS_GLOBAL", False)
    monkeypatch.setattr(audit_module, "_AUDIT_LOCK_FILE", None)

    assert audit_module._is_audit_in_progress(tmp_path) is False

    monkeypatch.setattr(audit_module, "_AUDIT_IN_PROGRESS_GLOBAL", True)
    assert audit_module._is_audit_in_progress(tmp_path) is True

    monkeypatch.setattr(audit_module, "_AUDIT_IN_PROGRESS_GLOBAL", False)
    lock_state_module.write_lock_metadata(
        tmp_path / ".coverage_dev_tools_in_progress.lock", lock_type="coverage_dev_tools"
    )
    assert audit_module._is_audit_in_progress(tmp_path) is True


@pytest.mark.unit
def test_is_audit_in_progress_cleans_stale_and_legacy_locks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Malformed/legacy locks are auto-cleaned and do not block audit state."""
    monkeypatch.setattr(audit_module, "_AUDIT_IN_PROGRESS_GLOBAL", False)
    monkeypatch.setattr(audit_module, "_AUDIT_LOCK_FILE", None)

    stale_payload = {
        "version": 1,
        "lock_type": "audit",
        "pid": 999999,
        "ppid": 1,
        "created_at": time.time() - 10,
        "stale_after_seconds": 5400,
        "host": "test-host",
        "command": "python -m pytest",
    }
    stale_lock = tmp_path / ".audit_in_progress.lock"
    stale_lock.write_text(json.dumps(stale_payload), encoding="utf-8")
    legacy_lock = tmp_path / ".coverage_dev_tools_in_progress.lock"
    legacy_lock.write_text("", encoding="utf-8")

    assert audit_module._is_audit_in_progress(tmp_path) is False
    assert not stale_lock.exists()
    assert not legacy_lock.exists()


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

    timing_file = (
        temp_project_copy
        / "development_tools"
        / "reports"
        / "jsons"
        / "tool_timings.json"
    )
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


@pytest.mark.unit
def test_run_audit_internal_interrupt_converts_to_failed_audit(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    """Internal Tier-3 interrupt signatures should fail audit without bubbling KeyboardInterrupt."""
    service = AIToolsService(project_root=str(temp_project_copy))

    monkeypatch.setattr(service, "_run_quick_audit_tools", lambda: True)
    monkeypatch.setattr(service, "_run_standard_audit_tools", lambda: True)

    def _raise_internal_interrupt():
        service._internal_interrupt_detected = True
        raise KeyboardInterrupt()

    monkeypatch.setattr(service, "_run_full_audit_tools", _raise_internal_interrupt)
    monkeypatch.setattr(service, "_save_audit_results_aggregated", lambda *_a, **_k: None)
    monkeypatch.setattr(service, "_reload_all_cache_data", lambda *_a, **_k: None)
    monkeypatch.setattr(service, "_sync_todo_with_changelog", lambda *_a, **_k: None)
    monkeypatch.setattr(service, "_validate_referenced_paths", lambda *_a, **_k: None)
    monkeypatch.setattr(
        service, "_check_and_trim_changelog_entries", lambda *_a, **_k: None
    )
    monkeypatch.setattr(service, "_check_documentation_quality", lambda *_a, **_k: None)
    monkeypatch.setattr(service, "_check_ascii_compliance", lambda *_a, **_k: None)
    monkeypatch.setattr(
        service, "_generate_ai_status_document", lambda *_a, **_k: "# AI Status\n"
    )
    monkeypatch.setattr(
        service,
        "_generate_ai_priorities_document",
        lambda *_a, **_k: "# AI Priorities\n",
    )
    monkeypatch.setattr(
        service, "_generate_consolidated_report", lambda *_a, **_k: "# Consolidated\n"
    )

    result = service.run_audit(full=True)

    assert result is False


@pytest.mark.unit
def test_run_full_audit_tools_traps_keyboardinterrupt_from_worker_group(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    """Tier 3 worker KeyboardInterrupt should be recorded as failure, not bubbled."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_timings = {}
    service._tool_execution_status = {}
    service._tools_run_in_current_tier = set()
    service._tool_cache_metadata = {}
    service.tier3_test_outcome = {}
    service._internal_interrupt_detected = False

    def _fake_run_tool_with_timing(tool_name, _tool_func):
        if tool_name == "generate_dev_tools_coverage":
            raise KeyboardInterrupt()
        return {"success": True}, 0.01

    monkeypatch.setattr(service, "_run_tool_with_timing", _fake_run_tool_with_timing)
    monkeypatch.setattr(service, "_extract_key_info", lambda *_a, **_k: None)
    monkeypatch.setattr(service, "_record_tool_cache_metadata", lambda *_a, **_k: None)
    # Patch the module reference used by orchestration so worker thread sees it
    monkeypatch.setattr(
        audit_module.audit_signal_state,
        "record_audit_keyboard_interrupt",
        lambda: True,
    )

    result = service._run_full_audit_tools()

    assert result is False
    assert service._internal_interrupt_detected is True


@pytest.mark.unit
def test_run_full_audit_tools_traps_keyboardinterrupt_from_as_completed(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    """Tier 3 as_completed KeyboardInterrupt should not bubble from _run_full_audit_tools."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_timings = {}
    service._tool_execution_status = {}
    service._tools_run_in_current_tier = set()
    service._tool_cache_metadata = {}
    service.tier3_test_outcome = {}
    service._internal_interrupt_detected = False

    monkeypatch.setattr(
        service, "_run_tool_with_timing", lambda *_a, **_k: ({"success": True}, 0.01)
    )
    monkeypatch.setattr(service, "_extract_key_info", lambda *_a, **_k: None)
    monkeypatch.setattr(service, "_record_tool_cache_metadata", lambda *_a, **_k: None)

    class _FakeFuture:
        pass

    class _FakeExecutor:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def submit(self, _fn, _group):
            return _FakeFuture()

        def shutdown(self, wait=True):
            pass

    def _raise_interrupt(_futures):
        raise KeyboardInterrupt()
        yield  # pragma: no cover

    monkeypatch.setattr(
        concurrent.futures, "ThreadPoolExecutor", _FakeExecutor, raising=True
    )
    monkeypatch.setattr(concurrent.futures, "as_completed", _raise_interrupt, raising=True)
    monkeypatch.setattr(
        audit_module.audit_signal_state,
        "record_audit_keyboard_interrupt",
        lambda: True,
    )

    result = service._run_full_audit_tools()

    assert result is False
    assert service._internal_interrupt_detected is True


@pytest.mark.unit
def test_run_full_audit_tools_ignores_as_completed_interrupt_after_all_done(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    """If as_completed is interrupted after all futures are done, Tier 3 should not hard-fail."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_timings = {}
    service._tool_execution_status = {}
    service._tools_run_in_current_tier = set()
    service._tool_cache_metadata = {}
    service.tier3_test_outcome = {}
    service._internal_interrupt_detected = False

    monkeypatch.setattr(
        service, "_run_tool_with_timing", lambda *_a, **_k: ({"success": True}, 0.01)
    )
    monkeypatch.setattr(service, "_extract_key_info", lambda *_a, **_k: None)
    monkeypatch.setattr(service, "_record_tool_cache_metadata", lambda *_a, **_k: None)

    class _DoneFuture:
        def done(self):
            return True

    class _FakeExecutor:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def submit(self, _fn, _group):
            return _DoneFuture()

        def shutdown(self, wait=True):
            pass

    def _raise_interrupt(_futures):
        raise KeyboardInterrupt()
        yield  # pragma: no cover

    monkeypatch.setattr(
        concurrent.futures, "ThreadPoolExecutor", _FakeExecutor, raising=True
    )
    monkeypatch.setattr(concurrent.futures, "as_completed", _raise_interrupt, raising=True)

    result = service._run_full_audit_tools()

    assert result is True
    assert service._internal_interrupt_detected is False


@pytest.mark.unit
def test_run_full_audit_tools_drains_done_futures_after_as_completed_interrupt(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    """Finished futures should still contribute timings when as_completed is interrupted late."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_timings = {}
    service._tool_execution_status = {}
    service._tools_run_in_current_tier = set()
    service._tool_cache_metadata = {}
    service.tier3_test_outcome = {}
    service._internal_interrupt_detected = False

    monkeypatch.setattr(
        service, "_run_tool_with_timing", lambda tool_name, _fn: ({"success": True}, 0.01)
    )
    monkeypatch.setattr(service, "_extract_key_info", lambda *_a, **_k: None)
    monkeypatch.setattr(service, "_record_tool_cache_metadata", lambda *_a, **_k: None)

    class _FakeFuture:
        def __init__(self, result_payload):
            self._result = result_payload

        def done(self):
            return True

        def result(self):
            return self._result

    class _FakeExecutor:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def submit(self, fn, group):
            return _FakeFuture(fn(group))

        def shutdown(self, wait=True):
            pass

    def _interrupt_after_first(futures):
        futures = list(futures)
        if futures:
            yield futures[0]
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        concurrent.futures, "ThreadPoolExecutor", _FakeExecutor, raising=True
    )
    monkeypatch.setattr(
        concurrent.futures, "as_completed", _interrupt_after_first, raising=True
    )

    result = service._run_full_audit_tools()

    assert result is True
    assert "run_test_coverage" in service._tool_timings
    assert "generate_dev_tools_coverage" in service._tool_timings


@pytest.mark.unit
def test_normalize_cache_state_mapping_and_fallback(temp_project_copy: Path):
    """_normalize_cache_state maps known labels and falls back to none_found."""
    service = AIToolsService(project_root=str(temp_project_copy))
    assert service._normalize_cache_state("cache_only") == "utilized"
    assert service._normalize_cache_state("partial_cache") == "partially_utilized"
    assert service._normalize_cache_state("cold_scan") == "invalidated"
    assert service._normalize_cache_state("unknown") == "none_found"
    assert service._normalize_cache_state("OTHER") == "none_found"
    assert service._normalize_cache_state("") is None
    assert service._normalize_cache_state(None) is None
    assert service._normalize_cache_state("   ") is None


@pytest.mark.unit
def test_tool_cache_state_for_log_non_cache_tool_returns_none(temp_project_copy: Path):
    """Tools not in CACHE_AWARE_TOOLS return None when allow_default is False."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_cache_metadata = {}
    assert service._tool_cache_state_for_log("unknown_tool_xyz", False) is None


@pytest.mark.unit
def test_tool_cache_state_for_log_default_none_found(temp_project_copy: Path):
    """Cache-aware tool with no metadata returns none_found when allowed."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_cache_metadata = {}
    # analyze_unused_imports is typically cache-aware
    result = service._tool_cache_state_for_log("analyze_unused_imports", True)
    assert result == "none_found"


@pytest.mark.unit
def test_extract_issue_count_various_shapes(temp_project_copy: Path):
    """_extract_issue_count handles bool, int, float, str and issues_found."""
    service = AIToolsService(project_root=str(temp_project_copy))
    assert service._extract_issue_count("run_test_coverage", {}) is None
    assert service._extract_issue_count("other", {"data": {"summary": {"total_issues": 5}}}) == 5
    assert service._extract_issue_count("other", {"data": {"summary": {"total_issues": True}}}) == 1
    assert service._extract_issue_count("other", {"data": {"summary": {"total_issues": 3.0}}}) == 3
    assert service._extract_issue_count("other", {"data": {"summary": {"total_issues": "7"}}}) == 7
    assert service._extract_issue_count("other", {"issues_found": True}) == 1
    assert service._extract_issue_count("other", {"issues_found": False}) == 0
    assert service._extract_issue_count("other", {"data": {"summary": {"total_issues": "x"}}}) is None


@pytest.mark.unit
def test_infer_cache_mode_from_hits_misses(temp_project_copy: Path):
    """_infer_cache_mode_from_hits_misses returns correct mode strings."""
    service = AIToolsService(project_root=str(temp_project_copy))
    assert service._infer_cache_mode_from_hits_misses(1, 0) == "cache_only"
    assert service._infer_cache_mode_from_hits_misses(2, 1) == "partial_cache"
    assert service._infer_cache_mode_from_hits_misses(0, 1) == "cold_scan"
    assert service._infer_cache_mode_from_hits_misses(0, 0) == "unknown"


@pytest.mark.unit
def test_run_tool_with_timing_raises_tool_execution_error_on_exception(
    temp_project_copy: Path,
):
    """_run_tool_with_timing raises ToolExecutionError when tool_func raises."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_cache_metadata = {}
    service._tools_run_in_current_tier = set()

    def _failing_tool():
        raise ValueError("simulated failure")

    with pytest.raises(Exception) as exc_info:
        service._run_tool_with_timing("fake_tool", _failing_tool)
    exc = cast(ToolExecutionError, exc_info.value)
    assert exc.tool_name == "fake_tool"
    assert exc.elapsed_time >= 0
    assert isinstance(exc.original_exception, ValueError)


@pytest.mark.unit
def test_extract_coverage_cache_metadata_from_json(temp_project_copy: Path):
    """_extract_coverage_cache_metadata reads cache mode from coverage JSON."""
    service = AIToolsService(project_root=str(temp_project_copy))
    jsons_dir = (
        temp_project_copy / "development_tools" / "tests" / "jsons"
    )
    jsons_dir.mkdir(parents=True, exist_ok=True)

    cov_file = jsons_dir / "coverage.json"
    cov_file.write_text(
        json.dumps({
            "_metadata": {"generated_by": "cache (no test execution)"},
        }),
        encoding="utf-8",
    )
    meta = service._extract_coverage_cache_metadata("run_test_coverage")
    assert meta.get("cache_mode") == "cache_only"

    cov_file.write_text(
        json.dumps({
            "_metadata": {"generated_by": "cache merge of shards"},
        }),
        encoding="utf-8",
    )
    meta = service._extract_coverage_cache_metadata("run_test_coverage")
    assert meta.get("cache_mode") == "partial_cache"

    cov_file.write_text(
        json.dumps({
            "_metadata": {"generated_by": "pytest-cov"},
        }),
        encoding="utf-8",
    )
    meta = service._extract_coverage_cache_metadata("run_test_coverage")
    assert meta.get("cache_mode") == "cold_scan"

    # Unknown tool returns empty
    assert service._extract_coverage_cache_metadata("unknown_tool") == {}
