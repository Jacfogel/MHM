"""Tests for development-tools pytest isolation from the host suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from development_tools.tests.pytest_isolation import (
    DEFAULT_TOOLS_PYTEST_INI,
    host_ignore_args,
    is_tools_test_path,
    partition_test_paths,
    path_contains_tools_root,
    tools_suite_pytest_args,
)
from tests.development_tools.conftest import load_development_tools_module

runner = load_development_tools_module("run_test_suite")
_CONFTEST = Path(__file__).resolve().parent / "conftest.py"
_TOOLS_INI = Path(__file__).resolve().parents[2] / "development_tools" / "pytest.ini"


@pytest.mark.unit
def test_get_test_run_config_defaults_tools_isolation():
    from development_tools.config import get_test_run_config

    cfg = get_test_run_config("quick")
    assert cfg["devtools_test_paths"] == ["tests/development_tools"]
    assert cfg["devtools_pytest_config"] == "development_tools/pytest.ini"
    assert cfg["devtools_confcutdir"] == "tests/development_tools"
    assert cfg["timeout_seconds"] == 3600

    full_cfg = get_test_run_config("full")
    assert full_cfg["timeout_seconds"] == 3600


@pytest.mark.unit
def test_tools_suite_pytest_args_use_owned_ini_and_confcutdir():
    args = tools_suite_pytest_args()
    assert args[0:2] == ["-c", DEFAULT_TOOLS_PYTEST_INI]
    assert "--rootdir=." in args
    assert "--confcutdir=tests/development_tools" in args


@pytest.mark.unit
def test_partition_full_tests_path_schedules_tools_second_invocation():
    host, tools = partition_test_paths(
        ["tests"],
        ["tests/development_tools"],
    )
    assert host == ["tests"]
    assert tools == ["tests/development_tools"]
    assert host_ignore_args(["tests/development_tools"]) == [
        "--ignore=tests/development_tools"
    ]


@pytest.mark.unit
def test_partition_selective_files_keeps_host_and_tools_apart():
    host, tools = partition_test_paths(
        [
            "tests/unit/test_foo.py",
            "tests/development_tools/test_config.py",
        ],
        ["tests/development_tools"],
    )
    assert host == ["tests/unit/test_foo.py"]
    assert tools == ["tests/development_tools/test_config.py"]
    assert is_tools_test_path("tests/development_tools/test_config.py")
    assert not is_tools_test_path("tests/unit/test_foo.py")
    assert path_contains_tools_root("tests", ["tests/development_tools"])
    assert not path_contains_tools_root("tests/unit", ["tests/development_tools"])


@pytest.mark.unit
def test_tools_conftest_does_not_import_host_conftest():
    text = _CONFTEST.read_text(encoding="utf-8")
    assert "from tests.conftest" not in text
    assert "initialize_loader_import_order" not in text
    assert "mock_config" not in text
    ini = _TOOLS_INI.read_text(encoding="utf-8")
    assert "confcutdir = tests/development_tools" in ini


@pytest.mark.unit
def test_build_phase_command_inserts_isolation_args(tmp_path):
    command = runner.build_phase_command(
        phase="parallel",
        cfg={
            "pytest_command": ["python", "-m", "pytest"],
            "pytest_base_args": ["--tb=short"],
            "test_paths": ["tests/development_tools"],
            "workers": "auto",
            "exclude_markers": ["e2e", "slow"],
            "no_parallel_marker": "no_parallel",
        },
        junit_xml=tmp_path / "parallel.xml",
        extra_args=tools_suite_pytest_args(),
        marker_phase="parallel",
        force_serial=True,
        test_paths=["tests/development_tools"],
    )
    assert "-c" in command
    assert DEFAULT_TOOLS_PYTEST_INI in command
    assert "--confcutdir=tests/development_tools" in command
    pytest_idx = command.index("pytest")
    assert command[pytest_idx + 1] == "-c"


@pytest.mark.unit
def test_run_phase_splits_host_and_tools_invocations(monkeypatch, tmp_path):
    calls: list[
        tuple[str, tuple[str, ...], tuple[str, ...], int | None]
    ] = []

    def fake_invoke(
        name,
        cfg,
        junit_dir,
        *,
        force_serial=False,
        test_paths=None,
        extra_args=None,
        marker_phase=None,
        timeout_seconds=None,
    ):
        calls.append((name, tuple(test_paths or []), tuple(extra_args or []), timeout_seconds))
        return runner.PhaseResult(
            name=name,
            command=["pytest", name],
            return_code=0,
            duration_seconds=0.1,
            counts={"total": 1, "passed": 1, "failed": 0, "errors": 0, "skipped": 0},
            failed_node_ids=[],
            output_tail="ok",
            junit_xml=str(junit_dir / f"{name}.xml"),
        )

    monkeypatch.setattr(runner, "_invoke_pytest", fake_invoke)
    monkeypatch.setattr(
        runner,
        "_tools_roots_from_cfg",
        lambda cfg: ["tests/development_tools"],
    )

    result = runner._run_phase(
        "parallel",
        {
            "test_paths": ["tests"],
            "devtools_test_paths": ["tests/development_tools"],
            "timeout_seconds": 120,
        },
        tmp_path,
        test_paths=["tests"],
    )

    assert result.name == "parallel"
    assert result.counts["passed"] == 2
    assert [call[0] for call in calls] == ["parallel", "parallel_devtools"]
    assert "--ignore=tests/development_tools" in calls[0][2]
    assert "-c" in calls[1][2]
    assert calls[1][1] == ("tests/development_tools",)
    assert calls[0][3] is not None
    assert 100 <= int(calls[0][3]) <= 120
    assert calls[1][3] is not None
    assert int(calls[1][3]) <= int(calls[0][3])


@pytest.mark.unit
def test_run_phase_skips_tools_when_timeout_budget_exhausted(monkeypatch, tmp_path):
    calls: list[str] = []

    def fake_invoke(
        name,
        cfg,
        junit_dir,
        *,
        force_serial=False,
        test_paths=None,
        extra_args=None,
        marker_phase=None,
        timeout_seconds=None,
    ):
        calls.append(name)
        return runner.PhaseResult(
            name=name,
            command=["pytest", name],
            return_code=0,
            duration_seconds=0.1,
            counts={"total": 1, "passed": 1, "failed": 0, "errors": 0, "skipped": 0},
            failed_node_ids=[],
            output_tail="ok",
            junit_xml=str(junit_dir / f"{name}.xml"),
            interrupted=True,
        )

    monkeypatch.setattr(runner, "_invoke_pytest", fake_invoke)
    monkeypatch.setattr(
        runner,
        "_tools_roots_from_cfg",
        lambda cfg: ["tests/development_tools"],
    )

    result = runner._run_phase(
        "parallel",
        {
            "test_paths": ["tests"],
            "devtools_test_paths": ["tests/development_tools"],
            "timeout_seconds": 60,
        },
        tmp_path,
        test_paths=["tests"],
    )

    assert calls == ["parallel"]
    assert result.interrupted is True
    assert result.counts["passed"] == 1
