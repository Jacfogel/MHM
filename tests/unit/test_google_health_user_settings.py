"""Unit tests for shared Google Health user settings operations."""

import pytest

from integrations.google_health.user_settings import (
    format_status_text,
    get_connect_readiness,
    get_health_integration_status,
    HealthIntegrationStatus,
    pause_health_integration,
)


@pytest.mark.unit
@pytest.mark.core
def test_get_connect_readiness_when_disabled(monkeypatch):
    monkeypatch.setattr(
        "integrations.google_health.user_settings.is_google_health_enabled",
        lambda: False,
    )
    ready, message = get_connect_readiness()
    assert ready is False
    assert "not enabled" in message


@pytest.mark.unit
@pytest.mark.core
def test_format_status_text_includes_connection_state():
    status = HealthIntegrationStatus(
        feature_state="enabled",
        connected=False,
        last_success_at="never",
        has_recent_error=False,
    )
    text = format_status_text(status)
    assert "enabled" in text
    assert "no" in text
    assert "Connect Google Health" in text


@pytest.mark.unit
@pytest.mark.user
def test_pause_health_integration_updates_account(test_data_dir):
    from core import get_user_data, update_user_account
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = "health-user-settings-pause"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    update_user_account(user_id, {"features": {"google_health": "enabled"}})

    assert pause_health_integration(user_id) is True
    account = get_user_data(user_id, "account").get("account") or {}
    assert account.get("features", {}).get("google_health") == "paused"


@pytest.mark.unit
@pytest.mark.user
def test_get_health_integration_status(test_data_dir):
    from core import update_user_account
    from integrations.google_health.data_handlers import ensure_health_directory, save_auth
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = "health-user-settings-status"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    update_user_account(user_id, {"features": {"google_health": "enabled"}})
    ensure_health_directory(user_id)
    save_auth(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-28 12:00:00",
            "access_token": "token",
            "refresh_token": "refresh",
        },
    )

    status = get_health_integration_status(user_id)
    assert status is not None
    assert status.feature_state == "enabled"
    assert status.connected is True
