"""
Account Management Handler

Channel-agnostic handler for account creation and linking operations.
"""

from typing import Dict, Any, List, Optional
from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.user_management import get_user_id_by_identifier, create_new_user
from core.user_data_handlers import get_user_data, get_all_user_ids, update_user_account
from core.user_data_manager import update_user_index
from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand

logger = get_component_logger('account_handler')


class AccountManagementHandler(InteractionHandler):
    """Handler for account management interactions"""
    
    @handle_errors("checking if account handler can handle intent")
    def can_handle(self, intent: str) -> bool:
        """Check if this handler can handle the given intent"""
        return intent in ['create_account', 'link_account', 'check_account_status']
    
    @handle_errors("handling account interaction", default_return=InteractionResponse("I'm having trouble with account management right now. Please try again.", True))
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        """Handle account management interactions"""
        intent = parsed_command.intent
        entities = parsed_command.entities
        
        if intent == 'create_account':
            return self._handle_create_account(user_id, entities)
        elif intent == 'link_account':
            return self._handle_link_account(user_id, entities)
        elif intent == 'check_account_status':
            return self._handle_check_account_status(user_id)
        else:
            return InteractionResponse(f"I don't understand that account command. Try: {', '.join(self.get_examples())}", True)
    
    @handle_errors("handling account creation")
    def _handle_create_account(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """
        Handle account creation request.
        
        Args:
            user_id: The user's internal ID (if they already have one) or channel identifier
            entities: Command entities containing username and other account data
        
        Returns:
            InteractionResponse with account creation result
        """
        username = entities.get('username')
        if not username:
            return InteractionResponse(
                "To create an account, please provide a username. What username would you like to use?",
                completed=False,
                suggestions=["Use my Discord username", "Create account"]
            )
        
        username = username.strip()
        
        # Validate username
        if len(username) < 3:
            return InteractionResponse(
                "❌ Username must be at least 3 characters long. Please choose a different username.",
                completed=False
            )
        
        # Check if username already exists
        if self._username_exists(username):
            return InteractionResponse(
                f"❌ Username '{username}' is already taken. Please choose a different username.",
                completed=False
            )
        
        # Extract channel-specific identifier (Discord ID, email, etc.)
        channel_identifier = entities.get('channel_identifier', '')
        channel_type = entities.get('channel_type', 'discord')
        
        # Extract feature selection (default to True for backward compatibility)
        tasks_enabled = entities.get('tasks_enabled', True)
        checkins_enabled = entities.get('checkins_enabled', True)
        messages_enabled = entities.get('messages_enabled', False)
        timezone = entities.get('timezone', 'America/Regina')
        
        # Create the account
        try:
            # Categories should be empty list initially (user can add categories later via UI)
            # The messages_enabled flag will be used to set automated_messages feature
            user_data = {
                'internal_username': username,
                'categories': [],  # Start with empty - user can add categories later
                'task_settings': {'enabled': tasks_enabled},
                'checkin_settings': {'enabled': checkins_enabled},
                'channel': {'type': channel_type},
                'timezone': timezone,
                'messages_enabled': messages_enabled  # Explicit flag for automated_messages feature
            }
            
            # Add channel-specific identifier
            if channel_type == 'discord' and channel_identifier:
                user_data['discord_user_id'] = channel_identifier
            elif channel_type == 'email' and channel_identifier:
                user_data['email'] = channel_identifier
            
            new_user_id = create_new_user(user_data)
            
            if new_user_id:
                logger.info(f"Created new MHM account: {username} (user_id: {new_user_id}, channel: {channel_type})")
                
                return InteractionResponse(
                    f"✅ **Account created successfully!**\n\n"
                    f"Your MHM username: `{username}`\n"
                    f"Your account is now linked to your {channel_type} account.\n\n"
                    f"You can now use commands like:\n"
                    f"• `/help` - See all available commands\n"
                    f"• `/profile` - View your profile\n"
                    f"• `create task [description]` - Create a new task\n"
                    f"• `show my tasks` - View your tasks\n\n"
                    f"Welcome to MHM! 🚀",
                    completed=True,
                    rich_data={
                        'type': 'account_created',
                        'username': username,
                        'user_id': new_user_id
                    }
                )
            else:
                return InteractionResponse(
                    "❌ Failed to create account. Please try again or contact support.",
                    completed=False
                )
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            return InteractionResponse(
                "❌ An error occurred while creating your account. Please try again.",
                completed=False
            )
    
    @handle_errors("handling account linking")
    def _handle_link_account(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """
        Handle account linking request.
        
        Args:
            user_id: The channel identifier (Discord ID, email, etc.)
            entities: Command entities containing username and confirmation code
        
        Returns:
            InteractionResponse with account linking result
        """
        username = entities.get('username')
        confirmation_code = entities.get('confirmation_code')
        channel_identifier = entities.get('channel_identifier', user_id)
        channel_type = entities.get('channel_type', 'discord')
        
        # Step 1: User provides username
        if not username:
            return InteractionResponse(
                "To link your account, please provide your existing MHM username.",
                completed=False,
                suggestions=["Link my account"]
            )
        
        username = username.strip()
        
        # Validate username
        if len(username) < 3:
            return InteractionResponse(
                "❌ Username must be at least 3 characters long. Please check your username and try again.",
                completed=False
            )
        
        # Check if username exists
        existing_user_id = self._get_user_id_by_username(username)
        if not existing_user_id:
            return InteractionResponse(
                f"❌ Username '{username}' not found. Please check your username and try again.",
                completed=False
            )
        
        # Check if account already has a channel identifier
        user_data_result = get_user_data(existing_user_id, 'account')
        account_data = user_data_result.get('account', {})
        
        # Check for existing link based on channel type
        if channel_type == 'discord':
            existing_discord_id = account_data.get('discord_user_id', '')
            if existing_discord_id and existing_discord_id != channel_identifier:
                return InteractionResponse(
                    f"❌ This account is already linked to a different Discord account.\n"
                    f"If this is your account, please contact support.",
                    completed=False
                )
        elif channel_type == 'email':
            existing_email = account_data.get('email', '')
            if existing_email and existing_email.lower() != channel_identifier.lower():
                return InteractionResponse(
                    f"❌ This account is already linked to a different email address.\n"
                    f"If this is your account, please contact support.",
                    completed=False
                )
        
        # Step 2: User provides confirmation code
        if not confirmation_code:
            # Generate and send confirmation code
            from communication.command_handlers.account_handler import _generate_confirmation_code, _send_confirmation_code
            code = _generate_confirmation_code()
            
            # Store pending operation (in-memory for now, could be moved to a proper store)
            from communication.command_handlers.account_handler import _pending_link_operations
            _pending_link_operations[channel_identifier] = {
                'operation_type': 'link',
                'username': username,
                'user_id': existing_user_id,
                'confirmation_code': code,
                'channel_type': channel_type
            }
            
            # Send confirmation code (pass channel_identifier for Discord)
            code_sent = _send_confirmation_code(existing_user_id, code, channel_type, channel_identifier=channel_identifier)
            
            if code_sent:
                return InteractionResponse(
                    f"✅ **Confirmation code sent!**\n\n"
                    f"A confirmation code has been sent to the email address associated with your MHM account.\n"
                    f"Please check your email and enter the code here to complete the linking process.",
                    completed=False,
                    rich_data={
                        'type': 'confirmation_code_sent',
                        'username': username,
                        'channel_type': channel_type
                    },
                    suggestions=["Enter confirmation code"]
                )
            else:
                return InteractionResponse(
                    f"❌ Could not send confirmation code. This account may not have an email address configured.\n"
                    f"Please contact support for assistance.",
                    completed=False
                )
        
        # Step 3: Verify confirmation code and link account
        from communication.command_handlers.account_handler import _pending_link_operations
        pending = _pending_link_operations.get(channel_identifier)
        
        if not pending or pending['operation_type'] != 'link':
            return InteractionResponse(
                "❌ No pending account linking operation found. Please start over.",
                completed=False
            )
        
        if confirmation_code.strip() != pending['confirmation_code']:
            return InteractionResponse(
                f"❌ Invalid confirmation code. Please check your {channel_type} and try again.",
                completed=False
            )
        
        # Link the account
        try:
            updates = {}
            if channel_type == 'discord':
                updates['discord_user_id'] = channel_identifier
            elif channel_type == 'email':
                updates['email'] = channel_identifier
            
            success = update_user_account(pending['user_id'], updates)
            
            if not success:
                return InteractionResponse(
                    "❌ Failed to link account. Please try again or contact support.",
                    completed=False
                )
            
            # Update user index
            try:
                update_user_index(pending['user_id'])
            except Exception as index_error:
                logger.warning(f"Failed to update user index after linking account: {index_error}")
            
            # Clear pending operation
            del _pending_link_operations[channel_identifier]
            
            return InteractionResponse(
                f"✅ **Account linked successfully!**\n\n"
                f"Your MHM account (`{username}`) is now linked to your {channel_type} account.\n\n"
                f"You can now use commands like:\n"
                f"• `/help` - See all available commands\n"
                f"• `/profile` - View your profile\n"
                f"• `create task [description]` - Create a new task\n"
                f"• `show my tasks` - View your tasks\n\n"
                f"Welcome back! 🚀",
                completed=True,
                rich_data={
                    'type': 'account_linked',
                    'username': username,
                    'user_id': pending['user_id']
                }
            )
        except Exception as e:
            logger.error(f"Error linking account: {e}")
            return InteractionResponse(
                "❌ An error occurred while linking your account. Please try again.",
                completed=False
            )
    
    @handle_errors("checking account status")
    def _handle_check_account_status(self, user_id: str) -> InteractionResponse:
        """Check if user has an account linked"""
        internal_user_id = get_user_id_by_identifier(user_id)
        
        if internal_user_id:
            user_data_result = get_user_data(internal_user_id, 'account')
            account_data = user_data_result.get('account', {})
            username = account_data.get('internal_username', 'Unknown')
            
            return InteractionResponse(
                f"✅ You have a MHM account linked!\n"
                f"Your account username: `{username}`\n"
                f"Use `/profile` to view your profile or `/help` to see available commands.",
                completed=True,
                rich_data={
                    'type': 'account_status',
                    'has_account': True,
                    'username': username
                }
            )
        else:
            return InteractionResponse(
                "❌ No MHM account found linked to this account.\n"
                "Use the account creation or linking options to get started.",
                completed=False,
                rich_data={
                    'type': 'account_status',
                    'has_account': False
                },
                suggestions=["Create account", "Link account"]
            )
    
    @handle_errors("checking if username exists", default_return=False)
    def _username_exists(self, username: str) -> bool:
        """Check if a username already exists in the system"""
        user_ids = get_all_user_ids()
        for user_id in user_ids:
            user_data_result = get_user_data(user_id, 'account')
            account_data = user_data_result.get('account', {})
            if account_data.get('internal_username', '').lower() == username.lower():
                return True
        return False
    
    @handle_errors("getting user ID by username", default_return=None)
    def _get_user_id_by_username(self, username: str) -> Optional[str]:
        """Get user ID by username"""
        user_ids = get_all_user_ids()
        for user_id in user_ids:
            user_data_result = get_user_data(user_id, 'account')
            account_data = user_data_result.get('account', {})
            if account_data.get('internal_username', '').lower() == username.lower():
                return user_id
        return None
    
    @handle_errors("getting account handler help")
    def get_help(self) -> str:
        return "Account management - create or link your MHM account"
    
    @handle_errors("getting account handler examples")
    def get_examples(self) -> List[str]:
        return [
            "create account",
            "link account",
            "check account status"
        ]


# Module-level utilities for account management
import secrets
import string
import time

# Store pending account operations (confirmation codes, etc.)
# Format: {channel_identifier: {operation_type: str, username: str, user_id: str, confirmation_code: str, timestamp: float}}
_pending_link_operations: Dict[str, Dict[str, Any]] = {}


@handle_errors("generating confirmation code", default_return="000000")
@handle_errors("generating confirmation code", default_return="000000")
def _generate_confirmation_code() -> str:
    """Generate a 6-digit confirmation code"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))


@handle_errors("sending confirmation code", default_return=False)
def _send_confirmation_code(user_id: str, confirmation_code: str, channel_type: str, channel_identifier: str = None) -> bool:
    """
    Send confirmation code via email (for account linking security).
    
    When linking a Discord account to an existing MHM account, the confirmation code
    is sent to the email address associated with the MHM account for security verification.
    
    Args:
        user_id: Internal user ID of the existing MHM account
        confirmation_code: The 6-digit confirmation code
        channel_type: The channel being linked ('discord', 'email', etc.) - used for message context
        channel_identifier: Channel-specific identifier (Discord user ID, etc.) - used for message context only
    """
    try:
        # Get user's email address (confirmation codes are always sent via email for security)
        user_data_result = get_user_data(user_id, 'account')
        account_data = user_data_result.get('account', {})
        
        recipient = account_data.get('email', '')
        if not recipient:
            logger.warning(f"User {user_id} does not have an email address configured - cannot send confirmation code")
            return False
        
        # Always send confirmation codes via email for security
        # channel_type is used for message context (which channel is being linked)
        
        # Send via communication manager
        from communication.core.channel_orchestrator import get_communication_manager
        comm_manager = get_communication_manager()
        
        if comm_manager:
            message = f"""Hello!

You requested to link your MHM account to {channel_type}.

Your confirmation code is: {confirmation_code}

Enter this code in {channel_type} to complete the linking process.

If you didn't request this, please ignore this message.

Thank you,
MHM Team"""
            
            # Send via email channel (confirmation codes are always sent via email for security)
            # Use async helper if available, otherwise sync
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule it
                    success = asyncio.run_coroutine_threadsafe(
                        comm_manager.send_message(
                            channel_name='email',
                            recipient=recipient,
                            message=message,
                            message_type="account_linking",
                            channel_preference='email'
                        ),
                        loop
                    ).result(timeout=10)
                else:
                    success = loop.run_until_complete(
                        comm_manager.send_message(
                            channel_name='email',
                            recipient=recipient,
                            message=message,
                            message_type="account_linking",
                            channel_preference='email'
                        )
                    )
            except Exception as async_error:
                logger.warning(f"Async send failed, trying sync: {async_error}")
                # Fallback to sync if async fails
                success = comm_manager.send_message_sync(
                    channel_name='email',
                    recipient=recipient,
                    message=message,
                    message_type="account_linking",
                    channel_preference='email'
                )
            
            if success:
                logger.info(f"Sent confirmation code to {recipient} for user {user_id}")
                return True
            else:
                logger.warning(f"Failed to send confirmation code to {recipient} for user {user_id}")
                return False
        else:
            logger.warning("Communication manager not available for sending confirmation code")
            return False
            
    except Exception as e:
        logger.error(f"Error sending confirmation code for user {user_id}: {e}")
        return False

