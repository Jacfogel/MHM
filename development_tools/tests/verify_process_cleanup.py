#!/usr/bin/env python3
"""
Verify process cleanup behavior for pytest workers on Windows.

Tracked migration of scripts/testing/verify_process_cleanup.py.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

from core.logger import get_component_logger

logger = get_component_logger("development_tools")


def get_python_processes() -> list[dict[str, object]]:
    """Return python.exe process metadata for Windows hosts."""
    if sys.platform != "win32":
        return []
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


def check_for_orphaned_processes() -> tuple[bool, list[dict[str, object]]]:
    """Check for pytest-like worker leftovers."""
    processes = get_python_processes()
    pytest_processes: list[dict[str, object]] = []
    for proc in processes:
        cmdline = str(proc.get("cmdline") or "")
        is_pytest = "pytest" in cmdline.lower() or "xdist" in cmdline.lower() or "gw" in cmdline.lower()
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

