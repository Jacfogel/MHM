"""Unit tests for health data handlers and sync manager."""

import uuid
from unittest.mock import patch

import pytest

from core import update_user_account
from core.error_handling import CommunicationError
from core.user_lookup import get_user_id_by_identifier
from integrations.google_health.data_handlers import (
    delete_user_health_data,
    ensure_health_directory,
    load_daily_summaries,
    load_sync_state,
    save_auth,
    save_sync_state,
)
from integrations.google_health.sync_manager import (
    sync_user_health_data,
    upsert_daily_summaries,
)
from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory


def _indexed_factory_user(username: str, test_data_dir: str) -> str:
    """Create a factory user and return the on-disk UUID, not the username."""
    assert TestUserFactory.create_basic_user(username, test_data_dir=test_data_dir)
    user_id = get_user_id_by_identifier(username)
    assert user_id, f"factory did not index user {username!r}"
    return user_id


def _allow_live_health_sync():
    """Skip the MHM_TESTING guard without disabling test-only user-data healing."""
    return patch(
        "integrations.google_health.sync_manager.is_google_health_testing_mode",
        return_value=False,
    )


def _health_user(test_data_dir: str, prefix: str = "health") -> str:
    user_id = _indexed_factory_user(f"{prefix}-{uuid.uuid4().hex[:8]}", test_data_dir)
    update_user_account(user_id, {"features": {"google_health": "enabled"}})
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
    return user_id


@pytest.mark.unit
@pytest.mark.user
def test_ensure_health_directory_creates_files(test_data_dir):
    user_id = _indexed_factory_user(
        f"health-test-user-001-{uuid.uuid4().hex[:8]}", test_data_dir
    )
    assert ensure_health_directory(user_id) is True
    doc = load_daily_summaries(user_id)
    assert doc is not None
    assert doc.get("schema_version") == 2
    assert doc.get("summaries") == []


@pytest.mark.unit
@pytest.mark.core
def test_upsert_daily_summaries_merges_by_date():
    existing = [{"date": "2026-06-26", "steps": 1000}]
    incoming = [{"date": "2026-06-27", "steps": 2000}, {"date": "2026-06-26", "steps": 1500}]
    merged = upsert_daily_summaries(existing, incoming)
    assert len(merged) == 2
    by_date = {item["date"]: item for item in merged}
    assert by_date["2026-06-26"]["steps"] == 1500
    assert by_date["2026-06-27"]["steps"] == 2000


@pytest.mark.unit
@pytest.mark.core
def test_upsert_daily_summaries_preserves_existing_fields_when_incoming_omits_them():
    existing = [
        {
            "date": "2026-06-26",
            "steps": 5000,
            "active_minutes": 7,
            "sleep_duration_minutes": 433,
        }
    ]
    incoming = [
        {
            "date": "2026-06-26",
            "steps": None,
            "active_minutes": None,
            "sleep_duration_minutes": 433,
            "resting_hr_bpm": 68.0,
            "completeness": ["sleep", "heart_rate"],
        }
    ]
    merged = upsert_daily_summaries(existing, incoming)
    row = merged[0]
    assert row["steps"] == 5000
    assert row["active_minutes"] == 7
    assert row["resting_hr_bpm"] == 68.0


@pytest.mark.unit
@pytest.mark.user
def test_sync_skips_when_feature_paused(test_data_dir):
    user_id = _indexed_factory_user(
        f"health-test-user-002-{uuid.uuid4().hex[:8]}", test_data_dir
    )
    update_user_account(user_id, {"features": {"google_health": "paused"}})
    with _allow_live_health_sync(), patch(
        "integrations.google_health.sync_manager.GOOGLE_HEALTH_ENABLED", True
    ):
        assert sync_user_health_data(user_id, force=True) is False


@pytest.mark.unit
@pytest.mark.user
def test_sync_completes_with_mocked_api(test_data_dir):
    user_id = _indexed_factory_user(
        f"health-test-user-sync-{uuid.uuid4().hex[:8]}", test_data_dir
    )
    update_user_account(user_id, {"features": {"google_health": "enabled"}})
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
    sample = [{"date": "2026-06-27", "steps": 5000, "completeness": ["activity"]}]
    with _allow_live_health_sync(), patch(
        "integrations.google_health.sync_manager.GOOGLE_HEALTH_ENABLED", True
    ), patch(
        "integrations.google_health.sync_manager.ensure_valid_access_token",
        return_value="token",
    ), patch(
        "integrations.google_health.sync_manager.fetch_daily_summaries",
        return_value=sample,
    ):
        assert sync_user_health_data(user_id, force=True) is True

    state = load_sync_state(user_id) or {}
    assert state.get("last_success_at")
    assert not state.get("last_error")
    doc = load_daily_summaries(user_id) or {}
    assert doc.get("summaries")


@pytest.mark.unit
@pytest.mark.user
def test_delete_user_health_data(test_data_dir):
    user_id = _indexed_factory_user(
        f"health-test-user-003-{uuid.uuid4().hex[:8]}", test_data_dir
    )
    ensure_health_directory(user_id)
    assert delete_user_health_data(user_id) is True
    assert ensure_health_directory(user_id) is True


@pytest.mark.unit
@pytest.mark.integrations
def test_sync_api_error_increments_failures_without_reconnect_notice(test_data_dir):
    user_id = _health_user(test_data_dir, "health-api-err")
    with (
        _allow_live_health_sync(),
        patch("integrations.google_health.sync_manager.GOOGLE_HEALTH_ENABLED", True),
        patch(
            "integrations.google_health.sync_manager.GOOGLE_HEALTH_SYNC_FAILURE_PAUSE_THRESHOLD",
            1,
        ),
        patch(
            "integrations.google_health.sync_manager.ensure_valid_access_token",
            return_value="token",
        ),
        patch(
            "integrations.google_health.sync_manager.fetch_daily_summaries",
            side_effect=CommunicationError("Google Health API error for sleep"),
        ),
        patch(
            "integrations.google_health.sync_manager.pause_google_health_feature"
        ) as pause,
        patch(
            "integrations.google_health.notifications.send_reconnect_notice"
        ) as send_notice,
    ):
        assert sync_user_health_data(user_id, force=True) is False

    pause.assert_called_once()
    send_notice.assert_not_called()
    state = load_sync_state(user_id) or {}
    assert int(state.get("consecutive_failures") or 0) >= 1
    assert not state.get("reconnect_notice_sent")
    assert "API error" in str(state.get("last_error") or "")


@pytest.mark.unit
@pytest.mark.integrations
def test_sync_timeout_returns_false_without_crash(test_data_dir):
    user_id = _health_user(test_data_dir, "health-timeout")
    with (
        _allow_live_health_sync(),
        patch("integrations.google_health.sync_manager.GOOGLE_HEALTH_ENABLED", True),
        patch(
            "integrations.google_health.sync_manager.ensure_valid_access_token",
            return_value="token",
        ),
        patch(
            "integrations.google_health.sync_manager.fetch_daily_summaries",
            side_effect=TimeoutError("Google Health request timed out"),
        ),
    ):
        assert sync_user_health_data(user_id, force=True) is False
    state = load_sync_state(user_id) or {}
    assert int(state.get("consecutive_failures") or 0) >= 1
    assert "timed out" in str(state.get("last_error") or "").lower()


@pytest.mark.unit
@pytest.mark.integrations
def test_sync_success_clears_reconnect_notice_and_failures(test_data_dir):
    user_id = _health_user(test_data_dir, "health-clear")
    save_sync_state(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-27 12:00:00",
            "consecutive_failures": 4,
            "reconnect_notice_sent": True,
            "last_error": "previous auth failure",
            "last_scheduled_slot": "morning",
        },
    )
    sample = [{"date": "2026-06-27", "steps": 5000, "completeness": ["activity"]}]
    with (
        _allow_live_health_sync(),
        patch("integrations.google_health.sync_manager.GOOGLE_HEALTH_ENABLED", True),
        patch(
            "integrations.google_health.sync_manager.ensure_valid_access_token",
            return_value="token",
        ),
        patch(
            "integrations.google_health.sync_manager.fetch_daily_summaries",
            return_value=sample,
        ),
    ):
        assert sync_user_health_data(user_id, force=True, scheduled_slot_key="evening") is True

    state = load_sync_state(user_id) or {}
    assert state.get("consecutive_failures") == 0
    assert state.get("reconnect_notice_sent") is False
    assert not state.get("last_error")
    assert state.get("last_scheduled_slot") == "evening"


@pytest.mark.unit
@pytest.mark.integrations
@pytest.mark.file_io
def test_google_health_sync_state_survives_reload(test_data_dir):
    user_id = _health_user(test_data_dir, "health-reload")
    assert save_sync_state(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-27 12:00:00",
            "reconnect_notice_sent": True,
            "last_scheduled_slot": "morning",
            "consecutive_failures": 2,
            "last_error": "temporary",
        },
    )
    reloaded = load_sync_state(user_id) or {}
    assert reloaded.get("reconnect_notice_sent") is True
    assert reloaded.get("last_scheduled_slot") == "morning"
    assert reloaded.get("consecutive_failures") == 2
