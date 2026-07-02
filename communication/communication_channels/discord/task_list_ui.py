"""Discord task list picker and per-task detail actions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord

from communication.command_handlers.shared_types import InteractionResponse
from communication.communication_channels.discord.discord_command_runner import (
    run_discord_handler_intent,
)
from communication.communication_channels.discord.discord_user_resolution import (
    internal_user_id as _internal_user_id,
)
from communication.communication_channels.discord.discord_response_delivery import (
    deliver_handler_response,
)
from communication.message_processing.conversation_flow_manager import conversation_manager
from communication.message_processing.flows.flow_constants import (
    TASK_DUE_DATE_SUGGESTIONS,
    TASK_PRIORITY_SUGGESTIONS,
)
from core.error_handling import handle_errors
from core.logger import get_component_logger
from tasks import get_task_by_id
from tasks.task_data_handlers import runtime_task_due_date

if TYPE_CHECKING:
    from communication.communication_channels.discord.bot import DiscordBot

logger = get_component_logger("discord")

TASK_LIST_VIEW_TIMEOUT_SECONDS = 600
TASK_LIST_SELECT_PREFIX = "task_list_select_"


@handle_errors("building task flow response", default_return=None)
def _task_flow_response(user_id: str, task_id: str, flow_kind: str) -> InteractionResponse:
    """Start a task follow-up flow and return the first prompt."""
    task = get_task_by_id(user_id, task_id)
    if not task:
        return InteractionResponse("Task not found.", True)

    title = task.get("title", "this task")
    if flow_kind == "due_date":
        conversation_manager.start_task_due_date_flow(
            user_id, task_id, ask_priority=False
        )
        return InteractionResponse(
            f"What due date and/or time for **{title}**?",
            completed=False,
            suggestions=list(TASK_DUE_DATE_SUGGESTIONS),
        )
    if flow_kind == "priority":
        ask_reminders = bool(runtime_task_due_date(task))
        conversation_manager.start_task_priority_flow(
            user_id, task_id, ask_reminders=ask_reminders
        )
        return InteractionResponse(
            f"What priority for **{title}**?",
            completed=False,
            suggestions=list(TASK_PRIORITY_SUGGESTIONS),
        )
    if flow_kind == "reminders":
        if not runtime_task_due_date(task):
            return InteractionResponse(
                f"**{title}** needs a due date before reminders can be set. "
                "Use **Due Date** first.",
                True,
            )
        conversation_manager.start_task_reminder_followup(user_id, task_id)
        reminder_suggestions = (
            conversation_manager._generate_context_aware_reminder_suggestions(
                user_id, task_id
            )
        )
        return InteractionResponse(
            f"Would you like to set custom reminder periods for **{title}**?",
            completed=False,
            suggestions=reminder_suggestions or ["Skip"],
        )
    return InteractionResponse("Unknown action.", True)


@handle_errors("running handler intent from task list UI", default_return=None)
def _run_handler_intent(
    user_id: str, intent: str, entities: dict[str, Any], original_message: str
) -> InteractionResponse:
    return run_discord_handler_intent(
        user_id,
        intent,
        entities,
        original_message,
        missing_handler_message="I could not run that action. Try typing the command instead.",
    )


@handle_errors("formatting task detail message", default_return="Task not found.")
def _format_task_detail(user_id: str, task_id: str) -> str:
    from tasks import task_service

    task = get_task_by_id(user_id, task_id)
    if not task:
        return "Task not found."
    return task_service.format_task_detail_display(task)


class TaskDetailView(discord.ui.View):
    """Ephemeral actions for one task."""

    @handle_errors("initializing task detail view", default_return=None)
    def __init__(self, user_id: str, task_id: str, discord_bot: DiscordBot | None):
        super().__init__(timeout=TASK_LIST_VIEW_TIMEOUT_SECONDS)
        self.user_id = user_id
        self.task_id = task_id
        self.discord_bot = discord_bot

    @handle_errors("starting task detail flow", default_return=None)
    async def _start_flow(
        self, interaction: discord.Interaction, flow_kind: str
    ) -> None:
        internal_id = _internal_user_id(interaction)
        if not internal_id or internal_id != self.user_id:
            await interaction.response.send_message(
                "Account not found.", ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        response = _task_flow_response(internal_id, self.task_id, flow_kind)
        await deliver_handler_response(
            interaction, response, self.discord_bot, ephemeral=True
        )

    @discord.ui.button(label="Due Date", style=discord.ButtonStyle.primary, row=0)
    @handle_errors("task detail due date button", default_return=None)
    async def due_date_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self._start_flow(interaction, "due_date")

    @discord.ui.button(label="Priority", style=discord.ButtonStyle.primary, row=0)
    @handle_errors("task detail priority button", default_return=None)
    async def priority_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self._start_flow(interaction, "priority")

    @discord.ui.button(label="Reminders", style=discord.ButtonStyle.primary, row=0)
    @handle_errors("task detail reminders button", default_return=None)
    async def reminders_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self._start_flow(interaction, "reminders")

    @discord.ui.button(label="Complete", style=discord.ButtonStyle.success, row=0)
    @handle_errors("task detail complete button", default_return=None)
    async def complete_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        internal_id = _internal_user_id(interaction)
        if not internal_id:
            await interaction.response.send_message(
                "Account not found.", ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        response = _run_handler_intent(
            internal_id,
            "complete_task",
            {"task_identifier": self.task_id},
            f"complete task {self.task_id}",
        )
        await interaction.followup.send(response.message, ephemeral=True)

    @discord.ui.button(label="More", style=discord.ButtonStyle.secondary, row=0)
    @handle_errors("task detail more button", default_return=None)
    async def more_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        task = get_task_by_id(self.user_id, self.task_id)
        short_id = (
            str(task.get("short_id") or self.task_id[:8]) if task else self.task_id[:8]
        )
        title = task.get("title", "Task") if task else "Task"
        text = (
            f"**More options for {title}**\n\n"
            f"• `update task {short_id} title ...`\n"
            f"• `delete task {short_id}`\n"
            f"• `show tasks` to return to the list"
        )
        await interaction.response.send_message(text, ephemeral=True)


class TaskListSelect(discord.ui.Select):
    """Dropdown to pick a task from the current list page."""

    @handle_errors("initializing task list select", default_return=None)
    def __init__(
        self,
        user_id: str,
        task_items: list[dict[str, Any]],
        discord_bot: DiscordBot | None,
    ):
        options = []
        for index, item in enumerate(task_items[:25], 1):
            title = str(item.get("title") or "Untitled")
            label = f"{index}. {title}"[:100]
            task_id = str(item.get("task_id") or "")
            short_id = str(item.get("short_id") or "")
            options.append(
                discord.SelectOption(
                    label=label,
                    value=task_id,
                    description=(short_id or task_id[:12])[:100] or None,
                )
            )
        super().__init__(
            placeholder="Select a task for details…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"{TASK_LIST_SELECT_PREFIX}{user_id}",
        )
        self.user_id = user_id
        self.discord_bot = discord_bot

    @handle_errors("task list select callback", default_return=None)
    async def callback(self, interaction: discord.Interaction) -> None:
        internal_id = _internal_user_id(interaction)
        if not internal_id or internal_id != self.user_id:
            await interaction.response.send_message(
                "Account not found.", ephemeral=True
            )
            return
        task_id = self.values[0]
        detail = _format_task_detail(internal_id, task_id)
        view = TaskDetailView(internal_id, task_id, self.discord_bot)
        await interaction.response.send_message(
            detail, view=view, ephemeral=True
        )


@handle_errors("binding task list show-more callback", default_return=None)
def _bind_show_more_callback(
    button: discord.ui.Button,
    payload: dict[str, Any],
    discord_bot: DiscordBot | None,
) -> None:
    @handle_errors("task list show-more button", default_return=None)
    async def callback(interaction: discord.Interaction) -> None:
        internal_id = _internal_user_id(interaction)
        if not internal_id:
            await interaction.response.send_message(
                "Account not found.", ephemeral=True
            )
            return
        await interaction.response.defer()
        intent = str(payload.get("intent") or "list_tasks")
        entities = payload.get("entities") or {}
        if not isinstance(entities, dict):
            entities = {}
        response = _run_handler_intent(
            internal_id, intent, entities, button.label or "Show More"
        )
        await deliver_handler_response(
            interaction, response, discord_bot, ephemeral=False
        )

    button.callback = callback


@handle_errors("creating Discord task list view", default_return=None)
def get_task_list_view(
    user_id: str,
    task_items: list[dict[str, Any]] | None,
    pagination_actions: list[Any] | None,
    discord_bot: DiscordBot | None = None,
) -> discord.ui.View | None:
    """Task picker select plus optional Show More button."""
    items = list(task_items or [])
    actions = list(pagination_actions or [])
    if not items and not actions:
        return None

    view = discord.ui.View(timeout=TASK_LIST_VIEW_TIMEOUT_SECONDS)
    if items:
        view.add_item(TaskListSelect(user_id, items, discord_bot))

    if actions and discord_bot is not None:
        button_data = discord_bot._pagination_action_button_data(actions[0])
        if button_data:
            label, payload = button_data
            button = discord.ui.Button(
                label=label[:80],
                style=discord.ButtonStyle.primary,
                custom_id=f"task_list_more_{user_id}_{payload.get('entities', {}).get('offset', 0)}",
            )
            _bind_show_more_callback(button, payload, discord_bot)
            view.add_item(button)

    return view
