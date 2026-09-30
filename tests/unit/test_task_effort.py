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
            assert estimate_task_efforts([{"id": "a", "title": "Brand new task"}]) == [
                {"id": "a", "minutes": 15}
            ]
            call.assert_not_called()

    def test_local_guess_is_replaced_when_the_model_returns(self):
        task_effort._effort_cache.clear()
        tasks = [{"id": "a", "title": "Brand new task"}]
        with patch("ai.chat.chatbot.get_ai_chatbot") as chatbot, patch(
            "ai.client.lm_studio_client.call_lm_studio_api"
        ) as call:
            chatbot.return_value.is_ai_available.return_value = False
            skipped = estimate_task_efforts(tasks)
            chatbot.return_value.is_ai_available.return_value = True
            call.return_value = "a 25"
            measured = estimate_task_efforts(tasks)
        assert skipped == [{"id": "a", "minutes": 15}]
        assert measured == [{"id": "a", "minutes": 25}]
        assert call.call_count == 1

    def test_failed_model_call_does_not_cache_the_local_guess(self):
        task_effort._effort_cache.clear()
        tasks = [{"id": "pharmacy", "title": "Call pharmacy", "description": ""}]
        with patch("ai.chat.chatbot.get_ai_chatbot") as chatbot, patch(
            "ai.client.lm_studio_client.call_lm_studio_api",
            side_effect=[None, "pharmacy 7"],
        ) as call:
            chatbot.return_value.is_ai_available.return_value = True
            first = estimate_task_efforts(tasks)
            second = estimate_task_efforts(tasks)
        assert first == [{"id": "pharmacy", "minutes": 10}]
        assert second == [{"id": "pharmacy", "minutes": 7}]
        assert call.call_count == 2

    def test_tasks_past_the_model_batch_are_asked_on_the_next_load(self):
        task_effort._effort_cache.clear()
        tasks = [
            {"id": f"t{index}", "title": f"Task number {index} extra words here"}
            for index in range(21)
        ]
        seen = []

        def fake_call(messages, **_kwargs):
            seen.append(messages[1]["content"])
            return "t0 12"

        with patch("ai.chat.chatbot.get_ai_chatbot") as chatbot, patch(
            "ai.client.lm_studio_client.call_lm_studio_api",
            side_effect=fake_call,
        ):
            chatbot.return_value.is_ai_available.return_value = True
            estimate_task_efforts(tasks)
            estimate_task_efforts(tasks)
        assert "t20" not in seen[0]
        assert "t20" in seen[1]
        assert "t0" not in seen[1]
