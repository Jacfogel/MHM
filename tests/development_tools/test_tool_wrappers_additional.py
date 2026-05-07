"""Additional branch coverage tests for shared/service/tool_wrappers.py."""

import subprocess
from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module


service_module = load_development_tools_module("shared.service")
tool_wrappers_module = load_development_tools_module("shared.service.tool_wrappers")
AIToolsService = service_module.AIToolsService


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
