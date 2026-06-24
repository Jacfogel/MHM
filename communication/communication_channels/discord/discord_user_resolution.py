"""Shared helpers for resolving MHM user IDs from Discord interactions."""

from __future__ import annotations

import discord

from core.error_handling import handle_errors


@handle_errors("resolving internal user from Discord interaction", default_return=None)
def internal_user_id(interaction: discord.Interaction) -> str | None:
    """Map a Discord interaction to the internal MHM user id."""
    from core import get_user_id_by_identifier

    if not interaction.user:
        return None
    return get_user_id_by_identifier(str(interaction.user.id))
