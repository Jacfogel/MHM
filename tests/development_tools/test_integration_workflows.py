"""Integration-style CLI tests that ensure run_development_tools dispatches correctly."""

from unittest.mock import MagicMock

import pytest

from tests.development_tools.conftest import load_development_tools_module

load_development_tools_module("shared.file_rotation")
runner = load_development_tools_module("run_development_tools")
lock_state_module = load_development_tools_module("shared.lock_state")


class TestCommandRouting:
    """Verify command routing without running heavyweight workflows."""

    @pytest.mark.integration
    def test_audit_command_success(self, monkeypatch, tmp_path):
        mock_service = MagicMock()
        mock_service.run_audit.return_value = True
        monkeypatch.setattr(runner, "AIToolsService", lambda project_root=None, config_path=None: mock_service)

        assert runner.main(["--project-root", str(tmp_path), "audit"]) == 0
        mock_service.run_audit.assert_called_once_with(
            quick=False, full=False, include_overlap=False, strict=False
        )

    @pytest.mark.integration
    def test_audit_command_failure(self, monkeypatch, tmp_path):
        mock_service = MagicMock()
        mock_service.run_audit.return_value = False
        monkeypatch.setattr(runner, "AIToolsService", lambda project_root=None, config_path=None: mock_service)

        assert runner.main(["--project-root", str(tmp_path), "audit"]) == 1
        mock_service.run_audit.assert_called_once_with(
            quick=False, full=False, include_overlap=False, strict=False
        )

    @pytest.mark.integration
    def test_audit_command_strict_passthrough(self, monkeypatch, tmp_path):
        mock_service = MagicMock()
        mock_service.run_audit.return_value = True
        monkeypatch.setattr(
            runner, "AIToolsService", lambda project_root=None, config_path=None: mock_service
        )

        assert (
            runner.main(
                ["--project-root", str(tmp_path), "audit", "--full", "--strict"]
            )
            == 0
        )
        mock_service.run_audit.assert_called_once_with(
            quick=False, full=True, include_overlap=False, strict=True
        )

    @pytest.mark.integration
    def test_docs_command_invokes_service(self, monkeypatch):
        mock_service = MagicMock()
        mock_service.run_docs.return_value = True
        monkeypatch.setattr(runner, "AIToolsService", lambda project_root=None, config_path=None: mock_service)

        assert runner.main(["docs"]) == 0
        mock_service.run_docs.assert_called_once_with()

    @pytest.mark.integration
    def test_cache_clear_alias_routes_to_clear_cache(self, monkeypatch, tmp_path):
        mock_service = MagicMock()
        mock_service.run_audit.return_value = True
        clear_cache_calls = []

        def _fake_clear_cache(_project_root, cache_scope=None, **_kwargs):
            clear_cache_calls.append(True)
            return 3

        monkeypatch.setattr(
            runner,
            "AIToolsService",
            lambda project_root=None, config_path=None: mock_service,
        )
        monkeypatch.setattr(runner, "_clear_all_caches", _fake_clear_cache)

        assert runner.main(["--project-root", str(tmp_path), "--cache-clear", "audit"]) == 0
        assert len(clear_cache_calls) == 1
        mock_service.run_audit.assert_called_once_with(
            quick=False, full=False, include_overlap=False, strict=False
        )

    @pytest.mark.integration
    def test_global_dev_tools_only_sets_service_mode(self, monkeypatch, tmp_path):
        """Parent CLI parses `--dev-tools-only` before the audit subcommand; service must still get the flag."""
        mock_service = MagicMock()
        mock_service.run_audit.return_value = True
        monkeypatch.setattr(
            runner,
            "AIToolsService",
            lambda project_root=None, config_path=None: mock_service,
        )
        assert (
            runner.main(
                [
                    "--project-root",
                    str(tmp_path),
                    "audit",
                    "--full",
                    "--dev-tools-only",
                ]
            )
            == 0
        )
        assert mock_service.dev_tools_only_mode is True

    @pytest.mark.integration
    def test_unknown_command_returns_2(self):
        assert runner.main(["nonexistent"]) == 2

    @pytest.mark.integration
    def test_missing_command_shows_help(self):
        assert runner.main([]) == 1

    @pytest.mark.integration
    def test_audit_keyboard_interrupt_cleans_up_lock_files(self, monkeypatch, tmp_path):
        mock_service = MagicMock()
        mock_service.run_audit.side_effect = KeyboardInterrupt()
        monkeypatch.setattr(
            runner,
            "AIToolsService",
            lambda project_root=None, config_path=None: mock_service,
        )

        audit_lock = tmp_path / ".audit_in_progress.lock"
        coverage_lock = tmp_path / ".coverage_in_progress.lock"
        dev_tools_coverage_lock = tmp_path / ".coverage_dev_tools_in_progress.lock"
        audit_lock.write_text("", encoding="utf-8")
        coverage_lock.write_text("", encoding="utf-8")
        dev_tools_coverage_lock.write_text("", encoding="utf-8")

        code = runner.main(["--project-root", str(tmp_path), "audit"])

        assert code == 130
        assert not audit_lock.exists()
        assert not coverage_lock.exists()
        assert not dev_tools_coverage_lock.exists()

    @pytest.mark.integration
    def test_audit_keyboard_interrupt_with_internal_signature_returns_failure_not_130(
        self, monkeypatch, tmp_path
    ):
        mock_service = MagicMock()
        mock_service._internal_interrupt_detected = True
        mock_service.run_audit.side_effect = KeyboardInterrupt()
        monkeypatch.setattr(
            runner,
            "AIToolsService",
            lambda project_root=None, config_path=None: mock_service,
        )

        code = runner.main(["--project-root", str(tmp_path), "audit"])

        assert code == 1

    @pytest.mark.integration
    def test_audit_preflight_cleans_stale_locks_and_runs(self, monkeypatch, tmp_path):
        mock_service = MagicMock()
        mock_service.run_audit.return_value = True
        monkeypatch.setattr(
            runner,
            "AIToolsService",
            lambda project_root=None, config_path=None: mock_service,
        )

        stale_lock = tmp_path / ".audit_in_progress.lock"
        stale_lock.write_text("", encoding="utf-8")

        code = runner.main(["--project-root", str(tmp_path), "audit"])

        assert code == 0
        assert not stale_lock.exists()
        mock_service.run_audit.assert_called_once_with(
            quick=False, full=False, include_overlap=False, strict=False
        )

    @pytest.mark.integration
    def test_audit_preflight_blocks_on_active_lock(self, monkeypatch, tmp_path):
        service_factory = MagicMock()
        monkeypatch.setattr(runner, "AIToolsService", service_factory)
        lock_state_module.write_lock_metadata(
            tmp_path / ".audit_in_progress.lock", lock_type="audit"
        )

        code = runner.main(["--project-root", str(tmp_path), "audit"])

        assert code == 1
        service_factory.assert_not_called()
