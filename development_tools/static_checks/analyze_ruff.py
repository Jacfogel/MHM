#!/usr/bin/env python3
# TOOL_TIER: supporting

"""Run ruff and emit standard-format JSON results."""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from .. import config
    from ..config.sync_ruff_toml import sync_ruff_toml
    from ..shared.audit_storage_scope import jsons_dir_for_scope
    from ..shared.cache_dependency_paths import (
        compute_full_repo_py_source_signature,
        compute_scoped_py_source_signature,
        static_check_config_digest,
    )
    from ..shared.sharded_static_analysis import merge_ruff_check_json_lists
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
    from development_tools.config.sync_ruff_toml import sync_ruff_toml
    from development_tools.shared.audit_storage_scope import jsons_dir_for_scope
    from development_tools.shared.cache_dependency_paths import (
        compute_full_repo_py_source_signature,
        compute_scoped_py_source_signature,
        static_check_config_digest,
    )
    from development_tools.shared.sharded_static_analysis import merge_ruff_check_json_lists
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

    _ruff_log = get_component_logger("development_tools.static_checks.analyze_ruff")
except ImportError:
    _ruff_log = None


def _build_unavailable_result(message: str) -> dict[str, Any]:
    return {
        "summary": {"total_issues": 0, "files_affected": 0, "status": "WARN"},
        "details": {
            "tool": "ruff",
            "tool_available": False,
            "message": message,
            "violations_by_rule": {},
            "top_files": [],
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


def _build_result_from_payload(payload: list[dict[str, Any]], returncode: int) -> dict[str, Any]:
    if not isinstance(payload, list):
        return _build_unavailable_result("ruff output payload is not a JSON list")

    per_file: dict[str, int] = {}
    by_rule: dict[str, int] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        file_path = str(item.get("filename", "")).strip()
        code = str(item.get("code", "")).strip()
        if file_path:
            per_file[file_path] = per_file.get(file_path, 0) + 1
        if code:
            by_rule[code] = by_rule.get(code, 0) + 1

    top_files = sorted(per_file.items(), key=lambda item: item[1], reverse=True)[:5]
    top_rules = sorted(by_rule.items(), key=lambda item: item[1], reverse=True)[:10]
    total_issues = len(payload)

    return {
        "summary": {
            "total_issues": total_issues,
            "files_affected": len(per_file),
            "status": "FAIL" if total_issues > 0 else "PASS",
        },
        "details": {
            "tool": "ruff",
            "tool_available": True,
            "returncode": returncode,
            "top_files": [
                {"file": file_path, "count": count} for file_path, count in top_files
            ],
            "violations_by_rule": {code: count for code, count in top_rules},
            "top_rules": [],
        },
    }


def _extract_rule_name(rule_output: str, expected_code: str) -> str:
    """Extract readable Ruff rule name from `ruff rule <CODE>` output."""
    text = str(rule_output or "").strip()
    if not text:
        return ""
    first_line = text.splitlines()[0].strip()
    match = re.match(r"^#\s+(.+)\s+\(([A-Z]+\d+)\)\s*$", first_line)
    if not match:
        return ""
    name, code = match.group(1).strip(), match.group(2).strip()
    if code != expected_code:
        return ""
    return name


def _resolve_top_rule_names(
    command: list[str],
    rule_codes: list[str],
    project_root: Path,
    timeout_seconds: int,
) -> dict[str, str]:
    """Resolve Ruff rule names for top rule codes using `ruff rule <CODE>`."""
    resolved: dict[str, str] = {}
    per_rule_timeout = max(5, min(timeout_seconds, 20))
    for code in rule_codes:
        try:
            result = subprocess.run(
                command + ["rule", code],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=per_rule_timeout,
            )
        except Exception:
            continue
        output = (result.stdout or "").strip() or (result.stderr or "").strip()
        name = _extract_rule_name(output, code)
        if name:
            resolved[code] = name
    return resolved


def _normalize_ruff_shard_rel_paths(project_root: Path, shard: Any) -> list[str]:
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


def _run_ruff_subprocess_for_json_list(
    project_root: Path,
    command: list[str],
    args: list[str],
    timeout_seconds: int,
) -> tuple[int | None, list[dict[str, Any]] | None, str]:
    """Run ruff; return (returncode, json list payload, error_message if failed)."""
    try:
        result = subprocess.run(
            command + args,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        return None, None, "ruff command not found"
    except subprocess.TimeoutExpired:
        return None, None, "ruff execution timed out"
    except KeyboardInterrupt:
        return None, None, (
            "ruff interrupted (console control event while waiting for ruff)"
        )
    except Exception as exc:
        return None, None, f"ruff execution failed: {exc}"

    stdout_text = result.stdout.strip()
    if not stdout_text:
        stderr_text = result.stderr.strip()
        if stderr_text:
            return None, None, f"ruff returned no JSON output: {stderr_text}"
        return None, None, "ruff returned no JSON output"

    try:
        payload = json.loads(stdout_text)
    except json.JSONDecodeError:
        return None, None, "ruff output was not valid JSON"

    if not isinstance(payload, list):
        return None, None, "ruff output payload is not a JSON list"
    return result.returncode, payload, ""


def run_ruff(project_root: Path) -> dict[str, Any]:
    static_cfg = config.get_static_analysis_config()
    configured_ruff_path = static_cfg.get(
        "ruff_config_path", "development_tools/config/ruff.toml"
    )
    sync_root_compat = bool(static_cfg.get("ruff_sync_root_compat", True))
    ruff_toml_path = sync_ruff_toml(
        project_root,
        config_path=configured_ruff_path,
        sync_root_compat=sync_root_compat,
    )
    command = _resolve_python_command(
        list(static_cfg.get("ruff_command", [sys.executable, "-m", "ruff"]))
    )
    timeout_seconds = int(static_cfg.get("timeout_seconds", 600) or 600)

    use_shards = bool(static_cfg.get("ruff_shard_scan", False))
    raw_shards = static_cfg.get("ruff_path_shards")
    shards: list[Any] = list(raw_shards) if isinstance(raw_shards, list) else []

    jsons_dir = jsons_dir_for_scope(project_root, "static_checks")
    cache_path = shard_cache_path(jsons_dir, "analyze_ruff")
    working_manifest = load_shard_manifest(cache_path)
    cfg_digest = static_check_config_digest(project_root)

    payload: list[dict[str, Any]] | None = None
    result_returncode = 0
    shard_run_info: dict[str, Any] | None = None
    cache_dirty = False

    if use_shards and shards:
        shard_lists: list[list[dict[str, Any]]] = []
        max_rc = 0
        subprocess_runs = 0
        fragment_hits = 0
        for shard in shards:
            rels = _normalize_ruff_shard_rel_paths(project_root, shard)
            if not rels:
                continue
            sid = stable_shard_id(rels)
            src_sig = compute_scoped_py_source_signature(project_root, rels)
            effective_sig = src_sig or "__empty_scope__"
            cached_list: list[dict[str, Any]] | None = None
            if cfg_digest is not None:
                frag = shard_entry_hit(
                    working_manifest,
                    config_digest=cfg_digest,
                    shard_id=sid,
                    source_signature=effective_sig,
                )
                if isinstance(frag, list):
                    cached_list = frag
            if cached_list is not None:
                shard_lists.append(cached_list)
                fragment_hits += 1
                continue
            args = ["check"] + rels + ["--output-format", "json"]
            if "--config" not in args:
                args.extend(["--config", str(ruff_toml_path)])
            rc, pl, err = _run_ruff_subprocess_for_json_list(
                project_root, command, args, timeout_seconds
            )
            if rc is None or pl is None:
                return _build_unavailable_result(err)
            subprocess_runs += 1
            max_rc = max(max_rc, int(rc))
            shard_lists.append(pl)
            if cfg_digest is not None:
                working_manifest = upsert_shard_manifest(
                    working_manifest,
                    tool_name="analyze_ruff",
                    config_digest=cfg_digest,
                    shard_id=sid,
                    source_signature=effective_sig,
                    fragment=pl,
                )
                cache_dirty = True
        if shard_lists:
            payload = merge_ruff_check_json_lists(shard_lists)
            result_returncode = max_rc
            shard_run_info = {
                "mode": "sharded",
                "subprocesses": subprocess_runs,
                "merged": True,
                "fragment_cache_hits": fragment_hits,
                "fragment_cache_misses": subprocess_runs,
            }
        if cache_dirty and isinstance(working_manifest, dict):
            with contextlib.suppress(OSError):
                save_shard_manifest_atomic(cache_path, working_manifest)
            cache_dirty = False

    if payload is None:
        mono_id = "__monolithic__"
        full_sig = compute_full_repo_py_source_signature(project_root)
        mono_cached: list[dict[str, Any]] | None = None
        if full_sig is not None and cfg_digest is not None:
            mf = load_shard_manifest(cache_path)
            frag = shard_entry_hit(
                mf,
                config_digest=cfg_digest,
                shard_id=mono_id,
                source_signature=full_sig,
            )
            if isinstance(frag, list):
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
            args = list(static_cfg.get("ruff_args", ["check", ".", "--output-format", "json"]))
            if "--config" not in args:
                args.extend(["--config", str(ruff_toml_path)])
            rc, pl, err = _run_ruff_subprocess_for_json_list(
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
                    tool_name="analyze_ruff",
                    config_digest=cfg_digest,
                    shard_id=mono_id,
                    source_signature=full_sig,
                    fragment=pl,
                )
                with contextlib.suppress(OSError):
                    save_shard_manifest_atomic(cache_path, wm)

    parsed_result = _build_result_from_payload(payload, result_returncode)
    details = parsed_result.get("details", {})
    if isinstance(details, dict):
        if shard_run_info is not None:
            details["shard_run"] = shard_run_info
            if _ruff_log and shard_run_info.get("mode") == "sharded":
                n = int(shard_run_info.get("subprocesses") or 0)
                h = int(shard_run_info.get("fragment_cache_hits") or 0)
                _ruff_log.info(
                    f"analyze_ruff: sharded run subprocesses={n} cache_hits={h}"
                )
        top_rule_counts = details.get("violations_by_rule", {})
        if isinstance(top_rule_counts, dict) and top_rule_counts:
            ordered_codes = [str(code) for code in top_rule_counts]
            names = _resolve_top_rule_names(
                command=command,
                rule_codes=ordered_codes,
                project_root=project_root,
                timeout_seconds=timeout_seconds,
            )
            details["top_rules"] = [
                {
                    "code": code,
                    "name": names.get(code, ""),
                    "count": int(count),
                }
                for code, count in top_rule_counts.items()
            ]
    return parsed_result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze ruff diagnostics.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory to analyze (default: current directory).",
    )
    ns = parser.parse_args(argv)

    result = run_ruff(Path(ns.project_root).resolve())
    if ns.json:
        print(json.dumps(result, indent=2))
    else:
        summary = result.get("summary", {})
        print(
            f"Ruff status={summary.get('status', 'UNKNOWN')} "
            f"issues={summary.get('total_issues', 0)} "
            f"files={summary.get('files_affected', 0)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
