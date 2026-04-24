"""Targeted helper tests for audit_orchestration mixin behavior."""

from __future__ import annotations

import json
import time
import concurrent.futures
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest

from development_tools.shared.service.audit_orchestration import ToolExecutionError
from tests.development_tools.conftest import load_development_tools_module

service_module = load_development_tools_module("shared.service")
audit_module = load_development_tools_module("shared.service.audit_orchestration")
lock_state_module = load_development_tools_module("shared.lock_state")
AIToolsService = service_module.AIToolsService


def _patch_audit_logger(service: Any):
    """Patch audit_orchestration module logger seen by AuditOrchestrationMixin methods.

    ``load_development_tools_module`` may register ``audit_orchestration`` more than once;
    mixin methods always use the function globals from the class object.
    """
    log_fn = service.__class__._log_tool_completion
    mock_logger = MagicMock()
    return patch.dict(log_fn.__globals__, {"logger": mock_logger}), mock_logger


@pytest.mark.unit
def test_get_status_file_mtimes_status_config_keyerror_uses_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """When get_status_config() raises KeyError, use default development_tools status paths."""
    import development_tools.config as dev_config

    def _raise_key() -> dict:
        raise KeyError("status_files")

    monkeypatch.setattr(dev_config, "get_status_config", _raise_key)
    status_dir = tmp_path / "development_tools"
    status_dir.mkdir(parents=True, exist_ok=True)
    (status_dir / "AI_STATUS.md").write_text("ok", encoding="utf-8")

    mtimes = audit_module._get_status_file_mtimes(tmp_path)
    assert mtimes["AI_STATUS.md"] > 0
    assert mtimes["AI_PRIORITIES.md"] == 0.0


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
def test_get_status_file_mtimes_dev_tools_only_targets_dev_tools_outputs(
    tmp_path: Path,
):
    """Dev-tools-only audits write DEV_TOOLS_* files; mtime probe must match."""
    status_dir = tmp_path / "development_tools"
    status_dir.mkdir(parents=True, exist_ok=True)
    (status_dir / "DEV_TOOLS_STATUS.md").write_text("s", encoding="utf-8")
    (status_dir / "AI_STATUS.md").write_text("legacy", encoding="utf-8")

    mtimes = audit_module._get_status_file_mtimes(tmp_path, dev_tools_only=True)
    assert mtimes["DEV_TOOLS_STATUS.md"] > 0
    assert mtimes["DEV_TOOLS_PRIORITIES.md"] == 0.0
    assert "AI_STATUS.md" not in mtimes


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
def test_effective_tier3_state_all_tracks_skipped_is_clean(temp_project_copy: Path):
    """Skipped classifications on all tracks are treated as clean."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service.tier3_test_outcome = {
        "parallel": {"classification": "skipped"},
        "no_parallel": {"classification": "skipped"},
        "development_tools": {"classification": "skipped"},
    }
    assert service._effective_tier3_state() == "clean"


@pytest.mark.unit
def test_service_dev_tools_only_mode_defaults_false(temp_project_copy: Path):
    """Audit entry sets dev_tools_only_mode; default is full-repo scope."""
    service = AIToolsService(project_root=str(temp_project_copy))
    assert service.dev_tools_only_mode is False
    service.dev_tools_only_mode = True
    assert service.dev_tools_only_mode is True


@pytest.mark.unit
def test_get_audit_and_coverage_lock_paths_config_attribute_error_fallback(
    temp_project_copy: Path,
):
    """Lock path helpers fall back to development_tools/*.lock when get_external_value fails."""
    import development_tools as dt_pkg

    service = AIToolsService(project_root=str(temp_project_copy))
    # Patch the same object `from development_tools import config` resolves to (package re-export
    # vs conftest-bound config.py module); string patch on development_tools.config alone can miss.
    with patch.object(dt_pkg.config, "get_external_value", side_effect=AttributeError("x")):
        audit_lock = service._get_audit_lock_file_path()
        cov_lock = service._get_coverage_lock_file_path()
    assert audit_lock == temp_project_copy / "development_tools" / ".audit_in_progress.lock"
    assert cov_lock == temp_project_copy / "development_tools" / ".coverage_in_progress.lock"


@pytest.mark.unit
def test_run_analyze_duplicate_functions_for_audit_tier_and_config(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    """Full-audit body similarity follows tier + config; config load failure uses safe defaults."""
    import development_tools.config as dev_config

    service = AIToolsService(project_root=str(temp_project_copy))
    captured: dict[str, object] = {}

    def _fake_run(**kwargs: object) -> dict:
        captured.clear()
        captured.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(service, "run_analyze_duplicate_functions", _fake_run)

    service.current_audit_tier = 2
    service._run_analyze_duplicate_functions_for_audit()
    assert captured.get("body_for_near_miss_only") is False

    service.current_audit_tier = 3
    service._run_analyze_duplicate_functions_for_audit()
    assert captured.get("body_for_near_miss_only") is True

    monkeypatch.setattr(
        dev_config,
        "get_analyze_duplicate_functions_config",
        lambda: {"run_body_similarity_on_full_audit": False},
    )
    service._run_analyze_duplicate_functions_for_audit()
    assert captured.get("body_for_near_miss_only") is False

    def _boom() -> dict:
        raise RuntimeError("simulated config failure")

    monkeypatch.setattr(dev_config, "get_analyze_duplicate_functions_config", _boom)
    service.current_audit_tier = 3
    service._run_analyze_duplicate_functions_for_audit()
    assert captured.get("body_for_near_miss_only") is True


@pytest.mark.unit
def test_finalize_tier3_audit_scope_dev_tools_only_marks_main_tracks_skipped(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    service.dev_tools_only_mode = True
    service.tier3_test_outcome = {"development_tools": {"state": "clean", "classification": "passed"}}

    service._finalize_tier3_audit_scope()

    assert service._tier3_skipped_main_tracks is True
    assert service._tier3_skipped_dev_track is False
    outcome = cast(dict, service.tier3_test_outcome)
    assert outcome["parallel"]["state"] == "skipped"
    assert outcome["no_parallel"]["state"] == "skipped"
    assert outcome["development_tools"]["classification"] == "passed"


@pytest.mark.unit
def test_finalize_tier3_audit_scope_full_repo_marks_dev_track_skipped_by_default(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    service.dev_tools_only_mode = False
    service.tier3_test_outcome = {"parallel": {"classification": "passed"}, "no_parallel": {"classification": "passed"}}

    service._finalize_tier3_audit_scope()

    assert service._tier3_skipped_main_tracks is False
    assert service._tier3_skipped_dev_track is True
    outcome = cast(dict, service.tier3_test_outcome)
    assert outcome["development_tools"]["state"] == "skipped"
    assert outcome["development_tools"]["classification_reason"] == "not_run_this_audit_scope"


@pytest.mark.unit
def test_finalize_tier3_audit_scope_full_repo_keeps_unified_dev_track_when_present(
    temp_project_copy: Path,
) -> None:
    """Full-repo Tier 3 should preserve unified dev-tools outcome details when available."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service.dev_tools_only_mode = False
    service.tier3_test_outcome = {
        "parallel": {"classification": "passed"},
        "no_parallel": {"classification": "passed"},
        "development_tools": {
            "state": "passed",
            "classification": "passed",
            "classification_reason": "no_dev_tools_failures_unified_run",
        },
    }

    service._finalize_tier3_audit_scope()

    assert service._tier3_skipped_main_tracks is False
    assert service._tier3_skipped_dev_track is False
    outcome = cast(dict, service.tier3_test_outcome)
    assert outcome["development_tools"]["classification"] == "passed"
    assert (
        outcome["development_tools"]["classification_reason"]
        == "no_dev_tools_failures_unified_run"
    )


@pytest.mark.unit
def test_finalize_tier3_audit_scope_full_repo_replaces_cache_only_precheck_dev_track(
    temp_project_copy: Path,
) -> None:
    """cache_only_precheck dev track should not be treated as a fresh unified run."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service.dev_tools_only_mode = False
    service.tier3_test_outcome = {
        "parallel": {"classification": "passed"},
        "no_parallel": {"classification": "passed"},
        "development_tools": {
            "state": "unknown",
            "classification": "unknown",
            "classification_reason": "cache_only_precheck",
        },
    }

    service._finalize_tier3_audit_scope()

    assert service._tier3_skipped_dev_track is True
    outcome = cast(dict, service.tier3_test_outcome)
    assert outcome["development_tools"]["classification"] == "skipped"
    assert (
        outcome["development_tools"]["classification_reason"]
        == "not_run_this_audit_scope"
    )


@pytest.mark.unit
def test_get_tier3_groups_respects_full_vs_dev_tools_only_scope():
    """Tier 3 coverage arms are mutually exclusive by audit scope (V5 §1.9)."""
    from development_tools.shared.audit_tiers import get_tier3_groups

    svc = MagicMock()
    svc.dev_tools_only_mode = False
    main, dev, dep, legacy, static = get_tier3_groups(svc)
    assert [n for n, _ in main] == ["run_test_coverage"]
    assert dev == []
    dep_names = [n for n, _ in dep]
    assert "generate_test_coverage_report" in dep_names
    assert "analyze_test_markers" in dep_names
    legacy_names = [n for n, _ in legacy]
    assert legacy_names == ["analyze_legacy_references", "generate_legacy_reference_report"]
    static_names = [n for n, _ in static]
    assert "verify_process_cleanup" in static_names

    svc.dev_tools_only_mode = True
    main, dev, dep, legacy, static = get_tier3_groups(svc)
    assert main == []
    assert [n for n, _ in dev] == ["generate_dev_tools_coverage"]
    dep_names_dt = [n for n, _ in dep]
    assert "generate_test_coverage_report" not in dep_names_dt
    assert "analyze_backup_health" in dep_names_dt
    legacy_names_dt = [n for n, _ in legacy]
    assert legacy_names_dt == ["analyze_legacy_references"]
    assert "generate_legacy_reference_report" not in legacy_names_dt
    static_names_dt = [n for n, _ in static]
    assert "verify_process_cleanup" in static_names_dt


@pytest.mark.unit
def test_get_tier2_groups_skips_unused_imports_report_when_dev_tools_only():
    """Dev-tools-only audits still analyze unused imports but do not rewrite UNUSED_IMPORTS_REPORT.md (V5 §7.19)."""
    from development_tools.shared.audit_tiers import get_tier2_groups

    svc = MagicMock()
    svc.dev_tools_only_mode = False
    _ind, groups = get_tier2_groups(svc)
    last_group = [n for n, _ in groups[-1]]
    assert last_group == ["analyze_unused_imports", "generate_unused_imports_report"]

    svc.dev_tools_only_mode = True
    _ind_dt, groups_dt = get_tier2_groups(svc)
    last_dt = [n for n, _ in groups_dt[-1]]
    assert last_dt == ["analyze_unused_imports"]


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
    assert "generate_dev_tools_coverage" not in tier3
    assert "analyze_pyright" in tier3
    assert "analyze_bandit" in tier3
    assert "analyze_pip_audit" in tier3
    assert "verify_process_cleanup" in tier3

    service.dev_tools_only_mode = True
    tier2_dt = service._get_expected_tools_for_tier(2)
    assert "generate_unused_imports_report" not in tier2_dt
    tier3_dt = service._get_expected_tools_for_tier(3)
    assert "generate_dev_tools_coverage" in tier3_dt
    assert "run_test_coverage" not in tier3_dt
    assert "generate_test_coverage_report" not in tier3_dt
    assert "generate_legacy_reference_report" not in tier3_dt


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
        / "scopes"
        / "full"
        / "jsons"
        / "tool_timings.json"
    )
    assert timing_file.exists()

    payload = json.loads(timing_file.read_text(encoding="utf-8"))
    assert "runs" in payload and payload["runs"]

    tier2_runs = [r for r in payload["runs"] if r.get("tier_number") == 2]
    assert tier2_runs, "expected a tier-2 timing run from this test"
    run = tier2_runs[-1]
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
        if tool_name == "run_test_coverage":
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
    assert "generate_dev_tools_coverage" not in service._tool_timings


@pytest.mark.unit
def test_run_full_audit_tools_dev_tools_only_runs_dev_coverage_not_main(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    """--dev-tools-only Tier 3 should schedule dev-tools coverage, not main run_test_coverage."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service.dev_tools_only_mode = True
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

    monkeypatch.setattr(
        concurrent.futures, "ThreadPoolExecutor", _FakeExecutor, raising=True
    )
    monkeypatch.setattr(
        concurrent.futures,
        "as_completed",
        lambda futures: iter(list(futures)),
        raising=True,
    )

    assert service._run_full_audit_tools() is True
    assert "generate_dev_tools_coverage" in service._tool_timings
    assert "run_test_coverage" not in service._tool_timings
    assert service._tier3_skipped_main_tracks is True
    assert service._tier3_skipped_dev_track is False
    assert service.tier3_test_outcome.get("parallel", {}).get("classification") == "skipped"


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


@pytest.mark.unit
def test_format_coverage_mode_summary_non_dict_and_partial_tools(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_cache_metadata = "not-a-dict"  # type: ignore[assignment]
    assert service._format_coverage_mode_summary() == ""

    service._tool_cache_metadata = {
        "run_test_coverage": {"cache_mode": "cache_only", "invalidation_reason": "none"},
        "generate_dev_tools_coverage": {},
    }
    summary = service._format_coverage_mode_summary()
    assert "run_test_coverage=cache_only" in summary
    assert "none" in summary
    assert "generate_dev_tools_coverage" not in summary


@pytest.mark.unit
def test_format_cache_mode_summary_skips_bad_entries_and_formats_hits(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_cache_metadata = "bad"  # type: ignore[assignment]
    assert service._format_cache_mode_summary(["analyze_unused_imports"]) == ""

    service._tool_cache_metadata = {
        "analyze_unused_imports": {
            "cache_mode": "partial_cache",
            "hits": 2,
            "misses": 3,
        },
        "analyze_legacy_references": {
            "cache_mode": "cache_only",
            "cache_hits": 1,
            "cache_misses": 0,
        },
        "broken_tool": "skip",  # type: ignore[dict-item]
    }
    out = service._format_cache_mode_summary(
        ["analyze_unused_imports", "analyze_legacy_references", "broken_tool"]
    )
    assert "analyze_unused_imports=partial_cache" in out
    assert "hits=2" in out and "misses=3" in out
    assert "analyze_legacy_references=cache_only" in out
    assert "hits=1" in out and "misses=0" in out


@pytest.mark.unit
def test_is_test_directory_path_heuristics(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))

    p_appdata = MagicMock(spec=Path)
    p_appdata.resolve.return_value = Path(r"C:\Users\X\AppData\Local\Temp\pytest-0\worker")
    assert service._is_test_directory(cast(Path, p_appdata)) is True

    p_tests_data = MagicMock(spec=Path)
    p_tests_data.resolve.return_value = Path("/repo/tests/data/x.txt")
    assert service._is_test_directory(cast(Path, p_tests_data)) is True

    p_tmp_pattern = MagicMock(spec=Path)
    p_tmp_pattern.resolve.return_value = Path("/var/tmp9abcdef/sub/file.py")
    assert service._is_test_directory(cast(Path, p_tmp_pattern)) is True

    p_plain = MagicMock(spec=Path)
    p_plain.resolve.return_value = Path("C:/Program Files/Vendor/app/main.py")
    assert service._is_test_directory(cast(Path, p_plain)) is False


@pytest.mark.unit
def test_extract_coverage_cache_metadata_corrupt_json_returns_empty(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    jsons_dir = temp_project_copy / "development_tools" / "tests" / "jsons"
    jsons_dir.mkdir(parents=True, exist_ok=True)
    bad = jsons_dir / "coverage.json"
    bad.write_text("{not-json", encoding="utf-8")
    assert service._extract_coverage_cache_metadata("run_test_coverage") == {}


@pytest.mark.unit
def test_infer_cache_mode_from_hits_misses_non_positive_total(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    assert service._infer_cache_mode_from_hits_misses(0, 0) == "unknown"
    assert service._infer_cache_mode_from_hits_misses(-1, 0) == "unknown"


@pytest.mark.unit
def test_log_tool_completion_success_maps_invalidated_cache_to_created(
    temp_project_copy: Path,
):
    """On success, cold_scan (invalidated) cache mode is logged as created for operators."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_cache_metadata = {"analyze_unused_imports": {"cache_mode": "cold_scan"}}
    result = {"success": True, "data": {"summary": {"total_issues": 4}}}
    ctx, log = _patch_audit_logger(service)
    with ctx:
        service._log_tool_completion("analyze_unused_imports", result, 0.42)
    msg = log.info.call_args[0][0]
    assert "Completed analyze_unused_imports: PASS" in msg
    assert "issues=4" in msg
    assert "cache=created" in msg


@pytest.mark.unit
def test_log_tool_completion_failure_uses_warning(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_cache_metadata = {}
    ctx, log = _patch_audit_logger(service)
    with ctx:
        service._log_tool_completion("analyze_ruff", {"success": False}, 0.05)
    log.warning.assert_called_once()
    assert "Completed analyze_ruff: FAIL" in log.warning.call_args[0][0]


@pytest.mark.unit
def test_log_tool_completion_truthy_dict_without_success_is_fail(
    temp_project_copy: Path,
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_cache_metadata = {}
    ctx, log = _patch_audit_logger(service)
    with ctx:
        service._log_tool_completion("analyze_bandit", {"data": {"summary": {}}}, 0.02)
    log.warning.assert_called_once()
    assert "FAIL" in log.warning.call_args[0][0]


@pytest.mark.unit
def test_log_tool_completion_generate_unused_imports_report_adds_path(
    temp_project_copy: Path,
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_cache_metadata = {}
    ctx, log = _patch_audit_logger(service)
    with ctx:
        service._log_tool_completion("generate_unused_imports_report", {"success": True}, 0.03)
    msg = log.info.call_args[0][0]
    assert "detailed_report=development_docs/UNUSED_IMPORTS_REPORT.md" in msg


@pytest.mark.unit
@pytest.mark.parametrize(
    ("pstate", "needle"),
    [
        ("requirements_lock_cache_hit", "pip_audit=cache_hit(no_subprocess)"),
        ("skipped_env", "pip_audit=skipped_env"),
        ("executed_subprocess", "pip_audit=subprocess=3.00s"),
        ("error", "pip_audit=error"),
    ],
)
def test_log_tool_completion_pip_audit_fragments(
    temp_project_copy: Path, pstate: str, needle: str
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tool_cache_metadata = {}
    details: dict = {"pip_audit_execution_state": pstate}
    if pstate == "executed_subprocess":
        details["pip_audit_subprocess_seconds"] = 3
    result = {"success": True, "data": {"details": details}}
    ctx, log = _patch_audit_logger(service)
    with ctx:
        service._log_tool_completion("analyze_pip_audit", result, 0.01)
    msg = log.info.call_args[0][0]
    assert needle in msg


