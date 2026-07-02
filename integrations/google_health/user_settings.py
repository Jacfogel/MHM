"""
Channel-agnostic Google Health user operations (Discord commands + admin UI).
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass

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

logger = get_component_logger("google_health")


@dataclass(frozen=True)
class HealthIntegrationStatus:
    """Read-only snapshot for status displays."""

    feature_state: str
    connected: bool
    last_success_at: str
    has_recent_error: bool


@handle_errors("reading Google Health integration status", default_return=None)
def get_health_integration_status(user_id: str) -> HealthIntegrationStatus | None:
    if not user_id:
        return None
    account = get_user_data(user_id, "account").get("account") or {}
    sync_state = load_sync_state(user_id) or {}
    return HealthIntegrationStatus(
        feature_state=(account.get("features") or {}).get("google_health", "disabled"),
        connected=has_valid_auth(user_id),
        last_success_at=str(sync_state.get("last_success_at") or "never"),
        has_recent_error=bool(sync_state.get("last_error")),
    )


@handle_errors("checking Google Health connect readiness", default_return=(False, ""))
def get_connect_readiness() -> tuple[bool, str]:
    """Return whether the server can start an OAuth connect flow."""
    if not GOOGLE_HEALTH_ENABLED:
        return False, "Google Health integration is not enabled on this server."
    if not GOOGLE_HEALTH_CLIENT_ID or not GOOGLE_HEALTH_CLIENT_SECRET:
        return (
            False,
            "Google Health is not configured (missing GOOGLE_HEALTH_CLIENT_ID "
            "or GOOGLE_HEALTH_CLIENT_SECRET in .env).",
        )
    auth_url = build_authorization_url(state="")
    if not auth_url:
        return False, "Could not build Google Health authorization URL."
    return True, ""


@handle_errors("building Google Health connect URL", default_return="")
def get_connect_authorization_url(user_id: str) -> str:
    """Return the browser OAuth URL for a one-time connect."""
    return build_authorization_url(state=user_id)


@handle_errors("running Google Health connect flow", default_return=(False, "Connect failed"))
def run_connect_flow(user_id: str) -> tuple[bool, str]:
    """
    Run OAuth callback, first sync, and enable google_health (blocking).

    Returns (success, error_message).
    """
    try:
        run_oauth_connect_flow(user_id)
        sync_user_health_data(user_id, force=True)
        account = get_user_data(user_id, "account").get("account") or {}
        features = dict(account.get("features") or {})
        features["google_health"] = "enabled"
        update_user_account(user_id, {"features": features})
        return True, ""
    except Exception as exc:
        logger.warning(f"Google Health connect flow failed for user {user_id}: {exc}")
        return False, str(exc)


@handle_errors("starting async Google Health connect flow", default_return=None)
def run_connect_flow_async(
    user_id: str,
    on_finished: Callable[[bool, str], None],
) -> None:
    """Run connect flow in a background thread."""

    @handle_errors("running async Google Health connect worker", default_return=None)
    def _run() -> None:
        """Background thread target: complete OAuth connect and first sync."""
        success, error = run_connect_flow(user_id)
        on_finished(success, error)

    threading.Thread(target=_run, daemon=True, name=f"google-health-connect-{user_id}").start()


@handle_errors("pausing Google Health integration", default_return=False)
# not_duplicate: google_health_feature_flag_mutators
def pause_health_integration(user_id: str) -> bool:
    account = get_user_data(user_id, "account").get("account") or {}
    features = dict(account.get("features") or {})
    features["google_health"] = "paused"
    return bool(update_user_account(user_id, {"features": features}))


@handle_errors("enabling Google Health integration", default_return=(False, ""))
# not_duplicate: google_health_feature_flag_mutators
def enable_health_integration(user_id: str) -> tuple[bool, str]:
    if not has_valid_auth(user_id):
        return False, "Connect Google Health first."
    account = get_user_data(user_id, "account").get("account") or {}
    features = dict(account.get("features") or {})
    features["google_health"] = "enabled"
    if not update_user_account(user_id, {"features": features}):
        return False, "Could not update account features."
    sync_user_health_data(user_id, force=True)
    return True, ""


@handle_errors("deleting Google Health integration data", default_return=False)
# not_duplicate: google_health_feature_flag_mutators
def delete_health_integration(user_id: str) -> bool:
    delete_user_health_data(user_id)
    account = get_user_data(user_id, "account").get("account") or {}
    features = dict(account.get("features") or {})
    features["google_health"] = "disabled"
    return bool(update_user_account(user_id, {"features": features}))


@handle_errors("syncing Google Health integration data", default_return=False)
def sync_health_integration(user_id: str) -> bool:
    return sync_user_health_data(user_id, force=True)


@handle_errors("formatting Google Health status text", default_return="")
def format_status_text(status: HealthIntegrationStatus) -> str:
    """Plain-text status block for UI or chat."""
    lines = [
        f"Feature: {status.feature_state}",
        f"Google account linked: {'yes' if status.connected else 'no'}",
        f"Last successful sync: {status.last_success_at}",
    ]
    if status.feature_state == "enabled" and status.connected and status.last_success_at == "never":
        lines.append(
            "Sync is scheduled automatically - the first pull may happen shortly after connect."
        )
    elif status.feature_state == "enabled" and not status.connected:
        lines.append("Connect Google Health to link your Google account.")
    if status.has_recent_error:
        lines.append(
            "A recent sync had an issue (logged internally). Messages stay normal until fixed."
        )
    return "\n".join(lines)
