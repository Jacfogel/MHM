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
from pathlib import Path
from typing import Dict, Optional
from core.error_handling import handle_errors

# Simple ANSI color codes for terminal output (works in modern PowerShell)
# Enable ANSI color support in Windows
if sys.platform == 'win32':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)  # Enable ANSI escape sequences

GREEN = '\033[32m'
RED = '\033[31m'
YELLOW = '\033[33m'
RESET = '\033[0m'

ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*m')

@handle_errors("parsing JUnit XML report", user_friendly=False, default_return={'passed': 0, 'failed': 0, 'skipped': 0, 'warnings': 0, 'errors': 0, 'total': 0, 'deselected': 0})
def parse_junit_xml(xml_path: str) -> Dict[str, int]:
    """
    Parse JUnit XML report to extract test statistics.
    
    Returns a dictionary with: passed, failed, skipped, warnings, errors, total
    """
    results = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'warnings': 0,
        'errors': 0,
        'total': 0,
        'deselected': 0
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
        for testsuite in root.findall('.//testsuite'):
            tests = int(testsuite.get('tests', 0))
            failures = int(testsuite.get('failures', 0))
            errors = int(testsuite.get('errors', 0))
            skipped = int(testsuite.get('skipped', 0))
            
            results['total'] += tests
            results['failed'] += failures
            results['errors'] += errors
            results['skipped'] += skipped
            results['passed'] += (tests - failures - errors - skipped)
        
        # If no testsuites found, try direct attributes on root
        if results['total'] == 0:
            results['total'] = int(root.get('tests', 0))
            results['failed'] = int(root.get('failures', 0))
            results['errors'] = int(root.get('errors', 0))
            results['skipped'] = int(root.get('skipped', 0))
            results['passed'] = results['total'] - results['failed'] - results['errors'] - results['skipped']
    except (ET.ParseError, ValueError, AttributeError):
        # If parsing fails (malformed XML, invalid values, etc.), return empty results
        # Other exceptions are handled by decorator
        pass
    
    return results

@handle_errors("running test command", user_friendly=False, default_return={'success': False, 'output': '', 'results': {}, 'duration': 0, 'warnings': '', 'failures': ''})
def run_command(cmd, description, progress_interval: int = 30, capture_output: bool = True):
    """
    Run a command and return results with periodic progress logs.
    
    Args:
        cmd: Command to run
        description: Description for progress messages
        progress_interval: Seconds between progress updates
        capture_output: If True, capture results via JUnit XML (always True in practice)
    
    Returns:
        dict with 'success', 'output', 'results', 'duration', 'warnings', 'failures' keys
    """
    print(f"\nRunning: {description}...")

    start_time = time.time()
    
    # To preserve pytest's colors, let it write directly to the terminal (no pipe)
    # Use JUnit XML report to get structured results without capturing output
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', suffix='.xml') as tmp_file:
        junit_xml_path = tmp_file.name
    
    try:
        # Generate JUnit XML report for parsing (doesn't affect colors)
        cmd_with_junit = cmd + ['--junit-xml', junit_xml_path]
        
        # Ensure pytest keeps ANSI colors even though we're piping output
        contains_color_flag = any(opt.startswith('--color') for opt in cmd_with_junit)
        if not contains_color_flag:
            cmd_with_junit.append('--color=yes')
        
        # Capture output to parse warnings, but also write to terminal to preserve colors
        # Use a pipe that we can read from AND write to terminal
        output_queue = queue.Queue()
        output_lines = []
        
        @handle_errors("reading output from pipe", user_friendly=False, default_return=None)
        def read_output(pipe, queue_obj):
            """Read from pipe and put lines in queue, also write to terminal."""
            try:
                for line in iter(pipe.readline, ''):
                    if line:
                        queue_obj.put(line)
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
        process = subprocess.Popen(
            cmd_with_junit,
            stdout=subprocess.PIPE,  # Capture for parsing
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            universal_newlines=True,
            bufsize=1
        )
        
        # Start thread to read output and display it
        output_thread = threading.Thread(target=read_output, args=(process.stdout, output_queue))
        output_thread.daemon = True
        output_thread.start()
        
        # Monitor progress while process runs
        next_tick = start_time + max(1, progress_interval)
        while process.poll() is None:
            now = time.time()
            if now >= next_tick:
                elapsed = int(now - start_time)
                print(f"[PROGRESS] {description} running for {elapsed}s...")
                next_tick += max(1, progress_interval)
            time.sleep(0.5)
        
        # Wait for process to complete
        process.wait()
        
        # Wait for output thread to finish
        output_thread.join(timeout=1)
        
        # Collect all output lines
        while not output_queue.empty():
            try:
                output_lines.append(output_queue.get_nowait())
            except queue.Empty:
                break
        
        output = ''.join(output_lines)
        output_plain = ANSI_ESCAPE_RE.sub('', output)
        
        summary_counts = {}
        summary_line_matches = re.findall(r'={5,}\s*(.+?)\s*={5,}', output_plain, re.MULTILINE)
        if summary_line_matches:
            summary_content = summary_line_matches[-1]
            count_matches = re.findall(
                r'(\d+)\s+(failed|passed|skipped|warnings?|deselected|errors?)',
                summary_content,
                re.IGNORECASE
            )
            for count_str, label in count_matches:
                key = label.lower()
                if key in ('warning', 'warnings'):
                    key = 'warnings'
                elif key in ('error', 'errors'):
                    key = 'errors'
                summary_counts[key] = int(count_str)
        
        # Parse results from JUnit XML
        results = parse_junit_xml(junit_xml_path)
        
        # Ensure expected keys exist
        results.setdefault('warnings', 0)
        results.setdefault('deselected', 0)
        
        # Update results with parsed summary counts
        for key, value in summary_counts.items():
            results[key] = value
        
        # Parse warnings/failures details from pytest output
        warnings_text = ''
        failures_text = ''
        
        # Extract warnings count from pytest output (e.g., "10 warnings in 143.99s")
        # Look for pattern like "1 failed, 3023 passed, 1 skipped, 10 warnings in 143.99s"
        warnings_match = re.search(r'(\d+)\s+warnings?\s+in\s+[\d.]+s', output_plain)
        if not warnings_match:
            # Also try pattern without "in" (some pytest versions)
            warnings_match = re.search(r',\s*(\d+)\s+warnings?\s+in', output_plain)
        if warnings_match:
            results['warnings'] = int(warnings_match.group(1))
        
        # Extract failures from short test summary
        failures_section = re.search(r'FAILED\s+(.+?)(?=\n\n|\n===|$)', output_plain, re.DOTALL)
        if failures_section:
            failures_text = failures_section.group(1).strip()
        
        duration = time.time() - start_time
        
        # Print status message
        if process.returncode == 0:
            print(f"\n{GREEN}[SUCCESS]{RESET} {description} completed successfully in {duration}s")
        else:
            print(f"\n{RED}[FAILED]{RESET} {description} failed with exit code {process.returncode} after {duration}s")
        
        # Return dict with all information
        return {
            'success': process.returncode == 0,
            'output': output,
            'results': results,
            'duration': duration,
            'warnings': warnings_text,
            'failures': failures_text
        }
    finally:
        # Clean up temp file
        try:
            if os.path.exists(junit_xml_path):
                os.unlink(junit_xml_path)
        except:
            pass

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
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
    
    return logger

@handle_errors("printing combined test summary", default_return=None)
def print_combined_summary(parallel_results: Optional[Dict], no_parallel_results: Optional[Dict], description: str):
    """
    Print a combined summary of test results from both parallel and serial runs.
    
    Args:
        parallel_results: Results dict from parallel test run (or None if not run)
        no_parallel_results: Results dict from serial test run (or None if not run)
        description: Test mode description
    """
    # Extract results from both runs
    parallel_res = parallel_results.get('results', {}) if parallel_results and isinstance(parallel_results, dict) else {}
    no_parallel_res = no_parallel_results.get('results', {}) if no_parallel_results and isinstance(no_parallel_results, dict) else {}
    
    # Combine results
    combined = {
        'passed': parallel_res.get('passed', 0) + no_parallel_res.get('passed', 0),
        'failed': parallel_res.get('failed', 0) + no_parallel_res.get('failed', 0),
        'skipped': parallel_res.get('skipped', 0) + no_parallel_res.get('skipped', 0),
        'warnings': parallel_res.get('warnings', 0) + no_parallel_res.get('warnings', 0),
        'errors': parallel_res.get('errors', 0) + no_parallel_res.get('errors', 0),
        'deselected': parallel_res.get('deselected', 0) + no_parallel_res.get('deselected', 0),
    }
    combined['total'] = combined['passed'] + combined['failed'] + combined['skipped'] + combined['errors']
    
    # Calculate total duration (ensure floats for decimal precision)
    parallel_duration = float(parallel_results.get('duration', 0)) if parallel_results and isinstance(parallel_results, dict) else 0.0
    no_parallel_duration = float(no_parallel_results.get('duration', 0)) if no_parallel_results and isinstance(no_parallel_results, dict) else 0.0
    total_duration = parallel_duration + no_parallel_duration
    
    # Collect all warnings and failures
    all_warnings = []
    all_failures = []
    
    if parallel_results and isinstance(parallel_results, dict):
        if parallel_results.get('warnings'):
            all_warnings.append(('Parallel Tests', parallel_results['warnings']))
        if parallel_results.get('failures'):
            all_failures.append(('Parallel Tests', parallel_results['failures']))
    
    if no_parallel_results and isinstance(no_parallel_results, dict):
        if no_parallel_results.get('warnings'):
            all_warnings.append(('Serial Tests', no_parallel_results['warnings']))
        if no_parallel_results.get('failures'):
            all_failures.append(('Serial Tests', no_parallel_results['failures']))
    
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
        p_passed = parallel_res.get('passed', 0)
        p_failed = parallel_res.get('failed', 0)
        p_skipped = parallel_res.get('skipped', 0)
        p_warnings = parallel_res.get('warnings', 0)
        p_deselected = parallel_res.get('deselected', 0)
        s_passed = no_parallel_res.get('passed', 0)
        s_failed = no_parallel_res.get('failed', 0)
        s_skipped = no_parallel_res.get('skipped', 0)
        s_warnings = no_parallel_res.get('warnings', 0)
        s_deselected = no_parallel_res.get('deselected', 0)
        
        print(f"  Parallel Tests:    {p_passed} passed, {p_failed} failed, {p_skipped} skipped, {p_deselected} deselected, {p_warnings} warnings ({parallel_duration}s)")
        print(f"  Serial Tests:      {s_passed} passed, {s_failed} failed, {s_skipped} skipped, {s_deselected} deselected, {s_warnings} warnings ({no_parallel_duration}s)")
        
        print(f"\nTotal Duration: {total_duration}s")
        
        # Log durations and test counts to test log file
        p_total = p_passed + p_failed + p_skipped
        s_total = s_passed + s_failed + s_skipped
        total_tests = p_total + s_total
        test_logger.info(f"TEST SUITE DURATION - Parallel: {parallel_duration:.2f}s, Serial: {no_parallel_duration:.2f}s, Total: {total_duration:.2f}s")
        test_logger.info(f"TEST SUITE COUNTS - Parallel: {p_total} tests ({p_passed} passed, {p_failed} failed, {p_skipped} skipped), Serial: {s_total} tests ({s_passed} passed, {s_failed} failed, {s_skipped} skipped), Total: {total_tests} tests ({combined['passed']} passed, {combined['failed']} failed, {combined['skipped']} skipped)")
    elif parallel_duration > 0:
        # Single run (--no-parallel was used)
        print(f"\nDuration: {parallel_duration}s")
        
        # Log duration and test counts to test log file
        p_total = parallel_res.get('passed', 0) + parallel_res.get('failed', 0) + parallel_res.get('skipped', 0)
        test_logger.info(f"TEST SUITE DURATION - Total: {parallel_duration:.2f}s (single run mode)")
        test_logger.info(f"TEST SUITE COUNTS - Total: {p_total} tests ({parallel_res.get('passed', 0)} passed, {parallel_res.get('failed', 0)} failed, {parallel_res.get('skipped', 0)} skipped)")
    
    # Show failures details
    if all_failures:
        print(f"\nFAILURES:")
        for source, failure_text in all_failures:
            if failure_text:
                print(f"\nFrom {source}:")
                print(failure_text)
    
    # Show warnings details
    if all_warnings:
        print(f"\nWARNINGS:")
        for source, warning_text in all_warnings:
            if warning_text:
                print(f"\nFrom {source}:")
                print(warning_text)
    
    # Final summary line in pytest format - match pytest's exact format
    print()
    parallel_deselected = parallel_res.get('deselected', 0)
    serial_deselected = no_parallel_res.get('deselected', 0) if no_parallel_results and isinstance(no_parallel_results, dict) else None
    if serial_deselected is None:
        include_deselected_in_summary = parallel_deselected > 0
    else:
        include_deselected_in_summary = parallel_deselected > 0 and serial_deselected > 0
    
    summary_parts = [
        f"{RED}{combined['failed']} failed{RESET}",
        f"{GREEN}{combined['passed']} passed{RESET}",
    ]
    if include_deselected_in_summary:
        summary_parts.append(f"{YELLOW}{combined['deselected']} deselected{RESET}")
    if combined['skipped'] > 0:
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
    if combined['failed'] > 0:
        border_color = RED
    elif combined['warnings'] > 0:
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
    print("\n" + "="*60)
    print("MHM TEST RUNNER - Available Modes")
    print("="*60)
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
    print("  --workers N - Number of parallel workers (default: 2, or 'auto' for optimal)")
    print("  --coverage  - Run with coverage reporting")
    print("  --durations-all - Show timing for all tests")
    print("  --no-shim   - Disable test data shim (for burn-in validation)")
    print("  --random-order - Use random test order (for order independence validation)")
    print("  --burnin-mode - Enable burn-in mode (combines --no-shim and --random-order)")
    print("\nExamples:")
    print("  python run_tests.py                    # Run all tests in parallel")
    print("  python run_tests.py --mode fast        # Quick unit tests only")
    print("  python run_tests.py --mode all --verbose # All tests with verbose output")
    print("  python run_tests.py --no-parallel      # Disable parallel execution")
    print("  python run_tests.py --workers 4       # Use 4 parallel workers")
    print("  python run_tests.py --burnin-mode     # Validation run (no shim, random order)")
    print("="*60)


@handle_errors("running static logging check", default_return=False)
def run_static_logging_check() -> bool:
    """Run the static logging enforcement script before executing tests."""
    script_path = Path(__file__).parent / "scripts" / "static_checks" / "check_channel_loggers.py"
    if not script_path.exists():
        print(f"[STATIC CHECK] Missing script: {script_path}")
        return False

    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
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
        help="Test execution mode (default: all)"
    )
    parser.add_argument(
        "--no-parallel", 
        action="store_true",
        help="Disable parallel test execution (parallel is enabled by default)"
    )
    parser.add_argument(
        "--workers", 
        type=str, 
        default="auto",
        help="Number of parallel workers (default: auto to let pytest-xdist decide, or specify a number like 2, 4, etc.)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "--progress-interval",
        type=int,
        default=30,
        help="Print progress every N seconds (default: 30)"
    )
    parser.add_argument(
        "--durations-all",
        action="store_true",
        help="Ask pytest to report durations for all tests at the end"
    )
    parser.add_argument(
        "--no-shim",
        action="store_true",
        help="Disable test data shim (ENABLE_TEST_DATA_SHIM=0) for burn-in validation"
    )
    parser.add_argument(
        "--random-order",
        action="store_true",
        help="Use truly random test order (not fixed seed) for order independence validation"
    )
    parser.add_argument(
        "--burnin-mode",
        action="store_true",
        help="Enable burn-in validation mode (combines --no-shim and --random-order)"
    )
    parser.add_argument(
        "--help-modes",
        action="store_true",
        help="Show detailed information about test modes"
    )
    parser.add_argument(
        "--skip-static-logging-check",
        action="store_true",
        help="Skip the static logging enforcement preflight (not recommended)"
    )

    args = parser.parse_args()
    
    # Show help modes if requested
    if args.help_modes:
        print_test_mode_info()
        return 0

    if args.skip_static_logging_check:
        print("[STATIC CHECK] Skipped by user request")
    elif not run_static_logging_check():
        return 1
    
    # Enforce safe defaults for Windows console
    os.environ.setdefault('PYTHONUTF8', '1')
    
    # Handle burn-in mode (combines --no-shim and --random-order)
    if args.burnin_mode:
        args.no_shim = True
        args.random_order = True
        print("[BURN-IN MODE] Enabled: --no-shim and --random-order for validation")
    
    # Ensure test data shim is enabled by default for CI/local runs unless explicitly disabled
    if args.no_shim:
        os.environ['ENABLE_TEST_DATA_SHIM'] = '0'
        print("[BURN-IN] Test data shim disabled (ENABLE_TEST_DATA_SHIM=0)")
    else:
        os.environ.setdefault('ENABLE_TEST_DATA_SHIM', '1')

    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Track if we need to exclude no_parallel tests from parallel execution
    exclude_no_parallel = False
    
    # Add parallel execution (enabled by default, can be disabled with --no-parallel)
    # When parallel is enabled, exclude no_parallel tests from parallel execution
    # They will be run separately in serial mode
    if not args.no_parallel:
        exclude_no_parallel = True
        
        # Use 'auto' to let pytest-xdist determine optimal worker count, or use specified number
        # Default to 2 workers for safety (some tests may have race conditions with more workers)
        if args.workers == "auto":
            cmd.extend(["-n", "auto"])
        else:
            try:
                # Validate that workers is a valid number if not "auto"
                num_workers = int(args.workers)
                if num_workers < 1:
                    print(f"[WARNING] Invalid worker count: {num_workers}. Using 2 instead.")
                    cmd.extend(["-n", "2"])
                else:
                    cmd.extend(["-n", str(num_workers)])
            except ValueError:
                print(f"[WARNING] Invalid worker value: {args.workers}. Using 2 instead.")
                cmd.extend(["-n", "2"])
    
    # Add verbose output
    if args.verbose:
        cmd.append("-v")
    
    # Set test environment variables
    os.environ['DISABLE_LOG_ROTATION'] = '1'  # Prevent log rotation issues during tests
    
    # Handle test order randomization
    addopts = os.environ.get('PYTEST_ADDOPTS', '')
    has_seed = "--randomly-seed" in addopts or any(arg.startswith('--randomly-seed') for arg in sys.argv)
    
    if args.random_order:
        # Use truly random order (pytest-randomly will generate a random seed)
        # Don't add --randomly-seed, let pytest-randomly use a random seed
        print("[BURN-IN] Using random test order (no fixed seed)")
    elif not has_seed:
        # Default: use fixed seed for deterministic runs
        cmd.extend(["--randomly-seed=12345"])  # default stable seed for order independence verification

    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=core", "--cov=communication", "--cov=ui", "--cov=tasks", "--cov=user", "--cov=ai", "--cov-report=html:tests/coverage_html", "--cov-report=term"])
        # Set environment variable to control coverage data file location
        os.environ['COVERAGE_FILE'] = 'tests/.coverage'

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
        print(f"Note: Tests marked with @pytest.mark.no_parallel will run separately in serial mode")
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
    
    # Run the tests
    parallel_results = run_command(cmd, description, progress_interval=args.progress_interval)
    success = parallel_results['success']
    
    # If parallel execution was enabled, also run no_parallel tests separately in serial mode
    no_parallel_results = None
    if not args.no_parallel:
        # Create a separate command for no_parallel tests (serial execution)
        no_parallel_cmd = [sys.executable, "-m", "pytest"]
        
        # Build marker filter: combine no_parallel with mode filter if present
        # Always exclude e2e tests (they are slow and should only run explicitly)
        if mode_marker_filter:
            # Combine markers: e.g., "no_parallel and not slow and not e2e" or "no_parallel and slow and not e2e"
            no_parallel_cmd.extend(["-m", f"no_parallel and {mode_marker_filter} and not e2e"])
        else:
            no_parallel_cmd.extend(["-m", "no_parallel and not e2e"])  # Only run no_parallel tests, exclude e2e
        
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
            no_parallel_cmd.extend(["--cov=core", "--cov=communication", "--cov=ui", "--cov=tasks", "--cov=user", "--cov=ai", "--cov-report=html:tests/coverage_html", "--cov-report=term"])
        if args.durations_all:
            no_parallel_cmd.append("--durations=0")
        
        # Copy randomization settings
        if args.random_order:
            pass  # Don't add seed for random order
        elif not has_seed:
            no_parallel_cmd.extend(["--randomly-seed=12345"])
        
        print(f"\n[NO_PARALLEL] Running tests marked with @pytest.mark.no_parallel in serial mode...")
        no_parallel_results = run_command(no_parallel_cmd, "No-Parallel Tests (Serial)", progress_interval=args.progress_interval)
        no_parallel_success = no_parallel_results['success']
        
        if not no_parallel_success:
            success = False
    
    # Print combined summary (always show, even if tests failed)
    # Handle case where parallel_results might be a bool (backward compatibility)
    if not isinstance(parallel_results, dict):
        # Convert bool to dict format for summary
        parallel_results = {'success': parallel_results, 'results': {}, 'duration': 0, 'output': ''}
    print_combined_summary(parallel_results, no_parallel_results, description)
    
    # Final status message (summary already printed above)
    if success:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
