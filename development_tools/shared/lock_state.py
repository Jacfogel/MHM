"""Shared lock-file state helpers for development tools orchestration."""

from __future__ import annotations

import json
import os
import socket
import sys
import time
from pathlib import Path
from typing import Any
from collections.abc import Iterable

LOCK_VERSION = 1


def write_lock_metadata(
    path: Path, lock_type: str, stale_after_seconds: int = 5400
) -> bool:
    """Write lock metadata JSON to disk."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": LOCK_VERSION,
            "lock_type": str(lock_type),
            "pid": os.getpid(),
            "ppid": os.getppid(),
            "created_at": time.time(),
            "stale_after_seconds": int(stale_after_seconds),
            "host": socket.gethostname(),
            "command": " ".join(sys.argv),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def read_lock_metadata(path: Path) -> dict[str, Any] | None:
    """Read lock metadata, returning None for missing or invalid payloads."""
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def is_pid_alive(pid: Any) -> bool:
    """Return True when process appears alive for provided PID."""
    try:
        pid_int = int(pid)
    except Exception:
        return False
    if pid_int <= 0:
        return False
    try:
        os.kill(pid_int, 0)
        return True
    except PermissionError:
        return True
    except ProcessLookupError:
        return False
    except OSError:
        return False


def evaluate_lock(path: Path, now_ts: float | None = None) -> dict[str, Any]:
    """Evaluate a single lock file and return state metadata."""
    now = now_ts if isinstance(now_ts, (int, float)) else time.time()
    result: dict[str, Any] = {
        "path": path,
        "state": "missing",
        "reason": "file_missing",
        "pid": None,
        "age_seconds": None,
    }
    if not path.exists():
        return result

    metadata = read_lock_metadata(path)
    if not metadata:
        result["state"] = "malformed"
        result["reason"] = "invalid_or_legacy_lock_payload"
        return result

    required_fields = {
        "version",
        "lock_type",
        "pid",
        "ppid",
        "created_at",
        "stale_after_seconds",
        "host",
        "command",
    }
    if not required_fields.issubset(set(metadata.keys())):
        result["state"] = "malformed"
        result["reason"] = "missing_required_metadata_fields"
        return result

    result["pid"] = metadata.get("pid")
    try:
        created_at = float(metadata.get("created_at"))
    except Exception:
        result["state"] = "malformed"
        result["reason"] = "invalid_created_at"
        return result
    try:
        stale_after_seconds = int(metadata.get("stale_after_seconds"))
    except Exception:
        stale_after_seconds = 5400
    if stale_after_seconds <= 0:
        stale_after_seconds = 5400

    age_seconds = max(0.0, now - created_at)
    result["age_seconds"] = age_seconds

    pid_alive = is_pid_alive(metadata.get("pid"))
    if pid_alive and age_seconds <= stale_after_seconds:
        result["state"] = "active"
        result["reason"] = "pid_alive_within_stale_window"
        return result
    if not pid_alive:
        result["state"] = "stale"
        result["reason"] = "process_not_running"
        return result

    result["state"] = "stale"
    result["reason"] = "stale_age_exceeded"
    return result


def evaluate_lock_set(
    paths: Iterable[Path], now_ts: float | None = None
) -> dict[str, list[dict[str, Any]]]:
    """Evaluate a list of lock paths and bucket results by state."""
    buckets: dict[str, list[dict[str, Any]]] = {
        "active": [],
        "stale": [],
        "malformed": [],
        "missing": [],
    }
    for path in paths:
        evaluation = evaluate_lock(path, now_ts=now_ts)
        state = evaluation.get("state", "missing")
        if state not in buckets:
            state = "missing"
        buckets[state].append(evaluation)
    return buckets


def cleanup_lock_paths(paths: Iterable[Path]) -> int:
    """Best-effort cleanup of lock file paths."""
    removed = 0
    for path in paths:
        try:
            if path.exists():
                path.unlink()
                removed += 1
        except Exception:
            continue
    return removed
