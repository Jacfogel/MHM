"""
Discord Welcome Handler

Discord-specific UI adapter for welcome messages.
Uses the channel-agnostic welcome_manager for core logic.
"""

from typing import TYPE_CHECKING, Optional
from core.logger import get_component_logger
from core.error_handling import handle_errors

if TYPE_CHECKING:
    import discord
from communication.core.welcome_manager import (
    has_been_welcomed as _has_been_welcomed,
    mark_as_welcomed as _mark_as_welcomed,
    clear_welcomed_status as _clear_welcomed_status,
    get_welcome_message as _get_welcome_message
)

logger = get_component_logger('discord')


# Discord-specific wrapper functions that delegate to channel-agnostic manager
@handle_errors("checking if Discord user has been welcomed", default_return=False)
def has_been_welcomed(discord_user_id: str) -> bool:
    """Check if a Discord user has already been sent a welcome message."""
    return _has_been_welcomed(discord_user_id, channel_type='discord')


@handle_errors("marking Discord user as welcomed", default_return=False)
def mark_as_welcomed(discord_user_id: str) -> bool:
    """Mark a Discord user as having been welcomed."""
    return _mark_as_welcomed(discord_user_id, channel_type='discord')


@handle_errors("clearing Discord welcomed status", default_return=False)
def clear_welcomed_status(discord_user_id: str) -> bool:
    """Clear the welcomed status for a Discord user (e.g., when they deauthorize)."""
    return _clear_welcomed_status(discord_user_id, channel_type='discord')


@handle_errors("getting Discord welcome message", default_return="")
def get_welcome_message(discord_user_id: str, discord_username: Optional[str] = None, is_authorization: bool = False) -> str:
    """
    Get a welcome message for a new Discord user.
    
    Args:
        discord_user_id: The user's Discord ID
        discord_username: The user's Discord username (optional, for prefilling)
        is_authorization: True if this is triggered by app authorization (DM), False for server messages
    
    Returns:
        str: Welcome message text
    """
    # Get channel-agnostic welcome message
    message = _get_welcome_message(
        channel_identifier=discord_user_id,
        channel_type='discord',
        username=discord_username,
        is_authorization=is_authorization
    )
    
    return message


@handle_errors("creating welcome message view with buttons", default_return=None)
def get_welcome_message_view(discord_user_id: str) -> 'discord.ui.View':
    """
    Create a Discord View with buttons for account creation and linking.
    
    Args:
        discord_user_id: The user's Discord ID
    
    Returns:
        discord.ui.View with buttons for account actions
    """
    import discord
    
    class WelcomeView(discord.ui.View):
        # ERROR_HANDLING_EXCLUDE: Simple constructor that only sets attributes
        def __init__(self, discord_user_id: str):
            """
            Initialize the welcome view with account action buttons.
            
            Creates a Discord UI view with buttons for creating a new account
            or linking to an existing account. Buttons persist without timeout.
            
            Args:
                discord_user_id: The Discord user ID for the welcome session
            """
            super().__init__(timeout=None)  # No timeout - buttons persist
            self.discord_user_id = discord_user_id
        
        @discord.ui.button(label="Create a New Account", style=discord.ButtonStyle.primary, custom_id=f"welcome_create_{discord_user_id}")
        @handle_errors("handling create account button click", default_return=None)
        async def create_account_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Handle Create Account button click"""
            # Start account creation flow (will handle interaction response internally)
            from communication.communication_channels.discord.account_flow_handler import start_account_creation_flow
            discord_username = interaction.user.name if interaction.user else None
            await start_account_creation_flow(interaction, self.discord_user_id, discord_username)
        
        @discord.ui.button(label="Link to Existing Account", style=discord.ButtonStyle.secondary, custom_id=f"welcome_link_{discord_user_id}")
        @handle_errors("handling link account button click", default_return=None)
        async def link_account_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Handle Link Account button click"""
            # Start account linking flow (will handle interaction response internally)
            from communication.communication_channels.discord.account_flow_handler import start_account_linking_flow
            await start_account_linking_flow(interaction, self.discord_user_id)
    
    return WelcomeView(discord_user_id)

