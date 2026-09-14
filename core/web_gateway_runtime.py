"""Run the website gateway on its own event loop inside the MHM service."""

import asyncio
from concurrent.futures import Future
from contextlib import suppress
from threading import Thread

from aiohttp import web

from core import config
from core.logger import get_component_logger

logger = get_component_logger("main")


class WebGatewayRuntime:
    def __init__(self, *, host=None, port=None, app_factory=None):
        self.host = config.WEB_GATEWAY_HOST if host is None else host
        self.port = config.WEB_GATEWAY_PORT if port is None else port
        self.app_factory = app_factory
        self._thread = None
        self._loop = None
        self._stop_event = None
        self._ready = Future()
        self.error = None
        self.bound_port = None

    def start(self):
        """Report bind failures without disrupting other MHM services or servers."""
        if self._thread is not None:
            return self.error is None and self._thread.is_alive()
        self._thread = Thread(target=self._run, name="mhm-web-gateway", daemon=True)
        self._thread.start()
        try:
            self._ready.result(timeout=5)
            return True
        except Exception as exc:
            self.error = type(exc).__name__
            logger.error(
                f"Website gateway could not start on {self.host}:{self.port}: {self.error}. Check whether the standalone gateway is already running."
            )
            self.stop()
            return False

    def _run(self):
        try:
            asyncio.run(self._serve())
        except Exception as exc:
            self.error = type(exc).__name__
            if not self._ready.done():
                self._ready.set_exception(exc)

    async def _serve(self):
        from core.web_account_service import create_web_app

        self._loop = asyncio.get_running_loop()
        self._stop_event = asyncio.Event()
        runner = web.AppRunner(
            (self.app_factory or create_web_app)(), access_log=None, shutdown_timeout=5
        )
        try:
            await runner.setup()
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()
            self.bound_port = runner.addresses[0][1]
            self._ready.set_result(True)
            logger.info(f"Website gateway listening on {self.host}:{self.bound_port}")
            await self._stop_event.wait()
        finally:
            await runner.cleanup()

    def stop(self):
        """Stop only the gateway this runtime owns and let aiohttp drain requests."""
        if self._loop and not self._loop.is_closed() and self._stop_event:
            with suppress(RuntimeError):
                self._loop.call_soon_threadsafe(self._stop_event.set)
        if self._thread:
            self._thread.join(timeout=6)
