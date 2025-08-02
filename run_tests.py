#!/usr/bin/env python3
"""
Test Runner for MHM Project

Provides different test execution modes for faster development workflow.
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n[SUCCESS] {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[FAILED] {description} failed with exit code {e.returncode}")
        return False

def main():
    parser = argparse.ArgumentParser(description="MHM Test Runner")
    parser.add_argument(
        "--mode", 
        choices=["fast", "unit", "integration", "behavior", "all", "slow"],
        default="fast",
        help="Test execution mode"
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
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add parallel execution if requested
    if args.parallel:
        cmd.extend(["-n", str(args.workers)])
    
    # Add verbose output
    if args.verbose:
        cmd.append("-v")
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=core", "--cov=bot", "--cov=tasks", "--cov-report=html", "--cov-report=term"])
    
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
        
    elif args.mode == "slow":
        # Slow tests only
        cmd.extend(["tests/", "-m", "slow"])
        description = "Slow Tests Only"
        
    elif args.mode == "all":
        # All tests
        cmd.extend(["tests/"])
        description = "All Tests"
    
    # Run the tests
    success = run_command(cmd, description)
    
    if success:
        print(f"\n[PASSED] {description} passed!")
        return 0
    else:
        print(f"\n[FAILED] {description} failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 