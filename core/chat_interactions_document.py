"""
On-disk envelope for chat interactions.

Kept as a leaf so file recovery can build this shape without importing
``profile_v2_io`` (which imports ``error_handling``).
"""

from typing import Any

from core.time_utilities import now_timestamp_full
from storage.user_data_v2_base import SCHEMA_VERSION


# ERROR_HANDLING_EXCLUDE: leaf document builder used during error recovery
def build_chat_interactions_document(interactions: list[Any]) -> dict[str, Any]:
    """Wrap interaction rows in the v2 chat-interactions envelope."""
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_timestamp_full(),
        "interactions": interactions,
    }
