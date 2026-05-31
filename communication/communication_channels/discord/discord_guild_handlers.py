# communication/communication_channels/discord/discord_guild_handlers.py

"""Discord guild lifecycle event handlers."""

import discord

from core.error_handling import handle_errors
from core.logger import get_component_logger

discord_logger = get_component_logger("discord")


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
