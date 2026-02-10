#!/usr/bin/env python3
"""
Test Runner for MHM Project

Provides different test execution modes for faster development workflow.
"""

import sys
import subprocess
import argparse
import os
import time
import xml.etree.ElementTree as ET
import threading
import queue
import re
import logging
import signal
import json
import shutil
from pathlib import Path
from typing import Dict, Optional, List
from core.error_handling import handle_errors
from core.time_utilities import now_timestamp_filename, now_timestamp_full

# Try to import psutil for resource monitoring (optional dependency)
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

# Simple ANSI color codes for terminal output (works in modern PowerShell)
# Enable ANSI color support in Windows
if sys.platform == "win32":
    import ctypes

    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(
        kernel32.GetStdHandle(-11), 7
    )  # Enable ANSI escape sequences

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")

# Global state for interrupt handling
_interrupt_requested = False
_current_process = None
_current_junit_xml = None
_partial_results_file = Path("tests/logs/partial_results.json")
_partial_results_file.parent.mkdir(parents=True, exist_ok=True)
# Use backups directory (consolidated from results_backup)
_backups_dir = Path("tests/logs/backups")
_backups_dir.mkdir(parents=True, exist_ok=True)
_last_output_time = None
_resource_warnings_enabled = True
_critical_memory_limit = 98.0
_auto_terminate_enabled = True
_captured_output_lines = []  # Store captured output for partial results extraction

# Global variable to store current test context
_current_test_context = None


@handle_errors(
    "killing process tree on Windows", user_friendly=False, default_return=False
)
def kill_process_tree_windows(pid):
    """Kill a process and all its children on Windows.

    Returns:
        bool: True if taskkill succeeded, False otherwise
    """
    try:
        # Use taskkill to kill the process tree
        # /T = kill child processes, /F = force kill
        result = subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            print(
                f"{GREEN}[CLEANUP]{RESET} Successfully killed process tree for PID {pid}"
            )
            return True
        elif (
            "not found" in result.stdout.lower() or "not found" in result.stderr.lower()
        ):
            # Process already gone - that's fine
            print(
                f"{YELLOW}[CLEANUP]{RESET} Process {pid} not found (already terminated)"
            )
            return True
        else:
            print(
                f"{YELLOW}[CLEANUP]{RESET} taskkill returned code {result.returncode} for PID {pid}: {result.stderr}"
            )
            return False
    except Exception as e:
        print(f"{YELLOW}[CLEANUP]{RESET} Error killing process tree for PID {pid}: {e}")
        # Fallback to regular kill if taskkill fails
        try:
            import signal

            os.kill(pid, signal.SIGTERM)
            return True
        except Exception:
            return False


@handle_errors(
    "cleaning up orphaned pytest processes", user_friendly=False, default_return=0
)
def cleanup_orphaned_pytest_processes():
    """Find and kill any orphaned pytest worker processes on Windows.

    Returns:
        int: Number of orphaned processes found and killed
    """
    if sys.platform != "win32":
        return 0  # Only needed on Windows

    killed_count = 0
    try:
        # Find all Python processes that look like pytest workers
        # Look for processes with "pytest" or "gw" (pytest-xdist worker) in command line
        result = subprocess.run(
            ["tasklist", "/FO", "CSV", "/FI", "IMAGENAME eq python.exe"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if result.returncode != 0:
            return 0

        # Parse output to find pytest processes
        lines = result.stdout.strip().split("\n")
        if len(lines) < 2:  # Header + at least one process
            return 0

        # Skip header line
        for line in lines[1:]:
            if not line.strip():
                continue
            try:
                # CSV format: "Image Name","PID","Session Name","Session#","Mem Usage"
                parts = line.split('","')
                if len(parts) >= 2:
                    pid_str = parts[1].strip('"')
                    pid = int(pid_str)

                    # Skip our own process
                    if pid == os.getpid():
                        continue

                    # Get command line for this process to check if it's pytest
                    cmd_result = subprocess.run(
                        [
                            "wmic",
                            "process",
                            "where",
                            f"ProcessId={pid}",
                            "get",
                            "CommandLine",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=3,
                        check=False,
                    )

                    if cmd_result.returncode == 0 and cmd_result.stdout:
                        cmdline = cmd_result.stdout.lower()
                        # Check if it's a pytest process (but not our current process)
                        if (
                            "pytest" in cmdline or "gw" in cmdline
                        ) and "xdist" in cmdline:
                            # This is likely an orphaned pytest worker
                            try:
                                kill_result = subprocess.run(
                                    ["taskkill", "/F", "/PID", str(pid)],
                                    capture_output=True,
                                    text=True,
                                    timeout=2,
                                    check=False,
                                )
                                if kill_result.returncode == 0:
                                    killed_count += 1
                                    print(
                                        f"{GREEN}[CLEANUP]{RESET} Killed orphaned pytest worker PID {pid}"
                                    )
                            except Exception as e:
                                print(
                                    f"{YELLOW}[CLEANUP]{RESET} Failed to kill orphaned process {pid}: {e}"
                                )
            except (ValueError, IndexError):
                continue

        if killed_count > 0:
            print(
                f"{GREEN}[CLEANUP]{RESET} Cleaned up {killed_count} orphaned pytest worker process(es)"
            )
        elif killed_count == 0:
            # Only print if we actually scanned (not if we returned early)
            pass  # Don't print "no orphaned processes" here - let caller decide
        return killed_count
    except Exception as e:
        print(f"{YELLOW}[CLEANUP]{RESET} Error during orphaned process cleanup: {e}")
        return killed_count


@handle_errors("handling interrupt signal", user_friendly=False, default_return=None)
def interrupt_handler(signum, frame):
    """Handle interrupt signals (Ctrl+C) gracefully."""
    global _interrupt_requested, _captured_output_lines, _current_test_context
    _interrupt_requested = True
    print(
        f"\n\n{YELLOW}[INTERRUPT]{RESET} Received interrupt signal (Ctrl+C) - saving partial results..."
    )

    # Collect any available output before saving
    output_text = "".join(_captured_output_lines) if _captured_output_lines else None

    # Save partial results if available (will try XML first, then output text)
    if _current_junit_xml:
        save_partial_results(
            _current_junit_xml,
            interrupted=True,
            output_text=output_text,
            test_context=_current_test_context,
        )

    # Also save captured output for worker test assignment extraction (even on interrupt)
    if _captured_output_lines:
        output_file = Path("tests/logs/pytest_console_output.txt")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(output_file, "w", encoding="utf-8", errors="replace") as f:
                f.write("".join(_captured_output_lines))
        except Exception:
            pass  # Non-critical

    # Terminate current process and all child processes (especially pytest-xdist workers)
    if _current_process and _current_process.poll() is None:
        print(
            f"{YELLOW}[INTERRUPT]{RESET} Terminating test process and all worker processes..."
        )
        try:
            # On Windows, we need to kill the entire process tree to get pytest-xdist workers
            if sys.platform == "win32":
                kill_process_tree_windows(_current_process.pid)
            else:
                # On Unix, terminate sends signal to process group
                _current_process.terminate()
        except Exception as e:
            print(f"{YELLOW}[WARNING]{RESET} Error during process termination: {e}")
            # Fallback to regular terminate
            try:
                _current_process.terminate()
            except Exception:
                pass

        # Wait up to 5 seconds for graceful shutdown
        shutdown_start = time.time()
        while _current_process.poll() is None and (time.time() - shutdown_start) < 5:
            time.sleep(0.1)
        if _current_process.poll() is None:
            print(
                f"{YELLOW}[INTERRUPT]{RESET} Process did not terminate, force killing process tree..."
            )
            # Force kill the entire process tree
            if sys.platform == "win32":
                kill_process_tree_windows(_current_process.pid)
            else:
                _current_process.kill()

        # Always check for orphaned processes after termination
        if sys.platform == "win32":
            # Small delay to allow processes to fully terminate
            time.sleep(0.5)
            orphaned_count = cleanup_orphaned_pytest_processes()
            if orphaned_count == 0:
                print(
                    f"{GREEN}[CLEANUP]{RESET} Verified: No orphaned processes remaining"
                )

        # CRITICAL: Consolidate worker logs even after interrupt
        # When process is forcefully terminated, pytest_sessionfinish may not run
        # So we need to consolidate worker logs manually
        try:
            # Import consolidation function
            sys.path.insert(0, str(Path(__file__).parent))
            from tests.conftest import _consolidate_worker_logs

            print(f"{GREEN}[CLEANUP]{RESET} Consolidating worker log files...")
            _consolidate_worker_logs()
            print(f"{GREEN}[CLEANUP]{RESET} Worker log consolidation complete")
        except Exception as e:
            print(
                f"{YELLOW}[CLEANUP]{RESET} Could not consolidate worker logs automatically: {e}"
            )
            print(
                f"{YELLOW}[CLEANUP]{RESET} Run manually: python development_tools/consolidate_worker_logs.py"
            )


@handle_errors("monitoring system resources", user_friendly=False, default_return={})
def monitor_resources():
    """Monitor system resource usage and return metrics."""
    if not PSUTIL_AVAILABLE:
        return {}

    try:
        process = psutil.Process()
        mem_info = process.memory_info()
        num_threads = process.num_threads()
        num_fds = process.num_fds() if hasattr(process, "num_fds") else None

        # Get system-wide memory info
        sys_mem = psutil.virtual_memory()

        return {
            "memory_rss_mb": mem_info.rss / (1024 * 1024),
            "memory_vms_mb": mem_info.vms / (1024 * 1024),
            "threads": num_threads,
            "file_descriptors": num_fds,
            "system_memory_percent": sys_mem.percent,
            "system_memory_available_mb": sys_mem.available / (1024 * 1024),
        }
    except Exception:
        return {}


@handle_errors("checking resource warnings", user_friendly=False, default_return=False)
def check_resource_warnings(resources: dict) -> bool:
    """Check if resources exceed warning thresholds."""
    if not resources or not _resource_warnings_enabled:
        return False

    warnings = []
    critical = False

    # Memory warning (80% of system memory)
    if "system_memory_percent" in resources:
        mem_percent = resources["system_memory_percent"]
        if mem_percent > 98:
            warnings.append(
                f"System memory usage: {mem_percent:.1f}% (CRITICAL - terminating to prevent system crash)"
            )
            critical = True
        elif mem_percent > 95:
            warnings.append(
                f"System memory usage: {mem_percent:.1f}% (CRITICAL - consider terminating)"
            )
            critical = True
        elif mem_percent > 80:
            warnings.append(f"System memory usage: {mem_percent:.1f}%")

    # Process memory warning (2GB)
    if "memory_rss_mb" in resources:
        if resources["memory_rss_mb"] > 2048:
            warnings.append(f"Process memory: {resources['memory_rss_mb']:.0f}MB")

    # Thread count warning (500 threads)
    if "threads" in resources:
        if resources["threads"] > 500:
            warnings.append(f"Thread count: {resources['threads']}")

    # File descriptor warning (1000 handles)
    if "file_descriptors" in resources and resources["file_descriptors"]:
        if resources["file_descriptors"] > 1000:
            warnings.append(f"File descriptors: {resources['file_descriptors']}")

    if warnings:
        if critical:
            print(f"\n{RED}[RESOURCE CRITICAL]{RESET} {'; '.join(warnings)}")
        else:
            print(f"\n{YELLOW}[RESOURCE WARNING]{RESET} {'; '.join(warnings)}")
        return True

    return False


@handle_errors(
    "checking critical resource limits", user_friendly=False, default_return=False
)
def check_critical_resources(resources: dict) -> bool:
    """Check if resources exceed critical thresholds requiring termination."""
    global _critical_memory_limit, _auto_terminate_enabled

    if not resources or not _auto_terminate_enabled:
        return False

    # Critical memory threshold: configurable (default 98%)
    if "system_memory_percent" in resources:
        if resources["system_memory_percent"] > _critical_memory_limit:
            return True

    return False


@handle_errors(
    "extracting results from output text",
    user_friendly=False,
    default_return={
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "warnings": 0,
        "errors": 0,
        "total": 0,
        "deselected": 0,
    },
)
def extract_results_from_output(output_text: str) -> dict[str, int]:
    """Extract test results from pytest output text when JUnit XML is unavailable."""
    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "warnings": 0,
        "errors": 0,
        "total": 0,
        "deselected": 0,
    }

    if not output_text:
        return results

    # Remove ANSI escape codes
    output_plain = ANSI_ESCAPE_RE.sub("", output_text)

    # Try to find summary line like "3819 passed, 1 skipped in 243.16s" or "4 failed, 2276 passed, 1 skipped, 4 warnings"
    # Pattern 1: Full summary with all counts
    full_pattern = (
        r"(\d+)\s+failed[,\s]+(\d+)\s+passed[,\s]+(\d+)\s+skipped[,\s]+(\d+)\s+warnings"
    )
    match = re.search(full_pattern, output_plain)
    if match:
        results["failed"] = int(match.group(1))
        results["passed"] = int(match.group(2))
        results["skipped"] = int(match.group(3))
        results["warnings"] = int(match.group(4))
        results["total"] = results["passed"] + results["failed"] + results["skipped"]
        return results

    # Pattern 2: Just passed/skipped (no failures)
    simple_pattern = r"(\d+)\s+passed[,\s]+(\d+)\s+skipped"
    match = re.search(simple_pattern, output_plain)
    if match:
        results["passed"] = int(match.group(1))
        results["skipped"] = int(match.group(2))
        results["total"] = results["passed"] + results["skipped"]
        return results

    # Pattern 3: Count dots in progress output (rough estimate)
    # Count dots (.) which represent passed tests
    dot_count = output_plain.count(".")
    if dot_count > 0:
        results["passed"] = dot_count
        results["total"] = dot_count

    return results


@handle_errors("extracting pytest session info", user_friendly=False, default_return={})
def extract_pytest_session_info(output_text: str) -> dict:
    """Extract pytest session information from output text."""
    session_info = {}
    if not output_text:
        return session_info

    output_plain = ANSI_ESCAPE_RE.sub("", output_text)

    # Extract number of workers
    workers_match = re.search(
        r"created:\s*(\d+)/(\d+)\s+workers", output_plain, re.IGNORECASE
    )
    if workers_match:
        session_info["workers_created"] = int(workers_match.group(1))
        session_info["workers_total"] = int(workers_match.group(2))

    # Extract number of test items
    items_match = re.search(
        r"(\d+)\s+workers\s+\[(\d+)\s+items?\]", output_plain, re.IGNORECASE
    )
    if items_match:
        session_info["test_items"] = int(items_match.group(2))

    # Extract collected/deselected counts
    collected_match = re.search(
        r"collected\s+(\d+)\s+items?(?:\s+/\s+(\d+)\s+deselected)?",
        output_plain,
        re.IGNORECASE,
    )
    if collected_match:
        session_info["collected"] = int(collected_match.group(1))
        if collected_match.group(2):
            session_info["deselected"] = int(collected_match.group(2))

    # Extract pytest plugins
    plugins_match = re.search(r"plugins:\s+(.+?)(?:\n|$)", output_plain, re.IGNORECASE)
    if plugins_match:
        plugins_str = plugins_match.group(1)
        # Parse plugins (format: "plugin1-version, plugin2-version")
        plugins = [p.strip() for p in plugins_str.split(",")]
        session_info["plugins"] = plugins

    return session_info


@handle_errors("saving partial test results", user_friendly=False, default_return=None)
def save_partial_results(
    junit_xml_path: str,
    interrupted: bool = False,
    output_text: str = None,
    test_context: dict = None,
):
    """Save partial test results from JUnit XML, falling back to output text parsing."""
    global _captured_output_lines

    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "warnings": 0,
        "errors": 0,
        "total": 0,
        "deselected": 0,
    }
    failure_details = []  # List of failure dicts with test names and error messages

    # First try to parse JUnit XML
    if junit_xml_path and os.path.exists(junit_xml_path):
        # Wait a moment for file to be written (especially important on interrupt)
        if interrupted:
            time.sleep(0.5)  # Give pytest time to write what it can
        results = parse_junit_xml(junit_xml_path)
        # Extract failure details even when interrupted
        failure_details = extract_failures_from_junit_xml(junit_xml_path)

    # If XML parsing returned zeros and we have output text, try extracting from output
    if results.get("total", 0) == 0 and (output_text or _captured_output_lines):
        output_to_parse = output_text or "".join(_captured_output_lines)
        if output_to_parse:
            output_results = extract_results_from_output(output_to_parse)
            # Merge results, preferring non-zero values
            for key in results:
                if output_results.get(key, 0) > 0 or results.get(key, 0) == 0:
                    results[key] = output_results.get(key, 0)

    # Extract pytest session info from output
    output_to_parse = output_text or "".join(_captured_output_lines)
    session_info = {}
    if output_to_parse:
        session_info = extract_pytest_session_info(output_to_parse)

    # Extract failure details from output text if JUnit XML didn't provide them
    if not failure_details and output_to_parse:
        # Try to extract from "short test summary info" section
        output_plain = ANSI_ESCAPE_RE.sub("", output_to_parse)
        # Look for "FAILED tests/path.py::TestClass::test_method" lines
        failed_test_pattern = r"FAILED\s+([^\s]+::[^\s]+)"
        failed_tests = re.findall(failed_test_pattern, output_plain)
        for test_name in failed_tests:
            failure_details.append(
                {
                    "test": test_name,
                    "type": "failure",
                    "message": "Extracted from output (JUnit XML unavailable)",
                    "details": "",
                }
            )

    # If interrupted, use test_items from session_info as the actual total
    # (JUnit XML might only contain completed tests, not all tests that were supposed to run)
    if interrupted and session_info and "test_items" in session_info:
        actual_total = session_info["test_items"]
        # Only update total if it's less than actual_total (meaning some tests didn't complete)
        if results.get("total", 0) < actual_total:
            # Update total to reflect all tests that were supposed to run
            results["total"] = actual_total
            # Note: we don't know which of the incomplete tests would have passed/failed,
            # so we leave passed/failed/skipped as-is (they only reflect completed tests)

    partial_data = {
        "timestamp": now_timestamp_full(),
        "interrupted": interrupted,
        "results": results,
        "junit_xml_path": junit_xml_path,
        "failures": failure_details,  # Include failure details even when interrupted
    }

    # Add test run context if provided
    if test_context:
        partial_data["test_run_context"] = test_context

    # Add pytest session info if available
    if session_info:
        partial_data["pytest_session"] = session_info

    # Save to partial results file (both main file and timestamped backup)
    try:
        # Save to main partial_results.json for easy access
        with open(_partial_results_file, "w", encoding="utf-8") as f:
            json.dump(partial_data, f, indent=2)

        # Also save timestamped copy to backups directory so it doesn't get overwritten
        timestamp = now_timestamp_filename()
        phase = test_context.get("phase", "unknown") if test_context else "unknown"
        mode = test_context.get("mode", "unknown") if test_context else "unknown"
        partial_filename = f"partial_results_{phase}_{mode}_{timestamp}.json"
        timestamped_partial_file = _backups_dir / partial_filename

        with open(timestamped_partial_file, "w", encoding="utf-8") as f:
            json.dump(partial_data, f, indent=2)

        if interrupted:
            print(f"{YELLOW}[PARTIAL RESULTS]{RESET} Saved to {_partial_results_file}")
            print(
                f"{YELLOW}[PARTIAL RESULTS]{RESET} Timestamped copy: {timestamped_partial_file.name}"
            )
            print(
                f"  Passed: {results.get('passed', 0)}, Failed: {results.get('failed', 0)}, Skipped: {results.get('skipped', 0)}"
            )
            if test_context:
                print(f"  Phase: {phase}, Mode: {mode}")
    except Exception as e:
        # Don't fail if partial results can't be saved
        print(f"{YELLOW}[WARNING]{RESET} Could not save partial results: {e}")


@handle_errors("detecting stuck process", user_friendly=False, default_return=False)
def detect_stuck_process(
    last_output_time: float, current_time: float, threshold: float = 600
) -> bool:
    """Detect if process appears stuck (no output for extended period)."""
    if last_output_time is None:
        return False

    time_since_output = current_time - last_output_time
    return time_since_output > threshold


@handle_errors(
    "extracting failure details from JUnit XML", user_friendly=False, default_return=[]
)
def extract_failures_from_junit_xml(xml_path: str) -> list[dict[str, str]]:
    """
    Extract detailed failure information from JUnit XML.

    Returns a list of dicts with 'test', 'message', and 'type' keys.
    """
    failures = []

    if not os.path.exists(xml_path):
        return failures

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find all testcase elements with failure or error children
        for testcase in root.findall(".//testcase"):
            # Check for failure element
            failure = testcase.find("failure")
            if failure is not None:
                test_name = (
                    f"{testcase.get('classname', '')}::{testcase.get('name', '')}"
                )
                failures.append(
                    {
                        "test": test_name,
                        "type": "failure",
                        "message": failure.get("message", ""),
                        "details": failure.text or "",
                    }
                )

            # Check for error element
            error = testcase.find("error")
            if error is not None:
                test_name = (
                    f"{testcase.get('classname', '')}::{testcase.get('name', '')}"
                )
                failures.append(
                    {
                        "test": test_name,
                        "type": "error",
                        "message": error.get("message", ""),
                        "details": error.text or "",
                    }
                )
    except (ET.ParseError, ValueError, AttributeError):
        pass

    return failures


@handle_errors(
    "parsing JUnit XML report",
    user_friendly=False,
    default_return={
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "warnings": 0,
        "errors": 0,
        "total": 0,
        "deselected": 0,
    },
)
def parse_junit_xml(xml_path: str) -> dict[str, int]:
    """
    Parse JUnit XML report to extract test statistics.

    Returns a dictionary with: passed, failed, skipped, warnings, errors, total
    """
    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "warnings": 0,
        "errors": 0,
        "total": 0,
        "deselected": 0,
    }

    if not os.path.exists(xml_path):
        return results

    # Parse XML - errors are handled by decorator, but we catch parsing errors
    # to return empty results gracefully
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # JUnit XML structure: <testsuites> contains <testsuite> elements
        # Each testsuite has attributes: tests, failures, errors, skipped
        for testsuite in root.findall(".//testsuite"):
            tests = int(testsuite.get("tests", 0))
            failures = int(testsuite.get("failures", 0))
            errors = int(testsuite.get("errors", 0))
            skipped = int(testsuite.get("skipped", 0))

            results["total"] += tests
            results["failed"] += failures
            results["errors"] += errors
            results["skipped"] += skipped
            results["passed"] += tests - failures - errors - skipped

        # If no testsuites found, try direct attributes on root
        if results["total"] == 0:
            results["total"] = int(root.get("tests", 0))
            results["failed"] = int(root.get("failures", 0))
            results["errors"] = int(root.get("errors", 0))
            results["skipped"] = int(root.get("skipped", 0))
            results["passed"] = (
                results["total"]
                - results["failed"]
                - results["errors"]
                - results["skipped"]
            )
    except (ET.ParseError, ValueError, AttributeError):
        # If parsing fails (malformed XML, invalid values, etc.), return empty results
        # Other exceptions are handled by decorator
        pass

    return results


@handle_errors(
    "building Windows no-parallel test environment",
    user_friendly=False,
    default_return={},
)
def build_windows_no_parallel_env() -> dict[str, str]:
    """Return environment overrides for stable Windows serial UI/no_parallel runs."""
    if sys.platform != "win32":
        return {}

    env_overrides: dict[str, str] = {
        # Avoid desktop/plugin initialization issues in headless test runs.
        "QT_QPA_PLATFORM": "offscreen",
    }

    # Ensure venv and Qt bins are present early in PATH for DLL resolution.
    path_parts: list[str] = []
    scripts_dir = Path(sys.executable).resolve().parent
    venv_root = scripts_dir.parent
    pyqt_bin = venv_root / "Lib" / "site-packages" / "PyQt6" / "Qt6" / "bin"

    if scripts_dir.exists():
        path_parts.append(str(scripts_dir))
    if pyqt_bin.exists():
        path_parts.append(str(pyqt_bin))

    existing_path = os.environ.get("PATH", "")
    if path_parts:
        env_overrides["PATH"] = os.pathsep.join(path_parts + [existing_path])

    return env_overrides


@handle_errors(
    "running test command",
    user_friendly=False,
    default_return={
        "success": False,
        "output": "",
        "results": {},
        "duration": 0,
        "warnings": "",
        "failures": "",
    },
)
def run_command(
    cmd,
    description,
    progress_interval: int = 30,
    capture_output: bool = True,
    test_context: dict = None,
    env_overrides: dict | None = None,
):
    """
    Run a command and return results with periodic progress logs.

    Args:
        cmd: Command to run
        description: Description for progress messages
        progress_interval: Seconds between progress updates
        capture_output: If True, capture results via JUnit XML (always True in practice)
        test_context: Optional dict with test run context (mode, phase, config, etc.)

    Returns:
        dict with 'success', 'output', 'results', 'duration', 'warnings', 'failures' keys
    """
    global _interrupt_requested, _current_process, _current_junit_xml, _last_output_time, _captured_output_lines, _current_test_context

    # Store test context globally for interrupt handler
    _current_test_context = test_context

    # Reset interrupt flag and captured output
    _interrupt_requested = False
    _last_output_time = None
    _captured_output_lines = []

    # Register signal handlers for graceful shutdown
    @handle_errors("signal handler", default_return=None)
    def signal_handler(signum, frame):
        interrupt_handler(signum, frame)

    # Register handlers (Windows supports SIGINT, SIGTERM may not be available)
    if hasattr(signal, "SIGINT"):
        signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):
        try:
            signal.signal(signal.SIGTERM, signal_handler)
        except (ValueError, OSError):
            pass  # SIGTERM not available on Windows

    print(f"\nRunning: {description}...")

    start_time = time.time()

    # To preserve pytest's colors, let it write directly to the terminal (no pipe)
    # Use JUnit XML report to get structured results without capturing output
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w+", delete=False, encoding="utf-8", suffix=".xml"
    ) as tmp_file:
        junit_xml_path = tmp_file.name
        _current_junit_xml = junit_xml_path

    try:
        # Generate JUnit XML report for parsing (doesn't affect colors)
        cmd_with_junit = cmd + ["--junit-xml", junit_xml_path]

        # Ensure pytest keeps ANSI colors even though we're piping output
        contains_color_flag = any(opt.startswith("--color") for opt in cmd_with_junit)
        if not contains_color_flag:
            cmd_with_junit.append("--color=yes")

        # Capture output to parse warnings, but also write to terminal to preserve colors
        # Use a pipe that we can read from AND write to terminal
        output_queue = queue.Queue()
        output_lines = []

        @handle_errors(
            "reading output from pipe", user_friendly=False, default_return=None
        )
        def read_output(pipe, queue_obj):
            """Read from pipe and put lines in queue, also write to terminal."""
            global _last_output_time, _captured_output_lines
            try:
                for line in iter(pipe.readline, ""):
                    if line:
                        _last_output_time = time.time()  # Track last output time
                        queue_obj.put(line)
                        # Store in global list for partial results extraction
                        _captured_output_lines.append(line)
                        # Also write to terminal to preserve colors
                        sys.stdout.write(line)
                        sys.stdout.flush()
            finally:
                try:
                    pipe.close()
                except Exception:
                    pass  # Ignore errors closing pipe

        # Let pytest write directly to terminal - this preserves ALL colors
        # We'll parse warnings from the output if we can capture it
        # On Windows, create a new process group so we can kill the entire process tree
        creation_flags = 0
        if sys.platform == "win32":
            # CREATE_NEW_PROCESS_GROUP allows us to kill the entire process tree
            import subprocess as sp

            creation_flags = sp.CREATE_NEW_PROCESS_GROUP
            print(
                f"{GREEN}[PROCESS]{RESET} Creating process with CREATE_NEW_PROCESS_GROUP flag for tree termination"
            )

        process_env = os.environ.copy()
        if env_overrides:
            process_env.update({k: str(v) for k, v in env_overrides.items()})

        process = subprocess.Popen(
            cmd_with_junit,
            stdout=subprocess.PIPE,  # Capture for parsing
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            universal_newlines=True,
            bufsize=1,
            creationflags=creation_flags if sys.platform == "win32" else 0,
            env=process_env,
        )

        if sys.platform == "win32":
            print(
                f"{GREEN}[PROCESS]{RESET} Started pytest process PID {process.pid} (can kill tree)"
            )

        _current_process = process

        # Start thread to read output and display it
        output_thread = threading.Thread(
            target=read_output, args=(process.stdout, output_queue)
        )
        output_thread.daemon = True
        output_thread.start()

        # Monitor progress while process runs
        # Add maximum timeout to prevent infinite hanging (30 minutes max)
        max_duration = 30 * 60  # 30 minutes
        next_tick = start_time + max(1, progress_interval)
        next_resource_check = (
            start_time + 60
        )  # Check resources every minute (more frequent if memory high)
        next_partial_save = start_time + 120  # Save partial results every 2 minutes
        stuck_warning_shown = False
        last_memory_percent = 0  # Track last memory reading to adjust check frequency

        while process.poll() is None:
            now = time.time()
            elapsed = now - start_time

            # Check for interrupt request
            if _interrupt_requested:
                print(
                    f"\n{YELLOW}[INTERRUPT]{RESET} Interrupt requested - terminating gracefully..."
                )
                # Collect output before saving
                output_text = (
                    "".join(_captured_output_lines) if _captured_output_lines else None
                )
                save_partial_results(
                    junit_xml_path,
                    interrupted=True,
                    output_text=output_text,
                    test_context=_current_test_context,
                )
                # Kill entire process tree (especially important for pytest-xdist workers on Windows)
                if sys.platform == "win32":
                    kill_process_tree_windows(process.pid)
                else:
                    process.terminate()
                shutdown_start = time.time()
                while process.poll() is None and (time.time() - shutdown_start) < 5:
                    time.sleep(0.1)
                if process.poll() is None:
                    # Force kill if still running
                    if sys.platform == "win32":
                        kill_process_tree_windows(process.pid)
                    else:
                        process.kill()
                break

            # Check for timeout
            if elapsed > max_duration:
                print(
                    f"\n{RED}[ERROR]{RESET} {description} exceeded maximum duration ({max_duration}s) - terminating"
                )
                save_partial_results(
                    junit_xml_path, interrupted=True, test_context=_current_test_context
                )
                # Kill entire process tree (especially important for pytest-xdist workers on Windows)
                if sys.platform == "win32":
                    kill_process_tree_windows(process.pid)
                else:
                    process.terminate()
                # Wait a bit for graceful shutdown (use polling since wait() timeout may not be available)
                shutdown_start = time.time()
                while process.poll() is None and (time.time() - shutdown_start) < 5:
                    time.sleep(0.1)
                if process.poll() is None:
                    # Force kill if still running
                    if sys.platform == "win32":
                        kill_process_tree_windows(process.pid)
                    else:
                        process.kill()
                break

            # Check for stuck process (no output for 10 minutes)
            if (
                detect_stuck_process(_last_output_time, now, threshold=600)
                and not stuck_warning_shown
            ):
                print(
                    f"\n{YELLOW}[WARNING]{RESET} Process appears stuck (no output for 10 minutes)"
                )
                print(f"{YELLOW}[WARNING]{RESET} Saving partial results...")
                save_partial_results(
                    junit_xml_path, interrupted=True, test_context=_current_test_context
                )
                stuck_warning_shown = True

            # Monitor resources periodically (more frequently if memory is high)
            if now >= next_resource_check:
                resources = monitor_resources()
                if resources:
                    check_resource_warnings(resources)
                    # Check for critical resource exhaustion - terminate if memory is critically high
                    if check_critical_resources(resources):
                        print(
                            f"\n{RED}[CRITICAL]{RESET} System memory critically high (>98%) - terminating tests to prevent system crash"
                        )
                        print(
                            f"{RED}[CRITICAL]{RESET} Saving partial results before termination..."
                        )
                        # Collect output before saving
                        output_text = (
                            "".join(_captured_output_lines)
                            if _captured_output_lines
                            else None
                        )
                        save_partial_results(
                            junit_xml_path,
                            interrupted=True,
                            output_text=output_text,
                            test_context=_current_test_context,
                        )
                        # Kill entire process tree (especially important for pytest-xdist workers on Windows)
                        if sys.platform == "win32":
                            kill_process_tree_windows(process.pid)
                        else:
                            process.terminate()
                        shutdown_start = time.time()
                        while (
                            process.poll() is None
                            and (time.time() - shutdown_start) < 5
                        ):
                            time.sleep(0.1)
                        if process.poll() is None:
                            # Force kill if still running
                            if sys.platform == "win32":
                                kill_process_tree_windows(process.pid)
                            else:
                                process.kill()
                        break

                    # Adjust check frequency based on memory usage
                    current_memory = resources.get("system_memory_percent", 0)
                    if current_memory > 95:
                        # Check every 15 seconds if memory is critically high
                        next_resource_check = now + 15
                    elif current_memory > 90:
                        # Check every 30 seconds if memory is very high
                        next_resource_check = now + 30
                    else:
                        # Normal check every minute
                        next_resource_check = now + 60
                    last_memory_percent = current_memory
                else:
                    next_resource_check = (
                        now + 60
                    )  # Default check every minute if monitoring unavailable

            # Save partial results periodically (less frequently to reduce file I/O)
            # Only save every 5 minutes during normal runs (not on interrupt - those are saved immediately)
            if now >= next_partial_save:
                save_partial_results(junit_xml_path, interrupted=False)
                next_partial_save = (
                    now + 300
                )  # Save every 5 minutes (reduced from 2 minutes)

                # Also save captured output for worker test assignment extraction
                # This helps identify which tests each worker ran (for memory leak debugging)
                if _captured_output_lines:
                    output_file = Path("tests/logs/pytest_console_output.txt")
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        with open(
                            output_file, "w", encoding="utf-8", errors="replace"
                        ) as f:
                            f.write("".join(_captured_output_lines))
                    except Exception:
                        pass  # Non-critical, don't fail on this

            if now >= next_tick:
                elapsed_int = int(elapsed)
                print(f"[PROGRESS] {description} running for {elapsed_int}s...")
                next_tick += max(1, progress_interval)
            time.sleep(0.5)

        # Wait for process to complete
        process.wait()

        # Wait for output thread to finish
        output_thread.join(timeout=1)

        # Save final captured output for worker test assignment extraction
        # This helps identify which tests each worker ran (for memory leak debugging)
        if _captured_output_lines:
            output_file = Path("tests/logs/pytest_console_output.txt")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(output_file, "w", encoding="utf-8", errors="replace") as f:
                    f.write("".join(_captured_output_lines))
            except Exception:
                pass  # Non-critical, don't fail on this

        # CRITICAL: On Windows, ensure all child processes (pytest-xdist workers) are terminated
        # Even if the main process exited, workers might still be running
        if sys.platform == "win32":
            # Kill process tree to ensure workers are terminated
            try:
                if process.poll() is None:
                    # Process still running - kill it and its children
                    kill_process_tree_windows(process.pid)
                else:
                    # Process exited but workers might be orphaned - kill tree anyway
                    kill_process_tree_windows(process.pid)
            except Exception:
                pass  # Process might already be gone, that's fine

            # Also check for any orphaned pytest worker processes
            cleanup_orphaned_pytest_processes()

            # CRITICAL: Consolidate worker logs even if pytest didn't finish normally
            # When process is forcefully terminated, pytest_sessionfinish may not run
            try:
                # Small delay to ensure workers have closed their file handles
                time.sleep(1.0)  # Longer delay for normal completion
                from tests.conftest import _consolidate_worker_logs

                print(f"{GREEN}[CLEANUP]{RESET} Consolidating worker log files...")
                _consolidate_worker_logs()
                print(f"{GREEN}[CLEANUP]{RESET} Worker log consolidation complete")
            except Exception as e:
                print(
                    f"{YELLOW}[CLEANUP]{RESET} Could not consolidate worker logs: {e}"
                )
                print(
                    f"{YELLOW}[CLEANUP]{RESET} Run manually: python scripts/testing/consolidate_worker_logs.py"
                )

        # Clear global process reference
        _current_process = None
        _current_junit_xml = None

        # Collect all output lines
        while not output_queue.empty():
            try:
                output_lines.append(output_queue.get_nowait())
            except queue.Empty:
                break

        output = "".join(output_lines)
        output_plain = ANSI_ESCAPE_RE.sub("", output)

        summary_counts = {}
        summary_line_matches = re.findall(
            r"={5,}\s*(.+?)\s*={5,}", output_plain, re.MULTILINE
        )
        if summary_line_matches:
            summary_content = summary_line_matches[-1]
            count_matches = re.findall(
                r"(\d+)\s+(failed|passed|skipped|warnings?|deselected|errors?)",
                summary_content,
                re.IGNORECASE,
            )
            for count_str, label in count_matches:
                key = label.lower()
                if key in ("warning", "warnings"):
                    key = "warnings"
                elif key in ("error", "errors"):
                    key = "errors"
                summary_counts[key] = int(count_str)

        # Parse results from JUnit XML (with atomic read to ensure consistency)
        # Use atomic file operations: read from temp location first
        results = {}
        try:
            # Ensure file is flushed before reading
            if os.path.exists(junit_xml_path):
                # On Windows, ensure file handle is closed
                time.sleep(0.1)  # Small delay to ensure file is written
                results = parse_junit_xml(junit_xml_path)
        except Exception as e:
            print(f"{YELLOW}[WARNING]{RESET} Could not parse JUnit XML: {e}")
            # Try to save partial results anyway
            if os.path.exists(junit_xml_path):
                save_partial_results(junit_xml_path, interrupted=_interrupt_requested)

        # Ensure expected keys exist
        results.setdefault("warnings", 0)
        results.setdefault("deselected", 0)

        # Update results with parsed summary counts
        for key, value in summary_counts.items():
            results[key] = value

        # Parse warnings/failures details from pytest output
        warnings_text = ""
        failures_text = ""

        # Extract warnings count from pytest output (e.g., "10 warnings in 143.99s")
        # Look for pattern like "1 failed, 3023 passed, 1 skipped, 10 warnings in 143.99s"
        warnings_match = re.search(r"(\d+)\s+warnings?\s+in\s+[\d.]+s", output_plain)
        if not warnings_match:
            # Also try pattern without "in" (some pytest versions)
            warnings_match = re.search(r",\s*(\d+)\s+warnings?\s+in", output_plain)
        if warnings_match:
            results["warnings"] = int(warnings_match.group(1))

        # Extract failures from short test summary
        # Try multiple patterns to catch different pytest output formats
        failures_text = ""

        # Pattern 1: Standard pytest format "FAILED tests/path.py::TestClass::test_method"
        failures_section = re.search(
            r"FAILED\s+(.+?)(?=\n\n|\n===|$)", output_plain, re.DOTALL
        )
        if failures_section:
            failures_text = failures_section.group(1).strip()
        else:
            # Pattern 2: Look for "FAILURES" section header followed by test names
            failures_header = re.search(
                r"FAILURES\s*=\s*={3,}\s*\n(.+?)(?=\n={3,}|\n\n|$)",
                output_plain,
                re.DOTALL,
            )
            if failures_header:
                failures_text = failures_header.group(1).strip()
            else:
                # Pattern 3: Extract individual FAILED lines (for parallel execution)
                failed_lines = re.findall(r"FAILED\s+([^\s]+::[^\s]+)", output_plain)
                if failed_lines:
                    failures_text = "\n".join(failed_lines)

        # Also extract failure details from JUnit XML if available (even when interrupted)
        failure_details = []
        if os.path.exists(junit_xml_path):
            try:
                failure_details = extract_failures_from_junit_xml(junit_xml_path)
            except Exception:
                pass  # Ignore errors extracting failures

        duration = time.time() - start_time

        # Detect known pytest teardown false-negative on Windows where all tests pass,
        # but pytest exits non-zero due cleanup_dead_symlinks PermissionError.
        is_windows_teardown_permission_false_negative = (
            process.returncode != 0
            and "cleanup_dead_symlinks" in output_plain
            and "PermissionError: [WinError 5] Access is denied" in output_plain
            and results.get("failed", 0) == 0
            and results.get("errors", 0) == 0
            and results.get("passed", 0) > 0
        )
        effective_returncode = (
            0 if is_windows_teardown_permission_false_negative else process.returncode
        )

        # Print status message
        if _interrupt_requested:
            print(
                f"\n{YELLOW}[INTERRUPTED]{RESET} {description} was interrupted after {duration}s"
            )
            print(
                f"{YELLOW}[INTERRUPTED]{RESET} Partial results saved to {_partial_results_file}"
            )
        elif effective_returncode == 0:
            print(
                f"\n{GREEN}[SUCCESS]{RESET} {description} completed successfully in {duration}s"
            )
            if is_windows_teardown_permission_false_negative:
                print(
                    f"{YELLOW}[WARNING]{RESET} Pytest exited non-zero due Windows temp cleanup permissions, but test results were clean."
                )
        else:
            print(
                f"\n{RED}[FAILED]{RESET} {description} failed with exit code {process.returncode} after {duration}s"
            )
            if process.returncode in (-1073741515, 3221226505):
                print(
                    f"{RED}[CRASH]{RESET} Windows process crash detected (0xC0000135 / STATUS_DLL_NOT_FOUND)."
                )
                print(
                    f"{YELLOW}[CRASH]{RESET} This is typically an environment/DLL issue (often Qt platform plugin loading)."
                )
            # Save partial results on failure
            save_partial_results(
                junit_xml_path, interrupted=False, test_context=_current_test_context
            )

        # Return dict with all information
        return {
            "success": effective_returncode == 0 and not _interrupt_requested,
            "output": output,
            "results": results,
            "duration": duration,
            "warnings": warnings_text,
            "failures": failures_text,
            "failure_details": failure_details,  # Include structured failure details
            "interrupted": _interrupt_requested,
        }
    finally:
        # Save final results before cleanup (atomic write)
        if os.path.exists(junit_xml_path):
            try:
                # Save to backup location with timestamp (using consolidated backups directory)
                timestamp = now_timestamp_filename()
                backup_path = _backups_dir / f"junit_results_{timestamp}.xml"

                # Atomic copy: write to temp first, then rename
                import shutil

                temp_backup = str(backup_path) + ".tmp"
                shutil.copy2(junit_xml_path, temp_backup)
                os.rename(temp_backup, str(backup_path))

                # Keep only last 5 backups
                backups = sorted(
                    _backups_dir.glob("junit_results_*.xml"), key=os.path.getmtime
                )
                if len(backups) > 5:
                    for old_backup in backups[:-5]:
                        try:
                            old_backup.unlink()
                        except Exception:
                            pass
            except Exception as e:
                print(f"{YELLOW}[WARNING]{RESET} Could not save result backup: {e}")

        # Clean up temp file (but keep it if interrupted for recovery)
        if not _interrupt_requested:
            try:
                if os.path.exists(junit_xml_path):
                    os.unlink(junit_xml_path)
            except:
                pass
        # CRITICAL: On Windows, ensure all processes are killed even if there was an exception
        if sys.platform == "win32" and _current_process:
            try:
                if _current_process.poll() is None:
                    # Process still running - kill it and its children
                    kill_process_tree_windows(_current_process.pid)
                else:
                    # Process exited but workers might be orphaned - kill tree anyway
                    kill_process_tree_windows(_current_process.pid)
            except Exception:
                pass

            # Also check for any orphaned pytest worker processes
            cleanup_orphaned_pytest_processes()

            # CRITICAL: Try to consolidate worker logs even on exception
            # This ensures logs are consolidated even if something went wrong
            try:
                time.sleep(1.0)  # Delay to allow workers to close file handles
                from tests.conftest import _consolidate_worker_logs

                _consolidate_worker_logs()
            except Exception:
                pass  # Don't fail if consolidation doesn't work

        # Clear global references
        _current_process = None
        _current_junit_xml = None


@handle_errors("setting up test logger", default_return=None)
def setup_test_logger():
    """
    Set up logger for test duration logging.

    Creates a logger for test run duration logging and ensures the tests/logs
    directory exists. Returns a configured logger instance.

    Returns:
        logging.Logger: Configured logger instance for test runs
    """
    logger = logging.getLogger("mhm_tests.run_tests")
    logger.setLevel(logging.INFO)

    # Only add handler if one doesn't exist
    if not logger.handlers:
        # Ensure tests/logs directory exists
        log_dir = Path("tests/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Add file handler for test_run.log
        log_file = log_dir / "test_run.log"
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Prevent propagation to root logger
        logger.propagate = False

    return logger


@handle_errors("printing combined test summary", default_return=None)
def print_combined_summary(
    parallel_results: dict | None,
    no_parallel_results: dict | None,
    description: str,
):
    """
    Print a combined summary of test results from both parallel and serial runs.

    Args:
        parallel_results: Results dict from parallel test run (or None if not run)
        no_parallel_results: Results dict from serial test run (or None if not run)
        description: Test mode description
    """
    # Extract results from both runs
    parallel_res = (
        parallel_results.get("results", {})
        if parallel_results and isinstance(parallel_results, dict)
        else {}
    )
    no_parallel_res = (
        no_parallel_results.get("results", {})
        if no_parallel_results and isinstance(no_parallel_results, dict)
        else {}
    )

    # Combine results
    combined = {
        "passed": parallel_res.get("passed", 0) + no_parallel_res.get("passed", 0),
        "failed": parallel_res.get("failed", 0) + no_parallel_res.get("failed", 0),
        "skipped": parallel_res.get("skipped", 0) + no_parallel_res.get("skipped", 0),
        "warnings": parallel_res.get("warnings", 0)
        + no_parallel_res.get("warnings", 0),
        "errors": parallel_res.get("errors", 0) + no_parallel_res.get("errors", 0),
        "deselected": parallel_res.get("deselected", 0)
        + no_parallel_res.get("deselected", 0),
    }
    combined["total"] = (
        combined["passed"]
        + combined["failed"]
        + combined["skipped"]
        + combined["errors"]
    )

    # Calculate total duration (ensure floats for decimal precision)
    parallel_duration = (
        float(parallel_results.get("duration", 0))
        if parallel_results and isinstance(parallel_results, dict)
        else 0.0
    )
    no_parallel_duration = (
        float(no_parallel_results.get("duration", 0))
        if no_parallel_results and isinstance(no_parallel_results, dict)
        else 0.0
    )
    total_duration = parallel_duration + no_parallel_duration

    # Collect all warnings and failures
    all_warnings = []
    all_failures = []

    if parallel_results and isinstance(parallel_results, dict):
        if parallel_results.get("warnings"):
            all_warnings.append(("Parallel Tests", parallel_results["warnings"]))
        if parallel_results.get("failures"):
            all_failures.append(("Parallel Tests", parallel_results["failures"]))

    if no_parallel_results and isinstance(no_parallel_results, dict):
        if no_parallel_results.get("warnings"):
            all_warnings.append(("Serial Tests", no_parallel_results["warnings"]))
        if no_parallel_results.get("failures"):
            all_failures.append(("Serial Tests", no_parallel_results["failures"]))

    # Print combined summary
    print(f"\n{'='*80}")
    print(f"COMBINED TEST RESULTS SUMMARY")
    print(f"{'='*80}")
    print(f"Mode: {description}")
    print(f"\nTest Statistics:")
    print(f"  Total Tests:  {combined['total']}")
    print(f"  Passed:       {combined['passed']}")
    print(f"  Failed:       {combined['failed']}")
    print(f"  Skipped:      {combined['skipped']}")
    print(f"  Deselected:   {combined['deselected']}")
    print(f"  Warnings:     {combined['warnings']}")

    # Set up logger for duration logging
    test_logger = setup_test_logger()

    # Show breakdown if we ran tests in two phases (parallel + serial)
    if no_parallel_results and isinstance(no_parallel_results, dict):
        print(f"\nBreakdown:")
        p_passed = parallel_res.get("passed", 0)
        p_failed = parallel_res.get("failed", 0)
        p_skipped = parallel_res.get("skipped", 0)
        p_warnings = parallel_res.get("warnings", 0)
        p_deselected = parallel_res.get("deselected", 0)
        p_interrupted = (
            parallel_results.get("interrupted", False)
            if parallel_results and isinstance(parallel_results, dict)
            else False
        )
        s_passed = no_parallel_res.get("passed", 0)
        s_failed = no_parallel_res.get("failed", 0)
        s_skipped = no_parallel_res.get("skipped", 0)
        s_warnings = no_parallel_res.get("warnings", 0)
        s_deselected = no_parallel_res.get("deselected", 0)

        # Format parallel tests line with interruption indicator
        parallel_status = ""
        if p_interrupted:
            parallel_status = f" {YELLOW}[INTERRUPTED]{RESET}"
        parallel_line = f"  Parallel Tests:    {p_passed} passed, {p_failed} failed, {p_skipped} skipped, {p_deselected} deselected, {p_warnings} warnings ({parallel_duration}s){parallel_status}"
        print(parallel_line)
        print(
            f"  Serial Tests:      {s_passed} passed, {s_failed} failed, {s_skipped} skipped, {s_deselected} deselected, {s_warnings} warnings ({no_parallel_duration}s)"
        )

        print(f"\nTotal Duration: {total_duration}s")

        # Log durations and test counts to test log file
        p_total = p_passed + p_failed + p_skipped
        s_total = s_passed + s_failed + s_skipped
        total_tests = p_total + s_total
        test_logger.info(
            f"TEST SUITE DURATION - Parallel: {parallel_duration:.2f}s, Serial: {no_parallel_duration:.2f}s, Total: {total_duration:.2f}s"
        )
        test_logger.info(
            f"TEST SUITE COUNTS - Parallel: {p_total} tests ({p_passed} passed, {p_failed} failed, {p_skipped} skipped), Serial: {s_total} tests ({s_passed} passed, {s_failed} failed, {s_skipped} skipped), Total: {total_tests} tests ({combined['passed']} passed, {combined['failed']} failed, {combined['skipped']} skipped)"
        )
    elif parallel_duration > 0:
        # Single run (--no-parallel was used)
        print(f"\nDuration: {parallel_duration}s")

        # Log duration and test counts to test log file
        p_total = (
            parallel_res.get("passed", 0)
            + parallel_res.get("failed", 0)
            + parallel_res.get("skipped", 0)
        )
        test_logger.info(
            f"TEST SUITE DURATION - Total: {parallel_duration:.2f}s (single run mode)"
        )
        test_logger.info(
            f"TEST SUITE COUNTS - Total: {p_total} tests ({parallel_res.get('passed', 0)} passed, {parallel_res.get('failed', 0)} failed, {parallel_res.get('skipped', 0)} skipped)"
        )

    # Show failures details
    # Collect failure details from both sources: failures_text and failure_details
    # Priority: Use failure_details from JUnit XML (most reliable), fall back to failures_text
    failure_details_to_print = []
    seen_tests = set()  # Track which tests we've already printed to avoid duplicates

    # First, add structured failure details from JUnit XML (most reliable source)
    if parallel_results and isinstance(parallel_results, dict):
        parallel_failure_details = parallel_results.get("failure_details", [])
        if parallel_failure_details:
            for failure_detail in parallel_failure_details:
                test_name = failure_detail.get("test", "Unknown test")
                if test_name not in seen_tests:
                    seen_tests.add(test_name)
                    message = failure_detail.get("message", "")
                    details = failure_detail.get("details", "")
                    failure_info = f"{test_name}"
                    if message:
                        failure_info += (
                            f"\n  Message: {message[:200]}"  # Truncate long messages
                        )
                    if details:
                        # Truncate very long details but keep first few lines
                        details_lines = details.split("\n")[:10]  # First 10 lines
                        details_preview = "\n".join(details_lines)
                        if len(details) > len(details_preview):
                            details_preview += "\n  ... (truncated)"
                        failure_info += f"\n  Details:\n{details_preview}"
                    failure_details_to_print.append(("Parallel Tests", failure_info))

    if no_parallel_results and isinstance(no_parallel_results, dict):
        serial_failure_details = no_parallel_results.get("failure_details", [])
        if serial_failure_details:
            for failure_detail in serial_failure_details:
                test_name = failure_detail.get("test", "Unknown test")
                if test_name not in seen_tests:
                    seen_tests.add(test_name)
                    message = failure_detail.get("message", "")
                    details = failure_detail.get("details", "")
                    failure_info = f"{test_name}"
                    if message:
                        failure_info += (
                            f"\n  Message: {message[:200]}"  # Truncate long messages
                        )
                    if details:
                        # Truncate very long details but keep first few lines
                        details_lines = details.split("\n")[:10]  # First 10 lines
                        details_preview = "\n".join(details_lines)
                        if len(details) > len(details_preview):
                            details_preview += "\n  ... (truncated)"
                        failure_info += f"\n  Details:\n{details_preview}"
                    failure_details_to_print.append(("Serial Tests", failure_info))

    # Also add failures from failures_text (parsed from output) if not already covered
    if all_failures:
        for source, failure_text in all_failures:
            if failure_text:
                # Extract test names from failure_text to check for duplicates
                test_names_in_text = re.findall(r"([^\s]+::[^\s]+)", failure_text)
                # Only add if we haven't seen these tests already
                if not any(test_name in seen_tests for test_name in test_names_in_text):
                    failure_details_to_print.append((source, failure_text))

    # Print all failures
    if failure_details_to_print:
        print(f"\n{RED}FAILURES:{RESET}")
        for source, failure_info in failure_details_to_print:
            print(f"\n{RED}From {source}:{RESET}")
            print(failure_info)
    elif combined["failed"] > 0:
        # If we have failures but couldn't extract details, at least show the count
        print(f"\n{RED}FAILURES:{RESET}")
        print(
            f"  {combined['failed']} test(s) failed, but failure details could not be extracted."
        )
        print(
            f"  Check {_partial_results_file} or {_backups_dir.name}/ for detailed failure information."
        )

    # Show warnings details
    if all_warnings:
        print(f"\nWARNINGS:")
        for source, warning_text in all_warnings:
            if warning_text:
                print(f"\nFrom {source}:")
                print(warning_text)

    # Show interruption notice if parallel tests were interrupted (before final summary)
    if (
        parallel_results
        and isinstance(parallel_results, dict)
        and parallel_results.get("interrupted", False)
    ):
        print(f"\n{YELLOW}⚠️  INTERRUPTION DETECTED:{RESET}")
        print(f"  Parallel tests were interrupted before completion.")
        print(f"  Partial results saved to: {_partial_results_file}")
        print(f"  Check {_backups_dir.name}/ directory for timestamped copies.")

    # Final summary line in pytest format - match pytest's exact format
    print()
    parallel_deselected = parallel_res.get("deselected", 0)
    serial_deselected = (
        no_parallel_res.get("deselected", 0)
        if no_parallel_results and isinstance(no_parallel_results, dict)
        else None
    )
    if serial_deselected is None:
        include_deselected_in_summary = parallel_deselected > 0
    else:
        include_deselected_in_summary = (
            parallel_deselected > 0 and serial_deselected > 0
        )

    summary_parts = [
        f"{RED}{combined['failed']} failed{RESET}",
        f"{GREEN}{combined['passed']} passed{RESET}",
    ]
    if include_deselected_in_summary:
        summary_parts.append(f"{YELLOW}{combined['deselected']} deselected{RESET}")
    if combined["skipped"] > 0:
        summary_parts.append(f"{YELLOW}{combined['skipped']} skipped{RESET}")
    summary_parts.append(f"{YELLOW}{combined['warnings']} warnings{RESET}")

    summary_text = ", ".join(summary_parts)

    # Format duration like pytest: "143.99s (0:02:23)"
    duration_decimal = f"{total_duration:.2f}s"
    # Calculate human-readable format (hours:minutes:seconds)
    hours = int(total_duration // 3600)
    minutes = int((total_duration % 3600) // 60)
    seconds = int(total_duration % 60)
    duration_human = f"({hours}:{minutes:02d}:{seconds:02d})"
    duration_str = f"{duration_decimal} {duration_human}"

    # Color-code border based on result state
    if combined["failed"] > 0:
        border_color = RED
    elif combined["warnings"] > 0:
        border_color = YELLOW
    else:
        border_color = GREEN

    border = f"{border_color}{'='*10}{RESET}"
    duration_segment = f"{border_color}in {duration_str}{RESET}"

    # Match pytest's format with colored components
    summary_line = f"{border} {summary_text}, {duration_segment} {border}"
    print(summary_line)
    print()


@handle_errors("printing test mode information", default_return=None)
def print_test_mode_info():
    """Print helpful information about test modes."""
    print("\n" + "=" * 60)
    print("MHM TEST RUNNER - Available Modes")
    print("=" * 60)
    print("Test Modes:")
    print("  all         - Run ALL tests (default)")
    print("  fast        - Unit tests only (excluding slow tests)")
    print("  unit        - Unit tests only")
    print("  integration - Integration tests only")
    print("  behavior    - Behavior tests (excluding slow tests)")
    print("  ui          - UI tests (excluding slow tests)")
    print("  slow        - Slow tests only")
    print("\nOptions:")
    print("  --verbose   - Verbose output")
    print("  --no-parallel - Disable parallel execution (parallel enabled by default)")
    print(
        "  --workers N - Number of parallel workers (default: 2, or 'auto' for optimal)"
    )
    print("  --coverage  - Run with coverage reporting")
    print("  --durations-all - Show timing for all tests")
    print("  --no-shim   - Disable test data shim (for burn-in validation)")
    print(
        "  --random-order - Use random test order (for order independence validation)"
    )
    print(
        "  --burnin-mode - Enable burn-in mode (combines --no-shim and --random-order)"
    )
    print("\nExamples:")
    print("  python run_tests.py                    # Run all tests in parallel")
    print("  python run_tests.py --mode fast        # Quick unit tests only")
    print("  python run_tests.py --mode all --verbose # All tests with verbose output")
    print("  python run_tests.py --no-parallel      # Disable parallel execution")
    print("  python run_tests.py --workers 4       # Use 4 parallel workers")
    print(
        "  python run_tests.py --burnin-mode     # Validation run (no shim, random order)"
    )
    print("=" * 60)


@handle_errors("running static logging check", default_return=False)
def run_static_logging_check() -> bool:
    """Run the static logging enforcement script before executing tests."""
    script_path = (
        Path(__file__).parent / "scripts" / "static_checks" / "check_channel_loggers.py"
    )
    if not script_path.exists():
        print(f"[STATIC CHECK] Missing script: {script_path}")
        return False

    result = subprocess.run(
        [sys.executable, str(script_path)], capture_output=True, text=True
    )
    if result.returncode != 0:
        print("[STATIC CHECK] Logging style violations detected:")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return False

    if result.stdout:
        print(result.stdout.strip())
    return True


@handle_errors("cleaning stale test artifacts", user_friendly=False, default_return=None)
def cleanup_stale_test_artifacts() -> None:
    """Best-effort cleanup for stale pytest/build artifacts that commonly accumulate on Windows."""
    root = Path(__file__).parent
    removed = 0

    exact_dirs = [
        ".pytest_cache",
        ".pytest_tmp",
        ".tmp_devtools_pyfiles",
        ".tmp_pytest",
        "htmlcov",
        "mhm.egg-info",
    ]
    glob_patterns = [
        ".pytest-tmp-*",
    ]

    for rel in exact_dirs:
        target = root / rel
        if not target.exists():
            continue
        try:
            shutil.rmtree(target)
            removed += 1
        except Exception:
            # Locked files/directories are expected on Windows; skip safely.
            pass

    for pattern in glob_patterns:
        for target in root.glob(pattern):
            if not target.exists() or not target.is_dir():
                continue
            try:
                shutil.rmtree(target)
                removed += 1
            except Exception:
                pass

    if removed:
        print(f"[CLEANUP] Removed {removed} stale artifact directory(s) before test run")


def main():
    """
    Main entry point for MHM test runner.

    Parses command-line arguments and executes pytest with appropriate configuration
    based on the selected test mode (all, fast, unit, integration, behavior, ui, slow).

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(description="MHM Test Runner")
    parser.add_argument(
        "--mode",
        choices=["fast", "unit", "integration", "behavior", "ui", "all", "slow"],
        default="all",
        help="Test execution mode (default: all)",
    )
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel test execution (parallel is enabled by default)",
    )
    parser.add_argument(
        "--workers",
        type=str,
        default="auto",
        help="Number of parallel workers (default: auto to let pytest-xdist decide, or specify a number like 2, 4, etc.)",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--coverage", action="store_true", help="Run with coverage reporting"
    )
    parser.add_argument(
        "--progress-interval",
        type=int,
        default=30,
        help="Print progress every N seconds (default: 30)",
    )
    parser.add_argument(
        "--durations-all",
        action="store_true",
        help="Ask pytest to report durations for all tests at the end",
    )
    parser.add_argument(
        "--no-shim",
        action="store_true",
        help="Disable test data shim (ENABLE_TEST_DATA_SHIM=0) for burn-in validation",
    )
    parser.add_argument(
        "--random-order",
        action="store_true",
        help="Use truly random test order (not fixed seed) for order independence validation",
    )
    parser.add_argument(
        "--burnin-mode",
        action="store_true",
        help="Enable burn-in validation mode (combines --no-shim and --random-order)",
    )
    parser.add_argument(
        "--help-modes",
        action="store_true",
        help="Show detailed information about test modes",
    )
    parser.add_argument(
        "--skip-static-logging-check",
        action="store_true",
        help="Skip the static logging enforcement preflight (not recommended)",
    )
    parser.add_argument(
        "--resource-warnings",
        action="store_true",
        default=True,
        help="Enable resource usage warnings (default: enabled)",
    )
    parser.add_argument(
        "--no-resource-warnings",
        dest="resource_warnings",
        action="store_false",
        help="Disable resource usage warnings",
    )
    parser.add_argument(
        "--critical-memory-limit",
        type=float,
        default=98.0,
        help="System memory percentage threshold for automatic termination (default: 98.0%%)",
    )
    parser.add_argument(
        "--no-auto-terminate",
        dest="auto_terminate",
        action="store_false",
        default=True,
        help="Disable automatic termination on critical memory usage",
    )

    args = parser.parse_args()

    # Set resource warnings flag
    global _resource_warnings_enabled
    # args.resource_warnings is True by default, False if --no-resource-warnings is used
    _resource_warnings_enabled = args.resource_warnings

    # Set critical memory handling
    global _critical_memory_limit, _auto_terminate_enabled
    _critical_memory_limit = args.critical_memory_limit
    _auto_terminate_enabled = args.auto_terminate

    if not _auto_terminate_enabled:
        print(
            f"[INFO] Automatic termination on critical memory disabled (use --critical-memory-limit to set threshold)"
        )
    else:
        print(
            f"[INFO] Automatic termination enabled at {_critical_memory_limit}% system memory"
        )

    # Show help modes if requested
    if args.help_modes:
        print_test_mode_info()
        return 0

    if args.skip_static_logging_check:
        print("[STATIC CHECK] Skipped by user request")
    elif not run_static_logging_check():
        return 1

    # Enforce safe defaults for Windows console
    os.environ.setdefault("PYTHONUTF8", "1")

    # Best-effort cleanup of stale pytest/build artifact directories.
    cleanup_stale_test_artifacts()

    # Handle burn-in mode (combines --no-shim and --random-order)
    if args.burnin_mode:
        args.no_shim = True
        args.random_order = True
        print("[BURN-IN MODE] Enabled: --no-shim and --random-order for validation")

    # Ensure test data shim is enabled by default for CI/local runs unless explicitly disabled
    if args.no_shim:
        os.environ["ENABLE_TEST_DATA_SHIM"] = "0"
        print("[BURN-IN] Test data shim disabled (ENABLE_TEST_DATA_SHIM=0)")
    else:
        os.environ.setdefault("ENABLE_TEST_DATA_SHIM", "1")

    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]

    # Force pytest temp/cache paths into repo-local directories to avoid
    # Windows permission issues in %LOCALAPPDATA% Temp and stale global cache dirs.
    run_id = now_timestamp_filename()
    pytest_root = Path(".tmp_pytest_runner")
    parallel_basetemp = pytest_root / run_id / "parallel"
    serial_basetemp = pytest_root / run_id / "serial"
    pytest_cache_dir = Path(".pytest_tmp_cache")
    parallel_basetemp.mkdir(parents=True, exist_ok=True)
    serial_basetemp.mkdir(parents=True, exist_ok=True)
    pytest_cache_dir.mkdir(parents=True, exist_ok=True)
    cmd.extend(
        [
            "--basetemp",
            str(parallel_basetemp),
            "-o",
            f"cache_dir={pytest_cache_dir}",
        ]
    )

    # Track if we need to exclude no_parallel tests from parallel execution
    exclude_no_parallel = False

    # Add parallel execution (enabled by default, can be disabled with --no-parallel)
    # When parallel is enabled, exclude no_parallel tests from parallel execution
    # They will be run separately in serial mode
    if not args.no_parallel:
        exclude_no_parallel = True

        # Use 'auto' to let pytest-xdist determine optimal worker count, or use specified number
        # CRITICAL: Limit auto workers to prevent OOM errors - use CPU count but cap at 6
        # Default to 2 workers for safety (some tests may have race conditions with more workers)
        # User reported 6 workers worked fine until recently, so allow up to 6
        if args.workers == "auto":
            import multiprocessing

            cpu_count = multiprocessing.cpu_count()
            # Reduce workers to prevent memory issues - cap at 4 workers instead of 6
            # For systems with 12+ CPUs, use 4 workers; for 8 CPUs use 3; for 4 CPUs use 2
            max_workers = min(4, max(2, cpu_count // 3))
            cmd.extend(["-n", str(max_workers)])
            print(
                f"[INFO] Auto-detected {cpu_count} CPUs, using {max_workers} workers to prevent OOM"
            )
        else:
            try:
                # Validate that workers is a valid number if not "auto"
                num_workers = int(args.workers)
                if num_workers < 1:
                    print(
                        f"[WARNING] Invalid worker count: {num_workers}. Using 2 instead."
                    )
                    cmd.extend(["-n", "2"])
                else:
                    cmd.extend(["-n", str(num_workers)])
            except ValueError:
                print(
                    f"[WARNING] Invalid worker value: {args.workers}. Using 2 instead."
                )
                cmd.extend(["-n", "2"])

    # Add verbose output
    if args.verbose:
        cmd.append("-v")

    # Set test environment variables
    os.environ["DISABLE_LOG_ROTATION"] = "1"  # Prevent log rotation issues during tests

    # Handle test order randomization
    addopts = os.environ.get("PYTEST_ADDOPTS", "")
    has_seed = "--randomly-seed" in addopts or any(
        arg.startswith("--randomly-seed") for arg in sys.argv
    )

    if args.random_order:
        # Use truly random order (pytest-randomly will generate a random seed)
        # Don't add --randomly-seed, let pytest-randomly use a random seed
        print("[BURN-IN] Using random test order (no fixed seed)")
    elif not has_seed:
        # Default: use fixed seed for deterministic runs
        cmd.extend(
            ["--randomly-seed=12345"]
        )  # default stable seed for order independence verification

    # Add coverage if requested
    if args.coverage:
        cmd.extend(
            [
                "--cov=core",
                "--cov=communication",
                "--cov=ui",
                "--cov=tasks",
                "--cov=user",
                "--cov=ai",
                "--cov-report=html:tests/coverage_html",
                "--cov-report=term",
            ]
        )
        # Set environment variable to control coverage data file location
        os.environ["COVERAGE_FILE"] = "tests/.coverage"

    # Optional per-test durations report
    if args.durations_all:
        cmd.append("--durations=0")

    # Track marker filters for later use in no_parallel test run
    mode_marker_filter = None

    # Add test selection based on mode
    if args.mode == "fast":
        # Fast tests: unit tests only
        cmd.extend(["tests/unit/"])
        mode_marker_filter = "not slow"
        description = "Fast Tests (Unit tests only, excluding slow tests)"

    elif args.mode == "unit":
        # Unit tests
        cmd.extend(["tests/unit/"])
        description = "Unit Tests"

    elif args.mode == "integration":
        # Integration tests
        cmd.extend(["tests/integration/"])
        description = "Integration Tests"

    elif args.mode == "behavior":
        # Behavior tests
        cmd.extend(["tests/behavior/"])
        mode_marker_filter = "not slow"
        description = "Behavior Tests (excluding slow tests)"

    elif args.mode == "ui":
        # UI tests
        cmd.extend(["tests/ui/"])
        mode_marker_filter = "not slow"
        description = "UI Tests (excluding slow tests)"

    elif args.mode == "slow":
        # Slow tests only
        cmd.extend(["tests/"])
        mode_marker_filter = "slow"
        description = "Slow Tests Only"

    elif args.mode == "all":
        # All tests
        cmd.extend(["tests/"])
        description = "All Tests (Unit, Integration, Behavior, UI)"

    # Add marker filters (combine mode filter with no_parallel and e2e exclusion if needed)
    marker_parts = []
    if mode_marker_filter:
        marker_parts.append(mode_marker_filter)
    if exclude_no_parallel:
        marker_parts.append("not no_parallel")
    # Always exclude e2e tests from regular runs (they are slow and should only run explicitly)
    marker_parts.append("not e2e")

    if marker_parts:
        # Combine all marker filters with "and"
        combined_filter = " and ".join(marker_parts)
        cmd.extend(["-m", combined_filter])

    # Print clear information about what we're running
    print(f"\nMHM Test Runner")
    print(f"Mode: {args.mode}")
    print(f"Description: {description}")
    if not args.no_parallel:
        print(f"Parallel: Yes ({args.workers} workers)")
        print(
            f"Note: Tests marked with @pytest.mark.no_parallel will run separately in serial mode"
        )
    else:
        print(f"Parallel: No (disabled)")
    if args.verbose:
        print(f"Verbose: Yes")
    if args.coverage:
        print(f"Coverage: Yes")
    if args.no_shim:
        print(f"Test Data Shim: Disabled (burn-in validation)")
    if args.random_order:
        print(f"Test Order: Random (burn-in validation)")

    print(f"\nPytest Configuration:")
    print(f"  Platform: {sys.platform}")
    print(f"  Python: {sys.version.split()[0]}")
    if not args.random_order and not has_seed:
        print(f"  Random Seed: 12345 (fixed for reproducibility)")

    # Build test context for partial results
    try:
        import pytest

        pytest_version = pytest.__version__
    except (ImportError, AttributeError):
        pytest_version = "unknown"

    base_test_context = {
        "mode": args.mode,
        "description": description,
        "parallel": not args.no_parallel,
        "workers": args.workers if not args.no_parallel else None,
        "platform": sys.platform,
        "python_version": sys.version.split()[0],
        "pytest_version": pytest_version,
        "random_seed": "12345" if not args.random_order and not has_seed else None,
        "random_order": args.random_order,
    }

    # Run the tests
    parallel_test_context = {**base_test_context, "phase": "parallel"}
    parallel_results = run_command(
        cmd,
        description,
        progress_interval=args.progress_interval,
        test_context=parallel_test_context,
    )
    success = parallel_results["success"]

    # If parallel execution was enabled, also run no_parallel tests separately in serial mode
    no_parallel_results = None
    if not args.no_parallel:
        # Create a separate command for no_parallel tests (serial execution)
        no_parallel_cmd = [sys.executable, "-m", "pytest"]
        no_parallel_cmd.extend(
            [
                "--basetemp",
                str(serial_basetemp),
                "-o",
                f"cache_dir={pytest_cache_dir}",
            ]
        )

        # Build marker filter: combine no_parallel with mode filter if present
        # Always exclude e2e tests (they are slow and should only run explicitly)
        if mode_marker_filter:
            # Combine markers: e.g., "no_parallel and not slow and not e2e" or "no_parallel and slow and not e2e"
            no_parallel_cmd.extend(
                ["-m", f"no_parallel and {mode_marker_filter} and not e2e"]
            )
        else:
            no_parallel_cmd.extend(
                ["-m", "no_parallel and not e2e"]
            )  # Only run no_parallel tests, exclude e2e

        # Copy test selection from main command (directory paths)
        if args.mode == "fast":
            no_parallel_cmd.extend(["tests/unit/"])
        elif args.mode == "unit":
            no_parallel_cmd.extend(["tests/unit/"])
        elif args.mode == "integration":
            no_parallel_cmd.extend(["tests/integration/"])
        elif args.mode == "behavior":
            no_parallel_cmd.extend(["tests/behavior/"])
        elif args.mode == "ui":
            no_parallel_cmd.extend(["tests/ui/"])
        elif args.mode == "slow":
            no_parallel_cmd.extend(["tests/"])
        elif args.mode == "all":
            no_parallel_cmd.extend(["tests/"])

        # Copy other options
        if args.verbose:
            no_parallel_cmd.append("-v")
        if args.coverage:
            no_parallel_cmd.extend(
                [
                    "--cov=core",
                    "--cov=communication",
                    "--cov=ui",
                    "--cov=tasks",
                    "--cov=user",
                    "--cov=ai",
                    "--cov-report=html:tests/coverage_html",
                    "--cov-report=term",
                ]
            )
        if args.durations_all:
            no_parallel_cmd.append("--durations=0")

        # Copy randomization settings
        if args.random_order:
            pass  # Don't add seed for random order
        elif not has_seed:
            no_parallel_cmd.extend(["--randomly-seed=12345"])

        print(
            f"\n[NO_PARALLEL] Running tests marked with @pytest.mark.no_parallel in serial mode..."
        )
        no_parallel_test_context = {
            **base_test_context,
            "phase": "serial",
            "parallel": False,
        }
        no_parallel_results = run_command(
            no_parallel_cmd,
            "No-Parallel Tests (Serial)",
            progress_interval=args.progress_interval,
            test_context=no_parallel_test_context,
            env_overrides=build_windows_no_parallel_env(),
        )
        no_parallel_success = no_parallel_results["success"]

        if not no_parallel_success:
            success = False

    # Print combined summary (always show, even if tests failed)
    # Handle case where parallel_results might be a bool (backward compatibility)
    if not isinstance(parallel_results, dict):
        # Convert bool to dict format for summary
        parallel_results = {
            "success": parallel_results,
            "results": {},
            "duration": 0,
            "output": "",
        }
    print_combined_summary(parallel_results, no_parallel_results, description)

    # Final status message (summary already printed above)
    if success:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
