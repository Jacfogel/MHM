"""
Channel notifications for Google Health integration events.
"""

from __future__ import annotations

from core import get_user_data
from core.error_handling import handle_errors
from core.logger import get_component_logger
from integrations.google_health.testing import is_google_health_testing_mode

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
    "invalid or revoked",
    "authentication failed",
    "unauthenticated",
)


@handle_errors("checking auth sync failure", default_return=False)
def is_auth_sync_failure(error: str) -> bool:
    """Return True when a sync error indicates OAuth/token refresh failure."""
    lowered = (error or "").lower()
    return any(marker in lowered for marker in _AUTH_FAILURE_MARKERS)


@handle_errors("sending Google Health reconnect notice", default_return=False)
def send_reconnect_notice(user_id: str) -> bool:
    """Attempt primary delivery; persisted health state owns notification retries."""
    if is_google_health_testing_mode():
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

    from communication.core.message_send_result import CHANNEL_SEND_UNCONFIRMED

    success = comm_manager.send_message_sync(
        messaging_service,
        recipient,
        RECONNECT_NOTICE_TEXT,
        user_id=user_id,
        category="health",
        _queue_on_failure=False,
    )
    if success is True or success == CHANNEL_SEND_UNCONFIRMED:
        logger.info(f"Sent Google Health reconnect notice to user {user_id}")
        return True
    logger.warning(
        f"Failed to send Google Health reconnect notice to user {user_id}"
    )
    return False


@handle_errors("maybe sending Google Health reconnect notice", default_return=None)
def maybe_send_reconnect_notice(
    user_id: str, sync_state: dict, error: str
) -> dict:
    """
    Deliver independently to the website and primary channel once per auth failure.

    Persist the returned state so incomplete delivery survives service restarts.
    """
    state = dict(sync_state or {})
    if not is_auth_sync_failure(error):
        return state
    if (
        not state.get("reconnect_notice_website_sent")
        and not is_google_health_testing_mode()
    ):
        from communication.communication_channels.website.inbox import deliver_to_website

        if deliver_to_website(user_id, RECONNECT_NOTICE_TEXT, "health"):
            state["reconnect_notice_website_sent"] = True
    if not state.get("reconnect_notice_sent"):
        preferences = get_user_data(user_id, "preferences").get("preferences") or {}
        if (preferences.get("channel") or {}).get("type") == "website":
            state["reconnect_notice_sent"] = bool(
                state.get("reconnect_notice_website_sent")
            )
        elif send_reconnect_notice(user_id):
            state["reconnect_notice_sent"] = True
    return state
