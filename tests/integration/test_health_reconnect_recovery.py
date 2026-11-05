"""Persisted reconnect warnings recover independently of paused health sync."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from core import update_user_account
from communication.communication_channels.website.inbox import list_website_messages
from integrations.google_health.data_handlers import load_sync_state, save_sync_state
from integrations.google_health.notifications import RECONNECT_NOTICE_TEXT
from integrations.google_health.sync_manager import sync_users_due_for_schedule
from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

pytestmark = [pytest.mark.integration, pytest.mark.integrations]


@pytest.fixture
def paused_health_user(test_data_dir):
    label = f"notice-recovery-{uuid.uuid4().hex[:10]}"
    assert TestUserFactory.create_basic_user(label, test_data_dir=test_data_dir)
    user_id = TestUserFactory.get_test_user_id_by_label(label, test_data_dir)
    assert user_id
    update_user_account(user_id, {"features": {"google_health": "paused"}})
    save_sync_state(
        user_id,
        {
            "schema_version": 2,
            "consecutive_failures": 5,
            "last_error": "Google Health refresh token is invalid or revoked; reconnect required",
            "reconnect_notice_sent": False,
        },
    )
    return user_id


@pytest.fixture
def recovery_poll(paused_health_user):
    manager = MagicMock()
    resolver = MagicMock()
    resolver.get_recipient_for_service.return_value = "discord_user:test"
    with (
        patch("integrations.google_health.sync_manager.GOOGLE_HEALTH_ENABLED", True),
        patch(
            "integrations.google_health.sync_manager.is_google_health_testing_mode",
            return_value=False,
        ),
        patch(
            "integrations.google_health.notifications.is_google_health_testing_mode",
            return_value=False,
        ),
        patch(
            "integrations.google_health.sync_manager.get_all_user_ids",
            return_value=[paused_health_user],
        ),
        patch(
            "integrations.google_health.notifications.get_user_data",
            return_value={"preferences": {"channel": {"type": "discord"}}},
        ),
        patch(
            "communication.core.channel_orchestrator.CommunicationManager",
            return_value=manager,
        ),
        patch(
            "communication.delivery.recipient_resolver.RecipientResolver",
            return_value=resolver,
        ),
        patch("integrations.google_health.sync_manager.sync_user_health_data") as sync,
    ):
        yield manager, sync


def test_failed_notice_recovers_from_disk_without_resuming_sync(
    paused_health_user, recovery_poll
):
    manager, sync = recovery_poll
    manager.send_message_sync.side_effect = [False, True]
    assert sync_users_due_for_schedule() == 0
    state = load_sync_state(paused_health_user)
    assert not state["reconnect_notice_sent"]
    assert state["reconnect_notice_website_sent"]
    assert [m["text"] for m in list_website_messages(paused_health_user)] == [
        RECONNECT_NOTICE_TEXT
    ]

    # Each poll reloads disk state, just as a new process does after restart.
    assert sync_users_due_for_schedule() == 0
    assert load_sync_state(paused_health_user)["reconnect_notice_sent"]
    assert sync_users_due_for_schedule() == 0
    assert manager.send_message_sync.call_count == 2
    assert manager.send_message_sync.call_args.kwargs["_queue_on_failure"] is False
    assert len(list_website_messages(paused_health_user)) == 1
    sync.assert_not_called()


def test_website_failure_retries_without_repeating_primary(
    paused_health_user, recovery_poll
):
    manager, sync = recovery_poll
    manager.send_message_sync.return_value = True
    with patch(
        "communication.communication_channels.website.inbox.deliver_to_website",
        side_effect=[False, True],
    ) as website:
        sync_users_due_for_schedule()
        assert load_sync_state(paused_health_user)["reconnect_notice_sent"]
        assert not load_sync_state(paused_health_user).get(
            "reconnect_notice_website_sent"
        )
        sync_users_due_for_schedule()
        sync_users_due_for_schedule()
    manager.send_message_sync.assert_called_once()
    assert website.call_count == 2
    assert load_sync_state(paused_health_user)["reconnect_notice_website_sent"]
    sync.assert_not_called()


@pytest.mark.parametrize(
    "feature,error",
    [("disabled", "refresh token invalid"), ("paused", "Network unavailable")],
)
def test_unrelated_pauses_and_disabled_accounts_get_no_warning(
    paused_health_user, recovery_poll, feature, error
):
    manager, sync = recovery_poll
    update_user_account(paused_health_user, {"features": {"google_health": feature}})
    state = load_sync_state(paused_health_user)
    state["last_error"] = error
    save_sync_state(paused_health_user, state)
    sync_users_due_for_schedule()
    manager.send_message_sync.assert_not_called()
    assert list_website_messages(paused_health_user) == []
    sync.assert_not_called()


def test_website_primary_gets_one_copy(paused_health_user, recovery_poll):
    manager, sync = recovery_poll
    with patch(
        "integrations.google_health.notifications.get_user_data",
        return_value={"preferences": {"channel": {"type": "website"}}},
    ):
        sync_users_due_for_schedule()
        sync_users_due_for_schedule()
    state = load_sync_state(paused_health_user)
    assert state["reconnect_notice_sent"]
    assert state["reconnect_notice_website_sent"]
    assert len(list_website_messages(paused_health_user)) == 1
    manager.send_message_sync.assert_not_called()
    sync.assert_not_called()
