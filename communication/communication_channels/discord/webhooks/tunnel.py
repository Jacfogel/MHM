"""Managed ngrok tunnel lifecycle for Discord webhooks."""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from typing import Any

import psutil

from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("discord")


@handle_errors("draining ngrok stderr pipe", default_return=None)
def _drain_ngrok_stderr(proc: Any) -> None:
    """Drain ngrok stderr so a full pipe cannot block the child process."""
    if not proc or proc.stderr is None:
        return
    try:
        while proc.stderr.read(4096):
            pass
    except Exception:
        pass


class DiscordWebhookTunnelMixin:
    """Ngrok and webhook-server startup helpers for the Discord host."""

    _ngrok_process: Any
    _ngrok_pid: int | None
    _webhook_server: Any

    @handle_errors("detecting external ngrok tunnel", default_return=False)
    def _has_external_ngrok_tunnel(self) -> bool:
        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if not proc.info["name"]:
                        continue
                    if "ngrok" not in proc.info["name"].lower():
                        continue
                    cmdline = proc.info.get("cmdline", [])
                    if (
                        cmdline
                        and "http" in " ".join(cmdline).lower()
                        and proc.is_running()
                    ):
                        logger.info(
                            "ngrok tunnel detected (external) - check "
                            "http://127.0.0.1:4040 for public URL"
                        )
                        return True
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue
        except Exception:
            return False
        return False

    @handle_errors("starting Discord webhook server", default_return=None)
    def _start_discord_webhook_server_for_ready(self) -> None:
        try:
            from communication.communication_channels.discord.webhooks.server import (
                WebhookServer,
            )
            from core.config import DISCORD_AUTO_NGROK, DISCORD_WEBHOOK_PORT

            if DISCORD_AUTO_NGROK:
                self._start_ngrok_tunnel(DISCORD_WEBHOOK_PORT)
            self._webhook_server = WebhookServer(
                port=DISCORD_WEBHOOK_PORT, bot_instance=self
            )
            if self._webhook_server.start():
                if self._ngrok_process:
                    logger.info(
                        "ngrok tunnel active - check ngrok web interface at "
                        "http://127.0.0.1:4040 for public URL"
                    )
                elif not self._has_external_ngrok_tunnel():
                    logger.info(
                        f"Webhook server ready on port {DISCORD_WEBHOOK_PORT} - "
                        "configure webhook URL in Discord Developer Portal"
                    )
            else:
                logger.warning("Failed to start Discord webhook server")
        except Exception as exc:
            logger.warning(f"Could not start webhook server: {exc}")

    @handle_errors("starting ngrok tunnel", default_return=None)
    def _start_ngrok_tunnel(self, port: int) -> None:
        try:
            ngrok_path = shutil.which("ngrok")
            if not ngrok_path:
                logger.warning(
                    "ngrok not found in PATH - auto-launch disabled. Install ngrok "
                    "or set DISCORD_AUTO_NGROK=false"
                )
                return
            if self._ngrok_process and self._ngrok_process.poll() is None:
                logger.info("ngrok tunnel already running (managed by this bot)")
                return
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if not proc.info["name"]:
                        continue
                    cmdline = proc.info.get("cmdline", [])
                    if (
                        "ngrok" in proc.info["name"].lower()
                        and cmdline
                        and "http" in " ".join(cmdline).lower()
                        and proc.is_running()
                    ):
                        logger.info(
                            f"ngrok tunnel already running externally "
                            f"(PID: {proc.info['pid']}) - skipping auto-launch"
                        )
                        return
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

            logger.info(f"Starting ngrok tunnel for port {port}...")
            popen_kwargs: dict[str, Any] = {
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.PIPE,
            }
            if os.name == "nt":
                popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            self._ngrok_process = subprocess.Popen(
                [ngrok_path, "http", str(port)], **popen_kwargs
            )
            time.sleep(2)
            if self._ngrok_process.poll() is None:
                self._ngrok_pid = self._ngrok_process.pid
                logger.info(
                    f"ngrok tunnel started successfully "
                    f"(PID: {self._ngrok_process.pid})"
                )
                logger.info("ngrok web interface: http://127.0.0.1:4040")
                logger.info(
                    "Check ngrok web interface for public URL to configure in "
                    "Discord Developer Portal"
                )

                threading.Thread(
                    target=_drain_ngrok_stderr,
                    args=(self._ngrok_process,),
                    daemon=True,
                ).start()
                return

            exit_code = self._ngrok_process.poll()
            err_text = ""
            try:
                if self._ngrok_process.stderr is not None:
                    err_text = (
                        self._ngrok_process.stderr.read()
                        .decode(errors="replace")
                        .strip()
                    )
            except Exception:
                pass
            logger.warning(
                f"ngrok process exited immediately (exit code: {exit_code})"
            )
            if err_text:
                logger.warning(f"ngrok stderr (excerpt): {err_text[:2048]}")
            logger.warning(
                "ngrok hint: ngrok v3+ needs a one-time authtoken "
                "(`ngrok config add-authtoken <token>` from "
                "https://dashboard.ngrok.com/). Or run ngrok yourself and set "
                "DISCORD_AUTO_NGROK=false."
            )
            self._ngrok_process = None
            self._ngrok_pid = None
        except FileNotFoundError:
            logger.warning("ngrok executable not found - auto-launch disabled")
            self._ngrok_process = None
            self._ngrok_pid = None
        except Exception as exc:
            logger.warning(f"Error starting ngrok tunnel: {exc}")
            self._ngrok_process = None
            self._ngrok_pid = None

    @handle_errors("stopping ngrok tunnel", default_return=None)
    def _stop_ngrok_tunnel(self) -> None:
        if not self._ngrok_process and not self._ngrok_pid:
            return
        stopped = False
        if self._ngrok_process:
            try:
                if self._ngrok_process.poll() is None:
                    pid = self._ngrok_process.pid
                    logger.info(f"Stopping ngrok tunnel (PID: {pid})...")
                    self._ngrok_process.terminate()
                    try:
                        self._ngrok_process.wait(timeout=5)
                        logger.info("ngrok tunnel stopped")
                        stopped = True
                    except subprocess.TimeoutExpired:
                        logger.warning(
                            "ngrok did not stop gracefully - forcing termination"
                        )
                        self._ngrok_process.kill()
                        self._ngrok_process.wait()
                        logger.info("ngrok tunnel force-stopped")
                        stopped = True
                else:
                    logger.debug(
                        f"ngrok tunnel already exited "
                        f"(exit code: {self._ngrok_process.poll()})"
                    )
                    stopped = True
                self._ngrok_process = None
            except Exception as exc:
                logger.warning(
                    f"Error stopping ngrok tunnel via process reference: {exc}"
                )
                self._ngrok_process = None
        if not stopped and self._ngrok_pid:
            try:
                logger.info(
                    f"Attempting to stop ngrok tunnel by PID "
                    f"(PID: {self._ngrok_pid})..."
                )
                proc = psutil.Process(self._ngrok_pid)
                if proc.is_running():
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                        logger.info("ngrok tunnel stopped (via PID)")
                    except psutil.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                        logger.info("ngrok tunnel force-stopped (via PID)")
                else:
                    logger.debug(f"ngrok process {self._ngrok_pid} already exited")
                stopped = True
            except psutil.NoSuchProcess:
                logger.debug(
                    f"ngrok process {self._ngrok_pid} not found (already stopped)"
                )
                stopped = True
            except Exception as exc:
                logger.warning(f"Error stopping ngrok tunnel by PID: {exc}")
        if stopped:
            self._ngrok_process = None
            self._ngrok_pid = None
