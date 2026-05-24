"""Unit tests for scheduler user timezone resolution."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from scheduler.user_timezone import (
    DEFAULT_SCHEDULER_TIMEZONE,
    localized_now_for_user,
    resolve_user_timezone_str,
)


@pytest.mark.unit
class TestResolveUserTimezoneStr:
    def test_returns_account_timezone_when_valid(self):
        with patch("core.get_user_data") as mock_get:
            mock_get.return_value = {"account": {"timezone": "America/New_York"}}

            assert resolve_user_timezone_str("user-1") == "America/New_York"

    def test_falls_back_when_timezone_missing(self):
        with patch("core.get_user_data") as mock_get:
            mock_get.return_value = {"account": {}}

            assert resolve_user_timezone_str("user-1") == DEFAULT_SCHEDULER_TIMEZONE

    def test_falls_back_when_timezone_invalid(self):
        with patch("core.get_user_data") as mock_get:
            mock_get.return_value = {"account": {"timezone": "Not/A_Real_Zone"}}

            assert resolve_user_timezone_str("user-1") == DEFAULT_SCHEDULER_TIMEZONE

    def test_falls_back_for_empty_user_id(self):
        assert resolve_user_timezone_str("") == DEFAULT_SCHEDULER_TIMEZONE


@pytest.mark.unit
class TestLocalizedNowForUser:
    def test_localizes_canonical_now_in_user_timezone(self, monkeypatch):
        from datetime import datetime

        import pytz

        fixed_naive = datetime(2026, 1, 20, 12, 0, 0)

        with patch(
            "scheduler.user_timezone.resolve_user_timezone_str",
            return_value="America/Regina",
        ):
            monkeypatch.setattr(
                "scheduler.user_timezone.now_datetime_full",
                lambda: fixed_naive,
            )

            result = localized_now_for_user("user-1")

        expected = pytz.timezone("America/Regina").localize(fixed_naive)
        assert result == expected
        assert result.tzinfo is not None
