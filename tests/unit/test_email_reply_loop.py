"""Tests for email reply stripping, threading, and check-in/task routing."""

from email import message_from_string
from unittest.mock import MagicMock, patch

import pytest

from communication.communication_channels.base.base_channel import ChannelStatus
from communication.communication_channels.email.bot import EmailBot
from communication.communication_channels.email.inbound_processor import (
    EmailInboundProcessor,
)
from communication.communication_channels.email.quote_strip import strip_quoted_reply
from communication.communication_channels.email.reply_context import (
    find_reply_context,
    inbound_already_handled,
    mark_inbound_handled,
    record_outbound_email,
)
from communication.command_handlers.shared_types import InteractionResponse
from communication.message_processing.email_reply_routing import (
    build_task_reply_command,
    route_checkin_reply,
    route_task_reply,
)
from communication.message_processing.flows.flow_constants import FLOW_CHECKIN


@pytest.mark.unit
@pytest.mark.communication
class TestQuoteStripping:
    def test_strips_gmail_quote_and_keeps_the_new_reply(self):
        body = (
            "I'm doing okay\n\n"
            "On Tue, Sep 23, 2026 at 12:26 AM MHM <bot@example.com> wrote:\n"
            "> How are you feeling?\n"
        )
        assert strip_quoted_reply(body) == "I'm doing okay"

    def test_strips_outlook_original_message(self):
        body = (
            "Done\n\n"
            "-----Original Message-----\n"
            "From: MHM <bot@example.com>\n"
            "Subject: Task reminder\n"
        )
        assert strip_quoted_reply(body) == "Done"

    def test_strips_quoted_lines_and_signature(self):
        body = "Later tonight\n\n-- \nSent from my phone\n> old line\n"
        assert strip_quoted_reply(body) == "Later tonight"

    def test_leaves_a_message_without_a_quote(self):
        assert strip_quoted_reply("Just a normal note") == "Just a normal note"


@pytest.mark.unit
@pytest.mark.communication
class TestReplyContext:
    def test_round_trip_finds_the_outbound_email(self, monkeypatch):
        context_dir = "tests/data/email_reply_loop_user"
        monkeypatch.setattr(
            "communication.communication_channels.email.reply_context.get_user_data_dir",
            lambda user_id: context_dir,
        )
        message_id = "<checkin-1@example.com>"
        try:
            assert record_outbound_email(
                "user-1",
                message_id,
                kind="checkin",
                subject="Check-in",
            )
            found = find_reply_context(
                "user-1",
                message_id,
                "<older@example.com> " + message_id,
            )
            assert found is not None
            assert found["kind"] == "checkin"
            assert inbound_already_handled("user-1", "<in-1@example.com>") is False
            assert mark_inbound_handled("user-1", "<in-1@example.com>") is True
            assert inbound_already_handled("user-1", "<in-1@example.com>") is True
        finally:
            from pathlib import Path

            path = Path(context_dir)
            if path.exists():
                for child in path.glob("*"):
                    child.unlink()
                path.rmdir()


@pytest.mark.unit
@pytest.mark.communication
class TestTaskReplyCommands:
    def test_done_completes_the_answered_task(self):
        command = build_task_reply_command("done", "task-9")
        assert command is not None
        assert command.intent == "complete_task"
        assert command.entities["task_identifier"] == "task-9"

    def test_later_and_until_map_to_snooze(self):
        later = build_task_reply_command("later", "task-9")
        assert later is not None
        assert later.intent == "snooze_task_reminder"
        assert "snooze_option" not in later.entities

        timed = build_task_reply_command("until Friday 3pm", "task-9")
        assert timed is not None
        assert timed.entities["snooze_option"] == "custom"
        assert timed.entities["snooze_when"] == "Friday 3pm"

    def test_skip_and_simplify_keep_the_task_id(self):
        skipped = build_task_reply_command("skip", "task-9")
        assert skipped is not None
        assert skipped.intent == "skip_task_occurrence"
        simplified = build_task_reply_command("simplify to wipe the kitchen counter", "task-9")
        assert simplified is not None
        assert simplified.intent == "simplify_task"
        assert simplified.entities["simplified_title"] == "wipe the kitchen counter"

    def test_unrelated_reply_is_not_a_task_command(self):
        assert build_task_reply_command("thanks for the reminder", "task-9") is None


@pytest.mark.unit
@pytest.mark.communication
class TestEmailReplyRouting:
    def test_checkin_reply_uses_the_open_checkin(self):
        with patch(
            "communication.message_processing.email_reply_routing.conversation_manager.answer_active_checkin",
            return_value=("Next question", False),
        ) as answer:
            response = route_checkin_reply("user-1", "7")
        answer.assert_called_once_with("user-1", "7")
        assert response is not None
        assert response.message == "Next question"

    def test_checkin_reply_falls_through_when_checkin_is_closed(self):
        with patch(
            "communication.message_processing.email_reply_routing.conversation_manager.answer_active_checkin",
            return_value=None,
        ):
            assert route_checkin_reply("user-1", "hello") is None

    def test_task_reply_does_not_use_an_open_checkin(self):
        with patch(
            "communication.command_handlers.task_handler.TaskManagementHandler.handle",
            return_value=InteractionResponse("Marked done.", True),
        ) as handle:
            response = route_task_reply("user-1", "done", "task-9")
        handle.assert_called_once()
        command = handle.call_args.args[1]
        assert command.intent == "complete_task"
        assert command.entities["task_identifier"] == "task-9"
        assert response.message == "Marked done."


@pytest.mark.unit
@pytest.mark.communication
class TestInboundReplyLoop:
    def _processor(self):
        channel = MagicMock()
        channel.is_ready.return_value = True
        channel.last_outbound_message_id = "<out@example.com>"
        return EmailInboundProcessor(
            get_email_channel=MagicMock(return_value=channel),
            run_async_sync=MagicMock(return_value=True),
            is_runtime_running=MagicMock(return_value=True),
        ), channel

    def test_quoted_checkin_reply_is_stripped_and_threaded(self):
        processor, channel = self._processor()
        email_msg = {
            "from": "member@example.com",
            "subject": "Re: Check-in",
            "body": "I'm okay\n\nOn Tue, Someone wrote:\n> How are you?",
            "message_id": "<user-msg@example.com>",
            "in_reply_to": "<checkin@example.com>",
            "references": "<checkin@example.com>",
            "imap_email_id": "4",
        }
        with (
            patch("core.get_user_id_by_identifier", return_value="user-1"),
            patch(
                "communication.communication_channels.email.reply_context.find_reply_context",
                return_value={"kind": "checkin", "task_id": "", "message_id": "<checkin@example.com>", "subject": "Check-in"},
            ),
            patch(
                "communication.communication_channels.email.reply_context.inbound_already_handled",
                return_value=False,
            ),
            patch(
                "communication.message_processing.email_reply_routing.route_checkin_reply",
                return_value=InteractionResponse("Thanks, next question.", False),
            ) as route,
            patch(
                "communication.communication_channels.email.reply_context.mark_inbound_handled",
                return_value=True,
            ) as marked,
        ):
            assert processor.process_incoming_email(email_msg) is True

        route.assert_called_once_with("user-1", "I'm okay")
        send_args = channel.send_message.call_args
        assert send_args.args[0] == "member@example.com"
        assert send_args.args[1] == "Thanks, next question."
        assert send_args.kwargs["subject"] == "Re: Check-in"
        assert send_args.kwargs["in_reply_to"] == "<user-msg@example.com>"
        assert send_args.kwargs["reply_kind"] == "checkin"
        marked.assert_called_once()

    def test_task_reply_maps_to_that_task(self):
        processor, _channel = self._processor()
        email_msg = {
            "from": "member@example.com",
            "subject": "Re: Task reminder: Dishes",
            "body": "done",
            "message_id": "<user-task@example.com>",
            "in_reply_to": "<task@example.com>",
            "references": "<task@example.com>",
            "imap_email_id": "5",
        }
        with (
            patch("core.get_user_id_by_identifier", return_value="user-1"),
            patch(
                "communication.communication_channels.email.reply_context.find_reply_context",
                return_value={
                    "kind": "task_reminder",
                    "task_id": "task-9",
                    "message_id": "<task@example.com>",
                    "subject": "Task reminder: Dishes",
                },
            ),
            patch(
                "communication.communication_channels.email.reply_context.inbound_already_handled",
                return_value=False,
            ),
            patch(
                "communication.message_processing.email_reply_routing.route_task_reply",
                return_value=InteractionResponse("Marked done.", True),
            ) as route,
            patch(
                "communication.communication_channels.email.reply_context.mark_inbound_handled",
                return_value=True,
            ),
        ):
            assert processor.process_incoming_email(email_msg) is True
        route.assert_called_once_with("user-1", "done", "task-9")

    def test_failed_send_leaves_the_message_unhandled(self):
        processor, channel = self._processor()
        channel.last_outbound_message_id = None
        email_msg = {
            "from": "member@example.com",
            "subject": "Hi",
            "body": "hello",
            "message_id": "<user-hi@example.com>",
            "imap_email_id": "6",
        }
        with (
            patch("core.get_user_id_by_identifier", return_value="user-1"),
            patch(
                "communication.communication_channels.email.reply_context.inbound_already_handled",
                return_value=False,
            ),
            patch(
                "communication.communication_channels.email.reply_context.find_reply_context",
                return_value=None,
            ),
            patch(
                "communication.message_processing.interaction_manager.handle_user_message",
                return_value=InteractionResponse("Hello back.", True),
            ),
            patch(
                "communication.communication_channels.email.reply_context.mark_inbound_handled",
            ) as marked,
        ):
            assert processor.process_incoming_email(email_msg) is False
        marked.assert_not_called()

    def test_quote_only_body_asks_for_the_new_text(self):
        processor, channel = self._processor()
        email_msg = {
            "from": "member@example.com",
            "subject": "Re: Check-in",
            "body": "On Tue, Someone wrote:\n> How are you?",
            "message_id": "<quote-only@example.com>",
            "imap_email_id": "7",
        }
        with (
            patch("core.get_user_id_by_identifier", return_value="user-1"),
            patch(
                "communication.communication_channels.email.reply_context.inbound_already_handled",
                return_value=False,
            ),
            patch(
                "communication.communication_channels.email.reply_context.mark_inbound_handled",
                return_value=True,
            ),
            patch(
                "communication.message_processing.interaction_manager.handle_user_message",
            ) as chat,
        ):
            assert processor.process_incoming_email(email_msg) is True
        chat.assert_not_called()
        assert "quoted message" in channel.send_message.call_args.args[1]


@pytest.mark.unit
@pytest.mark.communication
class TestOutboundThreading:
    def test_send_sets_message_id_and_reply_headers(self, monkeypatch):
        bot = EmailBot()
        bot._set_status(ChannelStatus.READY)
        server = MagicMock()
        monkeypatch.setattr(bot, "_get_email_config", lambda: ("smtp.test.com", "imap.test.com", "bot@example.com", "secret"))
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.smtplib.SMTP_SSL",
            MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=server), __exit__=MagicMock(return_value=False))),
        )
        monkeypatch.setattr(
            "communication.communication_channels.email.bot.record_outbound_email",
            lambda *args, **kwargs: True,
        )

        bot.send_message__send_email_sync(
            "person@example.com",
            "Next question",
            {
                "subject": "Check-in",
                "user_id": "user-1",
                "reply_kind": "checkin",
                "in_reply_to": "<user-msg@example.com>",
                "references": "<checkin@example.com>",
            },
        )

        _sender, recipient, payload = server.sendmail.call_args.args
        assert recipient == "person@example.com"
        parsed = message_from_string(payload)
        assert parsed["Subject"].startswith("Re:")
        assert parsed["In-Reply-To"] == "<user-msg@example.com>"
        assert "<user-msg@example.com>" in parsed["References"]
        assert parsed["Message-ID"]
        assert bot.last_outbound_message_id == parsed["Message-ID"]


@pytest.mark.unit
@pytest.mark.communication
def test_answer_active_checkin_ignores_other_flows():
    from communication.message_processing.conversation_flow_manager import (
        conversation_manager,
    )

    conversation_manager.user_states["email-checkin-user"] = {
        "flow": FLOW_CHECKIN,
        "state": 0,
        "data": {},
    }
    with patch.object(
        conversation_manager,
        "_handle_checkin",
        return_value=("Got it", False),
    ) as handle:
        assert conversation_manager.answer_active_checkin("email-checkin-user", "4") == (
            "Got it",
            False,
        )
    handle.assert_called_once()
    conversation_manager.user_states.pop("email-checkin-user", None)
    assert conversation_manager.answer_active_checkin("email-checkin-user", "4") is None
