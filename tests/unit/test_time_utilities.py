"""Tests for canonical time utility helpers."""

from datetime import datetime, timezone
import time

import pytest

from core import time_utilities

pytestmark = [pytest.mark.unit, pytest.mark.core]


@pytest.mark.unit
@pytest.mark.core
def test_now_datetime_utc_returns_aware_second_precision(monkeypatch):
    fixed_now = datetime(2026, 5, 12, 14, 15, 16, 123456, tzinfo=timezone.utc)

    class FixedDatetime:
        min = datetime.min

        @staticmethod
        def now(tz=None):
            assert tz is timezone.utc
            return fixed_now

    monkeypatch.setattr(time_utilities, "datetime", FixedDatetime)

    result = time_utilities.now_datetime_utc()

    assert result == datetime(2026, 5, 12, 14, 15, 16, tzinfo=timezone.utc)
    assert result.tzinfo is timezone.utc


@pytest.mark.unit
@pytest.mark.core
def test_now_timestamp_utc_iso_uses_canonical_utc_now(monkeypatch):
    fixed_now = datetime(2026, 5, 12, 14, 15, 16, tzinfo=timezone.utc)
    monkeypatch.setattr(time_utilities, "now_datetime_utc", lambda: fixed_now)

    assert time_utilities.now_timestamp_utc_iso() == "2026-05-12T14:15:16+00:00"


@pytest.mark.unit
@pytest.mark.core
def test_parse_flexible_date_only_accepts_common_variants():
    assert time_utilities.parse_flexible_date_only("2026-07-01") == "2026-07-01"
    assert time_utilities.parse_flexible_date_only("2026 07 01") == "2026-07-01"
    assert time_utilities.parse_flexible_date_only("2026/07/01") == "2026-07-01"
    assert time_utilities.parse_flexible_date_only("not a date") is None


@pytest.mark.unit
@pytest.mark.core
def test_format_time_compact_hour_minute():
    value = datetime(2026, 5, 12, 4, 5, 6)

    assert time_utilities.format_time_compact_hour_minute(value) == "0405"


@pytest.mark.unit
@pytest.mark.core
def test_format_datetime_for_ai_prompt():
    value = datetime(2026, 7, 7, 22, 54, 0)

    assert (
        time_utilities.format_datetime_for_ai_prompt(value)
        == "Tuesday, 2026-07-07 at 22:54"
    )


@pytest.mark.unit
@pytest.mark.core
def test_format_time_tuple():
    value = time.struct_time((2026, 5, 12, 0, 0, 0, 1, 132, -1))

    assert time_utilities.format_time_tuple(value, "%Y-%m-%d") == "2026-05-12"
