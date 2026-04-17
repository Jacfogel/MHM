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


@pytest.mark.unit
def test_run_analyze_bandit_parses_json_and_marks_issues(temp_project_copy, monkeypatch):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": True,
            "output": '{"summary":{"total_issues":2,"files_affected":1,"status":"FAIL"},"details":{"tool":"bandit"}}',
            "error": "",
            "returncode": 0,
        },
        raising=True,
    )
    monkeypatch.setattr(
        tool_wrappers_module, "save_tool_result", lambda *_a, **_k: None, raising=True
    )

    result = service.run_analyze_bandit()

    assert result["success"] is True
    assert result["issues_found"] is True
    assert result["data"]["summary"]["total_issues"] == 2


@pytest.mark.unit
def test_run_analyze_pip_audit_parses_json_and_marks_issues(temp_project_copy, monkeypatch):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": True,
            "output": '{"summary":{"total_issues":4,"files_affected":2,"status":"WARN"},"details":{"tool":"pip_audit"}}',
            "error": "",
            "returncode": 0,
        },
        raising=True,
    )
    monkeypatch.setattr(
        tool_wrappers_module, "save_tool_result", lambda *_a, **_k: None, raising=True
    )

    result = service.run_analyze_pip_audit()

    assert result["success"] is True
    assert result["issues_found"] is True
    assert result["data"]["summary"]["total_issues"] == 4


@pytest.mark.unit
def test_run_analyze_pip_audit_uses_cache_and_sets_execution_state(
    temp_project_copy, monkeypatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "_try_pip_audit_cache",
        lambda _domain: {
            "summary": {"total_issues": 0, "files_affected": 0},
            "details": {},
        },
        raising=True,
    )
    run_calls = {"count": 0}

    def _unexpected_run(*_args, **_kwargs):
        run_calls["count"] += 1
        return {}

    monkeypatch.setattr(service, "run_script", _unexpected_run, raising=True)

    result = service.run_analyze_pip_audit()

    assert run_calls["count"] == 0
    assert result["success"] is True
    assert result["issues_found"] is False
    details = result["data"]["details"]
    assert details["pip_audit_execution_state"] == "requirements_lock_cache_hit"
    assert details["pip_audit_subprocess_seconds"] is None


@pytest.mark.unit
def test_run_analyze_pyright_returns_failure_when_output_is_not_json(
    temp_project_copy, monkeypatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(service, "_try_static_check_cache", lambda *_a, **_k: None, raising=True)
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": False,
            "output": "pyright failed to serialize",
            "error": "stderr payload",
            "returncode": 1,
        },
        raising=True,
    )

    result = service.run_analyze_pyright()

    assert result["success"] is False
    assert "stderr payload" in result["error"]
