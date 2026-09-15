"""Unit tests for shrinking a task to a smaller next step."""

import pytest

from tasks.task_data_handlers import runtime_task_due_date
from tasks.task_simplify import simplify_task
from tests.test_helpers.test_utilities import TestUserFactory


@pytest.mark.unit
@pytest.mark.tasks
class TestSimplifyTask:
    def test_simplify_rewrites_title_and_keeps_due_date(self, test_data_dir):
        user_id = "simplify_keeps_due"
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        from tasks import create_task, get_task_by_id

        task_id = create_task(
            user_id,
            title="Clean the whole house",
            due_date="2026-09-20",
            due_time="14:00",
        )
        result = simplify_task(user_id, task_id, "Wipe the kitchen counter")
        assert result.success is True
        assert result.needs_title is False
        task = get_task_by_id(user_id, task_id)
        assert task.get("title") == "Wipe the kitchen counter"
        assert runtime_task_due_date(task) == "2026-09-20"
        assert task.get("due", {}).get("time") == "14:00"
        assert "Was: Clean the whole house" in str(task.get("description") or "")

    def test_simplify_without_title_asks(self, test_data_dir):
        user_id = "simplify_asks"
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        from tasks import create_task, get_task_by_id

        task_id = create_task(user_id, title="Clean the whole house")
        result = simplify_task(user_id, task_id, None)
        assert result.needs_title is True
        task = get_task_by_id(user_id, task_id)
        assert task.get("title") == "Clean the whole house"
