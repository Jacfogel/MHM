"""Unit tests for Google Health reconnect notifications."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from integrations.google_health.auth import DEAD_REFRESH_TOKEN_ERROR
from integrations.google_health.notifications import (
    RECONNECT_NOTICE_TEXT,
    is_auth_sync_failure,
    maybe_send_reconnect_notice,
    send_reconnect_notice,
)

pytestmark = [pytest.mark.integrations]


@pytest.mark.unit
@pytest.mark.core
def test_is_auth_sync_failure_detects_token_errors():
    assert is_auth_sync_failure("Unable to obtain valid access token")
    assert is_auth_sync_failure("No refresh token for user — reconnect required")
    assert is_auth_sync_failure(DEAD_REFRESH_TOKEN_ERROR)
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
    from integrations.google_health.data_handlers import (
        ensure_health_directory,
        save_auth,
        save_sync_state,
    )
    from integrations.google_health.sync_manager import sync_user_health_data
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    # Unique per run: leftover xdist user dirs keep paused feature / reconnect_notice_sent.
    user_id = f"health-notice-user-sync-{uuid.uuid4().hex[:10]}"
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
    save_sync_state(
        user_id,
        {
            "schema_version": 2,
            "consecutive_failures": 0,
            "reconnect_notice_sent": False,
            "last_error": "",
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


@pytest.mark.unit
@pytest.mark.user
@pytest.mark.integrations
def test_sync_pauses_once_on_refresh_http_400(test_data_dir):
    from core import get_user_data, update_user_account
    from integrations.google_health.data_handlers import (
        ensure_health_directory,
        load_sync_state,
        save_auth,
        save_sync_state,
    )
    from integrations.google_health.sync_manager import sync_user_health_data
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = f"health-notice-user-400-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    update_user_account(user_id, {"features": {"google_health": "enabled"}})
    ensure_health_directory(user_id)
    save_auth(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-27 12:00:00",
            "access_token": "expired",
            "refresh_token": "dead-refresh",
            "expires_at": "2000-01-01 00:00:00",
        },
    )
    save_sync_state(
        user_id,
        {
            "schema_version": 2,
            "consecutive_failures": 0,
            "reconnect_notice_sent": False,
            "last_error": "",
        },
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = (
        '{"error":"invalid_grant","error_description":"Token has been expired or revoked."}'
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
        2,
    ), patch(
        "integrations.google_health.auth.requests.post",
        return_value=mock_resp,
    ), patch(
        "integrations.google_health.notifications.send_reconnect_notice",
        return_value=True,
    ) as send_mock:
        assert sync_user_health_data(user_id, force=True) is False
        send_mock.assert_not_called()
        first_state = load_sync_state(user_id) or {}
        assert first_state.get("consecutive_failures") == 1
        assert DEAD_REFRESH_TOKEN_ERROR in (first_state.get("last_error") or "")

        assert sync_user_health_data(user_id, force=True) is False
        send_mock.assert_called_once_with(user_id)

    state = load_sync_state(user_id) or {}
    assert state.get("reconnect_notice_sent") is True
    assert state.get("consecutive_failures") == 2

    account = get_user_data(user_id, "account").get("account", {})
    assert account.get("features", {}).get("google_health") == "paused"


@pytest.mark.unit
@pytest.mark.core
def test_send_reconnect_notice_skips_in_testing_mode(monkeypatch):
    monkeypatch.setenv("MHM_TESTING", "1")
    assert send_reconnect_notice("user-1") is False


@pytest.mark.unit
@pytest.mark.core
def test_send_reconnect_notice_requires_preferences(monkeypatch):
    monkeypatch.setenv("MHM_TESTING", "0")
    with patch(
        "integrations.google_health.notifications.get_user_data",
        return_value={"preferences": None},
    ):
        assert send_reconnect_notice("user-1") is False


@pytest.mark.unit
@pytest.mark.core
def test_send_reconnect_notice_requires_channel(monkeypatch):
    monkeypatch.setenv("MHM_TESTING", "0")
    with patch(
        "integrations.google_health.notifications.get_user_data",
        return_value={"preferences": {"channel": {}}},
    ):
        assert send_reconnect_notice("user-1") is False


@pytest.mark.unit
@pytest.mark.core
def test_send_reconnect_notice_requires_recipient(monkeypatch):
    monkeypatch.setenv("MHM_TESTING", "0")
    mock_resolver = MagicMock()
    mock_resolver.get_recipient_for_service.return_value = None
    with patch(
        "integrations.google_health.notifications.get_user_data",
        return_value={"preferences": {"channel": {"type": "discord"}}},
    ), patch(
        "communication.delivery.recipient_resolver.RecipientResolver",
        return_value=mock_resolver,
    ), patch(
        "communication.core.channel_orchestrator.CommunicationManager",
    ):
        assert send_reconnect_notice("user-1") is False


@pytest.mark.unit
@pytest.mark.core
def test_send_reconnect_notice_returns_false_when_send_fails(monkeypatch):
    monkeypatch.setenv("MHM_TESTING", "0")
    mock_cm = MagicMock()
    mock_cm.send_message_sync.return_value = False
    mock_resolver = MagicMock()
    mock_resolver.get_recipient_for_service.return_value = "channel-1"
    with patch(
        "integrations.google_health.notifications.get_user_data",
        return_value={"preferences": {"channel": {"type": "discord"}}},
    ), patch(
        "communication.delivery.recipient_resolver.RecipientResolver",
        return_value=mock_resolver,
    ), patch(
        "communication.core.channel_orchestrator.CommunicationManager",
        return_value=mock_cm,
    ):
        assert send_reconnect_notice("user-1") is False


@pytest.mark.unit
@pytest.mark.core
def test_maybe_send_reconnect_notice_leaves_flag_unset_when_send_fails():
    state = {"reconnect_notice_sent": False}
    with patch(
        "integrations.google_health.notifications.send_reconnect_notice",
        return_value=False,
    ):
        result = maybe_send_reconnect_notice(
            "user-1", state, "Unable to obtain valid access token"
        )
    assert result.get("reconnect_notice_sent") is False
