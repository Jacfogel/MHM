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
    "exclude_markers": ["e2e"],
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


def _load_config() -> dict[str, Any]:
    try:
        from development_tools import config

        cfg = config.get_external_value("test_run", None)
        paths = config.get_paths_config()
    except Exception:
        cfg = None
        paths = {"tests_dir": "tests"}

    result = dict(DEFAULT_TEST_RUN)
    if isinstance(cfg, dict):
        result.update(cfg)
    if not result.get("test_paths"):
        tests_dir = str(paths.get("tests_dir", "tests")).strip().rstrip("/\\") or "tests"
        result["test_paths"] = [tests_dir]
    return result


def _has_xdist() -> bool:
    return importlib.util.find_spec("xdist") is not None


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
) -> list[str]:
    command = _pytest_command(cfg)
    command.extend(str(part) for part in (cfg.get("pytest_base_args") or []))
    command.extend(["--junitxml", str(junit_xml)])
    include_no_parallel = phase == "no_parallel"
    command.extend(["-m", _marker_expression(include_no_parallel=include_no_parallel, cfg=cfg)])
    if phase == "parallel" and not force_serial and _has_xdist():
        workers = str(cfg.get("workers") or "auto").strip()
        if workers and workers.lower() != "none":
            command.extend(["-n", workers])
    command.extend(str(path) for path in (cfg.get("test_paths") or ["tests"]))
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


def _run_phase(name: str, cfg: dict[str, Any], junit_dir: Path, *, force_serial: bool = False) -> PhaseResult:
    global _ACTIVE_PROCESS
    junit_xml = junit_dir / f"{name}.xml"
    with contextlib.suppress(OSError):
        junit_xml.unlink()
    command = build_phase_command(phase=name, cfg=cfg, junit_xml=junit_xml, force_serial=force_serial)
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


def run_suite(cfg: dict[str, Any]) -> dict[str, Any]:
    global _SIGINT_CFG
    _SIGINT_CFG = cfg
    previous_handler = signal.getsignal(signal.SIGINT) if hasattr(signal, "SIGINT") else None
    if hasattr(signal, "SIGINT"):
        signal.signal(signal.SIGINT, _handle_sigint)
    junit_dir = Path(str(cfg.get("junit_dir") or DEFAULT_TEST_RUN["junit_dir"]))
    if not junit_dir.is_absolute():
        junit_dir = Path.cwd() / junit_dir
    junit_dir.mkdir(parents=True, exist_ok=True)
    phases: list[PhaseResult] = []
    try:
        force_serial = not _has_xdist()
        phases.append(_run_phase("parallel", cfg, junit_dir, force_serial=force_serial))
        if not _STOP_REQUESTED:
            phases.append(_run_phase("no_parallel", cfg, junit_dir, force_serial=True))
    finally:
        if hasattr(signal, "SIGINT") and previous_handler is not None:
            signal.signal(signal.SIGINT, previous_handler)
    outcome = _aggregate(phases)
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
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run pytest suite without coverage for Tier 3 audits.")
    parser.add_argument("--output-file", default=None)
    parser.add_argument("--workers", default=None)
    parser.add_argument("--timeout", type=int, default=None)
    args = parser.parse_args(argv)
    cfg = _load_config()
    if args.workers:
        cfg["workers"] = args.workers
    if args.timeout:
        cfg["timeout_seconds"] = args.timeout
    payload = run_suite(cfg)
    output = json.dumps(payload, indent=2)
    if args.output_file:
        out = Path(args.output_file)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output, encoding="utf-8")
    print(output)
    state = payload["details"]["tier3_test_outcome"]["state"]
    return 0 if state == "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
