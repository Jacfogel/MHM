"""Website delivery channel. It stores messages for the signed-in home conversation."""

from typing import Any

from communication.communication_channels.base.base_channel import (
    BaseChannel,
    ChannelConfig,
    ChannelStatus,
    ChannelType,
)
from communication.communication_channels.website.inbox import (
    deliver_to_website,
)
from core.error_handling import handle_errors


class WebsiteBot(BaseChannel):
    """Always-on channel that keeps a copy of outbound messages for the website."""

    @handle_errors("initializing website channel", default_return=None)
    def __init__(self, config: ChannelConfig | None = None):
        super().__init__(config or ChannelConfig(name="website"))

    @property
    @handle_errors("getting website channel type", default_return=ChannelType.SYNC)
    def channel_type(self) -> ChannelType:
        return ChannelType.SYNC

    @handle_errors("initializing website channel", default_return=False)
    async def initialize(self) -> bool:
        self.status = ChannelStatus.READY
        return True

    @handle_errors("shutting down website channel", default_return=False)
    async def shutdown(self) -> bool:
        self.status = ChannelStatus.STOPPED
        return True

    @handle_errors("sending website message", default_return=False)
    async def send_message(self, recipient: str, message: str, **kwargs) -> bool:
        category = kwargs.get("category", "")
        return deliver_to_website(recipient, message, category if isinstance(category, str) else "")

    @handle_errors("receiving website messages", default_return=[])
    async def receive_messages(self) -> list[dict[str, Any]]:
        return []

    @handle_errors("checking website channel health", default_return=False)
    async def health_check(self) -> bool:
        return self.status == ChannelStatus.READY
