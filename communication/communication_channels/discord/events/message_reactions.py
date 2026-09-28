"""Discord reactions that ask for more of a scheduled message, or retire it."""

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

_VARIATION_SELECTOR = "\ufe0f"
_POSITIVE = {
    "👍",
    "thumbsup",
    "+1",
    "😀",
    "grinning",
    "😃",
    "smiley",
    "😄",
    "smile",
    "😁",
    "grin",
    "😆",
    "laughing",
    "satisfied",
    "😊",
    "blush",
    "🙂",
    "slightly_smiling_face",
    "slight_smile",
    "😉",
    "wink",
    "😇",
    "innocent",
    "😋",
    "yum",
    "😍",
    "heart_eyes",
    "🥰",
    "smiling_face_with_three_hearts",
    "smiling_face_with_3_hearts",
    "😘",
    "kissing_heart",
    "😗",
    "kissing",
    "😙",
    "kissing_smiling_eyes",
    "😚",
    "kissing_closed_eyes",
    "🤗",
    "hugging",
    "hugging_face",
    "hugs",
    "😂",
    "joy",
    "🤣",
    "rofl",
    "🤩",
    "star_struck",
    "🥳",
    "partying_face",
    "❤",
    "♥",
    "heart",
    "red_heart",
    "hearts",
    "🧡",
    "orange_heart",
    "💛",
    "yellow_heart",
    "💚",
    "green_heart",
    "💙",
    "blue_heart",
    "💜",
    "purple_heart",
    "🤍",
    "white_heart",
    "💖",
    "sparkling_heart",
    "💗",
    "heartpulse",
    "💓",
    "heartbeat",
    "💕",
    "two_hearts",
    "💞",
    "revolving_hearts",
    "💘",
    "cupid",
    "💝",
    "gift_heart",
    "🩷",
    "pink_heart",
    "🩵",
    "light_blue_heart",
    "🫶",
    "heart_hands",
    "🎉",
    "tada",
    "🙌",
    "raised_hands",
    "👏",
    "clap",
    "✅",
    "white_check_mark",
    "💯",
    "100",
    "⭐",
    "star",
    "🌟",
    "star2",
    "✨",
    "sparkles",
    "💪",
    "muscle",
}
_NEGATIVE = {
    "👎",
    "thumbsdown",
    "-1",
    "☹",
    "frowning_face",
    "frowning2",
    "white_frowning_face",
    "🙁",
    "slightly_frowning_face",
    "slight_frown",
    "😦",
    "frowning",
    "😞",
    "disappointed",
    "😠",
    "angry",
    "😡",
    "rage",
    "pout",
    "🤬",
    "face_with_symbols_over_mouth",
    "cursing_face",
    "😤",
    "triumph",
    "😒",
    "unamused",
    "🙄",
    "roll_eyes",
    "face_with_rolling_eyes",
    "😔",
    "pensive",
    "😢",
    "cry",
    "😭",
    "sob",
    "😩",
    "weary",
    "😫",
    "tired_face",
    "😣",
    "persevere",
    "😖",
    "confounded",
    "😬",
    "grimacing",
    "🤢",
    "nauseated_face",
    "🤮",
    "face_vomiting",
    "vomiting_face",
    "💩",
    "hankey",
    "poop",
    "💔",
    "broken_heart",
    "❌",
    "x",
    "🚫",
    "no_entry_sign",
    "⛔",
    "no_entry",
    "🙅",
    "no_good",
    "person_gesturing_no",
    "🛑",
    "stop_sign",
    "octagonal_sign",
    "🖕",
    "middle_finger",
    "reversed_hand_with_middle_finger_extended",
}


@handle_errors("handling Discord message reaction", default_return=None)
async def handle_message_reaction(bot: DiscordHandlerHost, payload: discord.RawReactionActionEvent) -> None:
    """Turn a positive or negative reaction into more similar messages, or retire that one."""
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
    """Return up or down for a clearly positive or negative emoji, otherwise None."""
    name = str(getattr(emoji, "name", "") or "").replace(_VARIATION_SELECTOR, "")
    if name in _POSITIVE:
        return "up"
    if name in _NEGATIVE:
        return "down"
    return None
