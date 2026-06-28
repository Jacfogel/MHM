"""Unit tests for safe AI health context."""

from datetime import datetime
from unittest.mock import patch

import pytest

from core.health_context_builder import build_safe_health_guidance_summary
from integrations.google_health.data_handlers import ensure_health_directory, save_health_signals


@pytest.mark.unit
@pytest.mark.user
def test_context_omits_raw_metrics(test_data_dir):
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
    assert "fitbit" not in summary.lower()
