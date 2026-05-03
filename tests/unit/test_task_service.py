"""Delegation tests for tasks.task_service facade."""

from unittest.mock import patch

import pytest


@pytest.mark.unit
@pytest.mark.tasks
def test_task_service_create_task_delegates():
    with patch("tasks.create_task", return_value="task-id-1") as m:
        from tasks import task_service

        assert task_service.create_task("u1", title="Do thing") == "task-id-1"
    m.assert_called_once_with(user_id="u1", title="Do thing")


@pytest.mark.unit
@pytest.mark.tasks
def test_task_service_load_active_tasks_delegates():
    with patch("tasks.load_active_tasks", return_value=[{"id": "a"}]) as m:
        from tasks import task_service

        assert task_service.load_active_tasks("u1") == [{"id": "a"}]
    m.assert_called_once_with("u1")
