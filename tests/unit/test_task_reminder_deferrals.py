"""Tests for bounded reminder-deferral history and adaptive guidance."""

from datetime import datetime, timedelta

import pytest

from tasks.task_reminder_deferrals import (
    MAX_REMINDER_DEFERRALS,
    append_reminder_deferral,
    repeated_deferral_advice,
)

pytestmark = [pytest.mark.unit, pytest.mark.tasks]


def test_deferral_history_keeps_only_the_newest_five_records():
    """The task record never accumulates an unbounded reminder history."""
    task = {"reminder_deferrals": []}
    start = datetime(2026, 10, 10, 9, 0, 0)
    for index in range(7):
        task["reminder_deferrals"] = append_reminder_deferral(
            task,
            "snooze",
            occurred_at=start + timedelta(days=index),
        )

    history = task["reminder_deferrals"]
    assert len(history) == MAX_REMINDER_DEFERRALS
    assert history[0]["at"] == "2026-10-12 09:00:00"
    assert history[-1]["at"] == "2026-10-16 09:00:00"


def test_repeated_deferral_prefers_an_existing_smaller_step():
    """An open subtask becomes the explanation after repeated deferrals."""
    task = {
        "reminder_deferrals": [
            {"action": "snooze", "at": "2026-10-15 09:00:00"},
            {"action": "skip", "at": "2026-10-16 09:00:00"},
        ]
    }

    advice = repeated_deferral_advice(task, focus_step={"title": "Find the form"})

    assert "next smaller step" in advice
    assert "Simplify" not in advice
