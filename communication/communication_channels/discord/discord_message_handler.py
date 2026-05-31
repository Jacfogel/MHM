# communication/communication_channels/discord/discord_message_handler.py

"""Discord on_message event handling."""

from __future__ import annotations

import discord

from communication.communication_channels.discord.discord_handler_protocol import (
    DiscordHandlerHost,
)
from core import get_user_id_by_identifier
from core.error_handling import handle_errors
from core.logger import get_component_logger

discord_logger = get_component_logger("discord")
logger = discord_logger


@handle_errors("handling Discord message", default_return=None)
async def handle_discord_message(
    bot: DiscordHandlerHost, message: discord.Message
) -> None:
    """Process inbound Discord messages through the interaction manager."""
    discord_logger.debug(
        f"DISCORD_MESSAGE_RECEIVED: author_id={message.author.id}, content='{message.content[:100]}', channel={message.channel.id}, guild={message.guild.id if message.guild else 'DM'}"
    )

    if bot.bot and message.author == bot.bot.user:
        discord_logger.debug(
            "DISCORD_MESSAGE_IGNORED: Message from bot itself, ignoring"
        )
        return

    discord_user_id = str(message.author.id)
    discord_logger.debug(
        f"DISCORD_MESSAGE_PROCESS: Looking up user for Discord ID {discord_user_id}"
    )
    internal_user_id = get_user_id_by_identifier(discord_user_id)

    if not internal_user_id:
        await _handle_unrecognized_user_message(message, discord_user_id)
        return

    discord_logger.info(
        f"DISCORD_MESSAGE_USER_IDENTIFIED: Discord ID {discord_user_id} → Internal user {internal_user_id}"
    )

    _sync_discord_user_id(internal_user_id, discord_user_id)
    await _process_identified_user_message(bot, message, internal_user_id, discord_user_id)


@handle_errors("handling unrecognized Discord user message", default_return=None)
async def _handle_unrecognized_user_message(
    message: discord.Message, discord_user_id: str
) -> None:
    discord_logger.warning(
        f"DISCORD_MESSAGE_UNRECOGNIZED: No internal user found for Discord ID {discord_user_id}"
    )

    from communication.communication_channels.discord.welcome_handler import (
        get_welcome_message,
        has_been_welcomed,
        mark_as_welcomed,
    )

    is_dm = isinstance(message.channel, discord.DMChannel)

    if not has_been_welcomed(discord_user_id):
        welcome_msg = get_welcome_message(discord_user_id, is_authorization=is_dm)

        if is_dm:
            try:
                await message.author.send(welcome_msg)
                mark_as_welcomed(discord_user_id)
                discord_logger.info(
                    f"Sent welcome DM to newly authorized Discord user: {discord_user_id}"
                )
            except discord.Forbidden:
                await message.channel.send(
                    f"I see you've authorized MHM! However, I can't send you a direct message. "
                    f"Here's your Discord ID to get started: `{discord_user_id}`\n\n"
                    f"**To get started:**\n"
                    f"- Create a new account via the MHM application UI with your Discord ID, or\n"
                    f"- Ask an administrator to link your Discord ID to an existing account"
                )
                mark_as_welcomed(discord_user_id)
                discord_logger.info(
                    f"Welcomed user {discord_user_id} via channel (DM blocked)"
                )
        else:
            try:
                await message.author.send(welcome_msg)
                mark_as_welcomed(discord_user_id)
                discord_logger.info(
                    f"Sent welcome DM to new Discord user (from server message): {discord_user_id}"
                )
            except discord.Forbidden:
                await message.channel.send(welcome_msg)
                mark_as_welcomed(discord_user_id)
                discord_logger.info(
                    f"Sent welcome message to new Discord user in channel: {discord_user_id}"
                )
        return

    if is_dm:
        try:
            await message.author.send(
                f"I don't recognize you yet! To use MHM, you need to create or link a MHM account.\n\n"
                f"**Your Discord ID:** `{discord_user_id}`\n\n"
                f"**To get started:**\n"
                f"- Create a new account via the MHM application UI, or\n"
                f"- Ask an administrator to link your Discord ID to an existing account\n\n"
                f"Once your account is linked, I'll be able to help you with tasks, reminders, and more!"
            )
        except discord.Forbidden:
            await message.channel.send(
                f"Your Discord ID: `{discord_user_id}` - Please create or link a MHM account to get started!"
            )
    else:
        await message.channel.send(
            f"I don't recognize you yet! To use MHM, you need to create or link a MHM account.\n\n"
            f"**Your Discord ID:** `{discord_user_id}`\n\n"
            f"**To get started:**\n"
            f"- Create a new account via the MHM application UI, or\n"
            f"- Ask an administrator to link your Discord ID to an existing account\n\n"
            f"Once your account is linked, I'll be able to help you with tasks, reminders, and more!"
        )


@handle_errors("syncing Discord user ID", default_return=None)
def _sync_discord_user_id(internal_user_id: str, discord_user_id: str) -> None:
    from core import get_user_data, save_user_data

    user_data_result = get_user_data(internal_user_id, "account")
    account_data = user_data_result.get("account", {})
    stored_discord_id = account_data.get("discord_user_id")

    if stored_discord_id and str(stored_discord_id) != discord_user_id:
        logger.info(
            f"Updating Discord user ID for user {internal_user_id} from {stored_discord_id} to {discord_user_id}"
        )
        account_data["discord_user_id"] = discord_user_id
        save_user_data(internal_user_id, "account", account_data)


@handle_errors("processing identified Discord user message", default_return=None)
async def _process_identified_user_message(
    bot: DiscordHandlerHost,
    message: discord.Message,
    internal_user_id: str,
    discord_user_id: str,
) -> None:
    from communication.message_processing.interaction_manager import handle_user_message

    discord_logger.info(
        f"DISCORD_BOT: Calling handle_user_message for user {internal_user_id} with message: '{message.content[:50]}...'"
    )
    response = handle_user_message(internal_user_id, message.content, "discord")

    if not response.message:
        return

    send_success = await bot._send_to_channel(
        message.channel,
        response.message,
        response.rich_data,
        response.suggestions,
    )

    if send_success:
        discord_logger.info(
            "Discord message handled successfully",
            user_id=internal_user_id,
            message_length=len(message.content),
            response_length=len(response.message),
            suggestions_count=(
                len(response.suggestions) if response.suggestions else 0
            ),
            has_rich_data=bool(response.rich_data),
        )
    else:
        discord_logger.warning(
            "Discord message send failed for user",
            user_id=internal_user_id,
            discord_user_id=discord_user_id,
        )
