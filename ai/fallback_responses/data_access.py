# ai/fallback_responses/data_access.py

"""Data access for fallback modules (patchable in tests via ai.fallback_responses)."""

from core import get_user_data
from core.response_tracking import get_recent_responses

__all__ = ["get_recent_responses", "get_user_data"]
