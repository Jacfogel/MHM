"""
Discord create hub: shared buttons and modals for tasks and notes.

Template quick-add buttons plus modals for custom task, quick note, and new note.
Business logic stays in command handlers; this module is UI only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord

from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from communication.communication_channels.discord.discord_response_delivery import (
    deliver_handler_response,
)
from communication.communication_channels.discord.discord_user_resolution import (
    internal_user_id as _internal_user_id,
)
from communication.communication_channels.discord.item_form_shared import (
    entities_from_shared_fields,
)
from core.error_handling import handle_errors
from core.logger import get_component_logger
if TYPE_CHECKING:
    from communication.communication_channels.discord.bot import DiscordBot

logger = get_component_logger("discord")

CREATE_HUB_PREFIX = "create_hub_"
CREATE_HUB_TIMEOUT_SECONDS = 600


@handle_errors("running handler for create hub action", default_return=None)
def _run_handler(
    user_id: str, intent: str, entities: dict[str, Any], original_message: str
) -> InteractionResponse:
    from communication.command_handlers.interaction_handlers import get_interaction_handler

    handler = get_interaction_handler(intent)
    if not handler:
        return InteractionResponse(
            "I could not run that action right now. Try typing the command instead.",
            True,
        )
    return handler.handle(
        user_id,
        ParsedCommand(
            intent=intent,
            entities=entities,
            confidence=1.0,
            original_message=original_message,
        ),
    )


@handle_errors("running create hub template task", default_return=None)
async def _hub_run_template_task(
    interaction: discord.Interaction,
    discord_bot: DiscordBot | None,
    template_id: str,
) -> None:
    internal_id = _internal_user_id(interaction)
    if not internal_id:
        await interaction.response.send_message("Account not found.", ephemeral=True)
        return
    await interaction.response.defer()
    entities = {"template_ref": template_id}
    response = _run_handler(
        internal_id,
        "create_task_from_template",
        entities,
        f"task template {template_id}",
    )
    await deliver_handler_response(interaction, response, discord_bot, ephemeral=False)


@handle_errors("binding create hub template button callback", default_return=None)
def _bind_template_button_callback(
    template_id: str, discord_bot: DiscordBot | None
):
    @handle_errors("create hub template button", default_return=None)
    async def callback(interaction: discord.Interaction) -> None:
        await _hub_run_template_task(interaction, discord_bot, template_id)

    return callback


@handle_errors("binding create hub modal button callback", default_return=None)
def _bind_modal_button_callback(
    label: str,
    discord_bot: DiscordBot | None,
    modal_builder,
):
    @handle_errors(f"create hub {label} button", default_return=None)
    async def callback(interaction: discord.Interaction) -> None:
        internal_id = _internal_user_id(interaction)
        if not internal_id:
            await interaction.response.send_message("Account not found.", ephemeral=True)
            return
        modal = modal_builder(internal_id, discord_bot)
        if modal is None:
            await interaction.response.send_message(
                "Could not open that form. Please try again.", ephemeral=True
            )
            return
        await interaction.response.send_modal(modal)

    return callback


@handle_errors("building custom task modal", default_return=None)
def _build_custom_task_modal(
    user_id: str, discord_bot: DiscordBot | None
) -> discord.ui.Modal | None:
    class CustomTaskModal(discord.ui.Modal, title="Create task"):
        title_input = discord.ui.TextInput(
            label="Title",
            placeholder="What needs doing?",
            max_length=200,
            required=True,
        )
        details_input = discord.ui.TextInput(
            label="Details",
            style=discord.TextStyle.paragraph,
            placeholder="Optional notes",
            max_length=1000,
            required=False,
        )
        due_input = discord.ui.TextInput(
            label="Due",
            placeholder="e.g. tomorrow, this week, Friday",
            max_length=80,
            required=False,
        )
        group_input = discord.ui.TextInput(
            label="Group",
            placeholder="e.g. health, work",
            max_length=80,
            required=False,
        )
        tags_input = discord.ui.TextInput(
            label="Tags",
            placeholder="Comma-separated, e.g. health, urgent",
            max_length=120,
            required=False,
        )

        @handle_errors("submitting custom task modal", context={"component": "discord"})
        async def on_submit(self, modal_interaction: discord.Interaction) -> None:
            internal_id = _internal_user_id(modal_interaction)
            if not internal_id:
                await modal_interaction.response.send_message(
                    "Account not found. Link your Discord account first.", ephemeral=True
                )
                return
            await modal_interaction.response.defer(ephemeral=True)
            entities = entities_from_shared_fields(
                title=self.title_input.value,
                description=self.details_input.value,
                group=self.group_input.value,
                tags_value=self.tags_input.value,
                due_phrase=self.due_input.value,
            )
            response = _run_handler(
                internal_id, "create_task", entities, "create task from modal"
            )
            await deliver_handler_response(
                modal_interaction, response, discord_bot, ephemeral=True
            )

    return CustomTaskModal()


@handle_errors("building quick note modal", default_return=None)
def _build_quick_note_modal(
    user_id: str, discord_bot: DiscordBot | None
) -> discord.ui.Modal | None:
    class QuickNoteModal(discord.ui.Modal, title="Quick note"):
        body_input = discord.ui.TextInput(
            label="Note",
            style=discord.TextStyle.paragraph,
            placeholder="Capture a thought...",
            max_length=1500,
            required=True,
        )
        tags_input = discord.ui.TextInput(
            label="Tags",
            placeholder="Optional, comma-separated",
            max_length=120,
            required=False,
        )

        @handle_errors("submitting quick note modal", context={"component": "discord"})
        async def on_submit(self, modal_interaction: discord.Interaction) -> None:
            internal_id = _internal_user_id(modal_interaction)
            if not internal_id:
                await modal_interaction.response.send_message(
                    "Account not found. Link your Discord account first.", ephemeral=True
                )
                return
            await modal_interaction.response.defer(ephemeral=True)
            entities = entities_from_shared_fields(
                title=self.body_input.value,
                tags_value=self.tags_input.value,
            )
            response = _run_handler(
                internal_id, "create_quick_note", entities, "quick note from modal"
            )
            await deliver_handler_response(
                modal_interaction, response, discord_bot, ephemeral=True
            )

    return QuickNoteModal()


@handle_errors("building new note modal", default_return=None)
def _build_new_note_modal(
    user_id: str, discord_bot: DiscordBot | None
) -> discord.ui.Modal | None:
    class NewNoteModal(discord.ui.Modal, title="New note"):
        title_input = discord.ui.TextInput(
            label="Title",
            placeholder="Note title",
            max_length=200,
            required=True,
        )
        body_input = discord.ui.TextInput(
            label="Body",
            style=discord.TextStyle.paragraph,
            placeholder="Optional body text",
            max_length=1500,
            required=False,
        )
        group_input = discord.ui.TextInput(
            label="Group",
            placeholder="Optional group",
            max_length=80,
            required=False,
        )
        tags_input = discord.ui.TextInput(
            label="Tags",
            placeholder="Comma-separated",
            max_length=120,
            required=False,
        )

        @handle_errors("submitting new note modal", context={"component": "discord"})
        async def on_submit(self, modal_interaction: discord.Interaction) -> None:
            internal_id = _internal_user_id(modal_interaction)
            if not internal_id:
                await modal_interaction.response.send_message(
                    "Account not found. Link your Discord account first.", ephemeral=True
                )
                return
            await modal_interaction.response.defer(ephemeral=True)
            entities = entities_from_shared_fields(
                title=self.title_input.value,
                description=self.body_input.value,
                group=self.group_input.value,
                tags_value=self.tags_input.value,
            )
            response = _run_handler(
                internal_id, "create_note", entities, "create note from modal"
            )
            await deliver_handler_response(
                modal_interaction, response, discord_bot, ephemeral=True
            )

    return NewNoteModal()


@handle_errors("creating Discord create hub view", default_return=None)
def get_create_hub_view(
    user_id: str, discord_bot: DiscordBot | None = None
) -> discord.ui.View | None:
    """Return a button menu for task templates and note/task modals."""

    view = discord.ui.View(timeout=CREATE_HUB_TIMEOUT_SECONDS)

    template_buttons = [
        ("Meds", "medication", discord.ButtonStyle.primary),
        ("Appt", "appointment", discord.ButtonStyle.primary),
        ("Call", "phone_call", discord.ButtonStyle.primary),
        ("Clean", "cleaning", discord.ButtonStyle.primary),
        ("Forms", "paperwork", discord.ButtonStyle.primary),
    ]
    for label, template_id, style in template_buttons:
        button = discord.ui.Button(
            label=label,
            style=style,
            custom_id=f"{CREATE_HUB_PREFIX}tpl_{template_id}_{user_id}",
        )

        button.callback = _bind_template_button_callback(template_id, discord_bot)
        view.add_item(button)

    custom_task = discord.ui.Button(
        label="Custom task",
        style=discord.ButtonStyle.secondary,
        custom_id=f"{CREATE_HUB_PREFIX}custom_task_{user_id}",
    )

    custom_task.callback = _bind_modal_button_callback(
        "custom task", discord_bot, _build_custom_task_modal
    )
    view.add_item(custom_task)

    quick_note = discord.ui.Button(
        label="Quick note",
        style=discord.ButtonStyle.success,
        custom_id=f"{CREATE_HUB_PREFIX}quick_note_{user_id}",
    )

    quick_note.callback = _bind_modal_button_callback(
        "quick note", discord_bot, _build_quick_note_modal
    )
    view.add_item(quick_note)

    new_note = discord.ui.Button(
        label="New note",
        style=discord.ButtonStyle.success,
        custom_id=f"{CREATE_HUB_PREFIX}new_note_{user_id}",
    )

    new_note.callback = _bind_modal_button_callback(
        "new note", discord_bot, _build_new_note_modal
    )
    view.add_item(new_note)

    return view


@handle_errors("building create hub rich data", default_return={})
def create_hub_rich_data(user_id: str) -> dict[str, Any]:
    """Rich-data marker for attaching the create hub view when sending on Discord."""
    return {"interaction_view": "create_hub", "user_id": user_id}
