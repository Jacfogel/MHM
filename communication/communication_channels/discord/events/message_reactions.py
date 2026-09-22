"""Discord thumbs-up and thumbs-down reactions on scheduled messages."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, cast

import discord

from communication.communication_channels.discord.events.protocol import DiscordHandlerHost
from core import get_user_id_by_identifier
from core.error_handling import handle_errors
from core.logger import get_component_logger
from messages.message_reactions import apply_message_reaction

discord_logger = get_component_logger("discord")

_THUMBS_UP = {"👍", "thumbsup"}
_THUMBS_DOWN = {"👎", "thumbsdown"}


@handle_errors("handling Discord message reaction", default_return=None)
async def handle_message_reaction(bot: DiscordHandlerHost, payload: discord.RawReactionActionEvent) -> None:
    """Turn a thumbs reaction on a sent MHM message into more, or fewer, similar messages."""
    discord_bot = bot.bot
    if discord_bot and discord_bot.user and payload.user_id == discord_bot.user.id:
        return
    kind = _reaction_kind(payload.emoji)
    if not kind:
        return
    internal_user_id = get_user_id_by_identifier(str(payload.user_id))
    if not internal_user_id:
        return
    result = apply_message_reaction(internal_user_id, str(payload.message_id), kind)
    reply = str(result.get("reply") or "").strip()
    if not reply or not discord_bot:
        return
    channel = discord_bot.get_channel(payload.channel_id)
    if channel is None:
        channel = await discord_bot.fetch_channel(payload.channel_id)
    send = getattr(channel, "send", None)
    if not callable(send):
        discord_logger.warning(
            "Could not reply to a message reaction because the channel cannot send"
        )
        return
    await cast(Callable[[str], Awaitable[Any]], send)(reply)


@handle_errors("classifying Discord reaction emoji", default_return=None)
def _reaction_kind(emoji: discord.PartialEmoji) -> str | None:
    """Return up or down for a thumbs emoji, otherwise None."""
    name = str(getattr(emoji, "name", "") or "")
    if name in _THUMBS_UP:
        return "up"
    if name in _THUMBS_DOWN:
        return "down"
    return None
