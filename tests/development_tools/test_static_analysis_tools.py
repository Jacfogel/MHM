"""Tests for static analysis wrapper scripts (ruff + pyright)."""

from pathlib import Path
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


@pytest.mark.unit
def test_analyze_ruff_passes_owned_config_path(monkeypatch, temp_project_copy):
    calls = []

    monkeypatch.setattr(
        ruff_module.config,
        "get_static_analysis_config",
        lambda: {
            "ruff_command": ["python", "-m", "ruff"],
            "ruff_args": ["check", ".", "--output-format", "json"],
            "ruff_config_path": "development_tools/config/ruff.toml",
            "ruff_sync_root_compat": False,
            "timeout_seconds": 10,
        },
    )
    monkeypatch.setattr(
        ruff_module,
        "sync_ruff_toml",
        lambda project_root, config_path, sync_root_compat: Path(project_root)
        / Path(config_path),
    )

    def _fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))

        class _Result:
            returncode = 0
            stdout = "[]"
            stderr = ""

        return _Result()

    monkeypatch.setattr(ruff_module.subprocess, "run", _fake_run)

    result = ruff_module.run_ruff(temp_project_copy)

    assert result["summary"]["status"] == "PASS"
    cmd, kwargs = calls[0]
    assert "--config" in cmd
    config_index = cmd.index("--config") + 1
    assert cmd[config_index].replace("\\", "/").endswith(
        "development_tools/config/ruff.toml"
    )
    assert kwargs["cwd"] == str(temp_project_copy)


@pytest.mark.unit
def test_analyze_pyright_passes_owned_project_path(monkeypatch, temp_project_copy):
    calls = []

    monkeypatch.setattr(
        pyright_module.config,
        "get_static_analysis_config",
        lambda: {
            "pyright_command": ["python", "-m", "pyright"],
            "pyright_args": ["--outputjson"],
            "pyright_project_path": "pyproject.toml",
            "timeout_seconds": 10,
        },
    )

    def _fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))

        class _Result:
            returncode = 0
            stdout = (
                '{"summary":{"filesAnalyzed":1,"errorCount":0,'
                '"warningCount":0,"informationCount":0},"generalDiagnostics":[]}'
            )
            stderr = ""

        return _Result()

    monkeypatch.setattr(pyright_module.subprocess, "run", _fake_run)

    result = pyright_module.run_pyright(temp_project_copy)

    assert result["summary"]["status"] == "PASS"
    cmd, kwargs = calls[0]
    assert "--project" in cmd
    project_index = cmd.index("--project") + 1
    assert cmd[project_index].replace("\\", "/").endswith("pyproject.toml")
    assert kwargs["cwd"] == str(temp_project_copy)


@pytest.mark.unit
def test_analyze_pyright_respects_existing_project_arg(monkeypatch, temp_project_copy):
    calls = []

    monkeypatch.setattr(
        pyright_module.config,
        "get_static_analysis_config",
        lambda: {
            "pyright_command": ["python", "-m", "pyright"],
            "pyright_args": ["--outputjson", "--project", "custom_pyright.json"],
            "pyright_project_path": "pyproject.toml",
            "timeout_seconds": 10,
        },
    )

    def _fake_run(cmd, **_kwargs):
        calls.append(cmd)

        class _Result:
            returncode = 0
            stdout = (
                '{"summary":{"filesAnalyzed":1,"errorCount":0,'
                '"warningCount":0,"informationCount":0},"generalDiagnostics":[]}'
            )
            stderr = ""

        return _Result()

    monkeypatch.setattr(pyright_module.subprocess, "run", _fake_run)
    pyright_module.run_pyright(temp_project_copy)

    cmd = calls[0]
    assert cmd.count("--project") == 1
    assert "custom_pyright.json" in cmd


@pytest.mark.unit
def test_analyze_pyright_keyboard_interrupt_returns_warn(monkeypatch, temp_project_copy):
    def _raise_interrupt(*_args, **_kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        pyright_module.config,
        "get_static_analysis_config",
        lambda: {
            "pyright_command": ["python", "-m", "pyright"],
            "pyright_args": ["--outputjson"],
            "pyright_project_path": "pyproject.toml",
            "timeout_seconds": 10,
        },
    )
    monkeypatch.setattr(pyright_module.subprocess, "run", _raise_interrupt)

    result = pyright_module.run_pyright(temp_project_copy)

    assert result["summary"]["status"] == "WARN"
    assert result["details"]["tool_available"] is False
    assert "interrupted" in str(result["details"].get("message", "")).lower()


@pytest.mark.unit
def test_analyze_ruff_keyboard_interrupt_returns_warn(monkeypatch, temp_project_copy):
    def _raise_interrupt(*_args, **_kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        ruff_module.config,
        "get_static_analysis_config",
        lambda: {
            "ruff_command": ["python", "-m", "ruff"],
            "ruff_args": ["check", ".", "--output-format", "json"],
            "ruff_config_path": "development_tools/config/ruff.toml",
            "ruff_sync_root_compat": False,
            "timeout_seconds": 10,
        },
    )
    monkeypatch.setattr(
        ruff_module,
        "sync_ruff_toml",
        lambda project_root, config_path, sync_root_compat: Path(project_root)
        / Path(config_path),
    )
    monkeypatch.setattr(ruff_module.subprocess, "run", _raise_interrupt)

    result = ruff_module.run_ruff(temp_project_copy)

    assert result["summary"]["status"] == "WARN"
    assert result["details"]["tool_available"] is False
    assert "interrupted" in str(result["details"].get("message", "")).lower()
