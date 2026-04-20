#!/usr/bin/env python3
# TOOL_TIER: supporting

"""Run bandit security linter and emit standard-format JSON results."""

from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from .. import config
    from ..shared.audit_storage_scope import jsons_dir_for_scope
    from ..shared.cache_dependency_paths import (
        compute_scoped_py_source_signature,
        static_check_config_digest,
    )
    from ..shared.sharded_static_analysis import merge_bandit_raw_payloads
    from ..shared.static_analysis_shard_cache import (
        load_shard_manifest,
        save_shard_manifest_atomic,
        shard_cache_path,
        shard_entry_hit,
        stable_shard_id,
        upsert_shard_manifest,
    )
except ImportError:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from development_tools import config
    from development_tools.shared.audit_storage_scope import jsons_dir_for_scope
    from development_tools.shared.cache_dependency_paths import (
        compute_scoped_py_source_signature,
        static_check_config_digest,
    )
    from development_tools.shared.sharded_static_analysis import merge_bandit_raw_payloads
    from development_tools.shared.static_analysis_shard_cache import (
        load_shard_manifest,
        save_shard_manifest_atomic,
        shard_cache_path,
        shard_entry_hit,
        stable_shard_id,
        upsert_shard_manifest,
    )

try:
    from core.logger import get_component_logger

    _bandit_log = get_component_logger("development_tools.static_checks.analyze_bandit")
except ImportError:
    _bandit_log = None


def _build_unavailable_result(message: str) -> dict[str, Any]:
    return {
        "summary": {"total_issues": 0, "files_affected": 0, "status": "WARN"},
        "details": {
            "tool": "bandit",
            "tool_available": False,
            "message": message,
            "severity_counts": {},
            "top_files": [],
            "returncode": None,
        },
    }


def _resolve_python_command(command: list[str]) -> list[str]:
    if not command:
        return command
    first = str(command[0]).lower()
    if first in {"python", "python3", "py", "python.exe"}:
        return [sys.executable] + command[1:]
    return command


def _build_result_from_payload(payload: dict[str, Any], returncode: int) -> dict[str, Any]:
    results = payload.get("results", [])
    if not isinstance(results, list):
        results = []

    severity_counts: dict[str, int] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for item in results:
        if not isinstance(item, dict):
            continue
        sev = str(item.get("issue_severity", "")).upper()
        if sev:
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

    actionable: list[dict[str, Any]] = [
        item
        for item in results
        if isinstance(item, dict)
        and str(item.get("issue_severity", "")).upper() in {"MEDIUM", "HIGH"}
    ]
    per_file: dict[str, int] = {}
    for item in actionable:
        fn = str(item.get("filename", "")).strip()
        if fn:
            per_file[fn] = per_file.get(fn, 0) + 1

    total_all = len(results)
    actionable_count = len(actionable)
    top_files = sorted(per_file.items(), key=lambda x: x[1], reverse=True)[:5]

    status = "PASS" if actionable_count == 0 else "FAIL"

    return {
        "summary": {
            "total_issues": actionable_count,
            "files_affected": len(per_file),
            "status": status,
        },
        "details": {
            "tool": "bandit",
            "tool_available": True,
            "returncode": returncode,
            "severity_counts": severity_counts,
            "low_severity_count": int(severity_counts.get("LOW", 0)),
            "total_findings_including_low": total_all,
            "top_files": [{"file": p, "count": c} for p, c in top_files],
        },
    }


def _run_bandit_subprocess_for_json(
    project_root: Path,
    command: list[str],
    args: list[str],
    timeout_seconds: int,
) -> tuple[int | None, dict[str, Any] | None, str]:
    """Run bandit; return (returncode, root JSON object, error_message if failed)."""
    try:
        result = subprocess.run(
            command + args,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        return None, None, "bandit command not found"
    except subprocess.TimeoutExpired:
        return None, None, "bandit execution timed out"
    except KeyboardInterrupt:
        return None, None, (
            "bandit interrupted (console control event while waiting for bandit)"
        )
    except Exception as exc:
        return None, None, f"bandit execution failed: {exc}"

    stdout_text = (result.stdout or "").strip()
    if not stdout_text:
        stderr_text = (result.stderr or "").strip()
        if stderr_text:
            return None, None, f"bandit returned no JSON output: {stderr_text}"
        return None, None, "bandit returned no JSON output"

    try:
        payload = json.loads(stdout_text)
    except json.JSONDecodeError:
        return None, None, "bandit output was not valid JSON"

    if not isinstance(payload, dict):
        return None, None, "bandit JSON root must be an object"
    return result.returncode, payload, ""


def run_bandit(project_root: Path) -> dict[str, Any]:
    static_cfg = config.get_static_analysis_config()
    command = _resolve_python_command(
        list(static_cfg.get("bandit_command", [sys.executable, "-m", "bandit"]))
    )
    exclude_csv = str(
        static_cfg.get(
            "bandit_exclude",
            "__pycache__,.git",
        )
    )
    timeout_seconds = int(static_cfg.get("bandit_timeout_seconds", 900) or 900)
    extra_args = list(static_cfg.get("bandit_args", []))

    default_roots = [
        "core",
        "communication",
        "ui",
        "ai",
        "user",
        "tasks",
        "notebook",
        "development_tools",
    ]
    scan_roots = list(static_cfg.get("bandit_scan_roots", default_roots))
    root_py = list(
        static_cfg.get("bandit_root_python", ["run_tests.py", "run_mhm.py"])
    )
    path_args: list[str] = []
    for name in scan_roots:
        p = project_root / name
        if p.is_dir():
            path_args.append(name)
    for name in root_py:
        p = project_root / name
        if p.is_file():
            path_args.append(name)
    if not path_args:
        path_args = ["."]

    pyproject_path = project_root / "pyproject.toml"
    config_prefix: list[str] = (
        ["-c", str(pyproject_path)] if pyproject_path.is_file() else []
    )

    jsons_dir = jsons_dir_for_scope(project_root, "static_checks")
    cache_path = shard_cache_path(jsons_dir, "analyze_bandit")
    working_manifest = load_shard_manifest(cache_path)
    cfg_digest = static_check_config_digest(project_root)

    shard_scan = bool(static_cfg.get("bandit_shard_scan", False))
    cache_dirty = False

    if shard_scan and len(path_args) > 1:
        payloads: list[dict[str, Any]] = []
        max_rc = 0
        subprocess_runs = 0
        fragment_hits = 0
        for rel_target in path_args:
            sid = stable_shard_id([rel_target])
            src_sig = compute_scoped_py_source_signature(project_root, [rel_target])
            effective_sig = src_sig or "__empty_scope__"
            cached_payload: dict[str, Any] | None = None
            if cfg_digest is not None:
                frag = shard_entry_hit(
                    working_manifest,
                    config_digest=cfg_digest,
                    shard_id=sid,
                    source_signature=effective_sig,
                )
                if isinstance(frag, dict):
                    cached_payload = frag
            if cached_payload is not None:
                payloads.append(cached_payload)
                fragment_hits += 1
                continue
            args_one: list[str] = (
                config_prefix
                + ["-r", rel_target]
                + ["-f", "json", "-q", "-x", exclude_csv]
                + extra_args
            )
            rc, payload, err = _run_bandit_subprocess_for_json(
                project_root, command, args_one, timeout_seconds
            )
            if rc is None or payload is None:
                return _build_unavailable_result(err)
            subprocess_runs += 1
            max_rc = max(max_rc, int(rc))
            payloads.append(payload)
            if cfg_digest is not None:
                working_manifest = upsert_shard_manifest(
                    working_manifest,
                    tool_name="analyze_bandit",
                    config_digest=cfg_digest,
                    shard_id=sid,
                    source_signature=effective_sig,
                    fragment=payload,
                )
                cache_dirty = True
        merged = merge_bandit_raw_payloads(payloads)
        out = _build_result_from_payload(merged, max_rc)
        det = out.get("details")
        if isinstance(det, dict):
            det["shard_run"] = {
                "mode": "sharded",
                "subprocesses": subprocess_runs,
                "merged": True,
                "fragment_cache_hits": fragment_hits,
                "fragment_cache_misses": subprocess_runs,
            }
        if _bandit_log:
            _bandit_log.info(
                f"analyze_bandit: sharded run subprocesses={subprocess_runs} cache_hits={fragment_hits}"
            )
        if cache_dirty and isinstance(working_manifest, dict):
            with contextlib.suppress(OSError):
                save_shard_manifest_atomic(cache_path, working_manifest)
        return out

    mono_id = "__monolithic__"
    full_sig = compute_scoped_py_source_signature(project_root, path_args)
    mono_cached: dict[str, Any] | None = None
    if full_sig is not None and cfg_digest is not None:
        mf = load_shard_manifest(cache_path)
        frag = shard_entry_hit(
            mf,
            config_digest=cfg_digest,
            shard_id=mono_id,
            source_signature=full_sig,
        )
        if isinstance(frag, dict):
            mono_cached = frag
    if mono_cached is not None:
        out = _build_result_from_payload(mono_cached, 0)
        det = out.get("details")
        if isinstance(det, dict):
            det["shard_run"] = {
                "mode": "single",
                "subprocesses": 0,
                "merged": False,
                "fragment_cache_hits": 1,
                "fragment_cache_misses": 0,
            }
        return out

    args: list[str] = (
        config_prefix
        + ["-r"]
        + path_args
        + ["-f", "json", "-q", "-x", exclude_csv]
        + extra_args
    )
    rc, payload, err = _run_bandit_subprocess_for_json(
        project_root, command, args, timeout_seconds
    )
    if rc is None or payload is None:
        return _build_unavailable_result(err)
    out = _build_result_from_payload(payload, int(rc))
    det = out.get("details")
    if isinstance(det, dict):
        det["shard_run"] = {"mode": "single", "subprocesses": 1}
    if full_sig is not None and cfg_digest is not None:
        wm = upsert_shard_manifest(
            load_shard_manifest(cache_path),
            tool_name="analyze_bandit",
            config_digest=cfg_digest,
            shard_id=mono_id,
            source_signature=full_sig,
            fragment=payload,
        )
        with contextlib.suppress(OSError):
            save_shard_manifest_atomic(cache_path, wm)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze bandit security findings.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory to analyze (default: current directory).",
    )
    ns = parser.parse_args(argv)

    result = run_bandit(Path(ns.project_root).resolve())
    if ns.json:
        print(json.dumps(result, indent=2))
    else:
        summary = result.get("summary", {})
        print(
            f"Bandit status={summary.get('status', 'UNKNOWN')} "
            f"issues={summary.get('total_issues', 0)} "
            f"files={summary.get('files_affected', 0)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
