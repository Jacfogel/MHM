"""
Channel-Agnostic Welcome Manager

Handles welcome messages and onboarding tracking across all channels.
"""

from pathlib import Path
from typing import Any
from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.config import BASE_DATA_DIR
from storage.runtime_state_storage import (
    get_runtime_state_path,
    load_runtime_state_json,
    save_runtime_state_json,
)

logger = get_component_logger("communication_manager")


@handle_errors("resolving welcome tracking path", re_raise=True)
def welcome_tracking_json_path() -> Path:
    """Path to welcome-tracking JSON under the current BASE_DATA_DIR (tests may patch BASE_DATA_DIR)."""
    return get_runtime_state_path("welcome_tracking.json", base_dir=BASE_DATA_DIR)


# Import-time snapshot for legacy readers; I/O uses welcome_tracking_json_path().
WELCOME_TRACKING_FILE = welcome_tracking_json_path()


@handle_errors("loading welcome tracking data", default_return={})
def _load_welcome_tracking() -> dict[str, dict[str, Any]]:
    """Load the welcome tracking data."""
    path = welcome_tracking_json_path()
    return load_runtime_state_json(path)


@handle_errors("saving welcome tracking data", default_return=False)
def _save_welcome_tracking(tracking_data: dict[str, dict[str, Any]]) -> bool:
    """Save the welcome tracking data."""
    path = welcome_tracking_json_path()
    return save_runtime_state_json(path, tracking_data)


@handle_errors("checking if user has been welcomed", default_return=False)
def has_been_welcomed(channel_identifier: str, channel_type: str = "discord") -> bool:
    """
    Check if a user has already been sent a welcome message.

    Args:
        channel_identifier: The user's channel-specific identifier (Discord ID, email, etc.)
        channel_type: The type of channel ('discord', 'email', etc.)

    Returns:
        bool: True if user has been welcomed
    """
    tracking_data = _load_welcome_tracking()
    key = f"{channel_type}:{channel_identifier}"
    return key in tracking_data


@handle_errors("marking user as welcomed", default_return=False)
def mark_as_welcomed(channel_identifier: str, channel_type: str = "discord") -> bool:
    """
    Mark a user as having been welcomed.

    Args:
        channel_identifier: The user's channel-specific identifier
        channel_type: The type of channel ('discord', 'email', etc.)

    Returns:
        bool: True if successful
    """
    # Local import to avoid startup-time circular import traps.
    from core.time_utilities import now_timestamp_full, now_timestamp_utc_iso

    tracking_data = _load_welcome_tracking()
    key = f"{channel_type}:{channel_identifier}"

    tracking_data[key] = {
        # Human-readable timestamp preferred for JSONs humans might read.
        # Keep the existing key name to avoid breaking any readers.
        "welcomed_at": now_timestamp_full(),
        # Optional machine-friendly timestamp for sorting/analysis.
        "welcomed_at_iso": now_timestamp_utc_iso(),
        "channel_type": channel_type,
        "welcomed": True,
    }

    return _save_welcome_tracking(tracking_data)


@handle_errors("clearing welcomed status", default_return=False)
def clear_welcomed_status(
    channel_identifier: str, channel_type: str = "discord"
) -> bool:
    """
    Clear the welcomed status for a user (e.g., when they deauthorize).

    Args:
        channel_identifier: The user's channel-specific identifier
        channel_type: The type of channel ('discord', 'email', etc.)

    Returns:
        bool: True if successful
    """
    tracking_data = _load_welcome_tracking()
    key = f"{channel_type}:{channel_identifier}"
    if key in tracking_data:
        del tracking_data[key]
        return _save_welcome_tracking(tracking_data)
    return True  # Already not in the list, so success


@handle_errors("finding retained Discord account for welcome", default_return=None)
def get_returning_discord_user_id(discord_user_id: str) -> str | None:
    """Recognize only a retained account still linked to this Discord identity.

    Welcome history is not identity evidence. Non-creating reads also reject a
    stale index pointing at deleted account data without reconstructing it.
    """
    from core import get_user_id_by_identifier
    from storage.user_data_read import get_user_data

    if not discord_user_id or not str(discord_user_id).isdecimal():
        return None
    user_id = get_user_id_by_identifier(discord_user_id)
    if not user_id:
        return None
    account = get_user_data(user_id, "account", auto_create=False).get("account", {})
    if account and str(account.get("discord_user_id", "")) == str(discord_user_id):
        return user_id
    return None


# not_duplicate: get_welcome_message
@handle_errors("getting welcome message", default_return="")
def get_welcome_message(
    channel_identifier: str,
    channel_type: str = "discord",
    username: str | None = None,
    is_authorization: bool = False,
) -> str:
    """
    Get onboarding copy, or a reconnect acknowledgement for a linked Discord account.

    Args:
        channel_identifier: The user's channel-specific identifier
        channel_type: The type of channel ('discord', 'email', etc.)
        username: Optional username to prefill
        is_authorization: True if this is triggered by app authorization, False for general messages

    Returns:
        str: Welcome message text
    """
    if (is_authorization and channel_type == "discord"
            and get_returning_discord_user_id(channel_identifier)):
        return (
            "👋 **Welcome back to MHM!**\n\n"
            "Your Discord account is still linked. Your saved preferences are ready.\n\n"
            "Try `/tasks`, `/checkin`, or `/help` to continue."
        )

    if is_authorization:
        # User just authorized/connected the app
        message = """👋 **Welcome to MHM (Motivational Health Messages)!**

Thank you for connecting MHM! I'm your personal motivational health assistant, and I'm here to send you encouraging messages, help you manage tasks, check-in with yourself and analyse trends, and provide personalized support.

**To get started, you'll need to create or link a MHM account:**

Use the buttons below to create a new account or link to an existing one.

**Once your account is linked, you can:**

• Create and manage tasks with reminders
• Set up check-ins
• Get personalized AI-powered support
• Manage your mental health goals

**Try these commands:**

• `/help` - See all available commands
• `create task [description]` - Create a new task
• `show my tasks` - View your tasks
• `show my profile` - View your profile (once linked)

Feel free to ask me anything! I'm here to help. 🚀"""
    else:
        # General welcome message
        message = """👋 **Welcome to MHM (Motivational Health Messages)!**

I'm your motivational health assistant, and I'm here to help you manage tasks, check-ins, and more.

**To get started, you'll need a MHM account:**

**Once your account is linked, you can:**

• Create and manage tasks
• Set up reminders
• Start check-ins
• Get personalized support

**Need help?** Just ask! Try commands like:
• `/help` - See available commands
• `show my profile` - View your profile (once linked)

I'll be here when you're ready! 🚀"""

    return message
