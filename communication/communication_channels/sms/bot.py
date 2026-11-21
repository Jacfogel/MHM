"""SMS channel with separate opt-in simulation and Twilio pilot modes."""

from typing import Any

from communication.communication_channels.base.base_channel import (
    BaseChannel, ChannelConfig, ChannelStatus, ChannelType,
)
from core.error_handling import handle_errors
from communication.communication_channels.sms.phone import normalize_phone




class SmsBot(BaseChannel):
    """Explicit mode selection; simulation never submits to a provider."""

    @handle_errors("initializing SMS object", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def __init__(self, config: ChannelConfig | None = None):
        """Initialize SMS lifecycle state without starting a listener or sending texts."""
        super().__init__(config or ChannelConfig(name="sms"))
        self.outbox: list[dict[str, Any]] = []
        self.transport = None
        self.webhook_server = None
        self.last_outbound_message_id = None

    @property
    # error_handling_exclude: pure framework accessor/no-op; no I/O or mutation.
    def channel_type(self) -> ChannelType:
        """Use the synchronous channel execution model."""
        return ChannelType.SYNC

    @handle_errors("initializing SMS channel", default_return=False)
    async def initialize(self) -> bool:
        """Start exactly one explicitly enabled SMS mode, failing closed on setup errors."""
        from core.config import SMS_SIMULATION_ENABLED, SMS_TWILIO_ENABLED, SMS_WEBHOOK_PORT

        if self.is_ready():
            return True
        if SMS_TWILIO_ENABLED:
            from communication.communication_channels.sms.twilio_transport import TwilioTransport
            from communication.communication_channels.sms.server import SmsWebhookServer

            try:
                self.transport = TwilioTransport(self)
                self.webhook_server = SmsWebhookServer(self.transport, SMS_WEBHOOK_PORT)
                self.webhook_server.start()
            except Exception:
                if self.webhook_server is not None:
                    self.webhook_server.server.server_close()
                    self.webhook_server = None
                self.transport = None
                self._set_status(ChannelStatus.ERROR, "SMS could not start. Check Twilio credentials, the HTTPS URL, and the local webhook port. Enable exactly one SMS mode.")
                return False
            self._set_status(ChannelStatus.READY)
            return True

        if not SMS_SIMULATION_ENABLED:
            self._set_status(ChannelStatus.ERROR, "SMS simulation is disabled. Enable SMS_SIMULATION_ENABLED to use the simulator.")
            return False
        self._set_status(ChannelStatus.READY)
        return True

    @handle_errors("stopping SMS channel", default_return=False, user_friendly=False, retry_after_recovery=False)
    async def shutdown(self) -> bool:
        """Stop accepting SMS work and close the live listener if present."""
        self._set_status(ChannelStatus.STOPPED)
        if self.webhook_server:
            self.webhook_server.stop()
            self.webhook_server = None
        return True

    @handle_errors("sending SMS message", default_return=False)
    async def send_message(self, recipient: str, message: str, **kwargs) -> bool | str:
        """Submit once through Twilio or capture a message in the simulation outbox."""
        if self.transport is not None:
            return self.transport.send(recipient, message, **kwargs)
        number = normalize_phone(recipient)
        if not self.is_ready() or not number or not isinstance(message, str) or not message.strip():
            self.error_message = "No simulated text was saved. Check that the simulator is running, the number includes its country code, and the message has text."
            return False
        # Character chunks exercise long-message handling only. A real provider
        # must apply GSM-7/UCS-2 encoding and concatenated-SMS segment limits.
        self.outbox.append({
            "recipient": number,
            "message": message,
            "segments": [message[i:i + 160] for i in range(0, len(message), 160)],
            "simulated": True,
        })
        self.error_message = None
        return True

    # error_handling_exclude: pure framework accessor/no-op; no I/O or mutation.
    # devtools: intentional[duplicate-functions]: push-channel-receive
    # Push-driven adapters satisfy the channel interface without polling an inbox.
    async def receive_messages(self) -> list[dict[str, Any]]:
        """No external inbox; use simulate_incoming for explicit local input."""
        return []

    # devtools: ignore[unused-functions]: framework invokes this channel/HTTP override dynamically.
    @handle_errors("checking SMS channel health", default_return=False, user_friendly=False, retry_after_recovery=False)
    async def health_check(self) -> bool:
        """Check local readiness and listener liveness without contacting Twilio."""
        return self.is_ready() and (self.webhook_server is None or self.webhook_server.thread.is_alive())

    @handle_errors("simulating inbound SMS", default_return=False)
    async def simulate_incoming(self, sender: str, message: str) -> bool:
        """Resolve a unique saved phone number, run a command, and save its reply.

        This can persist real command changes; use test accounts for simulation.
        Never expose this entry point as an unauthenticated network endpoint.
        """
        from core import get_user_data
        from core.user_management import get_all_user_ids
        from communication.message_processing.interaction_manager import handle_user_message

        if self.transport is not None:
            self.error_message = "Local input simulation is unavailable in live SMS mode."
            return False
        number = normalize_phone(sender)
        if not self.is_ready() or not number or not isinstance(message, str) or not message.strip():
            self.error_message = "The simulated reply was not processed. Start the simulator and provide a country-code number and message text."
            return False
        matches = []
        for user_id in get_all_user_ids():
            account = get_user_data(user_id, "account").get("account") or {}
            if normalize_phone(account.get("phone", "")) == number:
                matches.append(user_id)
        if len(matches) != 1:
            self.error_message = "The simulated reply was not processed. Save this phone number on exactly one MHM account, then try again."
            return False
        self.error_message = "I couldn't confirm the simulated command completed. Check the affected task or check-in before submitting it again."
        response = handle_user_message(matches[0], message, "sms")
        if not response or not response.message or not await self.send_message(number, response.message):
            self.error_message = "The command was processed, but its reply could not be saved in the simulated outbox. Check the affected task or check-in before submitting it again."
            return False
        return True
