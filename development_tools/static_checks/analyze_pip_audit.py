#!/usr/bin/env python3
# TOOL_TIER: supporting

"""Run pip-audit for the active environment and emit standard-format JSON results."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
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


def _build_unavailable_result(message: str) -> dict[str, Any]:
    return {
        "summary": {"total_issues": 0, "files_affected": 0, "status": "WARN"},
        "details": {
            "tool": "pip_audit",
            "tool_available": False,
            "message": message,
            "vulnerable_packages": [],
            "returncode": None,
        },
    }


def _pip_audit_skip_env_enabled() -> bool:
    """CI/offline: skip network fetch when MHM_PIP_AUDIT_SKIP is truthy."""
    val = os.environ.get("MHM_PIP_AUDIT_SKIP", "").strip().lower()
    return val in ("1", "true", "yes", "on")


def _build_skipped_by_env_result() -> dict[str, Any]:
    """Structured PASS with zero findings; details record policy skip (no subprocess)."""
    return {
        "summary": {"total_issues": 0, "files_affected": 0, "status": "PASS"},
        "details": {
            "tool": "pip_audit",
            "tool_available": True,
            "returncode": 0,
            "pip_audit_skipped": True,
            "message": (
                "pip-audit skipped: MHM_PIP_AUDIT_SKIP is set (CI/offline policy; "
                "no vulnerability index fetch)."
            ),
            "vulnerable_packages": [],
        },
    }


def _resolve_python_command(command: list[str]) -> list[str]:
    if not command:
        return command
    first = str(command[0]).lower()
    if first in {"python", "python3", "py", "python.exe"}:
        return [sys.executable] + command[1:]
    return command


def _count_vulnerabilities(payload: Any) -> tuple[int, int, list[dict[str, Any]]]:
    """Return (total_vuln_count, packages_with_vulns, sample rows for top display)."""
    total = 0
    packages = 0
    samples: list[dict[str, Any]] = []
    if isinstance(payload, dict) and "dependencies" in payload:
        deps = payload.get("dependencies", [])
    elif isinstance(payload, list):
        deps = payload
    else:
        return 0, 0, []

    if not isinstance(deps, list):
        return 0, 0, []

    for dep in deps:
        if not isinstance(dep, dict):
            continue
        name = str(dep.get("name", "")).strip()
        version = str(dep.get("version", "")).strip()
        vulns = dep.get("vulns") or dep.get("vulnerabilities") or []
        if not isinstance(vulns, list):
            continue
        n = len(vulns)
        if n <= 0:
            continue
        total += n
        packages += 1
        if len(samples) < 8:
            vid = ""
            if vulns and isinstance(vulns[0], dict):
                vid = str(vulns[0].get("id", vulns[0].get("cve", ""))).strip()
            samples.append(
                {
                    "name": name,
                    "version": version,
                    "vuln_count": n,
                    "example_id": vid,
                }
            )
    return total, packages, samples


def _build_result_from_payload(payload: Any, returncode: int) -> dict[str, Any]:
    total, pkg_count, samples = _count_vulnerabilities(payload)
    status = "WARN" if total > 0 else "PASS"
    return {
        "summary": {
            "total_issues": total,
            "files_affected": pkg_count,
            "status": status,
        },
        "details": {
            "tool": "pip_audit",
            "tool_available": True,
            "returncode": returncode,
            "vulnerable_packages": samples,
        },
    }


def requirements_signature(project_root: Path) -> str | None:
    """Stable hash of dependency files for cache invalidation."""
    root = project_root.resolve()
    parts: list[bytes] = []
    for rel in ("requirements.txt", "pyproject.toml"):
        p = root / rel
        if p.is_file():
            try:
                parts.append(rel.encode() + b"\0" + p.read_bytes())
            except OSError:
                continue
    if not parts:
        return None
    h = hashlib.sha256()
    for blob in parts:
        h.update(blob)
    return h.hexdigest()


def run_pip_audit(project_root: Path) -> dict[str, Any]:
    if _pip_audit_skip_env_enabled():
        return _build_skipped_by_env_result()
    static_cfg = config.get_static_analysis_config()
    command = _resolve_python_command(
        list(static_cfg.get("pip_audit_command", [sys.executable, "-m", "pip_audit"]))
    )
    timeout_seconds = int(static_cfg.get("pip_audit_timeout_seconds", 600) or 600)
    extra_args = list(static_cfg.get("pip_audit_args", []))
    args: list[str] = ["--format", "json"] + extra_args

    try:
        result = subprocess.run(
            command + args,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        return _build_unavailable_result("pip-audit command not found")
    except subprocess.TimeoutExpired:
        return _build_unavailable_result("pip-audit execution timed out (network or index slow)")
    except KeyboardInterrupt:
        return _build_unavailable_result(
            "pip-audit interrupted (console control event while waiting for pip-audit)"
        )
    except Exception as exc:
        return _build_unavailable_result(f"pip-audit execution failed: {exc}")

    stdout_text = (result.stdout or "").strip()
    stderr_text = (result.stderr or "").strip()

    if not stdout_text:
        hint = stderr_text or "no stdout"
        if "Network" in stderr_text or "network" in stderr_text.lower():
            return _build_unavailable_result(f"pip-audit failed (network/offline?): {hint[:500]}")
        return _build_unavailable_result(f"pip-audit returned no JSON output: {hint[:500]}")

    try:
        payload = json.loads(stdout_text)
    except json.JSONDecodeError:
        return _build_unavailable_result("pip-audit output was not valid JSON")

    return _build_result_from_payload(payload, result.returncode)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze pip-audit dependency vulnerabilities.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory (default: current directory).",
    )
    ns = parser.parse_args(argv)

    result = run_pip_audit(Path(ns.project_root).resolve())
    if ns.json:
        print(json.dumps(result, indent=2))
    else:
        summary = result.get("summary", {})
        print(
            f"pip-audit status={summary.get('status', 'UNKNOWN')} "
            f"vulns={summary.get('total_issues', 0)} "
            f"packages={summary.get('files_affected', 0)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
