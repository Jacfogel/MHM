from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from ui.ui_app_qt import MHMManagerUI


class _FakeComboBox:
    def __init__(self):
        self.items = []
        self.current_index = None

    def clear(self):
        self.items.clear()

    def addItem(self, text):
        self.items.append(text)

    def count(self):
        return len(self.items)

    def itemText(self, index):
        return self.items[index]

    def setCurrentIndex(self, index):
        self.current_index = index


@pytest.fixture
def ui_instance():
    obj = MHMManagerUI.__new__(MHMManagerUI)
    obj.ui = SimpleNamespace(comboBox_users=_FakeComboBox())
    obj.on_user_selected = Mock()
    return obj


@pytest.mark.ui
class TestUIUserComboHelpers:
    def test_reset_user_combo_box(self, ui_instance):
        ui_instance.ui.comboBox_users.addItem("old")
        ui_instance._reset_user_combo_box()
        assert ui_instance.ui.comboBox_users.items == ["Select a user..."]

    def test_build_enabled_features(self, ui_instance):
        user_account = {
            "features": {
                "automated_messages": "enabled",
                "checkins": "enabled",
                "task_management": "enabled",
            }
        }
        user_preferences = {"categories": ["motivational", "wellness"]}

        result = ui_instance._build_enabled_features(user_account, user_preferences)

        assert result == [
            "automated_messages",
            "motivational",
            "wellness",
            "checkins",
            "task_management",
        ]

    def test_collect_active_users_for_combo_filters_and_sorts(self, ui_instance):
        def _get_user_data(user_id, _fields):
            if user_id == "u1":
                return {
                    "account": {"account_status": "inactive", "internal_username": "zeta"},
                    "preferences": {},
                    "context": {},
                }
            if user_id == "u2":
                return {
                    "account": {
                        "account_status": "active",
                        "internal_username": "alpha",
                        "features": {"checkins": "enabled"},
                    },
                    "preferences": {"channel": {"type": "email"}},
                    "context": {"preferred_name": "Ann"},
                }
            return {
                "account": {
                    "account_status": "active",
                    "internal_username": "beta",
                    "features": {"task_management": "enabled"},
                },
                "preferences": {"channel": {"type": "discord"}},
                "context": {"preferred_name": ""},
            }

        with (
            patch("ui.ui_app_qt.get_all_user_ids", return_value=["u1", "u3", "u2"]),
            patch("ui.ui_app_qt.get_user_data", side_effect=_get_user_data),
        ):
            users = ui_instance._collect_active_users_for_combo()

        assert [u["user_id"] for u in users] == ["u2", "u3"]
        assert users[0]["channel_type"] == "email"
        assert users[1]["channel_type"] == "discord"

    def test_build_user_combo_display_name_with_feature_summary(self, ui_instance):
        display = ui_instance._build_user_combo_display_name(
            {
                "user_id": "u1",
                "internal_username": "jdoe",
                "channel_type": "email",
                "enabled_features": [
                    "automated_messages",
                    "daily_motivation",
                    "checkins",
                    "task_management",
                ],
            }
        )

        assert display == (
            "jdoe (email) [Messages: Daily Motivation, Check-ins, Tasks] - u1"
        )

    def test_reselect_user_if_present_selects_and_calls_handler(self, ui_instance):
        combo = ui_instance.ui.comboBox_users
        combo.items = [
            "Select a user...",
            "alpha (email) - user-alpha",
            "beta (discord) - user-beta",
        ]

        ui_instance._reselect_user_if_present("user-beta")

        assert combo.current_index == 2
        ui_instance.on_user_selected.assert_called_once_with("beta (discord) - user-beta")

    def test_refresh_user_list_fallback_populates_display_names(self, ui_instance):
        def _get_user_data(user_id, section):
            if section == "account":
                return {"account": {"internal_username": f"name-{user_id}"}}
            if user_id == "u1":
                return {"context": {"preferred_name": "Preferred"}}
            return {"context": {}}

        with (
            patch("ui.ui_app_qt.get_all_user_ids", return_value=["u1", "u2"]),
            patch("ui.ui_app_qt.get_user_data", side_effect=_get_user_data),
        ):
            ui_instance._refresh_user_list_fallback(Exception("primary failed"))

        assert ui_instance.ui.comboBox_users.items == [
            "Select a user...",
            "Preferred (name-u1) - u1",
            "name-u2 - u2",
        ]
