from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QWidget

from ui.admin_actions import CONFIGURATION_HELP_TEXT, AdminActions


pytestmark = [pytest.mark.ui, pytest.mark.unit]


@pytest.fixture(scope="module")
def qapp():
    """Provide a process-wide QApplication for dialog-constructing admin actions."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_build_all_users_summary_uses_user_data_sections():
    actions = AdminActions()

    def fake_get_user_data(user_id, section, **_kwargs):
        data = {
            "account": {"account": {"internal_username": "test-user"}},
            "context": {"context": {"preferred_name": "Tester"}},
            "preferences": {
                "preferences": {
                    "categories": ["health", "work"],
                    "channel": {"type": "discord"},
                }
            },
        }
        return data[section]

    with patch("ui.admin_actions.get_user_data", side_effect=fake_get_user_data):
        summary = actions._build_all_users_summary(["user-1"])

    assert "Total users: 1" in summary
    assert "User: test-user (Tester)" in summary
    assert "Service: discord" in summary
    assert "Categories: health, work" in summary


def test_build_system_health_report_includes_service_users_and_directories():
    actions = AdminActions()
    service_manager = Mock()
    service_manager.is_service_running.return_value = (False, None)

    def fake_load_attr(module_name, attr_name):
        values = {
            ("core.config", "BASE_DATA_DIR"): "data",
            ("core.config", "USER_INFO_DIR_PATH"): "users",
        }
        return values[(module_name, attr_name)]

    with patch("ui.admin_actions.get_all_user_ids", return_value=["user-1"]), \
        patch("ui.admin_actions._load_attr", side_effect=fake_load_attr), \
        patch("ui.admin_actions.os.path.exists", return_value=True), \
        patch("ui.admin_actions.os.walk", return_value=[]):
        report = actions._build_system_health_report(
            service_manager=service_manager,
            create_communication_manager=Mock(),
        )

    assert "[OK] Service Status: Stopped" in report
    assert "[INFO] Discord Status: Service not running" in report
    assert "[OK] Total Users: 1" in report
    assert "[OK] Directory data: Exists" in report


def test_toggle_logging_verbosity_updates_action_and_notifies_parent():
    actions = AdminActions()
    parent = Mock()
    action = Mock()

    with patch("ui.admin_actions._load_attr", return_value=lambda: True), \
        patch("ui.admin_actions.QMessageBox") as msgbox:
        actions.toggle_logging_verbosity(parent, action)

    action.setText.assert_called_once_with("Toggle Verbose Logging (Currently: ON)")
    msgbox.information.assert_called_once_with(
        parent, "Logging", "Verbose logging has been enabled"
    )


def test_toggle_logging_verbosity_off_updates_action():
    actions = AdminActions()
    parent = Mock()
    action = Mock()

    with patch("ui.admin_actions._load_attr", return_value=lambda: False), \
        patch("ui.admin_actions.QMessageBox") as msgbox:
        actions.toggle_logging_verbosity(parent, action)

    action.setText.assert_called_once_with("Toggle Verbose Logging (Currently: OFF)")
    msgbox.information.assert_called_once_with(
        parent, "Logging", "Verbose logging has been disabled"
    )


def test_view_log_file_opens_browser():
    actions = AdminActions()

    with patch("ui.admin_actions._load_attr", return_value="logs/app.log"), \
        patch("ui.admin_actions.webbrowser.open") as mock_open:
        actions.view_log_file()

    mock_open.assert_called_once_with("logs/app.log")


def test_open_process_watcher_shows_dialog():
    actions = AdminActions()
    parent = Mock()
    dialog = Mock()
    dialog_cls = Mock(return_value=dialog)

    with patch("ui.admin_actions._load_attr", return_value=dialog_cls):
        actions.open_process_watcher(parent)

    dialog_cls.assert_called_once_with(parent)
    dialog.show.assert_called_once()


def test_open_process_watcher_reports_load_failure():
    actions = AdminActions()
    parent = Mock()

    with patch("ui.admin_actions._load_attr", side_effect=ImportError("missing")), \
        patch("ui.admin_actions.QMessageBox") as msgbox:
        actions.open_process_watcher(parent)

    msgbox.critical.assert_called_once()
    assert "Failed to open process watcher" in msgbox.critical.call_args.args[2]


def test_force_clean_cache_cancelled_does_not_clean():
    actions = AdminActions()
    parent = Mock()
    perform_cleanup = Mock()

    def fake_load(_module, attr):
        return perform_cleanup if attr == "perform_cleanup" else Mock()

    with patch("ui.admin_actions._load_attr", side_effect=fake_load), \
        patch(
            "ui.admin_actions.QMessageBox.question",
            return_value=QMessageBox.StandardButton.No,
        ):
        actions.force_clean_cache(parent)

    perform_cleanup.assert_not_called()


def test_force_clean_cache_success_updates_timestamp():
    actions = AdminActions()
    parent = Mock()
    perform_cleanup = Mock(return_value=True)
    update_timestamp = Mock()

    def fake_load(_module, attr):
        if attr == "perform_cleanup":
            return perform_cleanup
        return update_timestamp

    with patch("ui.admin_actions._load_attr", side_effect=fake_load), \
        patch(
            "ui.admin_actions.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ), \
        patch("ui.admin_actions.QMessageBox.information") as mock_info:
        actions.force_clean_cache(parent)

    perform_cleanup.assert_called_once()
    update_timestamp.assert_called_once()
    mock_info.assert_called_once()


def test_force_clean_cache_failure_shows_critical():
    actions = AdminActions()
    parent = Mock()
    perform_cleanup = Mock(return_value=False)

    def fake_load(_module, attr):
        return perform_cleanup if attr == "perform_cleanup" else Mock()

    with patch("ui.admin_actions._load_attr", side_effect=fake_load), \
        patch(
            "ui.admin_actions.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ), \
        patch("ui.admin_actions.QMessageBox.critical") as mock_critical:
        actions.force_clean_cache(parent)

    mock_critical.assert_called_once_with(parent, "Error", "Cache cleanup failed")


def test_build_all_users_summary_empty_and_skips_missing_account():
    actions = AdminActions()

    assert "No users found" in actions._build_all_users_summary([])

    with patch(
        "ui.admin_actions.get_user_data",
        return_value={"account": None, "context": {}, "preferences": {}},
    ):
        summary = actions._build_all_users_summary(["missing-user"])

    assert "Total users: 1" in summary
    assert "User:" not in summary


def test_discord_health_lines_connected_and_error_paths():
    actions = AdminActions()

    connected = Mock()
    connected.get_channel_connectivity_status.return_value = {
        "connection_status": "connected",
        "latency": 0.12,
        "guild_count": 2,
    }
    connected_lines = actions._discord_health_lines(lambda: connected)
    assert connected_lines[0].startswith("[OK] Discord Status: Connected")

    missing = Mock()
    missing.get_channel_connectivity_status.return_value = None
    assert actions._discord_health_lines(lambda: missing) == [
        "[INFO] Discord Status: Unable to check"
    ]

    disconnected = Mock()
    disconnected.get_channel_connectivity_status.return_value = {
        "connection_status": "disconnected",
        "detailed_errors": {
            "token": {"error_message": "invalid token"},
        },
    }
    disconnected_lines = actions._discord_health_lines(lambda: disconnected)
    assert disconnected_lines[0] == "[WARN] Discord Status: Disconnected"
    assert "invalid token" in disconnected_lines[1]


def test_build_system_health_report_running_service_and_orphans():
    actions = AdminActions()
    service_manager = Mock()
    service_manager.is_service_running.return_value = (True, 4242)
    comm_manager = Mock()
    comm_manager.get_channel_connectivity_status.return_value = {
        "connection_status": "connected",
        "latency": 0.2,
        "guild_count": 1,
    }

    def fake_load_attr(module_name, attr_name):
        values = {
            ("core.config", "BASE_DATA_DIR"): "data",
            ("core.config", "USER_INFO_DIR_PATH"): "users",
        }
        return values[(module_name, attr_name)]

    with patch("ui.admin_actions.get_all_user_ids", return_value=["user-1"]), \
        patch("ui.admin_actions._load_attr", side_effect=fake_load_attr), \
        patch("ui.admin_actions.os.path.exists", return_value=True), \
        patch(
            "ui.admin_actions.os.walk",
            return_value=[("users", [], ["user-1.json", "orphan.json"])],
        ):
        report = actions._build_system_health_report(
            service_manager=service_manager,
            create_communication_manager=lambda: comm_manager,
        )

    assert "PID: 4242" in report
    assert "[OK] Discord Status: Connected" in report
    assert "[WARN] Found 1 orphaned message files" in report


def test_configuration_values_masks_discord_token():
    actions = AdminActions()

    def fake_load(_module, attr):
        values = {
            "BASE_DATA_DIR": "data",
            "LOG_MAIN_FILE": "app.log",
            "LOG_LEVEL": "INFO",
            "LM_STUDIO_BASE_URL": "http://localhost:1234/v1",
            "AI_TIMEOUT_SECONDS": 30,
            "SCHEDULER_INTERVAL": 60,
            "EMAIL_SMTP_SERVER": "",
            "EMAIL_IMAP_SERVER": "",
            "EMAIL_SMTP_USERNAME": "",
            "DISCORD_BOT_TOKEN": "secret-token",
        }
        return values[attr]

    with patch("ui.admin_actions._load_attr", side_effect=fake_load):
        values = dict(actions._configuration_values())

    assert values["Discord Bot Token"] == "Configured"
    assert values["Email SMTP Server"] == "Not configured"
    assert values["AI Timeout"] == "30s"


def test_view_cache_status_builds_dialog(qapp):
    actions = AdminActions()
    parent = QWidget()
    force_clean = Mock()

    def fake_load(_module, attr):
        if attr == "get_cleanup_status":
            return lambda: {
                "last_cleanup": "never",
                "days_since": 9,
                "next_cleanup": "soon",
            }
        if attr == "find_pycache_dirs":
            return lambda _root: ["__pycache__"]
        if attr == "find_pyc_files":
            return lambda _root: ["x.pyc"]
        if attr == "calculate_cache_size":
            return lambda _dirs, _files: 2048
        raise AssertionError(attr)

    with patch("ui.admin_actions._load_attr", side_effect=fake_load), \
        patch.object(QDialog, "exec", return_value=0) as mock_exec:
        actions.view_cache_status(parent, force_clean_cache=force_clean)

    mock_exec.assert_called_once()
    parent.deleteLater()


def test_validate_configuration_valid_and_invalid_reports(qapp):
    actions = AdminActions()
    parent = QWidget()

    valid_result = {
        "valid": True,
        "summary": "All good",
        "available_channels": ["discord"],
        "errors": [],
        "warnings": [],
    }
    invalid_result = {
        "valid": False,
        "summary": "Missing channels",
        "available_channels": [],
        "errors": ["No channel configured"],
        "warnings": ["LM Studio URL uses default"],
    }

    with patch("ui.admin_actions.validate_all_configuration", return_value=valid_result), \
        patch("ui.admin_actions.AdminActions._configuration_values", return_value=[("Log Level", "INFO")]), \
        patch.object(QDialog, "exec", return_value=0):
        actions.validate_configuration(parent)

    with patch("ui.admin_actions.validate_all_configuration", return_value=invalid_result), \
        patch("ui.admin_actions.AdminActions._configuration_values", return_value=[("Log Level", "INFO")]), \
        patch.object(QDialog, "exec", return_value=0):
        actions.validate_configuration(parent)

    parent.deleteLater()


def test_show_configuration_help_and_summary_windows(qapp):
    actions = AdminActions()
    parent = QWidget()

    with patch.object(QDialog, "exec", return_value=0) as mock_exec:
        actions.show_configuration_help(parent)
        with patch("ui.admin_actions.get_all_user_ids", return_value=[]), \
            patch.object(actions, "_build_all_users_summary", return_value="No users found in the system.\n"):
            actions.view_all_users_summary(parent)
        with patch.object(
            actions,
            "_build_system_health_report",
            return_value="Health check complete.\n",
        ):
            actions.system_health_check(
                parent,
                service_manager=Mock(),
                create_communication_manager=Mock(),
            )

    assert mock_exec.call_count == 3
    assert "REQUIRED SETTINGS" in CONFIGURATION_HELP_TEXT
    parent.deleteLater()

