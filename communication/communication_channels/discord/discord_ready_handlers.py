# communication/communication_channels/discord/discord_ready_handlers.py

"""Discord lifecycle event handlers (ready, disconnect, error)."""

from __future__ import annotations

from communication.communication_channels.base.base_channel import ChannelStatus
from communication.communication_channels.discord.discord_connection_status import (
    DiscordConnectionStatus,
)
from communication.communication_channels.discord.discord_handler_protocol import (
    DiscordHandlerHost,
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
