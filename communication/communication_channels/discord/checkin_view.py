"""
Discord Check-in View

Discord-specific UI adapter for check-in flow buttons.
"""

import discord
from typing import Optional
from core.logger import get_component_logger
from core.error_handling import handle_errors

logger = get_component_logger('discord')


@handle_errors("creating check-in view", default_return=None)
def get_checkin_view(user_id: str) -> Optional['discord.ui.View']:
    """
    Create a Discord View with buttons for check-in flow.
    
    Args:
        user_id: The user's internal user ID
    
    Returns:
        discord.ui.View with buttons for check-in actions
    """
    class CheckinView(discord.ui.View):
        # ERROR_HANDLING_EXCLUDE: Simple constructor that only sets attributes
        def __init__(self, user_id: str):
            super().__init__(timeout=None)  # No timeout - buttons persist
            self.user_id = user_id
        
        @discord.ui.button(label="Cancel Check-in", style=discord.ButtonStyle.danger, custom_id=f"checkin_cancel_{user_id}")
        @handle_errors("canceling check-in", context={"component": "discord"})
        async def cancel_checkin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Handle Cancel Check-in button click"""
            await interaction.response.defer()
            
            # Process cancel command through channel-agnostic pathway
            from communication.message_processing.interaction_manager import handle_user_message
            
            discord_user_id = str(interaction.user.id)
            from core.user_management import get_user_id_by_identifier
            internal_user_id = get_user_id_by_identifier(discord_user_id)
            
            if internal_user_id:
                # Use channel-agnostic pathway with message string
                response = handle_user_message(internal_user_id, "/cancel", "discord")
                await interaction.followup.send(response.message, ephemeral=True)
            else:
                await interaction.followup.send("❌ Could not find your account. Please try again.", ephemeral=True)
        
        @discord.ui.button(label="Skip Question", style=discord.ButtonStyle.secondary, custom_id=f"checkin_skip_{user_id}")
        @handle_errors("skipping check-in question", context={"component": "discord"})
        async def skip_question_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Handle Skip Question button click"""
            await interaction.response.defer()
            
            # Process skip command through channel-agnostic pathway
            from communication.message_processing.interaction_manager import handle_user_message
            
            discord_user_id = str(interaction.user.id)
            from core.user_management import get_user_id_by_identifier
            internal_user_id = get_user_id_by_identifier(discord_user_id)
            
            if internal_user_id:
                # Use channel-agnostic pathway with message string
                response = handle_user_message(internal_user_id, "skip", "discord")
                await interaction.followup.send(response.message, ephemeral=True)
            else:
                await interaction.followup.send("❌ Could not find your account. Please try again.", ephemeral=True)
        
        @discord.ui.button(label="More", style=discord.ButtonStyle.secondary, custom_id=f"checkin_more_{user_id}")
        @handle_errors("showing check-in help", context={"component": "discord"})
        async def more_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Handle More button click - show additional information"""
            more_info = (
                "**Check-in Help:**\n\n"
                "• You can answer with numbers (1-5), words like 'three and a half', or type 'skip' to skip any question\n"
                "• Type `/cancel` anytime to exit the check-in\n"
                "• Type `/checkin` anytime to start a new check-in\n"
                "• Your answers help me understand how you're doing and provide better support"
            )
            await interaction.response.send_message(more_info, ephemeral=True)
    
    return CheckinView(user_id)

