"""Regression coverage for the audit's standalone process-cleanup checker."""

import os
from pathlib import Path
import subprocess
import sys

import pytest


pytestmark = [pytest.mark.unit, pytest.mark.core]


@pytest.mark.parametrize("from_project_root", [True, False])
def test_process_cleanup_script_starts_without_pythonpath(tmp_path, from_project_root):
    """The audit script must import its package without an inherited path fix."""
    project_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["DEVTOOLS_TESTING"] = "1"
    env["DEV_TOOLS_LOGS_DIR"] = str(tmp_path / "logs")
    result = subprocess.run(
        [sys.executable, str(project_root / "development_tools/tests/verify_process_cleanup.py"), "--help"],
        cwd=project_root if from_project_root else tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Verify pytest process cleanup behavior" in result.stdout
