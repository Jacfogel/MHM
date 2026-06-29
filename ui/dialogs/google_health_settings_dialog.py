# ui/dialogs/google_health_settings_dialog.py
# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false

"""Admin UI dialog for Google Health connect, status, and controls."""

from __future__ import annotations

import webbrowser

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from core.error_handling import handle_errors
from core.logger import get_component_logger
from integrations.google_health.user_settings import (
    delete_health_integration,
    enable_health_integration,
    format_status_text,
    get_connect_authorization_url,
    get_connect_readiness,
    get_health_integration_status,
    pause_health_integration,
    sync_health_integration,
)

logger = get_component_logger("ui")


class _ConnectFlowWorker(QObject):
    """Background worker that runs the blocking OAuth connect flow."""

    finished = Signal(bool, str)

    @handle_errors("initializing Google Health connect worker", user_friendly=False, re_raise=True)
    def __init__(self, user_id: str) -> None:
        super().__init__()
        self.user_id = user_id

    @handle_errors("running Google Health connect worker", default_return=None)
    def run(self) -> None:
        from integrations.google_health.user_settings import run_connect_flow

        success, error = run_connect_flow(self.user_id)
        self.finished.emit(success, error)


class GoogleHealthSettingsDialog(QDialog):
    """Per-user Google Health connect panel for the admin UI."""

    user_changed = Signal()

    @handle_errors("initializing Google Health settings dialog", default_return=None)
    def __init__(self, parent=None, user_id: str | None = None) -> None:
        """Build the connect panel for ``user_id`` (admin UI)."""
        super().__init__(parent)
        self.user_id = user_id
        self._connect_thread: QThread | None = None
        self._connect_worker: _ConnectFlowWorker | None = None

        self.setWindowTitle("Google Health")
        self.setMinimumWidth(520)
        self.setMinimumHeight(360)

        layout = QVBoxLayout(self)

        intro = QLabel(
            "One-time Google account connect, then automatic daily sync for "
            "gentle message personalization (wellness only — not clinical)."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.status_view = QTextEdit()
        self.status_view.setReadOnly(True)
        self.status_view.setMaximumHeight(160)
        layout.addWidget(self.status_view)

        row_connect = QHBoxLayout()
        self.btn_connect = QPushButton("Connect Google Health")
        self.btn_connect.clicked.connect(self.start_connect)
        row_connect.addWidget(self.btn_connect)

        self.btn_refresh = QPushButton("Refresh Status")
        self.btn_refresh.clicked.connect(self.refresh_status)
        row_connect.addWidget(self.btn_refresh)
        layout.addLayout(row_connect)

        row_controls = QHBoxLayout()
        self.btn_enable = QPushButton("Enable")
        self.btn_enable.clicked.connect(self.enable_health)
        row_controls.addWidget(self.btn_enable)

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.clicked.connect(self.pause_health)
        row_controls.addWidget(self.btn_pause)

        self.btn_sync = QPushButton("Sync Now")
        self.btn_sync.clicked.connect(self.sync_now)
        row_controls.addWidget(self.btn_sync)

        self.btn_delete = QPushButton("Delete Local Data")
        self.btn_delete.clicked.connect(self.delete_data)
        row_controls.addWidget(self.btn_delete)
        layout.addLayout(row_controls)

        row_close = QHBoxLayout()
        row_close.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        row_close.addWidget(btn_close)
        layout.addLayout(row_close)

        self.refresh_status()

    @handle_errors("refreshing Google Health status display", default_return=None)
    def refresh_status(self) -> None:
        ready, readiness_error = get_connect_readiness()
        if not ready:
            self.status_view.setPlainText(readiness_error)
            self._set_actions_enabled(False)
            return

        if not self.user_id:
            self.status_view.setPlainText("No user selected.")
            self._set_actions_enabled(False)
            return

        status = get_health_integration_status(self.user_id)
        if status is None:
            self.status_view.setPlainText("Could not load health status.")
            self._set_actions_enabled(False)
            return

        self.status_view.setPlainText(format_status_text(status))
        self._set_actions_enabled(True)
        self.btn_connect.setEnabled(not status.connected)

    @handle_errors("setting Google Health dialog action state", default_return=None)
    def _set_actions_enabled(self, enabled: bool) -> None:
        for button in (
            self.btn_connect,
            self.btn_refresh,
            self.btn_enable,
            self.btn_pause,
            self.btn_sync,
            self.btn_delete,
        ):
            button.setEnabled(enabled)

    @handle_errors("starting Google Health connect from admin UI", default_return=None)
    def start_connect(self) -> None:
        if not self.user_id:
            return

        ready, error = get_connect_readiness()
        if not ready:
            QMessageBox.warning(self, "Google Health", error)
            return

        auth_url = get_connect_authorization_url(self.user_id)
        if not auth_url:
            QMessageBox.warning(self, "Google Health", "Could not build authorization URL.")
            return

        reply = QMessageBox.question(
            self,
            "Connect Google Health",
            "This opens your browser for a one-time Google sign-in.\n\n"
            "When the browser says you're connected, return here and click Refresh Status.\n\n"
            "Open the authorization page now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            webbrowser.open(auth_url)
        except Exception as exc:
            logger.warning(f"Could not open browser for Google Health OAuth: {exc}")
            QMessageBox.warning(
                self,
                "Open Browser Manually",
                f"Could not open your browser automatically.\n\nCopy this URL:\n{auth_url}",
            )

        self._set_actions_enabled(False)
        self.status_view.setPlainText(
            "Waiting for browser approval...\n\n"
            "Complete sign-in in your browser, then this panel will update automatically."
        )

        self._connect_thread = QThread()
        self._connect_worker = _ConnectFlowWorker(self.user_id)
        self._connect_worker.moveToThread(self._connect_thread)
        self._connect_thread.started.connect(self._connect_worker.run)
        self._connect_worker.finished.connect(self._on_connect_finished)
        self._connect_worker.finished.connect(self._connect_thread.quit)
        self._connect_worker.finished.connect(self._connect_worker.deleteLater)
        self._connect_thread.finished.connect(self._connect_thread.deleteLater)
        self._connect_thread.start()

    @handle_errors("handling Google Health connect completion", default_return=None)
    def _on_connect_finished(self, success: bool, error: str) -> None:
        self._connect_thread = None
        self._connect_worker = None
        self.refresh_status()
        self.user_changed.emit()

        if success:
            QMessageBox.information(
                self,
                "Google Health",
                "Connected. Sync runs automatically on your schedule.",
            )
            return

        QMessageBox.warning(
            self,
            "Connect Failed",
            error or "Google Health connect did not complete.",
        )

    @handle_errors("pausing Google Health from admin UI", default_return=None)
    def pause_health(self) -> None:
        if not self.user_id:
            return
        if pause_health_integration(self.user_id):
            self.refresh_status()
            self.user_changed.emit()
            QMessageBox.information(
                self,
                "Google Health",
                "Health personalization paused. Data is kept until you re-enable.",
            )

    @handle_errors("enabling Google Health from admin UI", default_return=None)
    def enable_health(self) -> None:
        if not self.user_id:
            return
        ok, message = enable_health_integration(self.user_id)
        self.refresh_status()
        if ok:
            self.user_changed.emit()
            QMessageBox.information(self, "Google Health", "Health personalization enabled.")
            return
        QMessageBox.warning(self, "Google Health", message or "Could not enable health.")

    @handle_errors("syncing Google Health from admin UI", default_return=None)
    def sync_now(self) -> None:
        if not self.user_id:
            return
        if sync_health_integration(self.user_id):
            self.refresh_status()
            QMessageBox.information(self, "Google Health", "Sync completed.")
            return
        QMessageBox.warning(
            self,
            "Google Health",
            "Sync did not complete. Check status and connection.",
        )

    @handle_errors("deleting Google Health data from admin UI", default_return=None)
    def delete_data(self) -> None:
        if not self.user_id:
            return
        reply = QMessageBox.question(
            self,
            "Delete Google Health Data",
            "Delete all local Google Health files for this user and disable the feature?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if delete_health_integration(self.user_id):
            self.refresh_status()
            self.user_changed.emit()
            QMessageBox.information(
                self,
                "Google Health",
                "Local Google Health data deleted and feature disabled.",
            )
