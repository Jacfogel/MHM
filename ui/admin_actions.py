"""Admin/system action helpers for the Qt management UI."""

from __future__ import annotations

import os
import webbrowser
from collections.abc import Callable
from importlib import import_module
from typing import Any

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


_lazy_dependencies = import_module("ui.lazy_dependencies")
handle_errors = _lazy_dependencies.handle_errors
get_all_user_ids = _lazy_dependencies.get_all_user_ids
get_component_logger = _lazy_dependencies.get_component_logger
get_user_data = _lazy_dependencies.get_user_data
validate_all_configuration = _lazy_dependencies.validate_all_configuration

logger = get_component_logger("ui")


def _load_attr(module_name: str, attr_name: str):
    """Load a project attribute through the UI lazy dependency boundary."""
    # ERROR_HANDLING_EXCLUDE: low-level lazy import helper; callers are decorated or fail fast.
    return _lazy_dependencies.load_attr(module_name, attr_name)


class AdminActions:
    """Run admin/system actions that are not core Qt shell responsibilities."""

    @handle_errors("toggling logging verbosity", default_return=None)
    def toggle_logging_verbosity(self, parent: QWidget, menu_action: Any) -> None:
        """Toggle logging verbosity, update the menu action, and notify the user."""
        toggle_verbose_logging = _load_attr("core.logger", "toggle_verbose_logging")

        is_verbose = toggle_verbose_logging()
        verbose_status = "ON" if is_verbose else "OFF"
        menu_action.setText(f"Toggle Verbose Logging (Currently: {verbose_status})")

        status = "enabled" if is_verbose else "disabled"
        QMessageBox.information(parent, "Logging", f"Verbose logging has been {status}")

    @handle_errors("viewing log file", default_return=None)
    def view_log_file(self) -> None:
        """Open the main log file in the default text editor."""
        log_main_file = _load_attr("core.config", "LOG_MAIN_FILE")
        webbrowser.open(log_main_file)

    @handle_errors("opening process watcher", default_return=None)
    def open_process_watcher(self, parent: QWidget) -> None:
        """Open the process watcher dialog."""
        try:
            ProcessWatcherDialog = _load_attr(
                "ui.dialogs.process_watcher_dialog", "ProcessWatcherDialog"
            )

            dialog = ProcessWatcherDialog(parent)
            dialog.show()
            logger.debug("Process watcher dialog opened")
        except Exception as e:
            logger.error(f"Error opening process watcher: {e}")
            QMessageBox.critical(parent, "Error", f"Failed to open process watcher: {e}")

    @handle_errors("viewing cache status", default_return=None)
    def view_cache_status(
        self,
        parent: QWidget,
        *,
        force_clean_cache: Callable[[], None],
    ) -> None:
        """Show cache cleanup status and information."""
        get_cleanup_status = _load_attr("core.auto_cleanup", "get_cleanup_status")
        find_pycache_dirs = _load_attr("core.auto_cleanup", "find_pycache_dirs")
        find_pyc_files = _load_attr("core.auto_cleanup", "find_pyc_files")
        calculate_cache_size = _load_attr("core.auto_cleanup", "calculate_cache_size")

        status = get_cleanup_status()
        pycache_dirs = find_pycache_dirs(".")
        pyc_files = find_pyc_files(".")
        current_size = calculate_cache_size(pycache_dirs, pyc_files)

        status_window = QDialog(parent)
        status_window.setWindowTitle("Cache Cleanup Status")
        status_window.setModal(True)
        status_window.resize(450, 350)

        layout = QVBoxLayout(status_window)

        title_label = QLabel("Cache Cleanup Status")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)

        status_text = QTextEdit()
        status_text.setReadOnly(True)
        status_text.setMaximumHeight(200)

        status_content = f"""Last cleanup: {status['last_cleanup']}
Days since cleanup: {status['days_since']}
Next cleanup: {status['next_cleanup']}

Current cache files found:
- {len(pycache_dirs)} __pycache__ directories
- {len(pyc_files)} standalone .pyc files
- Total size: {current_size / 1024:.1f} KB ({current_size / (1024 * 1024):.2f} MB)"""

        status_text.setPlainText(status_content)
        layout.addWidget(status_text)

        button_layout = QHBoxLayout()

        force_clean_button = QPushButton("Force Clean")
        force_clean_button.clicked.connect(
            lambda: [force_clean_cache(), status_window.accept()]
        )
        button_layout.addWidget(force_clean_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(status_window.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        status_window.exec()

    @handle_errors("forcing cache cleanup", default_return=None)
    def force_clean_cache(self, parent: QWidget) -> None:
        """Force cache cleanup regardless of schedule."""
        perform_cleanup = _load_attr("core.auto_cleanup", "perform_cleanup")
        update_cleanup_timestamp = _load_attr(
            "core.auto_cleanup", "update_cleanup_timestamp"
        )

        result = QMessageBox.question(
            parent,
            "Force Cache Cleanup",
            "This will force cleanup of all Python cache files regardless of when "
            "they were last cleaned.\n\nAre you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        success = perform_cleanup()
        if success:
            update_cleanup_timestamp()
            QMessageBox.information(
                parent, "Cache Cleanup", "Force cache cleanup completed successfully!"
            )
            logger.info("Force cache cleanup completed successfully")
        else:
            QMessageBox.critical(parent, "Error", "Cache cleanup failed")

    @handle_errors("validating configuration", default_return=None)
    def validate_configuration(self, parent: QWidget) -> None:
        """Show detailed configuration validation report."""
        result = validate_all_configuration()

        report_window = QDialog(parent)
        report_window.setWindowTitle("Configuration Validation Report")
        report_window.setModal(True)
        report_window.resize(700, 600)

        layout = QVBoxLayout(report_window)

        title_label = QLabel("Configuration Validation Report")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)

        summary_color = "green" if result["valid"] else "red"
        summary_icon = "[OK]" if result["valid"] else "[FAIL]"
        summary_label = QLabel(f"{summary_icon} {result['summary']}")
        summary_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        summary_label.setStyleSheet(f"color: {summary_color};")
        layout.addWidget(summary_label)

        if result["available_channels"]:
            channels_label = QLabel(
                f"Available Channels: {', '.join(result['available_channels'])}"
            )
            channels_label.setFont(QFont("Arial", 10))
            channels_label.setStyleSheet("color: blue;")
            layout.addWidget(channels_label)
        else:
            channels_label = QLabel("No communication channels available")
            channels_label.setFont(QFont("Arial", 10))
            channels_label.setStyleSheet("color: orange;")
            layout.addWidget(channels_label)

        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        if result["errors"]:
            errors_widget = QWidget()
            errors_layout = QVBoxLayout(errors_widget)
            errors_text = QTextEdit()
            errors_text.setReadOnly(True)
            for index, error in enumerate(result["errors"], 1):
                errors_text.append(f"{index}. {error}\n")
            errors_layout.addWidget(errors_text)
            tab_widget.addTab(errors_widget, f"Errors ({len(result['errors'])})")

        if result["warnings"]:
            warnings_widget = QWidget()
            warnings_layout = QVBoxLayout(warnings_widget)
            warnings_text = QTextEdit()
            warnings_text.setReadOnly(True)
            for index, warning in enumerate(result["warnings"], 1):
                warnings_text.append(f"{index}. {warning}\n")
            warnings_layout.addWidget(warnings_text)
            tab_widget.addTab(
                warnings_widget, f"Warnings ({len(result['warnings'])})"
            )

        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        config_text = QTextEdit()
        config_text.setReadOnly(True)

        config_values = self._configuration_values()
        for name, value in config_values:
            config_text.append(f"{name}: {value}\n")

        config_layout.addWidget(config_text)
        tab_widget.addTab(config_widget, "Current Configuration")

        button_layout = QHBoxLayout()

        if not result["valid"]:
            fix_button = QPushButton("Fix Configuration")
            fix_button.clicked.connect(lambda: self.show_configuration_help(report_window))
            button_layout.addWidget(fix_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(report_window.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)
        report_window.exec()

    @handle_errors("building configuration values", default_return=[])
    def _configuration_values(self) -> list[tuple[str, str]]:
        """Return display-ready configuration values for the validation dialog."""
        base_data_dir = _load_attr("core.config", "BASE_DATA_DIR")
        log_main_file = _load_attr("core.config", "LOG_MAIN_FILE")
        log_level = _load_attr("core.config", "LOG_LEVEL")
        lm_studio_base_url = _load_attr("core.config", "LM_STUDIO_BASE_URL")
        ai_timeout_seconds = _load_attr("core.config", "AI_TIMEOUT_SECONDS")
        scheduler_interval = _load_attr("core.config", "SCHEDULER_INTERVAL")
        email_smtp_server = _load_attr("core.config", "EMAIL_SMTP_SERVER")
        email_imap_server = _load_attr("core.config", "EMAIL_IMAP_SERVER")
        email_smtp_username = _load_attr("core.config", "EMAIL_SMTP_USERNAME")
        discord_bot_token = _load_attr("core.config", "DISCORD_BOT_TOKEN")

        return [
            ("Base Data Directory", str(base_data_dir)),
            ("Log File", str(log_main_file)),
            ("Log Level", str(log_level)),
            ("LM Studio URL", str(lm_studio_base_url)),
            ("AI Timeout", f"{ai_timeout_seconds}s"),
            ("Scheduler Interval", f"{scheduler_interval}s"),
            ("Email SMTP Server", email_smtp_server or "Not configured"),
            ("Email IMAP Server", email_imap_server or "Not configured"),
            ("Email Username", email_smtp_username or "Not configured"),
            (
                "Discord Bot Token",
                "Configured" if discord_bot_token else "Not configured",
            ),
        ]

    @handle_errors("showing configuration help", default_return=None)
    def show_configuration_help(self, parent_window: QWidget) -> None:
        """Show help for fixing configuration issues."""
        help_window = QDialog(parent_window)
        help_window.setWindowTitle("Configuration Help")
        help_window.setModal(True)
        help_window.resize(600, 500)

        layout = QVBoxLayout(help_window)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        layout.addWidget(help_text)
        help_text.setPlainText(CONFIGURATION_HELP_TEXT)

        close_button = QPushButton("Close")
        close_button.clicked.connect(help_window.accept)
        layout.addWidget(close_button)

        help_window.exec()

    @handle_errors("viewing all users summary", user_friendly=True, default_return=None)
    def view_all_users_summary(self, parent: QWidget) -> None:
        """Show a summary of all users in the system."""
        user_ids = get_all_user_ids()

        summary_window = QDialog(parent)
        summary_window.setWindowTitle("All Users Summary")
        summary_window.setModal(True)
        summary_window.resize(600, 400)

        layout = QVBoxLayout(summary_window)

        title_label = QLabel("All Users Summary")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)

        text_widget = QTextEdit()
        text_widget.setReadOnly(True)
        layout.addWidget(text_widget)

        text_widget.setPlainText(self._build_all_users_summary(user_ids))

        close_button = QPushButton("Close")
        close_button.clicked.connect(summary_window.accept)
        layout.addWidget(close_button)

        summary_window.exec()

    @handle_errors(
        "building all users summary",
        user_friendly=False,
        default_return="Unable to build users summary.\n",
    )
    def _build_all_users_summary(self, user_ids: list[str]) -> str:
        """Build the plain-text all-users summary body."""
        if not user_ids:
            return "No users found in the system.\n"

        summary_text = f"Total users: {len(user_ids)}\n\n"
        for user_id in user_ids:
            user_data_result = get_user_data(user_id, "account")
            user_account = user_data_result.get("account")
            context_result = get_user_data(user_id, "context")
            user_context = context_result.get("context")
            if not user_account:
                continue

            username = user_account.get("internal_username", "Unknown")
            preferred_name = user_context.get("preferred_name", "") if user_context else ""
            prefs_result = get_user_data(user_id, "preferences")
            prefs = prefs_result.get("preferences", {})
            categories = prefs.get("categories", [])
            messaging_service = prefs.get("channel", {}).get("type", "Unknown")

            summary_text += f"User: {username}"
            if preferred_name:
                summary_text += f" ({preferred_name})"
            summary_text += "\n"
            summary_text += f"  ID: {user_id}\n"
            summary_text += f"  Service: {messaging_service}\n"
            summary_text += (
                f"  Categories: {', '.join(categories) if categories else 'None'}\n"
            )
            summary_text += "\n"

        return summary_text

    @handle_errors(
        "performing system health check", user_friendly=True, default_return=None
    )
    def system_health_check(
        self,
        parent: QWidget,
        *,
        service_manager: Any,
        create_communication_manager: Callable[[], Any],
    ) -> None:
        """Perform a basic system health check."""
        health_window = QDialog(parent)
        health_window.setWindowTitle("System Health Check")
        health_window.setModal(True)
        health_window.resize(500, 400)

        layout = QVBoxLayout(health_window)

        title_label = QLabel("System Health Check")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)

        text_widget = QTextEdit()
        text_widget.setReadOnly(True)
        layout.addWidget(text_widget)

        text_widget.setPlainText(
            self._build_system_health_report(
                service_manager=service_manager,
                create_communication_manager=create_communication_manager,
            )
        )

        close_button = QPushButton("Close")
        close_button.clicked.connect(health_window.accept)
        layout.addWidget(close_button)

        health_window.exec()

    @handle_errors(
        "building system health report",
        user_friendly=False,
        default_return="Unable to build system health report.\n",
    )
    def _build_system_health_report(
        self,
        *,
        service_manager: Any,
        create_communication_manager: Callable[[], Any],
    ) -> str:
        """Build the system health report text."""
        lines = ["Running system health checks...", ""]

        is_running, pid = service_manager.is_service_running()
        lines.append(f"[OK] Service Status: {'Running' if is_running else 'Stopped'}")
        if is_running:
            lines.append(f" (PID: {pid})")
        lines.append("")

        if is_running:
            lines.extend(self._discord_health_lines(create_communication_manager))
        else:
            lines.append("[INFO] Discord Status: Service not running")

        user_ids = get_all_user_ids()
        lines.append(f"[OK] Total Users: {len(user_ids)}")

        base_data_dir = _load_attr("core.config", "BASE_DATA_DIR")
        user_info_dir_path = _load_attr("core.config", "USER_INFO_DIR_PATH")
        for dir_path in [base_data_dir, user_info_dir_path]:
            exists = os.path.exists(dir_path)
            status = "[OK]" if exists else "[FAIL]"
            lines.append(f"{status} Directory {dir_path}: {'Exists' if exists else 'Missing'}")

        lines.append("")
        lines.append("Checking for common issues...")
        if os.path.exists(user_info_dir_path):
            orphaned_files = 0
            for _root, _dirs, files in os.walk(user_info_dir_path):
                for file_name in files:
                    if file_name.endswith(".json"):
                        user_id = file_name.replace(".json", "")
                        if user_id not in user_ids:
                            orphaned_files += 1

            if orphaned_files == 0:
                lines.append("[OK] No orphaned message files found")
            else:
                lines.append(f"[WARN] Found {orphaned_files} orphaned message files")

        lines.append("")
        lines.append("Health check complete.")
        return "\n".join(lines) + "\n"

    @handle_errors(
        "checking Discord health for admin report",
        user_friendly=False,
        default_return=["[INFO] Discord Status: Unable to check"],
    )
    def _discord_health_lines(
        self, create_communication_manager: Callable[[], Any]
    ) -> list[str]:
        """Return Discord connectivity health lines."""
        comm_manager = create_communication_manager()
        discord_status = comm_manager.get_channel_connectivity_status("discord")
        if not discord_status:
            return ["[INFO] Discord Status: Unable to check"]

        connection_status = discord_status.get("connection_status", "unknown")
        if connection_status == "connected":
            latency = discord_status.get("latency", "unknown")
            guild_count = discord_status.get("guild_count", "unknown")
            return [
                "[OK] Discord Status: Connected "
                f"(Latency: {latency}s, Guilds: {guild_count})"
            ]

        lines = [f"[WARN] Discord Status: {connection_status.title()}"]
        detailed_errors = discord_status.get("detailed_errors", {})
        for error_type, error_info in detailed_errors.items():
            error_msg = error_info.get("error_message", "Unknown error")
            lines.append(f"  - {error_type.title()}: {error_msg}")
        return lines


CONFIGURATION_HELP_TEXT = """
CONFIGURATION HELP

To fix configuration issues, set up environment variables. Create a .env file in
the MHM root directory with the following variables:

REQUIRED SETTINGS:
=================

1. COMMUNICATION CHANNELS (at least one required):
   - For Email: EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD
   - For Discord: DISCORD_BOT_TOKEN

2. AI CONFIGURATION:
   - LM_STUDIO_BASE_URL (default: http://localhost:1234/v1)
   - LM_STUDIO_API_KEY (default: lm-studio)
   - LM_STUDIO_MODEL (default: deepseek-llm-7b-chat)

OPTIONAL SETTINGS:
=================

- BASE_DATA_DIR (default: data)
- LOG_MAIN_FILE (default: app.log)
- LOG_LEVEL (default: INFO)
- AI_TIMEOUT_SECONDS (default: 30)
- SCHEDULER_INTERVAL (default: 60)
- AUTO_CREATE_USER_DIRS (default: true)

EXAMPLE .env FILE:
=================

EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_SMTP_USERNAME=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password

# OR for Discord:
DISCORD_BOT_TOKEN=your-discord-bot-token

# AI Configuration:
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_MODEL=deepseek-llm-7b-chat

# Optional settings:
LOG_LEVEL=INFO
AI_TIMEOUT_SECONDS=30
SCHEDULER_INTERVAL=60

SETUP INSTRUCTIONS:
==================

1. Create a .env file in the MHM root directory
2. Add the required environment variables
3. Restart the MHM application
4. Run "Validate Configuration" again to check

For detailed setup instructions, see the ui/UI_GUIDE.md file.
""".strip()
