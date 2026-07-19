"""Additional helper coverage for development_tools/shared/service/commands.py."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tests.development_tools.conftest import load_development_tools_module, temp_project_copy_paths

service_module = load_development_tools_module("shared.service")
AIToolsService = service_module.AIToolsService


@pytest.fixture(scope="module")
def temp_project_copy():
    """One demo-tree copy per module (avoids ~5s copytree setup per test)."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "development_tools_demo"
    yield from temp_project_copy_paths(fixture_path.resolve())


@pytest.mark.unit
def test_build_coverage_metadata_includes_changed_domains(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    output = "Domain(s) changed: ['core', 'ui']\nUsing cached coverage data only"

    metadata = service._build_coverage_metadata(output, source="main_coverage")

    assert metadata["cache_mode"] == "cache_only"
    assert metadata["source"] == "main_coverage"
    assert metadata["changed_domains"] == ["core", "ui"]
    assert isinstance(metadata["invalidation_reason"], str)


@pytest.mark.unit
def test_latest_mtime_for_patterns_respects_excludes(tmp_path: Path):
    project_root = tmp_path
    keep = project_root / "tests" / "development_tools" / "test_keep.py"
    skip_prefix = project_root / "tests" / "data" / "test_skip.py"
    skip_exact = project_root / "tests" / "development_tools" / "test_skip_exact.py"
    keep.parent.mkdir(parents=True, exist_ok=True)
    skip_prefix.parent.mkdir(parents=True, exist_ok=True)
    skip_exact.parent.mkdir(parents=True, exist_ok=True)

    keep.write_text("pass", encoding="utf-8")
    skip_prefix.write_text("pass", encoding="utf-8")
    skip_exact.write_text("pass", encoding="utf-8")

    service = AIToolsService(project_root=str(project_root))
    latest = service._latest_mtime_for_patterns(
        patterns=["tests/**/*.py"],
        exclude_prefixes=["tests/data/"],
        exclude_paths=["tests/development_tools/test_skip_exact.py"],
    )

    assert latest > 0
    assert latest == keep.stat().st_mtime


@pytest.mark.unit
def test_is_coverage_file_fresh_compares_source_and_config_mtimes(tmp_path: Path):
    service = AIToolsService(project_root=str(tmp_path))
    coverage_file = tmp_path / ".coverage"
    src_file = tmp_path / "tests" / "unit" / "test_x.py"
    cfg_file = tmp_path / "development_tools" / "config" / "development_tools_config.json"
    src_file.parent.mkdir(parents=True, exist_ok=True)
    cfg_file.parent.mkdir(parents=True, exist_ok=True)
    src_file.write_text("pass", encoding="utf-8")
    cfg_file.write_text("{}", encoding="utf-8")

    assert (
        service._is_coverage_file_fresh(
            coverage_file,
            source_patterns=["tests/**/*.py"],
            config_paths=["development_tools/config/development_tools_config.json"],
        )
        is False
    )

    coverage_file.write_text("data", encoding="utf-8")
    future_time = time.time() + 5
    Path(coverage_file).touch()
    import os

    os.utime(coverage_file, (future_time, future_time))
    assert (
        service._is_coverage_file_fresh(
            coverage_file,
            source_patterns=["tests/**/*.py"],
            config_paths=["development_tools/config/development_tools_config.json"],
        )
        is True
    )


@pytest.mark.unit
def test_to_standard_dev_tools_coverage_result_wraps_legacy_payload(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    raw = {"overall": {"total_missed": 42}, "modules": {}}

    normalized = service._to_standard_dev_tools_coverage_result(raw)

    assert normalized["summary"]["total_issues"] == 42
    assert normalized["summary"]["files_affected"] == 0
    assert normalized["details"] == raw


@pytest.mark.unit
def test_cached_state_extractors_and_failure_classification(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))

    main_cached = {
        "details": {
            "tier3_test_outcome": {
                "parallel": {"classification": "passed"},
                "no_parallel": {"classification": "failed"},
                "development_tools": {"classification": "passed"},
            }
        }
    }
    dev_cached = {
        "details": {"dev_tools_test_outcome": {"classification": "infra_cleanup_error"}}
    }

    assert service._extract_cached_main_coverage_state(main_cached) == "test_failures"
    assert (
        service._extract_cached_dev_tools_state(dev_cached) == "infra_cleanup_error"
    )
    assert service._extract_track_classification({"classification": "passed"}) == "passed"
    assert service._extract_track_classification({}) == "unknown"
    assert service._derive_tier3_state_from_classifications(main_cached["details"]["tier3_test_outcome"]) == "test_failures"
    assert service._is_failure_state("infra_cleanup_error") is True
    assert service._is_failure_state("clean") is False

    legacy_details_only = {
        "details": {
            "coverage_outcome": {
                "parallel": {"classification": "passed"},
                "no_parallel": {"classification": "passed"},
            }
        }
    }
    assert service._extract_cached_main_coverage_state(legacy_details_only) is None


@pytest.mark.unit
def test_is_interrupt_signature_detects_keyboard_interrupt_and_code(
    temp_project_copy: Path,
):
    service = AIToolsService(project_root=str(temp_project_copy))
    assert service._is_interrupt_signature("Traceback\nKeyboardInterrupt", None) is True
    assert service._is_interrupt_signature("", 130) is True
    assert service._is_interrupt_signature("ok", 0) is False


@pytest.mark.unit
def test_is_coverage_file_fresh_invalidates_when_runner_script_is_newer(tmp_path: Path):
    service = AIToolsService(project_root=str(tmp_path))
    coverage_file = tmp_path / ".coverage"
    test_file = tmp_path / "tests" / "unit" / "test_x.py"
    runner = tmp_path / "development_tools" / "tests" / "run_test_coverage.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    runner.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("pass", encoding="utf-8")
    runner.write_text("RUNNER = 'ok'\n", encoding="utf-8")
    coverage_file.write_text("data", encoding="utf-8")

    old_time = time.time() - 10
    Path(coverage_file).touch()
    import os

    os.utime(coverage_file, (old_time, old_time))

    with patch(
        "development_tools.shared.service.tool_wrappers.SCRIPT_REGISTRY",
        {"run_test_coverage": "development_tools/tests/run_test_coverage.py"},
    ):
        assert (
            service._is_coverage_file_fresh(
                coverage_file,
                source_patterns=["tests/**/*.py"],
                tool_names=["run_test_coverage"],
            )
            is False
        )


@pytest.mark.unit
def test_run_flaky_detector_normalizes_json_and_appends_json_flag(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    captured: dict[str, tuple[str, ...]] = {}

    def _fake_run_script(_script_name: str, *args: str, **_kwargs: object) -> dict:
        captured["args"] = tuple(args)
        return {
            "success": True,
            "output": json.dumps(
                {
                    "summary": {"total_issues": 1, "files_affected": 1},
                    "details": {"flaky_tests": ["tests/test_demo.py::test_a"]},
                }
            ),
            "error": "",
            "returncode": 0,
        }

    monkeypatch.setattr(service, "run_script", _fake_run_script)
    save_calls: list[dict] = []

    def _capture_save(_tool: str, _domain: str, data: dict, **_kwargs: object) -> None:
        save_calls.append(data)

    monkeypatch.setitem(
        service.run_flaky_detector.__func__.__globals__,
        "save_tool_result",
        _capture_save,
    )

    result = service.run_flaky_detector("--max-runs", "3")

    assert result["success"] is True
    assert "--json" in captured["args"]
    assert result["data"]["summary"]["total_issues"] == 1
    assert save_calls and save_calls[-1]["summary"]["files_affected"] == 1


@pytest.mark.unit
def test_run_verify_process_cleanup_returns_error_on_invalid_json(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": True,
            "output": "not-json",
            "error": "",
            "returncode": 0,
        },
    )

    result = service.run_verify_process_cleanup("--target", "pytest")

    assert result["success"] is False
    assert "Invalid JSON output" in result["error"]
    assert result["returncode"] == 0


@pytest.mark.unit
def test_load_cached_result_if_available_dict_exception_and_non_dict(
    temp_project_copy: Path,
):
    service = AIToolsService(project_root=str(temp_project_copy))

    with patch(
        "development_tools.shared.output_storage.load_tool_result",
        return_value={"summary": {"total_issues": 0}},
    ):
        assert service._load_cached_result_if_available("analyze_ruff", "static_checks") == {
            "summary": {"total_issues": 0},
        }

    with patch(
        "development_tools.shared.output_storage.load_tool_result",
        side_effect=RuntimeError("simulated load failure"),
    ):
        assert service._load_cached_result_if_available("analyze_ruff", "static_checks") is None

    with patch(
        "development_tools.shared.output_storage.load_tool_result",
        return_value=["not", "a", "dict"],
    ):
        assert service._load_cached_result_if_available("analyze_ruff", "static_checks") is None


@pytest.mark.unit
def test_get_audit_related_lock_paths_uses_config_overrides(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    import development_tools as dt_pkg

    service = AIToolsService(project_root=str(temp_project_copy))

    def _fake_external_value(key: str, default: str) -> str:
        if key == "paths.audit_lock_file":
            return "locks/custom_audit.lock"
        if key == "paths.coverage_lock_file":
            return "locks/custom_coverage.lock"
        return default

    monkeypatch.setattr(
        dt_pkg.config,
        "get_external_value",
        _fake_external_value,
    )

    paths = service._get_audit_related_lock_paths()

    assert paths[0] == temp_project_copy / "locks" / "custom_audit.lock"
    assert paths[1] == temp_project_copy / "locks" / "custom_coverage.lock"
    assert paths[2] == temp_project_copy / "locks" / ".coverage_dev_tools_in_progress.lock"


@pytest.mark.unit
def test_get_existing_audit_related_locks_cleans_stale_and_returns_active(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    active = temp_project_copy / "active.lock"
    stale = temp_project_copy / "stale.lock"
    malformed = temp_project_copy / "bad.lock"

    monkeypatch.setattr(
        service,
        "_get_audit_related_lock_paths",
        lambda: [active, stale, malformed],
    )
    monkeypatch.setitem(
        service._get_existing_audit_related_locks.__func__.__globals__,
        "evaluate_lock_set",
        lambda _paths: {
            "active": [{"path": active}],
            "stale": [{"path": stale}],
            "malformed": [{"path": malformed}],
        },
    )
    cleaned: list[Path] = []
    monkeypatch.setitem(
        service._get_existing_audit_related_locks.__func__.__globals__,
        "cleanup_lock_paths",
        lambda paths: cleaned.extend(paths) or len(paths),
    )

    assert service._get_existing_audit_related_locks() == [active]
    assert cleaned == [stale, malformed]


@pytest.mark.unit
def test_run_docs_blocks_when_audit_locks_exist(temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch):
    service = AIToolsService(project_root=str(temp_project_copy))
    lock_path = temp_project_copy / "development_tools" / ".audit_in_progress.lock"
    monkeypatch.setattr(service, "_get_existing_audit_related_locks", lambda: [lock_path])
    run_script = MagicMock()
    monkeypatch.setattr(service, "run_script", run_script)

    assert service.run_docs() is False
    run_script.assert_not_called()


@pytest.mark.unit
def test_run_docs_collects_script_and_subcheck_failures(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(service, "_get_existing_audit_related_locks", lambda: [])
    monkeypatch.setattr(
        service,
        "run_script",
        lambda name, *args, **kwargs: {
            "success": name != "generate_module_dependencies",
            "error": f"{name} failed",
            "output": "",
        },
    )
    monkeypatch.setattr(service, "generate_directory_trees", lambda: None)
    monkeypatch.setattr(service, "_run_doc_sync_check", lambda: False)

    assert service.run_docs() is False


@pytest.mark.unit
def test_run_validate_parses_output_and_saves_result(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    payload = {"summary": {"total_issues": 0}, "details": {"ok": True}}
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {"success": True, "output": json.dumps(payload), "error": ""},
    )
    saved: list[tuple[str, str, dict]] = []
    monkeypatch.setitem(
        service.run_validate.__func__.__globals__,
        "save_tool_result",
        lambda tool, domain, data, **_kwargs: saved.append((tool, domain, data)),
    )

    assert service.run_validate() is True
    assert service.validation_results["success"] is True
    assert saved == [("analyze_ai_work", "ai_work", payload)]


@pytest.mark.unit
def test_run_validate_failure_returns_false(temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {"success": False, "output": "", "error": "boom"},
    )

    assert service.run_validate() is False


@pytest.mark.unit
def test_run_config_handles_json_suffix_and_save_failure(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    payload = {"summary": {"total_issues": 2}, "details": {"config_valid": False}}
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {
            "success": True,
            "output": "human preface\n" + json.dumps(payload),
            "error": "",
        },
    )
    monkeypatch.setitem(
        service.run_config.__func__.__globals__,
        "save_tool_result",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("save failed")),
    )

    assert service.run_config() is True


@pytest.mark.unit
def test_run_analyze_config_returns_parsed_data_and_updates_cache(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.results_cache = {}
    payload = {"summary": {"total_issues": 0}, "details": {"config_valid": True}}
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {"success": True, "output": json.dumps(payload), "error": ""},
    )
    saved: list[dict] = []
    monkeypatch.setitem(
        service.run_analyze_config.__func__.__globals__,
        "save_tool_result",
        lambda _tool, _domain, data, **_kwargs: saved.append(data),
    )

    result = service.run_analyze_config()

    assert result["success"] is True
    assert result["data"] == payload
    assert service.results_cache["analyze_config"] == payload
    assert saved == [payload]


@pytest.mark.unit
def test_run_analyze_config_invalid_json_preserves_script_success(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {"success": True, "output": "not-json", "error": ""},
    )

    result = service.run_analyze_config()

    assert result["success"] is True
    assert "data" not in result


@pytest.mark.unit
def test_run_workflow_stops_on_trigger_or_audit_failure(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(service, "check_trigger_requirements", lambda _task: False)
    assert service.run_workflow("docs") is False

    monkeypatch.setattr(service, "check_trigger_requirements", lambda _task: True)
    monkeypatch.setattr(
        service,
        "run_audit_first",
        lambda _task: {"success": False, "error": "audit failed"},
    )
    assert service.run_workflow("docs") is False


@pytest.mark.unit
def test_run_workflow_executes_task_and_validation(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(service, "check_trigger_requirements", lambda _task: True)
    monkeypatch.setattr(service, "run_audit_first", lambda _task: {"success": True})
    monkeypatch.setattr(service, "execute_task", lambda _task, _data: True)
    monkeypatch.setattr(
        service,
        "validate_work",
        lambda _task, data: {"success": True, "seen": data},
    )
    shown: list[dict] = []
    monkeypatch.setattr(service, "show_validation_report", lambda result: shown.append(result))

    assert service.run_workflow("docs", {"x": 1}) is True
    assert shown == [{"success": True, "seen": {"x": 1}}]


@pytest.mark.unit
def test_run_version_sync_records_success_and_failure(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    calls: list[tuple[object, ...]] = []

    def _success(*args: object, **_kwargs: object) -> dict:
        calls.append(args)
        return {"success": True, "output": "ok"}

    monkeypatch.setattr(service, "run_script", _success)

    assert service.run_version_sync("todo") is True
    assert service.fix_version_sync_results == {"success": True, "output": "ok"}
    assert calls[-1] == ("fix_version_sync", "sync", "--scope", "todo")

    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {"success": False, "error": "bad scope"},
    )

    assert service.run_version_sync("bad") is False


@pytest.mark.unit
def test_run_documentation_sync_persists_only_on_success(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    persisted: list[bool] = []

    monkeypatch.setattr(service, "_run_doc_sync_check", lambda: True)
    monkeypatch.setattr(
        service,
        "_persist_documentation_sync_aggregate_json",
        lambda: persisted.append(True),
        raising=False,
    )

    assert service.run_documentation_sync() is True
    assert persisted == [True]

    monkeypatch.setattr(service, "_run_doc_sync_check", lambda: False)

    assert service.run_documentation_sync() is False
    assert persisted == [True]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("fix_type", "expected_flag"),
    [
        ("all", "--all"),
        ("ascii", "--fix-ascii"),
        ("fix-ascii", "--fix-ascii"),
        ("number-headings", "--number-headings"),
        ("add-addresses", "--add-addresses"),
        ("convert-links", "--convert-links"),
    ],
)
def test_run_documentation_fix_builds_expected_args(
    temp_project_copy: Path,
    monkeypatch: pytest.MonkeyPatch,
    fix_type: str,
    expected_flag: str,
):
    service = AIToolsService(project_root=str(temp_project_copy))
    captured: dict[str, tuple[object, ...]] = {}

    def _fake_run_script(*args: object, **_kwargs: object) -> dict:
        captured["args"] = args
        return {"success": True}

    monkeypatch.setattr(service, "run_script", _fake_run_script)

    assert service.run_documentation_fix(fix_type, dry_run=True) is True
    assert captured["args"][0] == "fix_documentation"
    assert "--dry-run" in captured["args"]
    assert expected_flag in captured["args"]


@pytest.mark.unit
def test_run_documentation_fix_reports_returncode_when_error_is_empty(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": False,
            "error": "",
            "returncode": 7,
            "output": "details",
        },
    )

    assert service.run_documentation_fix("unknown") is False


@pytest.mark.unit
def test_run_dev_tools_coverage_reuses_fresh_cache(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.tier3_test_outcome = {"parallel": {"classification": "passed"}}
    cached_payload = {
        "overall": {"total_missed": 5},
        "details": {"dev_tools_test_outcome": {"classification": "passed"}},
    }

    monkeypatch.setattr(service, "_is_coverage_file_fresh", lambda *_a, **_k: True)
    monkeypatch.setattr(
        service,
        "_load_cached_result_if_available",
        lambda *_a, **_k: cached_payload,
    )
    run_script = MagicMock()
    monkeypatch.setattr(service, "run_script", run_script)

    result = service.run_dev_tools_coverage()

    assert result["success"] is True
    assert result["cache_metadata"]["cache_mode"] == "cache_only"
    assert result["data"]["summary"]["total_issues"] == 5
    assert service.tier3_test_outcome["development_tools"]["from_cache"] is True
    run_script.assert_not_called()


@pytest.mark.unit
def test_run_dev_tools_coverage_ignores_failed_cached_state(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.tier3_test_outcome = {}
    cached_payload = {
        "summary": {"total_issues": 1},
        "details": {"dev_tools_test_outcome": {"classification": "failed"}},
    }
    lock_file = temp_project_copy / "development_tools" / ".coverage_dev_tools_in_progress.lock"
    lock_file.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(service, "_is_coverage_file_fresh", lambda *_a, **_k: True)
    monkeypatch.setattr(
        service,
        "_load_cached_result_if_available",
        lambda *_a, **_k: cached_payload,
    )
    monkeypatch.setitem(
        service.run_dev_tools_coverage.__func__.__globals__,
        "write_lock_metadata",
        lambda path, **_kwargs: Path(path).write_text("{}", encoding="utf-8") or True,
    )
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {
            "success": False,
            "output": "",
            "error": "pytest failed",
            "returncode": 1,
        },
    )

    result = service.run_dev_tools_coverage()

    assert result["success"] is False
    assert "pytest failed" in result["error"]
    assert service.tier3_test_outcome["development_tools"]["classification"] == "failed"
    assert not lock_file.exists()


@pytest.mark.unit
def test_run_coverage_regeneration_reuses_fresh_cache(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.tier3_test_outcome = {
        "development_tools": {"classification": "skipped", "state": "skipped"}
    }
    cached_result = {
        "summary": {"total_issues": 0},
        "details": {
            "tier3_test_outcome": {
                "parallel": {"classification": "passed"},
                "no_parallel": {"classification": "passed"},
            }
        },
    }
    cached_summary = {"overall": {"missed": 12}}

    monkeypatch.setattr(service, "_is_coverage_file_fresh", lambda *_a, **_k: True)
    monkeypatch.setattr(
        service,
        "_load_cached_result_if_available",
        lambda *_a, **_k: cached_result,
    )
    monkeypatch.setattr(service, "_load_coverage_summary", lambda: cached_summary)
    run_script = MagicMock()
    monkeypatch.setattr(service, "run_script", run_script)

    assert service.run_coverage_regeneration() is True
    assert service._tool_cache_metadata["run_test_coverage"]["cache_mode"] == "cache_only"
    assert service.tier3_test_outcome["state"] == "clean"
    assert service.tier3_test_outcome["development_tools"]["classification"] == "skipped"
    run_script.assert_not_called()


@pytest.mark.unit
def test_run_coverage_regeneration_does_not_reuse_failed_cached_state(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.tier3_test_outcome = {}
    cached_result = {
        "details": {
            "tier3_test_outcome": {
                "parallel": {"classification": "failed"},
                "no_parallel": {"classification": "passed"},
            }
        }
    }
    lock_file = temp_project_copy / "development_tools" / ".coverage_in_progress.lock"
    lock_file.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(service, "_is_coverage_file_fresh", lambda *_a, **_k: True)
    monkeypatch.setattr(
        service,
        "_load_cached_result_if_available",
        lambda *_a, **_k: cached_result,
    )
    monkeypatch.setattr(service, "_load_coverage_summary", lambda: {"overall": {"missed": 0}})
    monkeypatch.setitem(
        service.run_coverage_regeneration.__func__.__globals__,
        "write_lock_metadata",
        lambda path, **_kwargs: Path(path).write_text("{}", encoding="utf-8") or True,
    )
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {
            "success": False,
            "output": "",
            "error": "coverage crashed",
            "returncode": 2,
        },
    )

    assert service.run_coverage_regeneration() is False
    assert service.tier3_test_outcome["state"] == "coverage_failed"
    assert not lock_file.exists()


@pytest.mark.unit
def test_run_analyze_system_signals_parses_prefixed_json_and_saves(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    payload = {"summary": {"total_issues": 0}, "details": {"health": "ok"}}
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {
            "success": True,
            "output": "preface\n" + json.dumps(payload) + "\ntrailing text",
        },
    )
    saved: list[dict] = []
    monkeypatch.setitem(
        service.run_analyze_system_signals.__func__.__globals__,
        "save_tool_result",
        lambda _tool, _domain, data, **_kwargs: saved.append(data),
    )

    assert service.run_analyze_system_signals() is True
    assert service.system_signals == payload
    assert saved == [payload]


@pytest.mark.unit
def test_run_analyze_system_signals_rejects_nonstandard_json_and_empty_output(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {"success": True, "output": json.dumps({"summary": {}})},
    )

    assert service.run_analyze_system_signals() is False

    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {"success": True, "output": ""},
    )

    assert service.run_analyze_system_signals() is False


@pytest.mark.unit
def test_run_test_markers_normalizes_missing_items_and_handles_no_output(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    payload = {
        "summary": {"total_issues": None, "files_affected": None},
        "details": {
            "missing": [{"file": "tests/a.py"}],
            "missing_domain": [["tests/b.py", "test_b"]],
        }
    }
    saved: list[dict] = []
    captured: dict[str, tuple[object, ...]] = {}

    def _run_script(*args: object, **_kwargs: object) -> dict:
        captured["args"] = args
        return {"success": False, "output": json.dumps(payload), "returncode": 1}

    monkeypatch.setattr(service, "run_script", _run_script)
    monkeypatch.setitem(
        service.run_test_markers.__func__.__globals__,
        "save_tool_result",
        lambda _tool, _domain, data, **_kwargs: saved.append(data),
    )

    result = service.run_test_markers(action="fix", dry_run=True)

    assert result["success"] is True  # fix/analyze actions succeed when JSON parses

    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {"success": False, "output": json.dumps(payload), "returncode": 1},
    )
    check_result = service.run_test_markers(action="check")
    assert check_result["success"] is False
    assert "--fix" in captured["args"]
    assert "--dry-run" in captured["args"]
    assert result["data"]["summary"]["total_issues"] == 2
    assert result["data"]["summary"]["files_affected"] == 2
    assert saved[-1]["summary"]["total_issues"] == 2

    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {"success": False, "output": "", "returncode": 3},
    )

    failed = service.run_test_markers(action="unknown")
    assert failed["success"] is False
    assert "No output received" in failed["error"]


@pytest.mark.unit
def test_execute_task_routes_known_and_unknown_types(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    calls: list[str] = []

    monkeypatch.setattr(
        service,
        "run_script",
        lambda name, *_a, **_k: calls.append(name) or {"success": True},
    )
    monkeypatch.setattr(
        service,
        "run_nightly_test_suite",
        lambda *, strict=False: {"state": "clean"},
    )

    assert service.execute_task("documentation") is True
    assert service.execute_task("function_registry") is True
    assert service.execute_task("module_dependencies") is True
    assert service.execute_task("nightly-test-suite") is True
    assert service.execute_task("nightly-audit") is True
    assert service.execute_task("unknown-task") is False
    assert calls == [
        "generate_documentation",
        "generate_function_registry",
        "generate_module_dependencies",
    ]

    monkeypatch.setattr(
        service,
        "run_nightly_test_suite",
        lambda *, strict=False: {"state": "failed"},
    )
    assert service.execute_task("nightly-audit") is False


@pytest.mark.unit
def test_generate_directory_trees_success_fail_and_safeguard(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))

    monkeypatch.setattr(
        service, "run_script", lambda *_a, **_k: {"success": True, "error": ""}
    )
    assert service.generate_directory_trees() is True

    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {"success": False, "error": "boom"},
    )
    assert service.generate_directory_trees() is False

    def _blocked(*_a, **_k):
        raise RuntimeError("Cannot write DIRECTORY_TREE.md during audit")

    monkeypatch.setattr(service, "run_script", _blocked)
    assert service.generate_directory_trees() is False

    def _other(*_a, **_k):
        raise RuntimeError("unrelated failure")

    monkeypatch.setattr(service, "run_script", _other)
    with pytest.raises(RuntimeError, match="unrelated"):
        service.generate_directory_trees()


@pytest.mark.unit
def test_run_cleanup_full_flag_and_exception(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    captured_kwargs: dict[str, object] = {}

    class _FakeCleanup:
        def __init__(self, project_root):
            self.project_root = project_root

        def cleanup_all(self, **kwargs):
            captured_kwargs.update(kwargs)
            return {"removed": 3}

    import development_tools.shared.fix_project_cleanup as cleanup_mod

    monkeypatch.setattr(cleanup_mod, "ProjectCleanup", _FakeCleanup)

    result = service.run_cleanup(full=True, dry_run=True)
    assert result["success"] is True
    assert result["data"]["removed"] == 3
    assert captured_kwargs["cache"] is True
    assert captured_kwargs["test_data"] is True
    assert captured_kwargs["coverage"] is True
    assert captured_kwargs["include_tool_caches"] is True
    assert captured_kwargs["dry_run"] is True

    class _BoomCleanup:
        def __init__(self, *_a, **_k):
            raise RuntimeError("cleanup exploded")

    monkeypatch.setattr(cleanup_mod, "ProjectCleanup", _BoomCleanup)
    failed = service.run_cleanup()
    assert failed["success"] is False
    assert "cleanup exploded" in failed["error"]


@pytest.mark.unit
def test_run_status_skip_status_files_avoids_generators(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "_generate_ai_status_document",
        lambda: (_ for _ in ()).throw(AssertionError("should not run")),
    )
    monkeypatch.setattr(
        service,
        "_generate_ai_priorities_document",
        lambda: (_ for _ in ()).throw(AssertionError("should not run")),
    )
    monkeypatch.setattr(
        service,
        "_generate_consolidated_report",
        lambda: (_ for _ in ()).throw(AssertionError("should not run")),
    )
    service.run_status(skip_status_files=True)
