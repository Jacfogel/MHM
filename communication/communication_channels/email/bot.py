# email_bot.py

import smtplib
import imaplib
import asyncio
import time
import contextlib
from email.mime.text import MIMEText
from email.header import decode_header
from email.message import EmailMessage
from email.parser import BytesParser
from email.policy import default as email_policy_default
from email.utils import make_msgid, parseaddr
from typing import Any

from core.config import (
    EMAIL_SMTP_SERVER,
    EMAIL_IMAP_SERVER,
    EMAIL_SMTP_USERNAME,
    EMAIL_SMTP_PASSWORD,
)
from core.logger import get_component_logger
from communication.communication_channels.base.base_channel import (
    BaseChannel,
    ChannelType,
    ChannelStatus,
    ChannelConfig,
)
from communication.communication_channels.email.quote_strip import html_to_plain_text
from communication.communication_channels.email.reply_context import (
    normalize_message_id,
    record_outbound_email,
)
from core.error_handling import handle_errors, ConfigurationError

# Route module-level logs to email component for consistency
email_logger = get_component_logger("email")
logger = email_logger

_REPLY_KINDS = {"checkin", "task_reminder", "message"}


@handle_errors("choosing email reply kind", default_return="message")
def reply_kind_from_send_kwargs(kwargs: dict) -> str:
    """Choose check-in, task reminder, or general message from send options."""
    explicit = kwargs.get("reply_kind")
    if explicit in _REPLY_KINDS:
        return str(explicit)
    category = str(kwargs.get("category") or "")
    if category == "checkin":
        return "checkin"
    if category == "task_reminders":
        return "task_reminder"
    return "message"


@handle_errors("building an outbound email message id", default_return="")
def build_outbound_message_id(sender: str, requested: str | None = None) -> str:
    """Return a Message-ID for an outbound email, reusing one when the caller set it."""
    existing = normalize_message_id(requested)
    if existing:
        return existing
    _name, address = parseaddr(sender or "")
    domain = address.split("@", 1)[1] if "@" in address else "mhm.local"
    return make_msgid(domain=domain)


class EmailBotError(Exception):
    """Custom exception for email bot-related errors."""

    pass


class EmailBot(BaseChannel):
    # Class-level variable to track last timeout log time for rate limiting
    _last_timeout_log_time = 0
    _timeout_log_interval = 3600  # 1 hour in seconds

    @handle_errors("initializing email bot", default_return=None)
    def __init__(self, config: ChannelConfig | None = None):
        """
        Initialize the EmailBot with configuration.

        Args:
            config: Channel configuration object. If None, creates default config
                   with email-specific settings (max_retries=3, retry_delay=1.0,
                   backoff_multiplier=2.0)
        """
        # Initialize BaseChannel
        if config is None:
            config = ChannelConfig(
                name="email", max_retries=3, retry_delay=1.0, backoff_multiplier=2.0
            )
        super().__init__(config)
        self.last_outbound_message_id: str | None = None

    @property
    # not_duplicate: channel_type_properties
    @handle_errors("getting email channel type", default_return=ChannelType.SYNC)
    def channel_type(self) -> ChannelType:
        """
        Get the channel type for email bot.

        Returns:
            ChannelType.SYNC: Email operations are synchronous
        """
        return ChannelType.SYNC  # Email operations are synchronous

    @handle_errors("initializing email bot", default_return=False)
    async def initialize(self) -> bool:
        """Initialize the email bot"""
        self._set_status(ChannelStatus.INITIALIZING)

        # Validate configuration
        if not self._get_email_config():
            error_msg = "Email configuration incomplete. Missing required settings."
            self._set_status(ChannelStatus.ERROR, error_msg)
            return False

        # Test SMTP connection
        # Use get_running_loop() first, fallback to new_event_loop() if no running loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop (shouldn't happen in async context, but handle gracefully)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        await loop.run_in_executor(None, self.initialize__test_smtp_connection)

        # Test IMAP connection
        await loop.run_in_executor(None, self.initialize__test_imap_connection)

        self._set_status(ChannelStatus.READY)
        logger.info("EmailBot initialized successfully.")
        return True

    # not_duplicate: email_connection_tests
    @handle_errors("testing SMTP connection")
    def initialize__test_smtp_connection(self):
        """Test SMTP connection synchronously"""
        config = self._get_email_config()
        if not config:
            return
        smtp_server, _, smtp_user, smtp_password = config
        # Use 10 second timeout to prevent indefinite hangs (slightly longer than IMAP for TLS handshake)
        with smtplib.SMTP_SSL(smtp_server, 465, timeout=10) as server:
            server.login(smtp_user, smtp_password)

    # not_duplicate: email_connection_tests
    @handle_errors("testing IMAP connection")
    def initialize__test_imap_connection(self):
        """Test IMAP connection synchronously"""
        config = self._get_email_config()
        if not config:
            return
        _, imap_server, smtp_user, smtp_password = config
        # Use 8 second timeout to match timeout used in _receive_emails_sync
        with imaplib.IMAP4_SSL(imap_server, timeout=8) as mail:
            mail.login(smtp_user, smtp_password)

    @handle_errors("shutting down email bot", default_return=False)
    async def shutdown(self) -> bool:
        """Shutdown the email bot"""
        self._set_status(ChannelStatus.STOPPED)
        logger.info("EmailBot stopped.")
        return True

    # not_duplicate: send_message_channel
    @handle_errors("sending email message", default_return=False)
    async def send_message(self, recipient: str, message: str, **kwargs) -> bool:
        """Send message via email"""
        if not self.is_ready():
            logger.error("EmailBot is not ready to send messages.")
            return False

        # Run the synchronous email sending in a thread pool
        # Use get_running_loop() first, fallback to new_event_loop() if no running loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop (shouldn't happen in async context, but handle gracefully)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        await loop.run_in_executor(
            None, self.send_message__send_email_sync, recipient, message, kwargs
        )
        # Enhanced logging with message content
        message_preview = message[:50] + "..." if len(message) > 50 else message
        logger.info(f"Email sent to {recipient} | Content: '{message_preview}'")
        return True

    @handle_errors("sending email synchronously")
    def send_message__send_email_sync(self, recipient: str, message: str, kwargs: dict):
        """Send email synchronously and remember its Message-ID for later replies."""
        self.last_outbound_message_id = None
        config = self._get_email_config()
        if not config:
            return
        smtp_server, _, smtp_user, smtp_password = config
        subject = str(kwargs.get("subject") or "Personal Assistant Message")
        in_reply_to = normalize_message_id(kwargs.get("in_reply_to"))
        if in_reply_to and not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
        message_id = build_outbound_message_id(smtp_user, kwargs.get("message_id"))

        msg = MIMEText(message)
        msg["From"] = smtp_user
        msg["To"] = recipient
        msg["Subject"] = subject
        msg["Message-ID"] = message_id
        if in_reply_to:
            references = str(kwargs.get("references") or "").strip()
            if in_reply_to not in references:
                references = f"{references} {in_reply_to}".strip()
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = references

        # Use 10 second timeout to prevent indefinite hangs (slightly longer than IMAP for TLS handshake)
        with smtplib.SMTP_SSL(smtp_server, 465, timeout=10) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipient, msg.as_string())

        self.last_outbound_message_id = message_id
        user_id = kwargs.get("user_id")
        if isinstance(user_id, str) and user_id.strip():
            record_outbound_email(
                user_id.strip(),
                message_id,
                kind=reply_kind_from_send_kwargs(kwargs),
                task_id=str(kwargs.get("task_id") or ""),
                subject=subject,
            )

    # devtools: intentional[duplicate-functions]: channel_receive_messages_contract
    @handle_errors("receiving email messages", default_return=[])
    async def receive_messages(self) -> list[dict[str, Any]]:
        """Receive messages from email"""
        if not self.is_ready():
            logger.error("EmailBot is not ready to receive messages.")
            return []

        # Run the synchronous email receiving in a thread pool
        # Use get_running_loop() first, fallback to new_event_loop() if no running loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop (shouldn't happen in async context, but handle gracefully)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        messages = await loop.run_in_executor(None, self._receive_emails_sync)
        if len(messages) > 0:
            logger.info(f"Received {len(messages)} new email(s)")
        return messages

    @handle_errors("receiving emails synchronously", default_return=[])
    def _receive_emails_sync(self) -> list[dict[str, Any]]:
        """Receive emails synchronously - only fetches UNSEEN emails for efficiency"""
        import socket

        messages = []
        mail = None
        config = self._get_email_config()
        if not config:
            return messages
        _, imap_server, smtp_user, smtp_password = config

        try:
            # Create IMAP connection with socket timeout (8 seconds to leave buffer for overall 10s timeout)
            # Set socket timeout before creating connection
            socket.setdefaulttimeout(8)
            logger.debug(f"Connecting to IMAP server: {imap_server}")
            mail = imaplib.IMAP4_SSL(imap_server, timeout=8)

            logger.debug("Attempting IMAP login")
            mail.login(smtp_user, smtp_password)
            logger.debug("IMAP login successful")

            logger.debug("Selecting inbox")
            mail.select("inbox")

            # Only search for UNSEEN emails (new emails) instead of ALL
            # This is much faster and avoids processing already-seen emails
            logger.debug("Searching for UNSEEN emails")
            status, message_ids = mail.search(None, "UNSEEN")

            if status != "OK" or not message_ids[0]:
                logger.debug("No UNSEEN emails found")
                mail.close()
                mail.logout()
                return messages

            email_ids = message_ids[0].split()

            # Limit to last 20 emails to prevent timeout with large inboxes
            # Process most recent emails first (reverse order)
            email_ids = email_ids[-20:] if len(email_ids) > 20 else email_ids

            logger.info(f"Processing {len(email_ids)} new emails")

            processed_email_ids = []  # Track successfully processed email IDs

            for email_id in email_ids:
                try:
                    status, msg_data = mail.fetch(email_id, "(BODY.PEEK[])")
                    if status != "OK":
                        logger.debug(f"Failed to fetch email {email_id}: {status}")
                        continue

                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = BytesParser(policy=email_policy_default).parsebytes(
                                response_part[1]
                            )
                            email_subject = decode_header(msg["subject"])[0][0]
                            if isinstance(email_subject, bytes):
                                email_subject = email_subject.decode()
                            email_from = msg.get("from")

                            # Extract email body text
                            body_text = self._receive_emails_sync__extract_body(msg)

                            messages.append(
                                {
                                    "from": email_from,
                                    "subject": email_subject,
                                    "body": body_text,
                                    # IMAP message sequence / fetch id (not a user template id)
                                    "imap_email_id": email_id.decode(),
                                    "message_id": str(msg.get("Message-ID") or ""),
                                    "in_reply_to": str(msg.get("In-Reply-To") or ""),
                                    "references": str(msg.get("References") or ""),
                                }
                            )
                            # Fetched with BODY.PEEK so the message stays unread
                            # until inbound handling succeeds.
                            processed_email_ids.append(email_id)
                            break  # Only process first valid response part
                except Exception as e:
                    logger.warning(f"Error processing email {email_id}: {e}")
                    continue  # Continue with next email even if one fails

            if processed_email_ids:
                logger.debug(
                    f"Fetched {len(processed_email_ids)} unread emails without marking them seen"
                )

            logger.debug("Email processing completed successfully")
            mail.close()
            mail.logout()
        except TimeoutError as e:
            # Rate limit timeout logging to once per hour (expected behavior when no emails)
            current_time = time.time()
            time_since_last_log = current_time - EmailBot._last_timeout_log_time

            if time_since_last_log >= EmailBot._timeout_log_interval:
                # Log at DEBUG level since this is expected behavior when no emails are present
                logger.debug(
                    f"IMAP socket timeout in _receive_emails_sync after 8 seconds (expected when no emails): {e}"
                )
                EmailBot._last_timeout_log_time = current_time
            # Try to clean up connection if it exists
            try:
                if mail:
                    mail.close()
                    mail.logout()
            except Exception:
                pass
        finally:
            # Reset socket timeout to default
            socket.setdefaulttimeout(None)

        logger.debug(
            f"Email receive operation completed, returning {len(messages)} messages"
        )
        return messages

    @handle_errors("marking email message seen", default_return=False)
    async def mark_message_seen(self, imap_email_id: str) -> bool:
        """Mark one inbox message read after it has been handled."""
        if not imap_email_id or not self.is_ready():
            return False
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return bool(
            await loop.run_in_executor(None, self._mark_message_seen_sync, imap_email_id)
        )

    @handle_errors("marking email message seen synchronously", default_return=False)
    def _mark_message_seen_sync(self, imap_email_id: str) -> bool:
        """Mark one IMAP message \\Seen."""
        import socket

        config = self._get_email_config()
        if not config or not imap_email_id:
            return False
        _, imap_server, smtp_user, smtp_password = config
        mail = None
        try:
            socket.setdefaulttimeout(8)
            mail = imaplib.IMAP4_SSL(imap_server, timeout=8)
            mail.login(smtp_user, smtp_password)
            mail.select("inbox")
            mail.store(str(imap_email_id), "+FLAGS", "\\Seen")
            return True
        finally:
            socket.setdefaulttimeout(None)
            if mail is not None:
                with contextlib.suppress(Exception):
                    mail.close()
                with contextlib.suppress(Exception):
                    mail.logout()

    @handle_errors("loading email configuration", default_return=None)
    def _get_email_config(self) -> tuple[str, str, str, str] | None:
        if not all(
            [
                EMAIL_SMTP_SERVER,
                EMAIL_IMAP_SERVER,
                EMAIL_SMTP_USERNAME,
                EMAIL_SMTP_PASSWORD,
            ]
        ):
            raise ConfigurationError(
                "Email configuration incomplete. Missing required settings."
            )
        return (
            EMAIL_SMTP_SERVER,
            EMAIL_IMAP_SERVER,
            EMAIL_SMTP_USERNAME,
            EMAIL_SMTP_PASSWORD,
        )

    @handle_errors("extracting email body text", default_return="")
    def _receive_emails_sync__extract_body(self, msg: EmailMessage) -> str:
        """Extract plain text body from email message"""
        body_text = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                # Extract text from text/plain or text/html parts
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body_text = (
                                payload.decode(charset, errors="ignore")
                                if isinstance(payload, bytes)
                                else str(payload)
                            )
                            break  # Prefer plain text
                    except Exception as e:
                        logger.debug(f"Error decoding plain text part: {e}")
                elif content_type == "text/html" and not body_text:
                    # Fallback to HTML if no plain text found
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            html_text = (
                                payload.decode(charset, errors="ignore")
                                if isinstance(payload, bytes)
                                else str(payload)
                            )
                            body_text = html_to_plain_text(html_text)
                    except Exception as e:
                        logger.debug(f"Error decoding HTML part: {e}")
        else:
            # Single part message
            content_type = msg.get_content_type()
            if content_type == "text/plain" or content_type == "text/html":
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        charset = msg.get_content_charset() or "utf-8"
                        body_text = (
                            payload.decode(charset, errors="ignore")
                            if isinstance(payload, bytes)
                            else str(payload)
                        )
                        if content_type == "text/html":
                            body_text = html_to_plain_text(body_text)
                except Exception as e:
                    logger.debug(f"Error decoding message body: {e}")

        return body_text.strip()

    @handle_errors("performing email health check", default_return=False)
    async def health_check(self) -> bool:
        """Perform health check on email connections"""
        # Test both SMTP and IMAP connections
        # Use get_running_loop() first, fallback to new_event_loop() if no running loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop (shouldn't happen in async context, but handle gracefully)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        await loop.run_in_executor(None, self.initialize__test_smtp_connection)
        await loop.run_in_executor(None, self.initialize__test_imap_connection)
        return True
