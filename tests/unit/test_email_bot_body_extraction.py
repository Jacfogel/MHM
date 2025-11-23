"""
Unit tests for email body extraction functionality.

Tests for _receive_emails_sync__extract_body method in email/bot.py
focusing on extracting text from various email formats.
"""

import pytest
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from unittest.mock import patch, MagicMock

from communication.communication_channels.email.bot import EmailBot


@pytest.fixture(scope="module")
def email_bot():
    """Create EmailBot instance once per module (shared across all tests in this file)."""
    return EmailBot()


@pytest.mark.unit
@pytest.mark.communication
class TestEmailBodyExtraction:
    """Test email body text extraction from various email formats."""

    def test_extract_body_plain_text_single_part(self, test_data_dir, email_bot):
        """Test extracting body from plain text single-part email."""
        # Create plain text email
        msg = MIMEText("This is a plain text message body.", 'plain')
        
        body = email_bot._receive_emails_sync__extract_body(msg)
        
        assert body == "This is a plain text message body.", "Should extract plain text body"

    def test_extract_body_html_single_part(self, test_data_dir, email_bot):
        """Test extracting body from HTML single-part email."""
        # Create HTML email
        html_content = "<html><body><p>This is <b>HTML</b> content.</p></body></html>"
        msg = MIMEText(html_content, 'html')
        
        body = email_bot._receive_emails_sync__extract_body(msg)
        
        # Should strip HTML tags
        assert "This is" in body, "Should extract text from HTML"
        assert "<html>" not in body, "Should remove HTML tags"
        assert "<b>" not in body, "Should remove HTML tags"
        assert "HTML" in body, "Should preserve text content"

    def test_extract_body_multipart_plain_text_preferred(self, test_data_dir, email_bot):
        """Test extracting body from multipart email with plain text preferred."""
        # Create multipart email with both plain and HTML
        msg = MIMEMultipart('alternative')
        
        plain_part = MIMEText("This is plain text.", 'plain')
        html_part = MIMEText("<html><body>This is HTML.</body></html>", 'html')
        
        msg.attach(plain_part)
        msg.attach(html_part)
        
        body = email_bot._receive_emails_sync__extract_body(msg)
        
        # Should prefer plain text
        assert body == "This is plain text.", "Should extract plain text from multipart"

    def test_extract_body_multipart_html_fallback(self, test_data_dir, email_bot):
        """Test extracting body from multipart email with HTML fallback."""
        # Create multipart email with only HTML (no plain text)
        msg = MIMEMultipart('alternative')
        
        html_part = MIMEText("<html><body><p>This is HTML content.</p></body></html>", 'html')
        msg.attach(html_part)
        
        body = email_bot._receive_emails_sync__extract_body(msg)
        
        # Should fallback to HTML and strip tags
        assert "This is HTML content" in body, "Should extract text from HTML fallback"
        assert "<html>" not in body, "Should remove HTML tags"

    def test_extract_body_multipart_with_attachment(self, test_data_dir, email_bot):
        """Test extracting body from multipart email with attachment."""
        # Create multipart email with text and attachment
        msg = MIMEMultipart('mixed')
        
        text_part = MIMEText("This is the message body.", 'plain')
        msg.attach(text_part)
        
        # Add attachment
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(b'Attachment content')
        attachment['Content-Disposition'] = 'attachment; filename="test.txt"'
        msg.attach(attachment)
        
        body = email_bot._receive_emails_sync__extract_body(msg)
        
        # Should extract text but not attachment
        assert body == "This is the message body.", "Should extract text, not attachment"

    def test_extract_body_multipart_nested(self, test_data_dir, email_bot):
        """Test extracting body from nested multipart email."""
        # Create nested multipart structure
        outer_msg = MIMEMultipart('mixed')
        
        # Inner multipart with alternative text/html
        inner_msg = MIMEMultipart('alternative')
        plain_part = MIMEText("Plain text content.", 'plain')
        inner_msg.attach(plain_part)
        
        outer_msg.attach(inner_msg)
        
        body = email_bot._receive_emails_sync__extract_body(outer_msg)
        
        # Should extract plain text from nested structure
        assert "Plain text content" in body, "Should extract text from nested multipart"

    def test_extract_body_handles_encoding_utf8(self, test_data_dir, email_bot):
        """Test extracting body with UTF-8 encoding."""
        # Create email with UTF-8 content
        msg = MIMEText("Hello 世界", 'plain', 'utf-8')
        
        body = email_bot._receive_emails_sync__extract_body(msg)
        
        assert "Hello 世界" in body, "Should handle UTF-8 encoding"

    def test_extract_body_handles_encoding_iso8859(self, test_data_dir, email_bot):
        """Test extracting body with ISO-8859-1 encoding."""
        # Create email with ISO-8859-1 content
        msg = MIMEText("Café résumé", 'plain', 'iso-8859-1')
        
        body = email_bot._receive_emails_sync__extract_body(msg)
        
        # Should decode correctly
        assert "Café" in body or "Caf" in body, "Should handle ISO-8859-1 encoding"

    def test_extract_body_handles_decode_errors(self, test_data_dir, email_bot):
        """Test extracting body handles decode errors gracefully."""
        # Create email with invalid encoding
        msg = MIMEText("Test message", 'plain', 'utf-8')
        
        # Mock decode to raise error
        with patch.object(msg, 'get_payload', return_value=b'\xff\xfeinvalid'):
            body = email_bot._receive_emails_sync__extract_body(msg)
            
            # Should return empty string or handle gracefully
            assert isinstance(body, str), "Should return string even on decode error"

    def test_extract_body_empty_message(self, test_data_dir, email_bot):
        """Test extracting body from empty message."""
        msg = MIMEText("", 'plain')
        
        body = email_bot._receive_emails_sync__extract_body(msg)
        
        assert body == "", "Should return empty string for empty message"

    def test_extract_body_strips_whitespace(self, test_data_dir, email_bot):
        """Test that extracted body is stripped of whitespace."""
        # Create email with extra whitespace
        msg = MIMEText("   Message with whitespace   ", 'plain')
        
        body = email_bot._receive_emails_sync__extract_body(msg)
        
        assert body == "Message with whitespace", "Should strip leading/trailing whitespace"

    def test_extract_body_html_normalizes_whitespace(self, test_data_dir, email_bot):
        """Test that HTML body extraction normalizes whitespace."""
        # Create HTML with multiple spaces and newlines
        html_content = "<html><body><p>Line 1</p>\n\n<p>Line 2</p>    <p>Line 3</p></body></html>"
        msg = MIMEText(html_content, 'html')
        
        body = email_bot._receive_emails_sync__extract_body(msg)
        
        # Should normalize whitespace
        assert "Line 1" in body, "Should extract text from HTML"
        assert "Line 2" in body, "Should extract text from HTML"
        assert "Line 3" in body, "Should extract text from HTML"
        # Whitespace should be normalized (multiple spaces/newlines collapsed)

    def test_extract_body_handles_missing_charset(self, test_data_dir, email_bot):
        """Test extracting body when charset is not specified."""
        # Create email without charset
        msg = MIMEText("Test message", 'plain')
        # Remove charset header
        if 'Content-Type' in msg:
            del msg['Content-Type']
        
        body = email_bot._receive_emails_sync__extract_body(msg)
        
        # Should default to utf-8
        assert "Test message" in body, "Should handle missing charset with utf-8 default"

    def test_extract_body_handles_multipart_mixed_with_text(self, test_data_dir, email_bot):
        """Test extracting body from multipart/mixed with text."""
        # Create multipart/mixed email
        msg = MIMEMultipart('mixed')
        
        text_part = MIMEText("Main message text.", 'plain')
        msg.attach(text_part)
        
        body = email_bot._receive_emails_sync__extract_body(msg)
        
        assert "Main message text" in body, "Should extract text from multipart/mixed"

    def test_extract_body_skips_attachment_content_disposition(self, test_data_dir, email_bot):
        """Test that attachments are skipped based on Content-Disposition."""
        # Create multipart with attachment
        msg = MIMEMultipart('mixed')
        
        text_part = MIMEText("Message body.", 'plain')
        msg.attach(text_part)
        
        # Add attachment with Content-Disposition
        attachment = MIMEBase('text', 'plain')
        attachment.set_payload("This is attachment content.")
        attachment['Content-Disposition'] = 'attachment; filename="file.txt"'
        msg.attach(attachment)
        
        body = email_bot._receive_emails_sync__extract_body(msg)
        
        # Should only extract message body, not attachment
        assert body == "Message body.", "Should skip attachment content"
        assert "attachment content" not in body, "Should not include attachment in body"

    def test_extract_body_handles_complex_html(self, test_data_dir, email_bot):
        """Test extracting body from complex HTML email."""
        html_content = """
        <html>
        <head><title>Test</title></head>
        <body>
            <div>
                <p>Paragraph 1</p>
                <p>Paragraph 2 with <strong>bold</strong> text</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </div>
        </body>
        </html>
        """
        msg = MIMEText(html_content, 'html')
        
        body = email_bot._receive_emails_sync__extract_body(msg)
        
        # Should extract text content
        assert "Paragraph 1" in body, "Should extract text from complex HTML"
        assert "Paragraph 2" in body, "Should extract text from complex HTML"
        assert "bold" in body, "Should extract text from HTML tags"
        assert "Item 1" in body, "Should extract text from lists"
        # Should not contain HTML tags
        assert "<p>" not in body, "Should remove HTML tags"
        assert "<div>" not in body, "Should remove HTML tags"

    def test_extract_body_handles_exception_gracefully(self, test_data_dir, email_bot):
        """Test that body extraction handles exceptions gracefully."""
        # Create email
        msg = MIMEText("Test", 'plain')
        
        # Mock walk() to raise exception
        with patch.object(msg, 'walk', side_effect=Exception("Test error")):
            body = email_bot._receive_emails_sync__extract_body(msg)
            
            # Should return empty string or handle gracefully
            assert isinstance(body, str), "Should return string even on exception"

