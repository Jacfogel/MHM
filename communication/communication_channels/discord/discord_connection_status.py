# communication/communication_channels/discord/discord_connection_status.py

import enum


class DiscordConnectionStatus(enum.Enum):
    """Detailed Discord connection status for better error reporting."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DNS_FAILURE = "dns_failure"
    NETWORK_FAILURE = "network_failure"
    AUTH_FAILURE = "authentication_failure"
    RATE_LIMITED = "rate_limited"
    GATEWAY_ERROR = "gateway_error"
    UNKNOWN_ERROR = "unknown_error"
