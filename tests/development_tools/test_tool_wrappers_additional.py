"""Additional branch coverage tests for shared/service/tool_wrappers.py."""

import json
import subprocess
from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module, temp_project_copy_paths


service_module = load_development_tools_module("shared.service")
tool_wrappers_module = load_development_tools_module("shared.service.tool_wrappers")
AIToolsService = service_module.AIToolsService


@pytest.fixture(scope="module")
def temp_project_copy():
    """One demo-tree copy per module (avoids ~5s copytree setup per test)."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "development_tools_demo"
    yield from temp_project_copy_paths(fixture_path.resolve())


@pytest.mark.unit
def test_run_analyze_function_registry_keyword_fallback_marks_issues(
    temp_project_copy, monkeypatch
):
    """Non-JSON diagnostic output should still be treated as actionable issues."""
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": False,
            "output": "2 items are missing from registry",
            "error": "non-zero",
            "returncode": 1,
        },
        raising=True,
    )

    result = service.run_analyze_function_registry()

    assert result["success"] is True
    assert result["issues_found"] is True
    assert result["error"] == ""


@pytest.mark.unit
def test_run_analyze_module_dependencies_builds_standard_summary(
    temp_project_copy, monkeypatch
):
    """Parsed dependency summary should be normalized and cached."""
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": True,
            "output": "dependency output",
            "error": "",
            "returncode": 0,
        },
        raising=True,
    )
    monkeypatch.setattr(
        service,
        "_parse_module_dependency_report",
        lambda _output: {"missing_dependencies": 2, "missing_sections": ["A", "B"]},
        raising=True,
    )
    monkeypatch.setattr(
        tool_wrappers_module, "save_tool_result", lambda *_a, **_k: None, raising=True
    )

    result = service.run_analyze_module_dependencies()

    assert result["data"]["summary"]["total_issues"] == 4
    assert result["issues_found"] is True
    # Cache stores standard format (summary/details) for report data loading
    assert service.results_cache["analyze_module_dependencies"]["details"]["missing_dependencies"] == 2


@pytest.mark.unit
def test_run_analyze_module_refactor_candidates_includes_cli_flags(
    temp_project_copy, monkeypatch
):
    """Wrapper should pass include flags and store parsed JSON output."""
    service = AIToolsService(project_root=str(temp_project_copy))
    captured: dict[str, tuple[object, ...] | None] = {"args": None}

    def _fake_run_script(_script_name, *args, **_kwargs):
        captured["args"] = args
        return {
            "success": True,
            "output": '{"summary":{"total_issues":3,"files_affected":2},"details":{"modules":[]}}',
            "error": "",
            "returncode": 0,
        }

    monkeypatch.setattr(service, "run_script", _fake_run_script, raising=True)
    monkeypatch.setattr(
        tool_wrappers_module, "save_tool_result", lambda *_a, **_k: None, raising=True
    )

    result = service.run_analyze_module_refactor_candidates(
        include_tests=True, include_dev_tools=True
    )

    captured_args = captured["args"]
    assert captured_args is not None
    assert "--include-tests" in captured_args
    assert "--include-dev-tools" in captured_args
    assert result["issues_found"] is True
    assert result["data"]["summary"]["total_issues"] == 3


@pytest.mark.unit
def test_run_analyze_facade_shims_saves_scoped_result(temp_project_copy, monkeypatch):
    """Facade/shim wrapper should parse JSON and save through scoped output storage."""
    service = AIToolsService(project_root=str(temp_project_copy))
    saved: list[tuple[str, str, dict]] = []

    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": True,
            "output": '{"summary":{"total_issues":1,"files_affected":1},"details":{"findings":[]}}',
            "error": "",
            "returncode": 0,
        },
        raising=True,
    )
    monkeypatch.setitem(
        service.run_analyze_facade_shims.__func__.__globals__,
        "save_tool_result",
        lambda tool, domain, data, **_kwargs: saved.append((tool, domain, data)),
    )

    result = service.run_analyze_facade_shims()

    assert result["issues_found"] is True
    assert saved and saved[0][0] == "analyze_facade_shims"
    assert saved[0][1] == "functions"


@pytest.mark.unit
def test_run_decision_support_saves_error_when_no_json_data(temp_project_copy, monkeypatch):
    """Wrapper should emit a standard error payload when decision support returns no JSON."""
    service = AIToolsService(project_root=str(temp_project_copy))
    saved_payload = {}

    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": True,
            "output": "plain text output only",
            "error": "",
            "returncode": 0,
        },
        raising=True,
    )
    monkeypatch.setattr(
        service, "_extract_decision_insights", lambda _result: None, raising=True
    )

    def _capture_save(_tool, _domain, data, **_kwargs):
        saved_payload["data"] = data

    monkeypatch.setitem(
        service.run_decision_support.__func__.__globals__,
        "save_tool_result",
        _capture_save,
    )

    service.run_decision_support()

    assert "produced no JSON output" in saved_payload["data"]["details"]["error"]


@pytest.mark.unit
def test_static_check_cache_metadata_branches():
    assert tool_wrappers_module._static_check_tool_cache_metadata(
        from_disk_cache=True
    ) == {"cache_mode": "cache_hit"}
    assert tool_wrappers_module._static_check_cache_metadata_from_analyzer_details(None) == {
        "cache_mode": "cold_scan"
    }

    hit = tool_wrappers_module._static_check_cache_metadata_from_analyzer_details(
        {"shard_run": {"fragment_cache_hits": 2, "fragment_cache_misses": 0, "mode": "sharded"}}
    )
    assert hit["cache_mode"] == "cache_hit"
    assert hit["fragment_hits"] == 2

    partial = tool_wrappers_module._static_check_cache_metadata_from_analyzer_details(
        {
            "shard_run": {
                "fragment_cache_hits": 1,
                "fragment_cache_misses": 3,
                "subprocesses": 3,
                "parity_note": "ok",
                "reason": "fallback",
            }
        }
    )
    assert partial["cache_mode"] == "partial_cache"
    assert partial["parity_note"] == "ok"
    assert partial["shard_fallback_reason"] == "fallback"


@pytest.mark.unit
def test_run_script_unregistered_missing_timeout_and_keyboard_interrupt(
    temp_project_copy, monkeypatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    assert "not registered" in service.run_script("missing_tool")["error"]

    monkeypatch.setitem(
        service.run_script.__func__.__globals__,
        "SCRIPT_REGISTRY",
        {"registered_missing": "does/not/exist.py", "registered_ok": "tool.py"},
    )
    assert "not found" in service.run_script("registered_missing")["error"]

    module_file = tool_wrappers_module.__file__
    assert module_file is not None
    script = Path(module_file).resolve().parent.parent.parent / "tool.py"
    script.write_text("pass\n", encoding="utf-8")
    try:
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *_a, **_k: (_ for _ in ()).throw(subprocess.TimeoutExpired("x", 1)),
        )
        timeout = service.run_script("registered_ok", timeout=60)
        assert timeout["success"] is False
        assert "timed out" in timeout["error"]

        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *_a, **_k: (_ for _ in ()).throw(KeyboardInterrupt()),
        )
        interrupted = service.run_script("registered_ok")
        assert interrupted["interrupted"] is True
        assert interrupted["returncode"] == 130
    finally:
        script.unlink(missing_ok=True)


@pytest.mark.unit
def test_run_analyze_documentation_preserves_cached_overlap_details(
    temp_project_copy, monkeypatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    cached = {
        "data": {
            "details": {
                "section_overlaps": {"A": ["B"]},
                "consolidation_recommendations": ["merge A/B"],
            }
        }
    }
    monkeypatch.setitem(
        service.run_analyze_documentation.__func__.__globals__,
        "load_tool_result",
        lambda *_a, **_k: cached,
    )
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {
            "success": True,
            "output": '{"summary":{"total_issues":0},"details":{}}',
            "error": "",
        },
    )
    saved: list[dict] = []
    monkeypatch.setitem(
        service.run_analyze_documentation.__func__.__globals__,
        "save_tool_result",
        lambda _tool, _domain, data, **_kwargs: saved.append(data),
    )

    result = service.run_analyze_documentation(include_overlap=False)

    assert result["success"] is True
    assert result["data"]["details"]["section_overlaps"] == {"A": ["B"]}
    assert result["data"]["details"]["overlap_data_source"] == "cached"
    assert saved[-1]["details"]["consolidation_recommendations"] == ["merge A/B"]


@pytest.mark.unit
def test_run_analyze_documentation_keyword_fallback_marks_issues(
    temp_project_copy, monkeypatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setitem(
        service.run_analyze_documentation.__func__.__globals__,
        "load_tool_result",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("cache failure")),
    )
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {
            "success": False,
            "output": "Found verbatim duplicate and placeholder text",
            "error": "nonzero",
        },
    )

    result = service.run_analyze_documentation()

    assert result["success"] is True
    assert result["issues_found"] is True
    assert result["error"] == ""


@pytest.mark.unit
def test_run_analyze_functions_parses_and_saves_json(temp_project_copy, monkeypatch):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.exclusion_config = {"include_tests": True, "include_dev_tools": True}
    captured: dict[str, tuple] = {}

    def _fake_run_script(_name, *args, **_kwargs):
        captured["args"] = args
        return {
            "success": True,
            "output": '{"summary":{"total_issues":0},"details":{"total_functions":1}}',
            "error": "",
        }

    monkeypatch.setattr(service, "run_script", _fake_run_script)
    saved: list[dict] = []
    monkeypatch.setitem(
        service.run_analyze_functions.__func__.__globals__,
        "save_tool_result",
        lambda _tool, _domain, data, **_kwargs: saved.append(data),
    )

    result = service.run_analyze_functions()

    assert "--include-tests" in captured["args"]
    assert "--include-dev-tools" in captured["args"]
    assert result["data"]["details"]["total_functions"] == 1
    assert service.results_cache["analyze_functions"] == saved[-1]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("archive/old_notes.md", True),
        ("docs/archived/legacy.md", True),
        ("development_docs/changelog_history/2024.md", True),
        ("TODO.md", True),
        ("development_docs/PLANS.md", True),
        ("development_tools/AI_PRIORITIES.md", True),
        ("development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN.md", True),
        ("plan_migration.md", True),
        ("development_tools/shared/service/core.py", False),
        ("communication/bot.py", False),
    ],
)
def test_is_historical_inventory_guard_path_matrix(temp_project_copy, path, expected):
    service = AIToolsService(project_root=str(temp_project_copy))
    assert service._is_historical_inventory_guard_path(path) is expected


@pytest.mark.unit
def test_run_analyze_unused_functions_parses_flags_and_saves(
    temp_project_copy, monkeypatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.exclusion_config = {"include_tests": True, "include_dev_tools": True}
    captured: dict[str, tuple] = {}
    saved: list[tuple[str, str, dict]] = []

    def _fake_run_script(_name, *args, **_kwargs):
        captured["args"] = args
        return {
            "success": True,
            "output": '{"summary":{"total_issues":2},"details":{}}',
            "error": "",
            "returncode": 0,
        }

    monkeypatch.setattr(service, "run_script", _fake_run_script, raising=True)
    monkeypatch.setitem(
        service.run_analyze_unused_functions.__func__.__globals__,
        "save_tool_result",
        lambda tool, domain, data, **_kwargs: saved.append((tool, domain, data)),
    )

    result = service.run_analyze_unused_functions(private_only=True, max_results=25)

    assert "--include-tests" in captured["args"]
    assert "--include-dev-tools" in captured["args"]
    assert "--private-only" in captured["args"]
    assert "--max-results" in captured["args"]
    assert "25" in captured["args"]
    assert result["issues_found"] is True
    assert result["success"] is True
    assert saved and saved[0][0] == "analyze_unused_functions"
    assert saved[0][1] == "functions"


@pytest.mark.unit
def test_run_analyze_duplicate_functions_parses_flags_and_saves(
    temp_project_copy, monkeypatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.exclusion_config = {"include_tests": False, "include_dev_tools": True}
    captured: dict[str, tuple] = {}
    saved: list[tuple[str, str, dict]] = []

    def _fake_run_script(_name, *args, **_kwargs):
        captured["args"] = args
        return {
            "success": True,
            "output": '{"summary":{"total_issues":1},"details":{"groups":[]}}',
            "error": "",
            "returncode": 0,
        }

    monkeypatch.setattr(service, "run_script", _fake_run_script, raising=True)
    monkeypatch.setitem(
        service.run_analyze_duplicate_functions.__func__.__globals__,
        "save_tool_result",
        lambda tool, domain, data, **_kwargs: saved.append((tool, domain, data)),
    )

    result = service.run_analyze_duplicate_functions(
        min_overall=0.8,
        min_name=0.9,
        consider_body_similarity=True,
        body_for_near_miss_only=True,
    )

    assert "--include-tests" not in captured["args"]
    assert "--include-dev-tools" in captured["args"]
    assert "--consider-body-similarity" in captured["args"]
    assert "--body-for-near-miss" in captured["args"]
    assert "--min-overall" in captured["args"]
    assert "0.8" in captured["args"]
    assert result["issues_found"] is True
    assert saved[0][0] == "analyze_duplicate_functions"


@pytest.mark.unit
def test_persist_documentation_sync_aggregate_json_shape(
    temp_project_copy, monkeypatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.docs_sync_summary = {
        "summary": {"total_issues": 3, "status": "FAIL"},
        "details": {
            "path_drift_files": ["a.md", "b.md"],
            "paired_doc_issues": 1,
            "path_drift_issues": 2,
            "ascii_issues": 0,
            "example_marker_hint_count": 1,
            "example_marker_findings": {"x.md": ["hint"]},
        },
    }
    service.docs_sync_results = {
        "all_results": {
            "paired_docs": {"ok": False},
            "path_drift": {"files": 2},
        }
    }
    saved: list[dict] = []
    monkeypatch.setitem(
        service._persist_documentation_sync_aggregate_json.__func__.__globals__,
        "save_tool_result",
        lambda _tool, _domain, data, **_kwargs: saved.append(data),
    )

    data = service._persist_documentation_sync_aggregate_json()

    assert data["summary"]["total_issues"] == 3
    assert data["summary"]["files_affected"] == 2
    assert data["summary"]["status"] == "FAIL"
    assert data["details"]["paired_doc_issues"] == 1
    assert data["details"]["ascii_compliance_issues"] == 0
    assert data["details"]["paired_docs"] == {"ok": False}
    assert data["details"]["example_marker_hint_count"] == 1
    assert saved and saved[0]["summary"]["status"] == "FAIL"


@pytest.mark.unit
def test_pip_audit_cache_hit_miss_and_corrupt(temp_project_copy, monkeypatch):
    service = AIToolsService(project_root=str(temp_project_copy))
    domain = "static_checks"
    monkeypatch.setattr(
        service, "_compute_requirements_lock_signature", lambda: "sig-abc", raising=True
    )

    assert service._try_pip_audit_cache(domain) is None

    from development_tools.shared.audit_storage_scope import jsons_dir_for_scope

    cache_file = (
        jsons_dir_for_scope(temp_project_copy, domain)
        / ".analyze_pip_audit_requirements_cache.json"
    )
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text('{"requirements_signature": "other"}', encoding="utf-8")
    assert service._try_pip_audit_cache(domain) is None

    cache_file.write_text("{not-json", encoding="utf-8")
    assert service._try_pip_audit_cache(domain) is None

    cache_file.write_text(
        '{"requirements_signature": "sig-abc"}', encoding="utf-8"
    )
    monkeypatch.setitem(
        service._try_pip_audit_cache.__func__.__globals__,
        "load_tool_result",
        lambda *_a, **_k: {"summary": {"total_issues": 0}},
    )
    loaded = service._try_pip_audit_cache(domain)
    assert loaded == {"summary": {"total_issues": 0}}

    service._save_pip_audit_cache(domain, {"summary": {}})
    saved_sig = json.loads(cache_file.read_text(encoding="utf-8"))
    assert saved_sig["requirements_signature"] == "sig-abc"


@pytest.mark.unit
def test_run_analyze_unused_functions_non_json_and_save_failure(
    temp_project_copy, monkeypatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {
            "success": False,
            "output": "not-json",
            "error": "bad",
            "returncode": 1,
        },
        raising=True,
    )
    result = service.run_analyze_unused_functions()
    assert "data" not in result or result.get("data") is None
    assert result.get("success") is False

    saved_calls = {"n": 0}

    def _raise_save(*_a, **_k):
        saved_calls["n"] += 1
        raise OSError("disk full")

    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {
            "success": True,
            "output": '{"summary":{"total_issues":1},"details":{}}',
            "error": "",
            "returncode": 0,
        },
        raising=True,
    )
    monkeypatch.setitem(
        service.run_analyze_unused_functions.__func__.__globals__,
        "save_tool_result",
        _raise_save,
    )
    result = service.run_analyze_unused_functions()
    assert saved_calls["n"] == 1
    assert result["success"] is True
    assert result["issues_found"] is True


@pytest.mark.unit
def test_run_analyze_facade_shims_include_low_signal_and_bad_json(
    temp_project_copy, monkeypatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    captured: dict[str, tuple] = {}
    saved: list = []

    def _fake_run(_name, *args, **_k):
        captured["args"] = args
        return {
            "success": True,
            "output": '{"summary":{"total_issues":0},"details":{}}',
            "error": "",
            "returncode": 0,
        }

    monkeypatch.setattr(service, "run_script", _fake_run, raising=True)
    monkeypatch.setitem(
        service.run_analyze_facade_shims.__func__.__globals__,
        "save_tool_result",
        lambda *a, **k: saved.append(a),
    )
    result = service.run_analyze_facade_shims(include_low_signal=True)
    assert "--include-low-signal" in captured["args"]
    assert result["success"] is True
    assert saved

    saved.clear()
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_a, **_k: {
            "success": False,
            "output": "plain text failure",
            "error": "x",
            "returncode": 1,
        },
        raising=True,
    )
    result = service.run_analyze_facade_shims()
    assert not saved
    assert "data" not in result or result.get("data") is None


@pytest.mark.unit
def test_run_analyze_function_patterns_success_and_exception(
    temp_project_copy, monkeypatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    saved: list[dict] = []

    import development_tools.functions.analyze_function_patterns as real_patterns
    import development_tools.functions.analyze_functions as real_funcs

    monkeypatch.setattr(
        real_patterns, "analyze_function_patterns", lambda _funcs: {"handlers": 1}
    )
    monkeypatch.setattr(
        real_funcs, "scan_all_python_files", lambda: [{"name": "foo"}]
    )
    monkeypatch.setitem(
        service.run_analyze_function_patterns.__func__.__globals__,
        "save_tool_result",
        lambda _t, _d, data, **_k: saved.append(data),
    )

    result = service.run_analyze_function_patterns()
    assert result["success"] is True
    assert result["data"]["details"]["handlers"] == 1
    assert saved

    monkeypatch.setattr(
        real_funcs,
        "scan_all_python_files",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    failed = service.run_analyze_function_patterns()
    assert failed["success"] is False
    assert "boom" in failed["error"]


@pytest.mark.unit
def test_dependency_patterns_reuses_module_imports_cache(
    temp_project_copy, monkeypatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.results_cache = {
        "analyze_module_imports": {
            "summary": {"total_issues": 0},
            "details": {"modules": {"a": ["b"]}},
        }
    }
    called = {"imports": 0}
    saved: list[dict] = []

    class _FakeImportAnalyzer:
        def __init__(self, *args, **kwargs):
            called["imports"] += 1

        def scan_all_python_files(self):
            return {"modules": {"should_not": ["run"]}}

    class _FakePatternAnalyzer:
        def analyze_dependency_patterns(self, imports):
            assert imports == {"modules": {"a": ["b"]}}
            return {"circular": [], "high_coupling": []}

    import development_tools.imports.analyze_module_imports as imports_mod
    import development_tools.imports.analyze_dependency_patterns as dep_mod

    monkeypatch.setattr(imports_mod, "ModuleImportAnalyzer", _FakeImportAnalyzer)
    monkeypatch.setattr(dep_mod, "DependencyPatternAnalyzer", _FakePatternAnalyzer)
    monkeypatch.setitem(
        service.run_analyze_dependency_patterns.__func__.__globals__,
        "save_tool_result",
        lambda _t, _d, data, **_k: saved.append(data),
    )

    result = service.run_analyze_dependency_patterns()
    assert called["imports"] == 0
    assert result["success"] is True
    assert saved[0]["details"]["circular"] == []
