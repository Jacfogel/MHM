"""Branch-focused tests for shared/service/tool_wrappers.py."""

import pytest

from tests.development_tools.conftest import load_development_tools_module


service_module = load_development_tools_module("shared.service")
tool_wrappers_module = load_development_tools_module("shared.service.tool_wrappers")
output_storage_module = load_development_tools_module("shared.output_storage")
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_run_script_rejects_unregistered_tool(temp_project_copy):
    """run_script should fail fast for unknown script keys."""
    service = AIToolsService(project_root=str(temp_project_copy))

    result = service.run_script("not_registered_tool")

    assert result["success"] is False
    assert "not registered" in result["error"]


@pytest.mark.unit
def test_run_script_reports_missing_registered_file(temp_project_copy, monkeypatch):
    """run_script should report missing paths for registered tools."""
    service = AIToolsService(project_root=str(temp_project_copy))
    script_registry = service.run_script.__func__.__globals__["SCRIPT_REGISTRY"]
    monkeypatch.setitem(
        script_registry, "missing_script_case", "docs/definitely_missing.py"
    )

    result = service.run_script("missing_script_case")

    assert result["success"] is False
    assert "not found" in result["error"]


@pytest.mark.unit
def test_run_script_handles_timeout(temp_project_copy, monkeypatch):
    """run_script should return timeout payload when subprocess exceeds timeout."""
    service = AIToolsService(project_root=str(temp_project_copy))

    def _raise_timeout(*_args, **_kwargs):
        raise tool_wrappers_module.subprocess.TimeoutExpired(cmd="fake", timeout=120)

    monkeypatch.setattr(tool_wrappers_module.subprocess, "run", _raise_timeout, raising=True)

    result = service.run_script("quick_status", timeout=120)

    assert result["success"] is False
    assert "timed out after 2 minutes" in result["error"]
    assert result["returncode"] is None


@pytest.mark.unit
def test_run_script_handles_keyboard_interrupt(temp_project_copy, monkeypatch):
    """run_script should return structured interrupt payload for KeyboardInterrupt."""
    service = AIToolsService(project_root=str(temp_project_copy))

    def _raise_interrupt(*_args, **_kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        tool_wrappers_module.subprocess, "run", _raise_interrupt, raising=True
    )

    result = service.run_script("quick_status", timeout=120)

    assert result["success"] is False
    assert result["returncode"] == 130
    assert result.get("interrupted") is True
    assert "KeyboardInterrupt" in result["error"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "script_name",
    ("run_test_coverage", "analyze_pyright", "analyze_ruff"),
)
def test_run_script_uses_windows_process_group_for_isolated_tools(
    temp_project_copy, monkeypatch, script_name
):
    """run_script should isolate heavy T3 tools' subprocess groups on Windows."""
    service = AIToolsService(project_root=str(temp_project_copy))
    captured = {}

    class _FakeResult:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return _FakeResult()

    monkeypatch.setattr(tool_wrappers_module.os, "name", "nt", raising=True)
    monkeypatch.setattr(
        tool_wrappers_module.subprocess, "CREATE_NEW_PROCESS_GROUP", 512, raising=False
    )
    monkeypatch.setattr(tool_wrappers_module.subprocess, "run", _fake_run, raising=True)

    result = service.run_script(script_name)

    assert result["success"] is True
    assert captured["kwargs"].get("creationflags") == 512


@pytest.mark.unit
def test_run_script_no_windows_process_group_for_quick_tools(
    temp_project_copy, monkeypatch
):
    """Light scripts should not set CREATE_NEW_PROCESS_GROUP on Windows."""
    service = AIToolsService(project_root=str(temp_project_copy))
    captured = {}

    class _FakeResult:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return _FakeResult()

    monkeypatch.setattr(tool_wrappers_module.os, "name", "nt", raising=True)
    monkeypatch.setattr(
        tool_wrappers_module.subprocess, "CREATE_NEW_PROCESS_GROUP", 512, raising=False
    )
    monkeypatch.setattr(tool_wrappers_module.subprocess, "run", _fake_run, raising=True)

    result = service.run_script("quick_status")

    assert result["success"] is True
    assert captured["kwargs"].get("creationflags", 0) == 0


@pytest.mark.unit
def test_run_analyze_documentation_merges_cached_overlap_data(temp_project_copy, monkeypatch):
    """Wrapper should preserve cached overlap fields when fresh output omits them."""
    service = AIToolsService(project_root=str(temp_project_copy))

    monkeypatch.setattr(
        output_storage_module,
        "load_tool_result",
        lambda *_args, **_kwargs: {
            "data": {
                "summary": {"total_issues": 1, "files_affected": 1},
                "details": {
                    "section_overlaps": {"a.md": ["b.md"]},
                    "consolidation_recommendations": ["merge docs"],
                },
            }
        },
        raising=True,
    )
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": True,
            "output": '{"summary": {"total_issues": 0, "files_affected": 0}, "details": {}}',
            "error": "",
            "returncode": 0,
        },
        raising=True,
    )
    monkeypatch.setattr(
        tool_wrappers_module,
        "save_tool_result",
        lambda *_args, **_kwargs: None,
        raising=True,
    )

    result = service.run_analyze_documentation(include_overlap=False)

    assert result["success"] is True
    assert result["data"]["details"]["overlap_data_source"] == "cached"
    assert "section_overlaps" in result["data"]["details"]
    assert "consolidation_recommendations" in result["data"]["details"]


@pytest.mark.unit
def test_run_analyze_documentation_uses_keyword_fallback_for_issues(temp_project_copy, monkeypatch):
    """Wrapper should classify issues when script output is non-JSON but diagnostic."""
    service = AIToolsService(project_root=str(temp_project_copy))
    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": False,
            "output": "verbatim duplicate section found",
            "error": "non-zero exit",
            "returncode": 1,
        },
        raising=True,
    )

    result = service.run_analyze_documentation()

    assert result["issues_found"] is True
    assert result["success"] is True
    assert result["error"] == ""


@pytest.mark.unit
def test_run_analyze_error_handling_loads_cached_data_on_successful_run_with_non_json_output(
    temp_project_copy, monkeypatch
):
    """Wrapper should use standardized cached output when script succeeds but emits non-JSON."""
    service = AIToolsService(project_root=str(temp_project_copy))

    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": True,
            "output": "some prefix text before json parse fails",
            "error": "",
            "returncode": 0,
        },
        raising=True,
    )
    monkeypatch.setattr(
        output_storage_module,
        "load_tool_result",
        lambda *_args, **_kwargs: {
            "analyze_error_handling": 70,
            "functions_missing_error_handling": 2,
        },
        raising=True,
    )
    monkeypatch.setattr(
        tool_wrappers_module,
        "save_tool_result",
        lambda *_args, **_kwargs: None,
        raising=True,
    )

    result = service.run_analyze_error_handling()

    assert result["success"] is True
    assert result["issues_found"] is True
    assert result["data"]["functions_missing_error_handling"] == 2


@pytest.mark.unit
def test_run_analyze_error_handling_skips_cache_when_script_failed(temp_project_copy, monkeypatch):
    """Wrapper must not pull cached data when script itself fails."""
    service = AIToolsService(project_root=str(temp_project_copy))
    cache_load_calls = {"count": 0}

    monkeypatch.setattr(
        service,
        "run_script",
        lambda *_args, **_kwargs: {
            "success": False,
            "output": "non json plain text",
            "error": "script failed",
            "returncode": 1,
        },
        raising=True,
    )

    def _track_cache_calls(*_args, **_kwargs):
        cache_load_calls["count"] += 1
        return {"analyze_error_handling": 0, "functions_missing_error_handling": 0}

    monkeypatch.setattr(
        output_storage_module,
        "load_tool_result",
        _track_cache_calls,
        raising=True,
    )

    result = service.run_analyze_error_handling()

    assert cache_load_calls["count"] == 0
    assert result["success"] is False


@pytest.mark.unit
def test_run_generate_test_coverage_report_fails_when_coverage_json_missing(temp_project_copy):
    """Coverage report generation should require pre-existing coverage.json data."""
    service = AIToolsService(project_root=str(temp_project_copy))

    result = service.run_generate_test_coverage_report()

    assert result["success"] is False
    assert "coverage.json not found" in result["error"]


@pytest.mark.unit
def test_run_generate_test_coverage_report_returns_script_result_when_report_missing(
    temp_project_copy, monkeypatch
):
    """If generator succeeds but report file is absent, wrapper should return script payload."""
    service = AIToolsService(project_root=str(temp_project_copy))
    coverage_path = (
        temp_project_copy / "development_tools" / "tests" / "jsons" / "coverage.json"
    )
    coverage_path.parent.mkdir(parents=True, exist_ok=True)
    coverage_path.write_text("{}", encoding="utf-8")

    script_result = {"success": True, "output": "generated", "error": "", "returncode": 0}
    monkeypatch.setattr(service, "run_script", lambda *_a, **_k: script_result, raising=True)

    result = service.run_generate_test_coverage_report()

    assert result == script_result
