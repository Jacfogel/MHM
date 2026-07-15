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
            "sleep_quality": "unknown",
            "active_intensity": "unknown",
            "resting_hr_signal": "unknown",
            "hrv_signal": "unknown",
        }
    )
    assert "use_gentle_tone" in guidance
    assert "avoid_high_pressure_productivity_prompt" in guidance


@pytest.mark.unit
def test_low_sleep_quality_triggers_gentle_even_when_duration_ok():
    guidance = apply_personalization_rules(
        {
            "confidence": "medium",
            "sleep_recovery": "high",
            "sleep_vs_baseline": "normal",
            "sleep_quality": "low",
            "activity_level": "normal",
            "active_intensity": "normal",
            "resting_hr_signal": "unknown",
            "hrv_signal": "unknown",
        }
    )
    assert "use_gentle_tone" in guidance
    assert "keep_expectations_small" in guidance


@pytest.mark.unit
def test_high_active_intensity_reinforces_even_when_steps_low():
    guidance = apply_personalization_rules(
        {
            "confidence": "high",
            "sleep_recovery": "normal",
            "sleep_vs_baseline": "normal",
            "sleep_quality": "normal",
            "activity_level": "low",
            "active_intensity": "high",
            "resting_hr_signal": "unknown",
            "hrv_signal": "unknown",
        }
    )
    assert "send_reinforcement" in guidance
    assert "avoid_nagging_movement_prompts" in guidance


@pytest.mark.unit
def test_low_active_intensity_with_good_sleep_suggests_light_movement():
    guidance = apply_personalization_rules(
        {
            "confidence": "medium",
            "sleep_recovery": "high",
            "sleep_vs_baseline": "normal",
            "sleep_quality": "normal",
            "activity_level": "unknown",
            "active_intensity": "low",
            "resting_hr_signal": "unknown",
            "hrv_signal": "unknown",
        }
    )
    assert "allow_light_movement_prompt" in guidance
    assert "suggest_short_walk_or_stretch" in guidance


@pytest.mark.unit
def test_low_confidence_returns_empty():
    assert apply_personalization_rules({"confidence": "low"}) == []


@pytest.mark.unit
def test_scheduled_prefix_has_no_numbers():
    prefix = build_scheduled_message_context_prefix(["use_gentle_tone"])
    assert prefix
    assert "bpm" not in prefix.lower()
    assert "steps" not in prefix.lower()
