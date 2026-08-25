"""Manual-checklist leftover tests for email delivery formatting and SMTP failures."""

from __future__ import annotations

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from communication.communication_channels.base.base_channel import ChannelStatus
from communication.communication_channels.email.bot import EmailBot
from communication.reminders.reminder_dispatcher import TaskReminderDispatcher


@pytest.mark.behavior
@pytest.mark.communication
def test_task_reminder_email_smtp_payload_has_subject_and_body():
    task = {
        "id": "t1",
        "title": "Drink water",
        "description": "A short glass with lunch",
        "priority": "high",
        "due": {"date": "2026-08-24", "time": "12:00"},
    }
    body = TaskReminderDispatcher(MagicMock()).create_task_reminder_message(task)
    assert "Drink water" in body
    assert "A short glass with lunch" in body

    bot = EmailBot()
    bot._set_status(ChannelStatus.READY)
    smtp_cm = MagicMock()
    server = MagicMock()
    smtp_cm.__enter__.return_value = server
    config = ("smtp.test.com", "imap.test.com", "bot@test.com", "secret")

    with (
        patch(
            "communication.communication_channels.email.bot.smtplib.SMTP_SSL",
            return_value=smtp_cm,
        ) as smtp_cls,
        patch.object(bot, "_get_email_config", return_value=config),
    ):
        bot.send_message__send_email_sync(
            "person@example.com",
            body,
            {"subject": "Personal Assistant Message"},
        )

    smtp_cls.assert_called_once()
    assert smtp_cls.call_args.kwargs.get("timeout") == 10 or (
        len(smtp_cls.call_args.args) >= 3 and smtp_cls.call_args.args[2] == 10
    )
    server.login.assert_called_once_with("bot@test.com", "secret")
    server.sendmail.assert_called_once()
    from email import message_from_string

    _from, to_addr, payload = server.sendmail.call_args[0]
    assert to_addr == "person@example.com"
    assert "Personal Assistant Message" in payload
    parsed = message_from_string(payload)
    body_bytes = parsed.get_payload(decode=True)
    assert body_bytes is not None
    if isinstance(body_bytes, bytes):
        text = body_bytes.decode("utf-8")
    else:
        text = str(body_bytes)
    assert "Drink water" in text
    assert "person@example.com" in payload


@pytest.mark.behavior
@pytest.mark.communication
def test_email_send_smtp_auth_failure_logs_and_does_not_raise():
    bot = EmailBot()
    bot._set_status(ChannelStatus.READY)
    config = ("smtp.test.com", "imap.test.com", "bot@test.com", "secret")

    with (
        patch(
            "communication.communication_channels.email.bot.smtplib.SMTP_SSL",
            side_effect=smtplib.SMTPAuthenticationError(535, b"Authentication failed"),
        ),
        patch.object(bot, "_get_email_config", return_value=config),
    ):
        result = bot.send_message__send_email_sync(
            "person@example.com", "hello", {"subject": "Test"}
        )

    assert result is None


@pytest.mark.behavior
@pytest.mark.communication
def test_email_send_uses_smtp_timeout():
    bot = EmailBot()
    bot._set_status(ChannelStatus.READY)
    smtp_cm = MagicMock()
    smtp_cm.__enter__.return_value = MagicMock()
    config = ("smtp.test.com", "imap.test.com", "bot@test.com", "secret")

    with (
        patch(
            "communication.communication_channels.email.bot.smtplib.SMTP_SSL",
            return_value=smtp_cm,
        ) as smtp_cls,
        patch.object(bot, "_get_email_config", return_value=config),
    ):
        bot.send_message__send_email_sync("to@example.com", "body", {})

    assert smtp_cls.call_args.kwargs.get("timeout") == 10
