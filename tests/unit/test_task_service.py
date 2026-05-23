"""Delegation tests for tasks.task_service facade."""

from unittest.mock import patch
from datetime import datetime

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


@pytest.mark.unit
@pytest.mark.tasks
def test_task_service_parse_time_string_normalizes_common_inputs():
    from tasks import task_service

    assert task_service.parse_time_string("noon") == "12:00"
    assert task_service.parse_time_string("12am") == "00:00"
    assert task_service.parse_time_string("2:30pm") == "14:30"


@pytest.mark.unit
@pytest.mark.tasks
def test_task_service_parse_relative_date_uses_canonical_clock():
    from tasks import task_service

    fixed_now = datetime(2026, 5, 11, 9, 0)
    with patch("tasks.task_service.now_datetime_full", return_value=fixed_now):
        assert task_service.parse_relative_date("today") == "2026-05-11"
        assert task_service.parse_relative_date("tomorrow") == "2026-05-12"
        assert task_service.parse_relative_date("next week") == "2026-05-18"
        assert task_service.parse_relative_date("tonight") == "2026-05-11"
        assert task_service.parse_relative_date("this week") == "2026-05-17"
        assert task_service.parse_relative_date("before Friday") == "2026-05-15"
        assert task_service.parse_relative_date("by Monday") == "2026-05-18"
        assert task_service.parse_relative_date("after school") == "2026-05-11"

    saturday = datetime(2026, 5, 16, 10, 0)
    with patch("tasks.task_service.now_datetime_full", return_value=saturday):
        assert task_service.parse_relative_date("this week") == "2026-05-24"

    sunday = datetime(2026, 5, 17, 10, 0)
    with patch("tasks.task_service.now_datetime_full", return_value=sunday):
        assert task_service.parse_relative_date("this week") == "2026-05-24"


@pytest.mark.unit
@pytest.mark.tasks
def test_task_service_prepare_create_task_data_applies_defaults_and_due_time():
    from tasks import task_service

    prefs = {
        "preferences": {
            "task_settings": {
                "recurring_settings": {
                    "default_recurrence_pattern": "weekly",
                    "default_recurrence_interval": 2,
                    "default_repeat_after_completion": False,
                }
            }
        }
    }
    entities = {"title": "Review", "due_date": "tomorrow at 2pm"}

    with patch("tasks.task_service.get_user_data", return_value=prefs), patch(
        "tasks.task_service.now_datetime_full",
        return_value=datetime(2026, 5, 11, 9, 0),
    ):
        prepared = task_service.prepare_create_task_data("u1", entities)

    assert prepared.task_data == {
        "title": "Review",
        "description": "",
        "due_date": "2026-05-12",
        "due_time": "14:00",
        "priority": "medium",
        "tags": [],
        "group": "",
        "recurrence_pattern": "weekly",
        "recurrence_interval": 2,
        "repeat_after_completion": False,
    }
    assert prepared.priority_was_provided is False


@pytest.mark.unit
@pytest.mark.tasks
def test_task_service_filter_and_sort_tasks():
    from tasks import task_service

    tasks = [
        {"id": "1", "title": "Low", "priority": "low", "due": {"date": "2026-05-13"}, "tags": ["home"]},
        {"id": "2", "title": "High", "priority": "high", "due": {"date": "2026-05-12"}, "tags": ["work"]},
        {"id": "3", "title": "Medium", "priority": "medium", "due": {"date": "2026-05-11"}, "tags": ["work"]},
    ]

    filtered = task_service.filter_tasks("u1", tasks, None, "medium", None)
    assert [task["id"] for task in filtered] == ["3"]
    assert [task["id"] for task in task_service.sort_tasks_by_priority_and_due_date(tasks)] == ["2", "3", "1"]


@pytest.mark.unit
@pytest.mark.tasks
def test_task_service_completed_task_candidates_support_partial_title():
    from tasks import task_service

    tasks = [{"id": "task-1", "short_id": "t1", "title": "Brush teeth"}]

    assert task_service.get_completed_task_candidates(tasks, "brush") == tasks
