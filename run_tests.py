#!/usr/bin/env python3
"""
MHM Test Runner - Comprehensive testing framework for MHM system.

This script provides:
- Complete test suite execution
- Individual module testing
- Test category filtering
- Detailed reporting and coverage analysis
- Dedicated test logging
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_tests_with_pytest(test_paths=None, markers=None, verbose=False, coverage=False):
    """Run tests using pytest with specified options."""
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add test paths
    if test_paths:
        cmd.extend(test_paths)
    else:
        cmd.append("tests/")
    
    # Add markers
    if markers:
        for marker in markers:
            cmd.extend(["-m", marker])
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add coverage
    if coverage:
        cmd.extend([
            "--cov=core",
            "--cov=bot", 
            "--cov=tasks",
            "--cov=ui",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
    
    # Add other useful options
    cmd.extend([
        "--tb=short",  # Shorter traceback format
        "--strict-markers",  # Strict marker checking
        "--disable-warnings",  # Disable warnings for cleaner output
        "--color=yes"  # Colored output
    ])
    
    print(f"Running tests with command: {' '.join(cmd)}")
    print(f"Test run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # Run tests
    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

def run_specific_module(module_name):
    """Run tests for a specific module."""
    module_tests = {
        "service": "tests/test_service.py",
        "message_management": "tests/test_message_management.py", 
        "communication": "tests/test_communication_manager.py",
        "task_management": "tests/test_task_management.py",
        "user_management": "tests/test_user_management.py",
        "file_operations": "tests/test_file_operations.py",
        "scheduler": "tests/test_scheduler.py",
        "error_handling": "tests/test_error_handling.py",
        "config": "tests/test_config.py"
    }
    
    if module_name not in module_tests:
        print(f"Unknown module: {module_name}")
        print(f"Available modules: {', '.join(module_tests.keys())}")
        return False
    
    test_file = module_tests[module_name]
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return False
    
    print(f"Running tests for module: {module_name}")
    return run_tests_with_pytest([test_file], verbose=True)

def run_test_categories():
    """Run tests by category."""
    categories = {
        "core": ["tests/test_service.py", "tests/test_message_management.py", 
                "tests/test_user_management.py", "tests/test_file_operations.py",
                "tests/test_scheduler.py", "tests/test_error_handling.py", 
                "tests/test_config.py"],
        "communication": ["tests/test_communication_manager.py"],
        "tasks": ["tests/test_task_management.py"],
        "ui": [],  # UI tests will be added later
        "integration": ["-m", "integration"],
        "unit": ["-m", "unit"],
        "slow": ["-m", "slow"]
    }
    
    print("Available test categories:")
    for category, description in {
        "core": "Core system functionality (service, messages, users, files, scheduler, errors, config)",
        "communication": "Communication channels and message delivery",
        "tasks": "Task management system",
        "ui": "User interface components (not yet implemented)",
        "integration": "Integration tests across modules",
        "unit": "Unit tests for individual functions",
        "slow": "Slow-running tests"
    }.items():
        print(f"  {category:15} - {description}")
    
    return categories

def show_test_summary():
    """Show summary of available tests."""
    test_files = list(Path("tests").glob("test_*.py"))
    
    print("MHM Test Suite Summary")
    print("=" * 50)
    print(f"Total test files: {len(test_files)}")
    print()
    
    # Group by module
    modules = {}
    for test_file in test_files:
        module_name = test_file.stem.replace("test_", "")
        if module_name not in modules:
            modules[module_name] = []
        modules[module_name].append(test_file)
    
    print("Test Modules:")
    for module, files in sorted(modules.items()):
        print(f"  {module:20} - {len(files)} test file(s)")
        for file in files:
            print(f"    {file.name}")
    print()
    
    # Show test categories
    categories = run_test_categories()
    print("Test Categories:")
    for category, files in categories.items():
        if isinstance(files, list) and files:
            print(f"  {category:15} - {len(files)} test file(s)")
        else:
            print(f"  {category:15} - marker-based")

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="MHM Test Runner - Comprehensive testing framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --module service   # Run service module tests
  python run_tests.py --category core    # Run core functionality tests
  python run_tests.py --markers unit     # Run only unit tests
  python run_tests.py --verbose          # Run with verbose output
  python run_tests.py --coverage         # Run with coverage report
  python run_tests.py --summary          # Show test summary
        """
    )
    
    parser.add_argument(
        "--module", "-m",
        help="Run tests for specific module (service, message_management, communication, task_management, etc.)"
    )
    
    parser.add_argument(
        "--category", "-c", 
        help="Run tests by category (core, communication, tasks, ui, integration, unit, slow)"
    )
    
    parser.add_argument(
        "--markers", "-k",
        nargs="+",
        help="Run tests with specific markers (unit, integration, slow, service, communication, ui)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run tests with verbose output"
    )
    
    parser.add_argument(
        "--coverage", "--cov",
        action="store_true", 
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--summary", "-s",
        action="store_true",
        help="Show test summary and exit"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available tests and exit"
    )
    
    args = parser.parse_args()
    
    # Show summary if requested
    if args.summary:
        show_test_summary()
        return
    
    # List tests if requested
    if args.list:
        show_test_summary()
        return
    
    # Check if we're in the right directory
    if not os.path.exists("tests"):
        print("Error: tests directory not found. Please run from project root.")
        return 1
    
    # Run specific module tests
    if args.module:
        success = run_specific_module(args.module)
        return 0 if success else 1
    
    # Run category tests
    if args.category:
        categories = run_test_categories()
        if args.category not in categories:
            print(f"Unknown category: {args.category}")
            print(f"Available categories: {', '.join(categories.keys())}")
            return 1
        
        test_paths = categories[args.category]
        if test_paths and isinstance(test_paths[0], str) and test_paths[0].startswith("-m"):
            # Marker-based category
            markers = [test_paths[1]] if len(test_paths) > 1 else []
            success = run_tests_with_pytest(markers=markers, verbose=args.verbose, coverage=args.coverage)
        else:
            # File-based category
            success = run_tests_with_pytest(test_paths=test_paths, verbose=args.verbose, coverage=args.coverage)
        return 0 if success else 1
    
    # Run all tests
    success = run_tests_with_pytest(
        markers=args.markers,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    print("-" * 80)
    print(f"Test run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 