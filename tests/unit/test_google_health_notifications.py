"""Unit tests for Google Health reconnect notifications."""

from unittest.mock import MagicMock, patch

import pytest

from integrations.google_health.notifications import (
    RECONNECT_NOTICE_TEXT,
    is_auth_sync_failure,
    maybe_send_reconnect_notice,
    send_reconnect_notice,
)


@pytest.mark.unit
@pytest.mark.core
def test_is_auth_sync_failure_detects_token_errors():
    assert is_auth_sync_failure("Unable to obtain valid access token")
    assert is_auth_sync_failure("No refresh token for user — reconnect required")
    assert not is_auth_sync_failure("Google Health API error for sleep")
    assert not is_auth_sync_failure("")


@pytest.mark.unit
@pytest.mark.core
def test_maybe_send_reconnect_notice_skips_non_auth_errors():
    state = {"reconnect_notice_sent": False}
    with patch(
        "integrations.google_health.notifications.send_reconnect_notice"
    ) as send_mock:
        result = maybe_send_reconnect_notice(
            "user-1", state, "Google Health API error for steps"
        )
    send_mock.assert_not_called()
    assert result["reconnect_notice_sent"] is False


@pytest.mark.unit
@pytest.mark.core
def test_maybe_send_reconnect_notice_skips_when_already_sent():
    state = {"reconnect_notice_sent": True}
    with patch(
        "integrations.google_health.notifications.send_reconnect_notice"
    ) as send_mock:
        result = maybe_send_reconnect_notice(
            "user-1", state, "Unable to obtain valid access token"
        )
    send_mock.assert_not_called()
    assert result["reconnect_notice_sent"] is True


@pytest.mark.unit
@pytest.mark.core
def test_maybe_send_reconnect_notice_sends_once_for_auth_failure():
    state = {"reconnect_notice_sent": False}
    with patch(
        "integrations.google_health.notifications.send_reconnect_notice",
        return_value=True,
    ) as send_mock:
        result = maybe_send_reconnect_notice(
            "user-1", state, "Unable to obtain valid access token"
        )
    send_mock.assert_called_once_with("user-1")
    assert result["reconnect_notice_sent"] is True


@pytest.mark.unit
@pytest.mark.core
def test_send_reconnect_notice_uses_user_channel():
    preferences = {"channel": {"type": "discord"}, "categories": ["health"]}
    mock_cm = MagicMock()
    mock_cm.send_message_sync.return_value = True

    with patch.dict("os.environ", {"MHM_TESTING": "0"}, clear=False), patch(
        "integrations.google_health.notifications.get_user_data",
        return_value={"preferences": preferences},
    ), patch(
        "communication.core.channel_orchestrator.CommunicationManager",
        return_value=mock_cm,
    ):
        assert send_reconnect_notice("user-1") is True

    mock_cm.send_message_sync.assert_called_once()
    args, kwargs = mock_cm.send_message_sync.call_args
    assert args[0] == "discord"
    assert args[2] == RECONNECT_NOTICE_TEXT
    assert kwargs.get("category") == "health"
    assert kwargs.get("user_id") == "user-1"


@pytest.mark.unit
@pytest.mark.user
def test_sync_sends_reconnect_notice_on_auth_pause(test_data_dir, monkeypatch):
    from core import get_user_data, update_user_account
    from integrations.google_health.data_handlers import ensure_health_directory, save_auth
    from integrations.google_health.sync_manager import sync_user_health_data
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = "health-notice-user-sync"
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
            "expires_at": "2000-01-01 00:00:00",
        },
    )
    with patch.dict("os.environ", {"MHM_TESTING": "0"}, clear=False), patch(
        "integrations.google_health.sync_manager.GOOGLE_HEALTH_ENABLED", True
    ), patch(
        "integrations.google_health.sync_manager._google_health_feature_enabled",
        return_value=True,
    ), patch(
        "integrations.google_health.sync_manager.has_valid_auth",
        return_value=True,
    ), patch(
        "integrations.google_health.sync_manager.GOOGLE_HEALTH_SYNC_FAILURE_PAUSE_THRESHOLD",
        1,
    ), patch(
        "integrations.google_health.sync_manager.ensure_valid_access_token",
        return_value=None,
    ), patch(
        "integrations.google_health.notifications.send_reconnect_notice",
        return_value=True,
    ) as send_mock:
        assert sync_user_health_data(user_id, force=True) is False

    send_mock.assert_called_once_with(user_id)

    from integrations.google_health.data_handlers import load_sync_state

    state = load_sync_state(user_id) or {}
    assert state.get("reconnect_notice_sent") is True

    account = get_user_data(user_id, "account").get("account", {})
    assert account.get("features", {}).get("google_health") == "paused"
