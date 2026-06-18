"""Tests for core.admin_account_provisioning."""

import os
import time
import uuid
from pathlib import Path

import pytest

from core.admin_account_provisioning import (
    build_features_dict,
    build_user_preferences_from_account_data,
    determine_chat_id,
    provision_admin_account,
)
from tests.test_helpers.test_support.test_helpers import wait_until


def _resolve_user_id_with_retry(
    internal_username: str,
    test_data_dir: str | None = None,
    attempts: int = 200,
    delay: float = 0.05,
) -> str | None:
    """Resolve internal_username -> user_id with index + on-disk fallback."""
    from core import get_user_id_by_identifier
    from core.file_locking import safe_json_read

    for attempt in range(attempts):
        user_id = get_user_id_by_identifier(internal_username)
        if user_id:
            return user_id

        if test_data_dir:
            users_dir = Path(test_data_dir) / "users"
            if users_dir.exists():
                for account_file in users_dir.glob("*/account.json"):
                    account = safe_json_read(str(account_file), default={})
                    account_internal_username = str(
                        account.get("internal_username", "")
                    ).strip()
                    account_username = str(account.get("username", "")).strip()
                    if (
                        account_internal_username.casefold()
                        == internal_username.casefold()
                        or account_username.casefold() == internal_username.casefold()
                    ):
                        return account_file.parent.name

        if attempt < attempts - 1:
            time.sleep(delay)
    return None


@pytest.mark.unit
@pytest.mark.user
class TestAdminAccountProvisioningHelpers:
    def test_determine_chat_id_email(self):
        assert determine_chat_id("email", "a@b.com", "", "") == "a@b.com"

    def test_determine_chat_id_discord(self):
        assert determine_chat_id("discord", "", "", "123456") == "123456"

    def test_determine_chat_id_unknown(self):
        assert determine_chat_id("sms", "a@b.com", "555", "123") == ""

    def test_build_features_dict_all_enabled(self):
        features = build_features_dict(
            {"messages": True, "tasks": True, "checkins": True}
        )
        assert features == {
            "automated_messages": "enabled",
            "task_management": "enabled",
            "checkins": "enabled",
        }

    def test_build_features_dict_all_disabled(self):
        features = build_features_dict(
            {"messages": False, "tasks": False, "checkins": False}
        )
        assert features == {
            "automated_messages": "disabled",
            "task_management": "disabled",
            "checkins": "disabled",
        }

    def test_build_user_preferences_includes_feature_settings(self):
        account_data = {
            "username": "testuser",
            "timezone": "America/Regina",
            "channel": {"type": "discord"},
            "contact_info": {"email": "", "phone": "", "discord": "999"},
            "categories": ["motivational"],
            "task_settings": {
                "enabled": True,
                "tags": ["work"],
                "reminder_lead_time": 30,
            },
            "checkin_settings": {"enabled": True, "frequency": "daily"},
            "features_enabled": {"messages": True, "tasks": True, "checkins": True},
            "personalization_data": {"preferred_name": "Test"},
        }

        prefs = build_user_preferences_from_account_data(account_data)

        assert prefs["internal_username"] == "testuser"
        assert prefs["chat_id"] == "999"
        assert prefs["categories"] == ["motivational"]
        assert "enabled" not in prefs["task_settings"]
        assert prefs["task_settings"]["tags"] == ["work"]
        assert "enabled" not in prefs["checkin_settings"]
        assert prefs["checkin_settings"]["frequency"] == "daily"


@pytest.mark.integration
@pytest.mark.user
class TestProvisionAdminAccount:
    def test_provision_admin_account_creates_user(self, test_data_dir):
        account_data = {
            "username": "provision_test_user",
            "timezone": "America/Regina",
            "channel": {"type": "discord"},
            "contact_info": {"email": "", "phone": "", "discord": "111222333"},
            "categories": [],
            "task_settings": {},
            "checkin_settings": {},
            "features_enabled": {
                "messages": False,
                "tasks": False,
                "checkins": False,
            },
            "personalization_data": {},
        }

        user_id = provision_admin_account(account_data)

        assert user_id is not None

        from core import get_user_data, get_user_id_by_identifier

        account = get_user_data(user_id, "account")
        assert account["account"]["internal_username"] == "provision_test_user"
        assert get_user_id_by_identifier("provision_test_user") == user_id


@pytest.mark.integration
@pytest.mark.user
class TestProvisionAdminAccountBehavior:
    """Integration tests for provision_admin_account persistence and side effects."""

    def test_provision_admin_account_creates_user_files(self, test_data_dir):
        unique_username = f"test-create-user-{uuid.uuid4().hex[:8]}"
        account_data = {
            "username": unique_username,
            "preferred_name": "Test Create User",
            "timezone": "America/New_York",
            "channel": {"type": "email", "contact": "test@example.com"},
            "contact_info": {"email": "test@example.com", "phone": "", "discord": ""},
            "categories": ["motivational", "health"],
            "features_enabled": {"messages": True, "tasks": False, "checkins": False},
            "task_settings": {},
            "checkin_settings": {},
            "personalization_data": {},
        }

        user_id = provision_admin_account(account_data)
        assert user_id is not None

        resolved_user_id = _resolve_user_id_with_retry(
            unique_username, test_data_dir=test_data_dir
        )
        assert resolved_user_id is not None

        user_dir = os.path.join(test_data_dir, "users", resolved_user_id)
        assert os.path.exists(user_dir)
        assert os.path.exists(os.path.join(user_dir, "account.json"))
        assert os.path.exists(os.path.join(user_dir, "preferences.json"))

    def test_provision_admin_account_persists_categories(self, test_data_dir):
        from core import get_user_data

        unique_username = f"test-categories-user-{uuid.uuid4().hex[:8]}"
        test_categories = ["motivational", "health", "fun_facts"]
        account_data = {
            "username": unique_username,
            "preferred_name": "Test Categories User",
            "timezone": "America/New_York",
            "channel": {"type": "email", "contact": "test@example.com"},
            "contact_info": {"email": "test@example.com", "phone": "", "discord": ""},
            "categories": test_categories,
            "features_enabled": {"messages": True, "tasks": False, "checkins": False},
            "task_settings": {},
            "checkin_settings": {},
            "personalization_data": {},
        }

        assert provision_admin_account(account_data) is not None

        user_id = _resolve_user_id_with_retry(
            unique_username, test_data_dir=test_data_dir
        )
        assert user_id is not None

        preferences = get_user_data(user_id, "preferences").get("preferences", {})
        assert set(preferences["categories"]) == set(test_categories)

    @pytest.mark.no_parallel  # shared user index and test_data_dir under xdist
    def test_provision_admin_account_persists_channel_info(self, test_data_dir):
        from core import get_user_data

        unique_username = f"test-channel-user-{uuid.uuid4().hex[:8]}"
        account_data = {
            "username": unique_username,
            "preferred_name": "Test Channel User",
            "timezone": "America/New_York",
            "channel": {"type": "discord", "contact": "user#1234"},
            "contact_info": {"email": "", "phone": "", "discord": "user#1234"},
            "categories": ["motivational"],
            "features_enabled": {"messages": True, "tasks": False, "checkins": False},
            "task_settings": {},
            "checkin_settings": {},
            "personalization_data": {},
        }

        assert provision_admin_account(account_data) is not None

        user_id = _resolve_user_id_with_retry(
            unique_username, test_data_dir=test_data_dir
        )
        assert user_id is not None

        preferences = get_user_data(user_id, "preferences").get("preferences", {})
        assert preferences["channel"]["type"] == "discord"
        assert (
            preferences.get("discord_user_id") == "user#1234"
            or preferences["channel"].get("contact") == "user#1234"
        )

    def test_provision_admin_account_persists_task_settings(self, test_data_dir):
        from core import get_user_data

        unique_username = f"test-tasks-user-{uuid.uuid4().hex[:8]}"
        task_settings = {
            "time_periods": {
                "morning": {
                    "start_time": "09:00",
                    "end_time": "12:00",
                    "days": ["Monday", "Tuesday"],
                }
            },
            "tags": ["work", "personal"],
        }
        account_data = {
            "username": unique_username,
            "preferred_name": "Test Tasks User",
            "timezone": "America/New_York",
            "channel": {"type": "email", "contact": "test@example.com"},
            "contact_info": {"email": "test@example.com", "phone": "", "discord": ""},
            "categories": ["motivational"],
            "features_enabled": {"messages": True, "tasks": True, "checkins": False},
            "task_settings": task_settings,
            "checkin_settings": {},
            "personalization_data": {},
        }

        assert provision_admin_account(account_data) is not None

        user_id = _resolve_user_id_with_retry(
            unique_username, test_data_dir=test_data_dir
        )
        assert user_id is not None

        saved_task_settings = (
            get_user_data(user_id, "preferences").get("preferences", {})[
                "task_settings"
            ]
        )
        if "time_periods" in saved_task_settings:
            assert "morning" in saved_task_settings["time_periods"]
        assert set(saved_task_settings["tags"]) == {"work", "personal"}

    @pytest.mark.no_parallel  # shared user index and test_data_dir under xdist
    def test_provision_admin_account_persists_checkin_settings(self, test_data_dir):
        from core import get_user_data

        unique_username = f"test-checkins-user-{uuid.uuid4().hex[:8]}"
        checkin_settings = {
            "time_periods": {
                "afternoon": {
                    "start_time": "14:00",
                    "end_time": "17:00",
                    "days": ["Monday", "Wednesday", "Friday"],
                }
            }
        }
        account_data = {
            "username": unique_username,
            "preferred_name": "Test Checkins User",
            "timezone": "America/New_York",
            "channel": {"type": "email", "contact": "test@example.com"},
            "contact_info": {"email": "test@example.com", "phone": "", "discord": ""},
            "categories": ["motivational"],
            "features_enabled": {"messages": True, "tasks": False, "checkins": True},
            "task_settings": {},
            "checkin_settings": checkin_settings,
            "personalization_data": {},
        }

        assert provision_admin_account(account_data) is not None

        user_id = _resolve_user_id_with_retry(
            unique_username, test_data_dir=test_data_dir
        )
        assert user_id is not None

        saved_checkin_settings = (
            get_user_data(user_id, "preferences").get("preferences", {})[
                "checkin_settings"
            ]
        )
        if "time_periods" in saved_checkin_settings:
            assert "afternoon" in saved_checkin_settings["time_periods"]
        assert isinstance(saved_checkin_settings, dict)

    @pytest.mark.no_parallel  # shared user index JSON + test_data_dir under xdist
    def test_provision_admin_account_updates_user_index(self, test_data_dir):
        from core import clear_user_caches
        from storage.user_data_operations import build_user_index

        unique_username = f"test-index-user-{uuid.uuid4().hex[:8]}"
        account_data = {
            "username": unique_username,
            "preferred_name": "Test Index User",
            "timezone": "America/New_York",
            "channel": {"type": "email", "contact": "test@example.com"},
            "contact_info": {"email": "test@example.com", "phone": "", "discord": ""},
            "categories": ["motivational"],
            "features_enabled": {"messages": True, "tasks": False, "checkins": False},
            "task_settings": {},
            "checkin_settings": {},
            "personalization_data": {},
        }

        user_id = provision_admin_account(account_data)
        assert user_id is not None

        resolved_user_id = _resolve_user_id_with_retry(
            unique_username, test_data_dir=test_data_dir
        )
        assert resolved_user_id is not None

        def _index_complete_for_user() -> bool:
            clear_user_caches()
            index = build_user_index()
            entry = index.get(resolved_user_id)
            return entry is not None and entry.get("active") is True

        assert wait_until(
            _index_complete_for_user,
            timeout_seconds=30.0,
            poll_seconds=0.1,
        )

    def test_provision_admin_account_sets_up_default_tags_when_tasks_enabled(
        self, test_data_dir
    ):
        from core.tags import get_user_tags

        unique_username = f"test-tags-user-{uuid.uuid4().hex[:8]}"
        account_data = {
            "username": unique_username,
            "preferred_name": "Test Tags User",
            "timezone": "America/New_York",
            "channel": {"type": "email", "contact": "test@example.com"},
            "contact_info": {"email": "test@example.com", "phone": "", "discord": ""},
            "categories": ["motivational"],
            "features_enabled": {"messages": True, "tasks": True, "checkins": False},
            "task_settings": {"time_periods": {}, "tags": []},
            "checkin_settings": {},
            "personalization_data": {},
        }

        assert provision_admin_account(account_data) is not None

        user_id = _resolve_user_id_with_retry(
            unique_username, test_data_dir=test_data_dir
        )
        assert user_id is not None

        tags = get_user_tags(user_id)
        assert len(tags) > 0
        assert any(
            "work" in tag.lower() or "personal" in tag.lower() for tag in tags
        )

    def test_provision_admin_account_saves_custom_tags_when_provided(
        self, test_data_dir
    ):
        from core import get_user_data

        custom_tags = ["urgent", "project-alpha", "review"]
        unique_username = f"test-custom-tags-user-{uuid.uuid4().hex[:8]}"
        account_data = {
            "username": unique_username,
            "preferred_name": "Test Custom Tags User",
            "timezone": "America/New_York",
            "channel": {"type": "email", "contact": "test@example.com"},
            "contact_info": {"email": "test@example.com", "phone": "", "discord": ""},
            "categories": ["motivational"],
            "features_enabled": {"messages": True, "tasks": True, "checkins": False},
            "task_settings": {"time_periods": {}, "tags": custom_tags},
            "checkin_settings": {},
            "personalization_data": {},
        }

        assert provision_admin_account(account_data) is not None

        user_id = _resolve_user_id_with_retry(
            unique_username, test_data_dir=test_data_dir
        )
        assert user_id is not None

        tags = (
            get_user_data(user_id, "preferences")
            .get("preferences", {})
            .get("task_settings", {})
            .get("tags", [])
        )
        assert len(tags) >= len(custom_tags)
        for tag in custom_tags:
            assert any(tag.lower() in t.lower() for t in tags)

    def test_provision_admin_account_persists_feature_flags(self, test_data_dir):
        from core import get_user_data

        unique_username = f"test-features-user-{uuid.uuid4().hex[:8]}"
        account_data = {
            "username": unique_username,
            "preferred_name": "Test Features User",
            "timezone": "America/New_York",
            "channel": {"type": "email", "contact": "test@example.com"},
            "contact_info": {"email": "test@example.com", "phone": "", "discord": ""},
            "categories": ["motivational", "health"],
            "features_enabled": {"messages": True, "tasks": True, "checkins": True},
            "task_settings": {"time_periods": {}},
            "checkin_settings": {"time_periods": {}},
            "personalization_data": {},
        }

        assert provision_admin_account(account_data) is not None

        user_id = _resolve_user_id_with_retry(
            unique_username, test_data_dir=test_data_dir
        )
        assert user_id is not None

        features = get_user_data(user_id, "account").get("account", {})["features"]
        assert features["automated_messages"] == "enabled"
        assert features["task_management"] == "enabled"
        assert features["checkins"] == "enabled"
