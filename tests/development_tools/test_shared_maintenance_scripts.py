"""Tests for shared maintenance scripts in development_tools/shared/."""

import json

import pytest

from tests.development_tools.conftest import load_development_tools_module


measure_tool_timings = load_development_tools_module("shared.measure_tool_timings")
verify_tool_storage = load_development_tools_module("shared.verify_tool_storage")


@pytest.mark.unit
def test_measure_tool_execution_with_dict_result():
    """Dict-style tool result should map success/error fields."""

    def _tool():
        return {"success": True, "error": ""}

    success, elapsed, error = measure_tool_timings.measure_tool_execution(
        service=None,
        tool_name="demo_tool",
        tool_func=_tool,
    )
    assert success is True
    assert elapsed >= 0.0
    assert error == ""


@pytest.mark.unit
def test_measure_tool_execution_handles_exceptions():
    """Exceptions should return a failed result with error text."""

    def _tool():
        raise RuntimeError("boom")

    success, elapsed, error = measure_tool_timings.measure_tool_execution(
        service=None,
        tool_name="demo_tool",
        tool_func=_tool,
    )
    assert success is False
    assert elapsed >= 0.0
    assert "boom" in error


@pytest.mark.unit
def test_generate_timing_report_writes_markdown_and_json(tmp_path):
    """Report generation should produce both markdown and JSON outputs."""
    output_file = tmp_path / "TIMING_ANALYSIS.md"
    results = {
        "tier1": {
            "quick_status": {"success": True, "time": 5.0, "error": ""},
        },
        "tier2": {
            "analyze_documentation": {"success": True, "time": 25.0, "error": ""},
        },
        "tier3": {
            "run_test_coverage": {"success": False, "time": 240.0, "error": "failed"},
        },
        "summary": {"total_tools": 3, "successful": 2, "failed": 1, "total_time": 270.0},
    }

    measure_tool_timings.generate_timing_report(results, output_file)

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "Tool Execution Timing Analysis" in content
    assert "quick_status" in content
    assert "analyze_documentation" in content

    json_file = output_file.with_suffix(".json")
    assert json_file.exists()
    payload = json.loads(json_file.read_text(encoding="utf-8"))
    assert payload["summary"]["total_tools"] == 3


@pytest.mark.unit
def test_run_timing_analysis_with_mocked_service(monkeypatch, tmp_path):
    """Timing analysis should aggregate tool results and call report generation."""
    output_file = tmp_path / "report.md"
    report_calls = []

    class _FakeService:
        def run_analyze_functions(self):
            return {"success": True}

        def run_analyze_documentation_sync(self):
            return {"success": True}

        def run_analyze_system_signals(self):
            return {"success": True}

        def run_analyze_config(self):
            return {"success": True}

        def run_script(self, *args, **kwargs):
            return {"success": True}

        def run_analyze_documentation(self, include_overlap=False):
            return {"success": include_overlap is False}

        def run_analyze_error_handling(self):
            return {"success": True}

        def run_decision_support(self):
            return {"success": True}

        def run_validate(self):
            return {"success": True}

        def run_analyze_function_registry(self):
            return {"success": True}

        def run_analyze_module_dependencies(self):
            return {"success": True}

        def run_analyze_module_refactor_candidates(self):
            return {"success": True}

        def run_analyze_module_imports(self):
            return {"success": True}

        def run_analyze_dependency_patterns(self):
            return {"success": True}

        def run_analyze_function_patterns(self):
            return {"success": True}

        def run_analyze_dev_tools_import_boundaries(self):
            return {"success": True}

        def run_analyze_package_exports(self):
            return {"success": True}

        def _run_analyze_duplicate_functions_for_audit(self):
            return {"success": True}

        def run_coverage_regeneration(self):
            return {"success": True}

        def run_dev_tools_coverage(self):
            return {"success": True}

        def run_test_markers(self, _mode):
            return {"success": True}

        def run_generate_test_coverage_report(self):
            return {"success": True}

        def run_analyze_legacy_references(self):
            return {"success": True}

        def run_generate_legacy_reference_report(self):
            return {"success": True}

        def run_backup_health_check(self, run_drill=False):
            return {"success": True}

        def run_analyze_ruff(self):
            return {"success": True}

        def run_analyze_pyright(self):
            return {"success": True}

        def run_analyze_bandit(self):
            return {"success": True}

        def run_analyze_pip_audit(self):
            return {"success": True}

        def run_verify_process_cleanup(self):
            return {"success": True}

        def run_analyze_unused_imports(self):
            return {"success": True}

        def run_generate_unused_imports_report(self):
            return {"success": True}

    def _fake_report(results, report_path):
        report_calls.append((results, report_path))

    monkeypatch.setattr(measure_tool_timings, "AIToolsService", _FakeService)
    monkeypatch.setattr(measure_tool_timings, "generate_timing_report", _fake_report)

    results = measure_tool_timings.run_timing_analysis(output_file)
    assert results["summary"]["failed"] == 0
    assert results["summary"]["successful"] == results["summary"]["total_tools"]
    assert report_calls
    assert report_calls[0][1] == output_file


@pytest.mark.unit
def test_check_tool_uses_save_tool_result_true_and_false():
    """Source inspection should detect save_tool_result usage."""

    class _HasStorage:
        def save_tool_result(self, _name: str, _data: dict) -> None:
            pass

        def run_demo(self):
            self.save_tool_result("demo", {})

    class _NoStorage:
        def run_demo(self):
            return {"ok": True}

    ok, msg = verify_tool_storage.check_tool_uses_save_tool_result("demo", _HasStorage)
    assert ok is True
    assert "save_tool_result" in msg

    ok, msg = verify_tool_storage.check_tool_uses_save_tool_result("demo", _NoStorage)
    assert ok is False
    assert "Does not use save_tool_result" in msg


@pytest.mark.unit
def test_verify_all_tools_success(monkeypatch, capsys):
    """Verification should pass when wrapper methods use standardized storage."""
    monkeypatch.setattr(
        verify_tool_storage,
        "EXPECTED_TOOLS",
        {"analyze_functions": "functions"},
    )

    class _GoodWrappers:
        def save_tool_result(self, _name: str, _data: dict) -> None:
            pass

        def run_analyze_functions(self):
            self.save_tool_result("analyze_functions", {})

    class _Empty:
        pass

    monkeypatch.setattr(verify_tool_storage, "ToolWrappersMixin", _GoodWrappers)
    monkeypatch.setattr(verify_tool_storage, "CommandsMixin", _Empty)
    monkeypatch.setattr(verify_tool_storage, "AuditOrchestrationMixin", _Empty)

    result = verify_tool_storage.verify_all_tools()
    out = capsys.readouterr().out
    assert result is True
    assert "1/1 tools verified" in out


@pytest.mark.unit
def test_verify_all_tools_failure(monkeypatch, capsys):
    """Verification should fail when wrapper omits standardized storage call."""
    monkeypatch.setattr(
        verify_tool_storage,
        "EXPECTED_TOOLS",
        {"analyze_functions": "functions"},
    )

    class _BadWrappers:
        def run_analyze_functions(self):
            return {"ok": True}

    class _Empty:
        pass

    monkeypatch.setattr(verify_tool_storage, "ToolWrappersMixin", _BadWrappers)
    monkeypatch.setattr(verify_tool_storage, "CommandsMixin", _Empty)
    monkeypatch.setattr(verify_tool_storage, "AuditOrchestrationMixin", _Empty)

    result = verify_tool_storage.verify_all_tools()
    out = capsys.readouterr().out
    assert result is False
    assert "WARNING: 1 tools need attention" in out
