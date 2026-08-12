"""Discord network diagnostics, connection state, and reconnection helpers."""

from __future__ import annotations

import asyncio
import socket
import time
from collections.abc import Callable
from typing import Any

from communication.communication_channels.base.base_channel import ChannelStatus
from communication.communication_channels.discord.events.status import (
    DiscordConnectionStatus,
)
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("discord")


class DiscordConnectionHealthMixin:
    """Connection-health surface for the Discord bot host."""

    bot: Any
    _connection_status: DiscordConnectionStatus
    _detailed_error_info: dict[str, Any]
    _health_check_interval: int
    _last_health_check: float
    _last_reconnect_time: float
    _max_reconnect_attempts: int
    _reconnect_attempts: int
    _reconnect_cooldown: float
    _starting: bool
    # Provided by BaseChannel when mixed into DiscordBot (typed for Pyright only).
    get_status: Callable[[], ChannelStatus]
    _set_status: Callable[..., None]

    @handle_errors("checking DNS resolution", default_return=False)
    def _check_dns_resolution(self, hostname: str = "discord.com") -> bool:
        if not hostname or not isinstance(hostname, str) or not hostname.strip():
            logger.error(f"Invalid hostname: {hostname}")
            return False
        alternative_dns_servers = [
            "8.8.8.8",
            "1.1.1.1",
            "208.67.222.222",
            "9.9.9.9",
        ]
        try:
            socket.gethostbyname(hostname)
            self._dns_success_count = getattr(self, "_dns_success_count", 0) + 1
            if self._dns_success_count % 60 == 0:
                logger.debug(
                    f"Primary DNS resolution successful for {hostname} "
                    f"(check #{self._dns_success_count})"
                )
            return True
        except socket.gaierror as exc:
            primary_error = {
                "hostname": hostname,
                "error_code": exc.errno,
                "error_message": str(exc),
                "timestamp": time.time(),
                "dns_server": "system_default",
            }
            logger.warning(f"Primary DNS failed for {hostname}: {exc}")
            for dns_server in alternative_dns_servers:
                try:
                    logger.info(
                        f"Trying alternative DNS server {dns_server} for {hostname}"
                    )
                    import dns.resolver

                    resolver = dns.resolver.Resolver()
                    resolver.nameservers = [dns_server]
                    resolver.timeout = 5
                    resolver.lifetime = 10
                    answers = resolver.resolve(hostname, "A")
                    if answers:
                        ip_address = str(answers[0])
                        logger.info(
                            f"Successfully resolved {hostname} to {ip_address} "
                            f"using {dns_server}"
                        )
                        self._detailed_error_info["dns_error"] = {
                            "hostname": hostname,
                            "primary_error": primary_error,
                            "resolved_with": dns_server,
                            "resolved_ip": ip_address,
                            "timestamp": time.time(),
                        }
                        return True
                except Exception as alt_exc:
                    logger.debug(
                        f"Alternative DNS {dns_server} also failed: {alt_exc}"
                    )
            self._detailed_error_info["dns_error"] = {
                "hostname": hostname,
                "primary_error": primary_error,
                "alternative_dns_failed": alternative_dns_servers,
                "timestamp": time.time(),
            }
            logger.error(f"All DNS servers failed for {hostname}")
            self._connection_status = DiscordConnectionStatus.DNS_FAILURE
            return False

    @handle_errors("checking network connectivity", default_return=False)
    def _check_network_connectivity(
        self, hostname: str = "discord.com", port: int = 443
    ) -> bool:
        if not hostname or not isinstance(hostname, str) or not hostname.strip():
            logger.error(f"Invalid hostname: {hostname}")
            return False
        if not isinstance(port, int) or port < 1 or port > 65535:
            logger.error(f"Invalid port: {port}")
            return False
        endpoints = [
            ("discord.com", 443),
            ("gateway.discord.gg", 443),
            ("gateway-us-east1-b.discord.gg", 443),
            ("gateway-us-east1-c.discord.gg", 443),
            ("gateway-us-east1-d.discord.gg", 443),
            ("gateway-us-east1-a.discord.gg", 443),
        ]
        if hostname != "discord.com":
            endpoints.insert(0, (hostname, port))
        for endpoint_hostname, endpoint_port in endpoints:
            try:
                socket.create_connection((endpoint_hostname, endpoint_port), timeout=5)
                self._network_success_count = (
                    getattr(self, "_network_success_count", 0) + 1
                )
                if self._network_success_count % 60 == 0:
                    logger.debug(
                        f"Network connectivity successful to "
                        f"{endpoint_hostname}:{endpoint_port} "
                        f"(check #{self._network_success_count})"
                    )
                return True
            except (TimeoutError, socket.gaierror, OSError) as exc:
                logger.debug(
                    f"Network connectivity failed to "
                    f"{endpoint_hostname}:{endpoint_port} - {exc}"
                )
        self._detailed_error_info["network_error"] = {
            "hostname": hostname,
            "port": port,
            "endpoints_tried": endpoints,
            "error_type": "all_endpoints_failed",
            "error_message": "All Discord endpoints failed connectivity test",
            "timestamp": time.time(),
        }
        logger.error("All Discord endpoints failed network connectivity test")
        self._connection_status = DiscordConnectionStatus.NETWORK_FAILURE
        return False

    @handle_errors("waiting for network recovery", default_return=False)
    def _wait_for_network_recovery(self, max_wait: int = 300) -> bool:
        if not isinstance(max_wait, int) or max_wait < 0:
            logger.error(f"Invalid max_wait: {max_wait}")
            return False
        logger.info(f"Waiting for network connectivity to recover (max {max_wait}s)...")
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if self._check_dns_resolution() and self._check_network_connectivity():
                logger.info("Network connectivity recovered successfully")
                self._connection_status = DiscordConnectionStatus.INITIALIZING
                return True
            time.sleep(10)
        logger.error(f"Network connectivity did not recover within {max_wait} seconds")
        return False

    @handle_errors("getting detailed connection status", default_return={})
    def _get_detailed_connection_status(self) -> dict[str, Any]:
        status_info = {
            "connection_status": self._connection_status.value,
            "bot_initialized": self.bot is not None,
            "bot_ready": self.bot.is_ready() if self.bot else False,
            "bot_closed": self.bot.is_closed() if self.bot else True,
            "reconnect_attempts": self._reconnect_attempts,
            "max_reconnect_attempts": self._max_reconnect_attempts,
            "last_reconnect_time": self._last_reconnect_time,
            "dns_resolution": self._check_dns_resolution(),
            "network_connectivity": self._check_network_connectivity(),
            "detailed_errors": self._detailed_error_info.copy(),
            "timestamp": time.time(),
        }
        if self.bot:
            try:
                status_info["latency"] = self.bot.latency
                status_info["guild_count"] = len(self.bot.guilds)
            except Exception as exc:
                status_info["discord_status_error"] = str(exc)
        return status_info

    @handle_errors("updating connection status", default_return=None)
    def _shared__update_connection_status(
        self,
        status: DiscordConnectionStatus,
        error_info: dict[str, Any] | None = None,
    ) -> None:
        if self._connection_status != status:
            self._connection_status = status
            if error_info:
                self._detailed_error_info.update(error_info)
            logger.info(f"Discord connection status changed to: {status.value}")
            if error_info:
                logger.debug(f"Connection error details: {error_info}")
        elif error_info:
            self._detailed_error_info.update(error_info)

    @handle_errors("checking network health", default_return=False)
    def _check_network_health(self) -> bool:
        logger.debug("Performing network health check...")
        if not self._check_dns_resolution():
            logger.warning("DNS resolution failed during health check")
            return False
        if not self._check_network_connectivity():
            logger.warning("Network connectivity failed during health check")
            return False
        if self.bot and hasattr(self.bot, "latency"):
            try:
                latency = self.bot.latency
                if latency > 1.0:
                    logger.warning(f"High Discord latency detected: {latency:.3f}s")
                    return False
                logger.debug(f"Discord latency: {latency:.3f}s")
            except Exception as exc:
                logger.debug(f"Could not check Discord latency: {exc}")
        logger.debug("Network health check passed")
        return True

    @handle_errors("checking if should attempt reconnection", default_return=False)
    def _should_attempt_reconnection(self) -> bool:
        current_time = time.time()
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.warning(
                f"Maximum reconnection attempts ({self._max_reconnect_attempts}) exceeded"
            )
            return False
        if current_time - self._last_reconnect_time < self._reconnect_cooldown:
            remaining = self._reconnect_cooldown - (
                current_time - self._last_reconnect_time
            )
            logger.debug(f"Reconnection cooldown active, {remaining:.1f}s remaining")
            return False
        if not self._check_network_health():
            logger.info("Network health check failed, skipping reconnection attempt")
            return False
        return True

    @handle_errors("performing Discord health check", default_return=False)
    async def health_check(self) -> bool:
        current_time = time.time()
        if current_time - self._last_health_check < self._health_check_interval:
            return self._connection_status == DiscordConnectionStatus.CONNECTED
        self._last_health_check = current_time
        status_info = self._get_detailed_connection_status()
        if not self.bot:
            logger.warning("Discord bot not initialized")
            self._shared__update_connection_status(
                DiscordConnectionStatus.UNINITIALIZED
            )
            return False
        if self.bot.is_closed():
            logger.warning("Discord bot is closed")
            self._shared__update_connection_status(DiscordConnectionStatus.DISCONNECTED)
            return False
        if not self.bot.is_ready():
            logger.warning("Discord bot is not ready")
            self._shared__update_connection_status(DiscordConnectionStatus.DISCONNECTED)
            return False
        if not self._check_dns_resolution():
            logger.warning("DNS resolution failed during health check")
            self._shared__update_connection_status(DiscordConnectionStatus.DNS_FAILURE)
            return False
        if not self._check_network_connectivity():
            logger.warning("Network connectivity failed during health check")
            self._shared__update_connection_status(
                DiscordConnectionStatus.NETWORK_FAILURE
            )
            return False
        try:
            latency = self.bot.latency
            if latency > 1.0:
                logger.warning(f"Discord latency is high: {latency:.2f}s")
                status_info["high_latency"] = True
                status_info["latency"] = latency
        except Exception as exc:
            logger.warning(f"Could not check Discord latency: {exc}")
        self._shared__update_connection_status(DiscordConnectionStatus.CONNECTED)
        logger.debug("Discord health check passed")
        return True

    @handle_errors("getting Discord health status", default_return={})
    def get_health_status(self) -> dict[str, Any]:
        return self._get_detailed_connection_status()

    @handle_errors("getting connection status summary", default_return="Unknown")
    def get_connection_status_summary(self) -> str:
        status_info = self._get_detailed_connection_status()
        status = status_info["connection_status"]
        if status == "connected":
            return (
                f"Connected (Latency: {status_info.get('latency', 'unknown')}s, "
                f"Guilds: {status_info.get('guild_count', 'unknown')})"
            )
        if status == "dns_failure":
            error = status_info.get("detailed_errors", {}).get("dns_error", {})
            return f"DNS Failure: {error.get('error_message', 'Unknown DNS error')}"
        if status == "network_failure":
            error = status_info.get("detailed_errors", {}).get("network_error", {})
            return (
                f"Network Failure: "
                f"{error.get('error_message', 'Unknown network error')}"
            )
        if status == "gateway_error":
            return "Gateway Error: Unable to connect to Discord servers"
        if status == "disconnected":
            return "Disconnected: Bot is not ready or closed"
        return f"Status: {status}"

    @handle_errors("checking if actually connected", default_return=False)
    def is_actually_connected(self) -> bool:
        if not self.bot:
            return False
        if self.bot.is_ready() and not self.bot.is_closed():
            if self.get_status() != ChannelStatus.READY:
                logger.info("Discord bot is actually connected - fixing status")
                self._set_status(ChannelStatus.READY)
                self._starting = False
            return True
        return False

    @handle_errors("checking if can send messages", default_return=False)
    def can_send_messages(self) -> bool:
        if not self.is_actually_connected():
            return False
        try:
            if not self.bot or not self.bot.user:
                return False
            return self.bot.guilds
        except Exception as exc:
            logger.warning(f"Error checking message sending capability: {exc}")
            return False

    @handle_errors("manually reconnecting Discord bot", default_return=False)
    async def manual_reconnect(self) -> bool:
        if not self.bot:
            logger.error("Cannot reconnect - bot not initialized")
            return False
        # Read the patchable token from the discord bot module so tests can patch it there.
        from communication.communication_channels.discord import bot as bot_module

        token = bot_module.DISCORD_BOT_TOKEN
        if not token:
            logger.error("Cannot reconnect - Discord bot token not configured")
            return False
        logger.info("Manual reconnection requested")
        if not self._check_dns_resolution():
            logger.error("DNS resolution failed - cannot reconnect")
            return False
        try:
            await self.bot.close()
            await asyncio.sleep(2)
            await self.bot.start(token)
            logger.info("Manual reconnection successful")
            return True
        except Exception as exc:
            logger.error(f"Manual reconnection failed: {exc}")
            return False
