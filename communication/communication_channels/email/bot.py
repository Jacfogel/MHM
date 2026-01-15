# email_bot.py

import smtplib
import imaplib
import email
import asyncio
import time
from email.mime.text import MIMEText
from email.header import decode_header
from typing import List, Dict, Any, Optional, Tuple

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
from core.error_handling import handle_errors, ConfigurationError

# Route module-level logs to email component for consistency
email_logger = get_component_logger("email")
logger = email_logger


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

    @property
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
        """Send email synchronously"""
        config = self._get_email_config()
        if not config:
            return
        smtp_server, _, smtp_user, smtp_password = config
        subject = kwargs.get("subject", "Personal Assistant Message")

        msg = MIMEText(message)
        msg["From"] = smtp_user
        msg["To"] = recipient
        msg["Subject"] = subject

        # Use 10 second timeout to prevent indefinite hangs (slightly longer than IMAP for TLS handshake)
        with smtplib.SMTP_SSL(smtp_server, 465, timeout=10) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipient, msg.as_string())

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
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    if status != "OK":
                        logger.debug(f"Failed to fetch email {email_id}: {status}")
                        continue

                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
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
                                    "message_id": email_id.decode(),
                                }
                            )
                            # Track this email as successfully processed
                            processed_email_ids.append(email_id)
                            break  # Only process first valid response part
                except Exception as e:
                    logger.warning(f"Error processing email {email_id}: {e}")
                    continue  # Continue with next email even if one fails

            # Mark successfully processed emails as SEEN to avoid re-fetching them
            if processed_email_ids:
                try:
                    # Mark all successfully processed email IDs as SEEN
                    for email_id in processed_email_ids:
                        mail.store(email_id, "+FLAGS", "\\Seen")
                    logger.debug(f"Marked {len(processed_email_ids)} emails as SEEN")
                except Exception as e:
                    logger.warning(f"Failed to mark emails as SEEN: {e}")

            logger.debug("Email processing completed successfully")
            mail.close()
            mail.logout()
        except socket.timeout as e:
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
    def _receive_emails_sync__extract_body(self, msg: email.message.Message) -> str:
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
                            body_text = payload.decode(charset, errors="ignore")
                            break  # Prefer plain text
                    except Exception as e:
                        logger.debug(f"Error decoding plain text part: {e}")
                elif content_type == "text/html" and not body_text:
                    # Fallback to HTML if no plain text found
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            html_text = payload.decode(charset, errors="ignore")
                            # Simple HTML stripping (remove tags)
                            import re

                            body_text = re.sub(r"<[^>]+>", "", html_text)
                            body_text = re.sub(r"\s+", " ", body_text).strip()
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
                        body_text = payload.decode(charset, errors="ignore")
                        if content_type == "text/html":
                            # Simple HTML stripping
                            import re

                            body_text = re.sub(r"<[^>]+>", "", body_text)
                            body_text = re.sub(r"\s+", " ", body_text).strip()
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
