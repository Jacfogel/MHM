"""Inbound email polling and reply adapter."""

from __future__ import annotations

import asyncio
import re
import threading
from collections.abc import Callable
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("email")


class EmailInboundProcessor:
    """Polls the email channel, routes inbound messages, and sends replies."""

    @handle_errors(
        "initializing email inbound processor", user_friendly=False, re_raise=True
    )
    def __init__(
        self,
        get_email_channel: Callable[[], Any],
        run_async_sync: Callable[[Any], Any],
        is_runtime_running: Callable[[], bool],
    ) -> None:
        self._get_email_channel = get_email_channel
        self._run_async_sync = run_async_sync
        self._is_runtime_running = is_runtime_running
        self._polling_thread: threading.Thread | None = None
        self._polling_stop_event = threading.Event()
        self._processed_email_ids: set[str] = set()

    @property
    @handle_errors("getting email polling thread", default_return=None)
    def polling_thread(self) -> threading.Thread | None:
        """Return the active polling thread, if one has been started."""
        return self._polling_thread

    @handle_errors("starting email polling thread", default_return=None)
    def start_polling(self) -> None:
        """Start the email polling thread."""
        if self._polling_thread is not None and self._polling_thread.is_alive():
            logger.debug("Email polling thread already running")
            return

        self._polling_stop_event.clear()
        self._polling_thread = threading.Thread(
            target=self._polling_loop, daemon=True
        )
        self._polling_thread.start()
        logger.info("Email polling thread started")

    @handle_errors("stopping email polling thread", default_return=None)
    def stop_polling(self) -> None:
        """Stop the email polling thread."""
        if self._polling_thread is None:
            return

        logger.info("Stopping email polling thread...")
        self._polling_stop_event.set()
        self._polling_thread.join(timeout=5)
        if self._polling_thread.is_alive():
            logger.warning("Email polling thread didn't stop within timeout")
        else:
            logger.info("Email polling thread stopped")
        self._polling_thread = None

    @handle_errors("email polling loop", default_return=None)
    def _polling_loop(self) -> None:
        """Background thread that periodically polls for incoming emails."""
        logger.info("Email polling loop started")
        poll_interval = 30

        while not self._polling_stop_event.is_set():
            try:
                email_channel = self._get_email_channel()
                if email_channel and email_channel.is_ready() and self._is_runtime_running():
                    self._poll_once(email_channel)
                else:
                    logger.debug(
                        "Email channel not available or not ready, skipping poll"
                    )
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e) if str(e) else f"{error_type} with no message"
                logger.error(
                    f"Error in email polling loop: {error_type} - {error_msg}",
                    exc_info=True,
                )

            if self._polling_stop_event.wait(timeout=poll_interval):
                break

        logger.info("Email polling loop stopped")

    @handle_errors("polling email channel once", default_return=None)
    def _poll_once(self, email_channel: Any) -> None:
        """Receive available email messages once and process unseen message IDs."""
        try:
            emails = self._run_async_sync(email_channel.receive_messages())
            if emails is None:
                logger.debug("Email receive returned no messages")
                return
            if not isinstance(emails, list):
                logger.warning(
                    f"Email receive returned unexpected payload type: {type(emails).__name__}"
                )
                return
            for email_msg in emails:
                if not isinstance(email_msg, dict):
                    logger.warning(
                        f"Skipping malformed email payload: {type(email_msg).__name__}"
                    )
                    continue
                email_id = email_msg.get("imap_email_id")
                if email_id and email_id not in self._processed_email_ids:
                    self.process_incoming_email(email_msg)
                    self._processed_email_ids.add(email_id)
                    if len(self._processed_email_ids) > 1000:
                        self._processed_email_ids = set(
                            list(self._processed_email_ids)[-500:]
                        )
        except asyncio.TimeoutError:
            logger.error(
                "Error polling for emails: Timeout waiting for receive_messages() to complete",
                exc_info=True,
            )
        except RuntimeError as e:
            logger.error(
                f"Error polling for emails: RuntimeError - {e} (event loop may be closed or invalid)",
                exc_info=True,
            )
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else f"{error_type} with no message"
            logger.error(
                f"Error polling for emails: {error_type} - {error_msg}",
                exc_info=True,
            )

    @handle_errors("processing incoming email", default_return=None)
    def process_incoming_email(self, email_msg: dict[str, Any]) -> None:
        """Process an incoming email message and send a response."""
        try:
            email_from = email_msg.get("from", "")
            email_body = email_msg.get("body", "")
            email_subject = email_msg.get("subject", "")

            if not email_from or not email_body:
                logger.debug(f"Skipping email with missing from or body: {email_msg}")
                return

            email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", email_from)
            if not email_match:
                logger.warning(
                    f"Could not extract email address from 'from' field: {email_from}"
                )
                return

            sender_email = email_match.group(0)

            if self.should_ignore_inbound_sender(sender_email):
                logger.info(
                    f"Ignoring inbound email from non-user/system sender: {sender_email}"
                )
                return

            from core import get_user_id_by_identifier

            user_id = get_user_id_by_identifier(sender_email)
            if not user_id:
                logger.info(f"Email from unregistered user: {sender_email}")
                response_text = (
                    "I don't recognize you yet! Please register first using the MHM application. "
                    f"Your email is: {sender_email}"
                )
                self.send_email_response(sender_email, response_text, email_subject)
                return

            logger.info(
                f"Processing email from registered user: {sender_email} (user_id: {user_id})"
            )

            from communication.message_processing.interaction_manager import (
                handle_user_message,
            )

            response = handle_user_message(user_id, email_body, "email")
            if response and response.message:
                self.send_email_response(
                    sender_email, response.message, f"Re: {email_subject}"
                )
            else:
                logger.warning(f"No response generated for email from user {user_id}")

        except Exception as e:
            logger.error(f"Error processing incoming email: {e}", exc_info=True)

    @handle_errors(
        "checking whether inbound sender should be ignored",
        user_friendly=False,
        default_return=False,
    )
    def should_ignore_inbound_sender(self, sender_email: str) -> bool:
        """Return True for known non-user/system senders that should never get replies."""
        if not sender_email or not isinstance(sender_email, str):
            return False

        normalized = sender_email.strip().lower()
        if "@" not in normalized:
            return False

        local_part = normalized.split("@", 1)[0]
        blocked_keywords = (
            "mailer-daemon",
            "postmaster",
            "no-reply",
            "noreply",
            "donotreply",
            "do-not-reply",
            "bounce",
        )
        return any(keyword in local_part for keyword in blocked_keywords)

    @handle_errors("sending email response", default_return=None)
    def send_email_response(
        self,
        recipient_email: str,
        response_text: str,
        subject: str = "Re: Your Message",
    ) -> None:
        """Send an email response to a user."""
        try:
            email_channel = self._get_email_channel()
            if not email_channel or not email_channel.is_ready():
                logger.error("Email channel not available for sending response")
                return

            self._run_async_sync(
                email_channel.send_message(
                    recipient_email, response_text, subject=subject
                )
            )
            logger.info(f"Email response sent to {recipient_email}")
        except Exception as e:
            logger.error(f"Error sending email response to {recipient_email}: {e}")
