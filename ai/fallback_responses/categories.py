# ai/fallback_responses/categories.py

"""Deterministic fallback response categories for routing and tests."""

from enum import Enum


class FallbackCategory(str, Enum):
    """Explicit fallback kinds; avoids one undifferentiated keyword cascade."""

    TECHNICAL_UNAVAILABLE = "technical_unavailable"
    NEW_USER_NO_CONTEXT = "new_user_no_context"
    DATA_UNAVAILABLE = "data_unavailable"
    CHECKIN_SUMMARY = "checkin_summary"
    GENERAL_SUPPORT = "general_support"
    PERSONALIZED_MESSAGE = "personalized_message"
