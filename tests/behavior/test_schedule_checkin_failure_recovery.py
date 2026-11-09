"""Schedule persistence failures and unavailable check-in commands stay actionable."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from communication.command_handlers.schedule_handler import ScheduleManagementHandler
from communication.command_handlers.shared_types import InteractionResponse
from communication.message_processing.flows.checkin_flow import CheckinFlowMixin

pytestmark = [pytest.mark.behavior, pytest.mark.communication]


@pytest.mark.parametrize("edit", [False, True])
@pytest.mark.parametrize("raises", [False, True])
def test_schedule_failure_does_not_claim_success_or_mutate_source(monkeypatch, edit, raises):
    """Rejected writes and exceptions must preserve the original read snapshot."""
    from core import schedule_runtime
    source = {"morning": {
        "start_time": "9:00 AM", "end_time": "11:00 AM",
        "days": ["ALL"], "active": True,
    }}
    before = deepcopy(source)
    monkeypatch.setattr(schedule_runtime, "get_schedule_time_periods", lambda *_: source)
    save = Mock(return_value=False)
    if raises:
        save.side_effect = RuntimeError("PRIVATE PATH AND TOKEN")
    monkeypatch.setattr(schedule_runtime, "set_schedule_periods", save)
    handler = ScheduleManagementHandler()
    entities = {"category": "tasks", "period_name": "morning",
                "start_time": "10am", "end_time": "12pm"}
    if edit:
        entities = {"category": "tasks", "period_name": "morning",
                    "new_start_time": "10am", "new_end_time": "12pm"}
    method = handler._handle_edit_schedule_period if edit else handler._handle_add_schedule_period
    response = method("schedule-failure-user", entities)
    save.assert_called_once()
    assert "couldn't confirm" in response.message
    assert "show my schedule" in response.message
    assert "PRIVATE" not in response.message
    assert "✅" not in response.message
    assert source == before


def test_schedule_active_off_is_saved(monkeypatch):
    """False is a requested change, not an omitted field."""
    from core import schedule_runtime
    source = {"morning": {"start_time": "9:00 AM", "end_time": "11:00 AM",
                          "days": ["ALL"], "active": True}}
    monkeypatch.setattr(schedule_runtime, "get_schedule_time_periods", lambda *_: source)
    save = Mock(return_value=True)
    monkeypatch.setattr(schedule_runtime, "set_schedule_periods", save)
    response = ScheduleManagementHandler()._handle_edit_schedule_period(
        "schedule-off-user", {"category": "tasks", "period_name": "morning", "new_active": False}
    )
    save.assert_called_once()
    assert save.call_args.args[2]["morning"]["active"] is False
    assert source["morning"]["active"] is True
    assert "inactive" in response.message


def test_invalid_schedule_edit_preserves_loaded_period(monkeypatch):
    """A time change followed by a validation failure must not alter cached data."""
    from core import schedule_runtime
    source = {"morning": {"start_time": "9:00 AM", "end_time": "11:00 AM",
                          "days": ["ALL"], "active": True}}
    before = deepcopy(source)
    monkeypatch.setattr(schedule_runtime, "get_schedule_time_periods", lambda *_: source)
    save = Mock()
    monkeypatch.setattr(schedule_runtime, "set_schedule_periods", save)
    response = ScheduleManagementHandler()._handle_edit_schedule_period(
        "invalid-schedule-user", {"category": "tasks", "period_name": "morning",
                                  "new_start_time": "10am", "new_days": ["Notaday"]}
    )
    assert "Invalid days" in response.message
    save.assert_not_called()
    assert source == before


@pytest.mark.parametrize("command", ["profile", "status", "analytics", "schedule", "messages"])
def test_unavailable_checkin_command_keeps_checkin_open(monkeypatch, command):
    from communication.command_handlers import interaction_handlers
    from communication.message_processing.flows import checkin_flow
    monkeypatch.setattr(interaction_handlers, "get_interaction_handler", lambda _: None)
    log_error = Mock()
    monkeypatch.setattr(checkin_flow.logger, "error", log_error)
    flow = CheckinFlowMixin()
    state = {"data": {"mood": 3}}
    flow.user_states = {"checkin-command-user": state}
    reply, completed = flow._handle_command_during_checkin("checkin-command-user", f"/{command}")
    assert not completed
    assert "check-in is still open" in reply
    assert "/help" in reply
    assert f"/{command}" in reply
    assert "handler" not in reply
    assert flow.user_states["checkin-command-user"] is state
    log_error.assert_called_once()
    assert "checkin-command-user" in log_error.call_args.args[0]
    assert command in log_error.call_args.args[0]


@pytest.mark.parametrize("response", [None, SimpleNamespace(), InteractionResponse(""),
                                      InteractionResponse("  "), SimpleNamespace(message=42)])
def test_checkin_messages_never_returns_empty_or_object_representation(monkeypatch, response):
    from communication.command_handlers import interaction_handlers
    handler = SimpleNamespace(handle_show_messages=Mock(return_value=response))
    monkeypatch.setattr(interaction_handlers, "get_interaction_handler", lambda _: handler)
    reply, completed = CheckinFlowMixin()._handle_command_during_checkin("message-user", "/messages")
    assert not completed
    assert "couldn't show your messages" in reply
    assert "check-in is still open" in reply


def test_checkin_messages_success_preserves_reply(monkeypatch):
    from communication.command_handlers import interaction_handlers
    handler = SimpleNamespace(handle_show_messages=lambda *_: InteractionResponse("Your messages"))
    monkeypatch.setattr(interaction_handlers, "get_interaction_handler", lambda _: handler)
    assert CheckinFlowMixin()._handle_command_during_checkin("message-user", "/messages") == (
        "Your messages", False
    )


def test_checkin_messages_missing_method_gives_recovery(monkeypatch):
    from communication.command_handlers import interaction_handlers
    monkeypatch.setattr(interaction_handlers, "get_interaction_handler", lambda _: SimpleNamespace())
    reply, completed = CheckinFlowMixin()._handle_command_during_checkin("message-user", "/messages")
    assert not completed
    assert "couldn't show your messages" in reply
    assert "/help" in reply
