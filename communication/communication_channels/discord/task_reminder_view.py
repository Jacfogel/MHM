"""
Discord Task Reminder View

Discord-specific UI adapter for task reminder buttons.
"""

import discord
from typing import Optional
from core.logger import get_component_logger
from core.error_handling import handle_errors

logger = get_component_logger('discord')


@handle_errors("creating task reminder view", default_return=None)
def get_task_reminder_view(user_id: str, task_id: str, task_title: str) -> Optional['discord.ui.View']:
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
        
        @discord.ui.button(label="Complete Task", style=discord.ButtonStyle.success, custom_id=f"task_complete_{user_id}_{task_id}")
        @handle_errors("completing task from reminder", context={"component": "discord"})
        async def complete_task_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Handle Complete Task button click"""
            await interaction.response.defer()
            
            # Process complete task command through channel-agnostic pathway
            from communication.message_processing.interaction_manager import handle_user_message
            
            discord_user_id = str(interaction.user.id)
            from core.user_management import get_user_id_by_identifier
            internal_user_id = get_user_id_by_identifier(discord_user_id)
            
            if internal_user_id:
                # Use channel-agnostic pathway with message string
                # Try task_id first, then fall back to task title
                message = f'complete task {self.task_id}'
                response = handle_user_message(internal_user_id, message, "discord")
                await interaction.followup.send(response.message, ephemeral=True)
            else:
                await interaction.followup.send("❌ Could not find your account. Please try again.", ephemeral=True)
        
        @discord.ui.button(label="Remind Me Later", style=discord.ButtonStyle.secondary, custom_id=f"task_remind_later_{user_id}_{task_id}")
        @handle_errors("snoozing task reminder", context={"component": "discord"})
        async def remind_later_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Handle Remind Me Later button click"""
            await interaction.response.defer()
            
            # For now, just acknowledge - could implement snooze functionality later
            await interaction.followup.send("✅ I'll remind you about this task later. You can also use `/tasks` to see all your tasks.", ephemeral=True)
        
        @discord.ui.button(label="More", style=discord.ButtonStyle.secondary, custom_id=f"task_more_{user_id}_{task_id}")
        @handle_errors("showing task reminder help", context={"component": "discord"})
        async def more_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Handle More button click - show additional information"""
            short_id = self.task_id[:8] if len(self.task_id) > 8 else self.task_id
            more_info = (
                f"**Task: {self.task_title}**\n\n"
                f"**To complete this task:**\n"
                f"• Reply: `complete task {short_id}`\n"
                f"• Or: `complete task \"{self.task_title}\"`\n"
                f"• Or: `/tasks` to see all your tasks\n\n"
                f"**Task ID:** `{short_id}`"
            )
            await interaction.response.send_message(more_info, ephemeral=True)
    
    return TaskReminderView(user_id, task_id, task_title)

