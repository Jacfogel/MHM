"""Unit tests for AI minute estimates used by the home focus suggestion."""

from unittest.mock import patch

import pytest

from tasks import task_effort
from tasks.task_effort import estimate_task_efforts, parse_task_effort_lines


@pytest.mark.unit
@pytest.mark.tasks
class TestTaskEffort:
    def test_parse_keeps_only_requested_ids_and_sane_minutes(self):
        text = "pharmacy 5\nhouse 120\nunknown 10\npharmacy 8\nbad 0\nwide 999"
        parsed = parse_task_effort_lines(text, {"pharmacy", "house", "bad", "wide"})
        assert parsed == [
            {"id": "pharmacy", "minutes": 5},
            {"id": "house", "minutes": 120},
        ]

    def test_estimate_uses_the_model_and_then_the_cache(self):
        task_effort._effort_cache.clear()
        tasks = [
            {"id": "pharmacy", "title": "Call pharmacy", "description": "Ask about the refill"},
        ]
        with patch("ai.chat.chatbot.get_ai_chatbot") as chatbot, patch(
            "ai.client.lm_studio_client.call_lm_studio_api",
            return_value="pharmacy 5",
        ) as call:
            chatbot.return_value.is_ai_available.return_value = True
            first = estimate_task_efforts(tasks)
            second = estimate_task_efforts(tasks)
        assert first == [{"id": "pharmacy", "minutes": 5}]
        assert second == [{"id": "pharmacy", "minutes": 5}]
        assert call.call_count == 1

    def test_estimate_skips_the_model_when_it_is_unavailable(self):
        task_effort._effort_cache.clear()
        with patch("ai.chat.chatbot.get_ai_chatbot") as chatbot, patch(
            "ai.client.lm_studio_client.call_lm_studio_api"
        ) as call:
            chatbot.return_value.is_ai_available.return_value = False
            assert estimate_task_efforts([{"id": "a", "title": "Brand new task"}]) == []
            call.assert_not_called()
