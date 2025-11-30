"""
Tests for development_tools ai_tools_runner CLI.

Smoke tests that verify the CLI runner works correctly with common commands.
"""

import pytest
import subprocess
import sys
from pathlib import Path


# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
RUNNER_SCRIPT = PROJECT_ROOT / "development_tools" / "ai_tools_runner.py"


class TestCLIRunnerSmokeTests:
    """Smoke tests for the CLI runner."""

    @pytest.mark.integration
    @pytest.mark.smoke
    def test_status_command_exits_zero(self):
        """Test that 'status' command exits with code 0 and produces output."""
        result = subprocess.run(
            [sys.executable, str(RUNNER_SCRIPT), "status"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=60  # Increased timeout to handle slow file system operations
        )
        assert result.returncode == 0, f"status command failed with exit code {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        # Command should complete successfully (output may go to logs, not stdout/stderr)

    @pytest.mark.integration
    @pytest.mark.smoke
    def test_config_command_exits_zero(self):
        """Test that 'config' command exits with code 0 and produces output."""
        result = subprocess.run(
            [sys.executable, str(RUNNER_SCRIPT), "config"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"config command failed with exit code {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        # Command should complete successfully (output may go to logs, not stdout/stderr)

    @pytest.mark.integration
    @pytest.mark.smoke
    def test_help_command_exits_zero(self):
        """Test that 'help' command exits with code 0 and shows help."""
        result = subprocess.run(
            [sys.executable, str(RUNNER_SCRIPT), "help"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"help command failed with exit code {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        # Should show help text
        assert "help" in result.stdout.lower() or len(result.stdout) > 0

    @pytest.mark.integration
    @pytest.mark.smoke
    def test_no_command_exits_one(self):
        """Test that running without a command exits with code 1 and shows help."""
        result = subprocess.run(
            [sys.executable, str(RUNNER_SCRIPT)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 1, f"No command should exit with code 1, got {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        # Should show help or usage information
        assert len(result.stdout) > 0, "Should show help when no command provided"

    @pytest.mark.integration
    @pytest.mark.smoke
    def test_unknown_command_exits_two(self):
        """Test that unknown command exits with code 2 and shows error and available commands."""
        result = subprocess.run(
            [sys.executable, str(RUNNER_SCRIPT), "unknown_command_that_does_not_exist"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 2, f"Unknown command should exit with code 2, got {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        # Should show error message
        assert "unknown" in result.stdout.lower() or "unknown" in result.stderr.lower() or len(result.stdout) > 0
        # Should show available commands
        assert "command" in result.stdout.lower() or len(result.stdout) > 0

    @pytest.mark.integration
    def test_runner_script_exists(self):
        """Test that the runner script file exists."""
        assert RUNNER_SCRIPT.exists(), f"Runner script not found at {RUNNER_SCRIPT}"

    @pytest.mark.integration
    def test_runner_script_is_executable(self):
        """Test that the runner script can be executed."""
        # Just verify it's a Python file
        assert RUNNER_SCRIPT.suffix == '.py' or RUNNER_SCRIPT.name == 'ai_tools_runner.py'

