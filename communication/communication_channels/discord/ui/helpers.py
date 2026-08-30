"""Shared Discord UI helpers: user resolution, command runner, response delivery."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord

from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from core.error_handling import handle_errors

if TYPE_CHECKING:
    from communication.communication_channels.discord.bot import DiscordBot


@handle_errors("resolving internal user from Discord interaction", default_return=None)
def internal_user_id(interaction: discord.Interaction) -> str | None:
    """Map a Discord interaction to the internal MHM user id."""
    from core import get_user_id_by_identifier

    if not interaction.user:
        return None
    return get_user_id_by_identifier(str(interaction.user.id))


@handle_errors("running Discord command handler", default_return=None)
def run_discord_handler_intent(
    user_id: str,
    intent: str,
    entities: dict[str, Any],
    original_message: str,
    *,
    missing_handler_message: str,
) -> InteractionResponse:
    """Run a command handler for a Discord UI action."""
    from communication.command_handlers.interaction_handlers import get_interaction_handler

    handler = get_interaction_handler(intent)
    if not handler:
        return InteractionResponse(missing_handler_message, True)
    return handler.handle(
        user_id,
        ParsedCommand(
            intent=intent,
            entities=entities,
            confidence=1.0,
            original_message=original_message,
        ),
    )


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
        view = discord_bot._resolve_interaction_view_from_rich_data(response.rich_data)
        if not view:
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
