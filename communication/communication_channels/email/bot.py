# email_bot.py

import smtplib
import imaplib
import asyncio
import time
import contextlib
from email.mime.text import MIMEText
from email.header import decode_header, make_header
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
from communication.core.message_send_result import CHANNEL_SEND_UNCONFIRMED
from core.error_handling import handle_errors, ConfigurationError

# Route module-level logs to email component for consistency
email_logger = get_component_logger("email")
logger = email_logger

_REPLY_KINDS = {"checkin", "task_reminder", "message"}
# Login can succeed while the server is slow to accept the message body.
# 10 seconds expired during sendmail on 2026-09-29; 30 seconds stays bounded.
_SMTP_SEND_TIMEOUT_SECONDS = 30
_SMTP_SEND_ATTEMPTS = 2
_SMTP_RETRY_PAUSE_SECONDS = 1
_TRANSIENT_SMTP_ERRORS = (smtplib.SMTPServerDisconnected, TimeoutError, ConnectionError)
_IMAP_RECEIVE_ATTEMPTS = 2
_IMAP_RETRY_PAUSE_SECONDS = 1


@handle_errors("decoding an email subject", default_return="")
def decode_email_subject(subject: Any) -> str:
    """Decode every encoded-word fragment using its declared charset."""
    if subject is None:
        return ""
    return str(make_header(decode_header(str(subject))))


@handle_errors("reading IMAP UID validity", default_return="")
def imap_uid_validity(mail: Any) -> str:
    """Return the selected mailbox UIDVALIDITY value, when advertised."""
    response = getattr(mail, "response", None)
    if not callable(response):
        return ""
    raw_response: Any = response("UIDVALIDITY")
    if not isinstance(raw_response, (list, tuple)) or len(raw_response) < 2:
        return ""
    values = raw_response[1]
    if not isinstance(values, (list, tuple)) or not values:
        return ""
    value = values[0]
    if isinstance(value, bytes):
        return value.decode("ascii", errors="ignore").strip()
    return str(value or "").strip()


# error_handling_exclude: decorator recovery would retry the write and could send the body twice
def _send_smtp_payload(original_send, data, handed_off: dict):
    """Send one SMTP payload and note when it is the finished message body.

    A dropped write is logged and raised again. The error decorator is not
    used here, because its recovery step would write the body a second time.
    """
    try:
        result = original_send(data)
    except Exception as exc:
        logger.warning(f"SMTP payload was not fully written: {exc}")
        raise
    if isinstance(data, (bytes, bytearray)) and data.endswith(b"\r\n.\r\n"):
        handed_off["sent"] = True
    return result


@handle_errors("noting when the SMTP body is sent", default_return=None)
def _watch_smtp_body(server, handed_off: dict) -> None:
    """Mark when sendmail has written the message body, before the acceptance reply."""
    original_send = server.send
    server.send = lambda data: _send_smtp_payload(original_send, data, handed_off)


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


@handle_errors("reading the attempted email message id", default_return=None)
def attempted_email_message_id(manager) -> str | None:
    """Return the Message-ID from the latest email attempt, including a failed send."""
    channels = getattr(manager, "_channels_dict", None)
    if not isinstance(channels, dict):
        return None
    channel = channels.get("email")
    outbound = getattr(channel, "last_outbound_message_id", None)
    if isinstance(outbound, str) and outbound.strip():
        return outbound.strip()
    return None


@handle_errors("choosing a message id for retry", default_return=None)
def message_id_for_retry(manager, requested: str | None = None) -> str | None:
    """Keep the Message-ID from this attempt so a retry does not mint a second one."""
    attempted = attempted_email_message_id(manager)
    if attempted:
        return attempted
    if isinstance(requested, str) and requested.strip():
        return requested.strip()
    return None


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
        self._last_receive_error = ""

    @handle_errors("reading the last email receive error", default_return="")
    def consume_receive_error(self) -> str:
        """Return and clear the most recent inbox receive failure."""
        error = self._last_receive_error
        self._last_receive_error = ""
        return error

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
    async def send_message(self, recipient: str, message: str, **kwargs) -> bool | str:
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
        sent = await loop.run_in_executor(
            None, self.send_message__send_email_sync, recipient, message, kwargs
        )
        if sent == CHANNEL_SEND_UNCONFIRMED:
            logger.warning(
                f"Email to {recipient} was handed to the server, but acceptance was not confirmed"
            )
            return CHANNEL_SEND_UNCONFIRMED
        if sent is not True:
            logger.error(f"Email send failed to {recipient}")
            return False
        message_preview = message[:50] + "..." if len(message) > 50 else message
        logger.info(f"Email sent to {recipient} | Content: '{message_preview}'")
        return True

    @handle_errors(
        "sending email synchronously",
        default_return=False,
        user_friendly=False,
    )
    def send_message__send_email_sync(
        self, recipient: str, message: str, kwargs: dict
    ) -> bool | str:
        """Send email synchronously and remember its Message-ID for later replies.

        Returns True only after the server accepts the message.
        A dropped connection is retried once when it happens before the body is sent.
        If the body was already written and the acceptance reply is lost, returns
        "unconfirmed" so the caller does not send a second copy.
        """
        self.last_outbound_message_id = None
        config = self._get_email_config()
        if not config:
            return False
        smtp_server, _, smtp_user, smtp_password = config
        subject = str(kwargs.get("subject") or "Personal Assistant Message")
        in_reply_to = normalize_message_id(kwargs.get("in_reply_to"))
        if in_reply_to and not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
        message_id = build_outbound_message_id(smtp_user, kwargs.get("message_id"))

        user_id = kwargs.get("user_id")
        context_user_id = user_id.strip() if isinstance(user_id, str) else ""
        if context_user_id and not record_outbound_email(
            context_user_id,
            message_id,
            kind=reply_kind_from_send_kwargs(kwargs),
            task_id=str(kwargs.get("task_id") or ""),
            subject=subject,
        ):
            logger.error(
                f"Email reply context could not be stored for user {context_user_id}; send aborted"
            )
            return False

        msg = MIMEText(message)
        msg["From"] = smtp_user
        msg["To"] = recipient
        msg["Subject"] = subject
        msg["Message-ID"] = message_id
        if message_id:
            self.last_outbound_message_id = message_id
        if in_reply_to:
            references = str(kwargs.get("references") or "").strip()
            if in_reply_to not in references:
                references = f"{references} {in_reply_to}".strip()
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = references

        outcome = None
        for attempt in range(1, _SMTP_SEND_ATTEMPTS + 1):
            try:
                with smtplib.SMTP_SSL(
                    smtp_server, 465, timeout=_SMTP_SEND_TIMEOUT_SECONDS
                ) as server:
                    server.login(smtp_user, smtp_password)
                    handed_off = {"sent": False}
                    _watch_smtp_body(server, handed_off)
                    try:
                        server.sendmail(smtp_user, recipient, msg.as_string())
                    except _TRANSIENT_SMTP_ERRORS as exc:
                        if handed_off["sent"]:
                            logger.warning(
                                f"Email to {recipient} was sent but the server did not confirm acceptance: {exc}"
                            )
                            outcome = CHANNEL_SEND_UNCONFIRMED
                        else:
                            raise
                    else:
                        outcome = True
            except _TRANSIENT_SMTP_ERRORS as exc:
                if outcome == CHANNEL_SEND_UNCONFIRMED:
                    break
                if attempt >= _SMTP_SEND_ATTEMPTS:
                    logger.warning(
                        f"Email send failed after {attempt} attempts to {recipient}: {exc}"
                    )
                    return False
                logger.warning(
                    f"Email send attempt {attempt} to {recipient} lost the SMTP connection before the message was sent; retrying: {exc}"
                )
                time.sleep(_SMTP_RETRY_PAUSE_SECONDS)
                continue
            except Exception as exc:
                if outcome == CHANNEL_SEND_UNCONFIRMED:
                    logger.warning(
                        f"Email to {recipient} was not confirmed, and closing the connection failed: {exc}"
                    )
                    break
                raise
            break

        if outcome not in (True, CHANNEL_SEND_UNCONFIRMED):
            return False

        self.last_outbound_message_id = message_id
        return outcome

    # devtools: intentional[duplicate-functions]: channel_receive_messages_contract
    @handle_errors("receiving email messages", default_return=[])
    async def receive_messages(self) -> list[dict[str, Any]]:
        """Receive messages from email"""
        if not self.is_ready():
            self._last_receive_error = "EmailBot is not ready to receive messages"
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

        try:
            messages = await loop.run_in_executor(None, self._receive_emails_sync)
        except Exception as exc:
            error_message = str(exc).strip() or "no error message"
            self._last_receive_error = f"{type(exc).__name__}: {error_message}"
            raise
        if len(messages) > 0:
            logger.info(f"Received {len(messages)} new email(s)")
        return messages

    @handle_errors("receiving emails synchronously", default_return=[])
    def _receive_emails_sync(self) -> list[dict[str, Any]]:
        """Receive emails synchronously - only fetches UNSEEN emails for efficiency"""
        self._last_receive_error = ""
        config = self._get_email_config()
        if not config:
            self._last_receive_error = "Email configuration is unavailable"
            return []
        _, imap_server, smtp_user, smtp_password = config

        last_error: Exception | None = None
        for attempt in range(1, _IMAP_RECEIVE_ATTEMPTS + 1):
            try:
                return self._receive_emails_sync_once(
                    imap_server, smtp_user, smtp_password
                )
            except TimeoutError as exc:
                last_error = exc
                current_time = time.time()
                time_since_last_log = current_time - EmailBot._last_timeout_log_time
                if time_since_last_log >= EmailBot._timeout_log_interval:
                    logger.debug(
                        "IMAP socket timeout after 8 seconds "
                        f"(attempt {attempt}/{_IMAP_RECEIVE_ATTEMPTS}): {exc}"
                    )
                    EmailBot._last_timeout_log_time = current_time
            except imaplib.IMAP4.abort as exc:
                last_error = exc
                logger.debug(
                    "IMAP connection aborted "
                    f"(attempt {attempt}/{_IMAP_RECEIVE_ATTEMPTS}): {exc}"
                )
            except Exception as exc:
                # Preserve the list-returning channel contract while making the
                # failure observable to the outage-aware inbound poller.
                last_error = exc
                logger.debug(
                    "IMAP receive failed "
                    f"(attempt {attempt}/{_IMAP_RECEIVE_ATTEMPTS}): "
                    f"{type(exc).__name__}: {exc}"
                )

            if attempt < _IMAP_RECEIVE_ATTEMPTS:
                time.sleep(_IMAP_RETRY_PAUSE_SECONDS)

        if last_error is not None:
            error_message = str(last_error).strip() or "no error message"
            self._last_receive_error = (
                f"{type(last_error).__name__}: {error_message}"
            )
        return []

    # error_handling_exclude: exceptions are handled by the bounded retry wrapper above
    def _receive_emails_sync_once(
        self, imap_server: str, smtp_user: str, smtp_password: str
    ) -> list[dict[str, Any]]:
        """Fetch one bounded batch using stable IMAP UIDs."""
        messages: list[dict[str, Any]] = []
        mail = None
        try:
            logger.debug(f"Connecting to IMAP server: {imap_server}")
            mail = imaplib.IMAP4_SSL(imap_server, timeout=8)
            logger.debug("Attempting IMAP login")
            mail.login(smtp_user, smtp_password)
            logger.debug("IMAP login successful")

            logger.debug("Selecting inbox")
            status, _select_data = mail.select("inbox")
            if status != "OK":
                raise EmailBotError(f"IMAP inbox selection failed: {status}")
            uid_validity = imap_uid_validity(mail)

            logger.debug("Searching for UNSEEN email UIDs")
            status, uid_data = mail.uid("search", "UNSEEN")
            if status != "OK":
                raise EmailBotError(f"IMAP unread search failed: {status}")
            if not uid_data or not uid_data[0]:
                logger.debug("No UNSEEN emails found")
                return messages

            email_uids = uid_data[0].split()
            # Drain the oldest unread messages first so a busy inbox cannot starve them.
            email_uids = email_uids[:20]
            logger.info(f"Processing {len(email_uids)} new emails")

            fetched_uids: list[bytes] = []
            for email_uid in email_uids:
                try:
                    status, msg_data = mail.uid(
                        "fetch", email_uid, "(BODY.PEEK[])"
                    )
                    if status != "OK":
                        logger.debug(
                            f"Failed to fetch email UID {email_uid!r}: {status}"
                        )
                        continue

                    for response_part in msg_data:
                        if not isinstance(response_part, tuple):
                            continue
                        msg = BytesParser(policy=email_policy_default).parsebytes(
                            response_part[1]
                        )
                        email_subject = decode_email_subject(msg.get("subject"))
                        email_from = msg.get("from")
                        body_text = self._receive_emails_sync__extract_body(msg)
                        uid_text = email_uid.decode("ascii")
                        messages.append(
                            {
                                "from": email_from,
                                "subject": email_subject,
                                "body": body_text,
                                "imap_uid": uid_text,
                                "imap_uid_validity": uid_validity,
                                # Compatibility alias for callers that have not migrated yet.
                                "imap_email_id": uid_text,
                                "message_id": str(msg.get("Message-ID") or ""),
                                "in_reply_to": str(msg.get("In-Reply-To") or ""),
                                "references": str(msg.get("References") or ""),
                            }
                        )
                        fetched_uids.append(email_uid)
                        break
                except (TimeoutError, imaplib.IMAP4.abort):
                    raise
                except Exception as exc:
                    logger.warning(f"Error processing email UID {email_uid!r}: {exc}")

            if fetched_uids:
                logger.debug(
                    f"Fetched {len(fetched_uids)} unread emails without marking them seen"
                )
            logger.debug("Email processing completed successfully")
            return messages
        finally:
            if mail is not None:
                with contextlib.suppress(Exception):
                    mail.close()
                with contextlib.suppress(Exception):
                    mail.logout()

    @handle_errors("marking email message seen", default_return=False)
    async def mark_message_seen(
        self, imap_uid: str, *, imap_uid_validity: str = ""
    ) -> bool:
        """Mark one inbox message read after it has been handled."""
        if not imap_uid or not self.is_ready():
            return False
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return bool(
            await loop.run_in_executor(
                None,
                self._mark_message_seen_sync,
                imap_uid,
                imap_uid_validity,
            )
        )

    @handle_errors("marking email message seen synchronously", default_return=False)
    def _mark_message_seen_sync(
        self, imap_uid: str, expected_uid_validity: str = ""
    ) -> bool:
        """Mark one IMAP UID \\Seen and verify that the server accepted it."""
        config = self._get_email_config()
        if not config or not imap_uid:
            return False
        _, imap_server, smtp_user, smtp_password = config
        mail = None
        try:
            mail = imaplib.IMAP4_SSL(imap_server, timeout=8)
            mail.login(smtp_user, smtp_password)
            status, _select_data = mail.select("inbox")
            if status != "OK":
                logger.warning(f"Cannot mark email read; inbox selection failed: {status}")
                return False
            current_uid_validity = imap_uid_validity(mail)
            if expected_uid_validity and current_uid_validity != expected_uid_validity:
                logger.warning(
                    "Cannot mark email read because mailbox UIDVALIDITY changed "
                    f"from {expected_uid_validity} to {current_uid_validity or 'unknown'}"
                )
                return False
            status, _store_data = mail.uid(
                "store", str(imap_uid), "+FLAGS", r"(\Seen)"
            )
            if status != "OK":
                logger.warning(
                    f"IMAP server rejected marking UID {imap_uid} read: {status}"
                )
                return False
            return True
        finally:
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
