"""Coverage JSON merge and parallel shard discovery helpers (V6 B-015).

Extracted from ``run_test_coverage.CoverageMetricsRegenerator``.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


def detect_expected_parallel_workers(pytest_output: str) -> int | None:
    """Extract expected xdist worker count from pytest output when available."""
    if not pytest_output:
        return None
    matches = re.findall(r"created:\s*(\d+)\s*/\s*(\d+)\s*workers", pytest_output)
    if not matches:
        return None
    try:
        created, configured = matches[-1]
        created_int = int(created)
        configured_int = int(configured)
        # Prefer created worker count; fallback to configured.
        return created_int if created_int > 0 else configured_int
    except (TypeError, ValueError):
        return None


def discover_parallel_coverage_artifacts(
    coverage_dir: Path, project_root: Path
) -> dict[str, list[Path]]:
    """Discover coverage files that should exist before combine.

    pytest-cov with data_suffix=True creates ``.coverage_parallel.<machine>.<pid>.<random>``
    per worker (not ``.worker0``). Also support legacy ``.coverage_parallel.worker*`` naming.
    """
    artifacts: dict[str, list[Path]] = {
        "parallel_shards": [],
        "project_root_shards": [],
    }
    if not coverage_dir.exists():
        return artifacts

    # All .coverage_parallel.* except the main file (data_suffix creates .machine.pid.random)
    artifacts["parallel_shards"].extend(
        f
        for f in coverage_dir.glob(".coverage_parallel.*")
        if f.name != ".coverage_parallel" and f.is_file()
    )
    artifacts["parallel_shards"].extend(
        [f for f in coverage_dir.glob(".coverage.worker*") if f.name != ".coverage"]
    )
    artifacts["parallel_shards"] = [
        f
        for f in artifacts["parallel_shards"]
        if f.name
        not in {".coverage_parallel", ".coverage_no_parallel", ".coverage"}
    ]

    # Same for project root (workers may write to cwd if COVERAGE_FILE not respected)
    artifacts["project_root_shards"].extend(
        f
        for f in project_root.glob(".coverage_parallel.*")
        if f.name != ".coverage_parallel" and f.is_file()
    )
    artifacts["project_root_shards"].extend(
        [
            f
            for f in project_root.glob(".coverage.worker*")
            if f.name != ".coverage"
        ]
    )
    return artifacts


def wait_for_parallel_coverage_artifacts(
    coverage_dir: Path,
    expected_workers: int | None,
    *,
    timeout_seconds: float = 5.0,
    poll_seconds: float = 0.25,
    discover_fn: Callable[[Path], dict[str, list[Path]]] | None = None,
    project_root: Path | None = None,
    log: Any | None = None,
) -> dict[str, Any]:
    """Wait briefly for shard files to appear before combine on slower filesystems."""
    if discover_fn is None:
        if project_root is None:
            raise ValueError("project_root is required when discover_fn is not provided")
        root = project_root

        def _default_discover(path: Path) -> dict[str, list[Path]]:
            return discover_parallel_coverage_artifacts(path, root)

        discover_fn = _default_discover

    start = time.time()
    discovered: dict[str, list[Path]] = {
        "parallel_shards": [],
        "project_root_shards": [],
    }
    while time.time() - start < timeout_seconds:
        discovered = discover_fn(coverage_dir)
        shard_count = len(discovered["parallel_shards"])
        if expected_workers and shard_count >= expected_workers:
            break
        # If workers are unknown, any shard is enough to proceed early.
        if expected_workers is None and shard_count > 0:
            break
        time.sleep(poll_seconds)

    elapsed = round(time.time() - start, 2)
    if log:
        log.debug(
            "Coverage shard detection: "
            f"expected_workers={expected_workers if expected_workers is not None else 'unknown'}, "
            f"found_in_coverage_dir={len(discovered['parallel_shards'])}, "
            f"found_in_project_root={len(discovered['project_root_shards'])}, "
            f"waited={elapsed}s"
        )
        if discovered["parallel_shards"]:
            log.debug(
                "Coverage shard files (coverage dir): "
                f"{[p.name for p in discovered['parallel_shards'][:12]]}"
            )
        if discovered["project_root_shards"]:
            log.warning(
                "Coverage shard files found in project root (unexpected): "
                f"{[p.name for p in discovered['project_root_shards'][:12]]}"
            )
    return {
        "expected_workers": expected_workers,
        "waited_seconds": elapsed,
        "parallel_shards": discovered["parallel_shards"],
        "project_root_shards": discovered["project_root_shards"],
    }


def merge_coverage_json(
    coverage_json_1: dict[str, Any],
    coverage_json_2: dict[str, Any],
    *,
    domain_mapper: Any | None = None,
    changed_domains: set[str] | None = None,
    log: Any | None = None,
) -> dict[str, Any]:
    """Merge two coverage JSON dictionaries with line-union for unchanged domains.

    Coverage JSON contains per-file executed/missing line lists. For selective
    runs, executed lines for unchanged domains must be unioned; otherwise
    coverage drops because fewer tests ran. For files in changed domains where
    statement counts differ, prefer the second (fresh) payload.
    """
    merged: dict[str, Any] = {
        "files": {},
        "totals": {
            "num_statements": 0,
            "covered_lines": 0,
            "missing_lines": 0,
            "percent_covered": 0.0,
        },
    }

    if not isinstance(coverage_json_1, dict) or not isinstance(coverage_json_2, dict):
        if log:
            log.warning(
                "Invalid coverage JSON structure in merge - one or both inputs are not dictionaries"
            )
        return merged

    files_1 = coverage_json_1.get("files", {})
    files_2 = coverage_json_2.get("files", {})

    if not isinstance(files_1, dict) or not isinstance(files_2, dict):
        if log:
            log.warning(
                "Invalid 'files' structure in coverage JSON - expected dictionaries"
            )
        return merged

    files_1_count = 0
    for file_path, file_data in files_1.items():
        if isinstance(file_data, dict):
            merged["files"][file_path] = file_data.copy()
            files_1_count += 1

    duplicate_count = 0
    files_2_unique_count = 0
    for file_path, file_data in files_2.items():
        if not isinstance(file_data, dict):
            continue
        if file_path in merged["files"]:
            duplicate_count += 1
            existing = merged["files"][file_path]
            if not isinstance(existing, dict):
                merged["files"][file_path] = file_data.copy()
                continue

            normalized_path = file_path.replace("\\", "/")
            file_domain = (
                domain_mapper.get_source_domain(normalized_path)
                if domain_mapper is not None
                else None
            )

            summary_1 = (
                existing.get("summary", {})
                if isinstance(existing.get("summary"), dict)
                else {}
            )
            summary_2 = (
                file_data.get("summary", {})
                if isinstance(file_data.get("summary"), dict)
                else {}
            )
            ns_1 = int(summary_1.get("num_statements", 0) or 0)
            ns_2 = int(summary_2.get("num_statements", 0) or 0)

            if (
                isinstance(changed_domains, set)
                and file_domain in changed_domains
                and ns_1 != ns_2
            ):
                merged["files"][file_path] = file_data.copy()
            else:
                existing_executed = set(existing.get("executed_lines", []) or [])
                fresh_executed = set(file_data.get("executed_lines", []) or [])
                executed_union = sorted(existing_executed | fresh_executed)

                existing_missing = set(existing.get("missing_lines", []) or [])
                fresh_missing = set(file_data.get("missing_lines", []) or [])
                # Only lines missing in BOTH runs are still missing after combining
                missing_intersection = sorted(existing_missing & fresh_missing)

                existing_excluded = set(existing.get("excluded_lines", []) or [])
                fresh_excluded = set(file_data.get("excluded_lines", []) or [])
                excluded_union = sorted(existing_excluded | fresh_excluded)

                merged_file = existing.copy()
                merged_file["executed_lines"] = executed_union
                merged_file["missing_lines"] = missing_intersection
                merged_file["excluded_lines"] = excluded_union

                covered_lines = len(executed_union)
                missing_lines = len(missing_intersection)
                num_statements = max(ns_1, ns_2, covered_lines + missing_lines)
                excluded_lines = len(excluded_union)

                percent = (
                    round((covered_lines / num_statements) * 100, 2)
                    if num_statements > 0
                    else 0.0
                )

                merged_file["summary"] = {
                    "num_statements": num_statements,
                    "covered_lines": covered_lines,
                    "missing_lines": missing_lines,
                    "excluded_lines": excluded_lines,
                    "percent_covered": percent,
                    "percent_covered_display": f"{percent:.2f}",
                }

                merged["files"][file_path] = merged_file
        else:
            merged["files"][file_path] = file_data.copy()
            files_2_unique_count += 1

    if log:
        log.debug(
            f"Merge details: {files_1_count} files from first JSON, {files_2_unique_count} unique files from second JSON, "
            f"{duplicate_count} duplicates (line-union for unchanged domains; fresh for changed domains)"
        )

    total_statements = 0
    total_covered = 0
    total_missing = 0

    for _file_path, file_data in merged["files"].items():
        if not isinstance(file_data, dict):
            continue
        summary = file_data.get("summary", {})
        if isinstance(summary, dict):
            total_statements += summary.get("num_statements", 0)
            total_covered += summary.get("covered_lines", 0)
            total_missing += summary.get("missing_lines", 0)

    merged["totals"]["num_statements"] = total_statements
    merged["totals"]["covered_lines"] = total_covered
    merged["totals"]["missing_lines"] = total_missing

    if total_statements > 0:
        merged["totals"]["percent_covered"] = round(
            (total_covered / total_statements) * 100, 2
        )

    return merged
