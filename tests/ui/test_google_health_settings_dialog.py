"""Behavior tests for the admin Google Health connect dialog."""

from __future__ import annotations

from contextlib import ExitStack
from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from integrations.google_health.user_settings import HealthIntegrationStatus
from ui.dialogs.google_health_settings_dialog import (
    GoogleHealthSettingsDialog,
    _ConnectFlowWorker,
)

pytestmark = [pytest.mark.ui]


@pytest.fixture(scope="module")
def qapp():
    """Provide a process-wide QApplication for dialog tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _status(*, connected: bool = False, feature_state: str = "disabled") -> HealthIntegrationStatus:
    """Build a status snapshot for refresh_status tests."""
    return HealthIntegrationStatus(
        feature_state=feature_state,
        connected=connected,
        last_success_at="never",
        has_recent_error=False,
    )


def _open_dialog(
    *,
    user_id: str | None = "user-1",
    ready: bool = True,
    ready_error: str = "",
    status: HealthIntegrationStatus | None = None,
    status_text: str = "status",
    load_status: HealthIntegrationStatus | None | object = ...,
):
    """Create a dialog while Google Health backends stay mocked."""
    stack = ExitStack()
    stack.enter_context(
        patch(
            "ui.dialogs.google_health_settings_dialog.get_connect_readiness",
            return_value=(ready, ready_error),
        )
    )
    if load_status is ...:
        load_status = status if status is not None else _status()
    if ready and user_id:
        stack.enter_context(
            patch(
                "ui.dialogs.google_health_settings_dialog.get_health_integration_status",
                return_value=load_status,
            )
        )
        stack.enter_context(
            patch(
                "ui.dialogs.google_health_settings_dialog.format_status_text",
                return_value=status_text,
            )
        )
    dialog = GoogleHealthSettingsDialog(user_id=user_id)
    return stack, dialog


class TestGoogleHealthSettingsDialog:
    """Connect panel refresh, controls, and OAuth start paths."""

    def test_refresh_status_when_not_ready_disables_actions(self, qapp):
        stack, dialog = _open_dialog(
            ready=False,
            ready_error="Google Health is not enabled.",
        )
        with stack:
            assert "not enabled" in dialog.status_view.toPlainText()
            assert dialog.btn_connect.isEnabled() is False
        dialog.deleteLater()

    def test_refresh_status_without_user_disables_actions(self, qapp):
        stack, dialog = _open_dialog(user_id=None)
        with stack:
            assert dialog.status_view.toPlainText() == "No user selected."
            assert dialog.btn_enable.isEnabled() is False
        dialog.deleteLater()

    def test_refresh_status_when_status_missing(self, qapp):
        stack, dialog = _open_dialog(load_status=None)
        with stack:
            assert dialog.status_view.toPlainText() == "Could not load health status."
            assert dialog.btn_sync.isEnabled() is False
        dialog.deleteLater()

    def test_refresh_status_enables_connect_when_not_linked(self, qapp):
        stack, dialog = _open_dialog(
            status=_status(connected=False),
            status_text="Feature: disabled",
        )
        with stack:
            assert dialog.status_view.toPlainText() == "Feature: disabled"
            assert dialog.btn_connect.isEnabled() is True
            assert dialog.btn_refresh.isEnabled() is True
        dialog.deleteLater()

    def test_refresh_status_disables_connect_when_linked(self, qapp):
        stack, dialog = _open_dialog(
            status=_status(connected=True, feature_state="enabled"),
            status_text="Feature: enabled",
        )
        with stack:
            assert dialog.btn_connect.isEnabled() is False
            assert dialog.btn_enable.isEnabled() is True
        dialog.deleteLater()

    def test_start_connect_without_user_returns(self, qapp):
        stack, dialog = _open_dialog(user_id=None)
        with stack:
            dialog.start_connect()
        dialog.deleteLater()

    def test_start_connect_warns_when_not_ready(self, qapp):
        stack, dialog = _open_dialog()
        with stack:
            with (
                patch(
                    "ui.dialogs.google_health_settings_dialog.get_connect_readiness",
                    return_value=(False, "missing credentials"),
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.QMessageBox.warning"
                ) as mock_warning,
            ):
                dialog.start_connect()
            mock_warning.assert_called_once()
        dialog.deleteLater()

    def test_start_connect_warns_when_auth_url_missing(self, qapp):
        stack, dialog = _open_dialog()
        with stack:
            with (
                patch(
                    "ui.dialogs.google_health_settings_dialog.get_connect_authorization_url",
                    return_value="",
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.QMessageBox.warning"
                ) as mock_warning,
            ):
                dialog.start_connect()
            mock_warning.assert_called_once()
            assert mock_warning.call_args.args[2] == "Could not build authorization URL."
        dialog.deleteLater()

    def test_start_connect_cancels_when_user_declines(self, qapp):
        stack, dialog = _open_dialog()
        with stack:
            with (
                patch(
                    "ui.dialogs.google_health_settings_dialog.get_connect_authorization_url",
                    return_value="https://example.test/oauth",
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.No,
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.webbrowser.open"
                ) as mock_open,
            ):
                dialog.start_connect()
            mock_open.assert_not_called()
        dialog.deleteLater()

    def test_start_connect_opens_browser_and_starts_worker(self, qapp):
        stack, dialog = _open_dialog()
        mock_thread = MagicMock()
        mock_worker = MagicMock()
        with stack:
            with (
                patch(
                    "ui.dialogs.google_health_settings_dialog.get_connect_authorization_url",
                    return_value="https://example.test/oauth",
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.Yes,
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.webbrowser.open"
                ) as mock_open,
                patch(
                    "ui.dialogs.google_health_settings_dialog.QThread",
                    return_value=mock_thread,
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog._ConnectFlowWorker",
                    return_value=mock_worker,
                ),
            ):
                dialog.start_connect()
            mock_open.assert_called_once_with("https://example.test/oauth")
            mock_worker.moveToThread.assert_called_once_with(mock_thread)
            mock_thread.start.assert_called_once()
            assert "Waiting for browser approval" in dialog.status_view.toPlainText()
            assert dialog.btn_connect.isEnabled() is False
        dialog.deleteLater()

    def test_start_connect_shows_url_when_browser_open_fails(self, qapp):
        stack, dialog = _open_dialog()
        mock_thread = MagicMock()
        mock_worker = MagicMock()
        with stack:
            with (
                patch(
                    "ui.dialogs.google_health_settings_dialog.get_connect_authorization_url",
                    return_value="https://example.test/oauth",
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.Yes,
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.webbrowser.open",
                    side_effect=OSError("no browser"),
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.QMessageBox.warning"
                ) as mock_warning,
                patch(
                    "ui.dialogs.google_health_settings_dialog.QThread",
                    return_value=mock_thread,
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog._ConnectFlowWorker",
                    return_value=mock_worker,
                ),
            ):
                dialog.start_connect()
            mock_warning.assert_called_once()
            assert "https://example.test/oauth" in mock_warning.call_args.args[2]
            mock_thread.start.assert_called_once()
        dialog.deleteLater()

    def test_on_connect_finished_success_notifies(self, qapp):
        stack, dialog = _open_dialog(
            status=_status(connected=True, feature_state="enabled"),
            status_text="connected",
        )
        with stack:
            emitted = []
            dialog.user_changed.connect(lambda: emitted.append(True))
            with patch(
                "ui.dialogs.google_health_settings_dialog.QMessageBox.information"
            ) as mock_info:
                dialog._on_connect_finished(True, "")
            mock_info.assert_called_once()
            assert emitted == [True]
        dialog.deleteLater()

    def test_on_connect_finished_failure_warns(self, qapp):
        stack, dialog = _open_dialog()
        with stack:
            with patch(
                "ui.dialogs.google_health_settings_dialog.QMessageBox.warning"
            ) as mock_warning:
                dialog._on_connect_finished(False, "user cancelled")
            mock_warning.assert_called_once()
            assert mock_warning.call_args.args[2] == "user cancelled"
        dialog.deleteLater()

    def test_pause_enable_sync_and_delete_controls(self, qapp):
        stack, dialog = _open_dialog(
            status=_status(connected=True, feature_state="enabled"),
        )
        with stack:
            emitted = []
            dialog.user_changed.connect(lambda: emitted.append(True))

            with (
                patch(
                    "ui.dialogs.google_health_settings_dialog.pause_health_integration",
                    return_value=True,
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.QMessageBox.information"
                ) as mock_info,
            ):
                dialog.pause_health()
            mock_info.assert_called_once()

            with (
                patch(
                    "ui.dialogs.google_health_settings_dialog.enable_health_integration",
                    return_value=(True, ""),
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.QMessageBox.information"
                ) as mock_info,
            ):
                dialog.enable_health()
            mock_info.assert_called_once()

            with (
                patch(
                    "ui.dialogs.google_health_settings_dialog.enable_health_integration",
                    return_value=(False, "Connect Google Health first."),
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.QMessageBox.warning"
                ) as mock_warning,
            ):
                dialog.enable_health()
            mock_warning.assert_called_once()

            with (
                patch(
                    "ui.dialogs.google_health_settings_dialog.sync_health_integration",
                    return_value=True,
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.QMessageBox.information"
                ) as mock_info,
            ):
                dialog.sync_now()
            mock_info.assert_called_once()

            with (
                patch(
                    "ui.dialogs.google_health_settings_dialog.sync_health_integration",
                    return_value=False,
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.QMessageBox.warning"
                ) as mock_warning,
            ):
                dialog.sync_now()
            mock_warning.assert_called_once()

            with (
                patch(
                    "ui.dialogs.google_health_settings_dialog.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.No,
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.delete_health_integration"
                ) as mock_delete,
            ):
                dialog.delete_data()
            mock_delete.assert_not_called()

            with (
                patch(
                    "ui.dialogs.google_health_settings_dialog.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.Yes,
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.delete_health_integration",
                    return_value=True,
                ),
                patch(
                    "ui.dialogs.google_health_settings_dialog.QMessageBox.information"
                ) as mock_info,
            ):
                dialog.delete_data()
            mock_info.assert_called_once()
            assert emitted
        dialog.deleteLater()

    def test_controls_without_user_return(self, qapp):
        stack, dialog = _open_dialog(user_id=None)
        with stack:
            dialog.pause_health()
            dialog.enable_health()
            dialog.sync_now()
            dialog.delete_data()
        dialog.deleteLater()


class TestConnectFlowWorker:
    """Background OAuth worker emits success or failure."""

    def test_run_emits_connect_result(self, qapp):
        worker = _ConnectFlowWorker("user-1")
        results = []
        worker.finished.connect(lambda ok, err: results.append((ok, err)))

        with patch(
            "integrations.google_health.user_settings.run_connect_flow",
            return_value=(True, ""),
        ):
            worker.run()

        assert results == [(True, "")]
        worker.deleteLater()
