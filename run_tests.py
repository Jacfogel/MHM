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
from pathlib import Path

def run_command(cmd, description, progress_interval: int = 30):
    """Run a command and return success status with periodic progress logs."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    start_time = time.time()
    try:
        process = subprocess.Popen(cmd)
        next_tick = start_time + max(1, progress_interval)
        # Periodic progress output
        while True:
            ret = process.poll()
            now = time.time()
            if now >= next_tick:
                elapsed = int(now - start_time)
                print(f"[PROGRESS] {description} running for {elapsed}s...")
                next_tick += max(1, progress_interval)
            if ret is not None:
                break
            time.sleep(0.5)

        total = int(time.time() - start_time)
        if process.returncode == 0:
            print(f"\n[SUCCESS] {description} completed successfully in {total}s")
            return True
        else:
            print(f"\n[FAILED] {description} failed with exit code {process.returncode} after {total}s")
            return False
    except Exception as e:
        total = int(time.time() - start_time)
        print(f"\n[FAILED] {description} error after {total}s: {e}")
        return False

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
    
    args = parser.parse_args()
    
    # Show help modes if requested
    if args.help_modes:
        print_test_mode_info()
        return 0
    
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
    
    # Add marker filters (combine mode filter with no_parallel exclusion if needed)
    marker_parts = []
    if mode_marker_filter:
        marker_parts.append(mode_marker_filter)
    if exclude_no_parallel:
        marker_parts.append("not no_parallel")
    
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
    
    # Run the tests
    success = run_command(cmd, description, progress_interval=args.progress_interval)
    
    # If parallel execution was enabled, also run no_parallel tests separately in serial mode
    if success and not args.no_parallel:
        # Create a separate command for no_parallel tests (serial execution)
        no_parallel_cmd = [sys.executable, "-m", "pytest"]
        
        # Build marker filter: combine no_parallel with mode filter if present
        if mode_marker_filter:
            # Combine markers: e.g., "no_parallel and not slow" or "no_parallel and slow"
            no_parallel_cmd.extend(["-m", f"no_parallel and {mode_marker_filter}"])
        else:
            no_parallel_cmd.extend(["-m", "no_parallel"])  # Only run no_parallel tests
        
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
        no_parallel_success = run_command(no_parallel_cmd, "No-Parallel Tests (Serial)", progress_interval=args.progress_interval)
        
        if not no_parallel_success:
            success = False
    
    if success:
        print(f"\n[PASSED] {description} passed!")
        return 0
    else:
        print(f"\n[FAILED] {description} failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 