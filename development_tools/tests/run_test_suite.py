#!/usr/bin/env python3
# TOOL_TIER: core

"""Portable pytest suite runner for Tier 3 audits.

Runs pytest without coverage and emits a structured Tier 3 test outcome that
matches the existing audit report contract.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_TEST_RUN = {
    "pytest_command": [sys.executable, "-m", "pytest"],
    "pytest_base_args": ["--tb=short", "--disable-warnings", "--maxfail=10"],
    "test_paths": None,
    "workers": "auto",
    "timeout_seconds": 1200,
    "exclude_markers": ["e2e", "slow"],
    "default_profile": "quick",
    "suite_profile": "quick",
    "no_parallel_marker": "no_parallel",
    "sigint_taps_to_stop": 5,
    "sigint_window_seconds": 2.0,
    "sigint_debounce_seconds": 0.35,
    "junit_dir": "development_tools/tests/jsons/test_suite_junit",
}


_INTERRUPT_TAPS = 0
_LAST_INTERRUPT_TIME: float | None = None
_STOP_REQUESTED = False
_ACTIVE_PROCESS: subprocess.Popen[str] | None = None
_SIGINT_CFG = DEFAULT_TEST_RUN.copy()

try:
    from development_tools.shared.logging import get_dev_tools_logger
    from development_tools.tests.test_file_coverage_cache import TestFileCoverageCache

    _suite_logger = get_dev_tools_logger("development_tools")
except ImportError:
    _suite_logger = None
    TestFileCoverageCache = None  # type: ignore[misc, assignment]


@dataclass
class PhaseResult:
    name: str
    command: list[str]
    return_code: int | None
    duration_seconds: float
    counts: dict[str, int]
    failed_node_ids: list[str]
    output_tail: str
    junit_xml: str
    interrupted: bool = False

    @property
    def classification(self) -> str:
        if self.interrupted:
            return "crashed"
        if self.return_code in (None,):
            return "crashed"
        if self.return_code == 5 and self.counts.get("total", 0) == 0:
            return "skipped"
        if self.return_code < 0 or self.return_code in {130, 3221225786, 3221225477}:
            return "crashed"
        if self.return_code not in (0, 5) and self.counts.get("total", 0) == 0:
            return "crashed"
        if self.counts.get("errors", 0) > 0:
            return "crashed"
        if self.counts.get("failed", 0) > 0 or self.return_code not in (0, 5):
            return "failed"
        return "passed"


def _load_config(profile: str | None = None) -> dict[str, Any]:
    try:
        from development_tools import config

        return config.get_test_run_config(profile)
    except Exception:
        result = dict(DEFAULT_TEST_RUN)
        profile_name = str(profile or result.get("default_profile") or "quick").strip().lower()
        if profile_name == "full":
            result["exclude_markers"] = ["e2e"]
        else:
            result["exclude_markers"] = ["e2e", "slow"]
        result["suite_profile"] = profile_name
        if not result.get("test_paths"):
            result["test_paths"] = ["tests"]
        return result


def _has_xdist() -> bool:
    return importlib.util.find_spec("xdist") is not None


def _resolved_worker_count(workers_cfg: str | None) -> int:
    """Match run_tests.py worker policy; leave headroom during Tier 3 audit contention."""
    workers_text = str(workers_cfg or "auto").strip().lower()
    if workers_text not in {"", "auto", "none"}:
        try:
            return max(1, int(workers_text))
        except ValueError:
            pass
    import multiprocessing

    cpu_count = multiprocessing.cpu_count()
    if os.environ.get("MHM_TIER3_AUDIT") == "1":
        return min(4, max(2, cpu_count // 3))
    return min(6, max(2, cpu_count // 2))


def _append_pytest_runtime_options(
    command: list[str],
    *,
    force_serial: bool,
    worker_count: int | None = None,
) -> None:
    """Apply the same runtime isolation/verbosity defaults as run_tests.py."""
    command.extend(["-W", "ignore::DeprecationWarning"])
    run_id = time.strftime("%Y%m%d_%H%M%S")
    pytest_root = Path("tests/data/tmp/pytest_runner") / run_id
    parallel_basetemp = pytest_root / "parallel"
    serial_basetemp = pytest_root / "serial"
    pytest_cache_dir = Path("tests/data/tmp/pytest_cache")
    basetemp = serial_basetemp if force_serial else parallel_basetemp
    basetemp.mkdir(parents=True, exist_ok=True)
    pytest_cache_dir.mkdir(parents=True, exist_ok=True)
    command.extend(
        [
            "--basetemp",
            str(basetemp),
            "-o",
            f"cache_dir={pytest_cache_dir}",
            "--ignore=tests/data",
            "--ignore=tests/data/tmp",
            "--ignore-glob=tests/data/tmp/**",
            "-q",
            "-o",
            "durations=0",
        ]
    )
    if not force_serial and worker_count and worker_count > 1:
        command.extend(["-n", str(worker_count), "--dist=loadscope"])


def _marker_expression(*, include_no_parallel: bool, cfg: dict[str, Any]) -> str:
    no_parallel = str(cfg.get("no_parallel_marker") or "no_parallel")
    parts: list[str] = [no_parallel if include_no_parallel else f"not {no_parallel}"]
    for marker in cfg.get("exclude_markers") or []:
        marker_text = str(marker).strip()
        if marker_text:
            parts.append(f"not {marker_text}")
    return " and ".join(parts)


def _pytest_command(cfg: dict[str, Any]) -> list[str]:
    command = [str(part) for part in (cfg.get("pytest_command") or DEFAULT_TEST_RUN["pytest_command"])]
    if command and command[0].lower() in {"python", "python.exe", "{python}"}:
        command[0] = sys.executable
    return command


def build_phase_command(
    *,
    phase: str,
    cfg: dict[str, Any],
    junit_xml: Path,
    force_serial: bool = False,
    test_paths: list[str] | None = None,
) -> list[str]:
    command = _pytest_command(cfg)
    command.extend(str(part) for part in (cfg.get("pytest_base_args") or []))
    command.extend(["--junitxml", str(junit_xml)])
    include_no_parallel = phase == "no_parallel"
    command.extend(["-m", _marker_expression(include_no_parallel=include_no_parallel, cfg=cfg)])
    worker_count: int | None = None
    if phase == "parallel" and not force_serial and _has_xdist():
        worker_count = _resolved_worker_count(str(cfg.get("workers") or "auto"))
    _append_pytest_runtime_options(
        command,
        force_serial=force_serial or worker_count in (None, 1),
        worker_count=worker_count,
    )
    paths = test_paths if test_paths is not None else (cfg.get("test_paths") or ["tests"])
    command.extend(str(path) for path in paths)
    return command


def _handle_sigint(signum: int, _frame: object) -> None:
    global _INTERRUPT_TAPS, _LAST_INTERRUPT_TIME, _STOP_REQUESTED
    now = time.time()
    window = float(_SIGINT_CFG.get("sigint_window_seconds", 2.0) or 2.0)
    debounce = float(_SIGINT_CFG.get("sigint_debounce_seconds", 0.35) or 0.35)
    threshold = int(_SIGINT_CFG.get("sigint_taps_to_stop", 5) or 5)
    if _LAST_INTERRUPT_TIME is not None:
        elapsed = now - _LAST_INTERRUPT_TIME
        if elapsed < debounce:
            return
        if elapsed > window:
            _INTERRUPT_TAPS = 0
    _INTERRUPT_TAPS += 1
    _LAST_INTERRUPT_TIME = now
    if threshold <= _INTERRUPT_TAPS:
        _STOP_REQUESTED = True
        if _ACTIVE_PROCESS is not None:
            _terminate_process_tree(_ACTIVE_PROCESS)
        return
    remaining = threshold - _INTERRUPT_TAPS
    print(f"[SIGINT] Ignoring interrupt; {remaining} more within {int(window)}s to stop.", flush=True)


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                capture_output=True,
                text=True,
                timeout=10,
            )
        else:
            os.killpg(process.pid, signal.SIGTERM)
    except Exception:
        with contextlib.suppress(Exception):
            process.terminate()


def _test_file_rel_from_case(classname: str, name: str) -> str | None:
    if classname:
        return f"{classname.replace('.', '/')}.py"
    if "::" in name:
        return name.split("::", 1)[0]
    return None


def _parse_junit_by_test_file(xml_path: Path) -> dict[str, dict[str, Any]]:
    """Group JUnit cases by test file path (project-relative)."""
    by_file: dict[str, dict[str, Any]] = {}
    if not xml_path.exists():
        return by_file
    try:
        root = ET.parse(xml_path).getroot()  # nosec B314 - local pytest output
    except Exception:
        return by_file
    for case in root.findall(".//testcase"):
        classname = case.get("classname") or ""
        name = case.get("name") or "unknown"
        rel = _test_file_rel_from_case(classname, name)
        if not rel:
            continue
        entry = by_file.setdefault(
            rel,
            {
                "counts": {"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                "failed_node_ids": [],
            },
        )
        counts = entry["counts"]
        counts["total"] += 1
        if case.find("skipped") is not None:
            counts["skipped"] += 1
            counts["passed"] += 0
        elif case.find("failure") is not None or case.find("error") is not None:
            if case.find("error") is not None:
                counts["errors"] += 1
            else:
                counts["failed"] += 1
            node_class = classname.replace(".", "/")
            node = f"{node_class}.py::{name}" if node_class else name
            entry["failed_node_ids"].append(node)
        else:
            counts["passed"] += 1
    for entry in by_file.values():
        entry["failed_node_ids"] = sorted(set(entry["failed_node_ids"]))
    return by_file


def _merge_counts(*parts: dict[str, int]) -> dict[str, int]:
    merged = {"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    for part in parts:
        for key in merged:
            merged[key] += int(part.get(key, 0) or 0)
    return merged


def _phase_from_counts(
    *,
    name: str,
    counts: dict[str, int],
    failed_node_ids: list[str],
    junit_xml: str,
    duration_seconds: float = 0.0,
    return_code: int = 0,
) -> PhaseResult:
    return PhaseResult(
        name=name,
        command=[],
        return_code=return_code,
        duration_seconds=duration_seconds,
        counts=counts,
        failed_node_ids=sorted(set(failed_node_ids)),
        output_tail="",
        junit_xml=junit_xml,
    )


def _parse_junit(xml_path: Path) -> tuple[dict[str, int], list[str]]:
    counts = {"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    failed_nodes: list[str] = []
    if not xml_path.exists():
        return counts, failed_nodes
    try:
        root = ET.parse(xml_path).getroot()  # nosec B314 - local pytest output
    except Exception:
        return counts, failed_nodes
    for suite in root.findall(".//testsuite"):
        total = int(suite.get("tests", 0) or 0)
        failures = int(suite.get("failures", 0) or 0)
        errors = int(suite.get("errors", 0) or 0)
        skipped = int(suite.get("skipped", 0) or 0)
        counts["total"] += total
        counts["failed"] += failures
        counts["errors"] += errors
        counts["skipped"] += skipped
        counts["passed"] += max(0, total - failures - errors - skipped)
    for case in root.findall(".//testcase"):
        if case.find("failure") is None and case.find("error") is None:
            continue
        classname = (case.get("classname") or "").replace(".", "/")
        name = case.get("name") or "unknown"
        node = f"{classname}.py::{name}" if classname else name
        failed_nodes.append(node)
    return counts, sorted(set(failed_nodes))


def _is_xdist_teardown_interrupt_output(output: str) -> bool:
    """Detect local xdist/execnet teardown hangs after test execution completes."""
    lowered = output.lower()
    return all(
        marker in lowered
        for marker in (
            "xdist",
            "teardown_nodes",
            "execnet",
            "keyboardinterrupt",
        )
    )


def _run_phase(
    name: str,
    cfg: dict[str, Any],
    junit_dir: Path,
    *,
    force_serial: bool = False,
    test_paths: list[str] | None = None,
) -> PhaseResult:
    global _ACTIVE_PROCESS
    junit_xml = junit_dir / f"{name}.xml"
    with contextlib.suppress(OSError):
        junit_xml.unlink()
    command = build_phase_command(
        phase=name,
        cfg=cfg,
        junit_xml=junit_xml,
        force_serial=force_serial,
        test_paths=test_paths,
    )
    start = time.perf_counter()
    output = ""
    return_code: int | None = None
    interrupted = False
    creationflags = 0
    popen_kwargs: dict[str, Any] = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
        "cwd": str(Path.cwd()),
        "env": {
            **os.environ,
            # Keep pytest on test loggers (see tests/conftest.py); do not inherit
            # audit CLI MHM_TESTING=0 into workers.
            "MHM_TESTING": "1",
            "MHM_TIER3_AUDIT": "1",
        },
    }
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        if creationflags:
            popen_kwargs["creationflags"] = creationflags
    else:
        popen_kwargs["start_new_session"] = True
    try:
        _ACTIVE_PROCESS = subprocess.Popen(command, **popen_kwargs)
        try:
            output, _ = _ACTIVE_PROCESS.communicate(timeout=int(cfg.get("timeout_seconds") or 1200))
        except subprocess.TimeoutExpired:
            interrupted = True
            _terminate_process_tree(_ACTIVE_PROCESS)
            output, _ = _ACTIVE_PROCESS.communicate(timeout=30)
        return_code = _ACTIVE_PROCESS.returncode
    except KeyboardInterrupt:
        interrupted = True
        if _ACTIVE_PROCESS is not None:
            _terminate_process_tree(_ACTIVE_PROCESS)
    finally:
        _ACTIVE_PROCESS = None
    counts, failed_nodes = _parse_junit(junit_xml)
    if _STOP_REQUESTED:
        interrupted = True
    tail = "\n".join((output or "").splitlines()[-80:])
    return PhaseResult(
        name=name,
        command=command,
        return_code=return_code,
        duration_seconds=round(time.perf_counter() - start, 3),
        counts=counts,
        failed_node_ids=failed_nodes,
        output_tail=tail,
        junit_xml=str(junit_xml),
        interrupted=interrupted,
    )


def _track_from_phase(phase: PhaseResult) -> dict[str, Any]:
    classification = phase.classification
    reason = {
        "passed": "pytest_passed",
        "failed": "pytest_failed",
        "crashed": "pytest_crashed_or_interrupted",
        "skipped": "no_tests_collected_for_marker",
    }.get(classification, "unknown")
    return {
        "state": classification,
        "classification": classification,
        "classification_reason": reason,
        "actionable_context": (
            "Inspect pytest output and JUnit XML for failing tests."
            if classification in {"failed", "crashed"}
            else ""
        ),
        "log_file": phase.junit_xml,
        "return_code_hex": hex(phase.return_code) if isinstance(phase.return_code, int) else None,
        "return_code": phase.return_code,
        "passed_count": phase.counts.get("passed", 0),
        "failed_count": phase.counts.get("failed", 0),
        "error_count": phase.counts.get("errors", 0),
        "skipped_count": phase.counts.get("skipped", 0),
        "failed_node_ids": phase.failed_node_ids,
    }


def _aggregate(phases: list[PhaseResult]) -> dict[str, Any]:
    failed_nodes = sorted({node for phase in phases for node in phase.failed_node_ids})
    labels = [phase.classification for phase in phases]
    if "crashed" in labels:
        state = "crashed"
    elif "failed" in labels:
        state = "test_failures"
    else:
        state = "clean"
    by_name = {phase.name: phase for phase in phases}
    return {
        "state": state,
        "parallel": _track_from_phase(by_name.get("parallel", phases[0])),
        "no_parallel": _track_from_phase(by_name.get("no_parallel", phases[-1])),
        "failed_node_ids": failed_nodes,
    }


def _build_cache_metadata(
    suite_cache: Any,
    *,
    cache_mode: str,
    suite_profile: str,
    changed_domains: set[str] | None = None,
    test_files_to_run: int | None = None,
) -> dict[str, Any]:
    stats = suite_cache.get_cache_stats() if suite_cache else {}
    return {
        "cache_mode": cache_mode,
        "source": "run_test_suite",
        "suite_profile": suite_profile,
        "invalidation_reason": getattr(suite_cache, "last_invalidation_reason", None)
        or ("domain_cache" if cache_mode != "cold_scan" else "full_run"),
        "changed_domains": sorted(changed_domains or []),
        "test_files_to_run": test_files_to_run,
        "test_files_cached": stats.get("test_files_cached"),
        "has_full_suite_cache": stats.get("has_full_suite_cache"),
    }


def _aggregate_cached_phases(
    suite_cache: Any,
    junit_dir: Path,
    *,
    full_snapshot: dict[str, Any] | None = None,
    per_file_cached: dict[str, dict[str, Any]] | None = None,
) -> list[PhaseResult]:
    if full_snapshot:
        parallel = full_snapshot.get("parallel") or {}
        no_parallel = full_snapshot.get("no_parallel") or {}
        return [
            _phase_from_counts(
                name="parallel",
                counts=parallel.get("counts") or {},
                failed_node_ids=parallel.get("failed_node_ids") or [],
                junit_xml=str(junit_dir / "parallel.xml"),
                duration_seconds=float(full_snapshot.get("parallel_duration_seconds") or 0),
            ),
            _phase_from_counts(
                name="no_parallel",
                counts=no_parallel.get("counts") or {},
                failed_node_ids=no_parallel.get("failed_node_ids") or [],
                junit_xml=str(junit_dir / "no_parallel.xml"),
                duration_seconds=float(full_snapshot.get("no_parallel_duration_seconds") or 0),
            ),
        ]
    parallel_counts: dict[str, int] = {}
    no_parallel_counts: dict[str, int] = {}
    parallel_failed: list[str] = []
    no_parallel_failed: list[str] = []
    for data in (per_file_cached or {}).values():
        if not isinstance(data, dict):
            continue
        if isinstance(data.get("parallel"), dict):
            parallel_counts = _merge_counts(
                parallel_counts, data["parallel"].get("counts") or {}
            )
            parallel_failed.extend(data["parallel"].get("failed_node_ids") or [])
        if isinstance(data.get("no_parallel"), dict):
            no_parallel_counts = _merge_counts(
                no_parallel_counts, data["no_parallel"].get("counts") or {}
            )
            no_parallel_failed.extend(data["no_parallel"].get("failed_node_ids") or [])
    return [
        _phase_from_counts(
            name="parallel",
            counts=parallel_counts,
            failed_node_ids=parallel_failed,
            junit_xml=str(junit_dir / "parallel.xml"),
        ),
        _phase_from_counts(
            name="no_parallel",
            counts=no_parallel_counts,
            failed_node_ids=no_parallel_failed,
            junit_xml=str(junit_dir / "no_parallel.xml"),
        ),
    ]


def _failed_test_file_rels_from_phases(phases: list[PhaseResult]) -> set[str]:
    rels: set[str] = set()
    for phase in phases:
        for node in phase.failed_node_ids:
            file_part = node.split("::", 1)[0]
            if file_part:
                rels.add(file_part.replace("\\", "/"))
    return rels


def _phase_ok_for_run_status(
    phase: PhaseResult, *, allow_empty_no_parallel_skip: bool = False
) -> bool:
    """Whether a phase outcome should count as success for cache run status."""
    if phase.classification == "passed":
        return True
    return bool(
        allow_empty_no_parallel_skip
        and phase.name == "no_parallel"
        and phase.classification == "skipped"
    )


def _merge_phase_with_cache(
    phase: PhaseResult,
    cached_by_file: dict[str, dict[str, Any]],
    phase_key: str,
) -> PhaseResult:
    fresh_by_file = _parse_junit_by_test_file(Path(phase.junit_xml))
    merged_counts: dict[str, int] = {}
    merged_failed: list[str] = []
    seen_files = set(cached_by_file.keys()) | set(fresh_by_file.keys())
    for rel in sorted(seen_files):
        cached_entry = cached_by_file.get(rel, {})
        cached_phase = (
            cached_entry.get(phase_key) if isinstance(cached_entry, dict) else None
        )
        fresh_phase = fresh_by_file.get(rel)
        if isinstance(cached_phase, dict) and rel not in fresh_by_file:
            merged_counts = _merge_counts(merged_counts, cached_phase.get("counts") or {})
            merged_failed.extend(cached_phase.get("failed_node_ids") or [])
        elif isinstance(fresh_phase, dict):
            merged_counts = _merge_counts(merged_counts, fresh_phase.get("counts") or {})
            merged_failed.extend(fresh_phase.get("failed_node_ids") or [])
    return _phase_from_counts(
        name=phase.name,
        counts=merged_counts,
        failed_node_ids=merged_failed,
        junit_xml=phase.junit_xml,
        duration_seconds=phase.duration_seconds,
        return_code=phase.return_code or 0,
    )


def run_suite(cfg: dict[str, Any], *, use_domain_cache: bool = True) -> dict[str, Any]:
    global _SIGINT_CFG
    _SIGINT_CFG = cfg
    previous_handler = signal.getsignal(signal.SIGINT) if hasattr(signal, "SIGINT") else None
    if hasattr(signal, "SIGINT"):
        signal.signal(signal.SIGINT, _handle_sigint)
    junit_dir = Path(str(cfg.get("junit_dir") or DEFAULT_TEST_RUN["junit_dir"]))
    if not junit_dir.is_absolute():
        junit_dir = Path.cwd() / junit_dir
    junit_dir.mkdir(parents=True, exist_ok=True)

    suite_cache = None
    changed_domains: set[str] = set()
    test_files_to_run: list[Path] = []
    cache_mode = "cold_scan"
    suite_profile = str(cfg.get("suite_profile") or cfg.get("default_profile") or "quick")
    if use_domain_cache:
        try:
            from development_tools.tests.test_file_suite_cache import TestFileSuiteCache

            suite_cache = TestFileSuiteCache(Path.cwd())
            changed_domains = suite_cache.get_changed_domains(suite_profile)
            test_files_to_run = suite_cache.get_test_files_to_run(changed_domains)
            if _suite_logger:
                _suite_logger.info(
                    "run_test_suite domain cache: invalidation=%s changed_domains=%s "
                    "files_to_run=%s has_full_snapshot=%s",
                    getattr(suite_cache, "last_invalidation_reason", None)
                    or getattr(suite_cache.coverage_cache, "last_invalidation_reason", None),
                    sorted(changed_domains),
                    len(test_files_to_run),
                    suite_cache.get_full_suite_cache() is not None,
                )
        except Exception:
            suite_cache = None
            use_domain_cache = False

    phases: list[PhaseResult] = []
    cache_metadata: dict[str, Any] = {}
    try:
        run_pytest = True
        test_filter_paths: list[str] | None = None
        cached_per_file: dict[str, dict[str, Any]] = {}
        full_snapshot = None
        if use_domain_cache and suite_cache:
            full_snapshot = suite_cache.get_full_suite_cache()
            cached_per_file = suite_cache.get_all_cached_suite_results(
                exclude_domains=changed_domains
            )
            if (
                not test_files_to_run
                and suite_cache.can_reuse_full_suite_cache(suite_profile)
            ):
                run_pytest = False
                cache_mode = "cache_hit"
                if _suite_logger:
                    _suite_logger.info(
                        "run_test_suite using cache only (no pytest): snapshot=%s cached_files=%s",
                        True,
                        len(cached_per_file),
                    )
                phases = _aggregate_cached_phases(
                    suite_cache,
                    junit_dir,
                    full_snapshot=full_snapshot,
                    per_file_cached=cached_per_file,
                )
            elif (
                not test_files_to_run
                and cached_per_file
                and suite_cache.can_reuse_full_suite_cache(suite_profile)
            ):
                run_pytest = False
                cache_mode = "cache_hit"
                if _suite_logger:
                    _suite_logger.info(
                        "run_test_suite using per-file cache only (no pytest): cached_files=%s",
                        len(cached_per_file),
                    )
                phases = _aggregate_cached_phases(
                    suite_cache,
                    junit_dir,
                    full_snapshot=None,
                    per_file_cached=cached_per_file,
                )
            elif test_files_to_run:
                cache_mode = "selective_run"
                test_filter_paths = [
                    str(tf.relative_to(Path.cwd())) for tf in test_files_to_run
                ]
            else:
                cache_mode = "full_run"

        if run_pytest:
            force_serial = not _has_xdist()
            parallel_phase = _run_phase(
                "parallel",
                cfg,
                junit_dir,
                force_serial=force_serial,
                test_paths=test_filter_paths,
            )
            if (
                not force_serial
                and parallel_phase.classification in {"crashed", "failed"}
                and _is_xdist_teardown_interrupt_output(parallel_phase.output_tail)
            ):
                retry_phase = _run_phase(
                    "parallel",
                    cfg,
                    junit_dir,
                    force_serial=True,
                    test_paths=test_filter_paths,
                )
                retry_phase.output_tail = (
                    "[RETRY] Parallel pytest hit xdist/execnet teardown interrupt; "
                    "reran phase serially.\n"
                    f"[XDIST OUTPUT TAIL]\n{parallel_phase.output_tail}\n"
                    f"[SERIAL OUTPUT TAIL]\n{retry_phase.output_tail}"
                )
                parallel_phase = retry_phase
            if use_domain_cache and suite_cache and test_filter_paths and cached_per_file:
                parallel_phase = _merge_phase_with_cache(
                    parallel_phase, cached_per_file, "parallel"
                )
            phases.append(parallel_phase)
            if not _STOP_REQUESTED:
                no_parallel_phase = _run_phase(
                    "no_parallel",
                    cfg,
                    junit_dir,
                    force_serial=True,
                    test_paths=test_filter_paths,
                )
                if use_domain_cache and suite_cache and test_filter_paths and cached_per_file:
                    no_parallel_phase = _merge_phase_with_cache(
                        no_parallel_phase, cached_per_file, "no_parallel"
                    )
                phases.append(no_parallel_phase)

            if use_domain_cache and suite_cache and not _STOP_REQUESTED:
                parallel_by_file = _parse_junit_by_test_file(Path(parallel_phase.junit_xml))
                no_parallel_by_file = (
                    _parse_junit_by_test_file(Path(phases[-1].junit_xml))
                    if len(phases) > 1
                    else {}
                )
                normalize_rel = (
                    TestFileCoverageCache._normalize_test_file_rel
                    if TestFileCoverageCache is not None
                    else lambda p: p.replace("\\", "/")
                )
                files_to_update = (
                    {
                        normalize_rel(str(p.relative_to(Path.cwd())))
                        for p in test_files_to_run
                    }
                    if test_files_to_run
                    else set(parallel_by_file) | set(no_parallel_by_file)
                )
                for rel in files_to_update:
                    test_path = Path.cwd() / rel
                    if not test_path.exists():
                        continue
                    suite_cache.cache_test_file_suite(
                        test_path,
                        parallel=parallel_by_file.get(rel),
                        no_parallel=no_parallel_by_file.get(rel),
                    )
                outcome_preview = _aggregate(phases)
                allow_np_skip = bool(test_filter_paths)
                parallel_ok = _phase_ok_for_run_status(phases[0])
                no_parallel_ok = (
                    _phase_ok_for_run_status(
                        phases[1], allow_empty_no_parallel_skip=allow_np_skip
                    )
                    if len(phases) > 1
                    else None
                )
                failed_domains: set[str] = set()
                run_domains: set[str] = set()
                for rel in files_to_update:
                    test_path = Path.cwd() / rel
                    if not test_path.exists():
                        continue
                    run_domains.update(
                        suite_cache.coverage_cache.get_test_files_domains(test_path)
                    )
                if outcome_preview["state"] != "clean":
                    for rel in _failed_test_file_rels_from_phases(phases):
                        test_path = Path.cwd() / rel
                        if test_path.exists():
                            failed_domains.update(
                                suite_cache.coverage_cache.get_test_files_domains(
                                    test_path
                                )
                            )
                np_present = len(phases) <= 1 or phases[1].classification != "crashed"
                suite_cache.update_run_status(
                    parallel_ok=parallel_ok,
                    no_parallel_ok=no_parallel_ok,
                    no_parallel_coverage_present=np_present,
                    failed_domains=failed_domains,
                    run_domains=(
                        run_domains
                        or changed_domains
                        or suite_cache._all_domains()
                    ),
                    suite_profile=suite_profile,
                )
                if outcome_preview["state"] == "clean":
                    suite_cache.cache_full_suite(
                        {
                            "parallel": {
                                "counts": phases[0].counts,
                                "failed_node_ids": phases[0].failed_node_ids,
                            },
                            "no_parallel": {
                                "counts": phases[-1].counts,
                                "failed_node_ids": phases[-1].failed_node_ids,
                            },
                            "parallel_duration_seconds": phases[0].duration_seconds,
                            "no_parallel_duration_seconds": phases[-1].duration_seconds,
                        }
                    )
                    if _suite_logger:
                        _suite_logger.info(
                            "run_test_suite cached full suite snapshot (mode=%s)",
                            cache_mode,
                        )
                else:
                    suite_cache.clear_full_suite_cache()
                    if _suite_logger:
                        _suite_logger.info(
                            "run_test_suite cleared full suite snapshot after state=%s",
                            outcome_preview["state"],
                        )
    finally:
        if hasattr(signal, "SIGINT") and previous_handler is not None:
            signal.signal(signal.SIGINT, previous_handler)

    if not cache_metadata and suite_cache:
        cache_metadata = _build_cache_metadata(
            suite_cache,
            cache_mode=cache_mode,
            suite_profile=suite_profile,
            changed_domains=changed_domains,
            test_files_to_run=len(test_files_to_run),
        )
    elif not cache_metadata:
        cache_metadata = {
            "cache_mode": "disabled",
            "source": "run_test_suite",
            "suite_profile": suite_profile,
            "invalidation_reason": "domain_cache_disabled",
        }

    outcome = _aggregate(phases)
    outcome["suite_profile"] = suite_profile
    return {
        "tool_name": "run_test_suite",
        "summary": {
            "total_issues": len(outcome.get("failed_node_ids", [])),
            "files_affected": 0,
            "status": "PASS" if outcome["state"] == "clean" else "FAIL",
        },
        "details": {
            "tier3_test_outcome": outcome,
            "phases": [
                {
                    "name": phase.name,
                    "command": phase.command,
                    "return_code": phase.return_code,
                    "duration_seconds": phase.duration_seconds,
                    "counts": phase.counts,
                    "classification": phase.classification,
                    "failed_node_ids": phase.failed_node_ids,
                    "junit_xml": phase.junit_xml,
                    "output_tail": phase.output_tail,
                }
                for phase in phases
            ],
            "xdist_available": _has_xdist(),
            "domain_cache": cache_metadata,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run pytest suite without coverage for Tier 3 audits.")
    parser.add_argument("--output-file", default=None)
    parser.add_argument("--workers", default=None)
    parser.add_argument("--timeout", type=int, default=None)
    parser.add_argument(
        "--profile",
        choices=["quick", "full"],
        default="quick",
        help="quick: exclude e2e and slow (Tier 3 default); full: exclude e2e only (nightly).",
    )
    parser.add_argument(
        "--no-domain-cache",
        action="store_true",
        help="Disable domain-based test selection and suite result caching (runs all tests).",
    )
    args = parser.parse_args(argv)
    cfg = _load_config(args.profile)
    if args.workers:
        cfg["workers"] = args.workers
    if args.timeout:
        cfg["timeout_seconds"] = args.timeout
    payload = run_suite(cfg, use_domain_cache=not args.no_domain_cache)
    output = json.dumps(payload, indent=2)
    state = payload["details"]["tier3_test_outcome"]["state"]
    if args.output_file:
        out = Path(args.output_file)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output, encoding="utf-8")
        # Keep stdout small when invoked via run_script(capture_output=True).
        print(
            f"run_test_suite profile={args.profile} state={state} "
            f"issues={payload.get('summary', {}).get('total_issues', 0)} "
            f"output={out.as_posix()}"
        )
    else:
        print(output)
    return 0 if state == "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
