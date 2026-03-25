"""Helper-focused tests for development_tools/tests/run_test_coverage.py."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from unittest.mock import patch

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
    # BACKUP_FORMAT is no longer forced by coverage runs; backups are always directory-based.
    assert "BACKUP_FORMAT" not in updated
    assert "audioop" in updated["PYTHONWARNINGS"]
    assert updated["TEST_LOGS_DIR"].endswith("tests\\data\\tmp\\runtime_logs") or updated[
        "TEST_LOGS_DIR"
    ].endswith("tests/data/tmp/runtime_logs")


@pytest.mark.unit
def test_windows_crash_classification_helpers(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)

    assert regenerator._is_windows_crash_return_code(3221226505) is True
    assert regenerator._is_windows_crash_return_code(3221225477) is True
    assert regenerator._is_windows_crash_return_code(3221225786) is False
    assert regenerator._is_interrupt_return_code(3221225786) is True
    assert regenerator._is_interrupt_return_code(130) is True
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
    assert regenerator._format_return_code_hex(3221225786) == "0xC000013A"
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
def test_build_track_outcome_interrupt_signature(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)

    interrupt = regenerator._build_track_outcome(
        return_code=3221225786,
        parsed_results={"total_tests": 0},
        output="KeyboardInterrupt",
        track_name="parallel",
    )

    assert interrupt["classification"] == "crashed"
    assert interrupt["classification_reason"] == "interrupt_signal"
    assert interrupt["return_code_hex"] == "0xC000013A"


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


@pytest.mark.unit
def test_parse_pytest_test_results_full_summary(tmp_path: Path):
    """_parse_pytest_test_results parses full format summary."""
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    stdout = "4 failed, 100 passed, 2 skipped, 1 warnings"
    results = regenerator._parse_pytest_test_results(stdout)
    assert results["failed_count"] == 4
    assert results["passed_count"] == 100
    assert results["skipped_count"] == 2
    assert results["warnings_count"] == 1


@pytest.mark.unit
def test_parse_pytest_test_results_simple_format(tmp_path: Path):
    """_parse_pytest_test_results parses simple format (passed, deselected)."""
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    stdout = "145 passed, 3439 deselected"
    results = regenerator._parse_pytest_test_results(stdout)
    assert results["passed_count"] == 145


@pytest.mark.unit
def test_parse_pytest_test_results_maxfail_and_seed(tmp_path: Path):
    """_parse_pytest_test_results detects maxfail and extracts random seed."""
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    stdout = "interrupted: stopping after 3 failures\n--randomly-seed=12345"
    results = regenerator._parse_pytest_test_results(stdout)
    assert results["maxfail_reached"] is True
    assert results["random_seed"] == "12345"


@pytest.mark.unit
def test_parse_pytest_test_results_empty_returns_defaults(tmp_path: Path):
    """_parse_pytest_test_results returns default structure for empty input."""
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    results = regenerator._parse_pytest_test_results("")
    assert results["random_seed"] is None
    assert results["passed_count"] == 0
    assert results["failed_count"] == 0
    assert results["failed_tests"] == []


@pytest.mark.unit
def test_detect_expected_parallel_workers_parses_pytest_xdist_line(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    out = "gw0 [1] created: 4 / 4 workers\n"
    assert regenerator._detect_expected_parallel_workers(out) == 4


@pytest.mark.unit
def test_detect_expected_parallel_workers_empty_returns_none(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    assert regenerator._detect_expected_parallel_workers("") is None
    assert regenerator._detect_expected_parallel_workers("no workers here") is None


@pytest.mark.unit
def test_ensure_python_path_in_env_prepends_on_windows(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    fake_py = tmp_path / "python.exe"
    fake_py.write_bytes(b"")
    env = {"PATH": "C:\\\\existing"}
    with patch.object(sys, "platform", "win32"), patch.object(sys, "executable", str(fake_py)):
        updated = regenerator._ensure_python_path_in_env(dict(env))
    assert str(fake_py.parent) in updated["PATH"]
    assert "C:\\\\existing" in updated["PATH"]


@pytest.mark.unit
def test_merge_coverage_json_rejects_non_dict_inputs(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    merged = regenerator._merge_coverage_json([], {})  # type: ignore[arg-type]
    assert merged["files"] == {}
    assert merged["totals"]["num_statements"] == 0


@pytest.mark.unit
def test_merge_coverage_json_merges_disjoint_files(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    a = {
        "files": {
            "a.py": {
                "summary": {
                    "num_statements": 10,
                    "covered_lines": 5,
                    "missing_lines": 5,
                }
            }
        }
    }
    b = {
        "files": {
            "b.py": {
                "summary": {
                    "num_statements": 4,
                    "covered_lines": 4,
                    "missing_lines": 0,
                }
            }
        }
    }
    merged = regenerator._merge_coverage_json(a, b)
    assert "a.py" in merged["files"]
    assert "b.py" in merged["files"]
    assert merged["totals"]["num_statements"] == 14
    assert merged["totals"]["covered_lines"] == 9


@pytest.mark.unit
def test_discover_parallel_coverage_artifacts_collects_shards(tmp_path: Path):
    """Shard discovery picks up pytest-cov style parallel files and filters main names."""
    project = tmp_path / "proj"
    cov_dir = project / "cov"
    cov_dir.mkdir(parents=True)
    (cov_dir / ".coverage_parallel").write_text("main", encoding="utf-8")
    (cov_dir / ".coverage_parallel.host123.1.abc").write_text("s1", encoding="utf-8")
    (cov_dir / ".coverage.worker2").write_text("s2", encoding="utf-8")

    regenerator = CoverageMetricsRegenerator(str(project), parallel=False)
    regenerator.project_root = project

    found = regenerator._discover_parallel_coverage_artifacts(cov_dir)
    names = {p.name for p in found["parallel_shards"]}
    assert ".coverage_parallel.host123.1.abc" in names
    assert ".coverage.worker2" in names
    assert ".coverage_parallel" not in names


@pytest.mark.unit
def test_discover_parallel_coverage_artifacts_missing_dir_returns_empty(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    regenerator.project_root = tmp_path
    missing = tmp_path / "nope"
    found = regenerator._discover_parallel_coverage_artifacts(missing)
    assert found["parallel_shards"] == []
    assert found["project_root_shards"] == []


@pytest.mark.unit
def test_wait_for_parallel_coverage_artifacts_stops_when_expected_met(tmp_path: Path):
    """Waits until shard count meets expected_workers."""
    project = tmp_path / "proj"
    cov_dir = project / "cov"
    cov_dir.mkdir(parents=True)
    regenerator = CoverageMetricsRegenerator(str(project), parallel=False)
    regenerator.project_root = project

    calls = {"n": 0}

    def fake_discover(_path: Path):
        calls["n"] += 1
        if calls["n"] < 2:
            return {"parallel_shards": [], "project_root_shards": []}
        shard = cov_dir / ".coverage_parallel.x"
        shard.write_text("1", encoding="utf-8")
        return {
            "parallel_shards": [shard],
            "project_root_shards": [],
        }

    with patch.object(regenerator, "_discover_parallel_coverage_artifacts", side_effect=fake_discover):
        with patch("time.sleep"):
            result = regenerator._wait_for_parallel_coverage_artifacts(
                cov_dir, expected_workers=1, timeout_seconds=2.0, poll_seconds=0.01
            )

    assert len(result["parallel_shards"]) == 1


@pytest.mark.unit
def test_detect_expected_parallel_workers_invalid_integers_returns_none(tmp_path: Path):
    regenerator = CoverageMetricsRegenerator(str(tmp_path), parallel=False)
    with patch(
        "development_tools.tests.run_test_coverage.re.findall",
        return_value=[("notint", "1")],
    ):
        assert regenerator._detect_expected_parallel_workers("created: notint / 1 workers") is None
