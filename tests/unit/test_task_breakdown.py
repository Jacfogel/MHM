"""Unit tests for suggested task steps saved as subtasks."""

import pytest

from tasks.task_breakdown import (
    add_task_subtasks,
    parse_task_step_lines,
    suggest_breakdown,
)
from tests.test_helpers.test_utilities import TestUserFactory


@pytest.mark.unit
@pytest.mark.tasks
class TestTaskBreakdown:
    def test_parse_keeps_short_unique_titles(self):
        text = (
            "1. Find the phone number\n"
            "- Ask for the next opening\n"
            "* Ask for the next opening\n"
            "Steps:\n"
            "This line is far too long to be a task title because it keeps going past the limit of one hundred and twenty characters easily.\n"
        )
        assert parse_task_step_lines(text) == [
            "Find the phone number",
            "Ask for the next opening",
        ]

    def test_suggest_returns_model_steps(self, test_data_dir, monkeypatch):
        user_id = "breakdown_suggest"
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        from tasks import create_task

        task_id = create_task(user_id, title="Call the dentist", due_date="2026-09-20")

        class Available:
            def is_ai_available(self):
                return True

        monkeypatch.setattr(
            "ai.chat.chatbot.get_ai_chatbot", lambda: Available()
        )
        monkeypatch.setattr(
            "ai.client.lm_studio_client.call_lm_studio_api",
            lambda **_kwargs: "Find the phone number\nCall the dentist\nAsk for the next opening",
        )
        result = suggest_breakdown(user_id, task_id)
        assert result.success is True
        assert result.steps == ["Find the phone number", "Ask for the next opening"]

    def test_suggest_reports_when_the_model_is_unavailable(self, test_data_dir, monkeypatch):
        user_id = "breakdown_unavailable"
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        from tasks import create_task

        task_id = create_task(user_id, title="Call the dentist")

        class Unavailable:
            def is_ai_available(self):
                return False

        monkeypatch.setattr(
            "ai.chat.chatbot.get_ai_chatbot", lambda: Unavailable()
        )
        result = suggest_breakdown(user_id, task_id)
        assert result.success is False
        assert result.unavailable is True
        assert result.steps == []

    def test_subtasks_keep_the_original_task(self, test_data_dir):
        user_id = "breakdown_subtasks"
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        from tasks import create_task, get_task_by_id, load_active_tasks

        task_id = create_task(
            user_id,
            title="Call the dentist",
            due_date="2026-09-20",
            due_time="14:00",
            priority="high",
            tags=["health"],
        )
        result = add_task_subtasks(
            user_id,
            task_id,
            ["Find the phone number", "Ask for the next opening"],
        )
        assert result.success is True
        parent = get_task_by_id(user_id, task_id)
        assert parent.get("title") == "Call the dentist"
        assert parent.get("due", {}).get("date") == "2026-09-20"
        children = [
            task
            for task in load_active_tasks(user_id)
            if task.get("parent_id") == parent.get("id")
        ]
        assert [task.get("title") for task in children] == [
            "Find the phone number",
            "Ask for the next opening",
        ]
        assert children[0].get("due", {}).get("date") == "2026-09-20"
        assert children[0].get("due", {}).get("time") == "14:00"
        assert children[0].get("priority") == "high"
        assert children[0].get("tags") == ["health"]
        assert not children[0].get("reminders")
        nested = add_task_subtasks(user_id, children[0].get("id"), ["Look up the number"])
        assert nested.success is False
        again = add_task_subtasks(user_id, task_id, ["Find the phone number"])
        assert again.success is False
