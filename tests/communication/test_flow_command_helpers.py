"""Unit tests for shared flow command helpers."""

from datetime import timedelta

import pytest

from communication.message_processing.flows.flow_command_helpers import (
    FLOW_FOCUS_JOURNAL,
    FLOW_FOCUS_LIST,
    FLOW_FOCUS_NOTE,
    FLOW_FOCUS_TASK,
    FLOW_STEP_DATE_TIME,
    FLOW_STEP_FREE_TEXT,
    FLOW_STEP_PRIORITY,
    is_cancel_message,
    is_flow_expired,
    is_skip_all_message,
    is_step_back_message,
    is_unrelated_flow_message,
    message_matches_keyword,
    try_flow_control_command,
    FlowControlHandlers,
)
from core.time_utilities import TIMESTAMP_FULL, format_timestamp, now_datetime_full

pytestmark = [pytest.mark.unit, pytest.mark.communication]


class TestMessageMatchesKeyword:
    def test_exact_match(self):
        assert message_matches_keyword("skip all", ["skip all"])

    def test_prefix_match(self):
        assert message_matches_keyword("skip all please", ["skip all"])

    def test_no_match(self):
        assert not message_matches_keyword("skip", ["skip all"])


class TestCancelSynonyms:
    @pytest.mark.parametrize(
        "message",
        ["cancel", "stop", "quit", "exit", "abort", "!stop", "/quit"],
    )
    def test_cancel_synonyms(self, message):
        assert is_cancel_message(message)


class TestStepBackExcludesUndoCreation:
    def test_undo_task_creation_is_not_step_back(self):
        assert not is_step_back_message(
            "undo task creation",
            undo_creation_phrases=["undo task creation", "undo task"],
        )

    def test_back_is_step_back(self):
        assert is_step_back_message("back")


class TestUnrelatedFlowMessage:
    def test_note_flow_treats_task_command_as_unrelated(self):
        assert is_unrelated_flow_message("!task buy milk", current_focus=FLOW_FOCUS_NOTE)

    def test_task_flow_treats_note_command_as_unrelated(self):
        assert is_unrelated_flow_message("/n my note", current_focus=FLOW_FOCUS_TASK)

    def test_list_flow_ignores_list_prefix(self):
        assert not is_unrelated_flow_message(
            "!list groceries", current_focus=FLOW_FOCUS_LIST
        )

    def test_greeting_is_unrelated(self):
        assert is_unrelated_flow_message("hello", current_focus=FLOW_FOCUS_TASK)

    def test_free_text_step_allows_create_in_body(self):
        """Journal/note body may contain 'create' without switching context."""
        message = "today i want to create a new habit of journaling"
        assert not is_unrelated_flow_message(
            message,
            current_focus=FLOW_FOCUS_JOURNAL,
            step=FLOW_STEP_FREE_TEXT,
        )

    def test_structured_step_flags_create_task(self):
        assert is_unrelated_flow_message(
            "create task buy milk",
            current_focus=FLOW_FOCUS_TASK,
            step=FLOW_STEP_DATE_TIME,
        )

    def test_priority_step_does_not_flag_low_as_unrelated(self):
        assert not is_unrelated_flow_message(
            "low",
            current_focus=FLOW_FOCUS_TASK,
            step=FLOW_STEP_PRIORITY,
        )


class TestFlowExpired:
    def test_recent_flow_not_expired(self):
        state = {"started_at": format_timestamp(now_datetime_full(), TIMESTAMP_FULL)}
        assert not is_flow_expired(state)

    def test_old_flow_expired(self):
        old = format_timestamp(
            now_datetime_full() - timedelta(minutes=11), TIMESTAMP_FULL
        )
        assert is_flow_expired({"started_at": old})


class TestTryFlowControlCommand:
    def test_skip_all_invokes_handler(self):
        called = []

        def on_skip_all():
            called.append(True)
            return ("done", True)

        result = try_flow_control_command(
            "skip all",
            {},
            FlowControlHandlers(on_skip_all=on_skip_all),
        )
        assert result == ("done", True)
        assert called

    def test_stop_triggers_undo_creation(self):
        result = try_flow_control_command(
            "stop",
            {},
            FlowControlHandlers(on_undo_creation=lambda: ("cancelled", True)),
        )
        assert result == ("cancelled", True)

    def test_unrelated_expired_uses_timeout_handler(self):
        old = format_timestamp(
            now_datetime_full() - timedelta(minutes=11), TIMESTAMP_FULL
        )
        result = try_flow_control_command(
            "hello",
            {"started_at": old},
            FlowControlHandlers(
                is_unrelated=lambda _: True,
                on_timeout_unrelated=lambda: ("finalized", True),
                on_unrelated_clear=lambda: ("cleared", True),
            ),
        )
        assert result == ("finalized", True)

    def test_unrelated_not_expired_clears(self):
        state = {"started_at": format_timestamp(now_datetime_full(), TIMESTAMP_FULL)}
        result = try_flow_control_command(
            "hello",
            state,
            FlowControlHandlers(
                is_unrelated=lambda _: True,
                on_timeout_unrelated=lambda: ("finalized", True),
                on_unrelated_clear=lambda: ("cleared", True),
            ),
        )
        assert result == ("cleared", True)

    def test_skip_all_keyword(self):
        assert is_skip_all_message("!skip all")
