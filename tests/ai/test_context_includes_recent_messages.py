import os
import re

from ai.chatbot import get_ai_chatbot
from core.message_management import store_sent_message
from core.response_tracking import store_user_response
from tests.test_utilities import setup_test_data_environment, cleanup_test_data_environment, create_test_user


class TestAIContextRecentMessages:
    def setup_method(self):
        # Ensure tests run in isolated test data environment
        self.test_dir, self.test_data_dir, _ = setup_test_data_environment()

    def teardown_method(self):
        cleanup_test_data_environment(self.test_dir)

    def test_comprehensive_context_includes_recent_sent_messages_and_checkin_status(self, monkeypatch):
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        user_id = "user_recent_msgs"
        assert create_test_user(user_id, user_type="basic", test_data_dir=self.test_data_dir)

        # Store a recent sent message (simulating automated outbound)
        ok = store_sent_message(
            user_id=user_id,
            category="motivational",
            message_id="m1",
            message="Keep going, you are doing great today!",
            delivery_status="sent",
            time_period="morning",
        )
        assert ok

        # Also store a checkin outbound message; it should be excluded from the list
        ok2 = store_sent_message(
            user_id=user_id,
            category="checkin",
            message_id="c1",
            message="On a scale of 1-5, how is your mood?",
            delivery_status="sent",
            time_period="morning",
        )
        assert ok2

        # Build context prompt and ensure recent automated messages are included
        bot = get_ai_chatbot()
        messages = bot._create_comprehensive_context_prompt(user_id, "hello")
        assert isinstance(messages, list) and len(messages) >= 2
        system = messages[0]
        assert system["role"] == "system"
        content = system["content"]

        # The summary should include the category and FULL text for the most recent non-checkin message
        assert "Recent automated messages" in content
        assert "[motivational]" in content
        assert "Keep going, you are doing great today!" in content
        # Exclude checkin category lines from the automated messages section
        assert "[checkin]" not in content

        # Check-in awareness line should be present (default: not completed since no responses stored yet)
        assert "Check-in today: not completed" in content

        # Store a check-in response for today with mood/energy and re-build context
        store_user_response(user_id, {"mood": 4, "energy": 3}, response_type="checkin")
        messages2 = bot._create_comprehensive_context_prompt(user_id, "hello")
        system2 = messages2[0]
        content2 = system2["content"]
        assert "Check-in today: completed at" in content2
        assert "mood 4/5" in content2
        assert "energy 3/5" in content2

        # Add a task reminder and ensure the separate line appears
        ok3 = store_sent_message(
            user_id=user_id,
            category="task_reminders",
            message_id="t1",
            message="Don't forget to review your tasks for today.",
            delivery_status="sent",
            time_period="afternoon",
        )
        assert ok3
        messages3 = bot._create_comprehensive_context_prompt(user_id, "hello")
        content3 = messages3[0]["content"]
        assert "Recent task reminder:" in content3
        assert "Don't forget to review your tasks for today." in content3


