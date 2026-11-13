"""Pure Tier 3 coverage/test outcome classification helpers (V6 B-015).

Extracted from ``run_test_coverage.CoverageMetricsRegenerator`` so return-code
and track-outcome logic can be tested without the full regenerator graph.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_WINDOWS_CRASH_CODES = {3221226505, 3221225477}
_INTERRUPT_RETURN_CODES = {130, 3221225786}
_CANONICAL_RETURN_CODE_HEX = {
    3221226505: "0xC0000135",
    3221225477: "0xC0000005",
    3221225786: "0xC000013A",
}
_XDIST_CRASH_MARKERS = (
    "windows fatal exception",
    "node down: not properly terminated",
    "execnet.gateway_base",
    "pluggyteardownraisedwarning",
    "oserror: cannot send (already closed?)",
)


def strip_xdist_args(cmd: list[str]) -> list[str]:
    """Return command list without xdist-specific arguments."""
    stripped: list[str] = []
    skip_next = False
    for arg in cmd:
        if skip_next:
            skip_next = False
            continue
        if arg in {"-n", "--numprocesses", "--dist"}:
            skip_next = True
            continue
        if arg.startswith("--dist="):
            continue
        stripped.append(arg)
    return stripped


def is_windows_crash_return_code(return_code: int | None) -> bool:
    """Check whether return code matches a known Windows crash code."""
    if return_code is None:
        return False
    return return_code in _WINDOWS_CRASH_CODES


def is_interrupt_return_code(return_code: int | None) -> bool:
    """Check whether return code indicates interrupt/control-event termination."""
    if return_code is None:
        return False
    # 130 is standard SIGINT-style shell exit.
    # 0xC000013A (3221225786) is Windows STATUS_CONTROL_C_EXIT.
    return return_code in _INTERRUPT_RETURN_CODES


def format_return_code_hex(return_code: int | None) -> str | None:
    """Return normalized hex code string for process return codes."""
    if return_code is None:
        return None
    if return_code in _CANONICAL_RETURN_CODE_HEX:
        return _CANONICAL_RETURN_CODE_HEX[return_code]
    try:
        return f"0x{(int(return_code) & 0xFFFFFFFF):08X}"
    except (TypeError, ValueError):
        return None


def classify_windows_crash_return_code(
    return_code: int | None,
) -> tuple[str | None, str | None]:
    """Return crash reason and actionable context for known Windows return codes."""
    if return_code == 3221226505:
        return (
            "windows_status_dll_not_found",
            "Missing DLL or PATH issue in Python/runtime dependencies. Verify Python install and dependency DLL availability.",
        )
    if return_code == 3221225477:
        return (
            "windows_status_access_violation",
            "Process access violation likely from native/library interaction. Review UI/native deps and threading-sensitive tests.",
        )
    return None, None


def is_infra_cleanup_error(output: str) -> bool:
    """Detect pytest teardown cleanup errors that are infra failures, not test failures."""
    if not output:
        return False
    lowered = output.lower()
    return "cleanup_dead_symlinks" in lowered and "permissionerror" in lowered


def is_xdist_worker_crash_output(output: str) -> bool:
    """Detect xdist/execnet worker crash patterns from pytest output."""
    if not output:
        return False
    lowered = output.lower()
    return any(marker in lowered for marker in _XDIST_CRASH_MARKERS)


def build_track_outcome(
    return_code: int | None,
    parsed_results: dict[str, Any],
    output: str,
    track_name: str = "track",
    log_file: Path | None = None,
) -> dict[str, Any]:
    """Build normalized per-track outcome details for report generation."""
    failed_tests = list(parsed_results.get("failed_tests", []))
    error_tests = list(parsed_results.get("error_tests", []))
    failed_node_ids = failed_tests + error_tests
    total_tests = int(parsed_results.get("total_tests", 0) or 0)
    failed_count = int(parsed_results.get("failed_count", 0) or 0)
    error_count = int(parsed_results.get("error_count", 0) or 0)
    passed_count = int(parsed_results.get("passed_count", 0) or 0)
    skipped_count = int(parsed_results.get("skipped_count", 0) or 0)
    deselected_count = int(parsed_results.get("deselected_count", 0) or 0)
    return_code_hex = format_return_code_hex(return_code)
    normalized_log_file = str(log_file).replace("\\", "/") if log_file else None

    state = "unknown"
    classification = "unknown"
    classification_reason = "unknown"
    actionable_context = "Review pytest stdout log for this track."
    if is_infra_cleanup_error(output):
        state = "infra_cleanup_error"
        classification = "infra_cleanup_error"
        classification_reason = "cleanup_dead_symlinks_permission_error"
        actionable_context = (
            "Pytest teardown cleanup permission issue detected. "
            "Review temp-dir cleanup permissions and retry."
        )
    elif is_interrupt_return_code(return_code):
        state = "crashed"
        classification = "crashed"
        classification_reason = "interrupt_signal"
        actionable_context = (
            "Subprocess terminated by interrupt/control event (SIGINT/CTRL+C). "
            "This is not always a direct user Ctrl+C; inspect terminal/host signal propagation."
        )
    elif is_xdist_worker_crash_output(output):
        state = "crashed"
        classification = "crashed"
        classification_reason = "xdist_worker_crash_output"
        actionable_context = (
            "xdist worker crash markers detected in pytest output. "
            "Inspect worker crash details in track log."
        )
    elif is_windows_crash_return_code(return_code):
        state = "crashed"
        classification = "crashed"
        crash_reason, crash_context = classify_windows_crash_return_code(return_code)
        classification_reason = crash_reason or "windows_crash_return_code"
        actionable_context = crash_context or actionable_context
    elif return_code is None and total_tests == 0 and not (output or "").strip():
        state = "skipped"
        classification = "skipped"
        classification_reason = "no_output_no_return_code"
        actionable_context = (
            f"{track_name} produced no return code and no parsed output "
            "(likely intentionally skipped)."
        )
    elif (
        track_name == "no_parallel"
        and return_code == 5
        and total_tests == 0
        and not failed_node_ids
    ):
        state = "skipped"
        classification = "skipped"
        classification_reason = "zero_no_parallel_tests_collected"
        actionable_context = "No no_parallel tests matched this scoped run."
    elif return_code not in (0, None) and total_tests == 0 and not failed_node_ids:
        state = "crashed"
        classification = "crashed"
        classification_reason = "nonzero_without_tests"
        actionable_context = (
            "Non-zero exit with zero parsed tests indicates subprocess "
            "crash/infra issue before pytest summary."
        )
    elif failed_count > 0 or error_count > 0 or failed_node_ids:
        state = "failed"
        classification = "failed"
        classification_reason = "pytest_failed_or_errored"
        actionable_context = (
            "One or more pytest node IDs failed/errored. Fix failing tests and rerun."
        )
    elif return_code == 0 and total_tests > 0:
        state = "passed"
        classification = "passed"
        classification_reason = "pytest_passed"
        actionable_context = "Track completed successfully."
    elif return_code == 0 and total_tests == 0:
        state = "skipped"
        classification = "skipped"
        classification_reason = "zero_tests_collected"
        actionable_context = "Track completed with zero collected tests."
    elif return_code is None:
        state = "crashed"
        classification = "crashed"
        classification_reason = "missing_return_code"
        actionable_context = "Subprocess did not return a valid exit code."

    return {
        "state": state,
        "classification": classification,
        "classification_reason": classification_reason,
        "actionable_context": actionable_context,
        "log_file": normalized_log_file,
        "return_code_hex": return_code_hex,
        "return_code": return_code,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "error_count": error_count,
        "skipped_count": skipped_count,
        "deselected_count": deselected_count,
        "failed_node_ids": failed_node_ids,
    }


def classify_coverage_outcome(
    parallel: dict[str, Any],
    no_parallel: dict[str, Any],
    coverage_collected: bool,
) -> str:
    """Compute aggregate coverage/test outcome state for Tier 3 reporting."""
    if not coverage_collected:
        return "coverage_failed"
    states = [
        parallel.get("classification", parallel.get("state")),
        no_parallel.get("classification", no_parallel.get("state")),
    ]
    if "infra_cleanup_error" in states:
        return "infra_cleanup_error"
    if "crashed" in states:
        return "crashed"
    if "failed" in states:
        return "test_failures"
    return "clean"


def build_cache_only_coverage_outcome(coverage_collected: bool) -> dict[str, Any]:
    """Build canonical Tier 3 outcome metadata for cache-only coverage runs."""
    track_state = "skipped" if coverage_collected else "failed"
    track_classification = "skipped" if coverage_collected else "failed"
    track_reason = (
        "cache_only" if coverage_collected else "cache_only_coverage_unavailable"
    )
    track_context = (
        "Pytest execution skipped because full coverage data was restored from cache."
        if coverage_collected
        else "Pytest execution skipped but no cached coverage data was available."
    )
    track = {
        "state": track_state,
        "classification": track_classification,
        "classification_reason": track_reason,
        "actionable_context": track_context,
        "log_file": None,
        "return_code_hex": None,
        "return_code": None,
        "passed_count": 0,
        "failed_count": 0,
        "error_count": 0,
        "skipped_count": 0,
        "deselected_count": 0,
        "failed_node_ids": [],
    }
    return {
        "state": classify_coverage_outcome(track, track, coverage_collected),
        "parallel": dict(track),
        "no_parallel": dict(track),
        "failed_node_ids": [],
    }
