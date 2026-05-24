"""Registry for optional channel interaction views."""

from __future__ import annotations

import importlib
from typing import Any

from core.error_handling import handle_errors


@handle_errors("creating channel interaction view", default_return=None)
def create_interaction_view(
    channel_name: str,
    view_type: str,
    user_id: str,
    **kwargs: Any,
) -> Any | None:
    """Create a channel-specific interaction view when the channel supports it."""
    module = importlib.import_module(
        f"communication.communication_channels.{channel_name}.interaction_views"
    )
    factory = getattr(module, f"create_{view_type}_view", None)
    if not callable(factory):
        return None
    return factory(user_id, **kwargs)
