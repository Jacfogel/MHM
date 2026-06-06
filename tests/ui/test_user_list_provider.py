from unittest.mock import patch

import pytest

from ui.user_list_provider import UserListProvider


pytestmark = [pytest.mark.ui, pytest.mark.unit]


@pytest.fixture
def provider():
    return UserListProvider()


@pytest.mark.ui
class TestUserListProvider:
    def test_build_enabled_features(self, provider):
        user_account = {
            "features": {
                "automated_messages": "enabled",
                "checkins": "enabled",
                "task_management": "enabled",
            }
        }
        user_preferences = {"categories": ["motivational", "wellness"]}

        result = provider.build_enabled_features(user_account, user_preferences)

        assert result == [
            "automated_messages",
            "motivational",
            "wellness",
            "checkins",
            "task_management",
        ]

    def test_collect_active_users_for_combo_filters_and_sorts(self, provider):
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
            patch(
                "ui.user_list_provider.get_all_user_ids",
                return_value=["u1", "u3", "u2"],
            ),
            patch("ui.user_list_provider.get_user_data", side_effect=_get_user_data),
        ):
            users = provider.collect_active_users_for_combo()

        assert [u["user_id"] for u in users] == ["u2", "u3"]
        assert users[0]["channel_type"] == "email"
        assert users[1]["channel_type"] == "discord"

    def test_build_user_combo_display_name_with_feature_summary(self, provider):
        display = provider.build_user_combo_display_name(
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

    def test_collect_fallback_display_names(self, provider):
        def _get_user_data(user_id, section):
            if section == "account":
                return {"account": {"internal_username": f"name-{user_id}"}}
            if user_id == "u1":
                return {"context": {"preferred_name": "Preferred"}}
            return {"context": {}}

        with (
            patch("ui.user_list_provider.get_all_user_ids", return_value=["u1", "u2"]),
            patch("ui.user_list_provider.get_user_data", side_effect=_get_user_data),
        ):
            names = provider.collect_fallback_display_names()

        assert names == [
            "Preferred (name-u1) - u1",
            "name-u2 - u2",
        ]

    def test_parse_user_id_from_display(self):
        assert UserListProvider.parse_user_id_from_display("alpha (email) - user-1") == (
            "user-1"
        )
        assert UserListProvider.parse_user_id_from_display("Select a user...") is None
        assert UserListProvider.parse_user_id_from_display("no-id-here") is None

    def test_find_reselect_index(self):
        items = [
            "Select a user...",
            "alpha (email) - user-alpha",
            "beta (discord) - user-beta",
        ]
        assert UserListProvider.find_reselect_index(items, "user-beta") == 2
        assert UserListProvider.find_reselect_index(items, None) is None

    def test_load_category_names_supports_list_and_dict(self, provider):
        with patch(
            "ui.user_list_provider.get_user_data",
            return_value={"preferences": {"categories": ["motivational", "health"]}},
        ):
            assert provider.load_category_names("u1") == ["motivational", "health"]

        with patch(
            "ui.user_list_provider.get_user_data",
            return_value={"preferences": {"categories": {"a": {}, "b": {}}}},
        ):
            assert provider.load_category_names("u1") == ["a", "b"]
