"""Pure pytest argv builders for coverage runs (V6 B-015).

Extracted from ``run_test_coverage.CoverageMetricsRegenerator`` so command
construction can be unit-tested without the full regenerator graph.
"""

from __future__ import annotations

from pathlib import Path


_DEFAULT_IGNORE_ARGS = (
    "--ignore=tests/data/pytest-tmp-*",
    "--ignore=tests/data/pytest-of-*",
)


def build_no_parallel_test_args(
    test_filter_args: list[str], test_directory: str
) -> list[str]:
    """Return pytest path arguments for the serial no_parallel phase."""
    if test_filter_args:
        return list(test_filter_args)
    return [test_directory]


def build_main_coverage_pytest_cmd(
    *,
    executable: str,
    parallel: bool,
    num_workers: str,
    cov_args: list[str],
    coverage_config_path: Path,
    maxfail: int,
    test_filter_args: list[str],
    coverage_json_output: Path | None = None,
    default_test_path: str = "tests/",
) -> list[str]:
    """Build the main (full-suite) coverage pytest command.

    Parallel mode omits JSON report generation (combine later). Serial mode
    writes JSON to ``coverage_json_output`` when provided.
    """
    cmd: list[str] = [
        executable,
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
    ]

    if parallel:
        cmd.extend(["-m", "not (no_parallel or e2e)"])
        cmd.extend(["-n", str(num_workers)])
        cmd.extend(["--dist=loadscope"])
        cmd.extend(
            [
                "--cov-append",
                *cov_args,
                "--cov-report=term-missing",
                f"--cov-config={coverage_config_path.resolve()}",
                "--tb=line",
                "-q",
                f"--maxfail={maxfail}",
                *_DEFAULT_IGNORE_ARGS,
            ]
        )
    else:
        serial_reports = [
            *cov_args,
            "--cov-report=term-missing",
        ]
        if coverage_json_output is not None:
            serial_reports.append(
                f"--cov-report=json:{coverage_json_output.resolve()}"
            )
        serial_reports.extend(
            [
                f"--cov-config={coverage_config_path.resolve()}",
                "--tb=line",
                "-q",
                f"--maxfail={maxfail}",
                *_DEFAULT_IGNORE_ARGS,
            ]
        )
        cmd.extend(serial_reports)

    if test_filter_args:
        cmd.extend(test_filter_args)
    else:
        cmd.append(default_test_path)
    return cmd


def build_no_parallel_coverage_pytest_cmd(
    *,
    executable: str,
    cov_args: list[str],
    coverage_config_path: Path,
    maxfail: int,
    test_filter_args: list[str],
    test_directory: str,
) -> list[str]:
    """Build the serial no_parallel track coverage pytest command."""
    path_args = build_no_parallel_test_args(test_filter_args, test_directory)
    return [
        executable,
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-m",
        "no_parallel and not e2e",
        *cov_args,
        "--cov-report=term-missing",
        f"--cov-config={coverage_config_path.resolve()}",
        "--tb=line",
        "-q",
        f"--maxfail={maxfail}",
        *_DEFAULT_IGNORE_ARGS,
        *path_args,
    ]


def build_dev_tools_coverage_pytest_cmd(
    *,
    executable: str,
    parallel: bool,
    num_workers: str,
    coverage_json_output: Path,
    coverage_config_path: Path,
    maxfail: int = 10,
    test_path: str = "tests/development_tools/",
) -> list[str]:
    """Build the development_tools-only coverage pytest command."""
    cmd: list[str] = [
        executable,
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-m",
        "not e2e",
    ]
    if parallel:
        cmd.extend(["-n", str(num_workers), "--dist=loadscope"])
    cmd.extend(
        [
            "--cov=development_tools",
            "--cov-report=term-missing",
            f"--cov-report=json:{coverage_json_output.resolve()}",
            f"--cov-config={coverage_config_path}",
            "--tb=line",
            "-q",
            f"--maxfail={maxfail}",
            "--continue-on-collection-errors",
            *_DEFAULT_IGNORE_ARGS,
            test_path,
        ]
    )
    return cmd
