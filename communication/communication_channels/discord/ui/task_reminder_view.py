"""
Discord Task Reminder View

Discord-specific UI adapter for task reminder buttons and reminder snooze choices.
"""

from typing import Optional

import discord

from core.ids import display_short_id
from core.logger import get_component_logger
from core.error_handling import handle_errors

logger = get_component_logger("discord")


@handle_errors("creating task reminder view", default_return=None)
def get_task_reminder_view(
    user_id: str, task_id: str, task_title: str
) -> Optional["discord.ui.View"]:
    """
    Create a Discord View with buttons for task reminder actions.

    Args:
        user_id: The user's internal user ID
        task_id: The task ID
        task_title: The task title

    Returns:
        discord.ui.View with buttons for task reminder actions
    """

    class TaskReminderView(discord.ui.View):
        # ERROR_HANDLING_EXCLUDE: Simple constructor that only sets attributes
        def __init__(self, user_id: str, task_id: str, task_title: str):
            """
            Initialize a Discord task reminder view with buttons.

            Args:
                user_id: The user's internal user ID
                task_id: The task ID to display in the reminder
                task_title: The title of the task to display
            """
            super().__init__(timeout=None)  # No timeout - buttons persist
            self.user_id = user_id
            self.task_id = task_id
            self.task_title = task_title

        @discord.ui.button(
            label="Complete Task",
            style=discord.ButtonStyle.success,
            custom_id=f"task_complete_{user_id}_{task_id}",
        )
        @handle_errors(
            "completing task from reminder", context={"component": "discord"}
        )
        async def complete_task_button(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            """Handle Complete Task button click"""
            await interaction.response.defer()

            from communication.message_processing.interaction_manager import (
                handle_user_message,
            )

            discord_user_id = str(interaction.user.id)
            from core import get_user_id_by_identifier

            internal_user_id = get_user_id_by_identifier(discord_user_id)

            if internal_user_id:
                message = f"complete task {self.task_id}"
                response = handle_user_message(internal_user_id, message, "discord")
                await interaction.followup.send(response.message, ephemeral=True)
            else:
                await interaction.followup.send(
                    "❌ Could not find your account. Please try again.", ephemeral=True
                )

        @discord.ui.button(
            label="Remind Me Later",
            style=discord.ButtonStyle.secondary,
            custom_id=f"task_remind_later_{user_id}_{task_id}",
        )
        @handle_errors("opening task reminder snooze choices", context={"component": "discord"})
        async def remind_later_button(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            """Handle Remind Me Later by asking when to ping again."""
            await interaction.response.defer()

            from communication.message_processing.interaction_manager import (
                handle_user_message,
            )
            from core import get_user_id_by_identifier

            internal_user_id = get_user_id_by_identifier(str(interaction.user.id))
            if not internal_user_id:
                await interaction.followup.send(
                    "❌ Could not find your account. Please try again.", ephemeral=True
                )
                return

            response = handle_user_message(
                internal_user_id, f"snooze task {self.task_id}", "discord"
            )
            view = None
            if not response.completed:
                view = get_task_snooze_choice_view(
                    internal_user_id, self.task_id, self.task_title
                )
            if view is not None:
                await interaction.followup.send(
                    response.message, view=view, ephemeral=True
                )
            else:
                await interaction.followup.send(response.message, ephemeral=True)

        @discord.ui.button(
            label="More",
            style=discord.ButtonStyle.secondary,
            custom_id=f"task_more_{user_id}_{task_id}",
        )
        @handle_errors("showing task reminder help", context={"component": "discord"})
        async def more_button(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            """Handle More button click - show additional information"""
            short_id = display_short_id(
                record_id=self.task_id,
                kind="task",
            ) or (self.task_id[:8] if len(self.task_id) > 8 else self.task_id)
            more_info = (
                f"**Task: {self.task_title}**\n\n"
                f"**To complete this task:**\n"
                f"* Reply: `complete task {short_id}`\n"
                f'* Or: `complete task "{self.task_title}"`\n'
                f"* Or: `/tasks` to see all your tasks\n\n"
                f"**To snooze this reminder** (due date stays the same):\n"
                f"* `snooze task {short_id} for 1 hour`\n"
                f"* `snooze task {short_id} until tonight`\n"
                f"* `snooze task {short_id} until next week`\n"
                f"* `snooze task {short_id} until Friday 3pm`\n\n"
                f"**To skip this time** (repeating tasks move to the next occurrence):\n"
                f"* `skip task {short_id}`\n\n"
                f"**To simplify** (smaller next step, due date stays):\n"
                f"* `simplify task {short_id} to a 5-minute version`\n\n"
                f"**Task ID:** `{short_id}`"
            )
            await interaction.response.send_message(more_info, ephemeral=True)

        @discord.ui.button(
            label="Skip",
            style=discord.ButtonStyle.secondary,
            custom_id=f"task_skip_{user_id}_{task_id}",
            row=1,
        )
        @handle_errors("skipping task occurrence from reminder", context={"component": "discord"})
        async def skip_button(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            """Skip this occurrence through the shared task command path."""
            await interaction.response.defer()
            from communication.message_processing.interaction_manager import (
                handle_user_message,
            )
            from core import get_user_id_by_identifier

            internal_user_id = get_user_id_by_identifier(str(interaction.user.id))
            if not internal_user_id:
                await interaction.followup.send(
                    "❌ Could not find your account. Please try again.", ephemeral=True
                )
                return
            response = handle_user_message(
                internal_user_id, f"skip task {self.task_id}", "discord"
            )
            await interaction.followup.send(response.message, ephemeral=True)

        @discord.ui.button(
            label="Simplify",
            style=discord.ButtonStyle.secondary,
            custom_id=f"task_simplify_{user_id}_{task_id}",
            row=1,
        )
        @handle_errors("opening task simplify modal", context={"component": "discord"})
        async def simplify_button(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            """Ask for a smaller version of the task."""
            await interaction.response.send_modal(
                _TaskSimplifyModal(self.user_id, self.task_id, self.task_title)
            )

    return TaskReminderView(user_id, task_id, task_title)


@handle_errors("creating task reminder snooze choice view", default_return=None)
def get_task_snooze_choice_view(
    user_id: str, task_id: str, task_title: str
) -> Optional["discord.ui.View"]:
    """Create buttons for 1 hour, tonight/tomorrow morning, next week, and custom snooze."""
    from tasks.task_reminder_snooze import tonight_snooze_label

    tonight_label = tonight_snooze_label(user_id)
    tonight_command = (
        "until tomorrow morning"
        if tonight_label.lower().startswith("tomorrow")
        else "until tonight"
    )

    class TaskSnoozeChoiceView(discord.ui.View):
        # ERROR_HANDLING_EXCLUDE: Simple constructor that only sets attributes
        def __init__(self, user_id: str, task_id: str, task_title: str):
            """Store the task to snooze for the choice buttons."""
            super().__init__(timeout=300)
            self.user_id = user_id
            self.task_id = task_id
            self.task_title = task_title

        @handle_errors(
            "running task reminder snooze command", context={"component": "discord"}
        )
        async def _run_snooze_command(
            self, interaction: discord.Interaction, command: str
        ) -> None:
            """Defer and run a channel-agnostic snooze command."""
            await interaction.response.defer()
            from communication.message_processing.interaction_manager import (
                handle_user_message,
            )
            from core import get_user_id_by_identifier

            internal_user_id = get_user_id_by_identifier(str(interaction.user.id))
            if not internal_user_id:
                await interaction.followup.send(
                    "❌ Could not find your account. Please try again.", ephemeral=True
                )
                return
            response = handle_user_message(internal_user_id, command, "discord")
            await interaction.followup.send(response.message, ephemeral=True)

        @discord.ui.button(label="1 hour", style=discord.ButtonStyle.primary)
        @handle_errors("snoozing task reminder 1 hour", context={"component": "discord"})
        async def snooze_one_hour(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            """Snooze the reminder for one hour."""
            await self._run_snooze_command(
                interaction, f"snooze task {self.task_id} for 1 hour"
            )

        @discord.ui.button(label=tonight_label, style=discord.ButtonStyle.primary)
        @handle_errors(
            "snoozing task reminder tonight or morning", context={"component": "discord"}
        )
        async def snooze_tonight(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            """Snooze until tonight, or tomorrow morning when it is already evening."""
            await self._run_snooze_command(
                interaction, f"snooze task {self.task_id} {tonight_command}"
            )

        @discord.ui.button(label="Next week", style=discord.ButtonStyle.primary)
        @handle_errors("snoozing task reminder next week", context={"component": "discord"})
        async def snooze_next_week(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            """Snooze the reminder until next week."""
            await self._run_snooze_command(
                interaction, f"snooze task {self.task_id} until next week"
            )

        @discord.ui.button(label="Custom", style=discord.ButtonStyle.secondary)
        @handle_errors("opening custom task reminder snooze modal", context={"component": "discord"})
        async def snooze_custom(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            """Open a modal so the user can type a custom snooze time."""
            await interaction.response.send_modal(
                _TaskSnoozeCustomModal(self.user_id, self.task_id, self.task_title)
            )

    return TaskSnoozeChoiceView(user_id, task_id, task_title)


class _TaskSnoozeCustomModal(discord.ui.Modal, title="Remind me when?"):
    """Collect a custom snooze time without changing the task due date."""

    when_input = discord.ui.TextInput(
        label="When",
        placeholder="Friday 3pm, in 20 minutes, next Tuesday morning",
        max_length=80,
        required=True,
    )

    # ERROR_HANDLING_EXCLUDE: Simple constructor that only sets attributes
    def __init__(self, user_id: str, task_id: str, task_title: str):
        """Store the task this custom snooze applies to."""
        super().__init__(timeout=300)
        self.user_id = user_id
        self.task_id = task_id
        self.task_title = task_title

    @handle_errors("submitting custom task reminder snooze", context={"component": "discord"})
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Snooze the reminder until the typed time."""
        await interaction.response.defer(ephemeral=True)
        from communication.message_processing.interaction_manager import (
            handle_user_message,
        )
        from core import get_user_id_by_identifier

        internal_user_id = get_user_id_by_identifier(str(interaction.user.id))
        if not internal_user_id:
            await interaction.followup.send(
                "❌ Could not find your account. Please try again.", ephemeral=True
            )
            return
        when = str(self.when_input.value or "").strip()
        response = handle_user_message(
            internal_user_id,
            f"snooze task {self.task_id} until {when}",
            "discord",
        )
        await interaction.followup.send(response.message, ephemeral=True)


class _TaskSimplifyModal(discord.ui.Modal, title="Smaller version?"):
    """Collect a smaller next-step title without changing the due date."""

    title_input = discord.ui.TextInput(
        label="Smaller version",
        placeholder="Wipe the kitchen counter",
        max_length=80,
        required=True,
    )

    # ERROR_HANDLING_EXCLUDE: Simple constructor that only sets attributes
    def __init__(self, user_id: str, task_id: str, task_title: str):
        """Store the task this simplify applies to."""
        super().__init__(timeout=300)
        self.user_id = user_id
        self.task_id = task_id
        self.task_title = task_title

    @handle_errors("submitting simplified task title", context={"component": "discord"})
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Rewrite the task to the typed smaller version."""
        await interaction.response.defer(ephemeral=True)
        from communication.message_processing.interaction_manager import (
            handle_user_message,
        )
        from core import get_user_id_by_identifier

        internal_user_id = get_user_id_by_identifier(str(interaction.user.id))
        if not internal_user_id:
            await interaction.followup.send(
                "❌ Could not find your account. Please try again.", ephemeral=True
            )
            return
        new_title = str(self.title_input.value or "").strip()
        response = handle_user_message(
            internal_user_id,
            f"simplify task {self.task_id} to {new_title}",
            "discord",
        )
        await interaction.followup.send(response.message, ephemeral=True)


@handle_errors("creating task simplify view", default_return=None)
def get_task_simplify_view(
    user_id: str, task_id: str, task_title: str
) -> Optional["discord.ui.View"]:
    """Create a button that opens the simplify modal after a typed simplify command."""

    class TaskSimplifyView(discord.ui.View):
        # ERROR_HANDLING_EXCLUDE: Simple constructor that only sets attributes
        def __init__(self, user_id: str, task_id: str, task_title: str):
            """Store the task to simplify."""
            super().__init__(timeout=300)
            self.user_id = user_id
            self.task_id = task_id
            self.task_title = task_title

        @discord.ui.button(label="Type smaller version", style=discord.ButtonStyle.primary)
        @handle_errors("opening typed-command simplify modal", context={"component": "discord"})
        async def open_simplify_modal(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            """Open the smaller-version modal."""
            await interaction.response.send_modal(
                _TaskSimplifyModal(self.user_id, self.task_id, self.task_title)
            )

    return TaskSimplifyView(user_id, task_id, task_title)
