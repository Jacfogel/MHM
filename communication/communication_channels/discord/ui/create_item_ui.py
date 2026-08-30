"""
Discord create hub: shared buttons and modals for tasks and notes.

Template buttons open a prefilled task modal; custom task, quick note, and new note also use modals.
Business logic stays in command handlers; this module is UI only.
Also contains shared modal field parsing previously in item_form_shared.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord

from communication.command_handlers.shared_types import InteractionResponse
from communication.communication_channels.discord.ui.helpers import (
    deliver_handler_response,
    internal_user_id as _internal_user_id,
    run_discord_handler_intent,
)
from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.tags import parse_tags_from_text

if TYPE_CHECKING:
    from communication.communication_channels.discord.bot import DiscordBot

logger = get_component_logger("discord")

CREATE_HUB_PREFIX = "create_hub_"
CREATE_HUB_MODAL_TASK_PREFIX = "create_hub_modal_task:"
CREATE_HUB_FIELD_TITLE = "create_hub_f_title"
CREATE_HUB_FIELD_DETAILS = "create_hub_f_details"
CREATE_HUB_FIELD_DUE = "create_hub_f_due"
CREATE_HUB_FIELD_GROUP = "create_hub_f_group"
CREATE_HUB_FIELD_TAGS = "create_hub_f_tags"
CREATE_HUB_TIMEOUT_SECONDS = 600


@handle_errors("parsing modal tags", default_return=[])
def parse_modal_tags(tags_value: str | None) -> list[str]:
    """Parse comma- or space-separated tags from a modal text field."""
    if not tags_value or not str(tags_value).strip():
        return []
    raw = str(tags_value).strip()
    if "," in raw:
        parts = [part.strip() for part in raw.split(",")]
    else:
        parts = [part.strip() for part in raw.split()]
    return [tag.lstrip("#") for tag in parts if tag]


@handle_errors("building entities from shared modal fields", default_return={})
def entities_from_shared_fields(
    *,
    title: str | None = None,
    description: str | None = None,
    group: str | None = None,
    tags_value: str | None = None,
    due_phrase: str | None = None,
    priority: str | None = None,
) -> dict[str, Any]:
    """Build handler entities dict from shared modal fields."""
    entities: dict[str, Any] = {}
    if title and title.strip():
        entities["title"] = title.strip()
    if description and description.strip():
        entities["description"] = description.strip()
    if group and group.strip():
        entities["group"] = group.strip()

    tags = parse_modal_tags(tags_value)
    if tags:
        entities["tags"] = tags

    if title:
        cleaned_title, parsed = parse_tags_from_text(title.strip())
        if parsed:
            entities["title"] = cleaned_title
            existing = entities.get("tags", [])
            entities["tags"] = list(dict.fromkeys([*existing, *parsed]))

    if due_phrase and due_phrase.strip():
        entities["due_date"] = due_phrase.strip()
    if priority and priority.strip():
        entities["priority"] = priority.strip().lower()

    return entities


@handle_errors("running handler for create hub action", default_return=None)
def _run_handler(
    user_id: str, intent: str, entities: dict[str, Any], original_message: str
) -> InteractionResponse:
    """Run a create-hub command handler intent and return its response."""
    return run_discord_handler_intent(
        user_id,
        intent,
        entities,
        original_message,
        missing_handler_message=(
            "I could not run that action right now. Try typing the command instead."
        ),
    )


@handle_errors("submitting create hub task modal", default_return=None)
async def _submit_task_form(
    modal_interaction: discord.Interaction,
    discord_bot: DiscordBot | None,
    *,
    intent: str,
    entities: dict[str, Any],
    original_message: str,
) -> None:
    """Defer and run a create-task intent after a modal submit."""
    if modal_interaction.response.is_done():
        return
    internal_id = _internal_user_id(modal_interaction)
    if not internal_id:
        await modal_interaction.response.send_message(
            "Account not found. Link your Discord account first.", ephemeral=True
        )
        return
    await modal_interaction.response.defer(ephemeral=True)
    response = _run_handler(internal_id, intent, entities, original_message)
    if response is None:
        response = InteractionResponse(
            "I could not create that right now. Please try typing the command instead.",
            True,
        )
    await deliver_handler_response(
        modal_interaction, response, discord_bot, ephemeral=True
    )


@handle_errors("reading create hub modal field values", default_return={})
def _modal_field_values(interaction: discord.Interaction) -> dict[str, str]:
    """Read text-input values from a modal-submit interaction payload."""
    values: dict[str, str] = {}
    data = getattr(interaction, "data", None) or {}
    for row in data.get("components", []) or []:
        for child in row.get("components", []) or []:
            custom_id = str(child.get("custom_id") or "")
            if custom_id:
                values[custom_id] = str(child.get("value") or "")
    return values


@handle_errors("handling create hub modal submit", default_return=None)
async def handle_create_hub_modal_submit(
    interaction: discord.Interaction,
    discord_bot: Any,
) -> bool:
    """Handle a create-hub task modal submit, including after a bot restart.

    Returns True when this interaction was a create-hub task modal.
    """
    data = getattr(interaction, "data", None) or {}
    custom_id = str(data.get("custom_id") or "")
    if not custom_id.startswith(CREATE_HUB_MODAL_TASK_PREFIX):
        return False
    if interaction.response.is_done():
        return True

    logger.info(f"Create hub modal submitted: {custom_id}")
    template_key = custom_id[len(CREATE_HUB_MODAL_TASK_PREFIX) :].strip() or "custom"
    values = _modal_field_values(interaction)
    extra: dict[str, Any] = {}
    if template_key != "custom":
        extra["template_ref"] = template_key
        intent = "create_task_from_template"
        original_message = f"task template {template_key}"
    else:
        intent = "create_task"
        original_message = "create task from modal"
    entities = entities_from_shared_fields(
        title=values.get(CREATE_HUB_FIELD_TITLE),
        description=values.get(CREATE_HUB_FIELD_DETAILS),
        group=values.get(CREATE_HUB_FIELD_GROUP),
        tags_value=values.get(CREATE_HUB_FIELD_TAGS),
        due_phrase=values.get(CREATE_HUB_FIELD_DUE),
    )
    if extra:
        entities = {**extra, **entities}
    await _submit_task_form(
        interaction,
        discord_bot,
        intent=intent,
        entities=entities,
        original_message=original_message,
    )
    return True


@handle_errors("binding create hub modal button callback", default_return=None)
def _bind_modal_button_callback(
    label: str,
    discord_bot: DiscordBot | None,
    modal_builder,
):
    """Return a Discord button callback that opens a create-hub modal."""
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


@handle_errors("building create hub task modal", default_return=None)
def _build_task_modal(
    user_id: str,
    discord_bot: DiscordBot | None,
    *,
    modal_title: str = "Create task",
    title_default: str = "",
    details_default: str = "",
    due_default: str = "",
    group_default: str = "",
    tags_default: str = "",
    intent: str = "create_task",
    original_message: str = "create task from modal",
    extra_entities: dict[str, Any] | None = None,
) -> discord.ui.Modal | None:
    """Return a task create modal, optionally prefilled from a template."""
    del user_id
    extra = dict(extra_entities or {})
    safe_title = (modal_title or "Create task")[:45]
    template_key = str(extra.get("template_ref") or "custom")
    modal_custom_id = f"{CREATE_HUB_MODAL_TASK_PREFIX}{template_key}"[:100]

    class TaskFormModal(discord.ui.Modal):
        title_input = discord.ui.TextInput(
            label="Title",
            custom_id=CREATE_HUB_FIELD_TITLE,
            placeholder="What needs doing?",
            default=title_default[:200] or None,
            max_length=200,
            required=True,
        )
        details_input = discord.ui.TextInput(
            label="Details",
            custom_id=CREATE_HUB_FIELD_DETAILS,
            style=discord.TextStyle.paragraph,
            placeholder="Optional notes",
            default=details_default[:1000] or None,
            max_length=1000,
            required=False,
        )
        due_input = discord.ui.TextInput(
            label="Due",
            custom_id=CREATE_HUB_FIELD_DUE,
            placeholder="e.g. tomorrow, this week, Friday",
            default=due_default[:80] or None,
            max_length=80,
            required=False,
        )
        group_input = discord.ui.TextInput(
            label="Group",
            custom_id=CREATE_HUB_FIELD_GROUP,
            placeholder="e.g. health, work",
            default=group_default[:80] or None,
            max_length=80,
            required=False,
        )
        tags_input = discord.ui.TextInput(
            label="Tags",
            custom_id=CREATE_HUB_FIELD_TAGS,
            placeholder="Comma-separated, e.g. health, urgent",
            default=tags_default[:120] or None,
            max_length=120,
            required=False,
        )

        @handle_errors("initializing create hub task modal", default_return=None)
        def __init__(self) -> None:
            super().__init__(
                title=safe_title,
                custom_id=modal_custom_id,
                timeout=None,
            )

        @handle_errors("submitting create hub task modal", context={"component": "discord"})
        async def on_submit(self, modal_interaction: discord.Interaction) -> None:
            if modal_interaction.response.is_done():
                return
            entities = entities_from_shared_fields(
                title=self.title_input.value,
                description=self.details_input.value,
                group=self.group_input.value,
                tags_value=self.tags_input.value,
                due_phrase=self.due_input.value,
            )
            if extra:
                entities = {**extra, **entities}
            await _submit_task_form(
                modal_interaction,
                discord_bot,
                intent=intent,
                entities=entities,
                original_message=original_message,
            )

    return TaskFormModal()


@handle_errors("building custom task modal", default_return=None)
def _build_custom_task_modal(
    user_id: str, discord_bot: DiscordBot | None
) -> discord.ui.Modal | None:
    """Return an empty custom-task modal."""
    return _build_task_modal(user_id, discord_bot)


@handle_errors("building template task modal", default_return=None)
def _build_template_task_modal(
    user_id: str, discord_bot: DiscordBot | None, template_id: str
) -> discord.ui.Modal | None:
    """Return a task modal prefilled from a built-in template."""
    from tasks.task_templates import template_form_defaults

    defaults = template_form_defaults(template_id)
    if not defaults:
        return None
    resolved_id = defaults["template_id"]
    return _build_task_modal(
        user_id,
        discord_bot,
        modal_title=defaults["modal_title"],
        title_default=defaults["title"],
        details_default=defaults["description"],
        due_default=defaults["due"],
        group_default=defaults["group"],
        tags_default=defaults["tags"],
        intent="create_task_from_template",
        original_message=f"task template {resolved_id}",
        extra_entities={"template_ref": resolved_id},
    )


@handle_errors("building quick note modal", default_return=None)
def _build_quick_note_modal(
    user_id: str, discord_bot: DiscordBot | None
) -> discord.ui.Modal | None:
    """Return a Discord modal for capturing a quick note."""
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

        @handle_errors("initializing quick note modal", default_return=None)
        def __init__(self) -> None:
            super().__init__(title="Quick note", timeout=None)

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
    """Return a Discord modal for creating a titled note."""
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

        @handle_errors("initializing new note modal", default_return=None)
        def __init__(self) -> None:
            super().__init__(title="New note", timeout=None)

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
        ("Call", "phone_call", discord.ButtonStyle.primary),
        ("Clean", "cleaning", discord.ButtonStyle.primary),
        ("Forms", "paperwork", discord.ButtonStyle.primary),
    ]
    for label, template_id, style in template_buttons:
        button = discord.ui.Button(
            label=label,
            style=style,
            custom_id=f"{CREATE_HUB_PREFIX}tpl_{template_id}_{user_id}",
            row=0,
        )

        button.callback = _bind_modal_button_callback(
            f"{label} template",
            discord_bot,
            lambda uid, bot, tid=template_id: _build_template_task_modal(uid, bot, tid),
        )
        view.add_item(button)

    custom_task = discord.ui.Button(
        label="Custom task",
        style=discord.ButtonStyle.secondary,
        custom_id=f"{CREATE_HUB_PREFIX}custom_task_{user_id}",
        row=0,
    )

    custom_task.callback = _bind_modal_button_callback(
        "custom task", discord_bot, _build_custom_task_modal
    )
    view.add_item(custom_task)

    quick_note = discord.ui.Button(
        label="Quick note",
        style=discord.ButtonStyle.success,
        custom_id=f"{CREATE_HUB_PREFIX}quick_note_{user_id}",
        row=1,
    )

    quick_note.callback = _bind_modal_button_callback(
        "quick note", discord_bot, _build_quick_note_modal
    )
    view.add_item(quick_note)

    new_note = discord.ui.Button(
        label="New note",
        style=discord.ButtonStyle.success,
        custom_id=f"{CREATE_HUB_PREFIX}new_note_{user_id}",
        row=1,
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
