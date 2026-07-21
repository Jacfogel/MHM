"""Pure Tier 3 outcome helpers extracted from ReportGenerationMixin (V6 B-015).

No legacy shim: call sites import these functions (or thin mixin wrappers that
delegate here). Prefer this module for new tests.
"""

from __future__ import annotations

from typing import Any


def coerce_int(value: Any, default: int = 0) -> int:
    """Best-effort int coercion for report metrics."""
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_test_node_id(node_id: str) -> str:
    """Normalize pytest node IDs for compact display (drop class segment)."""
    text = str(node_id or "").strip()
    if not text:
        return ""
    parts = text.split("::")
    if len(parts) >= 3:
        return f"{parts[0]}::{parts[-1]}"
    return text


def track_classification_label(outcome: dict[str, Any]) -> str:
    """Return the normalized track classification label."""
    if not isinstance(outcome, dict):
        return "unknown"
    classification = outcome.get("classification")
    if isinstance(classification, str) and classification.strip():
        return classification.strip()
    return "unknown"


def tier3_track_skipped_for_audit_scope(track: dict[str, Any]) -> bool:
    """True when Tier 3 split intentionally did not run this track."""
    if not isinstance(track, dict):
        return False
    return track.get("classification_reason") == "not_run_this_audit_scope"


def tier3_outcome_has_run_evidence(outcome: dict[str, Any]) -> bool:
    """True when outcome reflects a Tier 3 test run (not empty/stale cache)."""
    if not isinstance(outcome, dict) or not outcome:
        return False
    state = outcome.get("state")
    if isinstance(state, str) and state.strip() and state.strip() != "unknown":
        return True
    for key in ("parallel", "no_parallel", "development_tools"):
        track = outcome.get(key)
        if not isinstance(track, dict) or not track:
            continue
        if track.get("classification_reason") == "not_run_this_audit_scope":
            return True
        classification = track_classification_label(track)
        if classification not in {"", "unknown"}:
            return True
        for field in (
            "return_code",
            "passed_count",
            "failed_count",
            "error_count",
            "log_file",
        ):
            value = track.get(field)
            if value not in (None, 0, "", []):
                return True
    return False


def effective_tier3_state_from_outcome(outcome: dict[str, Any]) -> str:
    """Return effective Tier 3 state including development-tools test outcome."""
    state = outcome.get("state", "") if isinstance(outcome, dict) else ""

    if state in {"clean", "test_failures", "crashed", "infra_cleanup_error"}:
        return state
    if not isinstance(outcome, dict):
        return "unknown"
    if not tier3_outcome_has_run_evidence(outcome):
        return "unknown"
    parallel = (
        outcome.get("parallel", {}) if isinstance(outcome.get("parallel"), dict) else {}
    )
    no_parallel = (
        outcome.get("no_parallel", {})
        if isinstance(outcome.get("no_parallel"), dict)
        else {}
    )
    dev_tools = (
        outcome.get("development_tools", {})
        if isinstance(outcome.get("development_tools"), dict)
        else {}
    )
    track_labels = (
        track_classification_label(parallel),
        track_classification_label(no_parallel),
        track_classification_label(dev_tools),
    )
    if "infra_cleanup_error" in track_labels:
        return "infra_cleanup_error"
    if "crashed" in track_labels:
        return "crashed"
    if "failed" in track_labels:
        return "test_failures"
    if any(label in {"passed", "skipped"} for label in track_labels):
        return "clean"
    if any(label == "unknown" for label in track_labels):
        return "unknown"
    return "unknown"
