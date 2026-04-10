"""
Detect flaky pytest cases by repeated parallel runs.

This is a tracked migration of the historical scripts/flaky_detector.py utility.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logger import get_component_logger


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUN_LOG_DIR = PROJECT_ROOT / "development_tools" / "tests" / "logs" / "flaky_detector_runs"
DEFAULT_PROGRESS_FILE = (
    PROJECT_ROOT / "development_tools" / "tests" / "logs" / "flaky_detector_progress.json"
)
DEFAULT_REPORT_FILE = (
    PROJECT_ROOT / "development_tools" / "tests" / "logs" / "flaky_test_report.md"
)
logger = get_component_logger("development_tools")


def extract_failed_tests(stdout_text: str, stderr_text: str) -> set[str]:
    """Extract unique failing pytest nodeids from one test run."""
    combined = f"{stdout_text}\n{stderr_text}"
    failed: set[str] = set()
    summary_pattern = re.compile(r"^(?:FAILED|ERROR)\s+((?:tests)[^\s]+::[^\s]+)")
    inline_pattern = re.compile(r"^((?:tests)[^\s]+::[^\s]+)\s+(?:FAILED|ERROR)\b")

    for raw_line in combined.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = summary_pattern.match(line)
        if match:
            failed.add(match.group(1))
            continue
        match = inline_pattern.match(line)
        if match:
            failed.add(match.group(1))
    return failed


def analyze_results(failures: dict[str, list[int]], num_runs: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Classify intermittent and consistent failures."""
    flaky_tests: list[dict[str, Any]] = []
    consistently_failing: list[dict[str, Any]] = []

    for test_name, failure_runs in failures.items():
        unique_runs = sorted(set(failure_runs))
        failure_count = len(unique_runs)
        if failure_count == 0:
            continue
        entry: dict[str, Any] = {
            "test": test_name,
            "failures": failure_count,
            "total": num_runs,
            "failure_rate": (failure_count / num_runs) * 100,
            "failure_runs": unique_runs,
            "classification": "stable",
        }
        if failure_count < num_runs:
            entry["classification"] = "flaky"
            flaky_tests.append(entry)
        else:
            consistently_failing.append(entry)

    flaky_tests.sort(key=lambda x: x["failure_rate"], reverse=True)
    consistently_failing.sort(key=lambda x: x["test"])
    return flaky_tests, consistently_failing


def _save_progress(
    failures: dict[str, list[int]],
    run_num: int,
    total_runs: int,
    progress_path: Path,
) -> None:
    payload = {
        "run_num": run_num,
        "total_runs": total_runs,
        "failures": failures,
        "timestamp": datetime.now().isoformat(),
    }
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_progress(progress_path: Path) -> tuple[dict[str, list[int]], int, int]:
    if not progress_path.exists():
        return {}, 0, 0
    try:
        data = json.loads(progress_path.read_text(encoding="utf-8"))
        return dict(data.get("failures", {})), int(data.get("run_num", 0)), int(data.get("total_runs", 0))
    except Exception:
        return {}, 0, 0


def _write_report(
    output_file: Path,
    flaky_tests: list[dict[str, Any]],
    consistently_failing: list[dict[str, Any]],
    num_runs: int,
    run_records: list[dict[str, Any]],
) -> None:
    lines = [
        "# Flaky Test Detection Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Test runs: {num_runs}",
        "",
    ]
    if flaky_tests:
        lines.extend(["## Flaky Tests", ""])
        for test in flaky_tests:
            lines.extend(
                [
                    f"### {test['test']}",
                    f"- Failure rate: {test['failure_rate']:.1f}% ({test['failures']}/{test['total']})",
                    f"- Failed in runs: {test['failure_runs']}",
                    "",
                ]
            )
    else:
        lines.extend(["## Flaky Tests", "", "No intermittent failures detected.", ""])

    if consistently_failing:
        lines.extend(["## Consistently Failing", ""])
        for test in consistently_failing:
            lines.append(f"- `{test['test']}`")
        lines.append("")

    lines.extend(
        [
            "## Per-Run Summary",
            "",
            "| Run | Duration (s) | Return Code | Parsed Failures |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for record in run_records:
        lines.append(
            f"| {record['run']} | {record['duration_seconds']:.2f} | {record['return_code']} | {record['parsed_failures']} |"
        )
    lines.append("")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines), encoding="utf-8")


def run_detector(
    *,
    runs: int,
    workers: str,
    test_paths: list[str],
    progress_file: Path,
    output_file: Path,
    include_e2e: bool,
    timeout_seconds: int,
) -> dict[str, Any]:
    failures: dict[str, list[int]] = defaultdict(list)
    run_records: list[dict[str, Any]] = []
    saved_failures, start_run, saved_total = _load_progress(progress_file)
    if saved_total == runs and start_run > 0:
        failures.update(saved_failures)
        next_run = start_run + 1
    else:
        next_run = 1

    marker_filter = "not no_parallel" if include_e2e else "not no_parallel and not e2e"
    RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)

    for run_num in range(next_run, runs + 1):
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            *test_paths,
            "-n",
            str(workers),
            "-m",
            marker_filter,
            "--tb=no",
            "-q",
            "--maxfail=100",
        ]
        start = time.perf_counter()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            logger.warning(
                f"flaky_detector: pytest subprocess timed out (run {run_num}/{runs}, "
                f"{timeout_seconds}s): {exc}"
            )
            return {
                "summary": {
                    "total_issues": 1,
                    "files_affected": 0,
                    "status": "FAIL",
                },
                "details": {
                    "error": (
                        f"pytest run {run_num}/{runs} timed out after {timeout_seconds}s "
                        "(increase --timeout-seconds or narrow --test-path)"
                    ),
                    "timed_out_run": run_num,
                    "timeout_seconds": timeout_seconds,
                    "command": cmd,
                },
            }
        stdout_text = result.stdout or ""
        stderr_text = result.stderr or ""

        stdout_path = RUN_LOG_DIR / f"run_{run_num:02d}_stdout.log"
        stderr_path = RUN_LOG_DIR / f"run_{run_num:02d}_stderr.log"
        stdout_path.write_text(stdout_text, encoding="utf-8")
        stderr_path.write_text(stderr_text, encoding="utf-8")

        failed_this_run = extract_failed_tests(stdout_text, stderr_text)
        for nodeid in failed_this_run:
            failures.setdefault(nodeid, []).append(run_num)

        run_records.append(
            {
                "run": run_num,
                "duration_seconds": round(time.perf_counter() - start, 2),
                "return_code": result.returncode,
                "parsed_failures": len(failed_this_run),
            }
        )
        _save_progress(dict(failures), run_num, runs, progress_file)

    if progress_file.exists():
        progress_file.unlink()

    flaky_tests, consistently_failing = analyze_results(dict(failures), runs)
    _write_report(output_file, flaky_tests, consistently_failing, runs, run_records)

    files_affected = set()
    for test in flaky_tests + consistently_failing:
        nodeid = str(test.get("test", ""))
        file_part = nodeid.split("::", 1)[0]
        if file_part:
            files_affected.add(file_part)

    details = {
        "flaky_count": len(flaky_tests),
        "consistent_fail_count": len(consistently_failing),
        "flaky_tests": flaky_tests,
        "consistently_failing_tests": consistently_failing,
        "runs": runs,
        "workers": workers,
        "test_paths": test_paths,
        "report_path": output_file.relative_to(PROJECT_ROOT).as_posix(),
    }
    return {
        "summary": {
            "total_issues": len(flaky_tests) + len(consistently_failing),
            "files_affected": len(files_affected),
            "status": "WARN" if flaky_tests or consistently_failing else "PASS",
        },
        "details": details,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect flaky tests by repeated parallel runs.")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--workers", type=str, default="auto")
    parser.add_argument("--test-path", nargs="+", default=["tests/"])
    parser.add_argument("--output", type=str, default=str(DEFAULT_REPORT_FILE.relative_to(PROJECT_ROOT)))
    parser.add_argument("--progress-file", type=str, default=str(DEFAULT_PROGRESS_FILE.relative_to(PROJECT_ROOT)))
    parser.add_argument("--include-e2e", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--json", action="store_true", help="Emit standard {summary, details} JSON.")
    args = parser.parse_args(argv)

    output_file = (PROJECT_ROOT / args.output).resolve()
    progress_file = (PROJECT_ROOT / args.progress_file).resolve()
    try:
        result = run_detector(
            runs=args.runs,
            workers=args.workers,
            test_paths=args.test_path,
            progress_file=progress_file,
            output_file=output_file,
            include_e2e=args.include_e2e,
            timeout_seconds=args.timeout_seconds,
        )
    except Exception as exc:
        logger.error(f"flaky_detector failed: {exc}", exc_info=True)
        if args.json:
            print(
                json.dumps(
                    {
                        "summary": {
                            "total_issues": 0,
                            "files_affected": 0,
                            "status": "FAIL",
                        },
                        "details": {"error": str(exc)},
                    },
                    indent=2,
                )
            )
            return 1
        raise

    if args.json:
        print(json.dumps(result, indent=2))
        status = str(result.get("summary", {}).get("status", "")).upper()
        return 1 if status == "FAIL" else 0

    details = result.get("details", {})
    print(f"Flaky tests: {details.get('flaky_count', 0)}")
    print(f"Consistently failing tests: {details.get('consistent_fail_count', 0)}")
    print(f"Report: {details.get('report_path', output_file.relative_to(PROJECT_ROOT).as_posix())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

