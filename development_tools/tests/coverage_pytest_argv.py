"""Pure pytest argv builders for coverage runs (V6 B-015).

Extracted from ``run_test_coverage.CoverageMetricsRegenerator`` so command
construction can be unit-tested without the full regenerator graph.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from development_tools.tests.pytest_isolation import (
    DEFAULT_TOOLS_TEST_PATHS,
    host_ignore_args,
    partition_test_paths,
    path_contains_tools_root,
    tools_suite_pytest_args,
)


_DEFAULT_IGNORE_ARGS = (
    "--ignore=tests/data/pytest-tmp-*",
    "--ignore=tests/data/pytest-of-*",
)


class CoveragePytestPathSplit(NamedTuple):
    """Host pytest paths, tools pytest paths, and host ``--ignore`` flags."""

    host_paths: list[str]
    tools_paths: list[str]
    host_extra_args: list[str]
    use_host_default: bool


def partition_coverage_pytest_paths(
    test_filter_args: list[str],
    *,
    default_test_path: str = "tests/",
    tools_roots: list[str] | None = None,
) -> CoveragePytestPathSplit:
    """Split a coverage pytest selection into host and development-tools paths.

    ``tests/development_tools/`` loads a conftest that refuses the host
    pytest.ini. Those paths must be a second pytest process started with
    ``development_tools/pytest.ini``. An empty filter means the whole default
    tree, so the host command collects that tree and ignores the tools root.
    """
    roots = [str(root) for root in (tools_roots or DEFAULT_TOOLS_TEST_PATHS) if str(root).strip()]
    if not test_filter_args:
        if roots and path_contains_tools_root(default_test_path, roots):
            return CoveragePytestPathSplit([], list(roots), host_ignore_args(roots), True)
        return CoveragePytestPathSplit([], [], [], True)

    host_paths, tools_paths = partition_test_paths(list(test_filter_args), roots)
    ignore = (
        host_ignore_args(roots)
        if roots and any(path_contains_tools_root(path, roots) for path in host_paths)
        else []
    )
    return CoveragePytestPathSplit(host_paths, tools_paths, ignore, False)


def build_no_parallel_test_args(
    test_filter_args: list[str],
    test_directory: str,
    *,
    skip_default_path: bool = False,
) -> list[str]:
    """Return pytest path arguments for the serial no_parallel phase."""
    if test_filter_args:
        return list(test_filter_args)
    if skip_default_path:
        return []
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
    extra_args: list[str] | None = None,
    skip_default_path: bool = False,
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

    if extra_args:
        cmd.extend(extra_args)
    if test_filter_args:
        cmd.extend(test_filter_args)
    elif not skip_default_path:
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
    extra_args: list[str] | None = None,
    skip_default_path: bool = False,
) -> list[str]:
    """Build the serial no_parallel track coverage pytest command."""
    path_args = build_no_parallel_test_args(
        test_filter_args,
        test_directory,
        skip_default_path=skip_default_path,
    )
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
        *(extra_args or []),
        *path_args,
    ]


def build_isolated_tools_coverage_pytest_cmd(
    *,
    executable: str,
    parallel: bool,
    num_workers: str,
    cov_args: list[str],
    coverage_config_path: Path,
    maxfail: int,
    tools_paths: list[str],
) -> list[str]:
    """Build the development-tools coverage pytest command for a unified run.

    Uses ``development_tools/pytest.ini`` so the tools conftest accepts the
    process. Coverage is written to a separate data file and combined later.
    """
    cmd: list[str] = [
        executable,
        "-m",
        "pytest",
        *tools_suite_pytest_args(),
        "-p",
        "no:cacheprovider",
        "-m",
        "not e2e",
    ]
    if parallel:
        cmd.extend(["-n", str(num_workers), "--dist=loadscope", "--cov-append"])
    cmd.extend(
        [
            *cov_args,
            "--cov-report=term-missing",
            f"--cov-config={coverage_config_path.resolve()}",
            "--tb=line",
            "-q",
            f"--maxfail={maxfail}",
            *_DEFAULT_IGNORE_ARGS,
            *tools_paths,
        ]
    )
    return cmd


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
        *tools_suite_pytest_args(),
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
