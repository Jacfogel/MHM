"""Helper-focused tests for development_tools/tests/run_test_coverage.py."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module

coverage_module = load_development_tools_module("run_test_coverage")
CoverageMetricsRegenerator = coverage_module.CoverageMetricsRegenerator


@pytest.mark.unit
def test_strip_xdist_args_removes_xdist_flags():
    cmd = [
        "python",
        "-m",
        "pytest",
        "-n",
        "4",
        "--dist",
        "loadscope",
        "--dist=worksteal",
        "--numprocesses",
        "2",
        "-q",
    ]
    stripped = CoverageMetricsRegenerator._strip_xdist_args(cmd)
    assert stripped == ["python", "-m", "pytest", "-q"]


@pytest.mark.unit
def test_remove_tree_with_retries_handles_missing_path(tmp_path: Path):
    missing = tmp_path / "missing"
    assert CoverageMetricsRegenerator._remove_tree_with_retries(missing) is True


@pytest.mark.unit
def test_remove_tree_with_retries_removes_existing_tree(tmp_path: Path):
    target = tmp_path / "to-delete" / "nested"
    target.mkdir(parents=True, exist_ok=True)
    (target / "file.txt").write_text("x", encoding="utf-8")

    assert CoverageMetricsRegenerator._remove_tree_with_retries(tmp_path / "to-delete") is True
    assert not (tmp_path / "to-delete").exists()


@pytest.mark.unit
def test_configure_test_logging_env_sets_isolated_paths(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    env = {"PYTHONWARNINGS": "default"}

    updated = regenerator._configure_test_logging_env(env)

    assert updated["MHM_DEV_TOOLS_RUN"] == "0"
    assert updated["MHM_TESTING"] == "1"
    assert updated["BACKUP_FORMAT"] == "zip"
    assert "audioop" in updated["PYTHONWARNINGS"]
    assert updated["TEST_LOGS_DIR"].endswith("tests\\data\\tmp\\runtime_logs") or updated[
        "TEST_LOGS_DIR"
    ].endswith("tests/data/tmp/runtime_logs")


@pytest.mark.unit
def test_windows_crash_classification_helpers(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)

    assert regenerator._is_windows_crash_return_code(3221226505) is True
    assert regenerator._is_windows_crash_return_code(3221225477) is True
    assert regenerator._is_windows_crash_return_code(1) is False

    reason, context = regenerator._classify_windows_crash_return_code(3221226505)
    assert reason == "windows_status_dll_not_found"
    assert "Missing DLL" in context

    reason_none, context_none = regenerator._classify_windows_crash_return_code(123)
    assert reason_none is None
    assert context_none is None


@pytest.mark.unit
def test_format_return_code_hex_known_and_generic_codes(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    assert regenerator._format_return_code_hex(3221226505) == "0xC0000135"
    assert regenerator._format_return_code_hex(3221225477) == "0xC0000005"
    assert regenerator._format_return_code_hex(5) == "0x00000005"
    assert regenerator._format_return_code_hex(None) is None


@pytest.mark.unit
def test_infra_cleanup_and_xdist_detector_helpers(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    assert (
        regenerator._is_infra_cleanup_error(
            "PermissionError: [WinError 5] cleanup_dead_symlinks failed"
        )
        is True
    )
    assert regenerator._is_infra_cleanup_error("all good") is False
    assert (
        regenerator._is_xdist_worker_crash_output(
            "Windows fatal exception\nnode down: Not properly terminated"
        )
        is True
    )
    assert regenerator._is_xdist_worker_crash_output("clean output") is False


@pytest.mark.unit
def test_build_track_outcome_passed_and_skipped_branches(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)

    passed = regenerator._build_track_outcome(
        return_code=0,
        parsed_results={"total_tests": 4, "passed_count": 4},
        output="4 passed",
        track_name="parallel",
    )
    skipped = regenerator._build_track_outcome(
        return_code=None,
        parsed_results={"total_tests": 0},
        output="",
        track_name="no_parallel",
    )

    assert passed["classification"] == "passed"
    assert passed["classification_reason"] == "pytest_passed"
    assert skipped["classification"] == "skipped"
    assert skipped["classification_reason"] == "no_output_no_return_code"


@pytest.mark.unit
def test_classify_coverage_outcome_precedence(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)

    assert (
        regenerator._classify_coverage_outcome({}, {}, coverage_collected=False)
        == "coverage_failed"
    )
    assert (
        regenerator._classify_coverage_outcome(
            {"classification": "infra_cleanup_error"},
            {"classification": "passed"},
            coverage_collected=True,
        )
        == "infra_cleanup_error"
    )
    assert (
        regenerator._classify_coverage_outcome(
            {"classification": "crashed"},
            {"classification": "passed"},
            coverage_collected=True,
        )
        == "crashed"
    )
    assert (
        regenerator._classify_coverage_outcome(
            {"classification": "failed"},
            {"classification": "passed"},
            coverage_collected=True,
        )
        == "test_failures"
    )
    assert (
        regenerator._classify_coverage_outcome(
            {"classification": "passed"},
            {"classification": "skipped"},
            coverage_collected=True,
        )
        == "clean"
    )


@pytest.mark.unit
def test_rotate_log_files_moves_main_logs_to_archive(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    regenerator.coverage_logs_dir = tmp_path / "development_tools" / "tests" / "logs"
    regenerator.coverage_logs_dir.mkdir(parents=True, exist_ok=True)

    for idx in range(4):
        log_path = regenerator.coverage_logs_dir / f"pytest_parallel_stdout_2026-02-28_{idx:02d}.log"
        log_path.write_text(f"log {idx}", encoding="utf-8")

    regenerator._rotate_log_files("pytest_parallel_stdout", max_versions=3)

    main_logs = list(regenerator.coverage_logs_dir.glob("pytest_parallel_stdout_*.log"))
    archive_logs = list(
        (regenerator.coverage_logs_dir / "archive").glob("pytest_parallel_stdout_*.log")
    )
    assert len(main_logs) <= 1
    assert len(archive_logs) <= 2


@pytest.mark.unit
def test_generate_coverage_summary_fallback_and_timestamp(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)

    summary = regenerator._generate_coverage_summary_fallback({}, {"overall_coverage": 87.5})
    assert summary == "Overall Coverage: 87.5%"

    timestamp = regenerator.get_current_timestamp()
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", timestamp)
