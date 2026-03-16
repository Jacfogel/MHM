"""Gap-coverage unit tests for communication email bot."""

from __future__ import annotations

import asyncio
from email.message import EmailMessage

import pytest

from communication.communication_channels.base.base_channel import ChannelStatus
from communication.communication_channels.email.bot import EmailBot


class _ExecutorLoop:
    async def run_in_executor(self, executor, func, *args):
        return func(*args)


class _FakeImapMailbox:
    def __init__(self, search_result=None, fetch_map=None, search_error=None):
        if search_result is None:
            search_result = ("OK", [b""])
        self.search_result = search_result
        self.fetch_map = fetch_map or {}
        self.search_error = search_error
        self.store_calls = []
        self.closed = False
        self.logged_out = False

    def login(self, user, password):
        return "OK"

    def select(self, mailbox):
        return "OK", []

    def search(self, *_args):
        if self.search_error is not None:
            raise self.search_error
        return self.search_result

    def fetch(self, email_id, _what):
        result = self.fetch_map.get(email_id)
        if isinstance(result, Exception):
            raise result
        return result

    def store(self, email_id, flags_mode, flags_value):
        self.store_calls.append((email_id, flags_mode, flags_value))
        return "OK"

    def close(self):
        self.closed = True

    def logout(self):
        self.logged_out = True


@pytest.mark.unit
@pytest.mark.communication
class TestEmailBotGapCoverage:
    def test_get_email_config_missing_values_returns_none(self, monkeypatch):
        bot = EmailBot()
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.EMAIL_SMTP_SERVER", None
        )
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.EMAIL_IMAP_SERVER", None
        )
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.EMAIL_SMTP_USERNAME", None
        )
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.EMAIL_SMTP_PASSWORD", None
        )
        assert bot._get_email_config() is None

    def test_sync_connection_helpers_return_early_without_config(self, monkeypatch):
        bot = EmailBot()
        monkeypatch.setattr(bot, "_get_email_config", lambda: None)

        smtp_called = []
        imap_called = []
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.smtplib.SMTP_SSL",
            lambda *args, **kwargs: smtp_called.append(True),
        )
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.imaplib.IMAP4_SSL",
            lambda *args, **kwargs: imap_called.append(True),
        )

        bot.initialize__test_smtp_connection()
        bot.initialize__test_imap_connection()
        bot.send_message__send_email_sync("to@example.com", "hello", {})
        assert bot._receive_emails_sync() == []

        assert smtp_called == []
        assert imap_called == []

    def test_initialize_send_receive_health_use_fallback_event_loop(self, monkeypatch):
        bot = EmailBot()
        bot._set_status(ChannelStatus.READY)

        fake_loop = _ExecutorLoop()
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.asyncio.get_running_loop",
            lambda: (_ for _ in ()).throw(RuntimeError("no running loop")),
        )
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.asyncio.new_event_loop",
            lambda: fake_loop,
        )
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.asyncio.set_event_loop",
            lambda loop: None,
        )
        monkeypatch.setattr(bot, "_get_email_config", lambda: ("smtp", "imap", "user", "pass"))
        monkeypatch.setattr(bot, "initialize__test_smtp_connection", lambda: None)
        monkeypatch.setattr(bot, "initialize__test_imap_connection", lambda: None)
        monkeypatch.setattr(bot, "send_message__send_email_sync", lambda *args: None)
        monkeypatch.setattr(bot, "_receive_emails_sync", lambda: [{"id": "1"}])

        assert asyncio.run(bot.initialize()) is True
        assert asyncio.run(bot.send_message("u@example.com", "msg", subject="x")) is True
        received = asyncio.run(bot.receive_messages())
        assert len(received) == 1
        assert asyncio.run(bot.health_check()) is True

    def test_receive_emails_sync_no_unseen_branch(self, monkeypatch):
        bot = EmailBot()
        mailbox = _FakeImapMailbox(search_result=("OK", [b""]))
        monkeypatch.setattr(bot, "_get_email_config", lambda: ("smtp", "imap", "user", "pass"))
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.imaplib.IMAP4_SSL",
            lambda *args, **kwargs: mailbox,
        )

        messages = bot._receive_emails_sync()
        assert messages == []
        assert mailbox.closed is True
        assert mailbox.logged_out is True

    def test_receive_emails_sync_processes_and_marks_seen(self, monkeypatch):
        bot = EmailBot()

        msg = EmailMessage()
        # Encoded-word form yields bytes from decode_header path.
        msg["subject"] = "=?utf-8?b?VGVzdCBTdWJqZWN0?="
        msg["from"] = "sender@example.com"
        msg.set_content("Body text")
        raw_bytes = msg.as_bytes()

        fetch_map = {
            b"1": ("OK", [(None, raw_bytes)]),
            b"2": RuntimeError("failed fetch"),
        }
        mailbox = _FakeImapMailbox(search_result=("OK", [b"1 2"]), fetch_map=fetch_map)

        monkeypatch.setattr(bot, "_get_email_config", lambda: ("smtp", "imap", "user", "pass"))
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.imaplib.IMAP4_SSL",
            lambda *args, **kwargs: mailbox,
        )

        messages = bot._receive_emails_sync()
        assert len(messages) == 1
        assert messages[0]["from"] == "sender@example.com"
        assert messages[0]["subject"] == "Test Subject"
        assert mailbox.store_calls == [(b"1", "+FLAGS", "\\Seen")]
        assert mailbox.closed is True
        assert mailbox.logged_out is True

    def test_receive_emails_sync_timeout_cleanup_and_rate_limit(self, monkeypatch):
        bot = EmailBot()
        bot._last_timeout_log_time = 0

        mailbox = _FakeImapMailbox(search_error=TimeoutError("timed out"))
        monkeypatch.setattr(bot, "_get_email_config", lambda: ("smtp", "imap", "user", "pass"))
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.imaplib.IMAP4_SSL",
            lambda *args, **kwargs: mailbox,
        )
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.time.time",
            lambda: 9999999,
        )

        messages = bot._receive_emails_sync()
        assert messages == []
        assert mailbox.closed is True
        assert mailbox.logged_out is True

    def test_extract_body_exception_branches(self):
        bot = EmailBot()

        multipart = EmailMessage()
        multipart.set_type("multipart/mixed")
        attachment = EmailMessage()
        attachment.add_header("Content-Disposition", "attachment; filename=x.txt")
        attachment.set_type("text/plain")
        attachment.set_payload("ignored")
        multipart.attach(attachment)

        broken_plain = EmailMessage()
        broken_plain.set_type("text/plain")
        broken_plain.get_payload = lambda decode=True: (_ for _ in ()).throw(RuntimeError("plain decode fail"))  # type: ignore[reportAttributeAccessIssue]
        multipart.attach(broken_plain)

        broken_html = EmailMessage()
        broken_html.set_type("text/html")
        broken_html.get_payload = lambda decode=True: (_ for _ in ()).throw(RuntimeError("html decode fail"))  # type: ignore[reportAttributeAccessIssue]
        multipart.attach(broken_html)

        assert bot._receive_emails_sync__extract_body(multipart) == ""

        single_html = EmailMessage()
        single_html.set_type("text/html")
        single_html.get_payload = lambda decode=True: (_ for _ in ()).throw(RuntimeError("single decode fail"))  # type: ignore[reportAttributeAccessIssue]
        assert bot._receive_emails_sync__extract_body(single_html) == ""
