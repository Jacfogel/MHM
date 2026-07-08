"""Unit coverage for check-in command service helpers."""

from datetime import date, datetime, time
from unittest.mock import patch

import pytest

from checkins import checkin_service


@pytest.mark.unit
@pytest.mark.checkins
def test_get_checkin_start_status_detects_disabled_user():
    with patch("checkins.checkin_service.is_user_checkins_enabled", return_value=False):
        status = checkin_service.get_checkin_start_status("u1")

    assert status.enabled is False
    assert status.already_completed_today is False


@pytest.mark.unit
@pytest.mark.checkins
def test_get_checkin_start_status_detects_today_checkin():
    with patch("checkins.checkin_service.is_user_checkins_enabled", return_value=True), patch(
        "checkins.checkin_service.get_recent_checkins",
        return_value=[{"timestamp": "2026-05-11 08:00:00"}],
    ), patch(
        "checkins.checkin_service.checkin_runtime_timestamp",
        return_value="2026-05-11 08:00:00",
    ), patch(
        "checkins.checkin_service.parse_timestamp_full",
        return_value=datetime.combine(date.today(), time(8, 0)),
    ), patch(
        "checkins.checkin_service.user_local_date",
        return_value=date.today(),
    ):
        status = checkin_service.get_checkin_start_status("u1")

    assert status.enabled is True
    assert status.already_completed_today is True


@pytest.mark.unit
@pytest.mark.checkins
def test_checkin_display_date_falls_back_to_timestamp():
    with patch(
        "checkins.checkin_service.checkin_runtime_timestamp",
        return_value="2026-05-10 09:00:00",
    ), patch(
        "checkins.checkin_service.parse_timestamp_full",
        return_value=datetime(2026, 5, 10, 9, 0),
    ):
        assert checkin_service.checkin_display_date({}) == "2026-05-10"
