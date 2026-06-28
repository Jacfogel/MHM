"""Unit tests for Google Health API client parsing."""

import json
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from integrations.google_health.client import (
    _ROLLUP_MAX_DAYS,
    _build_civil_range,
    _build_filter,
    _date_from_data_point,
    fetch_daily_summaries,
    list_data_points,
)

FIXTURES = Path(__file__).resolve().parents[1] / "test_helpers" / "fixtures" / "google_health"

pytestmark = [pytest.mark.core]


@pytest.mark.unit
def test_build_civil_range_uses_end_of_day_on_last_date():
    civil = _build_civil_range(date(2026, 6, 13), date(2026, 6, 27))
    assert civil["start"]["date"] == {"year": 2026, "month": 6, "day": 13}
    assert civil["end"]["time"]["hours"] == 23
    assert civil["end"]["date"]["day"] == 27


@pytest.mark.unit
def test_rollup_max_days_within_google_limit():
    assert _ROLLUP_MAX_DAYS <= 14


@pytest.mark.unit
def test_list_data_points_skips_in_testing_mode(monkeypatch):
    monkeypatch.setenv("MHM_TESTING", "1")
    assert list_data_points("token", "sleep") == []


@pytest.mark.unit
def test_build_filter_sleep_uses_session_end_time():
    start = datetime(2026, 6, 24, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 27, 12, 0, tzinfo=timezone.utc)
    filt = _build_filter("sleep", "session_end", start_time=start, end_time=end)
    assert 'sleep.interval.end_time >= "2026-06-24T00:00:00Z"' in filt
    assert 'sleep.interval.end_time < "2026-06-27T12:00:00Z"' in filt


@pytest.mark.unit
def test_build_filter_steps_uses_interval_start_time():
    start = datetime(2026, 6, 24, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 27, 0, 0, tzinfo=timezone.utc)
    filt = _build_filter("steps", "interval_start", start_time=start, end_time=end)
    assert "steps.interval.start_time" in filt


@pytest.mark.unit
def test_build_filter_daily_uses_date_field():
    start = datetime(2026, 6, 24, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 27, 0, 0, tzinfo=timezone.utc)
    filt = _build_filter(
        "daily_resting_heart_rate", "daily_date", start_time=start, end_time=end
    )
    assert 'daily_resting_heart_rate.date >= "2026-06-24"' in filt
    assert 'daily_resting_heart_rate.date < "2026-06-28"' in filt


@pytest.mark.unit
def test_list_data_points_uses_kebab_case_endpoint(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    captured: dict = {}

    def _fake_get(url, headers=None, params=None, timeout=None):
        captured["url"] = url
        captured["params"] = params
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"dataPoints": []}
        return response

    with patch("integrations.google_health.client.requests.get", side_effect=_fake_get):
        list_data_points(
            "token",
            "daily-resting-heart-rate",
            start_time=datetime(2026, 6, 24, tzinfo=timezone.utc),
            end_time=datetime(2026, 6, 27, tzinfo=timezone.utc),
        )

    assert "daily-resting-heart-rate" in captured["url"]
    assert "daily_resting_heart_rate.date" in captured["params"]["filter"]


@pytest.mark.unit
def test_date_from_data_point_parses_structured_daily_date():
    point = {
        "dailyRestingHeartRate": {
            "date": {"year": 2026, "month": 6, "day": 27},
            "value": 62,
        }
    }
    assert _date_from_data_point(point) == "2026-06-27"


@pytest.mark.unit
def test_date_from_data_point_parses_steps_civil_start_time():
    point = {
        "steps": {
            "interval": {
                "civilStartTime": {
                    "date": {"year": 2026, "month": 6, "day": 27},
                    "time": {"hours": 7, "minutes": 5},
                }
            },
            "count": "40",
        }
    }
    assert _date_from_data_point(point) == "2026-06-27"


@pytest.mark.unit
def test_fetch_daily_summaries_merges_steps_hr_hrv_and_active_minutes(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    fixtures = {
        "sleep": json.loads((FIXTURES / "sleep_response.json").read_text(encoding="utf-8")),
        "steps_rollup": json.loads(
            (FIXTURES / "steps_rollup_response.json").read_text(encoding="utf-8")
        ),
        "active_zone_rollup": json.loads(
            (FIXTURES / "active_zone_rollup_response.json").read_text(encoding="utf-8")
        ),
        "daily-resting-heart-rate": json.loads(
            (FIXTURES / "daily_hr_response.json").read_text(encoding="utf-8")
        ),
        "daily-heart-rate-variability": json.loads(
            (FIXTURES / "daily_hrv_response.json").read_text(encoding="utf-8")
        ),
    }

    def _fake_list(token, data_type, **kwargs):
        payload = fixtures.get(data_type) or {}
        return payload.get("dataPoints", [])

    def _fake_rollup(token, data_type, **kwargs):
        if data_type == "steps":
            return fixtures["steps_rollup"]["rollupDataPoints"]
        if data_type == "active-zone-minutes":
            return fixtures["active_zone_rollup"]["rollupDataPoints"]
        return []

    with patch("integrations.google_health.client.list_data_points", side_effect=_fake_list), patch(
        "integrations.google_health.client.list_daily_rollups", side_effect=_fake_rollup
    ):
        summaries = fetch_daily_summaries("token", lookback_days=3)

    by_date = {item["date"]: item for item in summaries}
    assert by_date["2026-06-27"]["steps"] == 200
    assert by_date["2026-06-27"]["resting_hr_bpm"] == 62.0
    assert by_date["2026-06-27"]["hrv_rmssd_ms"] == 41.5
    assert by_date["2026-06-27"]["active_minutes"] == 3
    assert set(by_date["2026-06-27"]["completeness"]) == {
        "sleep",
        "activity",
        "heart_rate",
        "hrv",
    }


@pytest.mark.unit
def test_fetch_daily_summaries_parses_sleep(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    sleep_payload = json.loads((FIXTURES / "sleep_response.json").read_text(encoding="utf-8"))

    def _fake_list(token, data_type, **kwargs):
        if data_type == "sleep":
            return sleep_payload["dataPoints"]
        return []

    with patch("integrations.google_health.client.list_data_points", side_effect=_fake_list):
        summaries = fetch_daily_summaries("token", lookback_days=3)

    assert summaries
    assert summaries[0]["date"] == "2026-06-27"
    assert summaries[0]["sleep_duration_minutes"] == 480
