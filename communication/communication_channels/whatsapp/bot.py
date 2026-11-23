"""Direct Meta WhatsApp channel lifecycle."""

from communication.communication_channels.base.base_channel import BaseChannel, ChannelConfig, ChannelStatus, ChannelType
from core.error_handling import handle_errors
from core.logger import get_component_logger


class WhatsAppBot(BaseChannel):
    @handle_errors("creating WhatsApp channel", re_raise=True, user_friendly=False)
    def __init__(self, config=None):
        super().__init__(config or ChannelConfig(name="whatsapp", max_retries=1))
        self.logger = get_component_logger("communication_manager")
        self.transport = None
        self.webhook_server = None
        self.last_outbound_message_id = None

    @property
    # error_handling_exclude: pure channel execution model accessor.
    def channel_type(self):
        """Use synchronous transport submission behind the async channel interface."""
        return ChannelType.SYNC

    @handle_errors("initializing WhatsApp channel", default_return=False, retry_after_recovery=False)
    async def initialize(self):
        from core.config import WHATSAPP_WEBHOOK_PORT
        from communication.communication_channels.whatsapp.transport import MetaTransport
        from communication.communication_channels.whatsapp.server import WhatsAppWebhookServer

        if self.is_ready():
            return True
        try:
            self.transport = MetaTransport(self)
            self.webhook_server = WhatsAppWebhookServer(self.transport, WHATSAPP_WEBHOOK_PORT)
            self.webhook_server.start()
        except Exception:
            if self.webhook_server is not None:
                self.webhook_server.server.server_close()
            self.webhook_server = None
            self.transport = None
            self._set_status(ChannelStatus.ERROR, "WhatsApp could not start. Check Meta credentials and the webhook port.")
            return False
        self._set_status(ChannelStatus.READY)
        return True

    @handle_errors("stopping WhatsApp channel", default_return=False, retry_after_recovery=False)
    async def shutdown(self):
        self._set_status(ChannelStatus.STOPPED)
        if self.webhook_server:
            self.webhook_server.stop()
            self.webhook_server = None
        return True

    @handle_errors("sending WhatsApp message", default_return="unconfirmed", retry_after_recovery=False)
    async def send_message(self, recipient, message, **kwargs):
        if not self.is_ready() or self.transport is None:
            self.error_message = "Start and configure WhatsApp before sending a message."
            return False
        return self.transport.send(recipient, message, **kwargs)

    # devtools: intentional[duplicate-functions]: push-channel-receive
    # Push-driven adapters satisfy the channel interface without polling an inbox.
    # error_handling_exclude: push-driven channel does not poll.
    async def receive_messages(self):
        """Return no polled messages because signed webhooks deliver inbound events."""
        return []

    @handle_errors("checking WhatsApp health", default_return=False, user_friendly=False, retry_after_recovery=False)
    async def health_check(self):
        return self.is_ready() and self.webhook_server is not None and self.webhook_server.thread.is_alive()
