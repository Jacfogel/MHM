#!/usr/bin/env python3
# TOOL_TIER: supporting

"""Run pyright and emit standard-format JSON results."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    from .. import config
except ImportError:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from development_tools import config


def _build_unavailable_result(message: str) -> Dict[str, Any]:
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


def _resolve_python_command(command: List[str]) -> List[str]:
    """Normalize generic Python launcher commands to the current interpreter."""
    if not command:
        return command
    first = str(command[0]).lower()
    if first in {"python", "python3", "py", "python.exe"}:
        return [sys.executable] + command[1:]
    return command


def _build_result_from_payload(payload: Dict[str, Any], returncode: int) -> Dict[str, Any]:
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

    issue_diags: List[Dict[str, Any]] = []
    for diag in diagnostics:
        if not isinstance(diag, dict):
            continue
        severity = str(diag.get("severity", "")).lower()
        if severity in {"error", "warning"}:
            issue_diags.append(diag)

    per_file: Dict[str, int] = {}
    per_file_errors: Dict[str, int] = {}
    per_file_warnings: Dict[str, int] = {}
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


def run_pyright(project_root: Path) -> Dict[str, Any]:
    static_cfg = config.get_static_analysis_config()
    command = _resolve_python_command(
        list(static_cfg.get("pyright_command", [sys.executable, "-m", "pyright"]))
    )
    args = list(static_cfg.get("pyright_args", ["--outputjson"]))
    if "--project" not in args:
        configured_project = static_cfg.get(
            "pyright_project_path", "development_tools/config/pyrightconfig.json"
        )
        if configured_project:
            project_config_path = Path(str(configured_project))
            if not project_config_path.is_absolute():
                project_config_path = project_root / project_config_path
            args.extend(["--project", str(project_config_path)])
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
        return _build_unavailable_result("pyright command not found")
    except subprocess.TimeoutExpired:
        return _build_unavailable_result("pyright execution timed out")
    except Exception as exc:
        return _build_unavailable_result(f"pyright execution failed: {exc}")

    raw_output = result.stdout.strip()
    if not raw_output:
        stderr_text = result.stderr.strip()
        if stderr_text:
            return _build_unavailable_result(f"pyright returned no JSON output: {stderr_text}")
        return _build_unavailable_result("pyright returned no JSON output")

    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError:
        return _build_unavailable_result("pyright output was not valid JSON")

    return _build_result_from_payload(payload, result.returncode)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze pyright diagnostics.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory to analyze (default: current directory).",
    )
    ns = parser.parse_args(argv)

    result = run_pyright(Path(ns.project_root).resolve())
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
