"""Unit tests for development_tools.tests.flaky_detector."""

from __future__ import annotations

import subprocess

import pytest

from tests.development_tools.conftest import load_development_tools_module


flaky_detector = load_development_tools_module("tests.flaky_detector")
pytestmark = pytest.mark.unit


@pytest.mark.unit
def test_extract_failed_tests_parses_pytest_output():
    stdout = "\n".join(
        [
            "FAILED tests/unit/test_example.py::test_first - AssertionError",
            "tests/unit/test_other.py::test_second FAILED",
        ]
    )
    stderr = "ERROR tests/unit/test_err.py::test_boom - RuntimeError"

    parsed = flaky_detector.extract_failed_tests(stdout, stderr)

    assert "tests/unit/test_example.py::test_first" in parsed
    assert "tests/unit/test_other.py::test_second" in parsed
    assert "tests/unit/test_err.py::test_boom" in parsed


@pytest.mark.unit
def test_extract_failed_tests_empty_strings():
    assert flaky_detector.extract_failed_tests("", "") == set()


@pytest.mark.unit
def test_analyze_results_skips_zero_failure_runs():
    flaky, consistent = flaky_detector.analyze_results({"tests/a.py::t": []}, 3)
    assert flaky == [] and consistent == []


@pytest.mark.unit
def test_analyze_results_splits_flaky_and_consistent():
    failures = {
        "tests/unit/test_a.py::test_one": [1, 3],
        "tests/unit/test_b.py::test_two": [1, 2, 3],
    }
    flaky, consistent = flaky_detector.analyze_results(failures, 3)

    assert len(flaky) == 1
    assert flaky[0]["test"] == "tests/unit/test_a.py::test_one"
    assert len(consistent) == 1
    assert consistent[0]["test"] == "tests/unit/test_b.py::test_two"


@pytest.mark.unit
def test_run_detector_subprocess_timeout_returns_fail_payload(tmp_path, monkeypatch):
    """TimeoutExpired must yield standard JSON shape (no empty stdout for wrappers)."""

    def _raise_timeout(*_a, **_k):
        raise subprocess.TimeoutExpired(cmd=["pytest"], timeout=1)

    monkeypatch.setattr(flaky_detector.subprocess, "run", _raise_timeout)
    result = flaky_detector.run_detector(
        runs=1,
        workers="1",
        test_paths=["tests/unit"],
        progress_file=tmp_path / "flaky_progress.json",
        output_file=tmp_path / "flaky_report.md",
        include_e2e=False,
        timeout_seconds=30,
    )
    assert result["summary"]["status"] == "FAIL"
    assert result["summary"]["total_issues"] == 1
    assert "timed out" in str(result["details"].get("error", "")).lower()

