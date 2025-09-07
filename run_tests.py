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
    print("  --parallel  - Run tests in parallel")
    print("  --coverage  - Run with coverage reporting")
    print("  --durations-all - Show timing for all tests")
    print("\nExamples:")
    print("  python run_tests.py                    # Run all tests")
    print("  python run_tests.py --mode fast        # Quick unit tests only")
    print("  python run_tests.py --mode all --verbose # All tests with verbose output")
    print("  python run_tests.py --parallel --workers 4 # Parallel execution")
    print("="*60)

def main():
    parser = argparse.ArgumentParser(description="MHM Test Runner")
    parser.add_argument(
        "--mode", 
        choices=["fast", "unit", "integration", "behavior", "ui", "all", "slow"],
        default="all",
        help="Test execution mode (default: all)"
    )
    parser.add_argument(
        "--parallel", 
        action="store_true",
        help="Run tests in parallel (uses pytest-xdist)"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=2,
        help="Number of parallel workers (default: 2)"
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
    # Ensure test data shim is enabled by default for CI/local runs unless explicitly disabled
    os.environ.setdefault('ENABLE_TEST_DATA_SHIM', '1')

    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add parallel execution if requested
    if args.parallel:
        cmd.extend(["-n", str(args.workers)])
    
    # Add verbose output
    if args.verbose:
        cmd.append("-v")
    
    # Set test environment variables
    os.environ['DISABLE_LOG_ROTATION'] = '1'  # Prevent log rotation issues during tests
    
    # Add deterministic order unless user already provided a seed via env or PYTEST_ADDOPTS
    addopts = os.environ.get('PYTEST_ADDOPTS', '')
    has_seed = "--randomly-seed" in addopts or any(arg.startswith('--randomly-seed') for arg in sys.argv)
    if not has_seed:
        cmd.extend(["--randomly-seed=12345"])  # default stable seed for order independence verification

    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=core", "--cov=bot", "--cov=tasks", "--cov-report=html:tests/htmlcov", "--cov-report=term"])
        # Set environment variable to control coverage data file location
        os.environ['COVERAGE_FILE'] = 'tests/.coverage'

    # Optional per-test durations report
    if args.durations_all:
        cmd.append("--durations=0")
    
    # Add test selection based on mode
    if args.mode == "fast":
        # Fast tests: unit tests only
        cmd.extend(["tests/unit/", "-m", "not slow"])
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
        cmd.extend(["tests/behavior/", "-m", "not slow"])
        description = "Behavior Tests (excluding slow tests)"
        
    elif args.mode == "ui":
        # UI tests
        cmd.extend(["tests/ui/", "-m", "not slow"])
        description = "UI Tests (excluding slow tests)"
        
    elif args.mode == "slow":
        # Slow tests only
        cmd.extend(["tests/", "-m", "slow"])
        description = "Slow Tests Only"
        
    elif args.mode == "all":
        # All tests
        cmd.extend(["tests/"])
        description = "All Tests (Unit, Integration, Behavior, UI)"
    
    # Print clear information about what we're running
    print(f"\nMHM Test Runner")
    print(f"Mode: {args.mode}")
    print(f"Description: {description}")
    if args.parallel:
        print(f"Parallel: Yes ({args.workers} workers)")
    if args.verbose:
        print(f"Verbose: Yes")
    if args.coverage:
        print(f"Coverage: Yes")
    
    # Run the tests
    success = run_command(cmd, description, progress_interval=args.progress_interval)
    
    if success:
        print(f"\n[PASSED] {description} passed!")
        return 0
    else:
        print(f"\n[FAILED] {description} failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 