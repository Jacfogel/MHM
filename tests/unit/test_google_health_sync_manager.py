"""Unit tests for health data handlers and sync manager."""

from unittest.mock import patch

import pytest

from core import update_user_account
from integrations.google_health.data_handlers import (
    delete_user_health_data,
    ensure_health_directory,
    load_daily_summaries,
    load_sync_state,
    save_auth,
)
from integrations.google_health.sync_manager import (
    sync_user_health_data,
    upsert_daily_summaries,
)
from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory


@pytest.mark.unit
@pytest.mark.user
def test_ensure_health_directory_creates_files(test_data_dir):
    user_id = "health-test-user-001"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
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
def test_sync_skips_when_feature_paused(test_data_dir, monkeypatch):
    user_id = "health-test-user-002"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    update_user_account(user_id, {"features": {"google_health": "paused"}})
    monkeypatch.setenv("MHM_TESTING", "0")
    with patch("integrations.google_health.sync_manager.GOOGLE_HEALTH_ENABLED", True):
        assert sync_user_health_data(user_id, force=True) is False


@pytest.mark.unit
@pytest.mark.user
def test_sync_completes_with_mocked_api(test_data_dir, monkeypatch):
    user_id = "health-test-user-sync"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
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
    monkeypatch.setenv("MHM_TESTING", "0")
    sample = [{"date": "2026-06-27", "steps": 5000, "completeness": ["activity"]}]
    with patch("integrations.google_health.sync_manager.GOOGLE_HEALTH_ENABLED", True), patch(
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
    user_id = "health-test-user-003"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    ensure_health_directory(user_id)
    assert delete_user_health_data(user_id) is True
    assert ensure_health_directory(user_id) is True
