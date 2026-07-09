# ai/fallback/__init__.py

"""
Fallback response generation when LM Studio or AI API calls are unavailable.

Ownership: all fallback *content* and routing live under ai/fallback/.
communication/ adapters format and deliver messages only; they must not own
business fallback text or check-in-aware wording.
"""

from core.error_handling import handle_errors
from core.logger import get_component_logger

from ai.fallback.data_access import get_recent_responses, get_user_data
from ai.fallback.categories import FallbackCategory
from ai.fallback.coordinator import build_contextual_fallback
from ai.fallback.context import FallbackContext, build_fallback_context
from ai.fallback.personalized import build_personalized_message
from ai.fallback.profile_helpers import personalize_with_profile_name

logger = get_component_logger("ai")

__all__ = [
    "FallbackCategory",
    "FallbackContext",
    "FallbackResponses",
    "build_contextual_fallback",
    "build_fallback_context",
    "get_fallback_responses",
    "get_recent_responses",
    "get_user_data",
]


class FallbackResponses:
    """Template and data-aware fallback text; does not call LM Studio."""

    @handle_errors(
        "getting contextual fallback",
        default_return="I'd like to help with that! How can I assist you today?",
    )
    def contextual(self, user_prompt: str, user_id: str | None = None) -> str:
        text, _category = build_contextual_fallback(user_prompt, user_id)
        return text

    @handle_errors(
        "getting fallback personalized message",
        default_return="Wishing you a wonderful day! Remember that every small step toward your wellbeing matters.",
    )
    def personalized(self, user_id: str) -> str:
        text, _category = build_personalized_message(user_id)
        return text

    @handle_errors("personalizing fallback with profile name", default_return="")
    def personalize_with_profile_name(
        self, fallback_response: str, context_summary: list[str], profile: dict
    ) -> str:
        return personalize_with_profile_name(
            fallback_response, context_summary, profile
        )


_fallback_responses: FallbackResponses | None = None


@handle_errors("getting fallback responses helper")
def get_fallback_responses() -> FallbackResponses:
    """Return the shared fallback responses helper."""
    global _fallback_responses
    if _fallback_responses is None:
        _fallback_responses = FallbackResponses()
    return _fallback_responses
