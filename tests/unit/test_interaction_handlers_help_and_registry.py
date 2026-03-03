"""Unit tests for help/registry logic in interaction handlers."""

from __future__ import annotations

import pytest

from communication.command_handlers.interaction_handlers import (
    HelpHandler,
    INTERACTION_HANDLERS,
    get_all_handlers,
    get_interaction_handler,
)
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand


class _DummyHandler:
    """Minimal handler stub used to isolate registry behavior."""

    def __init__(self, accepted_intents: set[str]):
        self._accepted_intents = accepted_intents

    def can_handle(self, intent: str) -> bool:
        return intent in self._accepted_intents


@pytest.mark.unit
@pytest.mark.communication
class TestHelpHandler:
    def setup_method(self):
        self.handler = HelpHandler()

    def test_can_handle_known_help_intents(self):
        for intent in ("help", "commands", "examples", "status", "messages"):
            assert self.handler.can_handle(intent) is True

    def test_can_handle_unknown_intent_false(self):
        assert self.handler.can_handle("unknown_intent") is False

    def test_handle_general_help_dispatch(self):
        response = self.handler.handle(
            "user-1", ParsedCommand(intent="help", entities={}, confidence=1.0, original_message="help")
        )
        assert isinstance(response, InteractionResponse)
        assert "MHM Bot Commands" in response.message
        assert response.completed is True

    def test_handle_help_topic_tasks(self):
        response = self.handler._handle_general_help("user-1", {"topic": "tasks"})
        assert "Task Management Help" in response.message
        assert response.completed is True

    def test_handle_help_topic_checkin(self):
        response = self.handler._handle_general_help("user-1", {"topic": "checkin"})
        assert "Check-in Help" in response.message
        assert response.completed is True

    def test_handle_help_topic_profile(self):
        response = self.handler._handle_general_help("user-1", {"topic": "profile"})
        assert "Profile Management Help" in response.message
        assert response.completed is True

    def test_handle_commands_intent(self):
        response = self.handler.handle(
            "user-1",
            ParsedCommand(
                intent="commands",
                entities={},
                confidence=1.0,
                original_message="commands",
            ),
        )
        assert "Complete Command List" in response.message
        assert response.completed is True

    def test_handle_examples_schedule_topic(self):
        response = self.handler.handle(
            "user-1",
            ParsedCommand(
                intent="examples",
                entities={"category": "schedule"},
                confidence=1.0,
                original_message="examples schedule",
            ),
        )
        assert "Schedule Examples" in response.message
        assert response.completed is True

    def test_handle_examples_analytics_topic(self):
        response = self.handler._handle_examples("user-1", {"category": "analytics"})
        assert "Analytics Examples" in response.message
        assert response.completed is True

    def test_handle_unknown_intent_fallback_response(self):
        response = self.handler.handle(
            "user-1",
            ParsedCommand(
                intent="not-real",
                entities={},
                confidence=1.0,
                original_message="not-real",
            ),
        )
        assert "Try 'help'" in response.message
        assert response.completed is True

    def test_handle_status_with_registered_account(self, monkeypatch):
        monkeypatch.setattr(
            "communication.command_handlers.interaction_handlers.get_user_data",
            lambda user_id, data_type: {
                "account": {
                    "internal_username": "julie",
                    "timezone": "America/Regina",
                    "features": {"tasks": "enabled", "checkins": "disabled"},
                }
            },
        )
        monkeypatch.setattr(
            "tasks.load_active_tasks",
            lambda user_id: [{"title": "A"}, {"title": "B"}],
        )
        monkeypatch.setattr(
            "core.response_tracking.is_user_checkins_enabled",
            lambda user_id: True,
        )

        response = self.handler._handle_status("user-1")
        assert "System Status for julie" in response.message
        assert "Active Tasks: 2" in response.message
        assert response.completed is True

    def test_handle_status_without_account_prompts_registration(self, monkeypatch):
        monkeypatch.setattr(
            "communication.command_handlers.interaction_handlers.get_user_data",
            lambda user_id, data_type: {},
        )
        response = self.handler._handle_status("user-1")
        assert "Please register first" in response.message
        assert response.completed is True

    def test_handle_messages_with_recent_activity(self, monkeypatch):
        monkeypatch.setattr(
            "communication.command_handlers.interaction_handlers.get_user_data",
            lambda user_id, data_type: {"account": {"internal_username": "julie"}},
        )
        monkeypatch.setattr(
            "core.response_tracking.get_recent_checkins",
            lambda user_id, limit=5: [{"date": "2026-02-27"}],
        )

        response = self.handler._handle_messages("user-1")
        assert "Messages for julie" in response.message
        assert "Recent check-ins" in response.message
        assert response.completed is True

    def test_handle_messages_without_account_prompts_registration(self, monkeypatch):
        monkeypatch.setattr(
            "communication.command_handlers.interaction_handlers.get_user_data",
            lambda user_id, data_type: {},
        )
        response = self.handler._handle_messages("user-1")
        assert "Please register first" in response.message
        assert response.completed is True

    def test_handle_messages_with_no_recent_activity(self, monkeypatch):
        monkeypatch.setattr(
            "communication.command_handlers.interaction_handlers.get_user_data",
            lambda user_id, data_type: {"account": {"internal_username": "julie"}},
        )
        monkeypatch.setattr(
            "core.response_tracking.get_recent_checkins",
            lambda user_id, limit=5: [],
        )
        response = self.handler._handle_messages("user-1")
        assert "No recent check-ins found" in response.message
        assert response.completed is True

    def test_get_help_and_examples(self):
        assert self.handler.get_help() == "Get help and see available commands"
        assert "help" in self.handler.get_examples()


@pytest.mark.unit
@pytest.mark.communication
class TestInteractionHandlerRegistry:
    def test_get_interaction_handler_lazy_loads_when_entries_are_none(self):
        original = dict(INTERACTION_HANDLERS)
        try:
            INTERACTION_HANDLERS.clear()
            INTERACTION_HANDLERS.update(
                {
                    "TaskManagementHandler": None,
                    "CheckinHandler": None,
                    "ProfileHandler": None,
                    "HelpHandler": HelpHandler(),
                    "ScheduleManagementHandler": None,
                    "AnalyticsHandler": None,
                    "NotebookHandler": None,
                    "AccountManagementHandler": None,
                }
            )
            handler = get_interaction_handler("help")
            assert handler is not None
            assert handler.can_handle("help") is True
        finally:
            INTERACTION_HANDLERS.clear()
            INTERACTION_HANDLERS.update(original)

    def test_get_interaction_handler_returns_matching_handler(self):
        original = dict(INTERACTION_HANDLERS)
        try:
            INTERACTION_HANDLERS.clear()
            INTERACTION_HANDLERS.update(
                {
                    "TaskManagementHandler": _DummyHandler({"task_intent"}),
                    "CheckinHandler": _DummyHandler({"checkin_intent"}),
                    "ProfileHandler": _DummyHandler({"profile_intent"}),
                    "HelpHandler": _DummyHandler({"help"}),
                    "ScheduleManagementHandler": _DummyHandler({"schedule_intent"}),
                    "AnalyticsHandler": _DummyHandler({"analytics_intent"}),
                    "NotebookHandler": _DummyHandler({"notebook_intent"}),
                    "AccountManagementHandler": _DummyHandler({"account_intent"}),
                }
            )

            handler = get_interaction_handler("schedule_intent")
            assert isinstance(handler, _DummyHandler)
            assert handler.can_handle("schedule_intent") is True
        finally:
            INTERACTION_HANDLERS.clear()
            INTERACTION_HANDLERS.update(original)

    def test_get_interaction_handler_returns_none_for_unknown(self):
        original = dict(INTERACTION_HANDLERS)
        try:
            INTERACTION_HANDLERS.clear()
            INTERACTION_HANDLERS.update(
                {
                    "TaskManagementHandler": _DummyHandler({"task_intent"}),
                    "CheckinHandler": _DummyHandler({"checkin_intent"}),
                    "ProfileHandler": _DummyHandler({"profile_intent"}),
                    "HelpHandler": _DummyHandler({"help"}),
                    "ScheduleManagementHandler": _DummyHandler({"schedule_intent"}),
                    "AnalyticsHandler": _DummyHandler({"analytics_intent"}),
                    "NotebookHandler": _DummyHandler({"notebook_intent"}),
                    "AccountManagementHandler": _DummyHandler({"account_intent"}),
                }
            )

            assert get_interaction_handler("no-match") is None
        finally:
            INTERACTION_HANDLERS.clear()
            INTERACTION_HANDLERS.update(original)

    def test_get_all_handlers_returns_only_non_none_values(self):
        original = dict(INTERACTION_HANDLERS)
        try:
            INTERACTION_HANDLERS.clear()
            INTERACTION_HANDLERS.update(
                {
                    "TaskManagementHandler": _DummyHandler({"task_intent"}),
                    "CheckinHandler": None,
                    "ProfileHandler": _DummyHandler({"profile_intent"}),
                    "HelpHandler": _DummyHandler({"help"}),
                    "ScheduleManagementHandler": None,
                    "AnalyticsHandler": _DummyHandler({"analytics_intent"}),
                    "NotebookHandler": _DummyHandler({"notebook_intent"}),
                    "AccountManagementHandler": None,
                }
            )
            result = get_all_handlers()
            assert all(value is not None for value in result.values())
            assert "HelpHandler" in result
        finally:
            INTERACTION_HANDLERS.clear()
            INTERACTION_HANDLERS.update(original)

    def test_get_all_handlers_lazy_loads_when_entries_are_none(self):
        original = dict(INTERACTION_HANDLERS)
        try:
            INTERACTION_HANDLERS.clear()
            INTERACTION_HANDLERS.update(
                {
                    "TaskManagementHandler": None,
                    "CheckinHandler": None,
                    "ProfileHandler": None,
                    "HelpHandler": HelpHandler(),
                    "ScheduleManagementHandler": None,
                    "AnalyticsHandler": None,
                    "NotebookHandler": None,
                    "AccountManagementHandler": None,
                }
            )
            result = get_all_handlers()
            assert "HelpHandler" in result
            assert all(value is not None for value in result.values())
        finally:
            INTERACTION_HANDLERS.clear()
            INTERACTION_HANDLERS.update(original)
