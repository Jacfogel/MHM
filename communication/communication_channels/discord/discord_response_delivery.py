"""Deliver channel-agnostic InteractionResponse objects on Discord."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from communication.command_handlers.shared_types import InteractionResponse
from core.error_handling import handle_errors

if TYPE_CHECKING:
    from communication.communication_channels.discord.bot import DiscordBot


@handle_errors("delivering handler response on Discord", default_return=None)
async def deliver_handler_response(
    interaction: discord.Interaction,
    response: InteractionResponse,
    discord_bot: DiscordBot | None,
    *,
    ephemeral: bool = False,
) -> None:
    """Send a handler response via interaction followup (call after defer)."""
    embed: discord.Embed | None = None
    if discord_bot and discord_bot._has_display_rich_data(response.rich_data):
        embed = discord_bot._create_discord_embed(response.message, response.rich_data)

    view: discord.ui.View | None = None
    if discord_bot:
        button_labels, button_payloads = discord_bot._get_action_row_inputs(
            response.suggestions, response.rich_data
        )
        if button_labels:
            view = discord_bot._create_action_row(button_labels, button_payloads)

    content: str = response.message or ""
    if embed is not None and view is not None:
        await interaction.followup.send(
            content=content,
            embed=embed,
            view=view,
            ephemeral=ephemeral,
        )
    elif embed is not None:
        await interaction.followup.send(
            content=content,
            embed=embed,
            ephemeral=ephemeral,
        )
    elif view is not None:
        await interaction.followup.send(
            content=content,
            view=view,
            ephemeral=ephemeral,
        )
    else:
        await interaction.followup.send(content=content, ephemeral=ephemeral)
