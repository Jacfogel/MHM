"""Unit coverage for DiscordBot helper branches without network or Discord login."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from communication.command_handlers.shared_types import PaginationAction
from communication.communication_channels.base.base_channel import ChannelStatus
from communication.communication_channels.discord.bot import (
    DiscordBot,
    DiscordConnectionStatus,
)


pytestmark = [pytest.mark.unit, pytest.mark.communication]


@pytest.mark.unit
@pytest.mark.communication
def test_rich_data_payload_and_pagination_helpers():
    bot = DiscordBot()

    assert bot._has_display_rich_data(None) is False
    assert bot._has_display_rich_data({"suggestion_payloads": ["x"]}) is False
    assert bot._has_display_rich_data({"title": "Title"}) is True
    assert bot._get_suggestion_payloads({"suggestion_payloads": [{"intent": "next"}]}) == [
        {"intent": "next"}
    ]
    assert bot._get_suggestion_payloads({"suggestion_payloads": "bad"}) is None
    assert bot._get_pagination_actions({"pagination_actions": "bad"}) == []

    action = PaginationAction(
        domain="tasks",
        action="list_tasks",
        params={"status": "open"},
        offset=0,
        next_offset=5,
        limit=5,
        remaining_count=12,
    )
    label, payload = bot._pagination_action_button_data(action)
    assert label == "Show More (5 more)"
    assert payload == {
        "intent": "list_tasks",
        "entities": {"status": "open", "offset": 5, "limit": 5},
    }
    assert bot._pagination_action_button_data({"action": "", "remaining_count": 1}) is None
    assert (
        bot._pagination_action_button_data(
            {"action": "next", "params": "bad", "limit": 0, "remaining_count": 0}
        )
        is None
    )


@pytest.mark.unit
@pytest.mark.communication
def test_action_row_inputs_limit_buttons_and_store_payloads(monkeypatch: pytest.MonkeyPatch):
    bot = DiscordBot()
    labels, payloads = bot._get_action_row_inputs(
        ["A", "B", "C", "D", "E", "F"],
        {
            "suggestion_payloads": ["payload-a"],
            "pagination_actions": [
                {
                    "action": "show_more",
                    "params": {"kind": "tasks"},
                    "next_offset": 10,
                    "limit": 10,
                    "remaining_count": 20,
                }
            ],
        },
    )

    assert labels == ["A", "B", "C", "D", "E", "F", "Show More (10 more)"]
    assert payloads[:2] == ["payload-a", None]

    class _FakeView:
        def __init__(self):
            self.children = []

        def add_item(self, item):
            self.children.append(item)

    class _FakeButton:
        def __init__(self, *, style, label, custom_id):
            self.style = style
            self.label = label
            self.custom_id = custom_id

    import communication.communication_channels.discord.bot as bot_module

    monkeypatch.setattr(bot_module.discord.ui, "View", _FakeView)
    monkeypatch.setattr(bot_module.discord.ui, "Button", _FakeButton)

    view = bot._create_action_row(labels, payloads)
    assert view is not None
    assert len(view.children) == 7
    first_custom_id = view.children[0].custom_id
    assert bot._suggestion_button_payloads[first_custom_id] == "payload-a"
    assert bot._create_action_row([]) is None


@pytest.mark.unit
@pytest.mark.communication
def test_discord_button_style_for_flow_suggestions(monkeypatch):
    """Skip/undo flow buttons use secondary/danger; data suggestions stay primary."""
    import communication.communication_channels.discord.bot as bot_module

    bot = DiscordBot()
    danger = bot_module.discord.ButtonStyle.danger
    secondary = bot_module.discord.ButtonStyle.secondary
    primary = bot_module.discord.ButtonStyle.primary

    assert bot._discord_button_style_for_suggestion("Skip Question") == secondary
    assert bot._discord_button_style_for_suggestion("Skip All") == secondary
    assert bot._discord_button_style_for_suggestion("End List") == secondary
    assert bot._discord_button_style_for_suggestion("Undo Task Creation") == danger
    assert bot._discord_button_style_for_suggestion("High") == primary


@pytest.mark.unit
@pytest.mark.communication
def test_create_discord_embed_title_fields_footer_and_validation():
    bot = DiscordBot()

    assert bot._create_discord_embed("", {"title": "Bad"}) is None
    assert bot._create_discord_embed("Message", {}) is None

    embed = bot._create_discord_embed(
        "**Extracted** body text",
        {
            "type": "success",
            "fields": [{"name": "N", "value": "V", "inline": True}],
            "footer": "Footer text",
        },
    )

    assert embed is not None
    assert embed.title == "Extracted"
    assert embed.description == "body text"
    assert len(embed.fields) == 1
    assert embed.footer.text == "Footer text"


@pytest.mark.unit
@pytest.mark.communication
def test_connection_status_summary_and_send_capability():
    bot = DiscordBot()

    bot._shared__update_connection_status(
        DiscordConnectionStatus.DNS_FAILURE,
        {"dns_error": {"error_message": "no dns"}},
    )
    assert "DNS Failure: no dns" in bot.get_connection_status_summary()

    bot._shared__update_connection_status(
        DiscordConnectionStatus.NETWORK_FAILURE,
        {"network_error": {"error_message": "no route"}},
    )
    assert "Network Failure:" in bot.get_connection_status_summary()

    bot._shared__update_connection_status(DiscordConnectionStatus.GATEWAY_ERROR)
    assert "Gateway Error" in bot.get_connection_status_summary()

    mock_bot = MagicMock()
    mock_bot.is_ready.return_value = True
    mock_bot.is_closed.return_value = False
    mock_bot.user = object()
    mock_bot.guilds = ["guild"]
    bot.bot = mock_bot
    bot._set_status(ChannelStatus.STOPPED)

    assert bot.is_actually_connected() is True
    assert bot.get_status() == ChannelStatus.READY
    assert bot.can_send_messages() == ["guild"]


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.communication
async def test_validate_discord_user_accessibility_paths():
    bot = DiscordBot()
    assert await bot._validate_discord_user_accessibility("123") is False

    mock_bot = MagicMock()
    mock_bot.get_user.return_value = object()
    bot.bot = mock_bot
    assert await bot._validate_discord_user_accessibility("123") is True

    mock_bot.get_user.return_value = None
    mock_bot.fetch_user = AsyncMock(return_value=object())
    assert await bot._validate_discord_user_accessibility("456") is True
    mock_bot.fetch_user.assert_awaited_once_with(456)


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.communication
async def test_send_to_channel_uses_embed_view_and_plain_paths():
    bot = DiscordBot()
    channel = SimpleNamespace(id=123, send=AsyncMock())

    assert await bot._send_to_channel(channel, "plain") is True
    assert channel.send.await_args.kwargs == {"content": "plain"}

    channel.send.reset_mock()
    assert await bot._send_to_channel(
        channel,
        "rich",
        rich_data={"title": "T"},
        suggestions=["Next"],
    ) is True
    kwargs = channel.send.await_args.kwargs
    assert kwargs["content"] == "rich"
    assert kwargs["embed"] is not None
    assert kwargs["view"] is not None


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.communication
async def test_send_message_internal_validation_and_channel_paths():
    bot = DiscordBot()
    assert await bot._send_message_internal("123", "hello") is False

    mock_channel = SimpleNamespace(send=AsyncMock())
    mock_bot = MagicMock()
    mock_bot.get_channel.return_value = mock_channel
    bot.bot = mock_bot

    assert await bot._send_message_internal("", "hello") is False
    assert await bot._send_message_internal("123", "") is False
    assert await bot._send_message_internal("123", "hello", rich_data="bad") is False
    assert await bot._send_message_internal("123", "hello", suggestions="bad") is False
    assert await bot._send_message_internal("123", "hello") is True
    mock_channel.send.assert_awaited_once_with(content="hello")

    mock_bot.get_channel.return_value = None
    assert await bot._send_message_internal("not-a-channel", "hello") is False


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.communication
async def test_send_dm_validates_and_delegates(monkeypatch: pytest.MonkeyPatch):
    bot = DiscordBot()
    assert await bot.send_dm("", "hello") is False
    assert await bot.send_dm("123", "") is False

    called: list[tuple[str, str]] = []

    async def _fake_send_message(user_id: str, message: str) -> bool:
        called.append((user_id, message))
        return True

    monkeypatch.setattr(bot, "send_message", _fake_send_message)

    assert await bot.send_dm("123", "hello") is True
    assert called == [("123", "hello")]
