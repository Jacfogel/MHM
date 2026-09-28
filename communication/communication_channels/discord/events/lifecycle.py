# communication/communication_channels/discord/events/lifecycle.py

"""Discord lifecycle event handlers (ready, disconnect, error, guild join)."""

from __future__ import annotations

import discord

from communication.communication_channels.base.base_channel import ChannelStatus
from communication.communication_channels.discord.events.protocol import (
    DiscordHandlerHost,
)
from communication.communication_channels.discord.events.status import (
    DiscordConnectionStatus,
)
from core.error_handling import handle_errors
from core.logger import get_component_logger

discord_logger = get_component_logger("discord")
logger = discord_logger


@handle_errors(
    "Discord bot on_ready internal handler",
    user_friendly=False,
    default_return=None,
)
async def run_on_ready_internal(bot: DiscordHandlerHost) -> None:
    """Run post-ready startup tasks once per connection."""
    if bot._on_ready_fired:
        return

    bot._on_ready_fired = True
    discord_bot = bot.bot
    if not discord_bot:
        return

    logger.info(f"Discord Bot logged in as {discord_bot.user}")
    print(f"Discord Bot is online as {discord_bot.user}")

    bot._reconnect_attempts = 0
    bot._set_status(ChannelStatus.READY)
    bot._shared__update_connection_status(DiscordConnectionStatus.CONNECTED)

    bot._schedule_ready_tasks(discord_bot)
    bot._start_discord_webhook_server_for_ready()


@handle_errors("handling Discord disconnect event", default_return=None)
async def handle_disconnect(bot: DiscordHandlerHost) -> None:
    """Handle Discord disconnect events."""
    logger.warning("Discord bot disconnected")
    discord_logger.warning(
        "Discord bot disconnected",
        bot_name=str(bot.bot.user) if bot.bot and bot.bot.user else "unknown",
        reconnect_attempts=bot._reconnect_attempts,
    )
    current_status = bot.get_status()
    if current_status == ChannelStatus.READY:
        bot._set_status(ChannelStatus.ERROR, "Disconnected")
    bot._shared__update_connection_status(DiscordConnectionStatus.DISCONNECTED)
    logger.info("Discord.py will handle automatic reconnection")


@handle_errors("handling Discord error event", default_return=None)
async def handle_error(bot: DiscordHandlerHost, event, *args, **kwargs) -> None:
    """Handle Discord error events."""
    logger.error(f"Discord bot error in event {event}: {args} {kwargs}")

    error_str = str(args) + str(kwargs)
    discord_logger.error(
        "Discord bot error",
        event=event,
        error_details=error_str[:200],
        bot_name=str(bot.bot.user) if bot.bot and bot.bot.user else "unknown",
    )

    if any(
        keyword in error_str.lower()
        for keyword in ["connection", "dns", "timeout", "network"]
    ):
        logger.warning("Connection-related error detected - checking network status")
        discord_logger.warning("Connection-related error detected", event=event)
        if not bot._check_dns_resolution():
            logger.error("DNS resolution failed during error recovery")
            discord_logger.error("DNS resolution failed during error recovery")
            bot._shared__update_connection_status(DiscordConnectionStatus.DNS_FAILURE)
        if not bot._check_network_connectivity():
            logger.error("Network connectivity failed during error recovery")
            discord_logger.error("Network connectivity failed during error recovery")
            bot._shared__update_connection_status(
                DiscordConnectionStatus.NETWORK_FAILURE
            )


@handle_errors("handling Discord guild join event", default_return=None)
async def handle_guild_join(guild: discord.Guild) -> None:
    """Handle when the bot is added to a new Discord server."""
    discord_logger.info(f"Bot added to server: {guild.name} (ID: {guild.id})")

    welcome_channel = None
    if (
        guild.system_channel
        and guild.system_channel.permissions_for(guild.me).send_messages
    ):
        welcome_channel = guild.system_channel
        discord_logger.debug(f"Using system channel: {guild.system_channel.name}")
    else:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                welcome_channel = channel
                discord_logger.debug(f"Using text channel: {channel.name}")
                break

    if not welcome_channel:
        discord_logger.warning(
            f"Could not find a suitable channel to send welcome message in {guild.name}"
        )
        return

    welcome_msg = (
        f"👋 **Hello {guild.name}!**\n\n"
        f"I'm **MHM (Mental Health Manager)**, your mental health assistant bot. "
        f"I'm here to help you manage tasks, check-ins, reminders, and provide personalized support.\n\n"
        f"**To get started:**\n"
        f"1. Send me a message to get your Discord ID\n"
        f"2. Create or link a MHM account with that Discord ID\n"
        f"3. Start using commands like `/help` to see what I can do!\n\n"
        f"**Quick Commands:**\n"
        f"- `/help` - See all available commands\n"
        f"- `create task [description]` - Create a new task\n"
        f"- `show my tasks` - View your tasks\n"
        f"- `show my profile` - View your profile (once linked)\n\n"
        f"Feel free to ask me anything! I'm here to help. 🚀"
    )

    try:
        await welcome_channel.send(welcome_msg)
        discord_logger.info(
            f"Sent welcome message to {guild.name} in channel {welcome_channel.name}"
        )
    except Exception as e:
        discord_logger.warning(f"Could not send welcome message to {guild.name}: {e}")
