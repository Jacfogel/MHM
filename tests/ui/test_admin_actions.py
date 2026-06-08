from unittest.mock import Mock, patch

import pytest

from ui.admin_actions import AdminActions


pytestmark = [pytest.mark.ui, pytest.mark.unit]


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

