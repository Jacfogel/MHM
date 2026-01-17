import os
from datetime import datetime, timedelta

from communication.message_processing.conversation_flow_manager import (
    conversation_manager,
    FLOW_CHECKIN,
    CHECKIN_INACTIVITY_MINUTES,
)
from tests.test_utilities import (
    setup_test_data_environment,
    cleanup_test_data_environment,
    create_test_user,
)
from core.service_utilities import READABLE_TIMESTAMP_FORMAT


import pytest


@pytest.mark.behavior
@pytest.mark.checkins
class TestCheckinExpirySemantics:
    def setup_method(self):
        self.test_dir, self.test_data_dir, _ = setup_test_data_environment()

    def teardown_method(self):
        cleanup_test_data_environment(self.test_dir)

    def test_idle_timeout_expires_checkin(self, monkeypatch):
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        user_id = "user_idle_expire"
        assert create_test_user(
            user_id,
            user_type="basic",
            test_data_dir=self.test_data_dir,
            enable_checkins=True,
        )

        # Seed a minimal active check-in state directly to avoid feature flag differences
        conversation_manager.user_states[user_id] = {
            "flow": FLOW_CHECKIN,
            "state": 101,
            "data": {},
            "question_order": ["mood", "energy"],
            "current_question_index": 0,
        }
        state = conversation_manager.user_states[user_id]

        # Backdate last_activity beyond the configured inactivity window to trigger expiry
        idle_minutes = CHECKIN_INACTIVITY_MINUTES + 1
        past = (datetime.now() - timedelta(minutes=idle_minutes)).strftime(
            READABLE_TIMESTAMP_FORMAT
        )
        state["last_activity"] = past

        # Any inbound message should now cause expiry
        reply, completed = conversation_manager.handle_inbound_message(user_id, "hello")
        assert completed
        assert "expired due to inactivity" in reply.lower()

    def test_slash_command_expires_and_hands_off(self, monkeypatch):
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        user_id = "user_slash_expire"
        assert create_test_user(
            user_id,
            user_type="basic",
            test_data_dir=self.test_data_dir,
            enable_checkins=True,
        )

        # Seed an active check-in state
        conversation_manager.user_states[user_id] = {
            "flow": FLOW_CHECKIN,
            "state": 101,
            "data": {},
            "question_order": ["mood", "energy"],
            "current_question_index": 0,
        }

        # Send unrelated slash command
        reply, completed = conversation_manager.handle_inbound_message(
            user_id, "/tasks"
        )
        # Should delegate to tasks and complete the handoff response (single turn)
        assert completed
        # Flow should be cleared
        assert user_id not in conversation_manager.user_states
        assert "task" in reply.lower()

    def test_bang_command_expires_and_hands_off(self, monkeypatch):
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        user_id = "user_bang_expire"
        assert create_test_user(
            user_id,
            user_type="basic",
            test_data_dir=self.test_data_dir,
            enable_checkins=True,
        )

        # Seed an active check-in state
        conversation_manager.user_states[user_id] = {
            "flow": FLOW_CHECKIN,
            "state": 101,
            "data": {},
            "question_order": ["mood", "energy"],
            "current_question_index": 0,
        }

        # Send unrelated bang command
        reply, completed = conversation_manager.handle_inbound_message(
            user_id, "!tasks"
        )
        assert completed
        assert user_id not in conversation_manager.user_states
        assert "task" in reply.lower()
