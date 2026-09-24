"""Buttons for liking or retiring a scheduled Discord message."""

from __future__ import annotations

import asyncio

import discord

from core import get_user_id_by_identifier
from core.error_handling import handle_errors
from core.logger import get_component_logger
from messages.message_reactions import apply_message_reaction

logger = get_component_logger("discord")

_UP_ID = "mhm:message-feedback:up"
_DOWN_ID = "mhm:message-feedback:down"


class MessageFeedbackView(discord.ui.View):
    """Unselected More and Not for me buttons on a scheduled message."""

    @handle_errors("initializing message feedback view", default_return=None)
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="More like this",
        emoji="👍",
        style=discord.ButtonStyle.secondary,
        custom_id=_UP_ID,
    )
    @handle_errors("recording a More like this choice", default_return=None)
    async def more_like_this(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self._choose(interaction, "up")

    @discord.ui.button(
        label="Not for me",
        emoji="👎",
        style=discord.ButtonStyle.secondary,
        custom_id=_DOWN_ID,
    )
    @handle_errors("recording a Not for me choice", default_return=None)
    async def not_for_me(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self._choose(interaction, "down")

    @handle_errors("recording Discord message feedback button", default_return=None)
    async def _choose(self, interaction: discord.Interaction, kind: str) -> None:
        """Record one feedback choice and show it on the buttons."""
        message = interaction.message
        if message is None:
            await interaction.response.send_message(
                "That message is no longer available.", ephemeral=True
            )
            return
        internal_user_id = get_user_id_by_identifier(str(interaction.user.id))
        if not internal_user_id:
            await interaction.response.send_message(
                "I couldn't match this Discord account to MHM.", ephemeral=True
            )
            return
        await interaction.response.defer()
        result = await asyncio.to_thread(
            apply_message_reaction, internal_user_id, str(message.id), kind
        )
        reply = str(result.get("reply") or "").strip()
        if reply:
            await interaction.followup.send(reply)
        for child in self.children:
            if not isinstance(child, discord.ui.Button):
                continue
            child.disabled = True
            if child.custom_id == (_UP_ID if kind == "up" else _DOWN_ID):
                child.style = (
                    discord.ButtonStyle.success
                    if kind == "up"
                    else discord.ButtonStyle.danger
                )
        await message.edit(view=self)


@handle_errors("creating message feedback view", default_return=None)
def message_feedback_view() -> MessageFeedbackView:
    """Return the button row for a scheduled Discord message."""
    return MessageFeedbackView()
