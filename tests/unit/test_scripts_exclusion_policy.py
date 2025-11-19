"""
Test to verify that scripts/ directory is excluded from test discovery.

This test ensures the testing policy that scripts/ should never contain
discoverable tests is enforced.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.unit
def test_scripts_directory_excluded_from_test_discovery():
    """Verify that pytest does not discover any tests in scripts/ directory."""
    project_root = Path(__file__).parent.parent.parent
    
    # Run pytest collection to see what tests would be discovered
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    # Check that no tests from scripts/ are collected
    output = result.stdout + result.stderr
    
    # Look for any references to scripts/ in the collected tests
    scripts_tests = []
    for line in output.split('\n'):
        if 'scripts' in line.lower() and ('test' in line.lower() or '::' in line):
            # Filter out false positives (like "scripts" in comments or paths)
            if 'scripts/' in line or 'scripts\\' in line:
                scripts_tests.append(line.strip())
    
    # Assert no tests from scripts/ were discovered
    assert not scripts_tests, (
        f"Found {len(scripts_tests)} test(s) from scripts/ directory that should be excluded:\n"
        + "\n".join(scripts_tests)
        + "\n\nThis violates the testing policy: scripts/ should never contain discoverable tests."
    )


@pytest.mark.unit
def test_scripts_directory_has_no_test_files():
    """Verify that scripts/ directory does not contain test files."""
    project_root = Path(__file__).parent.parent.parent
    scripts_dir = project_root / "scripts"
    
    if not scripts_dir.exists():
        # If scripts/ doesn't exist, that's fine - policy is still enforced
        return
    
    # Find any test files in scripts/
    test_files = []
    for py_file in scripts_dir.rglob("test_*.py"):
        test_files.append(str(py_file.relative_to(project_root)))
    for py_file in scripts_dir.rglob("*_test.py"):
        test_files.append(str(py_file.relative_to(project_root)))
    
    # Assert no test files found
    assert not test_files, (
        f"Found {len(test_files)} test file(s) in scripts/ directory:\n"
        + "\n".join(test_files)
        + "\n\nTest files should be in tests/ directory, not scripts/."
    )

