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


class _GuildMessageChannel:
    def __init__(self):
        self.id = "guild-channel-1"
        self.send = AsyncMock()


def _message(*, content="hello", author_id=123, channel=None, guild=None):
    author = SimpleNamespace(id=author_id, send=AsyncMock())
    return SimpleNamespace(
        author=author,
        content=content,
        channel=channel or _DirectMessageChannel(),
        guild=guild,
    )


async def test_message_from_the_bot_is_ignored(monkeypatch):
    message = _message()
    bot = SimpleNamespace(bot=SimpleNamespace(user=message.author))
    lookup = MagicMock()
    monkeypatch.setattr(handler, "get_user_id_by_identifier", lookup)

    await handler.handle_discord_message(bot, message)

    lookup.assert_not_called()


async def test_unknown_message_routes_to_onboarding(monkeypatch):
    message = _message(author_id=321)
    bot = SimpleNamespace(bot=SimpleNamespace(user=object()))
    onboarding = AsyncMock()
    monkeypatch.setattr(handler, "get_user_id_by_identifier", lambda _uid: None)
    monkeypatch.setattr(handler, "_handle_unrecognized_user_message", onboarding)

    await handler.handle_discord_message(bot, message)

    onboarding.assert_awaited_once_with(message, "321")


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


@pytest.mark.parametrize("dm_blocked", [False, True])
async def test_new_server_user_is_welcomed_even_when_dm_is_blocked(
    monkeypatch, dm_blocked
):
    from communication.communication_channels.discord.onboarding import welcome_handler

    channel = _GuildMessageChannel()
    message = _message(
        author_id=654,
        channel=channel,
        guild=SimpleNamespace(id="guild-1"),
    )
    if dm_blocked:
        message.author.send.side_effect = discord.Forbidden(
            MagicMock(status=403, reason="Forbidden"), "DMs disabled"
        )
    monkeypatch.setattr(handler.discord, "DMChannel", _DirectMessageChannel)
    monkeypatch.setattr(welcome_handler, "has_been_welcomed", lambda _uid: False)
    monkeypatch.setattr(
        welcome_handler, "get_welcome_message", lambda *_args, **_kwargs: "Welcome"
    )
    marked = []
    monkeypatch.setattr(welcome_handler, "mark_as_welcomed", marked.append)

    await handler._handle_unrecognized_user_message(message, "654")

    message.author.send.assert_awaited_once_with("Welcome")
    if dm_blocked:
        channel.send.assert_awaited_once_with("Welcome")
    else:
        channel.send.assert_not_awaited()
    assert marked == ["654"]


@pytest.mark.parametrize("dm_blocked", [False, True])
async def test_returning_unrecognized_dm_always_gets_linking_guidance(
    monkeypatch, dm_blocked
):
    from communication.communication_channels.discord.onboarding import welcome_handler

    message = _message(author_id=852)
    if dm_blocked:
        message.author.send.side_effect = discord.Forbidden(
            MagicMock(status=403, reason="Forbidden"), "DMs disabled"
        )
    monkeypatch.setattr(handler.discord, "DMChannel", _DirectMessageChannel)
    monkeypatch.setattr(welcome_handler, "has_been_welcomed", lambda _uid: True)

    await handler._handle_unrecognized_user_message(message, "852")

    message.author.send.assert_awaited_once()
    if dm_blocked:
        fallback = message.channel.send.await_args.args[0]
        assert "852" in fallback
        assert "link" in fallback
    else:
        message.channel.send.assert_not_awaited()


async def test_returning_unrecognized_server_user_gets_channel_guidance(monkeypatch):
    from communication.communication_channels.discord.onboarding import welcome_handler

    channel = _GuildMessageChannel()
    message = _message(
        author_id=951,
        channel=channel,
        guild=SimpleNamespace(id="guild-1"),
    )
    monkeypatch.setattr(handler.discord, "DMChannel", _DirectMessageChannel)
    monkeypatch.setattr(welcome_handler, "has_been_welcomed", lambda _uid: True)

    await handler._handle_unrecognized_user_message(message, "951")

    message.author.send.assert_not_awaited()
    send_call = channel.send.await_args
    assert send_call is not None
    guidance = send_call.args[0]
    assert "951" in guidance
    assert "link" in guidance


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
    monkeypatch.setattr(
        core, "save_user_data", lambda *args: saved.append(args) or True
    )
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


async def test_identified_message_send_failure_is_reported_without_message_content(
    monkeypatch,
):
    from communication.message_processing import interaction_manager

    message = _message(content="private inbound text")
    bot = SimpleNamespace(_send_to_channel=AsyncMock(return_value=False))
    monkeypatch.setattr(
        interaction_manager,
        "handle_user_message",
        lambda *_args: SimpleNamespace(
            message="private outbound text",
            rich_data={},
            suggestions=[],
        ),
    )
    logged_error = MagicMock()
    monkeypatch.setattr(handler.discord_logger, "error", logged_error)

    await handler._process_identified_user_message(bot, message, "user-1", "123")

    logged_error.assert_called_once_with(
        "Discord message send failed for user",
        user_id="user-1",
        discord_user_id="123",
    )
    assert "private inbound text" not in str(logged_error.call_args)
    assert "private outbound text" not in str(logged_error.call_args)
