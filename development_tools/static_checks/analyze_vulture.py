#!/usr/bin/env python3
# TOOL_TIER: supporting

"""Run vulture dead-code scan and emit standard-format JSON results (V6 B-012)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from .. import config
except ImportError:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from development_tools import config

try:
    from development_tools.shared.logging import get_dev_tools_logger

    _vulture_log = get_dev_tools_logger("development_tools.static_checks.analyze_vulture")
except ImportError:
    _vulture_log = None

# file.py:12: unused function 'foo' (80% confidence)
_FINDING_RE = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+):\s*(?P<message>.+?)\s*\((?P<confidence>\d+)% confidence\)\s*$"
)


# Ephemeral / noisy trees that race with parallel tests or are not useful for dead-code signal.
_DEFAULT_VULTURE_EXCLUDES = (
    "*/tests/data/*",
    "*/tests/logs/*",
    "*/.venv/*",
    "*/__pycache__/*",
    "*/.git/*",
)


def _merge_vulture_exclude_args(extra_args: list[str]) -> list[str]:
    """Ensure default excludes are always applied (merge with any caller --exclude)."""
    args = list(extra_args)
    default = ",".join(_DEFAULT_VULTURE_EXCLUDES)
    for i, arg in enumerate(args):
        if arg == "--exclude" and i + 1 < len(args):
            existing = str(args[i + 1]).strip().strip(",")
            args[i + 1] = f"{existing},{default}" if existing else default
            return args
        if isinstance(arg, str) and arg.startswith("--exclude="):
            existing = arg.split("=", 1)[1].strip().strip(",")
            args[i] = f"--exclude={existing},{default}" if existing else f"--exclude={default}"
            return args
    return args + ["--exclude", default]


def _build_unavailable_result(message: str) -> dict[str, Any]:
    return {
        "summary": {"total_issues": 0, "files_affected": 0, "status": "WARN"},
        "details": {
            "tool": "vulture",
            "tool_available": False,
            "message": message,
            "min_confidence": None,
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


def _resolve_scan_paths(project_root: Path, static_cfg: dict[str, Any]) -> list[str]:
    """Prefer configured vulture paths; else get_scan_directories(); else ``.``."""
    configured = list(static_cfg.get("vulture_scan_paths") or [])
    path_args: list[str] = []
    for name in configured:
        p = project_root / name
        if p.exists():
            path_args.append(str(name).replace("\\", "/"))
    if path_args:
        return path_args
    try:
        scan_dirs = list(config.get_scan_directories() or [])
    except Exception:
        scan_dirs = []
    for name in scan_dirs:
        p = project_root / name
        if p.exists():
            path_args.append(str(name).replace("\\", "/"))
    return path_args or ["."]


def _parse_vulture_output(stdout_text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for raw_line in (stdout_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = _FINDING_RE.match(line)
        if not match:
            continue
        findings.append(
            {
                "file": match.group("file").replace("\\", "/"),
                "line": int(match.group("line")),
                "message": match.group("message").strip(),
                "confidence": int(match.group("confidence")),
            }
        )
    return findings


def _build_result_from_findings(
    findings: list[dict[str, Any]],
    *,
    returncode: int,
    min_confidence: int,
) -> dict[str, Any]:
    per_file: dict[str, int] = {}
    for item in findings:
        fn = str(item.get("file", "")).strip()
        if fn:
            per_file[fn] = per_file.get(fn, 0) + 1
    top_files = sorted(per_file.items(), key=lambda x: x[1], reverse=True)[:5]
    total = len(findings)
    # WARN when findings exist so Tier 3 does not treat vulture as a hard fail gate.
    status = "PASS" if total == 0 else "WARN"
    return {
        "summary": {
            "total_issues": total,
            "files_affected": len(per_file),
            "status": status,
        },
        "details": {
            "tool": "vulture",
            "tool_available": True,
            "returncode": returncode,
            "min_confidence": min_confidence,
            "top_files": [{"file": p, "count": c} for p, c in top_files],
            "findings_sample": findings[:25],
        },
    }


def run_vulture(project_root: Path) -> dict[str, Any]:
    static_cfg = config.get_static_analysis_config()
    command = _resolve_python_command(
        list(static_cfg.get("vulture_command", [sys.executable, "-m", "vulture"]))
    )
    min_confidence = int(static_cfg.get("vulture_min_confidence", 80) or 80)
    timeout_seconds = int(static_cfg.get("vulture_timeout_seconds", 600) or 600)
    extra_args = _merge_vulture_exclude_args(list(static_cfg.get("vulture_args", [])))
    path_args = _resolve_scan_paths(project_root, static_cfg)

    args = [
        *path_args,
        f"--min-confidence={min_confidence}",
        *extra_args,
    ]
    try:
        result = subprocess.run(
            command + args,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        return _build_unavailable_result("vulture command not found")
    except subprocess.TimeoutExpired:
        return _build_unavailable_result("vulture execution timed out")
    except KeyboardInterrupt:
        return _build_unavailable_result(
            "vulture interrupted (console control event while waiting for vulture)"
        )
    except Exception as exc:
        return _build_unavailable_result(f"vulture execution failed: {exc}")

    # vulture exits 0 when clean, 3 when dead code found (typical); other codes may be errors.
    stdout_text = result.stdout or ""
    stderr_text = (result.stderr or "").strip()
    findings = _parse_vulture_output(stdout_text)
    if result.returncode not in {0, 3} and not findings:
        message = stderr_text or f"vulture failed with return code {result.returncode}"
        return _build_unavailable_result(message)

    out = _build_result_from_findings(
        findings, returncode=int(result.returncode), min_confidence=min_confidence
    )
    if _vulture_log:
        _vulture_log.info(
            f"analyze_vulture: issues={out['summary']['total_issues']} "
            f"files={out['summary']['files_affected']} min_confidence={min_confidence}"
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze vulture dead-code findings.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory to analyze (default: current directory).",
    )
    ns = parser.parse_args(argv)

    result = run_vulture(Path(ns.project_root).resolve())
    if ns.json:
        print(json.dumps(result, indent=2))
    else:
        summary = result.get("summary", {})
        print(
            f"Vulture status={summary.get('status', 'UNKNOWN')} "
            f"issues={summary.get('total_issues', 0)} "
            f"files={summary.get('files_affected', 0)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
