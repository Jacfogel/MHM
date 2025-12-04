"""Integration-style CLI tests that ensure run_development_tools dispatches correctly."""

from unittest.mock import MagicMock

import pytest

from tests.development_tools.conftest import load_development_tools_module

load_development_tools_module("shared.file_rotation")
runner = load_development_tools_module("run_development_tools")


class TestCommandRouting:
    """Verify command routing without running heavyweight workflows."""

    @pytest.mark.integration
    def test_audit_command_success(self, monkeypatch):
        mock_service = MagicMock()
        mock_service.run_audit.return_value = True
        monkeypatch.setattr(runner, "AIToolsService", lambda project_root=None, config_path=None: mock_service)

        assert runner.main(["audit"]) == 0
        mock_service.run_audit.assert_called_once_with(quick=False, full=False, include_overlap=False)

    @pytest.mark.integration
    def test_audit_command_failure(self, monkeypatch):
        mock_service = MagicMock()
        mock_service.run_audit.return_value = False
        monkeypatch.setattr(runner, "AIToolsService", lambda project_root=None, config_path=None: mock_service)

        assert runner.main(["audit"]) == 1

    @pytest.mark.integration
    def test_docs_command_invokes_service(self, monkeypatch):
        mock_service = MagicMock()
        mock_service.run_docs.return_value = True
        monkeypatch.setattr(runner, "AIToolsService", lambda project_root=None, config_path=None: mock_service)

        assert runner.main(["docs"]) == 0
        mock_service.run_docs.assert_called_once_with()

    @pytest.mark.integration
    def test_unknown_command_returns_2(self):
        assert runner.main(["nonexistent"]) == 2

    @pytest.mark.integration
    def test_missing_command_shows_help(self):
        assert runner.main([]) == 1

