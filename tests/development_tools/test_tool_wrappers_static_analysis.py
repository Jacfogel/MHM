"""Tests for static analysis tool wrappers in shared/service/tool_wrappers.py."""

import pytest

from tests.development_tools.conftest import load_development_tools_module


service_module = load_development_tools_module("shared.service")
tool_wrappers_module = load_development_tools_module("shared.service.tool_wrappers")
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_run_analyze_ruff_parses_json_and_marks_issues(temp_project_copy, monkeypatch):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": False,
            "output": '{"summary":{"total_issues":5,"files_affected":2,"status":"FAIL"},"details":{"tool":"ruff"}}',
            "error": "ruff exited 1",
            "returncode": 1,
        },
        raising=True,
    )
    monkeypatch.setattr(
        tool_wrappers_module, "save_tool_result", lambda *_a, **_k: None, raising=True
    )

    result = service.run_analyze_ruff()

    assert result["success"] is True
    assert result["issues_found"] is True
    assert result["data"]["summary"]["total_issues"] == 5


@pytest.mark.unit
def test_run_analyze_pyright_parses_json_and_marks_issues(temp_project_copy, monkeypatch):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": False,
            "output": '{"summary":{"total_issues":3,"files_affected":2,"status":"FAIL"},"details":{"tool":"pyright","errors":2,"warnings":1}}',
            "error": "pyright exited 1",
            "returncode": 1,
        },
        raising=True,
    )
    monkeypatch.setattr(
        tool_wrappers_module, "save_tool_result", lambda *_a, **_k: None, raising=True
    )

    result = service.run_analyze_pyright()

    assert result["success"] is True
    assert result["issues_found"] is True
    assert result["data"]["details"]["errors"] == 2
