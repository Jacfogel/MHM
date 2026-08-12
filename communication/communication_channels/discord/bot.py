"""Thin BaseChannel host for Discord lifecycle and extracted handlers."""

from __future__ import annotations

import asyncio
import contextlib
import queue
import threading
import time
from typing import Any

import discord
from discord import app_commands  # noqa: F401  # patch/import surface for command_registration
from discord.ext import commands

from communication.communication_channels.base.base_channel import (
    BaseChannel,
    ChannelConfig,
    ChannelStatus,
    ChannelType,
)
from communication.communication_channels.discord.events.connection_health import (
    DiscordConnectionHealthMixin,
)
from communication.communication_channels.discord.events.status import (
    DiscordConnectionStatus,
)
from communication.communication_channels.discord.ui.rich_delivery import (
    DiscordRichDeliveryMixin,
)
from communication.communication_channels.discord.webhooks.tunnel import (
    DiscordWebhookTunnelMixin,
)
from core.config import DISCORD_APPLICATION_ID, DISCORD_BOT_TOKEN
from core.error_handling import handle_errors
from core.logger import get_component_logger
from core import get_user_id_by_identifier  # noqa: F401  # patch surface for command_registration

# Module attributes above remain bound so callers/tests can patch them on this module.

discord_logger = get_component_logger("discord")
logger = discord_logger

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True


class DiscordBot(
    DiscordRichDeliveryMixin,
    DiscordConnectionHealthMixin,
    DiscordWebhookTunnelMixin,
    BaseChannel,
):
    """Discord channel host; feature behavior lives in focused submodules."""

    @handle_errors("initializing Discord bot", default_return=None)
    def __init__(self, config: ChannelConfig | None = None):
        if config is None:
            config = ChannelConfig(
                name="discord",
                max_retries=5,
                retry_delay=2.0,
                backoff_multiplier=2.0,
            )
        super().__init__(config)
        self.bot = None
        self.discord_thread = None
        self._loop = None
        self._starting = False
        self._command_queue = queue.Queue()
        self._result_queue = queue.Queue()
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._last_reconnect_time = 0
        self._reconnect_cooldown = 60
        self._connection_status = DiscordConnectionStatus.UNINITIALIZED
        self._last_health_check = 0
        self._health_check_interval = 30
        self._detailed_error_info = {}
        self._events_registered = False
        self._commands_registered = False
        self._sessions_to_cleanup = []
        self._sync_task = None
        self._suggestion_button_payloads: dict[str, Any] = {}
        self._suggestion_button_counter = 0
        self._webhook_server = None
        self._ngrok_process = None
        self._ngrok_pid = None
        self._on_ready_fired = False
        self.logger = discord_logger

    @property
    @handle_errors("getting Discord channel type", default_return=ChannelType.ASYNC)
    def channel_type(self) -> ChannelType:
        return ChannelType.ASYNC

    @handle_errors("initializing Discord bot", default_return=False)
    async def initialize(self) -> bool:
        if self._starting:
            logger.info("Discord bot already initializing")
            return False
        if self.is_ready():
            logger.info("Discord bot already initialized")
            return True
        self._starting = True
        self._set_status(ChannelStatus.INITIALIZING)
        self._shared__update_connection_status(DiscordConnectionStatus.INITIALIZING)
        try:
            if not DISCORD_BOT_TOKEN:
                error_msg = "Discord bot token not configured."
                self._set_status(ChannelStatus.ERROR, error_msg)
                logger.error(error_msg)
                return False
            logger.info("Performing pre-flight network check...")
            if not self._check_network_health():
                logger.warning(
                    "Pre-flight network check failed, but continuing with initialization"
                )
            bot_kwargs: dict[str, Any] = {
                "command_prefix": "!",
                "intents": intents,
                "help_command": None,
            }
            if DISCORD_APPLICATION_ID is not None:
                bot_kwargs["application_id"] = DISCORD_APPLICATION_ID
            self.bot = commands.Bot(**bot_kwargs)
            if not self._events_registered:
                self.initialize__register_events()
            if not self._commands_registered:
                self.initialize__register_commands()
            self.discord_thread = threading.Thread(
                target=self.initialize__run_bot_in_thread, daemon=True
            )
            self.discord_thread.start()

            max_wait = 60
            total_waited = 0.0
            while total_waited < max_wait:
                await asyncio.sleep(0.5)
                total_waited += 0.5
                if self.bot and self.bot.is_ready():
                    self._set_status(ChannelStatus.READY)
                    self._reconnect_attempts = 0
                    self._starting = False
                    self._shared__update_connection_status(
                        DiscordConnectionStatus.CONNECTED
                    )
                    logger.info("Discord bot initialized successfully")
                    await asyncio.sleep(0.5)
                    if (
                        getattr(self, "_on_ready_handler", None)
                        and not self._on_ready_fired
                    ):
                        discord_logger.warning(
                            "Bot is ready but on_ready() hasn't fired - manually "
                            "triggering webhook server startup"
                        )
                        try:
                            if (
                                hasattr(self.bot, "loop")
                                and self.bot.loop
                                and not self.bot.loop.is_closed()
                            ):
                                self.bot.loop.create_task(self._on_ready_handler())
                            else:
                                discord_logger.debug(
                                    "Bot loop not available for manual on_ready trigger"
                                )
                        except Exception as exc:
                            discord_logger.warning(
                                "Failed to manually trigger webhook server startup: "
                                f"{exc}",
                                exc_info=True,
                            )
                    return True
                if total_waited % 10 == 0:
                    logger.info(
                        "Waiting for Discord bot to be ready... "
                        f"({total_waited}s/{max_wait}s)"
                    )
                    if total_waited % 20 == 0 and not self._check_network_health():
                        logger.warning(
                            "Network health check failed during initialization"
                        )
            error_msg = (
                f"Discord bot failed to become ready within {max_wait} seconds"
            )
            self._set_status(ChannelStatus.ERROR, error_msg)
            self._shared__update_connection_status(
                DiscordConnectionStatus.GATEWAY_ERROR,
                {
                    "error": error_msg,
                    "timeout_seconds": max_wait,
                    "timestamp": time.time(),
                },
            )
            logger.error(error_msg)
            return False
        finally:
            self._starting = False

    @handle_errors("running Discord bot in thread")
    def initialize__run_bot_in_thread(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self.initialize__bot_main_loop())

    @handle_errors("running Discord bot main loop")
    async def initialize__bot_main_loop(self):
        bot = self.bot
        if not bot or not DISCORD_BOT_TOKEN:
            logger.error("Discord bot not initialized or token missing")
            return
        bot_task = asyncio.create_task(bot.start(DISCORD_BOT_TOKEN))
        command_task = asyncio.create_task(self.initialize__process_command_queue())
        try:
            _done, pending = await asyncio.wait(
                [bot_task, command_task], return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        finally:
            if not bot.is_closed():
                await bot.close()
            try:
                http = getattr(bot, "_HTTP", None)
                http_client = getattr(http, "_HTTPClient", None) if http else None
                session = getattr(http_client, "_session", None) if http_client else None
                if session:
                    await session.close()
                    logger.info("Discord bot HTTP session closed in main loop")
            except Exception as exc:
                logger.debug(
                    "Error closing HTTP session in main loop "
                    f"(may already be closed): {exc}"
                )

    @handle_errors("processing Discord command queue")
    async def initialize__process_command_queue(self):
        while True:
            try:
                try:
                    command, args = self._command_queue.get_nowait()
                    if command == "send_message":
                        if len(args) in (4, 5):
                            result = await self._send_message_internal(*args)
                        else:
                            logger.error(f"Invalid send_message args: {args}")
                            result = False
                        self._result_queue.put(result)
                    elif command == "stop":
                        logger.info("Discord bot received stop command")
                        return
                except queue.Empty:
                    pass
                await asyncio.sleep(0.1)
            except Exception as exc:
                logger.error(f"Error in Discord command processing: {exc}")
                await asyncio.sleep(0.1)

    @handle_errors("scheduling Discord ready tasks", default_return=None)
    def _schedule_ready_tasks(self, bot) -> None:
        @handle_errors(
            "syncing Discord application commands",
            user_friendly=False,
            default_return=None,
        )
        async def _sync_app_cmds():
            if not getattr(bot, "application_id", None):
                logger.warning(
                    "Skipping Discord command sync: application_id unavailable. "
                    "Set DISCORD_APPLICATION_ID (matching your bot token's app) "
                    "to enable sync."
                )
                return
            await bot.tree.sync()
            logger.info("Discord application commands synced")

        @handle_errors(
            "checking for new authorized Discord users",
            user_friendly=False,
            default_return=None,
        )
        async def _check_new_authorized_users():
            discord_logger.debug(
                "Bot ready - will welcome users on Discord app authorization "
                "(via webhook) or first interaction"
            )

        self._sync_task = bot.loop.create_task(_sync_app_cmds())
        bot.loop.create_task(_check_new_authorized_users())

    @handle_errors("registering Discord events")
    def initialize__register_events(self):
        if self._events_registered or not self.bot:
            return
        from communication.communication_channels.discord.events.interaction_router import (
            handle_discord_interaction,
        )
        from communication.communication_channels.discord.events.lifecycle import (
            handle_disconnect,
            handle_error,
            handle_guild_join,
            run_on_ready_internal,
        )
        from communication.communication_channels.discord.events.message_handler import (
            handle_discord_message,
        )

        @self.bot.event
        @handle_errors(
            "Discord bot ready event", user_friendly=False, default_return=None
        )
        async def on_ready():
            await run_on_ready_internal(self)

        @self.bot.event
        @handle_errors("handling Discord disconnect event", default_return=None)
        async def on_disconnect():
            await handle_disconnect(self)

        @self.bot.event
        @handle_errors("handling Discord error event", default_return=None)
        async def on_error(event, *args, **kwargs):
            await handle_error(self, event, *args, **kwargs)

        @self.bot.event
        @handle_errors("handling Discord interaction event", default_return=None)
        async def on_interaction(interaction: discord.Interaction):
            await handle_discord_interaction(self, interaction)

        @self.bot.event
        @handle_errors("handling Discord guild join event", default_return=None)
        async def on_guild_join(guild):
            await handle_guild_join(guild)

        @self.bot.event
        @handle_errors("handling Discord message", default_return=None)
        async def on_message(message):
            await handle_discord_message(self, message)

        @handle_errors(
            "Discord bot on_ready manual handler",
            user_friendly=False,
            default_return=None,
        )
        async def _on_ready_handler():
            await run_on_ready_internal(self)

        self._on_ready_handler = _on_ready_handler
        self._events_registered = True
        if self.bot.is_ready():
            try:
                if (
                    hasattr(self.bot, "loop")
                    and self.bot.loop
                    and not self.bot.loop.is_closed()
                ):
                    self.bot.loop.create_task(_on_ready_handler())
                else:
                    discord_logger.debug(
                        "Bot loop not available for manual on_ready trigger"
                    )
            except Exception as exc:
                discord_logger.warning(
                    f"Failed to manually trigger webhook server startup: {exc}",
                    exc_info=True,
                )

    @handle_errors("registering Discord commands")
    def initialize__register_commands(self):
        from communication.communication_channels.discord.events.command_registration import (
            register_discord_commands,
        )

        register_discord_commands(self)

    @contextlib.asynccontextmanager
    @handle_errors("cleaning up session context", default_return=None)
    async def shutdown__session_cleanup_context(self):
        sessions_to_cleanup = []
        try:
            yield sessions_to_cleanup
        finally:
            cleanup_tasks = [
                self._cleanup_session_with_timeout(session)
                for session in sessions_to_cleanup
                if hasattr(session, "close") and not session.closed
            ]
            if cleanup_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*cleanup_tasks, return_exceptions=True),
                        timeout=10.0,
                    )
                    logger.info(
                        f"Successfully cleaned up {len(cleanup_tasks)} sessions"
                    )
                except asyncio.TimeoutError:
                    logger.warning("Session cleanup timed out")

    @handle_errors(
        "cleaning up session with timeout", user_friendly=False, default_return=False
    )
    async def _cleanup_session_with_timeout(self, session) -> bool:
        try:
            await asyncio.wait_for(session.close(), timeout=5.0)
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Session cleanup timed out for {type(session).__name__}")
            return False
        except Exception as exc:
            logger.debug(f"Error closing session {type(session).__name__}: {exc}")
            return False

    @handle_errors(
        "cleaning up event loop safely", user_friendly=False, default_return=False
    )
    async def _cleanup_event_loop_safely(
        self, loop: asyncio.AbstractEventLoop
    ) -> bool:
        if not loop or loop.is_closed():
            return True
        tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
        for task in tasks:
            task.cancel()
        if tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True), timeout=5.0
                )
            except asyncio.TimeoutError:
                logger.warning("Task cancellation timed out")
        if not loop.is_closed():
            loop.close()
        return True

    @handle_errors(
        "cleaning up aiohttp sessions", user_friendly=False, default_return=False
    )
    async def _cleanup_aiohttp_sessions(self) -> bool:
        import gc
        import aiohttp

        gc.collect()
        for obj in gc.get_objects():
            if isinstance(obj, aiohttp.ClientSession) and not obj.closed:
                try:
                    await obj.close()
                except Exception as exc:
                    logger.debug(f"Error closing aiohttp session: {exc}")
        return True

    @handle_errors("shutting down Discord bot", default_return=False)
    async def shutdown(self) -> bool:
        logger.info("Starting Discord bot shutdown...")
        try:
            self._stop_ngrok_tunnel()
            try:
                self._command_queue.put(("stop", None))
            except Exception as exc:
                logger.warning(f"Error sending stop command: {exc}")
            if self.discord_thread and self.discord_thread.is_alive():
                self.discord_thread.join(timeout=10)
                if self.discord_thread.is_alive():
                    logger.warning("Discord thread did not stop gracefully")
            if self.bot:
                async with self.shutdown__session_cleanup_context() as sessions:
                    if self._sync_task and not self._sync_task.done():
                        self._sync_task.cancel()
                        with contextlib.suppress(
                            asyncio.CancelledError, asyncio.TimeoutError
                        ):
                            await asyncio.wait_for(self._sync_task, timeout=2.0)
                    if not self.bot.is_closed():
                        await self.bot.close()
                        logger.info("Discord bot closed successfully")
                    http = getattr(self.bot, "_HTTP", None)
                    http_client = getattr(http, "_HTTPClient", None) if http else None
                    session = (
                        getattr(http_client, "_session", None) if http_client else None
                    )
                    if session:
                        sessions.append(session)
                    if self._loop:
                        await self._cleanup_event_loop_safely(self._loop)
                    await self._cleanup_aiohttp_sessions()
                    if self._webhook_server:
                        try:
                            self._webhook_server.stop()
                        except Exception as exc:
                            logger.debug(f"Error stopping webhook server: {exc}")
                    self._stop_ngrok_tunnel()
            self._stop_ngrok_tunnel()
            return True
        finally:
            self._set_status(ChannelStatus.STOPPED)
            logger.info("Discord bot shutdown completed")

    @handle_errors("sending Discord message", default_return=False)
    async def send_message(self, recipient: str, message: str, **kwargs) -> bool:
        if not recipient or not isinstance(recipient, str) or not recipient.strip():
            logger.error(f"Invalid recipient: {recipient}")
            return False
        if not message or not isinstance(message, str) or not message.strip():
            logger.error(f"Invalid message: {message}")
            return False
        if not self.is_ready():
            logger.error("Discord bot is not ready to send messages")
            return False
        args = (
            recipient,
            message,
            kwargs.get("rich_data", {}),
            kwargs.get("suggestions", []),
        )
        custom_view = kwargs.get("view")
        if custom_view:
            args = (*args, custom_view)
        self._command_queue.put(("send_message", args))
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                return self._result_queue.get_nowait()
            except queue.Empty:
                time.sleep(0.1)
        logger.error(f"Timeout waiting for Discord message send to {recipient}")
        return False

    @handle_errors("sending Discord DM", default_return=False)
    async def send_dm(self, user_id: str, message: str) -> bool:
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            logger.error(f"Invalid user_id: {user_id}")
            return False
        if not message or not isinstance(message, str) or not message.strip():
            logger.error(f"Invalid message: {message}")
            return False
        return await self.send_message(user_id, message)

    @handle_errors("receiving Discord messages", default_return=[])
    async def receive_messages(self) -> list[dict[str, Any]]:
        return []
