"""Unit tests for safe AI health context."""

from datetime import datetime
from unittest.mock import patch

import pytest

from core.health_context_builder import (
    build_recent_health_patterns,
    build_safe_health_guidance_summary,
    format_health_guidance_for_user_reply,
)
from integrations.google_health.data_handlers import ensure_health_directory, save_health_signals


@pytest.mark.unit
@pytest.mark.integrations
def test_format_health_guidance_for_user_reply_strips_prompt_framing():
    summary = (
        "Health personalization (wellness-oriented, not medical): "
        "Recent rest and recovery patterns suggest a gentler day. "
        "Never diagnose, cite wearables, or suggest medical treatment."
    )
    text = format_health_guidance_for_user_reply(summary)
    assert "Health personalization" not in text
    assert "Never diagnose" not in text
    assert "gentler day" in text.lower()


@pytest.mark.unit
@pytest.mark.integrations
@pytest.mark.user
def test_build_user_facing_signal_wellness_snippet_uses_coarse_fields(test_data_dir):
    from core import update_user_account
    from core.health_context_builder import build_user_facing_signal_wellness_snippet
    from integrations.google_health.data_handlers import ensure_health_directory, save_health_signals
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = "health-coarse-snippet-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    update_user_account(user_id, {"features": {"google_health": "enabled"}})
    ensure_health_directory(user_id)
    save_health_signals(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-07-12 20:58:03",
            "signals": [
                {
                    "date": "2026-07-12",
                    "sleep_recovery": "high",
                    "sleep_vs_baseline": "normal",
                    "sleep_quality": "high",
                    "activity_level": "unknown",
                    "active_intensity": "normal",
                    "resting_hr_signal": "normal",
                    "hrv_signal": "normal",
                    "confidence": "low",
                    "message_guidance": [],
                    "baseline_days_used": 28,
                    "computed_at": "2026-07-12 20:58:03",
                }
            ],
        },
    )

    fixed_now = datetime.strptime("2026-07-12 20:58:00", "%Y-%m-%d %H:%M:%S")
    with patch("core.health_signals.now_datetime_full", return_value=fixed_now):
        snippet = build_user_facing_signal_wellness_snippet(user_id)

    assert "solid night" in snippet.lower() or "sleep" in snippet.lower()
    assert "sleep quality" in snippet.lower()
    assert "usual amount" in snippet.lower() or "typical" in snippet.lower()


@pytest.mark.unit
@pytest.mark.user
def test_guidance_summary_omits_raw_metrics(test_data_dir):
    from core import update_user_account
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = "health-context-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    update_user_account(user_id, {"features": {"google_health": "enabled"}})
    ensure_health_directory(user_id)
    save_health_signals(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-27 12:00:00",
            "signals": [
                {
                    "date": "2026-06-27",
                    "sleep_recovery": "low",
                    "sleep_hours": 4.8,
                    "steps": 2437,
                    "sleep_vs_baseline": "below",
                    "activity_level": "low",
                    "resting_hr_signal": "elevated",
                    "hrv_signal": "low",
                    "confidence": "medium",
                    "message_guidance": ["use_gentle_tone", "keep_expectations_small"],
                    "baseline_days_used": 10,
                    "computed_at": "2026-06-27 12:00:00",
                }
            ],
        },
    )

    fixed_now = datetime.strptime("2026-06-27 08:00:00", "%Y-%m-%d %H:%M:%S")
    with patch("core.health_signals.now_datetime_full", return_value=fixed_now):
        summary = build_safe_health_guidance_summary(user_id)

    assert summary
    assert "4.8" not in summary
    assert "480" not in summary
    assert "2437" not in summary
    assert "~2,400" not in summary
    assert "fitbit" not in summary.lower()


@pytest.mark.unit
@pytest.mark.user
def test_recent_patterns_include_rounded_sleep_steps_and_active_minutes(test_data_dir):
    from core import update_user_account
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = "health-rounded-patterns-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    update_user_account(user_id, {"features": {"google_health": "enabled"}})
    ensure_health_directory(user_id)
    save_health_signals(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-27 12:00:00",
            "signals": [
                {
                    "date": "2026-06-27",
                    "sleep_recovery": "low",
                    "sleep_hours": 5.4,
                    "steps": 2437,
                    "sleep_vs_baseline": "below",
                    "sleep_quality": "low",
                    "activity_level": "low",
                    "active_minutes": 47,
                    "active_intensity": "normal",
                    "resting_hr_signal": "elevated",
                    "hrv_signal": "low",
                    "confidence": "medium",
                    "message_guidance": ["use_gentle_tone"],
                    "baseline_days_used": 10,
                    "computed_at": "2026-06-27 12:00:00",
                }
            ],
        },
    )

    fixed_now = datetime.strptime("2026-06-27 08:00:00", "%Y-%m-%d %H:%M:%S")
    with patch("core.health_signals.now_datetime_full", return_value=fixed_now):
        patterns = build_recent_health_patterns(user_id)

    assert "Recent wellness patterns" in patterns
    assert "~5.5 hours of sleep" in patterns
    assert "~2,400 steps" in patterns
    assert "~45 active minutes" in patterns
    assert "5.4" not in patterns
    assert "2437" not in patterns
    assert "47" not in patterns
    assert "bpm" not in patterns.lower()
    assert "rmssd" not in patterns.lower()


@pytest.mark.unit
@pytest.mark.user
def test_recent_patterns_include_multi_day_streaks(test_data_dir):
    from core import update_user_account
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = "health-streak-patterns-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    update_user_account(user_id, {"features": {"google_health": "enabled"}})
    ensure_health_directory(user_id)
    save_health_signals(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-27 12:00:00",
            "signals": [
                {
                    "date": "2026-06-25",
                    "sleep_recovery": "low",
                    "sleep_hours": 5.0,
                    "steps": 2000,
                    "sleep_vs_baseline": "below",
                    "activity_level": "low",
                    "active_intensity": "low",
                    "confidence": "medium",
                    "message_guidance": ["use_gentle_tone"],
                    "baseline_days_used": 10,
                    "computed_at": "2026-06-25 12:00:00",
                },
                {
                    "date": "2026-06-26",
                    "sleep_recovery": "low",
                    "sleep_hours": 4.5,
                    "steps": 1800,
                    "sleep_vs_baseline": "below",
                    "activity_level": "low",
                    "active_intensity": "normal",
                    "confidence": "medium",
                    "message_guidance": ["use_gentle_tone"],
                    "baseline_days_used": 10,
                    "computed_at": "2026-06-26 12:00:00",
                },
                {
                    "date": "2026-06-27",
                    "sleep_recovery": "low",
                    "sleep_hours": 5.2,
                    "steps": 2200,
                    "sleep_vs_baseline": "below",
                    "activity_level": "low",
                    "active_intensity": "low",
                    "confidence": "medium",
                    "message_guidance": ["use_gentle_tone"],
                    "baseline_days_used": 10,
                    "computed_at": "2026-06-27 12:00:00",
                },
            ],
        },
    )

    fixed_now = datetime.strptime("2026-06-27 08:00:00", "%Y-%m-%d %H:%M:%S")
    with patch("core.health_signals.now_datetime_full", return_value=fixed_now):
        patterns = build_recent_health_patterns(user_id)

    assert "shorter sleep for 3 days in a row" in patterns
    assert "lighter activity for 3 days in a row" in patterns


@pytest.mark.unit
@pytest.mark.user
def test_latest_usable_signal_falls_back_when_today_missing(test_data_dir):
    from core import update_user_account
    from core.health_signals import get_latest_usable_signal, get_today_signal
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = "health-latest-signal-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    update_user_account(user_id, {"features": {"google_health": "enabled"}})
    ensure_health_directory(user_id)
    save_health_signals(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-29 18:27:15",
            "signals": [
                {
                    "date": "2026-06-29",
                    "sleep_recovery": "high",
                    "sleep_hours": 9.93,
                    "sleep_vs_baseline": "normal",
                    "activity_level": "low",
                    "resting_hr_signal": "normal",
                    "hrv_signal": "low",
                    "confidence": "high",
                    "message_guidance": ["use_gentle_tone"],
                    "baseline_days_used": 16,
                    "computed_at": "2026-06-29 18:27:15",
                }
            ],
        },
    )

    fixed_now = datetime.strptime("2026-06-30 11:44:00", "%Y-%m-%d %H:%M:%S")
    with patch("core.health_signals.now_datetime_full", return_value=fixed_now):
        assert get_today_signal(user_id) is None
        latest = get_latest_usable_signal(user_id)
        assert latest is not None
        assert latest["date"] == "2026-06-29"
        assert latest["sleep_recovery"] == "high"


@pytest.mark.unit
@pytest.mark.user
def test_personalized_wellness_context_prefers_coarse_health(test_data_dir):
    from core import update_user_account
    from core.health_context_builder import build_personalized_wellness_context
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = "health-personalized-context-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    update_user_account(user_id, {"features": {"google_health": "enabled"}})
    ensure_health_directory(user_id)
    save_health_signals(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-29 18:27:15",
            "signals": [
                {
                    "date": "2026-06-29",
                    "sleep_recovery": "high",
                    "sleep_hours": 9.93,
                    "steps": 1820,
                    "sleep_vs_baseline": "normal",
                    "sleep_quality": "high",
                    "activity_level": "low",
                    "active_intensity": "high",
                    "resting_hr_signal": "normal",
                    "hrv_signal": "low",
                    "confidence": "high",
                    "message_guidance": ["allow_light_movement_prompt"],
                    "baseline_days_used": 16,
                    "computed_at": "2026-06-29 18:27:15",
                }
            ],
        },
    )

    fixed_now = datetime.strptime("2026-06-30 11:44:00", "%Y-%m-%d %H:%M:%S")
    with patch("core.health_signals.now_datetime_full", return_value=fixed_now):
        context = build_personalized_wellness_context(user_id)

    assert "~10 hours of sleep" in context
    assert "~1,800 steps" in context
    assert "sleep quality looked solid" in context
    assert "active effort was higher than usual" in context
    assert "sleep_recovery=high" not in context
    assert "9.93" not in context
    assert "1820" not in context
    assert "Recent wellness patterns" in context
    assert "wearable wellness" not in context.lower()
    assert "Primary source" not in context
    assert "Recent check-ins" not in context
    assert "%" not in context
    assert "90" not in context
