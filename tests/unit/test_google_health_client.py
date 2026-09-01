"""Unit tests for Google Health API client parsing."""

import json
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.error_handling import CommunicationError
from integrations.google_health.client import (
    _ROLLUP_DEFAULT_PAGE_SIZE,
    _ROLLUP_MAX_DAYS,
    _ROLLUP_MAX_WINDOW_PAGE_PRODUCT,
    _Fetcher,
    _build_civil_range,
    _build_filter,
    _clamp_rollup_page_size,
    _coerce_float,
    _coerce_int,
    _date_from_data_point,
    _date_from_interval,
    _fetch_points_for_type,
    _interval_duration_minutes,
    _list_data_points_chunked,
    _merge_active_minutes,
    _merge_sleep_into_summary,
    _merge_steps_into_summary,
    _parse_api_date,
    _parse_duration_minutes,
    _parse_iso_datetime,
    _resolve_data_type_spec,
    fetch_daily_summaries,
    list_daily_rollups,
    list_data_points,
)

FIXTURES = Path(__file__).resolve().parents[1] / "test_helpers" / "fixtures" / "google_health"

_fixtures_available = FIXTURES.is_dir() and (FIXTURES / "sleep_response.json").exists()

pytestmark = [pytest.mark.core, pytest.mark.integrations]


def _json_response(status_code: int, payload: dict | None = None, text: str = "") -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload or {}
    response.text = text
    return response


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
def test_rollup_default_page_size_respects_window_page_product():
    assert _ROLLUP_DEFAULT_PAGE_SIZE <= _ROLLUP_MAX_WINDOW_PAGE_PRODUCT
    assert 1 * _ROLLUP_DEFAULT_PAGE_SIZE <= _ROLLUP_MAX_WINDOW_PAGE_PRODUCT


@pytest.mark.unit
def test_clamp_rollup_page_size_enforces_google_product_limit():
    assert _clamp_rollup_page_size(1, 100) == 90
    assert _clamp_rollup_page_size(1, 90) == 90
    assert _clamp_rollup_page_size(2, 100) == 45
    assert _clamp_rollup_page_size(1, 14) == 14


@pytest.mark.unit
def test_fetch_points_falls_back_to_list_when_rollup_fails(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 3, tzinfo=timezone.utc)
    list_calls: list[str] = []

    def _fail_rollup(*_args, **_kwargs):
        raise CommunicationError("Google Health dailyRollUp error for steps")

    def _fake_chunked(token, data_type, **_kwargs):
        list_calls.append(data_type)
        return [
            {
                "steps": {
                    "interval": {
                        "civilStartTime": {
                            "date": {"year": 2026, "month": 8, "day": 2},
                            "time": {"hours": 0},
                        }
                    },
                    "count": "1200",
                }
            }
        ]

    fetcher = _Fetcher(
        "steps",
        "steps",
        "interval_start",
        _merge_steps_into_summary,
        source="daily_rollup",
    )
    with (
        patch(
            "integrations.google_health.client.list_daily_rollups",
            side_effect=_fail_rollup,
        ),
        patch(
            "integrations.google_health.client._list_data_points_chunked",
            side_effect=_fake_chunked,
        ),
    ):
        points = _fetch_points_for_type(
            "token", fetcher, start_time=start, end_time=end
        )

    assert list_calls == ["steps"]
    assert points[0]["steps"]["count"] == "1200"


@pytest.mark.unit
def test_list_data_points_skips_in_testing_mode(monkeypatch):
    monkeypatch.setenv("MHM_TESTING", "1")
    assert list_data_points("token", "sleep") == []


@pytest.mark.unit
@pytest.mark.integrations
def test_list_data_points_timeout_is_handled(monkeypatch):
    import requests

    monkeypatch.delenv("MHM_TESTING", raising=False)
    with patch(
        "integrations.google_health.client.requests.get",
        side_effect=requests.Timeout("timed out"),
    ):
        try:
            result = list_data_points("token", "sleep")
        except (CommunicationError, requests.Timeout, TimeoutError, OSError):
            return
        assert result == []


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
@pytest.mark.skipif(not _fixtures_available, reason="google_health fixtures are gitignored; not available on CI")
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
@pytest.mark.skipif(not _fixtures_available, reason="google_health fixtures are gitignored; not available on CI")
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


@pytest.mark.unit
def test_resolve_data_type_spec_legacy_and_unknown():
    endpoint, prefix, mode = _resolve_data_type_spec("dailyRestingHeartRate")
    assert endpoint == "daily-resting-heart-rate"
    assert prefix == "daily_resting_heart_rate"
    assert mode == "daily_date"

    endpoint, prefix, mode = _resolve_data_type_spec("custom-metric")
    assert endpoint == "custom-metric"
    assert prefix == "custom_metric"
    assert mode == "interval_start"


@pytest.mark.unit
def test_list_data_points_paginates_and_collects_points(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    pages = [
        _json_response(
            200,
            {"dataPoints": [{"name": "a"}], "nextPageToken": "page-2"},
        ),
        _json_response(200, {"data points": [{"name": "b"}]}),
    ]
    with patch(
        "integrations.google_health.client.requests.get", side_effect=pages
    ) as get_mock:
        points = list_data_points("token", "sleep")
    assert [point["name"] for point in points] == ["a", "b"]
    assert get_mock.call_args_list[1].kwargs["params"]["pageToken"] == "page-2"


@pytest.mark.unit
def test_list_data_points_http_error_raises(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    with patch(
        "integrations.google_health.client.requests.get",
        return_value=_json_response(500, text="server exploded"),
    ):
        with pytest.raises(CommunicationError, match="Google Health API error"):
            list_data_points("token", "sleep")


@pytest.mark.unit
def test_list_daily_rollups_skips_in_testing_mode(monkeypatch):
    monkeypatch.setenv("MHM_TESTING", "1")
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 3, tzinfo=timezone.utc)
    assert list_daily_rollups("token", "steps", start_time=start, end_time=end) == []


@pytest.mark.unit
def test_list_daily_rollups_paginates_and_chunks_wide_windows(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    pages = [
        _json_response(
            200,
            {"rollupDataPoints": [{"name": "day-1"}], "nextPageToken": "p2"},
        ),
        _json_response(200, {"rollupDataPoints": [{"name": "day-2"}]}),
        _json_response(200, {"rollupDataPoints": [{"name": "day-3"}]}),
    ]
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 20, tzinfo=timezone.utc)
    with patch(
        "integrations.google_health.client.requests.post", side_effect=pages
    ) as post_mock:
        points = list_daily_rollups("token", "steps", start_time=start, end_time=end)
    assert [point["name"] for point in points] == ["day-1", "day-2", "day-3"]
    assert post_mock.call_count == 3
    assert post_mock.call_args_list[1].kwargs["json"]["pageToken"] == "p2"


@pytest.mark.unit
def test_list_daily_rollups_http_error_raises(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 2, tzinfo=timezone.utc)
    with patch(
        "integrations.google_health.client.requests.post",
        return_value=_json_response(400, text="bad rollup"),
    ):
        with pytest.raises(CommunicationError, match="dailyRollUp"):
            list_daily_rollups("token", "steps", start_time=start, end_time=end)


@pytest.mark.unit
def test_list_data_points_chunked_skips_failed_windows(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 12, tzinfo=timezone.utc)
    calls: list[tuple[datetime, datetime]] = []

    def _fake_list(token, data_type, *, start_time, end_time, **_kwargs):
        calls.append((start_time, end_time))
        if len(calls) == 2:
            raise CommunicationError("Google Health API error for steps")
        return [{"name": f"chunk-{len(calls)}"}]

    with patch(
        "integrations.google_health.client.list_data_points", side_effect=_fake_list
    ):
        points = _list_data_points_chunked(
            "token", "steps", start_time=start, end_time=end, chunk_days=5
        )
    assert len(calls) == 3
    assert [point["name"] for point in points] == ["chunk-1", "chunk-3"]


@pytest.mark.unit
def test_fetch_points_uses_chunked_list_for_interval_types():
    fetcher = _Fetcher(
        "steps", "steps", "interval_start", _merge_steps_into_summary
    )
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 2, tzinfo=timezone.utc)
    with patch(
        "integrations.google_health.client._list_data_points_chunked",
        return_value=[{"name": "interval"}],
    ) as chunked:
        points = _fetch_points_for_type(
            "token", fetcher, start_time=start, end_time=end
        )
    chunked.assert_called_once()
    assert points[0]["name"] == "interval"


@pytest.mark.unit
def test_parse_api_date_handles_string_and_invalid_dict():
    assert _parse_api_date(None) is None
    assert _parse_api_date("2026-06-27T12:00:00Z") == "2026-06-27"
    assert _parse_api_date({"year": "x", "month": 1, "day": 1}) is None
    assert _parse_api_date({"year": 2026, "month": 6, "day": 27}) == "2026-06-27"
    assert _parse_api_date(2026) is None
    assert _parse_api_date({"year": 2026}) is None


@pytest.mark.unit
def test_parse_duration_minutes_supports_common_api_shapes():
    assert _parse_duration_minutes(None) is None
    assert _parse_duration_minutes(90) == 90
    assert _parse_duration_minutes("3600s") == 60
    assert _parse_duration_minutes("8:00:30") == 481
    assert _parse_duration_minutes("8:15") == 495
    assert _parse_duration_minutes("8:xx") is None
    assert _parse_duration_minutes({"seconds": 3600}) == 60
    assert _parse_duration_minutes("not-a-duration") is None
    assert _parse_duration_minutes(["3600"]) is None


@pytest.mark.unit
def test_parse_iso_datetime_and_interval_duration():
    assert _parse_iso_datetime("") is None
    assert _parse_iso_datetime("not-a-date") is None
    parsed = _parse_iso_datetime("2026-06-27T01:00:00Z")
    assert parsed is not None
    assert parsed.hour == 1
    minutes = _interval_duration_minutes(
        {
            "startTime": "2026-06-27T00:00:00Z",
            "endTime": "2026-06-27T01:30:00Z",
        }
    )
    assert minutes == 90
    assert _interval_duration_minutes({"startTime": "2026-06-27T02:00:00Z"}) is None


@pytest.mark.unit
def test_date_from_interval_and_point_fallbacks():
    assert _date_from_interval({}) is None
    assert _date_from_interval({"other": True}) is None
    assert _date_from_interval({"civilStartTime": "2026-06-27T07:00:00Z"}) == "2026-06-27"
    assert _date_from_interval({"startTime": "2026-06-27T07:00:00Z"}) == "2026-06-27"
    assert _date_from_data_point({"civilDate": "2026-06-27"}) == "2026-06-27"
    assert _date_from_data_point(
        {"interval": {"startTime": "2026-06-28T00:00:00Z"}}
    ) == "2026-06-28"


@pytest.mark.unit
def test_coerce_int_and_float_reject_invalid_values():
    assert _coerce_int(None) is None
    assert _coerce_int("12.9") == 12
    assert _coerce_int("nope") is None
    assert _coerce_float(None) is None
    assert _coerce_float("41.5") == 41.5
    assert _coerce_float("nope") is None


@pytest.mark.unit
def test_merge_sleep_uses_interval_and_stage_list():
    summary: dict = {}
    point = {
        "name": "sleep/1",
        "sleep": {
            "interval": {
                "startTime": "2026-06-27T00:00:00Z",
                "endTime": "2026-06-27T08:00:00Z",
            },
            "efficiency": "91.5",
            "stages": [
                {
                    "type": "light",
                    "startTime": "2026-06-27T00:00:00Z",
                    "endTime": "2026-06-27T03:00:00Z",
                },
                {
                    "type": "deep",
                    "startTime": "2026-06-27T03:00:00Z",
                    "endTime": "2026-06-27T05:00:00Z",
                },
                {
                    "type": "rem",
                    "startTime": "2026-06-27T05:00:00Z",
                    "endTime": "2026-06-27T07:00:00Z",
                },
                {
                    "type": "awake",
                    "startTime": "2026-06-27T07:00:00Z",
                    "endTime": "2026-06-27T07:10:00Z",
                },
            ],
        },
    }
    _merge_sleep_into_summary(summary, point)
    assert summary["sleep_duration_minutes"] == 480
    assert summary["sleep_efficiency_pct"] == 91.5
    assert summary["sleep_stages"]["light_minutes"] == 180
    assert summary["sleep_stages"]["deep_minutes"] == 120
    assert "sleep" in summary["completeness"]


@pytest.mark.unit
def test_merge_steps_replaces_on_count_sum_and_adds_counts():
    summary: dict = {"steps": 10}
    _merge_steps_into_summary(summary, {"steps": {"count": 5}})
    assert summary["steps"] == 15
    _merge_steps_into_summary(summary, {"steps": {"countSum": 200}})
    assert summary["steps"] == 200


@pytest.mark.unit
def test_merge_active_minutes_uses_zone_totals_or_count():
    zone_summary: dict = {}
    _merge_active_minutes(
        zone_summary,
        {
            "activeZoneMinutes": {
                "sumInCardioHeartZone": 2,
                "sumInPeakHeartZone": 1,
                "sumInFatBurnHeartZone": 4,
            }
        },
    )
    assert zone_summary["active_minutes"] == 7

    count_summary: dict = {"active_minutes": 3}
    _merge_active_minutes(count_summary, {"active_zone_minutes": {"minutes": 5}})
    assert count_summary["active_minutes"] == 8


@pytest.mark.unit
def test_fetch_daily_summaries_skips_in_testing_mode(monkeypatch):
    monkeypatch.setenv("MHM_TESTING", "1")
    assert fetch_daily_summaries("token") == []


@pytest.mark.unit
def test_fetch_daily_summaries_skips_api_errors_and_undated_points(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    calls = {"n": 0}

    def _fake_fetch(_token, fetcher, **_kwargs):
        calls["n"] += 1
        if fetcher.endpoint == "sleep":
            raise CommunicationError("Google Health API error for sleep")
        if fetcher.endpoint == "steps":
            return [{"steps": {"count": 12}}]
        return [
            {
                "date": "2026-06-27",
                "dailyRestingHeartRate": {"beatsPerMinute": 62},
                "name": "hr/1",
            }
        ]

    with patch(
        "integrations.google_health.client._fetch_points_for_type",
        side_effect=_fake_fetch,
    ):
        summaries = fetch_daily_summaries("token", lookback_days=2)

    assert calls["n"] == 5
    by_date = {item["date"]: item for item in summaries}
    assert by_date["2026-06-27"]["resting_hr_bpm"] == 62.0


@pytest.mark.unit
def test_fetch_daily_summaries_skips_invalid_summary_models(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)

    def _fake_fetch(_token, fetcher, **_kwargs):
        if fetcher.endpoint != "sleep":
            return []
        return [
            {
                "date": "2026-06-27",
                "sleep": {"duration": 480},
            }
        ]

    with patch(
        "integrations.google_health.client._fetch_points_for_type",
        side_effect=_fake_fetch,
    ), patch(
        "integrations.google_health.client.DailySummaryModel.model_validate",
        side_effect=ValueError("bad summary"),
    ):
        assert fetch_daily_summaries("token", lookback_days=1) == []
