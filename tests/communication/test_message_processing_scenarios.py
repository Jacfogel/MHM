"""
Scenario-style coverage for communication message_processing and command_registry modules.

Targets user_suggestions, response_enhancer, parsing_shortcuts, flow_message_dispatcher,
and communication command_registry paths below the 80% domain goal.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from communication.communication_channels.base.command_registry import (
    CommandDefinition,
    DiscordCommandRegistry,
    EmailCommandRegistry,
    get_command_registry,
)
from communication.message_processing.command_parser import ParsingResult
from communication.message_processing.flow_message_dispatcher import (
    FlowDispatchResult,
    dispatch_flow_message,
)
from communication.message_processing.flows.flow_constants import (
    FLOW_CHECKIN,
    FLOW_TASK_DUE_DATE,
    FLOW_TASK_PRIORITY,
    FLOW_TASK_REMINDER,
    TASK_DUE_DATE_SUGGESTIONS,
    TASK_PRIORITY_SUGGESTIONS,
)
from communication.message_processing.parsing_shortcuts import (
    coerce_unknown_update_task,
    reinforce_update_task_parsing,
    try_parsing_shortcuts,
)
from communication.message_processing.response_enhancer import enhance_response_with_ai
from communication.message_processing.user_suggestions import (
    augment_suggestions,
    get_user_suggestions,
)
from checkins.checkin_data_manager import store_checkin_response
from tasks import create_task
from tests.test_helpers.test_utilities import TestUserFactory


def _unique_user(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.mark.unit
@pytest.mark.communication
class TestAugmentSuggestions:
    """Branch coverage for augment_suggestions."""

    def test_completed_response_unchanged(self):
        parsed = ParsedCommand("complete_task", {}, 1.0, "done")
        response = InteractionResponse("All set.", completed=True)
        assert augment_suggestions(parsed, response) is response
        assert response.suggestions is None

    def test_multiple_matching_tasks_suggestions(self):
        parsed = ParsedCommand("complete_task", {}, 0.9, "complete task")
        response = InteractionResponse("Multiple matching tasks found.", completed=False)
        out = augment_suggestions(parsed, response)
        assert out.suggestions == ["list tasks", "cancel"]

    def test_confirm_delete_suggestions(self):
        parsed = ParsedCommand("delete_task", {}, 0.9, "delete task")
        response = InteractionResponse("Please confirm delete for task 1.", completed=False)
        out = augment_suggestions(parsed, response)
        assert out.suggestions == ["confirm delete", "cancel"]

    def test_complete_task_prompt_suggestions(self):
        parsed = ParsedCommand("complete_task", {}, 0.9, "complete")
        response = InteractionResponse(
            "Did you want to complete this task?", completed=False
        )
        out = augment_suggestions(parsed, response)
        assert out.suggestions == ["complete task 1", "cancel"]

    def test_edit_schedule_period_update_suggestions(self):
        parsed = ParsedCommand("edit_schedule_period", {}, 0.9, "edit morning period")
        response = InteractionResponse(
            "What would you like to update for morning?", completed=False
        )
        out = augment_suggestions(parsed, response)
        assert out.suggestions == ["from 9am to 11am", "active off"]

    def test_update_task_which_task_suggestions(self):
        parsed = ParsedCommand("update_task", {}, 0.9, "update task 1")
        response = InteractionResponse("Which task would you like to update?", completed=False)
        out = augment_suggestions(parsed, response)
        assert out.suggestions == ["list tasks", "cancel"]

    def test_generic_update_prompt_suggestions(self):
        parsed = ParsedCommand("update_task", {}, 0.9, "update task 1")
        response = InteractionResponse(
            "What would you like to update for task 1?", completed=False
        )
        out = augment_suggestions(parsed, response)
        assert out.suggestions == ["due date tomorrow", "priority high"]


@pytest.mark.integration
@pytest.mark.communication
class TestGetUserSuggestionsScenarios:
    """Real task/check-in/category paths in get_user_suggestions."""

    @pytest.fixture
    def fixed_now(self):
        return datetime(2026, 6, 18, 12, 0, 0)

    def test_no_tasks_suggests_add_task(self, test_data_dir, fixed_now):
        user_id = _unique_user("suggest_no_tasks")
        TestUserFactory.create_basic_user(
            user_id, enable_checkins=False, enable_tasks=True, test_data_dir=test_data_dir
        )
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ):
            suggestions = get_user_suggestions(user_id)
        assert "Add a new task for today" in suggestions

    def test_overdue_task_suggestion(self, test_data_dir, fixed_now):
        user_id = _unique_user("suggest_overdue")
        TestUserFactory.create_basic_user(
            user_id, enable_checkins=False, enable_tasks=True, test_data_dir=test_data_dir
        )
        create_task(user_id, title="Late report", due_date="2026-06-17")
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ):
            suggestions = get_user_suggestions(user_id)
        assert any("Catch up on" in s and "Late report" in s for s in suggestions)

    def test_due_today_suggestion(self, test_data_dir, fixed_now):
        user_id = _unique_user("suggest_today")
        TestUserFactory.create_basic_user(
            user_id, enable_checkins=False, enable_tasks=True, test_data_dir=test_data_dir
        )
        create_task(user_id, title="Today chore", due_date="2026-06-18")
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ):
            suggestions = get_user_suggestions(user_id)
        assert any('Finish "Today chore" due today' in s for s in suggestions)

    def test_future_due_suggestion(self, test_data_dir, fixed_now):
        user_id = _unique_user("suggest_future")
        TestUserFactory.create_basic_user(
            user_id, enable_checkins=False, enable_tasks=True, test_data_dir=test_data_dir
        )
        create_task(user_id, title="Future plan", due_date="2026-06-25")
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ):
            suggestions = get_user_suggestions(user_id)
        assert any("Plan for" in s and "Future plan" in s for s in suggestions)

    def test_task_without_due_date(self, test_data_dir, fixed_now):
        user_id = _unique_user("suggest_no_due")
        TestUserFactory.create_basic_user(
            user_id, enable_checkins=False, enable_tasks=True, test_data_dir=test_data_dir
        )
        create_task(user_id, title="Open item")
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ):
            suggestions = get_user_suggestions(user_id)
        assert any('Work on "Open item" from your task list' in s for s in suggestions)

    def test_multiple_tasks_includes_list_prompt(self, test_data_dir, fixed_now):
        user_id = _unique_user("suggest_multi")
        TestUserFactory.create_basic_user(
            user_id, enable_checkins=False, enable_tasks=True, test_data_dir=test_data_dir
        )
        create_task(user_id, title="First")
        create_task(user_id, title="Second")
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ):
            suggestions = get_user_suggestions(user_id)
        assert "Show my tasks" in suggestions

    def test_task_load_failure_fallback(self, fixed_now):
        user_id = _unique_user("suggest_task_err")
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ), patch(
            "tasks.load_active_tasks",
            side_effect=RuntimeError("boom"),
        ):
            suggestions = get_user_suggestions(user_id)
        assert "Show my tasks" in suggestions

    def test_checkin_disabled_still_has_profile_help(self, test_data_dir, fixed_now):
        user_id = _unique_user("suggest_no_checkin")
        TestUserFactory.create_basic_user(
            user_id, enable_checkins=False, enable_tasks=False, test_data_dir=test_data_dir
        )
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ):
            suggestions = get_user_suggestions(user_id)
        assert "Show my profile" in suggestions
        assert "Help with tasks" in suggestions
        assert len(suggestions) <= 5

    def test_categories_add_schedule_suggestions(self, test_data_dir, fixed_now):
        user_id = _unique_user("suggest_cats")
        TestUserFactory.create_basic_user(
            user_id, enable_checkins=False, enable_tasks=False, test_data_dir=test_data_dir
        )
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ), patch(
            "core.get_user_categories",
            return_value=["motivational", "tasks"],
        ):
            suggestions = get_user_suggestions(user_id)
        assert any("Review your motivational schedule" in s for s in suggestions)
        assert "Schedule status" in suggestions

    def test_task_with_due_time_uses_datetime_parse(self, test_data_dir, fixed_now):
        user_id = _unique_user("suggest_due_time")
        TestUserFactory.create_basic_user(
            user_id, enable_checkins=False, enable_tasks=True, test_data_dir=test_data_dir
        )
        create_task(
            user_id,
            title="Timed item",
            due_date="2026-06-18",
            due_time="15:00",
        )
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ):
            suggestions = get_user_suggestions(user_id)
        assert any('Finish "Timed item" due today' in s for s in suggestions)

    def test_stale_checkin_suggests_log_today(self, test_data_dir, fixed_now):
        user_id = _unique_user("suggest_stale_checkin")
        TestUserFactory.create_basic_user(
            user_id, enable_checkins=True, enable_tasks=False, test_data_dir=test_data_dir
        )
        store_checkin_response(
            user_id, {"mood": 4, "submitted_at": "2026-06-15 09:00:00"}
        )
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ), patch(
            "checkins.checkin_data_manager.is_user_checkins_enabled",
            return_value=True,
        ):
            suggestions = get_user_suggestions(user_id)
        assert "Log a quick check-in for today" in suggestions

    def test_recent_checkin_with_mood_suggests_trend(self, test_data_dir, fixed_now):
        user_id = _unique_user("suggest_mood")
        TestUserFactory.create_basic_user(
            user_id, enable_checkins=True, enable_tasks=False, test_data_dir=test_data_dir
        )
        store_checkin_response(
            user_id, {"mood": "Calm", "submitted_at": "2026-06-18 08:00:00"}
        )
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ), patch(
            "checkins.checkin_data_manager.is_user_checkins_enabled",
            return_value=True,
        ):
            suggestions = get_user_suggestions(user_id)
        assert "Review your recent check-ins" in suggestions
        assert any("mood trend" in s and "calm" in s for s in suggestions)

    def test_checkins_enabled_no_history_suggests_first(self, test_data_dir, fixed_now):
        user_id = _unique_user("suggest_first_checkin")
        TestUserFactory.create_basic_user(
            user_id, enable_checkins=True, enable_tasks=False, test_data_dir=test_data_dir
        )
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ), patch(
            "checkins.checkin_data_manager.is_user_checkins_enabled",
            return_value=True,
        ), patch(
            "checkins.checkin_data_manager.get_recent_checkins",
            return_value=[],
        ):
            suggestions = get_user_suggestions(user_id)
        assert "Start your first check-in" in suggestions

    def test_many_checkins_suggests_weekly_mood_trends(self, test_data_dir, fixed_now):
        user_id = _unique_user("suggest_week_trends")
        TestUserFactory.create_basic_user(
            user_id, enable_checkins=True, enable_tasks=False, test_data_dir=test_data_dir
        )
        for day in (15, 16, 17):
            store_checkin_response(
                user_id,
                {"mood": 5, "submitted_at": f"2026-06-{day} 09:00:00"},
            )
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ):
            suggestions = get_user_suggestions(user_id)
        assert "View mood trends from this week" in suggestions

    def test_checkin_block_failure_fallback(self, fixed_now):
        user_id = _unique_user("suggest_checkin_err")
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ), patch(
            "checkins.checkin_data_manager.is_user_checkins_enabled",
            side_effect=RuntimeError("fail"),
        ):
            suggestions = get_user_suggestions(user_id)
        assert "Start a check-in" in suggestions

    def test_categories_failure_fallback(self, fixed_now):
        user_id = _unique_user("suggest_cat_err")
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ), patch(
            "tasks.load_active_tasks",
            return_value=[],
        ), patch(
            "checkins.checkin_data_manager.is_user_checkins_enabled",
            return_value=False,
        ), patch(
            "core.get_user_categories",
            side_effect=RuntimeError("fail"),
        ):
            suggestions = get_user_suggestions(user_id)
        assert "Show my schedule" in suggestions

    def test_analytics_block_failure_fallback(self, fixed_now):
        user_id = _unique_user("suggest_analytics_err")
        with patch(
            "communication.message_processing.user_suggestions.now_datetime_full",
            return_value=fixed_now,
        ), patch(
            "tasks.load_active_tasks",
            return_value=[],
        ), patch(
            "checkins.checkin_data_manager.is_user_checkins_enabled",
            return_value=False,
        ), patch(
            "core.get_user_categories",
            return_value=[],
        ), patch(
            "checkins.checkin_data_manager.get_recent_checkins",
            side_effect=RuntimeError("fail"),
        ):
            suggestions = get_user_suggestions(user_id)
        assert "Show my analytics" in suggestions


@pytest.mark.unit
@pytest.mark.communication
class TestResponseEnhancer:
    """AI enhancement guardrails and truncation."""

    def test_disabled_returns_original(self):
        response = InteractionResponse("Hello there.")
        parsed = ParsedCommand("greeting", {}, 0.9, "hi")
        mock_bot = MagicMock()
        out = enhance_response_with_ai(
            "user-1",
            response,
            parsed,
            ai_chatbot=mock_bot,
            enable_ai_enhancement=False,
        )
        assert out.message == "Hello there."
        mock_bot.generate_response.assert_not_called()

    def test_excluded_intent_skips_enhancement(self):
        response = InteractionResponse("Your tasks:")
        parsed = ParsedCommand("list_tasks", {}, 0.9, "list tasks")
        mock_bot = MagicMock()
        out = enhance_response_with_ai(
            "user-1",
            response,
            parsed,
            ai_chatbot=mock_bot,
            enable_ai_enhancement=True,
        )
        assert out.message == "Your tasks:"
        mock_bot.generate_response.assert_not_called()

    def test_profile_keyword_in_intent_skips(self):
        response = InteractionResponse("Profile info")
        parsed = ParsedCommand("show_user_profile", {}, 0.9, "profile")
        mock_bot = MagicMock()
        out = enhance_response_with_ai(
            "user-1",
            response,
            parsed,
            ai_chatbot=mock_bot,
            enable_ai_enhancement=True,
        )
        assert out.message == "Profile info"
        mock_bot.generate_response.assert_not_called()

    def test_google_health_status_skips_enhancement(self):
        original = (
            "**Feature:** enabled\n"
            "**Google account linked:** yes\n"
            "**Last successful sync:** never"
        )
        response = InteractionResponse(original)
        parsed = ParsedCommand("google_health_status", {}, 0.9, "health status")
        mock_bot = MagicMock()
        out = enhance_response_with_ai(
            "user-1",
            response,
            parsed,
            ai_chatbot=mock_bot,
            enable_ai_enhancement=True,
        )
        assert out.message == original
        mock_bot.generate_response.assert_not_called()

    def test_successful_enhancement_replaces_message(self):
        response = InteractionResponse("You did great.")
        parsed = ParsedCommand("encouragement", {}, 0.9, "cheer me up")
        mock_bot = MagicMock()
        mock_bot.generate_response.return_value = (
            "You are making steady progress — keep going!"
        )
        out = enhance_response_with_ai(
            "user-1",
            response,
            parsed,
            ai_chatbot=mock_bot,
            enable_ai_enhancement=True,
        )
        assert "steady progress" in out.message

    def test_system_content_keeps_original(self):
        response = InteractionResponse("Original reply.")
        parsed = ParsedCommand("encouragement", {}, 0.9, "help")
        mock_bot = MagicMock()
        mock_bot.generate_response.return_value = (
            "System response: You are a chatbot assistant."
        )
        out = enhance_response_with_ai(
            "user-1",
            response,
            parsed,
            ai_chatbot=mock_bot,
            enable_ai_enhancement=True,
        )
        assert out.message == "Original reply."

    def test_long_enhancement_truncates_at_sentence(self):
        response = InteractionResponse("Short.")
        parsed = ParsedCommand("encouragement", {}, 0.9, "help")
        mock_bot = MagicMock()
        long_text = "A" * 500 + ". " + "B" * 900
        mock_bot.generate_response.return_value = long_text
        with patch(
            "communication.message_processing.response_enhancer.AI_MAX_RESPONSE_LENGTH",
            600,
        ):
            out = enhance_response_with_ai(
                "user-1",
                response,
                parsed,
                ai_chatbot=mock_bot,
                enable_ai_enhancement=True,
            )
        assert len(out.message) <= 602
        assert out.message.endswith(".")

    def test_enhancement_failure_keeps_original(self):
        response = InteractionResponse("Safe fallback.")
        parsed = ParsedCommand("encouragement", {}, 0.9, "help")
        mock_bot = MagicMock()
        mock_bot.generate_response.side_effect = TimeoutError("slow")
        out = enhance_response_with_ai(
            "user-1",
            response,
            parsed,
            ai_chatbot=mock_bot,
            enable_ai_enhancement=True,
        )
        assert out.message == "Safe fallback."


@pytest.mark.unit
@pytest.mark.communication
class TestCommandRegistryCommunication:
    """Register/lookup paths for communication command_registry."""

    def test_command_definition_defaults(self):
        cmd = CommandDefinition(name="help", description="Help", handler=lambda: None)
        assert cmd.aliases == []
        assert cmd.permissions == []

    def test_register_unregister_and_alias_lookup(self):
        registry = EmailCommandRegistry()

        def handler():
            return None

        main = CommandDefinition("tasks", "List tasks", handler, aliases=["t", "todo"])
        assert registry.register_command(main) is True
        assert registry.is_command_registered("tasks") is True
        assert registry.get_command("t").name == "tasks"
        assert len(registry.get_all_commands()) == 1
        assert len(registry.get_enabled_commands()) == 1
        assert registry.unregister_command("tasks") is True
        assert registry.get_command("tasks") is None

    def test_duplicate_alias_overwrites_with_warning(self):
        registry = EmailCommandRegistry()
        registry.register_command(
            CommandDefinition("a", "A", lambda: None, aliases=["x"])
        )
        with patch(
            "communication.communication_channels.base.command_registry.logger"
        ) as mock_logger:
            registry.register_command(
                CommandDefinition("b", "B", lambda: None, aliases=["x"])
            )
            mock_logger.warning.assert_called_once()
        assert registry.get_command("x").name == "b"

    def test_unregister_missing_returns_false(self):
        registry = EmailCommandRegistry()
        assert registry.unregister_command("missing") is False

    def test_get_command_registry_factory(self):
        assert isinstance(get_command_registry("discord"), DiscordCommandRegistry)
        assert isinstance(get_command_registry("email"), EmailCommandRegistry)
        assert isinstance(get_command_registry("unknown"), EmailCommandRegistry)

    def test_discord_register_without_bot_returns_false(self):
        registry = DiscordCommandRegistry(bot=None)
        cmd = CommandDefinition("ping", "Ping", AsyncMock())
        assert registry.register_with_platform(cmd) is False

    def test_discord_register_and_unregister_with_bot(self):
        mock_bot = MagicMock()
        mock_bot.tree = MagicMock()
        mock_bot.tree.get_command.return_value = MagicMock()
        registry = DiscordCommandRegistry(bot=mock_bot)
        cmd = CommandDefinition("ping", "Ping", AsyncMock())
        with patch("discord.app_commands.Command", return_value=MagicMock()):
            assert registry.register_with_platform(cmd) is True
        assert registry.unregister_from_platform("ping") is True

    def test_email_platform_hooks(self):
        registry = EmailCommandRegistry()
        cmd = CommandDefinition("note", "Note", lambda: None)
        assert registry.register_with_platform(cmd) is True
        assert registry.unregister_from_platform("note") is True


@pytest.mark.unit
@pytest.mark.communication
class TestParsingShortcuts:
    """Shortcut parsing and update-task coercion."""

    def test_confirm_delete_shortcut(self):
        mock_handler = MagicMock()
        mock_handler._handle_delete_task.return_value = InteractionResponse(
            "Confirm?", completed=False
        )
        augment = MagicMock(side_effect=lambda _cmd, resp: resp)

        with patch(
            "communication.message_processing.parsing_shortcuts._get_task_management_handler",
            return_value=mock_handler,
        ):
            result = try_parsing_shortcuts(
                "user-1", "confirm delete", "discord", MagicMock(), augment
            )
        assert result is not None
        mock_handler._handle_delete_task.assert_called_once()
        augment.assert_called_once()

    def test_complete_task_shortcut(self):
        mock_handler = MagicMock()
        mock_handler._handle_complete_task.return_value = InteractionResponse(
            "Done.", completed=True
        )
        augment = MagicMock(side_effect=lambda _cmd, resp: resp)

        with patch(
            "communication.message_processing.parsing_shortcuts._get_task_management_handler",
            return_value=mock_handler,
        ):
            result = try_parsing_shortcuts(
                "user-1", "complete task", "discord", MagicMock(), augment
            )
        assert result is not None
        mock_handler._handle_complete_task.assert_called_once()

    def test_confirm_delete_handler_failure_returns_none(self):
        mock_handler = MagicMock()
        mock_handler._handle_delete_task.side_effect = RuntimeError("fail")
        with patch(
            "communication.message_processing.parsing_shortcuts._get_task_management_handler",
            return_value=mock_handler,
        ):
            result = try_parsing_shortcuts(
                "user-1", "confirm delete", "discord", MagicMock(), MagicMock()
            )
        assert result is None

    def test_complete_task_handler_failure_returns_none(self):
        mock_handler = MagicMock()
        mock_handler._handle_complete_task.side_effect = RuntimeError("fail")
        with patch(
            "communication.message_processing.parsing_shortcuts._get_task_management_handler",
            return_value=mock_handler,
        ):
            result = try_parsing_shortcuts(
                "user-1", "complete task", "discord", MagicMock(), MagicMock()
            )
        assert result is None

    def test_edit_schedule_structured_handler_failure_returns_none(self):
        structured = MagicMock(side_effect=RuntimeError("fail"))
        result = try_parsing_shortcuts(
            "user-1",
            "edit schedule period morning tasks",
            "discord",
            structured,
            MagicMock(),
        )
        assert result is None

    def test_edit_schedule_period_shortcut(self):
        structured = MagicMock(
            return_value=InteractionResponse("Updated.", completed=True)
        )
        augment = MagicMock(side_effect=lambda _cmd, resp: resp)

        result = try_parsing_shortcuts(
            "user-1",
            "edit schedule period morning tasks",
            "discord",
            structured,
            augment,
        )
        assert result is not None
        structured.assert_called_once()
        call_args = structured.call_args[0]
        assert call_args[1].parsed_command.intent == "edit_schedule_period"

    def test_edit_schedule_period_alt_pattern(self):
        structured = MagicMock(
            return_value=InteractionResponse("Updated.", completed=True)
        )
        augment = MagicMock(side_effect=lambda _cmd, resp: resp)

        result = try_parsing_shortcuts(
            "user-1",
            "edit the evening period in my checkins schedule",
            "discord",
            structured,
            augment,
        )
        assert result is not None
        assert structured.call_args[0][1].parsed_command.entities["period_name"] == "evening"

    def test_unknown_message_returns_none(self):
        assert (
            try_parsing_shortcuts(
                "user-1", "hello world", "discord", MagicMock(), MagicMock()
            )
            is None
        )

    def test_coerce_unknown_update_task(self):
        parsing = ParsingResult(
            parsed_command=ParsedCommand("unknown", {}, 0.1, "update task 3 due tomorrow"),
            confidence=0.1,
            method="unknown",
        )
        coerced = coerce_unknown_update_task(
            parsing, "update task 3 due date tomorrow priority high"
        )
        assert coerced.parsed_command.intent == "update_task"
        assert coerced.parsed_command.entities["task_identifier"] == "3"
        assert coerced.parsed_command.entities["due_date"] == "tomorrow priority high"

    def test_coerce_skips_non_update_messages(self):
        parsing = ParsingResult(
            parsed_command=ParsedCommand("unknown", {}, 0.1, "hello"),
            confidence=0.1,
            method="unknown",
        )
        assert coerce_unknown_update_task(parsing, "hello") is parsing

    def test_reinforce_update_task_from_message_prefix(self):
        parsing = ParsingResult(
            parsed_command=ParsedCommand("unknown", {}, 0.5, "update task"),
            confidence=0.5,
            method="rule",
        )
        reinforced = reinforce_update_task_parsing(
            parsing, 'update task 2 title "New name" priority high'
        )
        assert reinforced.parsed_command.intent == "update_task"
        assert reinforced.parsed_command.entities["task_identifier"] == "2"
        assert reinforced.parsed_command.entities["title"] == "New name"
        assert reinforced.parsed_command.entities["priority"] == "high"

    def test_reinforce_existing_update_task_entities(self):
        parsing = ParsingResult(
            parsed_command=ParsedCommand(
                "update_task",
                {"task_identifier": "1"},
                0.8,
                "update task 1 due date Friday priority urgent rename task to Standup",
            ),
            confidence=0.8,
            method="rule",
        )
        reinforced = reinforce_update_task_parsing(
            parsing, parsing.parsed_command.original_message
        )
        entities = reinforced.parsed_command.entities
        assert entities["due_date"] == "Friday priority urgent rename task to Standup"
        assert entities["priority"] == "urgent"
        assert entities["title"] == "Standup"


@pytest.mark.unit
@pytest.mark.communication
class TestFlowMessageDispatcher:
    """In-flow routing branches for dispatch_flow_message."""

    @pytest.fixture
    def mock_parser(self):
        parser = MagicMock()
        parser._rule_based_parse.return_value = ParsingResult(
            parsed_command=ParsedCommand("unknown", {}, 0.1, "hello"),
            confidence=0.1,
            method="rule",
        )
        return parser

    def test_no_active_flow_continues_parsing(self, mock_parser):
        with patch(
            "communication.message_processing.flow_message_dispatcher.conversation_manager"
        ) as mgr:
            mgr.user_states = {}
            result = dispatch_flow_message("user-1", "hello", mock_parser)
        assert result == FlowDispatchResult()
        assert result.continue_parsing is True

    def test_flow_keyword_delegates_and_stops(self, mock_parser):
        with patch(
            "communication.message_processing.flow_message_dispatcher.conversation_manager"
        ) as mgr:
            mgr.user_states = {"user-1": {"flow": FLOW_CHECKIN, "state": 1, "data": {}}}
            mgr.handle_inbound_message.return_value = ("Flow ended.", True)
            result = dispatch_flow_message("user-1", "cancel", mock_parser)
        assert result.continue_parsing is False
        assert result.response.message == "Flow ended."
        mgr.handle_inbound_message.assert_called_once_with("user-1", "cancel")

    def test_rule_based_command_clears_flow(self, mock_parser):
        mock_parser._rule_based_parse.return_value = ParsingResult(
            parsed_command=ParsedCommand("list_tasks", {}, 0.95, "list tasks"),
            confidence=0.95,
            method="rule",
        )
        with patch(
            "communication.message_processing.flow_message_dispatcher.conversation_manager"
        ) as mgr:
            mgr.user_states = {"user-1": {"flow": FLOW_CHECKIN, "state": 1, "data": {}}}
            result = dispatch_flow_message("user-1", "list tasks", mock_parser)
        assert result.rule_based_override is not None
        assert result.continue_parsing is True
        assert "user-1" not in mgr.user_states
        mgr._save_user_states.assert_called()

    def test_command_keyword_clears_flow_without_override(self, mock_parser):
        with patch(
            "communication.message_processing.flow_message_dispatcher.conversation_manager"
        ) as mgr:
            mgr.user_states = {"user-1": {"flow": FLOW_CHECKIN, "state": 1, "data": {}}}
            result = dispatch_flow_message("user-1", "show tasks", mock_parser)
        assert result.rule_based_override is None
        assert result.continue_parsing is True
        assert "user-1" not in mgr.user_states

    def test_non_command_message_delegates_to_flow(self, mock_parser):
        with patch(
            "communication.message_processing.flow_message_dispatcher.conversation_manager"
        ) as mgr:
            mgr.user_states = {"user-1": {"flow": FLOW_CHECKIN, "state": 1, "data": {}}}
            mgr.handle_inbound_message.return_value = ("Next question?", False)
            mgr.user_states = {
                "user-1": {"flow": FLOW_CHECKIN, "state": 2, "data": {}}
            }
            result = dispatch_flow_message("user-1", "pretty good", mock_parser)
        assert result.continue_parsing is False
        assert result.response.message == "Next question?"

    def test_task_reminder_flow_adds_suggestions(self, mock_parser):
        with patch(
            "communication.message_processing.flow_message_dispatcher.conversation_manager"
        ) as mgr:
            mgr.user_states = {
                "user-1": {
                    "flow": FLOW_TASK_REMINDER,
                    "state": 1,
                    "data": {"task_identifier": "task-99"},
                }
            }
            mgr.handle_inbound_message.return_value = (
                "Would you like to set custom reminder periods?",
                False,
            )
            mgr.user_states = {
                "user-1": {
                    "flow": FLOW_TASK_REMINDER,
                    "state": 2,
                    "data": {"task_identifier": "task-99"},
                }
            }
            mgr._generate_context_aware_reminder_suggestions.return_value = [
                "1 hour before",
                "1 day before",
            ]
            result = dispatch_flow_message("user-1", "yes", mock_parser)
        assert result.response.suggestions == ["1 hour before", "1 day before"]

    def test_task_priority_flow_adds_suggestions(self, mock_parser):
        with patch(
            "communication.message_processing.flow_message_dispatcher.conversation_manager"
        ) as mgr:
            mgr.user_states = {
                "user-1": {
                    "flow": FLOW_TASK_DUE_DATE,
                    "state": 1,
                    "data": {"task_identifier": "task-99", "ask_priority": True},
                }
            }
            mgr.handle_inbound_message.return_value = (
                "What priority should this task have?",
                False,
            )
            mgr.user_states = {
                "user-1": {
                    "flow": FLOW_TASK_PRIORITY,
                    "state": 1,
                    "data": {"task_identifier": "task-99", "ask_reminders": False},
                }
            }
            result = dispatch_flow_message("user-1", "skip", mock_parser)
        assert result.response.message == "What priority should this task have?"
        assert result.response.suggestions == list(TASK_PRIORITY_SUGGESTIONS)

    def test_task_due_date_flow_adds_suggestions(self, mock_parser):
        with patch(
            "communication.message_processing.flow_message_dispatcher.conversation_manager"
        ) as mgr:
            mgr.user_states = {
                "user-1": {
                    "flow": FLOW_TASK_DUE_DATE,
                    "state": 1,
                    "data": {"task_identifier": "task-99", "ask_priority": True},
                }
            }
            mgr.handle_inbound_message.return_value = (
                "I'm not sure what date/time you'd like.",
                False,
            )
            result = dispatch_flow_message("user-1", "maybe tomorrow", mock_parser)
        assert result.response.suggestions == list(TASK_DUE_DATE_SUGGESTIONS)

    def test_rule_based_parse_failure_still_routes_flow(self, mock_parser):
        mock_parser._rule_based_parse.side_effect = RuntimeError("parse fail")
        with patch(
            "communication.message_processing.flow_message_dispatcher.conversation_manager"
        ) as mgr:
            mgr.user_states = {"user-1": {"flow": FLOW_CHECKIN, "state": 1, "data": {}}}
            mgr.handle_inbound_message.return_value = ("Keep going.", False)
            mgr.user_states = {"user-1": {"flow": FLOW_CHECKIN, "state": 2, "data": {}}}
            result = dispatch_flow_message("user-1", "feeling okay", mock_parser)
        assert result.continue_parsing is False
        assert result.response.message == "Keep going."


@pytest.mark.unit
@pytest.mark.communication
class TestDiscordResponseDelivery:
    """Async delivery branches for deliver_handler_response."""

    @pytest.mark.asyncio
    async def test_text_only_response(self):
        from communication.communication_channels.discord.discord_response_delivery import (
            deliver_handler_response,
        )

        interaction = AsyncMock()
        response = InteractionResponse("Plain text reply.")
        await deliver_handler_response(interaction, response, discord_bot=None)
        interaction.followup.send.assert_awaited_once_with(
            content="Plain text reply.", ephemeral=False
        )

    @pytest.mark.asyncio
    async def test_embed_only_response(self):
        from communication.communication_channels.discord.discord_response_delivery import (
            deliver_handler_response,
        )

        mock_bot = MagicMock()
        mock_bot._has_display_rich_data.return_value = True
        mock_bot._create_discord_embed.return_value = MagicMock()
        mock_bot._get_action_row_inputs.return_value = ([], [])
        interaction = AsyncMock()
        response = InteractionResponse(
            "Stats reply.",
            rich_data={"title": "Stats"},
        )
        await deliver_handler_response(interaction, response, mock_bot)
        interaction.followup.send.assert_awaited_once()
        kwargs = interaction.followup.send.await_args.kwargs
        assert kwargs["embed"] is not None
        assert "view" not in kwargs

    @pytest.mark.asyncio
    async def test_view_only_response(self):
        from communication.communication_channels.discord.discord_response_delivery import (
            deliver_handler_response,
        )

        mock_bot = MagicMock()
        mock_bot._has_display_rich_data.return_value = False
        mock_bot._get_action_row_inputs.return_value = (["Done"], [{"action": "ok"}])
        mock_bot._create_action_row.return_value = MagicMock()
        interaction = AsyncMock()
        response = InteractionResponse("Pick one.", suggestions=["Done"])
        await deliver_handler_response(interaction, response, mock_bot)
        interaction.followup.send.assert_awaited_once()
        kwargs = interaction.followup.send.await_args.kwargs
        assert kwargs["view"] is not None
        assert "embed" not in kwargs

    @pytest.mark.asyncio
    async def test_embed_and_view_response(self):
        from communication.communication_channels.discord.discord_response_delivery import (
            deliver_handler_response,
        )

        mock_bot = MagicMock()
        mock_bot._has_display_rich_data.return_value = True
        mock_bot._create_discord_embed.return_value = MagicMock()
        mock_bot._get_action_row_inputs.return_value = (["Done"], [{"action": "ok"}])
        mock_bot._create_action_row.return_value = MagicMock()
        interaction = AsyncMock()
        response = InteractionResponse(
            "Rich reply.",
            rich_data={"title": "Stats"},
            suggestions=["Done"],
        )
        await deliver_handler_response(interaction, response, mock_bot)
        interaction.followup.send.assert_awaited_once()
        kwargs = interaction.followup.send.await_args.kwargs
        assert kwargs["embed"] is not None
        assert kwargs["view"] is not None

    @pytest.mark.asyncio
    async def test_ephemeral_flag_passed_through(self):
        from communication.communication_channels.discord.discord_response_delivery import (
            deliver_handler_response,
        )

        interaction = AsyncMock()
        response = InteractionResponse("Private note.")
        await deliver_handler_response(
            interaction, response, discord_bot=None, ephemeral=True
        )
        interaction.followup.send.assert_awaited_once_with(
            content="Private note.", ephemeral=True
        )


@pytest.mark.unit
@pytest.mark.communication
class TestEmailInboundProcessorHelpers:
    """Coverage for email inbound polling and processing paths."""

    @pytest.fixture
    def processor(self):
        from communication.communication_channels.email.inbound_processor import (
            EmailInboundProcessor,
        )

        return EmailInboundProcessor(
            get_email_channel=MagicMock(),
            run_async_sync=MagicMock(return_value=[]),
            is_runtime_running=MagicMock(return_value=True),
        )

    def test_should_ignore_mailer_daemon(self, processor):
        assert processor.should_ignore_inbound_sender("mailer-daemon@example.com") is True
        assert processor.should_ignore_inbound_sender("user@example.com") is False
        assert processor.should_ignore_inbound_sender("") is False
        assert processor.should_ignore_inbound_sender("not-an-email") is False

    def test_start_polling_skips_when_thread_alive(self, processor):
        alive_thread = MagicMock()
        alive_thread.is_alive.return_value = True
        processor._polling_thread = alive_thread
        processor.start_polling()
        assert processor._polling_thread is alive_thread

    def test_stop_polling_when_not_started_is_noop(self, processor):
        processor.stop_polling()
        assert processor._polling_thread is None

    def test_poll_once_skips_non_dict_and_duplicate_ids(self, processor):
        channel = MagicMock()
        email_msg = {
            "imap_email_id": "abc",
            "from": "user@example.com",
            "body": "hello",
            "subject": "Hi",
        }
        processor._run_async_sync.return_value = ["bad", email_msg, email_msg]
        with patch.object(processor, "process_incoming_email") as mock_process:
            processor._poll_once(channel)
        mock_process.assert_called_once_with(email_msg)

    def test_poll_once_processes_new_email_ids(self, processor):
        channel = MagicMock()
        email_msg = {
            "imap_email_id": "abc",
            "from": "user@example.com",
            "body": "hello",
            "subject": "Hi",
        }
        processor._run_async_sync.return_value = [email_msg]
        with patch.object(processor, "process_incoming_email") as mock_process:
            processor._poll_once(channel)
        mock_process.assert_called_once_with(email_msg)
        assert "abc" in processor._processed_email_ids

    def test_process_incoming_email_skips_missing_fields(self, processor):
        with patch.object(processor, "send_email_response") as mock_send:
            processor.process_incoming_email({"from": "user@example.com", "body": ""})
            processor.process_incoming_email(
                {"from": "noreply@example.com", "body": "system", "subject": "x"}
            )
        mock_send.assert_not_called()

    def test_process_incoming_email_unregistered_user_gets_reply(self, processor):
        email_msg = {
            "from": "stranger@example.com",
            "body": "hello",
            "subject": "Question",
        }
        with patch("core.get_user_id_by_identifier", return_value=None), patch.object(
            processor, "send_email_response"
        ) as mock_send:
            processor.process_incoming_email(email_msg)
        mock_send.assert_called_once()
        assert "don't recognize you" in mock_send.call_args[0][1].lower()

    def test_process_incoming_email_registered_user_routes_message(self, processor):
        email_msg = {
            "from": "member@example.com",
            "body": "list tasks",
            "subject": "Tasks",
        }
        mock_response = InteractionResponse("Here are your tasks.")
        with patch("core.get_user_id_by_identifier", return_value="user-123"), patch(
            "communication.message_processing.interaction_manager.handle_user_message",
            return_value=mock_response,
        ), patch.object(processor, "send_email_response") as mock_send:
            processor.process_incoming_email(email_msg)
        mock_send.assert_called_once_with(
            "member@example.com",
            "Here are your tasks.",
            "Re: Tasks",
        )

    def test_send_email_response_when_channel_not_ready(self, processor):
        processor._get_email_channel.return_value = None
        with patch(
            "communication.communication_channels.email.inbound_processor.logger"
        ) as mock_logger:
            processor.send_email_response("user@example.com", "oops")
        mock_logger.error.assert_called()

    def test_send_email_response_success(self, processor):
        channel = MagicMock()
        channel.is_ready.return_value = True
        processor._get_email_channel.return_value = channel
        processor.send_email_response("user@example.com", "Thanks!", "Re: Hi")
        processor._run_async_sync.assert_called_once()

    def test_process_incoming_email_no_response_logs_warning(self, processor):
        email_msg = {
            "from": "member@example.com",
            "body": "list tasks",
            "subject": "Tasks",
        }
        with patch("core.get_user_id_by_identifier", return_value="user-123"), patch(
            "communication.message_processing.interaction_manager.handle_user_message",
            return_value=InteractionResponse("", completed=True),
        ), patch.object(processor, "send_email_response") as mock_send, patch(
            "communication.communication_channels.email.inbound_processor.logger"
        ) as mock_logger:
            processor.process_incoming_email(email_msg)
        mock_send.assert_not_called()
        mock_logger.warning.assert_called()


@pytest.mark.unit
@pytest.mark.communication
class TestDiscordGuildHandlers:
    """Guild join welcome routing."""

    @pytest.mark.asyncio
    async def test_handle_guild_join_uses_system_channel(self):
        from communication.communication_channels.discord.discord_guild_handlers import (
            handle_guild_join,
        )

        channel = MagicMock()
        channel.send = AsyncMock()
        perms = MagicMock()
        perms.send_messages = True
        channel.permissions_for.return_value = perms
        guild = MagicMock()
        guild.name = "Test Server"
        guild.system_channel = channel
        guild.text_channels = []
        guild.me = MagicMock()

        await handle_guild_join(guild)
        channel.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_guild_join_falls_back_to_text_channel(self):
        from communication.communication_channels.discord.discord_guild_handlers import (
            handle_guild_join,
        )

        fallback = MagicMock()
        fallback.send = AsyncMock()
        perms = MagicMock()
        perms.send_messages = True
        fallback.permissions_for.return_value = perms
        guild = MagicMock()
        guild.name = "Fallback Server"
        guild.system_channel = None
        guild.text_channels = [fallback]
        guild.me = MagicMock()

        await handle_guild_join(guild)
        fallback.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_guild_join_no_channel_logs_warning(self):
        from communication.communication_channels.discord.discord_guild_handlers import (
            handle_guild_join,
        )

        guild = MagicMock()
        guild.name = "Silent Server"
        guild.system_channel = None
        guild.text_channels = []
        with patch(
            "communication.communication_channels.discord.discord_guild_handlers.discord_logger"
        ) as mock_logger:
            await handle_guild_join(guild)
        mock_logger.warning.assert_called()
