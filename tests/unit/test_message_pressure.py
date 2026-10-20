"""Tests for coordinated task, motivational, and health message pressure."""

from datetime import datetime

from unittest.mock import patch

import pytest

from core.message_pressure import (
    MessagePressureSettings,
    energy_is_low,
    message_pressure_settings_from_preferences,
    quiet_mode_is_active,
    resolve_message_pressure,
    scheduled_message_pressure_prefix,
    task_reminder_allowed_during_quiet_mode,
)

pytestmark = [pytest.mark.unit, pytest.mark.communication]


def test_low_energy_softens_messages_without_health_data():
    """A reliable low-energy check-in is enough to lower message pressure."""
    with (
        patch("checkins.checkin_service.today_checkin_energy", return_value=1),
        patch("core.health_signals.get_message_guidance", return_value=[]),
        patch(
            "core.message_pressure.load_message_pressure_settings",
            return_value=MessagePressureSettings(),
        ),
    ):
        policy = resolve_message_pressure("u1")
        prefix = scheduled_message_pressure_prefix("u1")

    assert policy.gentle is True
    assert "gentler" in prefix
    assert "productivity pressure" in prefix


def test_avoid_nagging_applies_to_the_shared_policy():
    """Reliable avoid-nagging guidance lowers pressure for every message category."""
    with (
        patch("checkins.checkin_service.today_checkin_energy", return_value=4),
        patch(
            "core.health_signals.get_message_guidance",
            return_value=["avoid_nagging_movement_prompts"],
        ),
        patch(
            "core.message_pressure.load_message_pressure_settings",
            return_value=MessagePressureSettings(),
        ),
    ):
        policy = resolve_message_pressure("u1")
        prefix = scheduled_message_pressure_prefix("u1")

    assert policy.gentle is True
    assert policy.avoid_nagging is True
    assert "avoid repeated prompting" in prefix


def test_missing_signals_preserve_current_message_behavior():
    """No reliable energy or health guidance adds no prompt assumptions."""
    with (
        patch("checkins.checkin_service.today_checkin_energy", return_value=None),
        patch("core.health_signals.get_message_guidance", return_value=[]),
        patch(
            "core.message_pressure.load_message_pressure_settings",
            return_value=MessagePressureSettings(),
        ),
    ):
        policy = resolve_message_pressure("u1")
        prefix = scheduled_message_pressure_prefix("u1")

    assert policy.gentle is False
    assert prefix == ""


def test_saved_energy_rule_is_explicit_and_can_be_disabled():
    strict = MessagePressureSettings(
        automatic_energy_rules=True,
        low_energy_threshold=1,
    )
    disabled = MessagePressureSettings(
        automatic_energy_rules=False,
        low_energy_threshold=4,
    )

    assert energy_is_low(1, strict) is True
    assert energy_is_low(2, strict) is False
    assert energy_is_low(1, disabled) is False


def test_quiet_mode_has_a_clear_expiry_and_gentle_policy():
    settings = MessagePressureSettings(quiet_mode_until="2026-10-19 15:00:00")

    assert quiet_mode_is_active(settings, now_dt=datetime(2026, 10, 19, 14, 59))
    assert not quiet_mode_is_active(settings, now_dt=datetime(2026, 10, 19, 15, 0))

    with (
        patch("checkins.checkin_service.today_checkin_energy", return_value=4),
        patch("core.health_signals.get_message_guidance", return_value=[]),
        patch(
            "core.message_pressure.load_message_pressure_settings",
            return_value=settings,
        ),
        patch(
            "scheduler.user_timezone.user_local_now_naive",
            return_value=datetime(2026, 10, 19, 14, 0),
        ),
    ):
        policy = resolve_message_pressure("u1")

    assert policy.quiet_mode is True
    assert policy.gentle is True
    assert policy.avoid_nagging is True


def test_quiet_mode_allows_only_due_or_explicitly_urgent_task_reminders():
    now = datetime(2026, 10, 19, 10, 0)

    assert task_reminder_allowed_during_quiet_mode({"priority": "critical"}, now_dt=now)
    assert task_reminder_allowed_during_quiet_mode(
        {"priority": "medium", "due": {"date": "2026-10-19"}}, now_dt=now
    )
    assert not task_reminder_allowed_during_quiet_mode(
        {"priority": "high", "due": {"date": "2026-10-20"}}, now_dt=now
    )


def test_invalid_saved_controls_fall_back_to_safe_defaults():
    settings = message_pressure_settings_from_preferences(
        {
            "message_pressure_settings": {
                "automatic_energy_rules": "yes",
                "low_energy_threshold": 5,
                "quiet_mode_until": "tomorrow",
            }
        }
    )

    assert settings == MessagePressureSettings()


def test_pressure_setting_helpers_use_safe_defaults_on_unexpected_objects():
    class BrokenPreferences(dict):
        def get(self, key, default=None):
            raise RuntimeError("broken preferences")

    class BrokenSettings:
        @property
        def automatic_energy_rules(self):
            raise RuntimeError("broken settings")

    assert message_pressure_settings_from_preferences(BrokenPreferences(x=1)) == (
        MessagePressureSettings()
    )
    assert energy_is_low(1, BrokenSettings()) is False  # type: ignore[arg-type]
