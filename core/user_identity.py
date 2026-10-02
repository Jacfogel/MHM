"""Canonical user identity and display-label helpers.

User identity is the account UUID. Human-facing labels come from profile context
or contact information and are never used as storage identifiers.
"""

from __future__ import annotations

from typing import Any

from core.error_handling import handle_errors


@handle_errors("selecting account contact label", default_return="")
def account_contact_label(account: dict[str, Any] | None) -> str:
    """Return the first useful contact label from an account document."""
    if not isinstance(account, dict):
        return ""
    for field in ("email", "discord_username", "phone", "discord_user_id", "chat_id"):
        value = str(account.get(field) or "").strip()
        if value:
            return value
    return ""


@handle_errors("building user display label", default_return="Unknown")
def user_display_label(
    user_id: str,
    account: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> str:
    """Return preferred name, contact label, or the canonical UUID for display."""
    if isinstance(context, dict):
        preferred_name = str(context.get("preferred_name") or "").strip()
        if preferred_name:
            return preferred_name
    return account_contact_label(account) or str(user_id or "").strip() or "Unknown"
