"""Unit tests for derived health signal builder."""

import pytest

from integrations.google_health.signal_builder import (
    build_signal_for_date,
    rebuild_signals_for_summaries,
)

pytestmark = [pytest.mark.core]


def _baseline_summaries(*, with_quality: bool = False, with_active: bool = False):
    summaries = []
    for day in range(1, 15):
        row = {
            "date": f"2026-06-{day:02d}",
            "sleep_duration_minutes": 420,
            "steps": 8000,
        }
        if with_quality:
            row["sleep_efficiency_pct"] = 85.0
            row["sleep_stages"] = {
                "deep_minutes": 70,
                "rem_minutes": 70,
                "light_minutes": 250,
                "awake_minutes": 30,
            }
        if with_active:
            row["active_minutes"] = 40
        summaries.append(row)
    return summaries


@pytest.mark.unit
def test_build_signal_low_sleep_and_activity():
    summaries = _baseline_summaries()
    summaries.append({"date": "2026-06-27", "sleep_duration_minutes": 240, "steps": 500})
    signal = build_signal_for_date("2026-06-27", summaries)
    assert signal is not None
    assert signal["sleep_recovery"] == "low"
    assert signal["activity_level"] == "low"
    assert signal["sleep_quality"] == "unknown"
    assert signal["active_intensity"] == "unknown"
    assert "use_gentle_tone" in signal["message_guidance"]


@pytest.mark.unit
def test_build_signal_missing_data_returns_low_confidence_guidance_empty():
    summaries = [{"date": "2026-06-27", "completeness": []}]
    signal = build_signal_for_date("2026-06-27", summaries)
    assert signal is not None
    assert signal["confidence"] == "low"
    assert signal["message_guidance"] == []
    assert signal["sleep_quality"] == "unknown"
    assert signal["active_intensity"] == "unknown"


@pytest.mark.unit
def test_build_signal_sleep_quality_from_efficiency_and_stages():
    summaries = _baseline_summaries(with_quality=True)
    summaries.append(
        {
            "date": "2026-06-27",
            "sleep_duration_minutes": 420,
            "steps": 8000,
            "sleep_efficiency_pct": 60.0,
            "sleep_stages": {
                "deep_minutes": 20,
                "rem_minutes": 20,
                "light_minutes": 350,
                "awake_minutes": 30,
            },
        }
    )
    signal = build_signal_for_date("2026-06-27", summaries)
    assert signal is not None
    assert signal["sleep_quality"] == "low"
    assert "use_gentle_tone" in signal["message_guidance"]


@pytest.mark.unit
def test_build_signal_sleep_quality_unknown_without_stages_or_efficiency():
    summaries = _baseline_summaries()
    summaries.append(
        {"date": "2026-06-27", "sleep_duration_minutes": 480, "steps": 7000}
    )
    signal = build_signal_for_date("2026-06-27", summaries)
    assert signal is not None
    assert signal["sleep_quality"] == "unknown"


@pytest.mark.unit
def test_build_signal_active_intensity_from_active_minutes():
    summaries = _baseline_summaries(with_active=True)
    summaries.append(
        {
            "date": "2026-06-27",
            "sleep_duration_minutes": 420,
            "steps": 4000,
            "active_minutes": 90,
        }
    )
    signal = build_signal_for_date("2026-06-27", summaries)
    assert signal is not None
    assert signal["active_intensity"] == "high"
    assert "send_reinforcement" in signal["message_guidance"]


@pytest.mark.unit
def test_build_signal_active_intensity_absolute_fallback_without_baseline():
    summaries = [
        {
            "date": "2026-06-27",
            "sleep_duration_minutes": 420,
            "steps": 5000,
            "active_minutes": 10,
        }
    ]
    signal = build_signal_for_date("2026-06-27", summaries)
    assert signal is not None
    assert signal["active_intensity"] == "low"


@pytest.mark.unit
def test_rebuild_signals_for_dates():
    summaries = [
        {"date": "2026-06-26", "sleep_duration_minutes": 420, "steps": 6000},
        {"date": "2026-06-27", "sleep_duration_minutes": 480, "steps": 7000},
    ]
    signals = rebuild_signals_for_summaries(summaries)
    assert len(signals) == 2
