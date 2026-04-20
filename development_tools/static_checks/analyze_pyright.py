#!/usr/bin/env python3
# TOOL_TIER: supporting

"""Run pyright and emit standard-format JSON results."""

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
        compute_full_repo_py_source_signature,
        compute_scoped_py_source_signature,
        static_check_config_digest,
    )
    from ..shared.sharded_static_analysis import merge_pyright_json_payloads
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
        compute_full_repo_py_source_signature,
        compute_scoped_py_source_signature,
        static_check_config_digest,
    )
    from development_tools.shared.sharded_static_analysis import merge_pyright_json_payloads
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

    _pyright_log = get_component_logger("development_tools.static_checks.analyze_pyright")
except ImportError:
    _pyright_log = None


def _build_unavailable_result(message: str) -> dict[str, Any]:
    return {
        "summary": {"total_issues": 0, "files_affected": 0, "status": "WARN"},
        "details": {
            "tool": "pyright",
            "tool_available": False,
            "message": message,
            "errors": 0,
            "warnings": 0,
            "information": 0,
            "top_files": [],
            "top_error_files": [],
            "top_warning_files": [],
            "returncode": None,
        },
    }


def _resolve_python_command(command: list[str]) -> list[str]:
    """Normalize generic Python launcher commands to the current interpreter."""
    if not command:
        return command
    first = str(command[0]).lower()
    if first in {"python", "python3", "py", "python.exe"}:
        return [sys.executable] + command[1:]
    return command


def _normalize_pyright_shard_rel_paths(project_root: Path, shard: Any) -> list[str]:
    """Return existing repo-relative paths for one shard (forward slashes, no traversal)."""
    if not isinstance(shard, (list, tuple)):
        return []
    out: list[str] = []
    for rel in shard:
        s = str(rel).strip().replace("\\", "/")
        if not s or s.startswith("/") or ".." in s.split("/"):
            continue
        p = (project_root / s).resolve()
        try:
            p.relative_to(project_root.resolve())
        except ValueError:
            continue
        if p.exists():
            out.append(s)
    return out


def _run_pyright_subprocess_for_json(
    project_root: Path,
    command: list[str],
    args: list[str],
    timeout_seconds: int,
) -> tuple[int | None, dict[str, Any] | None, str]:
    try:
        result = subprocess.run(
            command + args,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        return None, None, "pyright command not found"
    except subprocess.TimeoutExpired:
        return None, None, "pyright execution timed out"
    except TimeoutError:
        return None, None, "pyright execution timed out"
    except KeyboardInterrupt:
        return None, None, (
            "pyright interrupted (console control event while waiting for pyright)"
        )
    except Exception as exc:
        return None, None, f"pyright execution failed: {exc}"

    raw_output = result.stdout.strip()
    if not raw_output:
        stderr_text = result.stderr.strip()
        if stderr_text:
            return None, None, f"pyright returned no JSON output: {stderr_text}"
        return None, None, "pyright returned no JSON output"

    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError:
        return None, None, "pyright output was not valid JSON"

    if not isinstance(payload, dict):
        return None, None, "pyright output payload is not a JSON object"
    return result.returncode, payload, ""


def _build_result_from_payload(payload: dict[str, Any], returncode: int) -> dict[str, Any]:
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    diagnostics = (
        payload.get("generalDiagnostics", []) if isinstance(payload, dict) else []
    )
    if not isinstance(summary, dict):
        summary = {}
    if not isinstance(diagnostics, list):
        diagnostics = []

    errors = int(summary.get("errorCount", 0) or 0)
    warnings = int(summary.get("warningCount", 0) or 0)
    information = int(summary.get("informationCount", 0) or 0)
    files_analyzed = int(summary.get("filesAnalyzed", 0) or 0)

    issue_diags: list[dict[str, Any]] = []
    for diag in diagnostics:
        if not isinstance(diag, dict):
            continue
        severity = str(diag.get("severity", "")).lower()
        if severity in {"error", "warning"}:
            issue_diags.append(diag)

    per_file: dict[str, int] = {}
    per_file_errors: dict[str, int] = {}
    per_file_warnings: dict[str, int] = {}
    for diag in issue_diags:
        file_path = str(diag.get("file", "")).strip()
        if not file_path:
            continue
        severity = str(diag.get("severity", "")).lower()
        per_file[file_path] = per_file.get(file_path, 0) + 1
        if severity == "error":
            per_file_errors[file_path] = per_file_errors.get(file_path, 0) + 1
        elif severity == "warning":
            per_file_warnings[file_path] = per_file_warnings.get(file_path, 0) + 1

    top_files = sorted(per_file.items(), key=lambda item: item[1], reverse=True)[:5]
    top_error_files = sorted(
        per_file_errors.items(), key=lambda item: item[1], reverse=True
    )[:5]
    top_warning_files = sorted(
        per_file_warnings.items(), key=lambda item: item[1], reverse=True
    )[:5]
    if errors > 0:
        status = "FAIL"
    elif warnings > 0:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "summary": {
            "total_issues": errors + warnings,
            "files_affected": len(per_file),
            "status": status,
        },
        "details": {
            "tool": "pyright",
            "tool_available": True,
            "errors": errors,
            "warnings": warnings,
            "information": information,
            "files_analyzed": files_analyzed,
            "returncode": returncode,
            "top_files": [
                {"file": file_path, "count": count} for file_path, count in top_files
            ],
            "top_error_files": [
                {"file": file_path, "count": count}
                for file_path, count in top_error_files
            ],
            "top_warning_files": [
                {"file": file_path, "count": count}
                for file_path, count in top_warning_files
            ],
        },
    }


def run_pyright(project_root: Path) -> dict[str, Any]:
    static_cfg = config.get_static_analysis_config()
    command = _resolve_python_command(
        list(static_cfg.get("pyright_command", [sys.executable, "-m", "pyright"]))
    )
    args = list(static_cfg.get("pyright_args", ["--outputjson"]))
    project_config_path: Path | None = None
    if "--project" not in args:
        configured_project = static_cfg.get(
            "pyright_project_path", "pyproject.toml"
        )
        if configured_project:
            pcp = Path(str(configured_project))
            if not pcp.is_absolute():
                pcp = project_root / pcp
            project_config_path = pcp.resolve()
            if not project_config_path.is_file():
                fallback = (project_root / "pyproject.toml").resolve()
                if fallback.is_file():
                    if _pyright_log:
                        _pyright_log.warning(
                            "static_analysis pyright_project_path %s not found; using %s",
                            project_config_path,
                            fallback,
                        )
                    project_config_path = fallback
            args.extend(["--project", str(project_config_path)])
    timeout_seconds = int(static_cfg.get("timeout_seconds", 600) or 600)

    use_shards = bool(static_cfg.get("pyright_shard_scan", False))
    raw_shards = static_cfg.get("pyright_path_shards")
    shards: list[Any] = list(raw_shards) if isinstance(raw_shards, list) else []

    jsons_dir = jsons_dir_for_scope(project_root, "static_checks")
    cache_path = shard_cache_path(jsons_dir, "analyze_pyright")
    working_manifest = load_shard_manifest(cache_path)
    cfg_digest = static_check_config_digest(project_root)

    payload: dict[str, Any] | None = None
    result_returncode = 0
    shard_run_info: dict[str, Any] | None = None
    cache_dirty = False

    if use_shards and shards:
        shard_payloads: list[dict[str, Any]] = []
        max_rc = 0
        subprocess_runs = 0
        fragment_hits = 0
        for shard in shards:
            rels = _normalize_pyright_shard_rel_paths(project_root, shard)
            if not rels:
                continue
            sid = stable_shard_id(rels)
            src_sig = compute_scoped_py_source_signature(project_root, rels)
            effective_sig = src_sig or "__empty_scope__"
            cached_obj: dict[str, Any] | None = None
            if cfg_digest is not None:
                frag = shard_entry_hit(
                    working_manifest,
                    config_digest=cfg_digest,
                    shard_id=sid,
                    source_signature=effective_sig,
                )
                if isinstance(frag, dict):
                    cached_obj = frag
            if cached_obj is not None:
                shard_payloads.append(cached_obj)
                fragment_hits += 1
                continue
            run_args = list(args) + rels
            rc, pl, err = _run_pyright_subprocess_for_json(
                project_root, command, run_args, timeout_seconds
            )
            if rc is None or pl is None:
                return _build_unavailable_result(err)
            subprocess_runs += 1
            max_rc = max(max_rc, int(rc))
            shard_payloads.append(pl)
            if cfg_digest is not None:
                working_manifest = upsert_shard_manifest(
                    working_manifest,
                    tool_name="analyze_pyright",
                    config_digest=cfg_digest,
                    shard_id=sid,
                    source_signature=effective_sig,
                    fragment=pl,
                )
                cache_dirty = True
        if shard_payloads:
            payload = merge_pyright_json_payloads(shard_payloads)
            result_returncode = max_rc
            shard_run_info = {
                "mode": "sharded",
                "subprocesses": subprocess_runs,
                "merged": True,
                "fragment_cache_hits": fragment_hits,
                "fragment_cache_misses": subprocess_runs,
                "parity_note": (
                    "Sharded Pyright may omit cross-package diagnostics; run a full-project "
                    "Pyright periodically (e.g. pyright_shard_scan false or CI) for strict parity."
                ),
            }
        if cache_dirty and isinstance(working_manifest, dict):
            with contextlib.suppress(OSError):
                save_shard_manifest_atomic(cache_path, working_manifest)
            cache_dirty = False

    if payload is None:
        mono_id = "__monolithic__"
        full_sig = compute_full_repo_py_source_signature(project_root)
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
            payload = mono_cached
            result_returncode = 0
            shard_run_info = {
                "mode": "single",
                "subprocesses": 0,
                "fragment_cache_hits": 1,
                "fragment_cache_misses": 0,
            }
        else:
            rc, pl, err = _run_pyright_subprocess_for_json(
                project_root, command, args, timeout_seconds
            )
            if rc is None or pl is None:
                return _build_unavailable_result(err)
            payload = pl
            result_returncode = int(rc)
            if shard_run_info is None:
                shard_run_info = (
                    {
                        "mode": "single_fallback",
                        "subprocesses": 1,
                        "reason": "no_shard_paths_resolved",
                    }
                    if (use_shards and shards)
                    else {"mode": "single", "subprocesses": 1}
                )
            if full_sig is not None and cfg_digest is not None:
                wm = upsert_shard_manifest(
                    load_shard_manifest(cache_path),
                    tool_name="analyze_pyright",
                    config_digest=cfg_digest,
                    shard_id=mono_id,
                    source_signature=full_sig,
                    fragment=pl,
                )
                with contextlib.suppress(OSError):
                    save_shard_manifest_atomic(cache_path, wm)

    parsed = _build_result_from_payload(payload, result_returncode)
    details = parsed.get("details", {})
    if isinstance(details, dict) and shard_run_info is not None:
        details["shard_run"] = shard_run_info
        if _pyright_log and shard_run_info.get("mode") == "sharded":
            n = int(shard_run_info.get("subprocesses") or 0)
            h = int(shard_run_info.get("fragment_cache_hits") or 0)
            _pyright_log.info(
                f"analyze_pyright: sharded run subprocesses={n} cache_hits={h}"
            )
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze pyright diagnostics.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory to analyze (default: current directory).",
    )
    ns = parser.parse_args(argv)

    try:
        result = run_pyright(Path(ns.project_root).resolve())
    except (subprocess.TimeoutExpired, TimeoutError) as exc:
        result = _build_unavailable_result("pyright execution timed out")
        if ns.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Pyright timed out: {exc}")
        return 1
    except Exception as exc:
        result = _build_unavailable_result(f"analyze_pyright crashed: {exc}")
        if ns.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Pyright failed: {exc}")
        return 1

    if ns.json:
        print(json.dumps(result, indent=2))
    else:
        summary = result.get("summary", {})
        print(
            f"Pyright status={summary.get('status', 'UNKNOWN')} "
            f"issues={summary.get('total_issues', 0)} "
            f"files={summary.get('files_affected', 0)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
