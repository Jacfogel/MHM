"""Unit tests for health personalization rules."""

import pytest

from integrations.google_health.personalization_rules import (
    apply_personalization_rules,
    build_scheduled_message_context_prefix,
)

pytestmark = [pytest.mark.core]


@pytest.mark.unit
def test_poor_sleep_low_activity_guidance():
    guidance = apply_personalization_rules(
        {
            "confidence": "medium",
            "sleep_recovery": "low",
            "activity_level": "low",
            "sleep_vs_baseline": "below",
            "resting_hr_signal": "unknown",
            "hrv_signal": "unknown",
        }
    )
    assert "use_gentle_tone" in guidance
    assert "avoid_high_pressure_productivity_prompt" in guidance


@pytest.mark.unit
def test_low_confidence_returns_empty():
    assert apply_personalization_rules({"confidence": "low"}) == []


@pytest.mark.unit
def test_scheduled_prefix_has_no_numbers():
    prefix = build_scheduled_message_context_prefix(["use_gentle_tone"])
    assert prefix
    assert "bpm" not in prefix.lower()
    assert "steps" not in prefix.lower()
