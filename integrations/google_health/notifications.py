"""
Channel notifications for Google Health integration events.
"""

from __future__ import annotations

import os

from core import get_user_data
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("google_health")

RECONNECT_NOTICE_TEXT = (
    "Heads up - I couldn't refresh your Google Health connection, "
    "so health sync is paused.\n\n"
    "When you're ready, run **connect google health** once to link again. "
    "No rush."
)

_AUTH_FAILURE_MARKERS = (
    "access token",
    "refresh token",
    "token refresh",
    "reconnect required",
    "unable to obtain valid access token",
)


@handle_errors("checking auth sync failure", default_return=False)
def is_auth_sync_failure(error: str) -> bool:
    """Return True when a sync error indicates OAuth/token refresh failure."""
    lowered = (error or "").lower()
    return any(marker in lowered for marker in _AUTH_FAILURE_MARKERS)


@handle_errors("sending Google Health reconnect notice", default_return=False)
def send_reconnect_notice(user_id: str) -> bool:
    """Send a one-time low-key reconnect message on the user's primary channel."""
    if os.getenv("MHM_TESTING") == "1":
        logger.debug(f"Skipping reconnect notice in testing mode for user {user_id}")
        return False

    prefs_result = get_user_data(user_id, "preferences", normalize_on_read=True)
    preferences = prefs_result.get("preferences")
    if not preferences:
        logger.warning(
            f"Cannot send Google Health reconnect notice - no preferences for {user_id}"
        )
        return False

    messaging_service = preferences.get("channel", {}).get("type")
    if not messaging_service:
        logger.warning(
            f"Cannot send Google Health reconnect notice - no channel for {user_id}"
        )
        return False

    from communication.core.channel_orchestrator import CommunicationManager
    from communication.delivery.recipient_resolver import RecipientResolver

    comm_manager = CommunicationManager()
    recipient = RecipientResolver().get_recipient_for_service(
        user_id, messaging_service, preferences
    )
    if not recipient:
        logger.warning(
            f"Cannot send Google Health reconnect notice - no recipient for {user_id}"
        )
        return False

    success = comm_manager.send_message_sync(
        messaging_service,
        recipient,
        RECONNECT_NOTICE_TEXT,
        user_id=user_id,
        category="health",
    )
    if success:
        logger.info(f"Sent Google Health reconnect notice to user {user_id}")
    else:
        logger.warning(
            f"Failed to send Google Health reconnect notice to user {user_id}"
        )
    return bool(success)


@handle_errors("maybe sending Google Health reconnect notice", default_return=None)
def maybe_send_reconnect_notice(
    user_id: str, sync_state: dict, error: str
) -> dict:
    """
    Send reconnect notice once when auto-pausing after auth failures.

    Returns updated sync_state (may set reconnect_notice_sent).
    """
    state = dict(sync_state or {})
    if state.get("reconnect_notice_sent"):
        return state
    if not is_auth_sync_failure(error):
        return state
    if send_reconnect_notice(user_id):
        state["reconnect_notice_sent"] = True
    return state
