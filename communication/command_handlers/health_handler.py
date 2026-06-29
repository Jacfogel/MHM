# communication/command_handlers/health_handler.py

"""Channel-agnostic Google Health integration commands."""

from __future__ import annotations

from core.config import GOOGLE_HEALTH_ENABLED
from core.error_handling import handle_errors
from core.logger import get_component_logger
from integrations.google_health.user_settings import (
    delete_health_integration,
    enable_health_integration,
    format_status_text,
    get_connect_authorization_url,
    get_connect_readiness,
    get_health_integration_status,
    pause_health_integration,
    run_connect_flow_async,
    sync_health_integration,
)

from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand

logger = get_component_logger("communication_manager")


class HealthHandler(InteractionHandler):
    """Handler for Google Health connect, status, pause, delete, and debug sync."""

    @handle_errors("checking if health handler can handle intent")
    def can_handle(self, intent: str) -> bool:
        return intent in (
            "connect_google_health",
            "google_health_status",
            "pause_google_health",
            "enable_google_health",
            "delete_google_health_data",
            "sync_google_health",
        )

    @handle_errors(
        "handling health interaction",
        default_return=InteractionResponse(
            "I'm having trouble with health settings right now. Please try again.", True
        ),
    )
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        intent = parsed_command.intent
        handlers = {
            "connect_google_health": self._handle_connect,
            "google_health_status": self._handle_status,
            "pause_google_health": self._handle_pause,
            "enable_google_health": self._handle_enable,
            "delete_google_health_data": self._handle_delete,
            "sync_google_health": self._handle_sync,
        }
        handler = handlers.get(intent)
        if handler:
            return handler(user_id)
        return InteractionResponse(
            f"I don't understand that health command. Try: {', '.join(self.get_examples())}",
            True,
        )

    @handle_errors(
        "connecting google health",
        default_return=InteractionResponse(
            "Could not start Google Health connect. Check server logs.", True
        ),
    )
    def _handle_connect(self, user_id: str) -> InteractionResponse:
        if not GOOGLE_HEALTH_ENABLED:
            return InteractionResponse(
                "Google Health integration is not enabled on this server.", True
            )

        ready, error = get_connect_readiness()
        if not ready:
            return InteractionResponse(error, completed=True)

        auth_url = get_connect_authorization_url(user_id)
        run_connect_flow_async(user_id, lambda _ok, _err: None)

        return InteractionResponse(
            "**Connect Google Health (one-time)**\n\n"
            "1. Open this link in your browser:\n"
            f"{auth_url}\n\n"
            "2. Sign in and approve read-only access.\n"
            "3. When the browser says you're connected, you're done — "
            "sync runs automatically on schedule (no daily action needed).\n\n"
            "Use `health status` to check connection after approving.",
            completed=True,
            suggestions=["health status"],
        )

    @handle_errors(
        "showing google health status",
        default_return=InteractionResponse("Could not load health status.", True),
    )
    def _handle_status(self, user_id: str) -> InteractionResponse:
        status = get_health_integration_status(user_id)
        if status is None:
            return InteractionResponse("Could not load health status.", True)
        body = format_status_text(status)
        text = (
            body.replace("Feature:", "**Feature:**", 1)
            .replace("Google account linked:", "**Google account linked:**", 1)
            .replace("Last successful sync:", "**Last successful sync:**", 1)
        )
        return InteractionResponse(text, completed=True)

    @handle_errors(
        "pausing google health",
        default_return=InteractionResponse("Could not pause health personalization.", True),
    )
    def _handle_pause(self, user_id: str) -> InteractionResponse:
        pause_health_integration(user_id)
        return InteractionResponse(
            "Health personalization paused. Your data is kept; sync and tone adjustments stop until you re-enable.",
            completed=True,
            suggestions=["enable health"],
        )

    @handle_errors(
        "enabling google health",
        default_return=InteractionResponse("Could not enable health personalization.", True),
    )
    def _handle_enable(self, user_id: str) -> InteractionResponse:
        ok, message = enable_health_integration(user_id)
        if not ok:
            return InteractionResponse(
                message if message == "Connect Google Health first."
                else message or "Could not enable health personalization.",
                True,
            )
        return InteractionResponse(
            "Health personalization enabled. Sync runs automatically on schedule.",
            completed=True,
        )

    @handle_errors(
        "deleting google health data",
        default_return=InteractionResponse("Could not delete health data.", True),
    )
    def _handle_delete(self, user_id: str) -> InteractionResponse:
        delete_health_integration(user_id)
        return InteractionResponse(
            "Local Google Health data deleted and feature disabled.", completed=True
        )

    @handle_errors(
        "manual health sync",
        default_return=InteractionResponse("Health sync failed.", True),
    )
    def _handle_sync(self, user_id: str) -> InteractionResponse:
        ok = sync_health_integration(user_id)
        if ok:
            return InteractionResponse(
                "Health sync completed (debug). Normal operation is automatic.", completed=True
            )
        return InteractionResponse(
            "Health sync did not complete. Check connection with `health status`.", True
        )

    @handle_errors("building health handler help", default_return="Google Health commands unavailable.")
    def get_help(self) -> str:
        """Return short help text for Google Health commands."""
        return self.get_help_text()

    @handle_errors(
        "building health handler help text",
        default_return="Google Health: connect, status, pause, enable, delete, sync.",
    )
    def get_help_text(self) -> str:
        """Return formatted help for Google Health integration commands."""
        return """**Google Health (optional)**
One-time connect, then automatic daily sync for gentler personalized messages.

• `connect google health` — link your account (once)
• `health status` — connection and last sync
• `pause health` / `enable health`
• `delete health data` — remove local data
• `sync health` — debug only (normally automatic)"""

    @handle_errors("listing health handler examples", default_return=["health status"])
    def get_examples(self) -> list[str]:
        """Return example phrases for Google Health commands."""
        return [
            "connect google health",
            "health status",
            "pause health",
            "enable health",
            "delete health data",
            "sync health",
        ]
