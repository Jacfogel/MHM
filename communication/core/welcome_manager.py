"""
Channel-Agnostic Welcome Manager

Handles welcome messages and onboarding tracking across all channels.
"""

import json
from pathlib import Path
from typing import Any
from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.config import BASE_DATA_DIR

logger = get_component_logger("communication_manager")

# File to track which users have been welcomed (channel-agnostic)
WELCOME_TRACKING_FILE = Path(BASE_DATA_DIR) / "welcome_tracking.json"


@handle_errors("loading welcome tracking data", default_return={})
def _load_welcome_tracking() -> dict[str, dict[str, Any]]:
    """Load the welcome tracking data."""
    if not WELCOME_TRACKING_FILE.exists():
        return {}

    with open(WELCOME_TRACKING_FILE, encoding="utf-8") as f:
        return json.load(f)


@handle_errors("saving welcome tracking data", default_return=False)
def _save_welcome_tracking(tracking_data: dict[str, dict[str, Any]]) -> bool:
    """Save the welcome tracking data."""
    WELCOME_TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WELCOME_TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump(tracking_data, f, indent=2)
    return True


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
    from core.time_utilities import now_timestamp_full
    from datetime import datetime

    tracking_data = _load_welcome_tracking()
    key = f"{channel_type}:{channel_identifier}"

    tracking_data[key] = {
        # Human-readable timestamp preferred for JSONs humans might read.
        # Keep the existing key name to avoid breaking any readers.
        "welcomed_at": now_timestamp_full(),
        # Optional machine-friendly timestamp for sorting/analysis.
        # ISO must come from a datetime object (not string manipulation).
        #
        # NOTE (datetime audit): This does not map cleanly to core/time_utilities.py
        # without introducing new helpers or adopting ISO as a canonical persisted
        # format. Leaving as-is for now and explicitly flagging.
        "welcomed_at_iso": datetime.now().isoformat(),
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


@handle_errors("getting welcome message", default_return="")
def get_welcome_message(
    channel_identifier: str,
    channel_type: str = "discord",
    username: str | None = None,
    is_authorization: bool = False,
) -> str:
    """
    Get a channel-agnostic welcome message for a new user.

    Args:
        channel_identifier: The user's channel-specific identifier
        channel_type: The type of channel ('discord', 'email', etc.)
        username: Optional username to prefill
        is_authorization: True if this is triggered by app authorization, False for general messages

    Returns:
        str: Welcome message text
    """
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
