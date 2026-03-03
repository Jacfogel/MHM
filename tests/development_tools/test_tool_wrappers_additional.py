"""Additional branch coverage tests for shared/service/tool_wrappers.py."""

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
    assert service.results_cache["analyze_module_dependencies"]["missing_dependencies"] == 2


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
