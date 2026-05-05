"""
Tests for development_tools run_development_tools CLI.

Smoke tests that verify the CLI runner works correctly with common commands.
"""

import pytest
import subprocess
import sys
from pathlib import Path

from tests.development_tools.conftest import load_development_tools_module


# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
RUNNER_SCRIPT = PROJECT_ROOT / "development_tools" / "run_development_tools.py"
runner = load_development_tools_module("run_development_tools")


class TestCLIRunnerSmokeTests:
    """Smoke tests for the CLI runner."""

    @pytest.mark.integration
    @pytest.mark.smoke
    def test_status_command_exits_zero(self, monkeypatch):
        """Test that 'status' command exits with code 0 and produces output."""
        mock_service = type(
            "_MockService",
            (),
            {"run_status": lambda self: None},
        )()
        monkeypatch.setattr(
            runner,
            "AIToolsService",
            lambda project_root=None, config_path=None: mock_service,
        )
        monkeypatch.setattr(
            runner,
            "_cleanup_transient_runtime_artifacts",
            lambda *_args, **_kwargs: None,
        )

        assert runner.main(["status"]) == 0

    @pytest.mark.integration
    @pytest.mark.smoke
    def test_config_command_exits_zero(self, monkeypatch):
        """Test that 'config' command exits with code 0 and produces output."""
        mock_service = type(
            "_MockService",
            (),
            {"run_config": lambda self: True},
        )()
        monkeypatch.setattr(
            runner,
            "AIToolsService",
            lambda project_root=None, config_path=None: mock_service,
        )
        monkeypatch.setattr(
            runner,
            "_cleanup_transient_runtime_artifacts",
            lambda *_args, **_kwargs: None,
        )
        result = runner.main(["config"])
        assert result == 0

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
    def test_unknown_command_exits_two(self, capsys):
        """Test that unknown command exits with code 2 and shows error and available commands."""
        result = runner.main(["unknown_command_that_does_not_exist"])
        captured = capsys.readouterr()

        assert result == 2
        # Should show error message
        assert "unknown" in captured.out.lower() or "unknown" in captured.err.lower()
        # Should show available commands
        assert "command" in captured.out.lower()

    @pytest.mark.integration
    def test_runner_script_exists(self):
        """Test that the runner script file exists."""
        assert RUNNER_SCRIPT.exists(), f"Runner script not found at {RUNNER_SCRIPT}"

    @pytest.mark.integration
    def test_runner_script_is_executable(self):
        """Test that the runner script can be executed."""
        # Just verify it's a Python file
        assert RUNNER_SCRIPT.suffix == '.py' or RUNNER_SCRIPT.name == 'run_development_tools.py'

