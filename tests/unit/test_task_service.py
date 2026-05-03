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


@pytest.mark.unit
@pytest.mark.tasks
def test_task_service_get_task_candidates_matches_short_id():
    from tasks import task_service

    tasks = [{"id": "task-1", "short_id": "t123abc", "title": "Pay bills"}]

    assert task_service.get_task_candidates(tasks, "t123abc") == tasks


@pytest.mark.unit
@pytest.mark.tasks
def test_task_service_find_task_by_identifier_matches_common_variation():
    from tasks import task_service

    task = {"id": "task-1", "title": "Brush teeth"}

    assert task_service.find_task_by_identifier([task], "dental") == task


@pytest.mark.unit
@pytest.mark.tasks
def test_task_service_find_most_urgent_task_prefers_overdue():
    from tasks import task_service

    overdue = {"id": "old", "title": "Overdue", "due": {"date": "2000-01-01"}}
    high = {"id": "high", "title": "High", "priority": "high"}

    assert task_service.find_most_urgent_task([high, overdue]) == overdue
