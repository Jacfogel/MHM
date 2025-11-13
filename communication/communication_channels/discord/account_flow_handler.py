"""
Discord Account Flow Handler

Discord-specific UI adapter for account creation and linking flows.
Uses the channel-agnostic AccountManagementHandler for core logic.
"""

import discord
from typing import Optional
from core.logger import get_component_logger
from core.error_handling import handle_errors
from communication.command_handlers.shared_types import ParsedCommand
from communication.command_handlers.account_handler import AccountManagementHandler

logger = get_component_logger('discord')

# Use the channel-agnostic handler for core logic
_account_handler = AccountManagementHandler()


@handle_errors("starting account creation flow", default_return=None)
async def start_account_creation_flow(interaction: discord.Interaction, discord_user_id: str, discord_username: str = None):
    """
    Start the account creation flow via Discord modal.
    
    Args:
        interaction: The Discord interaction (button click)
        discord_user_id: The user's Discord ID
        discord_username: Optional Discord username to prefill
    """
    # Validate interaction type
    if not isinstance(interaction, discord.Interaction):
        logger.error(f"Invalid interaction type: {type(interaction)}, expected discord.Interaction")
        return
    
    try:
        # Check if user already has an account using channel-agnostic handler
        parsed_command = ParsedCommand(
            intent='check_account_status',
            entities={'channel_identifier': discord_user_id, 'channel_type': 'discord'},
            confidence=1.0,
            original_message="check account status"
        )
        status_response = _account_handler.handle(discord_user_id, parsed_command)
        
        if status_response.rich_data and status_response.rich_data.get('has_account'):
            # User already has account - respond with message
            await interaction.response.send_message(
                status_response.message,
                ephemeral=True
            )
            return
        
        # Check if Discord username is available for prefilling (if unique)
        prefilled_username = ""
        if discord_username:
            # Check if Discord username is unique (not already taken in MHM system)
            # Use the handler's internal method to check username availability
            try:
                if not _account_handler._username_exists(discord_username):
                    prefilled_username = discord_username
            except Exception as e:
                logger.debug(f"Could not check username availability for prefilling: {e}")
                # If check fails, don't prefill (safer)
                prefilled_username = ""
        
        # Create a modal for account creation
        class CreateAccountModal(discord.ui.Modal, title="Create MHM Account"):
            username_input = discord.ui.TextInput(
                label="Username",
                placeholder="Enter a unique username for MHM",
                default=prefilled_username,
                min_length=3,
                max_length=50,
                required=True
            )
            
            async def on_submit(self, modal_interaction: discord.Interaction):
                username = self.username_input.value.strip()
                
                # Validate username
                if not username or len(username) < 3:
                    await modal_interaction.response.send_message(
                        "❌ Username must be at least 3 characters long.",
                        ephemeral=True
                    )
                    return
                
                # Username validation is handled by the channel-agnostic handler
                
                # Use channel-agnostic handler for account creation
                try:
                    parsed_command = ParsedCommand(
                        intent='create_account',
                        entities={
                            'username': username,
                            'channel_identifier': discord_user_id,
                            'channel_type': 'discord'
                        },
                        confidence=1.0,
                        original_message=f"create account {username}"
                    )
                    
                    # Use a temporary user_id (the Discord ID) - handler will create new account
                    response = _account_handler.handle(discord_user_id, parsed_command)
                    
                    await modal_interaction.response.send_message(
                        response.message,
                        ephemeral=True
                    )
                    
                    if response.completed:
                        logger.info(f"Created new MHM account for Discord user {discord_user_id}: {username}")
                    else:
                        logger.warning(f"Account creation incomplete for Discord user {discord_user_id}: {response.message}")
                except Exception as e:
                    logger.error(f"Error creating account for Discord user {discord_user_id}: {e}")
                    await modal_interaction.response.send_message(
                        "❌ An error occurred while creating your account. Please try again.",
                        ephemeral=True
                    )
        
        # Send modal via response (modals must be sent via response, not followup)
        await interaction.response.send_modal(CreateAccountModal())
        
    except Exception as e:
        logger.error(f"Error starting account creation flow for {discord_user_id}: {e}")
        try:
            await interaction.followup.send(
                "❌ An error occurred. Please try again.",
                ephemeral=True
            )
        except:
            pass


@handle_errors("starting account linking flow", default_return=None)
async def start_account_linking_flow(interaction: discord.Interaction, discord_user_id: str):
    """
    Start the account linking flow with confirmation code.
    
    Args:
        interaction: The Discord interaction (button click)
        discord_user_id: The user's Discord ID
    """
    try:
        # Check if user already has an account using channel-agnostic handler
        parsed_command = ParsedCommand(
            intent='check_account_status',
            entities={'channel_identifier': discord_user_id, 'channel_type': 'discord'},
            confidence=1.0,
            original_message="check account status"
        )
        status_response = _account_handler.handle(discord_user_id, parsed_command)
        
        if status_response.rich_data and status_response.rich_data.get('has_account'):
            # User already has account - respond with message
            await interaction.response.send_message(
                status_response.message,
                ephemeral=True
            )
            return
        
        # Create a modal for username input
        class LinkAccountModal(discord.ui.Modal, title="Link to Existing Account"):
            username_input = discord.ui.TextInput(
                label="MHM Username",
                placeholder="Enter your existing MHM username",
                min_length=3,
                max_length=50,
                required=True
            )
            
            async def on_submit(self, modal_interaction: discord.Interaction):
                username = self.username_input.value.strip()
                
                # Validate username
                if not username or len(username) < 3:
                    await modal_interaction.response.send_message(
                        "❌ Username must be at least 3 characters long.",
                        ephemeral=True
                    )
                    return
                
                # Use channel-agnostic handler for account linking (step 1: username)
                try:
                    parsed_command = ParsedCommand(
                        intent='link_account',
                        entities={
                            'username': username,
                            'channel_identifier': discord_user_id,
                            'channel_type': 'discord'
                        },
                        confidence=1.0,
                        original_message=f"link account {username}"
                    )
                    
                    response = _account_handler.handle(discord_user_id, parsed_command)
                    
                    if not response.completed:
                        # Handler is requesting confirmation code - show modal for code input
                        if 'confirmation_code_sent' in (response.rich_data or {}).get('type', ''):
                            # Create a modal for confirmation code input
                            class ConfirmLinkModal(discord.ui.Modal, title="Enter Confirmation Code"):
                                code_input = discord.ui.TextInput(
                                    label="Confirmation Code",
                                    placeholder="Enter the 6-digit code from your email",
                                    min_length=6,
                                    max_length=6,
                                    required=True
                                )
                                
                                async def on_submit(self, confirm_interaction: discord.Interaction):
                                    entered_code = self.code_input.value.strip()
                                    
                                    # Use channel-agnostic handler for account linking (step 2: confirmation code)
                                    try:
                                        parsed_command = ParsedCommand(
                                            intent='link_account',
                                            entities={
                                                'username': username,
                                                'confirmation_code': entered_code,
                                                'channel_identifier': discord_user_id,
                                                'channel_type': 'discord'
                                            },
                                            confidence=1.0,
                                            original_message=f"link account {username} {entered_code}"
                                        )
                                        
                                        link_response = _account_handler.handle(discord_user_id, parsed_command)
                                        
                                        await confirm_interaction.response.send_message(
                                            link_response.message,
                                            ephemeral=True
                                        )
                                        
                                        if link_response.completed:
                                            logger.info(f"Linked MHM account {username} to Discord user {discord_user_id}")
                                    except Exception as e:
                                        logger.error(f"Error linking account for Discord user {discord_user_id}: {e}")
                                        await confirm_interaction.response.send_message(
                                            "❌ An error occurred while linking your account. Please try again.",
                                            ephemeral=True
                                        )
                            
                            await modal_interaction.response.send_message(
                                response.message,
                                ephemeral=True
                            )
                            # Can't send modal via followup - need to send message with instructions instead
                            await modal_interaction.followup.send(
                                "Please use `/start` and select 'Link Account' again to enter your confirmation code.",
                                ephemeral=True
                            )
                        else:
                            # Other error or incomplete state
                            await modal_interaction.response.send_message(
                                response.message,
                                ephemeral=True
                            )
                    else:
                        # Account already linked or other completed state
                        await modal_interaction.response.send_message(
                            response.message,
                            ephemeral=True
                        )
                except Exception as e:
                    logger.error(f"Error in account linking flow for Discord user {discord_user_id}: {e}")
                    await modal_interaction.response.send_message(
                        "❌ An error occurred. Please try again.",
                        ephemeral=True
                    )
        
        # Send modal via response (modals must be sent via response, not followup)
        await interaction.response.send_modal(LinkAccountModal())
        
    except Exception as e:
        logger.error(f"Error starting account linking flow for {discord_user_id}: {e}")
        try:
            await interaction.followup.send(
                "❌ An error occurred. Please try again.",
                ephemeral=True
            )
        except:
            pass


# All helper functions have been moved to the channel-agnostic AccountManagementHandler
# This file now only contains Discord-specific UI (modals, buttons, interactions)

