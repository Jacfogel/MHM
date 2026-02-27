#!/usr/bin/env python3
# TOOL_TIER: supporting

"""Run ruff and emit standard-format JSON results."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    from .. import config
    from ..config.sync_ruff_toml import sync_ruff_toml
except ImportError:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from development_tools import config
    from development_tools.config.sync_ruff_toml import sync_ruff_toml


def _build_unavailable_result(message: str) -> Dict[str, Any]:
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


def _resolve_python_command(command: List[str]) -> List[str]:
    """Normalize generic Python launcher commands to the current interpreter."""
    if not command:
        return command
    first = str(command[0]).lower()
    if first in {"python", "python3", "py", "python.exe"}:
        return [sys.executable] + command[1:]
    return command


def _build_result_from_payload(payload: List[Dict[str, Any]], returncode: int) -> Dict[str, Any]:
    if not isinstance(payload, list):
        return _build_unavailable_result("ruff output payload is not a JSON list")

    per_file: Dict[str, int] = {}
    by_rule: Dict[str, int] = {}
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
    command: List[str],
    rule_codes: List[str],
    project_root: Path,
    timeout_seconds: int,
) -> Dict[str, str]:
    """Resolve Ruff rule names for top rule codes using `ruff rule <CODE>`."""
    resolved: Dict[str, str] = {}
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


def run_ruff(project_root: Path) -> Dict[str, Any]:
    static_cfg = config.get_static_analysis_config()
    ruff_toml_path = sync_ruff_toml(project_root)
    command = _resolve_python_command(
        list(static_cfg.get("ruff_command", [sys.executable, "-m", "ruff"]))
    )
    args = list(static_cfg.get("ruff_args", ["check", ".", "--output-format", "json"]))
    if "--config" not in args:
        args.extend(["--config", str(ruff_toml_path)])
    timeout_seconds = int(static_cfg.get("timeout_seconds", 600) or 600)

    try:
        result = subprocess.run(
            command + args,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        return _build_unavailable_result("ruff command not found")
    except subprocess.TimeoutExpired:
        return _build_unavailable_result("ruff execution timed out")
    except Exception as exc:
        return _build_unavailable_result(f"ruff execution failed: {exc}")

    stdout_text = result.stdout.strip()
    if not stdout_text:
        stderr_text = result.stderr.strip()
        if stderr_text:
            return _build_unavailable_result(f"ruff returned no JSON output: {stderr_text}")
        return _build_unavailable_result("ruff returned no JSON output")

    try:
        payload = json.loads(stdout_text)
    except json.JSONDecodeError:
        return _build_unavailable_result("ruff output was not valid JSON")

    parsed_result = _build_result_from_payload(payload, result.returncode)
    details = parsed_result.get("details", {})
    if isinstance(details, dict):
        top_rule_counts = details.get("violations_by_rule", {})
        if isinstance(top_rule_counts, dict) and top_rule_counts:
            ordered_codes = [str(code) for code in top_rule_counts.keys()]
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


def main(argv: List[str] | None = None) -> int:
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
