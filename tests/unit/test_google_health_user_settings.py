"""Unit tests for shared Google Health user settings operations."""

import threading
import uuid
from unittest.mock import patch

import pytest

from integrations.google_health.user_settings import (
    HealthIntegrationStatus,
    delete_health_integration,
    enable_health_integration,
    format_status_text,
    get_connect_authorization_url,
    get_connect_readiness,
    get_health_integration_status,
    pause_health_integration,
    run_connect_flow,
    run_connect_flow_async,
    sync_health_integration,
)

pytestmark = [pytest.mark.integrations]


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
def test_get_connect_readiness_when_credentials_missing(monkeypatch):
    monkeypatch.setattr(
        "integrations.google_health.user_settings.is_google_health_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "integrations.google_health.user_settings.GOOGLE_HEALTH_CLIENT_ID", ""
    )
    monkeypatch.setattr(
        "integrations.google_health.user_settings.GOOGLE_HEALTH_CLIENT_SECRET", ""
    )
    ready, message = get_connect_readiness()
    assert ready is False
    assert "GOOGLE_HEALTH_CLIENT_ID" in message


@pytest.mark.unit
@pytest.mark.core
def test_get_connect_readiness_when_auth_url_cannot_be_built(monkeypatch):
    monkeypatch.setattr(
        "integrations.google_health.user_settings.is_google_health_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "integrations.google_health.user_settings.GOOGLE_HEALTH_CLIENT_ID", "cid"
    )
    monkeypatch.setattr(
        "integrations.google_health.user_settings.GOOGLE_HEALTH_CLIENT_SECRET",
        "secret",
    )
    monkeypatch.setattr(
        "integrations.google_health.user_settings.build_authorization_url",
        lambda state="": "",
    )
    ready, message = get_connect_readiness()
    assert ready is False
    assert "authorization URL" in message


@pytest.mark.unit
@pytest.mark.core
def test_get_connect_readiness_when_configured(monkeypatch):
    monkeypatch.setattr(
        "integrations.google_health.user_settings.is_google_health_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "integrations.google_health.user_settings.GOOGLE_HEALTH_CLIENT_ID", "cid"
    )
    monkeypatch.setattr(
        "integrations.google_health.user_settings.GOOGLE_HEALTH_CLIENT_SECRET",
        "secret",
    )
    monkeypatch.setattr(
        "integrations.google_health.user_settings.build_authorization_url",
        lambda state="": "https://auth.example/connect",
    )
    ready, message = get_connect_readiness()
    assert ready is True
    assert message == ""


@pytest.mark.unit
@pytest.mark.core
def test_get_connect_authorization_url_passes_user_state(monkeypatch):
    monkeypatch.setattr(
        "integrations.google_health.user_settings.build_authorization_url",
        lambda state="": f"https://auth.example/?state={state}",
    )
    url = get_connect_authorization_url("user-42")
    assert "state=user-42" in url


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
@pytest.mark.core
def test_format_status_text_notes_pending_first_sync_and_recent_error():
    pending = HealthIntegrationStatus(
        feature_state="enabled",
        connected=True,
        last_success_at="never",
        has_recent_error=False,
    )
    pending_text = format_status_text(pending)
    assert "first pull may happen shortly" in pending_text

    errored = HealthIntegrationStatus(
        feature_state="enabled",
        connected=True,
        last_success_at="2026-08-31 12:00:00",
        has_recent_error=True,
    )
    error_text = format_status_text(errored)
    assert "recent sync had an issue" in error_text


@pytest.mark.unit
@pytest.mark.core
def test_get_health_integration_status_rejects_empty_user_id():
    assert get_health_integration_status("") is None


@pytest.mark.unit
@pytest.mark.user
def test_pause_health_integration_updates_account(test_data_dir):
    from core import get_user_data, update_user_account
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = f"health-user-settings-pause-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    update_user_account(user_id, {"features": {"google_health": "enabled"}})

    assert pause_health_integration(user_id) is True
    account = get_user_data(user_id, "account").get("account") or {}
    assert account.get("features", {}).get("google_health") == "paused"


@pytest.mark.unit
@pytest.mark.user
def test_get_health_integration_status(test_data_dir):
    from core import update_user_account
    from integrations.google_health.data_handlers import (
        ensure_health_directory,
        save_auth,
        save_sync_state,
    )
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = f"health-user-settings-status-{uuid.uuid4().hex[:10]}"
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
    save_sync_state(
        user_id,
        {
            "schema_version": 2,
            "last_success_at": "2026-08-30 08:00:00",
            "last_error": "token refresh failed",
        },
    )

    status = get_health_integration_status(user_id)
    assert status is not None
    assert status.feature_state == "enabled"
    assert status.connected is True
    assert status.last_success_at == "2026-08-30 08:00:00"
    assert status.has_recent_error is True


@pytest.mark.unit
@pytest.mark.user
def test_run_connect_flow_enables_feature_after_oauth_and_sync(test_data_dir):
    from core import get_user_data
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = f"health-connect-flow-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    with patch(
        "integrations.google_health.user_settings.run_oauth_connect_flow"
    ) as oauth, patch(
        "integrations.google_health.user_settings.sync_user_health_data",
        return_value=True,
    ) as sync:
        ok, error = run_connect_flow(user_id)
    assert ok is True
    assert error == ""
    oauth.assert_called_once_with(user_id)
    sync.assert_called_once_with(user_id, force=True)
    account = get_user_data(user_id, "account").get("account") or {}
    assert account.get("features", {}).get("google_health") == "enabled"


@pytest.mark.unit
@pytest.mark.user
def test_run_connect_flow_returns_error_when_oauth_raises(test_data_dir):
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = f"health-connect-fail-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    with patch(
        "integrations.google_health.user_settings.run_oauth_connect_flow",
        side_effect=RuntimeError("oauth exploded"),
    ):
        ok, error = run_connect_flow(user_id)
    assert ok is False
    assert "oauth exploded" in error


@pytest.mark.unit
@pytest.mark.core
def test_run_connect_flow_async_invokes_callback():
    finished: list[tuple[bool, str]] = []
    done = threading.Event()

    def _on_finished(success: bool, error: str) -> None:
        finished.append((success, error))
        done.set()

    with patch(
        "integrations.google_health.user_settings.run_connect_flow",
        return_value=(True, ""),
    ) as connect:
        run_connect_flow_async("user-async", _on_finished)
        assert done.wait(timeout=5)
    connect.assert_called_once_with("user-async")
    assert finished == [(True, "")]


@pytest.mark.unit
@pytest.mark.user
def test_enable_health_integration_requires_existing_auth(test_data_dir):
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = f"health-enable-no-auth-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    ok, error = enable_health_integration(user_id)
    assert ok is False
    assert "Connect Google Health first" in error


@pytest.mark.unit
@pytest.mark.user
def test_enable_health_integration_enables_and_syncs(test_data_dir):
    from core import get_user_data
    from integrations.google_health.data_handlers import ensure_health_directory, save_auth
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = f"health-enable-ok-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
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
    with patch(
        "integrations.google_health.user_settings.sync_user_health_data",
        return_value=True,
    ) as sync:
        ok, error = enable_health_integration(user_id)
    assert ok is True
    assert error == ""
    sync.assert_called_once_with(user_id, force=True)
    account = get_user_data(user_id, "account").get("account") or {}
    assert account.get("features", {}).get("google_health") == "enabled"


@pytest.mark.unit
@pytest.mark.user
def test_enable_health_integration_reports_account_update_failure(test_data_dir):
    from integrations.google_health.data_handlers import ensure_health_directory, save_auth
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = f"health-enable-fail-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
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
    with patch(
        "integrations.google_health.user_settings.update_user_account",
        return_value=False,
    ):
        ok, error = enable_health_integration(user_id)
    assert ok is False
    assert "Could not update account features" in error


@pytest.mark.unit
@pytest.mark.user
def test_delete_health_integration_disables_feature_and_removes_data(test_data_dir):
    from core import get_user_data, update_user_account
    from integrations.google_health.data_handlers import (
        ensure_health_directory,
        has_valid_auth,
        save_auth,
    )
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = f"health-delete-{uuid.uuid4().hex[:10]}"
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
    assert delete_health_integration(user_id) is True
    assert has_valid_auth(user_id) is False
    account = get_user_data(user_id, "account").get("account") or {}
    assert account.get("features", {}).get("google_health") == "disabled"


@pytest.mark.unit
@pytest.mark.user
def test_sync_health_integration_forces_sync(test_data_dir):
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = f"health-sync-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    with patch(
        "integrations.google_health.user_settings.sync_user_health_data",
        return_value=True,
    ) as sync:
        assert sync_health_integration(user_id) is True
    sync.assert_called_once_with(user_id, force=True)
