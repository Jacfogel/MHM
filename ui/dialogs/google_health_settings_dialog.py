# ui/dialogs/google_health_settings_dialog.py
# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false

"""Admin UI dialog for Google Health connect, status, and controls."""

from __future__ import annotations

import webbrowser

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from core.error_handling import handle_errors
from core import get_user_data, update_user_preferences
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


class _SyncFlowWorker(QObject):
    """Run the shared blocking sync operation outside the UI thread."""

    finished = Signal(bool)

    @handle_errors("initializing Google Health sync worker", re_raise=True)
    def __init__(self, user_id: str) -> None:
        super().__init__()
        self.user_id = user_id

    @handle_errors("running Google Health sync worker", default_return=None)
    def run(self) -> None:
        """Always report completion, including unexpected backend failures."""
        success = False
        try:
            success = self._sync()
        finally:
            self.finished.emit(success)


    @handle_errors("performing Google Health desktop sync", default_return=False)
    def _sync(self) -> bool:
        """Return a safe failure result while the outer worker owns completion."""
        return bool(sync_health_integration(self.user_id))


class GoogleHealthSettingsDialog(QDialog):
    """Per-user Google Health connect panel for the admin UI."""

    user_changed = Signal()

    @handle_errors("initializing Google Health settings dialog", default_return=None)
    def __init__(self, parent=None, user_id: str | None = None) -> None:
        """Build the connect panel for ``user_id`` (admin UI)."""
        super().__init__(parent)
        self.user_id = user_id
        self._sync_thread: QThread | None = None
        self._sync_worker: _SyncFlowWorker | None = None
        self._sync_success = False
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

        self.use_in_messages = QCheckBox("Use health data in scheduled messages")
        self.use_in_chat = QCheckBox("Use health data in chat")
        preferences = (
            ((get_user_data(user_id, "preferences", auto_create=False) or {}).get("preferences") or {})
            if user_id else {}
        )
        personalization = preferences.get("health_personalization") or {}
        self.use_in_messages.setChecked(personalization.get("use_in_messages", True) is True)
        self.use_in_chat.setChecked(personalization.get("use_in_chat", True) is True)
        layout.addWidget(self.use_in_messages)
        layout.addWidget(self.use_in_chat)
        self.btn_save_personalization = QPushButton("Save Personalization")
        self.btn_save_personalization.clicked.connect(self.save_personalization)
        self.btn_save_personalization.setEnabled(bool(user_id))
        layout.addWidget(self.btn_save_personalization)

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

    @handle_errors("saving health personalization preferences", default_return=None)
    def save_personalization(self) -> None:
        """Save independent opt-outs without enabling the account feature."""
        if not self.user_id:
            return
        if not update_user_preferences(self.user_id, {"health_personalization": {
            "use_in_messages": self.use_in_messages.isChecked(),
            "use_in_chat": self.use_in_chat.isChecked(),
        }}, auto_create=False):
            QMessageBox.warning(self, "Google Health", "Could not save personalization. Try again.")
            return
        self.user_changed.emit()
        QMessageBox.information(self, "Google Health", "Personalization preferences saved.")

    @handle_errors("refreshing Google Health status display", default_return=None)
    def refresh_status(self) -> None:
        if self._sync_thread is not None:
            self._set_actions_enabled(False)
            return
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
        self.btn_connect.setEnabled(not status.connected or status.reconnect_required)

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
        if not self.user_id or self._sync_thread is not None or self._connect_thread is not None:
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
            "After browser approval, return here and wait for the connection result.\n\n"
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
        """Start one sync; keep account controls locked until its thread exits."""
        if not self.user_id or self._sync_thread is not None or self._connect_thread is not None:
            return
        self._sync_success = False
        self._set_actions_enabled(False)
        self.status_view.setPlainText("Syncing Google Health… Please wait.")
        self._sync_thread = QThread(self)
        self._sync_worker = _SyncFlowWorker(self.user_id)
        self._sync_worker.moveToThread(self._sync_thread)
        self._sync_thread.started.connect(self._sync_worker.run)
        self._sync_worker.finished.connect(self._on_sync_result)
        self._sync_worker.finished.connect(self._sync_thread.quit)
        self._sync_worker.finished.connect(self._sync_worker.deleteLater)
        self._sync_thread.finished.connect(self._on_sync_finished)
        self._sync_thread.finished.connect(self._sync_thread.deleteLater)
        self._sync_thread.start()

    @handle_errors("recording Google Health sync result", default_return=None)
    def _on_sync_result(self, success: bool) -> None:
        """Remember the result while retaining worker references until exit."""
        self._sync_success = success

    @handle_errors("finishing Google Health desktop sync", default_return=None)
    def _on_sync_finished(self) -> None:
        """Refresh persisted status and explain the next action on failure."""
        self._sync_thread = None
        self._sync_worker = None
        self.refresh_status()
        self.user_changed.emit()
        if self._sync_success:
            QMessageBox.information(self, "Google Health", "Sync completed.")
            return
        status = get_health_integration_status(self.user_id)
        if status is not None and (not status.connected or status.reconnect_required):
            message = "Reconnect Google Health using Connect, then try Sync Now again."
        elif status is not None and status.feature_state != "enabled":
            message = "Health is paused or disabled. Enable it before syncing; reconnect if requested in status."
        else:
            message = "Sync did not complete. Check your connection and status, then try again."
        QMessageBox.warning(self, "Google Health", message)

    @handle_errors("closing Google Health dialog", default_return=None)
    def done(self, result: int) -> None:
        """Keep the dialog alive while its background worker owns a thread."""
        if self._sync_thread is None:
            super().done(result)

    @handle_errors("handling Google Health dialog close", default_return=None)
    def closeEvent(self, event) -> None:
        """Do not destroy a running sync thread when the window is closed."""
        if self._sync_thread is not None:
            event.ignore()
            return
        super().closeEvent(event)

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
