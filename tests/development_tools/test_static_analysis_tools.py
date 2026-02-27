"""Tests for static analysis wrapper scripts (ruff + pyright)."""

import pytest

from tests.development_tools.conftest import load_development_tools_module


ruff_module = load_development_tools_module("static_checks.analyze_ruff")
pyright_module = load_development_tools_module("static_checks.analyze_pyright")


@pytest.mark.unit
def test_analyze_ruff_build_result_from_payload_counts_files_and_rules():
    payload = [
        {"filename": "core/a.py", "code": "F401"},
        {"filename": "core/a.py", "code": "F401"},
        {"filename": "ui/b.py", "code": "E402"},
    ]

    result = ruff_module._build_result_from_payload(payload, returncode=1)

    assert result["summary"]["total_issues"] == 3
    assert result["summary"]["files_affected"] == 2
    assert result["summary"]["status"] == "FAIL"
    assert result["details"]["violations_by_rule"]["F401"] == 2


@pytest.mark.unit
def test_analyze_pyright_build_result_from_payload_counts_error_warning():
    payload = {
        "summary": {
            "filesAnalyzed": 42,
            "errorCount": 2,
            "warningCount": 1,
            "informationCount": 0,
        },
        "generalDiagnostics": [
            {"file": "core/a.py", "severity": "error"},
            {"file": "core/a.py", "severity": "warning"},
            {"file": "ui/b.py", "severity": "error"},
        ],
    }

    result = pyright_module._build_result_from_payload(payload, returncode=1)

    assert result["summary"]["total_issues"] == 3
    assert result["summary"]["files_affected"] == 2
    assert result["summary"]["status"] == "FAIL"
    assert result["details"]["errors"] == 2
    assert result["details"]["warnings"] == 1
    assert result["details"]["top_error_files"][0]["file"] == "core/a.py"
    assert result["details"]["top_error_files"][0]["count"] == 1
    assert result["details"]["top_warning_files"][0]["file"] == "core/a.py"
    assert result["details"]["top_warning_files"][0]["count"] == 1


@pytest.mark.unit
def test_analyze_ruff_unavailable_command_returns_warn(monkeypatch, temp_project_copy):
    def _raise_file_not_found(*_args, **_kwargs):
        raise FileNotFoundError("ruff not installed")

    monkeypatch.setattr(ruff_module.subprocess, "run", _raise_file_not_found)

    result = ruff_module.run_ruff(temp_project_copy)

    assert result["summary"]["status"] == "WARN"
    assert result["details"]["tool_available"] is False
