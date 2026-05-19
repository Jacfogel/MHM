# ai/fallback_responses/profile_helpers.py

"""User profile helpers for fallback text (names only; no channel logic)."""

import ai.fallback_responses.data_access as data_access
from core.error_handling import handle_errors


@handle_errors("loading user context for fallback", default_return={})
def load_user_context(user_id: str | None) -> dict:
    """Return the user's context dict, or empty dict when unavailable."""
    if not user_id:
        return {}
    context_result = data_access.get_user_data(user_id, "context")
    if not context_result:
        return {}
    return context_result.get("context") or {}


@handle_errors("reading preferred name from context", default_return="")
def preferred_name_from_context(user_context: dict) -> str:
    """Return trimmed preferred name from a user context dict, or empty string."""
    return user_context.get("preferred_name", "").strip()


@handle_errors("building name prefix from context", default_return="")
def name_prefix_from_context(user_context: dict) -> str:
    """Return a greeting prefix like ``'Alex, '`` when a preferred name exists."""
    name = preferred_name_from_context(user_context)
    return f"{name}, " if name else ""


@handle_errors("personalizing fallback with profile name", default_return="")
def personalize_with_profile_name(
    fallback_response: str, context_summary: list[str], profile: dict
) -> str:
    """Inject preferred name into greeting-based fallback responses when available."""
    if not context_summary:
        return fallback_response

    user_name = profile.get("preferred_name", "")
    if user_name and user_name not in fallback_response:
        fallback_response = fallback_response.replace("Hello!", f"Hello {user_name}!")
        fallback_response = fallback_response.replace("Hi!", f"Hi {user_name}!")
    return fallback_response
