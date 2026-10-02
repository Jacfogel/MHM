"""
Account Management Handler

Channel-agnostic handler for account creation and linking operations.
"""

import secrets
import string
from typing import Any
from core.logger import get_component_logger
from core.error_handling import handle_errors
from core import get_user_id_by_identifier, create_new_user
from core import get_user_data, update_user_account
from core.user_identity import user_display_label
from storage.user_data_operations import update_user_index
from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import (
    InteractionResponse,
    ParsedCommand,
)

logger = get_component_logger("communication_manager")


class AccountManagementHandler(InteractionHandler):
    """Handler for account management interactions"""

    @handle_errors("checking if account handler can handle intent")
    def can_handle(self, intent: str) -> bool:
        """Check if this handler can handle the given intent"""
        return intent in ["create_account", "link_account", "check_account_status"]

    @handle_errors(
        "handling account interaction",
        default_return=InteractionResponse(
            "I'm having trouble with account management right now. Please try again.",
            True,
        ),
    )
    def handle(
        self, user_id: str, parsed_command: ParsedCommand
    ) -> InteractionResponse:
        """Handle account management interactions"""
        intent = parsed_command.intent
        entities = parsed_command.entities

        if intent == "create_account":
            return self._handle_create_account(user_id, entities)
        elif intent == "link_account":
            return self._handle_link_account(user_id, entities)
        elif intent == "check_account_status":
            return self._handle_check_account_status(user_id)
        else:
            return InteractionResponse(
                f"I don't understand that account command. Try: {', '.join(self.get_examples())}",
                True,
            )

    @handle_errors("handling account creation")
    def _handle_create_account(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """
        Handle account creation request.

        Args:
            user_id: The user's internal ID (if they already have one) or channel identifier
            entities: Command entities containing a preferred name and account data

        Returns:
            InteractionResponse with account creation result
        """
        display_name = entities.get("preferred_name") or entities.get("username")
        if not display_name:
            return InteractionResponse(
                "To create an account, please provide the name you would like MHM to use.",
                completed=False,
                suggestions=["Use my Discord display name", "Create account"],
            )

        display_name = str(display_name).strip()
        if len(display_name) > 100:
            return InteractionResponse(
                "❌ Preferred name must be 100 characters or fewer.",
                completed=False,
            )

        # Extract channel-specific identifier (Discord ID, email, etc.)
        channel_identifier = entities.get("channel_identifier", "")
        channel_type = entities.get("channel_type", "discord")

        required_feature_fields = ("tasks_enabled", "checkins_enabled", "messages_enabled")
        missing_feature_fields = [
            field for field in required_feature_fields if field not in entities
        ]
        if missing_feature_fields:
            missing_list = ", ".join(missing_feature_fields)
            return InteractionResponse(
                "To create an account, please choose your feature settings first. "
                f"Missing: {missing_list}.",
                completed=False,
                suggestions=["Enable tasks", "Enable check-ins", "Enable messages"],
            )

        tasks_enabled = entities["tasks_enabled"]
        checkins_enabled = entities["checkins_enabled"]
        messages_enabled = entities["messages_enabled"]
        timezone = entities.get("timezone", "America/Regina")

        try:
            # Categories should be empty list initially (user can add categories later via UI)
            # The messages_enabled flag will be used to set automated_messages feature
            user_data = {
                "preferred_name": display_name,
                "categories": [],  # Start with empty - user can add categories later
                "task_settings": {"enabled": tasks_enabled},
                "checkin_settings": {"enabled": checkins_enabled},
                "channel": {"type": channel_type},
                "timezone": timezone,
                "messages_enabled": messages_enabled,  # Explicit flag for automated_messages feature
            }

            # Add channel-specific identifier
            if channel_type == "discord" and channel_identifier:
                user_data["discord_user_id"] = channel_identifier
            elif channel_type == "email" and channel_identifier:
                user_data["email"] = channel_identifier

            new_user_id = create_new_user(user_data)

            if new_user_id:
                logger.info(
                    f"Created new MHM account: {new_user_id} (channel: {channel_type})"
                )

                return InteractionResponse(
                    f"✅ **Account created successfully!**\n\n"
                    f"MHM will call you **{display_name}**.\n"
                    f"Your account ID is `{new_user_id}`.\n"
                    f"Your account is now linked to your {channel_type} account.\n\n"
                    f"You can now use commands like:\n"
                    f"• `/help` - See all available commands\n"
                    f"• `/profile` - View your profile\n"
                    f"• `create task [description]` - Create a new task\n"
                    f"• `show my tasks` - View your tasks\n\n"
                    f"Welcome to MHM! 🚀",
                    completed=True,
                    rich_data={
                        "type": "account_created",
                        "display_name": display_name,
                        "user_id": new_user_id,
                    },
                )
            else:
                return InteractionResponse(
                    "❌ Failed to create account. Please try again or contact support.",
                    completed=False,
                )
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            return InteractionResponse(
                "❌ An error occurred while creating your account. Please try again.",
                completed=False,
            )

    @handle_errors("handling account linking")
    def _handle_link_account(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """
        Handle account linking request.

        Args:
            user_id: The channel identifier (Discord ID, email, etc.)
            entities: Command entities containing an account identifier and confirmation code

        Returns:
            InteractionResponse with account linking result
        """
        account_identifier = (
            entities.get("account_identifier")
            or entities.get("email")
            or entities.get("username")
        )
        confirmation_code = entities.get("confirmation_code")
        channel_identifier = entities.get("channel_identifier", user_id)
        channel_type = entities.get("channel_type", "discord")

        # Step 1: User provides a canonical ID or contact identifier.
        if not account_identifier:
            return InteractionResponse(
                "To link your account, provide its account ID, email address, Discord ID, or phone number.",
                completed=False,
                suggestions=["Link my account"],
            )

        account_identifier = str(account_identifier).strip()
        existing_user_id = get_user_id_by_identifier(account_identifier)
        if not existing_user_id:
            return InteractionResponse(
                "❌ Account not found. Check the account ID or contact identifier and try again.",
                completed=False,
            )

        # Check if account already has a channel identifier
        user_data_result = get_user_data(existing_user_id, "account")
        account_data = user_data_result.get("account", {})
        context_result = get_user_data(existing_user_id, "context")
        display_label = user_display_label(
            existing_user_id, account_data, context_result.get("context", {})
        )

        # Check for existing link based on channel type
        if channel_type == "discord":
            existing_discord_id = account_data.get("discord_user_id", "")
            if existing_discord_id and existing_discord_id != channel_identifier:
                return InteractionResponse(
                    "❌ This account is already linked to a different Discord account.\n"
                    "If this is your account, please contact support.",
                    completed=False,
                )
        elif channel_type == "email":
            existing_email = account_data.get("email", "")
            if existing_email and existing_email.lower() != channel_identifier.lower():
                return InteractionResponse(
                    "❌ This account is already linked to a different email address.\n"
                    "If this is your account, please contact support.",
                    completed=False,
                )

        # Step 2: User provides confirmation code
        if not confirmation_code:
            # Generate and send confirmation code (module-level helpers below)
            code = _generate_confirmation_code()

            # Store pending operation (in-memory for now, could be moved to a proper store)
            _pending_link_operations[channel_identifier] = {
                "operation_type": "link",
                "account_identifier": account_identifier,
                "user_id": existing_user_id,
                "confirmation_code": code,
                "channel_type": channel_type,
            }

            # Send confirmation code (pass channel_identifier for Discord)
            code_sent = _send_confirmation_code(
                existing_user_id,
                code,
                channel_type,
                channel_identifier=channel_identifier,
            )

            if code_sent:
                return InteractionResponse(
                    "✅ **Confirmation code sent!**\n\n"
                    "A confirmation code has been sent to the email address associated with your MHM account.\n"
                    "Please check your email and enter the code here to complete the linking process.",
                    completed=False,
                    rich_data={
                        "type": "confirmation_code_sent",
                        "account_id": existing_user_id,
                        "channel_type": channel_type,
                    },
                    suggestions=["Enter confirmation code"],
                )
            else:
                return InteractionResponse(
                    "❌ Could not send confirmation code. This account may not have an email address configured.\n"
                    "Please contact support for assistance.",
                    completed=False,
                )

        # Step 3: Verify confirmation code and link account
        pending = _pending_link_operations.get(channel_identifier)

        if not pending or pending["operation_type"] != "link":
            return InteractionResponse(
                "❌ No pending account linking operation found. Please start over.",
                completed=False,
            )

        if confirmation_code.strip() != pending["confirmation_code"]:
            return InteractionResponse(
                f"❌ Invalid confirmation code. Please check your {channel_type} and try again.",
                completed=False,
            )

        # Link the account
        try:
            updates = {}
            if channel_type == "discord":
                updates["discord_user_id"] = channel_identifier
            elif channel_type == "email":
                updates["email"] = channel_identifier

            success = update_user_account(pending["user_id"], updates)

            if not success:
                return InteractionResponse(
                    "❌ Failed to link account. Please try again or contact support.",
                    completed=False,
                )

            try:
                update_user_index(pending["user_id"])
            except Exception as index_error:
                logger.warning(
                    f"Failed to update user index after linking account: {index_error}"
                )

            # Clear pending operation
            del _pending_link_operations[channel_identifier]

            return InteractionResponse(
                f"✅ **Account linked successfully!**\n\n"
                f"Your MHM account for **{display_label}** is now linked to your {channel_type} account.\n\n"
                f"You can now use commands like:\n"
                f"• `/help` - See all available commands\n"
                f"• `/profile` - View your profile\n"
                f"• `create task [description]` - Create a new task\n"
                f"• `show my tasks` - View your tasks\n\n"
                f"Welcome back! 🚀",
                completed=True,
                rich_data={
                    "type": "account_linked",
                    "display_name": display_label,
                    "user_id": pending["user_id"],
                },
            )
        except Exception as e:
            logger.error(f"Error linking account: {e}")
            return InteractionResponse(
                "❌ An error occurred while linking your account. Please try again.",
                completed=False,
            )

    @handle_errors("checking account status")
    def _handle_check_account_status(self, user_id: str) -> InteractionResponse:
        """Check if user has an account linked"""
        internal_user_id = get_user_id_by_identifier(user_id)

        if internal_user_id:
            user_data_result = get_user_data(internal_user_id, "account")
            account_data = user_data_result.get("account", {})
            context_result = get_user_data(internal_user_id, "context")
            display_label = user_display_label(
                internal_user_id, account_data, context_result.get("context", {})
            )

            return InteractionResponse(
                f"✅ You have a MHM account linked!\n"
                f"Account: **{display_label}**\n"
                f"Account ID: `{internal_user_id}`\n"
                f"Use `/profile` to view your profile or `/help` to see available commands.",
                completed=True,
                rich_data={
                    "type": "account_status",
                    "has_account": True,
                    "display_name": display_label,
                    "user_id": internal_user_id,
                },
            )
        else:
            return InteractionResponse(
                "❌ No MHM account found linked to this account.\n"
                "Use the account creation or linking options to get started.",
                completed=False,
                rich_data={"type": "account_status", "has_account": False},
                suggestions=["Create account", "Link account"],
            )

    @handle_errors("getting account handler help")
    def get_help(self) -> str:
        """Get help text for account management commands."""
        return "Account management - create or link your MHM account"

    @handle_errors("getting account handler examples")
    def get_examples(self) -> list[str]:
        """Get example commands for account management."""
        return ["create account", "link account", "check account status"]


# Store pending account operations (confirmation codes, etc.)
# Format: {channel_identifier: {operation_type, account_identifier, user_id, confirmation_code, channel_type}}
_pending_link_operations: dict[str, dict[str, Any]] = {}


@handle_errors("generating confirmation code", default_return="000000")
@handle_errors("generating confirmation code", default_return="000000")
def _generate_confirmation_code() -> str:
    """Generate a 6-digit confirmation code"""
    return "".join(secrets.choice(string.digits) for _ in range(6))


@handle_errors("sending confirmation code", default_return=False)
def _send_confirmation_code(
    user_id: str,
    confirmation_code: str,
    channel_type: str,
    channel_identifier: str | None = None,
) -> bool:
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
        user_data_result = get_user_data(user_id, "account")
        account_data = user_data_result.get("account", {})

        recipient = account_data.get("email", "")
        if not recipient:
            logger.warning(
                f"User {user_id} does not have an email address configured - cannot send confirmation code"
            )
            return False

        # Always send confirmation codes via email for security
        # channel_type is used for message context (which channel is being linked)

        # Send via communication manager
        from communication.core.channel_orchestrator import CommunicationManager

        comm_manager = CommunicationManager()

        if comm_manager:
            message = f"""Hello!

You requested to link your MHM account to {channel_type}.

Your confirmation code is: {confirmation_code}

Enter this code in {channel_type} to complete the linking process.

If you didn't request this, please ignore this message.

Thank you,
MHM Team"""

            # Send via email channel (confirmation codes are always sent via email for security)
            # Use send_message_sync which handles async/sync conversion internally
            # This avoids creating unawaited coroutines and RuntimeWarnings
            success = comm_manager.send_message_sync(
                channel_name="email",
                recipient=recipient,
                message=message,
                message_type="account_linking",
                channel_preference="email",
            )

            if success:
                logger.info(f"Sent confirmation code to {recipient} for user {user_id}")
                return True
            else:
                logger.error(
                    f"Failed to send confirmation code to {recipient} for user {user_id}"
                )
                return False
        else:
            logger.warning(
                "Communication manager not available for sending confirmation code"
            )
            return False

    except Exception as e:
        logger.error(f"Error sending confirmation code for user {user_id}: {e}")
        return False
