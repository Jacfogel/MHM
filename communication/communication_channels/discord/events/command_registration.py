"""Discord slash and classic command registration."""

from __future__ import annotations

import contextlib

import discord

from communication.communication_channels.discord.events.protocol import (
    DiscordHandlerHost,
)
from core.error_handling import handle_errors


@handle_errors("registering Discord slash and prefix commands", default_return=None)
def register_discord_commands(host: DiscordHandlerHost) -> None:
    """Register dynamic slash and prefix commands on the host's Discord client."""
    if host._commands_registered or not host.bot:
        return
    # Resolve these through bot.py to preserve its established patch/import surface.
    from communication.communication_channels.discord import bot as bot_module

    from communication.message_processing.interaction_manager import (
        get_interaction_manager,
        handle_user_message,
    )

    command_definitions = get_interaction_manager().get_command_definitions()
    for command_definition in command_definitions:
        name = command_definition["name"]
        mapped = command_definition["mapped_message"]
        description = command_definition["description"]

        @handle_errors(
            "handling Discord app command",
            context={"command": name},
            default_return=None,
        )
        async def _app_cb(
            interaction: discord.Interaction, _mapped=mapped, _name=name
        ):
            discord_user_id = str(interaction.user.id)
            internal_user_id = bot_module.get_user_id_by_identifier(discord_user_id)
            if not internal_user_id:
                await interaction.response.send_message(
                    "Please create or link a MHM account to use this feature. "
                    f"Your Discord ID: `{discord_user_id}`",
                    ephemeral=True,
                )
                return
            response = handle_user_message(internal_user_id, _mapped, "discord")
            embed = None
            if host._has_display_rich_data(response.rich_data):
                embed = host._create_discord_embed(
                    response.message, response.rich_data
                )
            view = host._resolve_interaction_view_from_rich_data(response.rich_data)
            if not view:
                labels, payloads = host._get_action_row_inputs(
                    response.suggestions, response.rich_data
                )
                if labels:
                    view = host._create_action_row(labels, payloads)
            if embed and view:
                await interaction.response.send_message(embed=embed, view=view)
            elif embed:
                await interaction.response.send_message(embed=embed)
            elif view:
                await interaction.response.send_message(response.message, view=view)
            else:
                await interaction.response.send_message(response.message)

        with contextlib.suppress(Exception):
            host.bot.tree.add_command(
                bot_module.app_commands.Command(
                    name=name,
                    description=(description or f"{name} command"),
                    callback=_app_cb,
                )
            )

    for command_definition in command_definitions:
        name = command_definition["name"]
        mapped = command_definition["mapped_message"]
        if name in ["help"]:
            continue

        @handle_errors(
            "handling Discord dynamic command",
            context={"command": name},
            default_return=None,
        )
        async def _dynamic(ctx, _mapped=mapped, _name=name):
            internal_user_id = bot_module.get_user_id_by_identifier(str(ctx.author.id))
            if not internal_user_id:
                await ctx.send("Please register first to use this feature.")
                return
            response = handle_user_message(internal_user_id, _mapped, "discord")
            await ctx.send(response.message)

        with contextlib.suppress(Exception):
            host.bot.command(name=name)(_dynamic)

    host._commands_registered = True
