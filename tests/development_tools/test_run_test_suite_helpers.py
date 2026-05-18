"""Helper-focused tests for development_tools/tests/run_test_suite.py."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, cast

import pytest

from tests.development_tools.conftest import load_development_tools_module

runner = load_development_tools_module("run_test_suite")


def _marker_arg(command: list[str]) -> str:
    return command[len(command) - 1 - command[::-1].index("-m") + 1]


def _cfg(**overrides):
    cfg = {
        "pytest_command": ["python", "-m", "pytest"],
        "pytest_base_args": ["--tb=short"],
        "test_paths": ["tests"],
        "workers": "auto",
        "exclude_markers": ["e2e"],
        "no_parallel_marker": "no_parallel",
        "sigint_taps_to_stop": 3,
        "sigint_window_seconds": 2.0,
        "sigint_debounce_seconds": 0.1,
    }
    cfg.update(overrides)
    return cfg


@pytest.mark.unit
def test_parallel_command_uses_xdist_and_excludes_e2e_and_no_parallel(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "_has_xdist", lambda: True)

    command = runner.build_phase_command(
        phase="parallel",
        cfg=_cfg(workers="4"),
        junit_xml=tmp_path / "parallel.xml",
    )

    assert command[:3] == [sys.executable, "-m", "pytest"]
    assert _marker_arg(command) == "not no_parallel and not e2e"
    assert command[command.index("-n") + 1] == "4"
    assert command[-1] == "tests"


@pytest.mark.unit
def test_parallel_command_falls_back_to_serial_without_xdist(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "_has_xdist", lambda: False)

    command = runner.build_phase_command(
        phase="parallel",
        cfg=_cfg(workers="auto"),
        junit_xml=tmp_path / "parallel.xml",
    )

    assert "-n" not in command
    assert _marker_arg(command) == "not no_parallel and not e2e"


@pytest.mark.unit
def test_no_parallel_phase_is_serial_and_marker_scoped(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "_has_xdist", lambda: True)

    command = runner.build_phase_command(
        phase="no_parallel",
        cfg=_cfg(workers="4"),
        junit_xml=tmp_path / "no_parallel.xml",
    )

    assert "-n" not in command
    assert _marker_arg(command) == "no_parallel and not e2e"


@pytest.mark.unit
def test_phase_classification_and_aggregate_states(tmp_path: Path):
    passed = runner.PhaseResult(
        name="parallel",
        command=[],
        return_code=0,
        duration_seconds=0.1,
        counts={"total": 2, "passed": 2, "failed": 0, "errors": 0, "skipped": 0},
        failed_node_ids=[],
        output_tail="",
        junit_xml=str(tmp_path / "parallel.xml"),
    )
    failed = runner.PhaseResult(
        name="no_parallel",
        command=[],
        return_code=1,
        duration_seconds=0.1,
        counts={"total": 1, "passed": 0, "failed": 1, "errors": 0, "skipped": 0},
        failed_node_ids=["tests/test_a.py::test_bad"],
        output_tail="",
        junit_xml=str(tmp_path / "no_parallel.xml"),
    )
    crashed = runner.PhaseResult(
        name="parallel",
        command=[],
        return_code=2,
        duration_seconds=0.1,
        counts={"total": 1, "passed": 0, "failed": 0, "errors": 1, "skipped": 0},
        failed_node_ids=[],
        output_tail="",
        junit_xml=str(tmp_path / "crashed.xml"),
    )

    assert passed.classification == "passed"
    assert failed.classification == "failed"
    assert crashed.classification == "crashed"
    assert runner._aggregate([passed, failed])["state"] == "test_failures"
    assert runner._aggregate([crashed])["state"] == "crashed"


@pytest.mark.unit
def test_configured_python_placeholder_uses_current_interpreter(tmp_path):
    command = runner.build_phase_command(
        phase="parallel",
        cfg=_cfg(pytest_command=["{python}", "-m", "pytest"]),
        junit_xml=tmp_path / "parallel.xml",
        force_serial=True,
    )

    assert command[:3] == [sys.executable, "-m", "pytest"]


@pytest.mark.unit
def test_pytest_startup_failure_without_junit_is_crashed(tmp_path: Path):
    phase = runner.PhaseResult(
        name="parallel",
        command=[],
        return_code=1,
        duration_seconds=0.1,
        counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
        failed_node_ids=[],
        output_tail="No module named pytest",
        junit_xml=str(tmp_path / "parallel.xml"),
    )

    assert phase.classification == "crashed"


@pytest.mark.unit
def test_sigint_threshold_ignores_until_confirmed(monkeypatch):
    calls = []

    class Process:
        pid = 123

        def poll(self):
            return None

    times = iter([100.0, 100.5, 101.0])
    monkeypatch.setattr(runner.time, "time", lambda: next(times))
    monkeypatch.setattr(runner, "_terminate_process_tree", lambda process: calls.append(process.pid))
    runner_any = cast(Any, runner)
    runner_any._INTERRUPT_TAPS = 0
    runner_any._LAST_INTERRUPT_TIME = None
    runner_any._STOP_REQUESTED = False
    runner_any._ACTIVE_PROCESS = Process()
    runner_any._SIGINT_CFG = _cfg(sigint_taps_to_stop=3)

    runner._handle_sigint(2, None)
    runner._handle_sigint(2, None)
    assert calls == []
    assert runner._STOP_REQUESTED is False

    runner._handle_sigint(2, None)
    assert calls == [123]
    assert runner._STOP_REQUESTED is True

    runner_any._ACTIVE_PROCESS = None
