"""Unit tests for suggested task steps saved as subtasks."""

import pytest

from tasks.task_breakdown import (
    add_task_subtasks,
    next_open_step,
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

    def test_completing_or_deleting_the_parent_includes_its_steps(self, test_data_dir):
        user_id = "breakdown_parent_lifecycle"
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        from tasks import (
            complete_task,
            create_task,
            delete_task,
            get_task_by_id,
            load_active_tasks,
            load_completed_tasks,
        )

        parent_id = create_task(user_id, title="Call the dentist", due_date="2026-09-20")
        add_task_subtasks(user_id, parent_id, ["Find the phone number", "Ask for the next opening"])
        create_task(user_id, title="Buy milk")
        children = [
            task for task in load_active_tasks(user_id) if task.get("parent_id") == parent_id
        ]
        assert complete_task(user_id, children[0].get("id")) is True
        assert get_task_by_id(user_id, parent_id).get("status") == "active"
        assert complete_task(user_id, parent_id) is True
        completed_titles = {task.get("title") for task in load_completed_tasks(user_id)}
        assert completed_titles == {
            "Call the dentist",
            "Find the phone number",
            "Ask for the next opening",
        }
        assert [task.get("title") for task in load_active_tasks(user_id)] == ["Buy milk"]

        parent_id = create_task(user_id, title="Clean the kitchen")
        add_task_subtasks(user_id, parent_id, ["Wipe the counter"])
        done_id = create_task(user_id, title="Take out the trash")
        assert complete_task(user_id, done_id) is True
        assert delete_task(user_id, parent_id) is True
        remaining_titles = {task.get("title") for task in load_active_tasks(user_id)}
        remaining_titles.update(task.get("title") for task in load_completed_tasks(user_id))
        assert "Clean the kitchen" not in remaining_titles
        assert "Wipe the counter" not in remaining_titles
        assert "Buy milk" in remaining_titles

    def test_restore_can_bring_steps_back(self, test_data_dir):
        user_id = "breakdown_restore_steps"
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        from communication.command_handlers.task_handler import (
            PENDING_RESTORE,
            handle_pending_restore,
        )
        from core.time_utilities import now_timestamp_full
        from tasks import (
            complete_task,
            create_task,
            load_active_tasks,
            load_completed_tasks,
            restore_task,
        )
        from tasks.task_breakdown import detach_task_step

        parent_id = create_task(user_id, title="Call the dentist")
        add_task_subtasks(user_id, parent_id, ["Find the phone number"])
        assert complete_task(user_id, parent_id) is True
        assert restore_task(user_id, parent_id) is True
        active_titles = {task.get("title") for task in load_active_tasks(user_id)}
        completed_titles = {task.get("title") for task in load_completed_tasks(user_id)}
        assert active_titles == {"Call the dentist"}
        assert completed_titles == {"Find the phone number"}

        parent_id = create_task(user_id, title="Clean the kitchen")
        add_task_subtasks(user_id, parent_id, ["Wipe the counter"])
        assert complete_task(user_id, parent_id) is True
        assert restore_task(user_id, parent_id, restore_steps=True) is True
        brought_back = {task.get("title") for task in load_active_tasks(user_id)}
        assert {"Clean the kitchen", "Wipe the counter"}.issubset(brought_back)
        assert "Wipe the counter" not in {
            task.get("title") for task in load_completed_tasks(user_id)
        }

        step = next(
            task for task in load_active_tasks(user_id) if task.get("title") == "Wipe the counter"
        )
        detached = detach_task_step(user_id, step.get("id"))
        assert detached is not None and detached.success is True
        assert next(
            task for task in load_active_tasks(user_id) if task.get("id") == step.get("id")
        ).get("parent_id") in (None, "")
        own_steps = add_task_subtasks(user_id, step.get("id"), ["Find the spray"])
        assert own_steps.success is True

        again = create_task(user_id, title="Mail the form")
        add_task_subtasks(user_id, again, ["Find a stamp"])
        assert complete_task(user_id, again) is True
        PENDING_RESTORE[user_id] = {"task_id": again, "asked_at": now_timestamp_full()}
        reply = handle_pending_restore(user_id, "With the steps")
        assert reply is not None
        assert "smaller steps" in reply.message
        restored = {task.get("title") for task in load_active_tasks(user_id)}
        assert "Mail the form" in restored
        assert "Find a stamp" in restored
        PENDING_RESTORE.pop(user_id, None)

    def test_weekly_task_keeps_its_steps_on_the_next_occurrence(self, test_data_dir):
        user_id = "breakdown_weekly_steps"
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        from tasks import complete_task, create_task, load_active_tasks

        parent_id = create_task(
            user_id,
            title="Clean the kitchen",
            due_date="2026-09-20",
            recurrence_pattern="weekly",
        )
        add_task_subtasks(
            user_id,
            parent_id,
            ["Wipe the counter", "Sweep the floor"],
        )
        assert complete_task(user_id, parent_id) is True
        active = load_active_tasks(user_id)
        parents = [task for task in active if not task.get("parent_id")]
        assert [task.get("title") for task in parents] == ["Clean the kitchen"]
        next_id = parents[0].get("id")
        assert next_id != parent_id
        steps = [task for task in active if task.get("parent_id") == next_id]
        assert {task.get("title") for task in steps} == {
            "Wipe the counter",
            "Sweep the floor",
        }
        assert steps[0].get("due", {}).get("date") == parents[0].get("due", {}).get("date")

    def test_reminder_names_the_open_step(self, test_data_dir):
        user_id = "breakdown_reminder_step"
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        from tasks import create_task, get_task_by_id
        from communication.reminders.reminder_dispatcher import TaskReminderDispatcher

        parent_id = create_task(
            user_id,
            title="Call the dentist",
            description="Bring the insurance card",
            due_date="2026-09-20",
            priority="high",
        )
        add_task_subtasks(user_id, parent_id, ["Find the phone number"])
        parent = get_task_by_id(user_id, parent_id)
        message = TaskReminderDispatcher(None).create_task_reminder_message(
            parent,
            focus_step=next_open_step(user_id, parent),
        )
        assert "Find the phone number" in message
        assert "Part of Call the dentist" in message
        assert "Bring the insurance card" not in message
