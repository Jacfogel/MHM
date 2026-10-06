"""Risk-focused tests for inbound Discord message routing."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

import communication.communication_channels.discord.events.message_handler as handler


pytestmark = [pytest.mark.unit, pytest.mark.communication, pytest.mark.asyncio]


class _DirectMessageChannel:
    def __init__(self):
        self.id = "dm-1"
        self.send = AsyncMock()


def _message(*, content="hello", author_id=123):
    author = SimpleNamespace(id=author_id, send=AsyncMock())
    return SimpleNamespace(
        author=author,
        content=content,
        channel=_DirectMessageChannel(),
        guild=None,
    )


async def test_message_from_the_bot_is_ignored(monkeypatch):
    message = _message()
    bot = SimpleNamespace(bot=SimpleNamespace(user=message.author))
    lookup = MagicMock()
    monkeypatch.setattr(handler, "get_user_id_by_identifier", lookup)

    await handler.handle_discord_message(bot, message)

    lookup.assert_not_called()


async def test_new_unrecognized_dm_sends_welcome_and_marks_user(monkeypatch):
    from communication.communication_channels.discord.onboarding import welcome_handler

    message = _message(author_id=456)
    monkeypatch.setattr(handler.discord, "DMChannel", _DirectMessageChannel)
    monkeypatch.setattr(welcome_handler, "has_been_welcomed", lambda _uid: False)
    monkeypatch.setattr(
        welcome_handler, "get_welcome_message", lambda *_args, **_kwargs: "Welcome"
    )
    marked = []
    monkeypatch.setattr(welcome_handler, "mark_as_welcomed", marked.append)

    await handler._handle_unrecognized_user_message(message, "456")

    message.author.send.assert_awaited_once_with("Welcome")
    message.channel.send.assert_not_awaited()
    assert marked == ["456"]


async def test_blocked_welcome_dm_falls_back_to_channel(monkeypatch):
    from communication.communication_channels.discord.onboarding import welcome_handler

    message = _message(author_id=789)
    forbidden = discord.Forbidden(
        MagicMock(status=403, reason="Forbidden"), "DMs disabled"
    )
    message.author.send.side_effect = forbidden
    monkeypatch.setattr(handler.discord, "DMChannel", _DirectMessageChannel)
    monkeypatch.setattr(welcome_handler, "has_been_welcomed", lambda _uid: False)
    monkeypatch.setattr(
        welcome_handler, "get_welcome_message", lambda *_args, **_kwargs: "Welcome"
    )
    marked = []
    monkeypatch.setattr(welcome_handler, "mark_as_welcomed", marked.append)

    await handler._handle_unrecognized_user_message(message, "789")

    message.channel.send.assert_awaited_once()
    assert "Discord ID" in message.channel.send.await_args.args[0]
    assert marked == ["789"]


async def test_identified_message_syncs_changed_discord_id_and_sends_response(
    monkeypatch,
):
    import core
    from communication.message_processing import interaction_manager

    message = _message(content="What should I do?", author_id=987)
    bot = SimpleNamespace(
        bot=SimpleNamespace(user=object()),
        _send_to_channel=AsyncMock(return_value=True),
    )
    monkeypatch.setattr(handler, "get_user_id_by_identifier", lambda _uid: "user-1")
    monkeypatch.setattr(
        core,
        "get_user_data",
        lambda *_args: {"account": {"discord_user_id": "old-id"}},
    )
    saved = []
    monkeypatch.setattr(core, "save_user_data", lambda *args: saved.append(args) or True)
    monkeypatch.setattr(
        interaction_manager,
        "handle_user_message",
        lambda *_args: SimpleNamespace(
            message="A helpful answer",
            rich_data={"kind": "text"},
            suggestions=["Try this"],
        ),
    )

    await handler.handle_discord_message(bot, message)

    assert saved == [
        (
            "user-1",
            "account",
            {"discord_user_id": "987"},
        )
    ]
    bot._send_to_channel.assert_awaited_once_with(
        message.channel,
        "A helpful answer",
        {"kind": "text"},
        ["Try this"],
    )


async def test_identified_message_with_empty_response_does_not_send(monkeypatch):
    from communication.message_processing import interaction_manager

    message = _message()
    bot = SimpleNamespace(_send_to_channel=AsyncMock())
    monkeypatch.setattr(
        interaction_manager,
        "handle_user_message",
        lambda *_args: SimpleNamespace(message="", rich_data={}, suggestions=[]),
    )

    await handler._process_identified_user_message(bot, message, "user-1", "123")

    bot._send_to_channel.assert_not_awaited()
