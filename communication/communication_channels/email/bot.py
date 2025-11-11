# email_bot.py

import smtplib
import imaplib
import email
import asyncio
from email.mime.text import MIMEText
from email.header import decode_header
from typing import List, Dict, Any

from core.config import EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD
from core.logger import get_component_logger
from communication.communication_channels.base.base_channel import BaseChannel, ChannelType, ChannelStatus, ChannelConfig
from core.error_handling import handle_errors

# Route module-level logs to email component for consistency
email_logger = get_component_logger('email')
logger = email_logger

class EmailBotError(Exception):
    """Custom exception for email bot-related errors."""
    pass

class EmailBot(BaseChannel):
    @handle_errors("initializing email bot", default_return=None)
    def __init__(self, config: ChannelConfig = None):
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
                name='email',
                max_retries=3,
                retry_delay=1.0,
                backoff_multiplier=2.0
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
        if not all([EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD]):
            error_msg = "Email configuration incomplete. Missing required settings."
            self._set_status(ChannelStatus.ERROR, error_msg)
            return False

        # Test SMTP connection
        # Use get_running_loop() first, fallback to get_event_loop()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.initialize__test_smtp_connection)
        
        # Test IMAP connection
        await loop.run_in_executor(None, self.initialize__test_imap_connection)
        
        self._set_status(ChannelStatus.READY)
        logger.info("EmailBot initialized successfully.")
        return True

    @handle_errors("testing SMTP connection")
    def initialize__test_smtp_connection(self):
        """Test SMTP connection synchronously"""
        with smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, 465) as server:
            server.login(EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD)

    @handle_errors("testing IMAP connection")
    def initialize__test_imap_connection(self):
        """Test IMAP connection synchronously"""
        with imaplib.IMAP4_SSL(EMAIL_IMAP_SERVER) as mail:
            mail.login(EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD)

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
        # Use get_running_loop() first, fallback to get_event_loop()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.send_message__send_email_sync, recipient, message, kwargs)
        # Enhanced logging with message content
        message_preview = message[:50] + "..." if len(message) > 50 else message
        logger.info(f"Email sent to {recipient} | Content: '{message_preview}'")
        return True

    @handle_errors("sending email synchronously")
    def send_message__send_email_sync(self, recipient: str, message: str, kwargs: dict):
        """Send email synchronously"""
        subject = kwargs.get('subject', 'Personal Assistant Message')
        
        msg = MIMEText(message)
        msg['From'] = EMAIL_SMTP_USERNAME
        msg['To'] = recipient
        msg['Subject'] = subject

        with smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, 465) as server:
            server.login(EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD)
            server.sendmail(EMAIL_SMTP_USERNAME, recipient, msg.as_string())

    @handle_errors("receiving email messages", default_return=[])
    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Receive messages from email"""
        if not self.is_ready():
            logger.error("EmailBot is not ready to receive messages.")
            return []

        # Run the synchronous email receiving in a thread pool
        # Use get_running_loop() first, fallback to get_event_loop()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        messages = await loop.run_in_executor(None, self._receive_emails_sync)
        logger.info(f"Received {len(messages)} emails.")
        return messages

    @handle_errors("receiving emails synchronously", default_return=[])
    def _receive_emails_sync(self) -> List[Dict[str, Any]]:
        """Receive emails synchronously"""
        messages = []
        
        with imaplib.IMAP4_SSL(EMAIL_IMAP_SERVER) as mail:
            mail.login(EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD)
            mail.select("inbox")
            status, message_ids = mail.search(None, "ALL")
            email_ids = message_ids[0].split()

            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        email_subject = decode_header(msg["subject"])[0][0]
                        if isinstance(email_subject, bytes):
                            email_subject = email_subject.decode()
                        email_from = msg.get("from")
                        
                        # Extract email body text
                        body_text = self._receive_emails_sync__extract_body(msg)
                        
                        messages.append({
                            'from': email_from,
                            'subject': email_subject,
                            'body': body_text,
                            'message_id': email_id.decode()
                        })
        
        return messages
    
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
                            charset = part.get_content_charset() or 'utf-8'
                            body_text = payload.decode(charset, errors='ignore')
                            break  # Prefer plain text
                    except Exception as e:
                        logger.debug(f"Error decoding plain text part: {e}")
                elif content_type == "text/html" and not body_text:
                    # Fallback to HTML if no plain text found
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            html_text = payload.decode(charset, errors='ignore')
                            # Simple HTML stripping (remove tags)
                            import re
                            body_text = re.sub(r'<[^>]+>', '', html_text)
                            body_text = re.sub(r'\s+', ' ', body_text).strip()
                    except Exception as e:
                        logger.debug(f"Error decoding HTML part: {e}")
        else:
            # Single part message
            content_type = msg.get_content_type()
            if content_type == "text/plain" or content_type == "text/html":
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        charset = msg.get_content_charset() or 'utf-8'
                        body_text = payload.decode(charset, errors='ignore')
                        if content_type == "text/html":
                            # Simple HTML stripping
                            import re
                            body_text = re.sub(r'<[^>]+>', '', body_text)
                            body_text = re.sub(r'\s+', ' ', body_text).strip()
                except Exception as e:
                    logger.debug(f"Error decoding message body: {e}")
        
        return body_text.strip()

    @handle_errors("performing email health check", default_return=False)
    async def health_check(self) -> bool:
        """Perform health check on email connections"""
        # Test both SMTP and IMAP connections
        # Use get_running_loop() first, fallback to get_event_loop()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.initialize__test_smtp_connection)
        await loop.run_in_executor(None, self.initialize__test_imap_connection)
        return True

