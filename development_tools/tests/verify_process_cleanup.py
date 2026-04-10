#!/usr/bin/env python3
"""
Verify process cleanup behavior for pytest workers on Windows.

Tracked migration of scripts/testing/verify_process_cleanup.py.

On Windows, process metadata uses Get-CimInstance Win32_Process so CommandLine
is populated (tasklist CSV does not expose command lines; V5 §3.18).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from typing import Any

from core.logger import get_component_logger

logger = get_component_logger("development_tools")


def _parse_cim_json_payload(raw: str) -> list[dict[str, Any]]:
    """Parse PowerShell ConvertTo-Json output for python.exe processes."""
    text = raw.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def _get_python_processes_win32_cim() -> list[dict[str, object]] | None:
    """Return python.exe rows with ProcessId and CommandLine via CIM, or None on failure."""
    # Single-line script: always emit a JSON array (empty when no python.exe).
    ps = (
        r"$pids = @(Get-CimInstance -ClassName Win32_Process -Filter \"Name='python.exe'\"); "
        r"$out = foreach ($x in $pids) { "
        r"[PSCustomObject]@{ "
        r"ProcessId = $x.ProcessId; "
        r"CommandLine = $(if ($null -eq $x.CommandLine) { '' } else { [string]$x.CommandLine }) "
        r"} }; "
        r"ConvertTo-Json -InputObject @($out) -Compress -Depth 5"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("CIM process listing failed to start: %s", exc)
        return None

    if result.returncode != 0:
        logger.warning(
            "CIM process listing returned %s: %s",
            result.returncode,
            (result.stderr or "").strip()[:500],
        )
        return None

    rows = _parse_cim_json_payload(result.stdout or "")
    processes: list[dict[str, object]] = []
    for row in rows:
        raw_pid = row.get("ProcessId", row.get("processId"))
        if raw_pid is None:
            continue
        try:
            pid = int(raw_pid)
        except (TypeError, ValueError):
            continue
        cmd = row.get("CommandLine", row.get("commandLine"))
        cmdline = "" if cmd is None else str(cmd)
        processes.append({"pid": pid, "cmdline": cmdline, "is_pytest": False})
    return processes


def _get_python_processes_win32_tasklist() -> list[dict[str, object]]:
    """Legacy: tasklist CSV has no command line; cmdline left empty (weak pytest detection)."""
    result = subprocess.run(
        ["tasklist", "/FO", "CSV", "/FI", "IMAGENAME eq python.exe"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        return []

    processes: list[dict[str, object]] = []
    lines = result.stdout.strip().splitlines()
    for line in lines[1:]:
        parts = line.split('","')
        if len(parts) < 2:
            continue
        try:
            pid = int(parts[1].strip('"'))
        except ValueError:
            continue
        processes.append({"pid": pid, "cmdline": "", "is_pytest": False})
    return processes


def get_python_processes() -> list[dict[str, object]]:
    """Return python.exe process metadata for Windows hosts."""
    if sys.platform != "win32":
        return []

    cim = _get_python_processes_win32_cim()
    if cim is not None:
        return cim

    logger.warning("Falling back to tasklist (no CommandLine); pytest orphan detection may miss workers.")
    return _get_python_processes_win32_tasklist()


def check_for_orphaned_processes() -> tuple[bool, list[dict[str, object]]]:
    """Check for pytest-like worker leftovers."""
    processes = get_python_processes()
    pytest_processes: list[dict[str, object]] = []
    for proc in processes:
        cmdline = str(proc.get("cmdline") or "")
        is_pytest = (
            "pytest" in cmdline.lower()
            or "xdist" in cmdline.lower()
            or "gw" in cmdline.lower()
        )
        proc["is_pytest"] = is_pytest
        if is_pytest:
            pytest_processes.append(proc)
    return bool(pytest_processes), pytest_processes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify pytest process cleanup behavior.")
    parser.add_argument("--watch", action="store_true", help="Continuously watch for orphaned processes.")
    parser.add_argument("--interval-seconds", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="Emit standard {summary, details} JSON.")
    args = parser.parse_args(argv)

    if args.watch:
        print("Watching for orphaned pytest processes. Press Ctrl+C to stop.")
        try:
            while True:
                found, offenders = check_for_orphaned_processes()
                if found:
                    print(f"Found {len(offenders)} potential orphaned pytest process(es).")
                else:
                    print("No orphaned pytest processes found.")
                time.sleep(args.interval_seconds)
        except KeyboardInterrupt:
            print("Stopped.")
        return 0

    found, offenders = check_for_orphaned_processes()
    result = {
        "summary": {
            "total_issues": len(offenders),
            "files_affected": len(offenders),
            "status": "WARN" if found else "PASS",
        },
        "details": {
            "platform": sys.platform,
            "orphaned_processes_found": found,
            "orphaned_processes": offenders,
        },
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    if found:
        logger.warning(f"Found {len(offenders)} potential orphaned pytest process(es).")
        print(f"Found {len(offenders)} potential orphaned pytest process(es).")
        return 0
    logger.info("No orphaned pytest processes found.")
    print("No orphaned pytest processes found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
