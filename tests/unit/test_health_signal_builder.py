"""Unit tests for derived health signal builder."""

import pytest

from integrations.google_health.signal_builder import build_signal_for_date, rebuild_signals_for_summaries

pytestmark = [pytest.mark.core]


@pytest.mark.unit
def test_build_signal_low_sleep_and_activity():
    summaries = [
        {"date": f"2026-06-{d:02d}", "sleep_duration_minutes": 420, "steps": 8000}
        for d in range(1, 15)
    ]
    summaries.append({"date": "2026-06-27", "sleep_duration_minutes": 240, "steps": 500})
    signal = build_signal_for_date("2026-06-27", summaries)
    assert signal is not None
    assert signal["sleep_recovery"] == "low"
    assert signal["activity_level"] == "low"
    assert "use_gentle_tone" in signal["message_guidance"]


@pytest.mark.unit
def test_build_signal_missing_data_returns_low_confidence_guidance_empty():
    summaries = [{"date": "2026-06-27", "completeness": []}]
    signal = build_signal_for_date("2026-06-27", summaries)
    assert signal is not None
    assert signal["confidence"] == "low"
    assert signal["message_guidance"] == []


@pytest.mark.unit
def test_rebuild_signals_for_dates():
    summaries = [
        {"date": "2026-06-26", "sleep_duration_minutes": 420, "steps": 6000},
        {"date": "2026-06-27", "sleep_duration_minutes": 480, "steps": 7000},
    ]
    signals = rebuild_signals_for_summaries(summaries)
    assert len(signals) == 2
