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
)


_DEFAULT_IGNORE_ARGS = (
    "--ignore=tests/data/pytest-tmp-*",
    "--ignore=tests/data/pytest-of-*",
)


class CoveragePytestPathSplit(NamedTuple):
    """Host pytest paths and ``--ignore`` flags."""

    host_paths: list[str]
    host_extra_args: list[str]
    use_host_default: bool


def partition_coverage_pytest_paths(
    test_filter_args: list[str],
    *,
    default_test_path: str = "tests/",
    tools_roots: list[str] | None = None,
) -> CoveragePytestPathSplit:
    """Keep development-tools tests out of the host coverage selection.

    ``development_tools/tool_tests/`` loads a conftest that refuses the host
    pytest.ini. An empty filter means the whole default
    tree, so the host command collects that tree and ignores the tools root.
    """
    roots = ["development_tools", *(tools_roots or DEFAULT_TOOLS_TEST_PATHS)]
    if not test_filter_args:
        host_paths, _ = partition_test_paths([default_test_path], roots)
        return CoveragePytestPathSplit([], host_ignore_args(roots), bool(host_paths))

    host_paths, _ = partition_test_paths(test_filter_args, roots)
    return CoveragePytestPathSplit(host_paths, host_ignore_args(roots), False)


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
