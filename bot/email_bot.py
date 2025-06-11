# email_bot.py

import smtplib
import imaplib
import email
import asyncio
from email.mime.text import MIMEText
from email.header import decode_header
from typing import List, Dict, Any

from core.config import EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD
from core.logger import get_logger
from bot.base_channel import BaseChannel, ChannelType, ChannelStatus, ChannelConfig

logger = get_logger(__name__)

class EmailBotError(Exception):
    """Custom exception for email bot-related errors."""
    pass

class EmailBot(BaseChannel):
    def __init__(self, config: ChannelConfig = None):
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
    def channel_type(self) -> ChannelType:
        return ChannelType.SYNC  # Email operations are synchronous

    async def initialize(self) -> bool:
        """Initialize the email bot"""
        self._set_status(ChannelStatus.INITIALIZING)
        
        try:
            # Validate configuration
            if not all([EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD]):
                error_msg = "Email configuration incomplete. Missing required settings."
                self._set_status(ChannelStatus.ERROR, error_msg)
                return False

            # Test SMTP connection
            await asyncio.get_event_loop().run_in_executor(
                None, self._test_smtp_connection
            )
            
            # Test IMAP connection
            await asyncio.get_event_loop().run_in_executor(
                None, self._test_imap_connection
            )
            
            self._set_status(ChannelStatus.READY)
            logger.info("EmailBot initialized successfully.")
            return True
            
        except Exception as e:
            error_msg = f"Failed to initialize EmailBot: {e}"
            self._set_status(ChannelStatus.ERROR, error_msg)
            logger.error(error_msg)
            return False

    def _test_smtp_connection(self):
        """Test SMTP connection synchronously"""
        with smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, 465) as server:
            server.login(EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD)

    def _test_imap_connection(self):
        """Test IMAP connection synchronously"""
        with imaplib.IMAP4_SSL(EMAIL_IMAP_SERVER) as mail:
            mail.login(EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD)

    async def shutdown(self) -> bool:
        """Shutdown the email bot"""
        try:
            self._set_status(ChannelStatus.STOPPED)
            logger.info("EmailBot stopped.")
            return True
        except Exception as e:
            logger.error(f"Failed to stop EmailBot: {e}")
            return False

    async def send_message(self, recipient: str, message: str, **kwargs) -> bool:
        """Send message via email"""
        if not self.is_ready():
            logger.error("EmailBot is not ready to send messages.")
            return False

        try:
            # Run the synchronous email sending in a thread pool
            await asyncio.get_event_loop().run_in_executor(
                None, self._send_email_sync, recipient, message, kwargs
            )
            logger.info(f"Email sent to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _send_email_sync(self, recipient: str, message: str, kwargs: dict):
        """Send email synchronously"""
        subject = kwargs.get('subject', 'Personal Assistant Message')
        
        msg = MIMEText(message)
        msg['From'] = EMAIL_SMTP_USERNAME
        msg['To'] = recipient
        msg['Subject'] = subject

        with smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, 465) as server:
            server.login(EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD)
            server.sendmail(EMAIL_SMTP_USERNAME, recipient, msg.as_string())

    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Receive messages from email"""
        if not self.is_ready():
            logger.error("EmailBot is not ready to receive messages.")
            return []

        try:
            # Run the synchronous email receiving in a thread pool
            messages = await asyncio.get_event_loop().run_in_executor(
                None, self._receive_emails_sync
            )
            logger.info(f"Received {len(messages)} emails.")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to receive emails: {e}")
            return []

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
                        messages.append({
                            'from': email_from,
                            'subject': email_subject,
                            'message_id': email_id.decode()
                        })
        
        return messages

    async def health_check(self) -> bool:
        """Perform health check on email connections"""
        try:
            # Test both SMTP and IMAP connections
            await asyncio.get_event_loop().run_in_executor(
                None, self._test_smtp_connection
            )
            await asyncio.get_event_loop().run_in_executor(
                None, self._test_imap_connection
            )
            return True
        except Exception as e:
            logger.error(f"Email health check failed: {e}")
            return False

    # Legacy methods for backward compatibility
    def start(self):
        """Legacy start method"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(self.initialize())
        if not success:
            raise EmailBotError("Failed to initialize EmailBot")

    def stop(self):
        """Legacy stop method"""
        if asyncio.get_event_loop().is_running():
            asyncio.create_task(self.shutdown())
        else:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.shutdown())

    def is_initialized(self):
        """Legacy method for backward compatibility"""
        return self.is_ready()
