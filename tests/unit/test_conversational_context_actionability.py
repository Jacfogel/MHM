"""Actionability audit tests: feature flags and recent-message context boundaries."""

import os

import pytest

from ai.context.assembly import build_context_parts
from ai.chat.response_generator import get_response_generator
from core import get_user_data, get_user_id_by_identifier
from messages.message_data_manager import store_sent_message
from storage.user_data_write import update_user_account, update_user_preferences
from tests.test_helpers.test_utilities import (
    TestUserFactory,
    cleanup_test_data_environment,
    setup_test_data_environment,
)


@pytest.mark.unit
@pytest.mark.ai
class TestConversationalContextActionability:
    def setup_method(self):
        self.test_dir, self.test_data_dir, _ = setup_test_data_environment()

    def teardown_method(self):
        cleanup_test_data_environment(self.test_dir)

    def _bind_runtime_to_test_data_dir(self, monkeypatch) -> None:
        """Point config + UserDataManager at this test's isolated data dir.

        Autouse ``mock_config`` patches BASE_DATA_DIR to the session store; these
        tests create users under a per-test temp dir, so both must agree.
        """
        import core.config
        import storage.user_data_operations as udm

        monkeypatch.setenv("TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TESTING", "1")
        monkeypatch.setattr(core.config, "BASE_DATA_DIR", self.test_data_dir)
        monkeypatch.setattr(
            core.config,
            "USER_INFO_DIR_PATH",
            os.path.join(self.test_data_dir, "users"),
        )
        udm.user_data_manager = udm.UserDataManager()

    def _resolve_user_id(self, user_id: str) -> str:
        return get_user_id_by_identifier(user_id) or user_id

    def _set_automated_messages_feature(self, user_id: str, enabled: bool) -> None:
        """Set automated_messages feature; clear categories when disabling.

        Account saves re-enable automated_messages whenever preferences still
        list categories (cross-file invariant), so disable must clear categories.
        """
        actual_id = self._resolve_user_id(user_id)
        if not enabled:
            assert update_user_preferences(actual_id, {"categories": []})
        account_result = get_user_data(actual_id, "account")
        account = account_result.get("account") or {}
        features = dict(account.get("features") or {})
        features["automated_messages"] = "enabled" if enabled else "disabled"
        assert update_user_account(actual_id, {"features": features})

    def test_feature_enablement_lists_disabled_features(self, monkeypatch):
        self._bind_runtime_to_test_data_dir(monkeypatch)

        user_id = "user_actionability_flags"
        assert TestUserFactory.create_basic_user(
            user_id,
            enable_checkins=False,
            enable_tasks=False,
            test_data_dir=self.test_data_dir,
        )
        self._set_automated_messages_feature(user_id, enabled=True)
        actual_id = self._resolve_user_id(user_id)

        parts = build_context_parts(actual_id)
        joined = "\n".join(parts)
        assert "Feature availability" in joined
        assert "check-ins are disabled" in joined
        assert "task management is disabled" in joined
        assert "automated messages are enabled" in joined

    def test_recent_messages_omitted_when_automated_messages_disabled(self, monkeypatch):
        self._bind_runtime_to_test_data_dir(monkeypatch)

        user_id = "user_no_auto_msgs"
        assert TestUserFactory.create_basic_user(
            user_id, enable_checkins=True, enable_tasks=True, test_data_dir=self.test_data_dir
        )
        self._set_automated_messages_feature(user_id, enabled=False)
        actual_id = self._resolve_user_id(user_id)

        assert store_sent_message(
            user_id=actual_id,
            category="motivational",
            message_id="m1",
            message="You are doing great!",
            delivery_status="sent",
            time_period="morning",
        )

        messages = get_response_generator().create_comprehensive_context_prompt(
            actual_id, "hello"
        )
        content = messages[0]["content"]
        assert "automated messages are disabled" in content
        assert "Recent automated messages sent to them:" not in content
        assert "You are doing great!" not in content

    def test_recent_messages_included_when_automated_messages_enabled(self, monkeypatch):
        self._bind_runtime_to_test_data_dir(monkeypatch)

        user_id = "user_with_auto_msgs"
        assert TestUserFactory.create_basic_user(
            user_id, enable_checkins=True, enable_tasks=True, test_data_dir=self.test_data_dir
        )
        self._set_automated_messages_feature(user_id, enabled=True)
        actual_id = self._resolve_user_id(user_id)

        assert store_sent_message(
            user_id=actual_id,
            category="motivational",
            message_id="m2",
            message="Keep going today!",
            delivery_status="sent",
            time_period="morning",
        )

        messages = get_response_generator().create_comprehensive_context_prompt(
            actual_id, "hello"
        )
        content = messages[0]["content"]
        assert "automated messages are enabled" in content
        assert "Recent automated messages sent to them:" in content
        assert "Keep going today!" in content
