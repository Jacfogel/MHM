"""Unit tests for the shared task-focus policy."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest

from tasks.task_focus import (
    _days_until_due,
    _focus_reason,
    _leaf_candidates,
    _time_band,
    _urgency,
    choose_task_focus,
    task_focus_signals,
)
from core.message_pressure import MessagePressureSettings


@pytest.mark.unit
@pytest.mark.tasks
class TestTaskFocusPolicy:
    def test_private_helpers_return_safe_defaults_on_unexpected_input(self):
        now = datetime(2026, 10, 17, 10, 0)

        assert _time_band("bad") == ""  # type: ignore[arg-type]
        assert (
            _days_until_due(
                {"due": {"date": "2026-10-17"}},
                None,  # type: ignore[arg-type]
            )
            is None
        )
        assert _urgency("medium", "bad") == 0  # type: ignore[arg-type]
        assert _focus_reason(None) == (  # type: ignore[arg-type]
            "This is the next task selected by your current priorities."
        )
        assert _leaf_candidates(None, now) == []  # type: ignore[arg-type]

    def test_low_energy_prefers_short_task_with_same_urgency(self):
        tasks = [
            {
                "id": "long",
                "title": "Write the full quarterly planning document",
                "priority": "high",
            },
            {"id": "short", "title": "Email Pat", "priority": "high"},
        ]

        decision = choose_task_focus(
            tasks,
            now_dt=datetime(2026, 10, 17, 10, 0),
            energy=1,
            random_value=lambda: 0.0,
        )

        assert decision is not None
        assert decision.task["id"] == "short"
        assert decision.gentle is True
        assert "small step" in decision.reason

    def test_urgent_task_is_not_hidden_by_easier_nonurgent_task(self):
        tasks = [
            {
                "id": "urgent",
                "title": "Prepare the overdue tax return package",
                "priority": "medium",
                "due": {"date": "2026-10-16"},
            },
            {"id": "easy", "title": "Email Pat", "priority": "low"},
        ]

        decision = choose_task_focus(
            tasks,
            now_dt=datetime(2026, 10, 17, 10, 0),
            energy=1,
            random_value=lambda: 0.0,
        )

        assert decision is not None
        assert decision.task["id"] == "urgent"
        assert "urgent" in decision.reason

    def test_open_subtask_is_selected_instead_of_parent(self):
        tasks = [
            {"id": "parent", "title": "Clean kitchen", "priority": "medium"},
            {
                "id": "step",
                "parent_id": "parent",
                "title": "Wipe counter",
                "priority": "medium",
            },
        ]

        decision = choose_task_focus(
            tasks,
            now_dt=datetime(2026, 10, 17, 10, 0),
            random_value=lambda: 0.0,
        )

        assert decision is not None
        assert decision.task["id"] == "step"

    def test_currently_snoozed_task_is_not_selected(self):
        tasks = [
            {
                "id": "snoozed",
                "title": "Not yet",
                "priority": "critical",
                "reminder_snooze_until": "2026-10-17 12:00:00",
            },
            {"id": "available", "title": "Available", "priority": "low"},
        ]

        decision = choose_task_focus(
            tasks,
            now_dt=datetime(2026, 10, 17, 10, 0),
            random_value=lambda: 0.0,
        )

        assert decision is not None
        assert decision.task["id"] == "available"

    def test_reliable_health_guidance_enables_gentle_tone(self):
        with (
            patch("checkins.checkin_service.today_checkin_energy", return_value=None),
            patch(
                "core.health_signals.get_message_guidance",
                return_value=["use_gentle_tone"],
            ),
            patch(
                "core.message_pressure.load_message_pressure_settings",
                return_value=MessagePressureSettings(),
            ),
        ):
            assert task_focus_signals("user-1") == (None, True)

    def test_explicit_energy_rule_can_leave_energy_two_unmodified(self):
        tasks = [
            {"id": "long", "title": "Prepare the long planning document"},
            {"id": "short", "title": "Email Pat"},
        ]

        decision = choose_task_focus(
            tasks,
            now_dt=datetime(2026, 10, 17, 10, 0),
            energy=2,
            low_energy=False,
            random_value=lambda: 0.0,
        )

        assert decision is not None
        assert decision.gentle is False
        assert "energy is low" not in decision.reason.lower()
