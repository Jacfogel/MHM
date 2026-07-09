"""Compact fallback context built from AIContextEnvelope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.context.analytics import analyze_checkin_entries
from ai.context.service import AIContextEnvelope, build_ai_context_envelope
from ai.fallback.profile_helpers import name_prefix_from_context, preferred_name_from_context
from core.error_handling import handle_errors


@dataclass(frozen=True)
class FallbackContext:
    """Envelope-backed context for deterministic fallback routing."""

    user_id: str | None
    envelope: AIContextEnvelope | None
    preferred_name: str
    name_prefix: str
    action_catalog_summary: str
    is_new_user: bool
    structured: dict[str, Any]

    @property
    @handle_errors("reading check-in rows from fallback context", default_return=[])
    def recent_checkin_rows(self) -> list[dict[str, Any]]:
        """Return recent check-in rows in the shape used by check-in analytics."""
        checkins = self.structured.get("checkins") or {}
        recent = checkins.get("recent") or []
        return [row for row in recent if isinstance(row, dict)]


@handle_errors("building fallback context", default_return=None)
def build_fallback_context(
    user_id: str | None,
    user_prompt: str | None = None,
    *,
    envelope: AIContextEnvelope | None = None,
) -> FallbackContext | None:
    """Build compact fallback context from the canonical AI context envelope."""
    if envelope is None and user_id:
        envelope = build_ai_context_envelope(
            user_id,
            requested_intent="fallback_response",
            prompt_request=user_prompt,
            include_conversation_history=False,
        )

    structured = envelope.structured if envelope else {}
    personal = structured.get("personal_context") or {}
    preferred_name = preferred_name_from_context(personal)
    name_prefix = name_prefix_from_context(personal)

    catalog = structured.get("action_catalog") or {}
    action_catalog_summary = str(catalog.get("summary") or "Actions: none available.")

    conversation = structured.get("conversation") or {}
    recent_chat = conversation.get("recent_chat_interactions") or []
    checkins = structured.get("checkins") or {}
    recent_checkins = checkins.get("recent") or []
    is_new_user = bool(
        user_id
        and not recent_chat
        and not recent_checkins
        and not (structured.get("tasks") or {}).get("active")
    )

    return FallbackContext(
        user_id=user_id,
        envelope=envelope,
        preferred_name=preferred_name,
        name_prefix=name_prefix,
        action_catalog_summary=action_catalog_summary,
        is_new_user=is_new_user,
        structured=structured,
    )


@handle_errors("analyzing check-ins for fallback context", default_return=None)
def analyze_fallback_checkins(context: FallbackContext | None):
    """Return check-in analytics from envelope rows when available."""
    if context is None:
        return None
    rows = context.recent_checkin_rows
    if not rows:
        return None
    return analyze_checkin_entries(rows)
