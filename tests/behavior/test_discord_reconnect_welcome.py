"""Reconnect recognition uses retained account links, never welcome history."""

import uuid
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import AsyncMock
from concurrent.futures import Future
from types import SimpleNamespace

import pytest

from communication.core.welcome_manager import (
    get_returning_discord_user_id,
    get_welcome_message,
    mark_as_welcomed,
)
from communication.communication_channels.discord.onboarding.welcome_handler import (
    get_welcome_message_view,
)
from storage.user_data_read import get_user_data
from tests.test_helpers.test_utilities import TestUserFactory


@pytest.mark.behavior
@pytest.mark.communication
@pytest.mark.parametrize("state", ["new", "returning", "unlinked", "deleted"])
def test_authorization_respects_retained_identity(test_data_dir, monkeypatch, state):
    import core

    # Only construct the view; no callbacks or Discord network event loop run.
    monkeypatch.setattr("discord.ui.view.asyncio.get_running_loop", lambda: Mock())
    discord_id = "123456789012345678"
    users_dir = Path(test_data_dir) / "users"
    user_id = None
    if state in {"returning", "unlinked"}:
        assert TestUserFactory.create_discord_user(discord_id, test_data_dir=test_data_dir)
        user_id = core.get_user_id_by_identifier(discord_id)
        assert user_id
        if state == "unlinked":
            assert core.update_user_account(user_id, {"discord_user_id": ""})
            # Even a stale lookup entry must not count as a current link.
            monkeypatch.setattr(core, "get_user_id_by_identifier", lambda _: user_id)
    elif state == "deleted":
        user_id = str(uuid.uuid4())
        monkeypatch.setattr(core, "get_user_id_by_identifier", lambda _: user_id)
        assert not (users_dir / user_id).exists()
    else:
        monkeypatch.setattr(core, "get_user_id_by_identifier", lambda _: None)

    # Having been welcomed in the past is insufficient evidence of an account.
    assert mark_as_welcomed(discord_id)
    before_dirs = set(users_dir.iterdir()) if users_dir.exists() else set()
    before = get_user_data(user_id, ["account", "preferences"], auto_create=False) if state in {"returning", "unlinked"} else {}
    message = get_welcome_message(discord_id, is_authorization=True)
    view = get_welcome_message_view(discord_id)
    if state == "returning":
        assert get_returning_discord_user_id(discord_id) == user_id
        assert "Welcome back" in message and "still linked" in message
        assert "create or link" not in message.lower()
        assert view is None
    else:
        assert get_returning_discord_user_id(discord_id) is None
        assert "create or link" in message.lower()
        assert view is not None
        assert {item.label for item in view.children} == {
            "Create a New Account", "Link to Existing Account"
        }
        view.stop()
    assert (set(users_dir.iterdir()) if users_dir.exists() else set()) == before_dirs
    if before:
        assert get_user_data(user_id, ["account", "preferences"], auto_create=False) == before


@pytest.mark.behavior
@pytest.mark.communication
def test_reconnect_copy_does_not_apply_to_email(test_data_dir, monkeypatch):
    monkeypatch.setattr("communication.core.welcome_manager.get_returning_discord_user_id",
                        lambda _: pytest.fail("Email must not use Discord identity lookup"))
    assert "create or link" in get_welcome_message(
        "fixture@example.test", channel_type="email", is_authorization=True
    ).lower()


@pytest.mark.behavior
@pytest.mark.communication
def test_webhook_sends_reconnect_once_without_setup_buttons(test_data_dir, monkeypatch):
    from communication.core.welcome_manager import clear_welcomed_status
    from communication.communication_channels.discord.webhooks.handler import handle_application_authorized
    import core

    discord_id = "223456789012345678"
    assert TestUserFactory.create_discord_user(discord_id, test_data_dir=test_data_dir)
    user_id = core.get_user_id_by_identifier(discord_id)
    before = get_user_data(user_id, "preferences", auto_create=False)
    clear_welcomed_status(discord_id)
    user = SimpleNamespace(send=AsyncMock())
    loop = Mock()
    loop.is_closed.return_value = False
    bot = SimpleNamespace(bot=SimpleNamespace(loop=loop, fetch_user=AsyncMock(return_value=user)))

    def run_without_network_loop(coroutine, _loop):
        """All awaits are mocks; drive the coroutine to completion synchronously."""
        future = Future()
        try:
            coroutine.send(None)
        except StopIteration as done:
            future.set_result(done.value)
        else:
            coroutine.close()
            pytest.fail("Unexpected real asynchronous operation in mocked delivery")
        return future

    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    monkeypatch.setattr("asyncio.run_coroutine_threadsafe", run_without_network_loop)
    event = {"event": {"type": "APPLICATION_AUTHORIZED", "data": {
        "user": {"id": discord_id, "username": "fixture"}
    }}}
    assert handle_application_authorized(event, bot)
    assert handle_application_authorized(event, bot)
    user.send.assert_awaited_once()
    assert "Welcome back" in user.send.await_args.args[0]
    assert user.send.await_args.kwargs["view"] is None
    assert get_user_data(user_id, "preferences", auto_create=False) == before
