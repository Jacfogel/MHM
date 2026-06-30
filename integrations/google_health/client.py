"""
Read-only Google Health API client.

Fetches sleep, activity, and health metrics via health.googleapis.com/v4.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

import requests

from core.config import GOOGLE_HEALTH_API_BASE_URL
from core.error_handling import CommunicationError, handle_errors
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full
from integrations.google_health.schemas import DailySummaryModel, SleepStagesSummaryModel

logger = get_component_logger("google_health")

FilterMode = Literal["interval_start", "session_end", "daily_date"]
FetchSource = Literal["list", "daily_rollup"]

# Wide intraday list queries can trigger Google 500s; chunk when falling back to list.
_LIST_CHUNK_DAYS = 5
# Google dailyRollUp civil span limit (active-zone-minutes and related types).
_ROLLUP_MAX_DAYS = 14

# Endpoint paths use kebab-case; filter fields use snake_case (Google Health API).
DATA_TYPE_SPECS: dict[str, tuple[str, FilterMode]] = {
    "sleep": ("sleep", "session_end"),
    "steps": ("steps", "interval_start"),
    "active-zone-minutes": ("active_zone_minutes", "interval_start"),
    "daily-resting-heart-rate": ("daily_resting_heart_rate", "daily_date"),
    "daily-heart-rate-variability": ("daily_heart_rate_variability", "daily_date"),
}

DATA_TYPES = tuple(DATA_TYPE_SPECS.keys())


@dataclass(frozen=True)
class _Fetcher:
    endpoint: str
    filter_prefix: str
    filter_mode: FilterMode
    merge: Callable[[dict[str, Any], dict[str, Any]], None]
    source: FetchSource = "list"


@handle_errors("checking Google Health testing mode", default_return=False)
def _testing_mode() -> bool:
    """Return True when MHM_TESTING skips live Google Health API calls."""
    return os.getenv("MHM_TESTING") == "1"


@handle_errors("building Google Health list filter", default_return="")
def _build_filter(
    filter_prefix: str,
    filter_mode: FilterMode,
    *,
    start_time: datetime,
    end_time: datetime,
) -> str:
    """Build an AIP-160 filter for list dataPoints (type-specific fields)."""
    if filter_mode == "daily_date":
        start_date = start_time.astimezone(timezone.utc).date().isoformat()
        end_exclusive = (end_time.astimezone(timezone.utc).date() + timedelta(days=1)).isoformat()
        return (
            f'{filter_prefix}.date >= "{start_date}" '
            f'AND {filter_prefix}.date < "{end_exclusive}"'
        )

    start_iso = start_time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_iso = end_time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if filter_mode == "session_end":
        field = f"{filter_prefix}.interval.end_time"
    else:
        field = f"{filter_prefix}.interval.start_time"
    return f'{field} >= "{start_iso}" AND {field} < "{end_iso}"'


@handle_errors("resolving Google Health data type spec", default_return=("", "", "interval_start"))
def _resolve_data_type_spec(data_type: str) -> tuple[str, str, FilterMode]:
    """Resolve endpoint slug and filter prefix for a data type key."""
    legacy_map = {
        "dailyRestingHeartRate": "daily-resting-heart-rate",
        "dailyHeartRateVariability": "daily-heart-rate-variability",
        "activeZoneMinutes": "active-zone-minutes",
    }
    endpoint = legacy_map.get(data_type, data_type)
    if endpoint in DATA_TYPE_SPECS:
        filter_prefix, filter_mode = DATA_TYPE_SPECS[endpoint]
        return endpoint, filter_prefix, filter_mode
    filter_prefix = endpoint.replace("-", "_")
    return endpoint, filter_prefix, "interval_start"


@handle_errors("listing Google Health data points", default_return=[], re_raise=True)
def list_data_points(
    access_token: str,
    data_type: str,
    *,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    page_size: int = 25,
) -> list[dict[str, Any]]:
    """List data points for a data type (users/me)."""
    if _testing_mode():
        return []

    endpoint, filter_prefix, filter_mode = _resolve_data_type_spec(data_type)
    parent = f"users/me/dataTypes/{endpoint}"
    url = f"{GOOGLE_HEALTH_API_BASE_URL}/{parent}/dataPoints"
    params: dict[str, Any] = {"pageSize": page_size}
    if start_time and end_time:
        params["filter"] = _build_filter(
            filter_prefix,
            filter_mode,
            start_time=start_time,
            end_time=end_time,
        )

    headers = {"Authorization": f"Bearer {access_token}"}
    collected: list[dict[str, Any]] = []
    page_token: str | None = None

    while True:
        if page_token:
            params["pageToken"] = page_token
        elif "pageToken" in params:
            del params["pageToken"]

        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code != 200:
            body_preview = (response.text or "")[:300]
            logger.warning(
                f"Google Health list failed for {endpoint} status={response.status_code} "
                f"filter={params.get('filter', '')!r} body={body_preview!r}"
            )
            raise CommunicationError(f"Google Health API error for {endpoint}")

        payload = response.json()
        batch = payload.get("dataPoints") or payload.get("data points") or []
        collected.extend(batch)
        page_token = payload.get("nextPageToken") or None
        if not page_token:
            break

    logger.info(f"Google Health listed {len(collected)} data point(s) for {endpoint}")
    return collected


@handle_errors("building civil datetime payload", default_return={})
def _civil_datetime(day: date) -> dict[str, Any]:
    """Build Google Health civil date-time starting at midnight UTC."""
    return {
        "date": {"year": day.year, "month": day.month, "day": day.day},
        "time": {"hours": 0, "minutes": 0, "seconds": 0, "nanos": 0},
    }


@handle_errors("building civil end-of-day payload", default_return={})
def _civil_end_of_day(day: date) -> dict[str, Any]:
    """Build Google Health civil date-time ending at 23:59:59 UTC."""
    return {
        "date": {"year": day.year, "month": day.month, "day": day.day},
        "time": {"hours": 23, "minutes": 59, "seconds": 59, "nanos": 0},
    }


@handle_errors("building civil date range payload", default_return={})
def _build_civil_range(start_date: date, end_date: date) -> dict[str, Any]:
    """Civil date range for dailyRollUp (per Google Health API examples)."""
    return {
        "start": _civil_datetime(start_date),
        "end": _civil_end_of_day(end_date),
    }


@handle_errors("listing Google Health daily rollups", default_return=[], re_raise=True)
def _list_daily_rollups_single(
    access_token: str,
    endpoint: str,
    *,
    start_date: date,
    end_date: date,
    window_size_days: int = 1,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    """Single dailyRollUp request for an inclusive civil date range (max ~14 days)."""
    url = f"{GOOGLE_HEALTH_API_BASE_URL}/users/me/dataTypes/{endpoint}/dataPoints:dailyRollUp"
    body: dict[str, Any] = {
        "range": _build_civil_range(start_date, end_date),
        "windowSizeDays": window_size_days,
        "pageSize": page_size,
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    collected: list[dict[str, Any]] = []
    page_token: str | None = None

    while True:
        if page_token:
            body["pageToken"] = page_token
        elif "pageToken" in body:
            del body["pageToken"]

        response = requests.post(url, headers=headers, json=body, timeout=60)
        if response.status_code != 200:
            body_preview = (response.text or "")[:300]
            logger.warning(
                f"Google Health dailyRollUp failed for {endpoint} status={response.status_code} "
                f"range={start_date.isoformat()}..{end_date.isoformat()} body={body_preview!r}"
            )
            raise CommunicationError(f"Google Health dailyRollUp error for {endpoint}")

        payload = response.json()
        batch = payload.get("rollupDataPoints") or []
        collected.extend(batch)
        page_token = payload.get("nextPageToken") or None
        if not page_token:
            break

    return collected


@handle_errors("listing Google Health daily rollups", default_return=[])
def list_daily_rollups(
    access_token: str,
    data_type: str,
    *,
    start_time: datetime,
    end_time: datetime,
    window_size_days: int = 1,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    """Fetch daily rollup totals in <=14-day civil chunks (Google API limit)."""
    if _testing_mode():
        return []

    endpoint, _, _ = _resolve_data_type_spec(data_type)
    start_date = start_time.astimezone(timezone.utc).date()
    end_date = end_time.astimezone(timezone.utc).date()
    collected: list[dict[str, Any]] = []
    chunk_start = start_date

    while chunk_start <= end_date:
        chunk_end = min(chunk_start + timedelta(days=_ROLLUP_MAX_DAYS - 1), end_date)
        collected.extend(
            _list_daily_rollups_single(
                access_token,
                endpoint,
                start_date=chunk_start,
                end_date=chunk_end,
                window_size_days=window_size_days,
                page_size=page_size,
            )
        )
        chunk_start = chunk_end + timedelta(days=1)

    logger.info(
        f"Google Health dailyRollUp returned {len(collected)} day(s) for {endpoint}"
    )
    return collected


@handle_errors("listing Google Health data points in chunks", default_return=[])
def _list_data_points_chunked(
    access_token: str,
    data_type: str,
    *,
    start_time: datetime,
    end_time: datetime,
    chunk_days: int = _LIST_CHUNK_DAYS,
) -> list[dict[str, Any]]:
    """List interval data in smaller windows to avoid Google server errors on wide queries."""
    collected: list[dict[str, Any]] = []
    chunk_start = start_time
    while chunk_start < end_time:
        chunk_end = min(chunk_start + timedelta(days=chunk_days), end_time)
        try:
            collected.extend(
                list_data_points(
                    access_token,
                    data_type,
                    start_time=chunk_start,
                    end_time=chunk_end,
                )
            )
        except CommunicationError:
            logger.warning(
                f"Chunked list failed for {data_type} "
                f"{chunk_start.isoformat()}..{chunk_end.isoformat()}"
            )
        chunk_start = chunk_end
    return collected


@handle_errors("fetching Google Health points for data type", default_return=[])
def _fetch_points_for_type(
    access_token: str,
    fetcher: _Fetcher,
    *,
    start_time: datetime,
    end_time: datetime,
) -> list[dict[str, Any]]:
    if fetcher.source == "daily_rollup":
        try:
            return list_daily_rollups(
                access_token,
                fetcher.endpoint,
                start_time=start_time,
                end_time=end_time,
            )
        except CommunicationError:
            logger.warning(
                f"dailyRollUp failed for {fetcher.endpoint}; falling back to chunked list"
            )
            return _list_data_points_chunked(
                access_token,
                fetcher.endpoint,
                start_time=start_time,
                end_time=end_time,
            )
    if fetcher.filter_mode == "interval_start":
        return _list_data_points_chunked(
            access_token,
            fetcher.endpoint,
            start_time=start_time,
            end_time=end_time,
        )
    return list_data_points(
        access_token,
        fetcher.endpoint,
        start_time=start_time,
        end_time=end_time,
    )


@handle_errors("parsing Google Health API date", default_return=None)
def _parse_api_date(value: Any) -> str | None:
    """Normalize API date values to YYYY-MM-DD strings."""
    if value is None:
        return None
    if isinstance(value, str):
        return value[:10]
    if isinstance(value, dict) and {"year", "month", "day"} <= value.keys():
        try:
            return f"{int(value['year']):04d}-{int(value['month']):02d}-{int(value['day']):02d}"
        except (TypeError, ValueError):
            return None
    return None


@handle_errors("parsing duration to minutes", default_return=None)
def _parse_duration_minutes(value: Any) -> int | None:
    """Parse Google Health duration fields into whole minutes."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        if value.endswith("s") and value[:-1].replace(".", "", 1).isdigit():
            return int(float(value[:-1]) / 60)
        if ":" in value:
            parts = value.split(":")
            try:
                if len(parts) == 3:
                    h, m, s = (int(p) for p in parts)
                    return h * 60 + m + (1 if s >= 30 else 0)
                if len(parts) == 2:
                    h, m = (int(p) for p in parts)
                    return h * 60 + m
            except ValueError:
                return None
    if isinstance(value, dict):
        seconds = value.get("seconds")
        if isinstance(seconds, (int, float)):
            return int(seconds / 60)
    return None


@handle_errors("parsing ISO datetime", default_return=None)
def _parse_iso_datetime(raw: str) -> datetime | None:
    """Parse ISO-8601 timestamps from Google Health API responses."""
    if not raw:
        return None
    text = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


@handle_errors("computing interval duration minutes", default_return=None)
def _interval_duration_minutes(interval: dict[str, Any]) -> int | None:
    """Compute minutes between interval start and end timestamps."""
    start_raw = interval.get("startTime") or interval.get("start_time")
    end_raw = interval.get("endTime") or interval.get("end_time")
    start = _parse_iso_datetime(str(start_raw)) if start_raw else None
    end = _parse_iso_datetime(str(end_raw)) if end_raw else None
    if start and end and end > start:
        return int((end - start).total_seconds() / 60)
    return None


@handle_errors("extracting date from civil datetime", default_return=None)
def _date_from_civil_datetime(civil: Any) -> str | None:
    """Extract YYYY-MM-DD from a Google Health civil datetime object."""
    if not isinstance(civil, dict):
        return None
    return _parse_api_date(civil.get("date"))


@handle_errors("extracting date from interval", default_return=None)
def _date_from_interval(interval: dict[str, Any]) -> str | None:
    """Extract calendar date from a Google Health interval payload."""
    if not interval:
        return None
    for civil_key in (
        "civilStartTime",
        "civil_start_time",
        "civilEndTime",
        "civil_end_time",
    ):
        civil = interval.get(civil_key)
        if isinstance(civil, dict):
            parsed = _date_from_civil_datetime(civil)
            if parsed:
                return parsed
        elif isinstance(civil, str):
            return civil[:10]
    for time_key in ("startTime", "start_time", "endTime", "end_time"):
        raw = interval.get(time_key)
        if raw and isinstance(raw, str):
            return raw[:10]
    return None


@handle_errors("extracting date from data point", default_return=None)
def _date_from_data_point(point: dict[str, Any]) -> str | None:
    """Extract calendar date from any supported Google Health data point shape."""
    for key in ("date", "civilDate"):
        parsed = _parse_api_date(point.get(key))
        if parsed:
            return parsed

    parsed = _date_from_civil_datetime(point.get("civilStartTime"))
    if parsed:
        return parsed

    for nested_key in (
        "dailyRestingHeartRate",
        "dailyHeartRateVariability",
        "activeZoneMinutes",
        "active_zone_minutes",
        "steps",
        "sleep",
    ):
        nested = point.get(nested_key)
        if not isinstance(nested, dict):
            continue
        parsed = _parse_api_date(nested.get("date"))
        if parsed:
            return parsed
        parsed = _date_from_interval(nested.get("interval") or {})
        if parsed:
            return parsed

    return _date_from_interval(point.get("interval") or {})


@handle_errors("extracting sleep payload", default_return={})
def _sleep_payload(point: dict[str, Any]) -> dict[str, Any]:
    """Return nested sleep object or the point itself when sleep is top-level."""
    return point.get("sleep") or point


@handle_errors("coercing integer metric", default_return=None)
def _coerce_int(value: Any) -> int | None:
    """Safely coerce API numeric values to int."""
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


@handle_errors("coercing float metric", default_return=None)
def _coerce_float(value: Any) -> float | None:
    """Safely coerce API numeric values to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@handle_errors("appending completeness tag", default_return=None)
def _append_completeness(summary: dict[str, Any], tag: str) -> None:
    """Track which metric groups were populated for a daily summary."""
    summary.setdefault("completeness", [])
    if tag not in summary["completeness"]:
        summary["completeness"].append(tag)


@handle_errors("appending API record id", default_return=None)
def _append_record_id(summary: dict[str, Any], point: dict[str, Any]) -> None:
    """Record Google Health data point resource name for traceability."""
    name = point.get("name") or point.get("dataPointName") or ""
    if name:
        summary.setdefault("api_record_ids", []).append(str(name))


@handle_errors("merging sleep into daily summary", default_return=None)
def _merge_sleep_into_summary(summary: dict[str, Any], point: dict[str, Any]) -> None:
    """Merge sleep duration, efficiency, and stages into a daily summary dict."""
    sleep = _sleep_payload(point)
    interval = sleep.get("interval") or point.get("interval") or {}
    duration = _parse_duration_minutes(
        sleep.get("duration") or sleep.get("timeInBed") or sleep.get("time_in_bed")
    )
    if duration is None:
        duration = _interval_duration_minutes(interval)
    if duration is not None:
        summary["sleep_duration_minutes"] = max(
            summary.get("sleep_duration_minutes") or 0, duration
        )
    efficiency = sleep.get("efficiency") or sleep.get("sleepEfficiency")
    if efficiency is not None:
        with suppress(TypeError, ValueError):
            summary["sleep_efficiency_pct"] = float(efficiency)
    stages_raw = sleep.get("stages") or sleep.get("stageSummary") or {}
    if isinstance(stages_raw, list):
        totals = {"light": 0, "deep": 0, "rem": 0, "awake": 0}
        for stage in stages_raw:
            stage_type = str(stage.get("type") or "").lower()
            minutes = _interval_duration_minutes(stage) or 0
            if "light" in stage_type:
                totals["light"] += minutes
            elif "deep" in stage_type:
                totals["deep"] += minutes
            elif "rem" in stage_type:
                totals["rem"] += minutes
            elif "awake" in stage_type:
                totals["awake"] += minutes
        stages_raw = {k: v for k, v in totals.items() if v}
    if stages_raw:
        stages = SleepStagesSummaryModel(
            light_minutes=_parse_duration_minutes(stages_raw.get("light")),
            deep_minutes=_parse_duration_minutes(stages_raw.get("deep")),
            rem_minutes=_parse_duration_minutes(stages_raw.get("rem")),
            awake_minutes=_parse_duration_minutes(stages_raw.get("awake")),
        )
        summary["sleep_stages"] = stages.model_dump(exclude_none=True)
    _append_record_id(summary, point)
    if duration is not None or efficiency is not None or stages_raw:
        _append_completeness(summary, "sleep")


@handle_errors("merging steps into daily summary", default_return=None)
def _merge_steps_into_summary(summary: dict[str, Any], point: dict[str, Any]) -> None:
    """Merge step counts into a daily summary dict."""
    steps_obj = point.get("steps") or point
    value = (
        steps_obj.get("countSum")
        or steps_obj.get("count_sum")
        or steps_obj.get("count")
        or steps_obj.get("value")
        or point.get("value")
    )
    step_count = _coerce_int(value)
    if step_count is not None:
        if steps_obj.get("countSum") is not None or steps_obj.get("count_sum") is not None:
            summary["steps"] = step_count
        else:
            summary["steps"] = (summary.get("steps") or 0) + step_count
        _append_completeness(summary, "activity")
    _append_record_id(summary, point)


@handle_errors("merging active minutes into daily summary", default_return=None)
def _merge_active_minutes(summary: dict[str, Any], point: dict[str, Any]) -> None:
    """Merge active zone minutes into a daily summary dict."""
    azm = point.get("activeZoneMinutes") or point.get("active_zone_minutes") or point
    zone_keys = ("sumInCardioHeartZone", "sumInPeakHeartZone", "sumInFatBurnHeartZone")
    if any(azm.get(key) is not None for key in zone_keys):
        minutes = sum(_coerce_int(azm.get(key)) or 0 for key in zone_keys)
        summary["active_minutes"] = minutes
        _append_completeness(summary, "activity")
        _append_record_id(summary, point)
        return
    value = (
        azm.get("activeZoneMinutes")
        or azm.get("active_zone_minutes")
        or azm.get("minutes")
        or azm.get("count")
        or azm.get("value")
    )
    minutes = _coerce_int(value)
    if minutes is not None:
        summary["active_minutes"] = (summary.get("active_minutes") or 0) + minutes
        _append_completeness(summary, "activity")
    _append_record_id(summary, point)


@handle_errors("merging resting heart rate into daily summary", default_return=None)
def _merge_resting_hr(summary: dict[str, Any], point: dict[str, Any]) -> None:
    """Merge resting heart rate into a daily summary dict."""
    hr = point.get("dailyRestingHeartRate") or point.get("heartRate") or point
    value = (
        hr.get("beatsPerMinute")
        or hr.get("value")
        or hr.get("bpm")
        or hr.get("restingBpm")
    )
    bpm = _coerce_float(value)
    if bpm is not None:
        summary["resting_hr_bpm"] = bpm
        _append_completeness(summary, "heart_rate")
    _append_record_id(summary, point)


@handle_errors("merging HRV into daily summary", default_return=None)
def _merge_hrv(summary: dict[str, Any], point: dict[str, Any]) -> None:
    """Merge heart rate variability into a daily summary dict."""
    hrv = point.get("dailyHeartRateVariability") or point
    value = (
        hrv.get("averageHeartRateVariabilityMilliseconds")
        or hrv.get("deepSleepRootMeanSquareOfSuccessiveDifferencesMilliseconds")
        or hrv.get("rmssd")
        or hrv.get("value")
        or hrv.get("dailyRmssd")
    )
    rmssd = _coerce_float(value)
    if rmssd is not None:
        summary["hrv_rmssd_ms"] = rmssd
        _append_completeness(summary, "hrv")
    _append_record_id(summary, point)


_FETCHERS: tuple[_Fetcher, ...] = (
    _Fetcher("sleep", "sleep", "session_end", _merge_sleep_into_summary),
    _Fetcher(
        "steps",
        "steps",
        "interval_start",
        _merge_steps_into_summary,
        source="daily_rollup",
    ),
    _Fetcher(
        "active-zone-minutes",
        "active_zone_minutes",
        "interval_start",
        _merge_active_minutes,
        source="daily_rollup",
    ),
    _Fetcher(
        "daily-resting-heart-rate",
        "daily_resting_heart_rate",
        "daily_date",
        _merge_resting_hr,
    ),
    _Fetcher(
        "daily-heart-rate-variability",
        "daily_heart_rate_variability",
        "daily_date",
        _merge_hrv,
    ),
)


@handle_errors("fetching daily summaries from Google Health", default_return=[])
def fetch_daily_summaries(
    access_token: str,
    *,
    lookback_days: int = 3,
) -> list[dict[str, Any]]:
    """Fetch and normalize daily summaries for the lookback window."""
    if _testing_mode():
        return []

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=max(lookback_days, 1))
    by_date: dict[str, dict[str, Any]] = {}

    for fetcher in _FETCHERS:
        try:
            points = _fetch_points_for_type(
                access_token,
                fetcher,
                start_time=start,
                end_time=end,
            )
        except CommunicationError:
            logger.warning(f"Skipping data type {fetcher.endpoint} due to API error")
            continue

        skipped_dates = 0
        for point in points:
            day = _date_from_data_point(point)
            if not day:
                skipped_dates += 1
                continue
            summary = by_date.setdefault(
                day,
                {
                    "date": day,
                    "source_synced_at": now_timestamp_full(),
                    "api_record_ids": [],
                    "completeness": [],
                },
            )
            fetcher.merge(summary, point)
        if skipped_dates:
            logger.debug(
                f"Skipped {skipped_dates} {fetcher.endpoint} point(s) with no parseable date"
            )

    results: list[dict[str, Any]] = []
    for day_key in sorted(by_date.keys()):
        try:
            model = DailySummaryModel.model_validate(by_date[day_key])
            results.append(model.model_dump())
        except Exception as exc:
            logger.warning(f"Skipping invalid summary for {day_key}: {exc}")
    logger.info(f"Google Health fetch produced {len(results)} daily summar(ies)")
    return results
