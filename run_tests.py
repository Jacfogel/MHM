#!/usr/bin/env python3
"""
MHM Test Runner

This script runs the comprehensive test suite for the Mental Health Management (MHM) system.
It provides different test modes and options for running tests efficiently.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def run_tests(test_type='all', verbose=False):
    """
    Run the MHM test suite.
    
    Args:
        test_type (str): Type of tests to run ('all', 'unit', 'integration', 'slow', 'ai')
        verbose (bool): Run tests in verbose mode
    """
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Build pytest command using current Python interpreter
    cmd = [sys.executable, '-m', 'pytest']
    
    # Add test directory
    cmd.append('tests/')
    
    # Add markers based on test type
    if test_type == 'unit':
        cmd.extend(['-m', 'unit'])
    elif test_type == 'integration':
        cmd.extend(['-m', 'integration'])
    elif test_type == 'slow':
        cmd.extend(['-m', 'slow'])
    elif test_type == 'ai':
        cmd.extend(['-m', 'ai'])
    # 'all' runs all tests (no marker filter)
    
    # Add verbosity
    if verbose:
        cmd.append('-v')
    
    # Add other useful options
    cmd.extend([
        '--tb=short',  # Short traceback format
        '--strict-markers',  # Strict marker checking
        '--disable-warnings'  # Disable warnings for cleaner output
    ])
    
    print(f"Running tests: {' '.join(cmd)}")
    print(f"Test type: {test_type}")
    print(f"Verbose: {verbose}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user.")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description='Run MHM test suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --type unit        # Run only unit tests
  python run_tests.py --type integration # Run only integration tests
  python run_tests.py --verbose          # Run with verbose output
  python run_tests.py --type slow        # Run only slow tests
        """
    )
    
    parser.add_argument(
        '--type', '-t',
        choices=['all', 'unit', 'integration', 'slow', 'ai'],
        default='all',
        help='Type of tests to run (default: all)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Run tests in verbose mode'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick tests only (excludes slow and ai tests)'
    )
    
    args = parser.parse_args()
    
    # Handle quick mode
    if args.quick:
        if args.type != 'all':
            print("Warning: --quick overrides --type. Running quick tests only.")
        args.type = 'unit'  # Quick mode runs unit tests only
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("Error: pytest is not installed.")
        print("Install it with: pip install pytest")
        return 1
    
    # Run the tests
    exit_code = run_tests(
        test_type=args.type,
        verbose=args.verbose
    )
    
    # Print summary
    print("-" * 50)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed.")
    
    return exit_code

if __name__ == '__main__':
    sys.exit(main()) 