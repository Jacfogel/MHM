"""Unit tests for per-user Google Health sync scheduling."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest
import pytz

from scheduler.health_sync_schedule import get_due_sync_slot_key


def _local_dt(tz_name: str, year: int, month: int, day: int, hour: int, minute: int):
    tz = pytz.timezone(tz_name)
    return tz.localize(datetime(year, month, day, hour, minute, 0))


@pytest.mark.unit
@pytest.mark.scheduler
def test_no_slot_due_before_first_sync_time():
    now = _local_dt("America/Regina", 2026, 6, 28, 5, 0)
    assert (
        get_due_sync_slot_key(
            "user-1",
            now_local=now,
            sync_times=["06:30", "18:00"],
            last_scheduled_slot="",
        )
        is None
    )


@pytest.mark.unit
@pytest.mark.scheduler
def test_morning_slot_due_after_local_sync_time():
    now = _local_dt("America/Regina", 2026, 6, 28, 7, 0)
    assert (
        get_due_sync_slot_key(
            "user-1",
            now_local=now,
            sync_times=["06:30", "18:00"],
            last_scheduled_slot="",
        )
        == "2026-06-28_06:30"
    )


@pytest.mark.unit
@pytest.mark.scheduler
def test_evening_slot_due_after_morning_slot_completed():
    now = _local_dt("America/Regina", 2026, 6, 28, 19, 0)
    assert (
        get_due_sync_slot_key(
            "user-1",
            now_local=now,
            sync_times=["06:30", "18:00"],
            last_scheduled_slot="2026-06-28_06:30",
        )
        == "2026-06-28_18:00"
    )


@pytest.mark.unit
@pytest.mark.scheduler
def test_not_due_when_latest_slot_already_synced():
    now = _local_dt("America/Regina", 2026, 6, 28, 20, 0)
    assert (
        get_due_sync_slot_key(
            "user-1",
            now_local=now,
            sync_times=["06:30", "18:00"],
            last_scheduled_slot="2026-06-28_18:00",
        )
        is None
    )


@pytest.mark.unit
@pytest.mark.scheduler
def test_different_timezone_uses_local_wall_clock():
    # 12:00 UTC = 08:00 America/New_York (EDT, June)
    now = _local_dt("America/New_York", 2026, 6, 28, 8, 0)
    assert (
        get_due_sync_slot_key(
            "user-1",
            now_local=now,
            sync_times=["06:30", "18:00"],
            last_scheduled_slot="",
        )
        == "2026-06-28_06:30"
    )


@pytest.mark.unit
@pytest.mark.scheduler
def test_sync_users_due_for_schedule_skips_when_not_due(test_data_dir):
    from core import update_user_account
    from integrations.google_health.data_handlers import ensure_health_directory, save_auth
    from integrations.google_health.sync_manager import sync_users_due_for_schedule
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = "health-schedule-user-001"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    update_user_account(
        user_id, {"features": {"google_health": "enabled"}, "timezone": "America/Regina"}
    )
    ensure_health_directory(user_id)
    save_auth(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-27 12:00:00",
            "access_token": "token",
            "refresh_token": "refresh",
            "expires_at": "2099-01-01 00:00:00",
        },
    )

    early = _local_dt("America/Regina", 2026, 6, 28, 5, 0)
    with patch.dict("os.environ", {"MHM_TESTING": "0"}, clear=False), patch(
        "integrations.google_health.sync_manager.GOOGLE_HEALTH_ENABLED", True
    ), patch(
        "integrations.google_health.sync_manager.get_all_user_ids",
        return_value=[user_id],
    ), patch(
        "scheduler.health_sync_schedule.localized_now_for_user",
        return_value=early,
    ), patch(
        "integrations.google_health.sync_manager.sync_user_health_data"
    ) as sync_mock:
        assert sync_users_due_for_schedule() == 0
        sync_mock.assert_not_called()


@pytest.mark.unit
@pytest.mark.scheduler
def test_sync_users_due_for_schedule_syncs_due_user(test_data_dir):
    from core import update_user_account
    from integrations.google_health.data_handlers import ensure_health_directory, save_auth
    from integrations.google_health.sync_manager import sync_users_due_for_schedule
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = "health-schedule-user-002"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    update_user_account(
        user_id, {"features": {"google_health": "enabled"}, "timezone": "America/Regina"}
    )
    ensure_health_directory(user_id)
    save_auth(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-27 12:00:00",
            "access_token": "token",
            "refresh_token": "refresh",
            "expires_at": "2099-01-01 00:00:00",
        },
    )

    due = _local_dt("America/Regina", 2026, 6, 28, 7, 0)
    with patch.dict("os.environ", {"MHM_TESTING": "0"}, clear=False), patch(
        "integrations.google_health.sync_manager.GOOGLE_HEALTH_ENABLED", True
    ), patch(
        "integrations.google_health.sync_manager.get_all_user_ids",
        return_value=[user_id],
    ), patch(
        "scheduler.health_sync_schedule.localized_now_for_user",
        return_value=due,
    ), patch(
        "integrations.google_health.sync_manager.sync_user_health_data",
        return_value=True,
    ) as sync_mock:
        assert sync_users_due_for_schedule() == 1

    sync_mock.assert_called_once_with(
        user_id, scheduled_slot_key="2026-06-28_06:30"
    )
