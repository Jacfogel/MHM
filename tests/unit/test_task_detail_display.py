"""Unit tests for task detail formatting."""

import pytest

from tasks import task_service


@pytest.mark.unit
@pytest.mark.tasks
def test_format_task_detail_display_includes_due_time_and_reminders():
    task = {
        "title": "Buy groceries",
        "description": "Get milk and eggs",
        "priority": "high",
        "due": {"date": "2026-06-24", "time": "14:00"},
        "short_id": "tabcd12",
        "reminders": [
            {
                "kind": "scheduled",
                "period": {
                    "date": "2026-06-24",
                    "start_time": "13:00",
                    "end_time": "13:30",
                },
            }
        ],
    }
    text = task_service.format_task_detail_display(task)
    assert "Buy groceries" in text
    assert "14:00" in text
    assert "13:00-13:30" in text
    assert "tabcd12" in text


@pytest.mark.unit
@pytest.mark.tasks
def test_format_task_detail_display_includes_group():
    task = {
        "title": "Call dentist",
        "group": "medical",
        "short_id": "tgrp001",
    }
    text = task_service.format_task_detail_display(task)
    assert "**Group:** medical" in text
