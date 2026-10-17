"""Tests for coordinated task, motivational, and health message pressure."""

from unittest.mock import patch

import pytest

from core.message_pressure import (
    resolve_message_pressure,
    scheduled_message_pressure_prefix,
)

pytestmark = [pytest.mark.unit, pytest.mark.communication]


def test_low_energy_softens_messages_without_health_data():
    """A reliable low-energy check-in is enough to lower message pressure."""
    with (
        patch("checkins.checkin_service.today_checkin_energy", return_value=1),
        patch("core.health_signals.get_message_guidance", return_value=[]),
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
    ):
        policy = resolve_message_pressure("u1")
        prefix = scheduled_message_pressure_prefix("u1")

    assert policy.gentle is False
    assert prefix == ""
