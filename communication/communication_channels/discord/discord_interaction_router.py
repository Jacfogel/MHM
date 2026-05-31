# communication/communication_channels/discord/discord_interaction_router.py

"""Route Discord component and application-command interactions."""

from __future__ import annotations

from typing import Any

import discord

from communication.communication_channels.discord.discord_handler_protocol import (
    DiscordHandlerHost,
)
from core import get_user_id_by_identifier
from core.error_handling import handle_errors
from core.logger import get_component_logger

discord_logger = get_component_logger("discord")


@handle_errors("handling Discord interaction event", default_return=None)
async def handle_discord_interaction(
    bot: DiscordHandlerHost, interaction: discord.Interaction
) -> None:
    """Handle Discord interactions (slash commands, buttons, etc.)."""
    if interaction.type == discord.InteractionType.component:
        await _handle_component_interaction(bot, interaction)
        return

    if interaction.type == discord.InteractionType.application_command:
        await _handle_application_command_interaction(bot, interaction)


@handle_errors("handling Discord component interaction", default_return=None)
async def _handle_component_interaction(
    bot: DiscordHandlerHost, interaction: discord.Interaction
) -> None:
    if not interaction.data or "custom_id" not in interaction.data:
        return

    custom_id = interaction.data["custom_id"]

    if custom_id.startswith("welcome_create_") or custom_id.startswith("welcome_link_"):
        await _handle_welcome_button(bot, interaction, custom_id)
        return

    if custom_id.startswith(("checkin_", "task_", "create_hub_")):
        return

    if custom_id.startswith("suggestion_"):
        await _handle_suggestion_button(bot, interaction, custom_id)


@handle_errors("handling Discord welcome button", default_return=None)
async def _handle_welcome_button(
    bot: DiscordHandlerHost, interaction: discord.Interaction, custom_id: str
) -> None:
    parts = custom_id.split("_", 2)
    if len(parts) < 3:
        return

    discord_user_id = parts[2]
    from communication.communication_channels.discord.account_flow_handler import (
        start_account_creation_flow,
        start_account_linking_flow,
    )

    discord_username = interaction.user.name if interaction.user else None

    if not isinstance(interaction, discord.Interaction):
        discord_logger.error(
            f"Invalid interaction type for welcome button: {type(interaction)}"
        )
        await interaction.response.send_message(
            "❌ An error occurred. Please try again.",
            ephemeral=True,
        )
        return

    if custom_id.startswith("welcome_create_"):
        await start_account_creation_flow(
            interaction, discord_user_id, discord_username
        )
    elif custom_id.startswith("welcome_link_"):
        await start_account_linking_flow(interaction, discord_user_id)


@handle_errors("handling Discord suggestion button", default_return=None)
async def _handle_suggestion_button(
    bot: DiscordHandlerHost, interaction: discord.Interaction, custom_id: str
) -> None:
    await interaction.response.defer()

    button_label = _extract_suggestion_button_label(interaction, custom_id)
    discord_logger.info(
        f"Processing suggestion button '{button_label}' (custom_id: {custom_id})"
    )

    if not button_label:
        discord_logger.warning(
            f"Could not extract button label from suggestion button {custom_id}"
        )
        await interaction.followup.send(
            "❌ Could not process button click. Please try typing the command instead.",
            ephemeral=True,
        )
        return

    discord_user_id = str(interaction.user.id)
    internal_user_id = get_user_id_by_identifier(discord_user_id)

    if not internal_user_id:
        discord_logger.warning(
            f"No internal user ID found for Discord user {discord_user_id}"
        )
        await interaction.followup.send(
            "❌ User account not found. Please try again.",
            ephemeral=True,
        )
        return

    response = _build_suggestion_button_response(
        bot, custom_id, button_label, internal_user_id
    )
    if response is None:
        await interaction.followup.send(
            "❌ An error occurred processing your button click. Please try typing the command instead.",
            ephemeral=True,
        )
        return
    await _send_suggestion_followup(bot, interaction, response)


@handle_errors("extracting suggestion button label", default_return=None)
def _extract_suggestion_button_label(
    interaction: discord.Interaction, custom_id: str
) -> str | None:
    button_label = None
    comp = getattr(interaction, "component", None)
    if comp:
        button_label = getattr(comp, "label", None)
    if not button_label and interaction.data:
        button_label = interaction.data.get("label")
    if not button_label and interaction.message:
        for component in interaction.message.components:
            children = getattr(component, "children", None)
            if children:
                for child in children:
                    if hasattr(child, "custom_id") and child.custom_id == custom_id:
                        button_label = getattr(child, "label", None)
                        break
            if button_label:
                break
    return button_label


@handle_errors(
    "building suggestion button response",
    default_return=None,
)
def _build_suggestion_button_response(
    bot: DiscordHandlerHost,
    custom_id: str,
    button_label: str,
    internal_user_id: str,
) -> Any:
    from communication.command_handlers.interaction_handlers import get_interaction_handler
    from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
    from communication.message_processing.interaction_manager import handle_user_message

    payload = bot._suggestion_button_payloads.get(custom_id)
    if isinstance(payload, dict) and payload.get("intent"):
        intent = str(payload["intent"])
        entities = payload.get("entities", {})
        if not isinstance(entities, dict):
            entities = {}
        handler = get_interaction_handler(intent)
        if handler:
            return handler.handle(
                internal_user_id,
                ParsedCommand(
                    intent=intent,
                    entities=entities,
                    confidence=1.0,
                    original_message=button_label,
                ),
            )
        return InteractionResponse(
            "I could not continue that notebook page. Please try the command again.",
            True,
        )

    button_message = (
        str(payload) if isinstance(payload, str) else button_label.lower().strip()
    )
    discord_logger.info(
        f"Processing button click as message '{button_message}' for user {internal_user_id}"
    )
    return handle_user_message(internal_user_id, button_message, "discord")


@handle_errors("sending suggestion button followup", default_return=None)
async def _send_suggestion_followup(
    bot: DiscordHandlerHost, interaction: discord.Interaction, response: Any
) -> None:
    embed = None
    if bot._has_display_rich_data(response.rich_data):
        embed = bot._create_discord_embed(response.message, response.rich_data)

    view = None
    button_labels, button_payloads = bot._get_action_row_inputs(
        response.suggestions, response.rich_data
    )
    if button_labels:
        view = bot._create_action_row(button_labels, button_payloads)

    if embed and view:
        await interaction.followup.send(
            content=response.message or "", embed=embed, view=view
        )
    elif embed:
        await interaction.followup.send(content=response.message or "", embed=embed)
    elif view:
        await interaction.followup.send(content=response.message, view=view)
    else:
        await interaction.followup.send(content=response.message)


@handle_errors("handling Discord application command interaction", default_return=None)
async def _handle_application_command_interaction(
    bot: DiscordHandlerHost, interaction: discord.Interaction
) -> None:
    discord_user_id = str(interaction.user.id)
    command_name = (
        interaction.command.name
        if hasattr(interaction, "command") and interaction.command
        else "unknown"
    )
    discord_logger.debug(
        f"DISCORD_INTERACTION: user_id={discord_user_id}, command={command_name}"
    )

    from communication.communication_channels.discord.welcome_handler import (
        get_welcome_message,
        has_been_welcomed,
        mark_as_welcomed,
    )

    internal_user_id = get_user_id_by_identifier(discord_user_id)

    if command_name == "start" and not internal_user_id:
        await _handle_start_command_welcome(interaction, discord_user_id)
        return

    if not internal_user_id and not has_been_welcomed(discord_user_id):
        welcome_msg = get_welcome_message(discord_user_id, is_authorization=True)
        try:
            await interaction.user.send(welcome_msg)
            mark_as_welcomed(discord_user_id)
            discord_logger.info(
                f"Sent welcome DM to newly authorized Discord user via interaction: {discord_user_id}"
            )
        except discord.Forbidden:
            mark_as_welcomed(discord_user_id)
            discord_logger.info(
                f"User {discord_user_id} has DMs disabled, marked as welcomed"
            )
        except Exception as e:
            discord_logger.warning(f"Error sending welcome DM to {discord_user_id}: {e}")


@handle_errors("handling Discord /start welcome", default_return=None)
async def _handle_start_command_welcome(
    interaction: discord.Interaction, discord_user_id: str
) -> None:
    from communication.communication_channels.discord.welcome_handler import (
        get_welcome_message,
        mark_as_welcomed,
    )

    welcome_msg = get_welcome_message(discord_user_id, is_authorization=True)
    try:
        await interaction.user.send(welcome_msg)
        mark_as_welcomed(discord_user_id)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "👋 Welcome! I've sent you setup instructions via DM. Check your direct messages!",
                ephemeral=True,
            )
        discord_logger.info(
            f"Sent welcome DM to newly authorized Discord user via /start: {discord_user_id}"
        )
    except discord.Forbidden:
        mark_as_welcomed(discord_user_id)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"👋 Welcome! I see you've authorized MHM. However, I can't send you a direct message.\n\n"
                f"**Your Discord ID:** `{discord_user_id}`\n\n"
                f"**To get started:**\n"
                f"- Create a new account via the MHM application UI with your Discord ID, or\n"
                f"- Ask an administrator to link your Discord ID to an existing account",
                ephemeral=True,
            )
        discord_logger.info(f"Welcomed user {discord_user_id} via /start (DM blocked)")
    except Exception as e:
        discord_logger.warning(f"Error sending welcome DM to {discord_user_id}: {e}")
