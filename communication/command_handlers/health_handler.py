# communication/command_handlers/health_handler.py

"""Channel-agnostic Google Health integration commands."""

from __future__ import annotations

import threading
from typing import Any

from core import get_user_data, update_user_account
from core.config import (
    GOOGLE_HEALTH_CLIENT_ID,
    GOOGLE_HEALTH_CLIENT_SECRET,
    GOOGLE_HEALTH_ENABLED,
)
from core.error_handling import handle_errors
from core.logger import get_component_logger
from integrations.google_health.auth import build_authorization_url, run_oauth_connect_flow
from integrations.google_health.data_handlers import (
    delete_user_health_data,
    has_valid_auth,
    load_sync_state,
)
from integrations.google_health.sync_manager import sync_user_health_data

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

        result: dict[str, Any] = {"url": "", "error": ""}

        def _run() -> None:
            """Run OAuth callback, first sync, and enable google_health in a background thread."""

            try:

                @handle_errors("capturing OAuth authorization URL")
                def _notify(url: str) -> None:
                    """Store the browser authorization URL from the local OAuth callback."""
                    result["url"] = url

                run_oauth_connect_flow(user_id, on_complete=_notify)
                sync_user_health_data(user_id, force=True)
                account = get_user_data(user_id, "account").get("account") or {}
                features = dict(account.get("features") or {})
                features["google_health"] = "enabled"
                update_user_account(user_id, {"features": features})
            except Exception as exc:
                result["error"] = str(exc)

        auth_url = build_authorization_url(state=user_id)
        if not GOOGLE_HEALTH_CLIENT_ID or not GOOGLE_HEALTH_CLIENT_SECRET or not auth_url:
            return InteractionResponse(
                "Google Health is not configured on this server yet "
                "(missing client ID in `.env`). Ask your admin to set "
                "`GOOGLE_HEALTH_CLIENT_ID` and `GOOGLE_HEALTH_CLIENT_SECRET`.",
                completed=True,
            )

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

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
        account = get_user_data(user_id, "account").get("account") or {}
        state = (account.get("features") or {}).get("google_health", "disabled")
        sync_state = load_sync_state(user_id) or {}
        connected = has_valid_auth(user_id)
        last_sync = sync_state.get("last_success_at") or "never"
        lines = [
            f"**Feature:** {state} (`enabled` = sync + personalization, `paused` = off, `disabled` = off)",
            f"**Google account linked:** {'yes' if connected else 'no'}",
            f"**Last successful sync:** {last_sync}",
        ]
        if state == "enabled" and connected and last_sync == "never":
            lines.append(
                "Sync is scheduled automatically — the first pull may happen shortly after connect."
            )
        elif state == "enabled" and not connected:
            lines.append("Run `connect google health` to link your Google account.")
        if sync_state.get("last_error"):
            lines.append(
                "A recent sync had an issue (logged internally). Messages stay normal until fixed."
            )
        return InteractionResponse("\n".join(lines), completed=True)

    @handle_errors(
        "pausing google health",
        default_return=InteractionResponse("Could not pause health personalization.", True),
    )
    def _handle_pause(self, user_id: str) -> InteractionResponse:
        account = get_user_data(user_id, "account").get("account") or {}
        features = dict(account.get("features") or {})
        features["google_health"] = "paused"
        update_user_account(user_id, {"features": features})
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
        if not has_valid_auth(user_id):
            return InteractionResponse(
                "Connect Google Health first with `connect google health`.", True
            )
        account = get_user_data(user_id, "account").get("account") or {}
        features = dict(account.get("features") or {})
        features["google_health"] = "enabled"
        update_user_account(user_id, {"features": features})
        sync_user_health_data(user_id, force=True)
        return InteractionResponse(
            "Health personalization enabled. Sync runs automatically on schedule.",
            completed=True,
        )

    @handle_errors(
        "deleting google health data",
        default_return=InteractionResponse("Could not delete health data.", True),
    )
    def _handle_delete(self, user_id: str) -> InteractionResponse:
        delete_user_health_data(user_id)
        account = get_user_data(user_id, "account").get("account") or {}
        features = dict(account.get("features") or {})
        features["google_health"] = "disabled"
        update_user_account(user_id, {"features": features})
        return InteractionResponse(
            "Local Google Health data deleted and feature disabled.", completed=True
        )

    @handle_errors(
        "manual health sync",
        default_return=InteractionResponse("Health sync failed.", True),
    )
    def _handle_sync(self, user_id: str) -> InteractionResponse:
        ok = sync_user_health_data(user_id, force=True)
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
