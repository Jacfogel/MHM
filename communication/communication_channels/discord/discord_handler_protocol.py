# communication/communication_channels/discord/discord_handler_protocol.py

"""Typing protocol for Discord handler modules (avoids importing bot.py)."""

from __future__ import annotations

from typing import Any, Protocol

import discord

from communication.communication_channels.base.base_channel import ChannelStatus
from communication.communication_channels.discord.discord_connection_status import (
    DiscordConnectionStatus,
)


class DiscordHandlerHost(Protocol):
    """Structural typing surface of ``DiscordBot`` used by extracted handler modules."""

    bot: discord.Client | None
    _on_ready_fired: bool
    _reconnect_attempts: int
    _suggestion_button_payloads: dict[str, Any]

    def get_status(self) -> ChannelStatus:
        """Return the channel lifecycle status for this Discord bot instance."""
        ...

    def _set_status(self, status: ChannelStatus, reason: str | None = None) -> None:
        """Update channel lifecycle status, optionally recording a human-readable reason."""
        ...

    def _shared__update_connection_status(
        self, status: DiscordConnectionStatus, error_info: dict[str, Any] | None = None
    ) -> None:
        """Record detailed Discord connection status and optional diagnostic metadata."""
        ...

    def _schedule_ready_tasks(self, bot: discord.Client) -> None:
        """Schedule post-ready maintenance such as slash-command sync after login."""
        ...

    def _start_discord_webhook_server_for_ready(self) -> None:
        """Start the Discord webhook server once the bot connection is ready."""
        ...

    def _check_dns_resolution(self, hostname: str = "discord.com") -> bool:
        """Return whether DNS resolution succeeds for the given hostname."""
        ...

    def _check_network_connectivity(
        self, hostname: str = "discord.com", port: int = 443, timeout: float = 5.0
    ) -> bool:
        """Return whether a TCP connection to the host/port succeeds within timeout."""
        ...

    def _has_display_rich_data(self, rich_data: dict[str, Any] | None) -> bool:
        """Return whether rich_data contains fields that should render in a Discord embed."""
        ...

    def _create_discord_embed(
        self, message: str, rich_data: dict[str, Any] | None
    ) -> discord.Embed | None:
        """Build a Discord embed from a plain-text message and optional rich_data payload."""
        ...

    def _get_action_row_inputs(
        self,
        suggestions: list[str] | None,
        rich_data: dict[str, Any] | None,
    ) -> tuple[list[str], list[Any]]:
        """Derive button labels and payloads for suggestion or pagination action rows."""
        ...

    def _create_action_row(
        self, button_labels: list[str], button_payloads: list[Any]
    ) -> Any:
        """Create a Discord UI view containing the given suggestion or pagination buttons."""
        ...

    async def _send_to_channel(
        self,
        channel: discord.abc.Messageable,
        message: str,
        rich_data: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
    ) -> bool:
        """Send a message (with optional embed, rich data, and buttons) to a channel."""
        ...
