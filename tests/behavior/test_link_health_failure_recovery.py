"""Unconfirmed health settings and failed account verification stay truthful."""

from unittest.mock import Mock

import pytest

from communication.command_handlers import account_handler, health_handler
from communication.command_handlers.account_handler import _generate_confirmation_code as generate_code

pytestmark = [pytest.mark.behavior, pytest.mark.communication]


@pytest.fixture
def link_context(monkeypatch):
    monkeypatch.setattr(account_handler, "_pending_link_operations", {})
    monkeypatch.setattr(account_handler, "get_user_id_by_identifier", lambda _: "account-1")
    monkeypatch.setattr(account_handler, "get_user_data", lambda *_: {"account": {}, "context": {}})
    monkeypatch.setattr(account_handler, "user_display_label", lambda *_: "Account")
    update = Mock(return_value=True)
    send = Mock(return_value=True)
    monkeypatch.setattr(account_handler, "update_user_account", update)
    monkeypatch.setattr(account_handler, "_send_confirmation_code", send)
    monkeypatch.setattr(account_handler, "_generate_confirmation_code", lambda: "123456")
    return update, send


def test_code_delivery_failure_leaves_no_verifiable_challenge(link_context):
    _, send = link_context
    send.return_value = False
    account_handler._pending_link_operations["channel-1"] = {"confirmation_code": "old-code"}
    response = account_handler.AccountManagementHandler()._handle_link_account(
        "channel-1", {"account_identifier": "account-1"}
    )
    assert "linking has not started" in response.message
    assert "email" in response.message
    assert "channel-1" not in account_handler._pending_link_operations


def test_code_generation_failure_sends_nothing_and_creates_no_challenge(monkeypatch, link_context):
    _, send = link_context
    # Exercise the real decorated generator with an unavailable random source.
    monkeypatch.setattr(account_handler.secrets, "choice", Mock(side_effect=RuntimeError("PRIVATE ERROR")))
    assert generate_code() is None
    monkeypatch.setattr(account_handler, "_generate_confirmation_code", generate_code)
    response = account_handler.AccountManagementHandler()._handle_link_account(
        "channel-1", {"account_identifier": "account-1"}
    )
    assert "couldn't start account verification" in response.message
    assert "PRIVATE" not in response.message
    assert not account_handler._pending_link_operations
    send.assert_not_called()


@pytest.mark.parametrize("mismatch", ["user_id", "channel_type"])
def test_verification_is_bound_to_requested_account_and_channel(link_context, mismatch):
    update, _ = link_context
    pending = {"operation_type": "link", "user_id": "account-1", "channel_type": "discord",
               "confirmation_code": "123456"}
    pending[mismatch] = "another-account" if mismatch == "user_id" else "email"
    account_handler._pending_link_operations["channel-1"] = pending
    response = account_handler.AccountManagementHandler()._handle_link_account(
        "channel-1", {"account_identifier": "account-1", "confirmation_code": "123456"}
    )
    assert "different account or channel" in response.message
    update.assert_not_called()


def test_wrong_code_directs_user_to_verification_email(link_context):
    account_handler._pending_link_operations["channel-1"] = {
        "operation_type": "link", "user_id": "account-1", "channel_type": "discord",
        "confirmation_code": "123456",
    }
    response = account_handler.AccountManagementHandler()._handle_link_account(
        "channel-1", {"account_identifier": "account-1", "confirmation_code": "999999"}
    )
    assert "latest verification email" in response.message
    assert "check your discord" not in response.message.lower()
    link_context[0].assert_not_called()


def test_unsupported_link_channel_never_sends_or_writes(link_context):
    response = account_handler.AccountManagementHandler()._handle_link_account(
        "channel-1", {"account_identifier": "account-1", "channel_type": "unsupported"}
    )
    assert "Discord and email" in response.message
    link_context[0].assert_not_called()
    link_context[1].assert_not_called()
    assert not account_handler._pending_link_operations


def test_link_write_failure_suggests_checking_status(link_context):
    update, _ = link_context
    update.return_value = False
    account_handler._pending_link_operations["channel-1"] = {
        "operation_type": "link", "user_id": "account-1", "channel_type": "discord",
        "confirmation_code": "123456",
    }
    response = account_handler.AccountManagementHandler()._handle_link_account(
        "channel-1", {"account_identifier": "account-1", "confirmation_code": "123456"}
    )
    assert "couldn't confirm" in response.message
    assert "check account status" in response.message
    assert "linked successfully" not in response.message


@pytest.mark.parametrize("method,operation", [
    ("_handle_pause", "pause_health_integration"),
    ("_handle_delete", "delete_health_integration"),
])
@pytest.mark.parametrize("raises", [False, True])
def test_health_write_failure_does_not_claim_success(monkeypatch, method, operation, raises):
    persist = Mock(return_value=False)
    if raises:
        persist.side_effect = RuntimeError("PRIVATE ERROR")
    monkeypatch.setattr(health_handler, operation, persist)
    response = getattr(health_handler.HealthHandler(), method)("health-user")
    persist.assert_called_once_with("health-user")
    assert "couldn't confirm" in response.message
    assert "health status" in response.message
    assert "PRIVATE" not in response.message
