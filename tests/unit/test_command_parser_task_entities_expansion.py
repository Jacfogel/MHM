"""
Expanded unit coverage for task-centric helpers in the command parser.

These tests focus on extraction helpers that are lightweight and deterministic.
"""

import pytest

from communication.message_processing.command_parser import EnhancedCommandParser


@pytest.fixture(scope="module")
def command_parser():
    """Create EnhancedCommandParser instance once per module."""
    return EnhancedCommandParser()


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.tasks
class TestCommandParserTaskEntityExtraction:
    """Coverage expansion for task entity extraction helpers."""

    @pytest.mark.parametrize(
        "title, expected_due_date",
        [
            ("Call mom in 2 hours", "in 2 hours"),
            ("Pay rent in 3 days", "in 3 days"),
            ("Review report in 1 week", "in 1 week"),
            ("Meet client next tuesday at 11:00", "next tuesday at 11:00"),
            ("Plan trip next monday", "next monday"),
            ("Submit timesheet friday at noon", "friday at noon"),
            ("Go jogging monday at 2pm", "monday at 2pm"),
            ("Check mail friday", "friday"),
            ("Call dentist tomorrow", "tomorrow"),
            ("Renew license next week", "next week"),
            ("Update resume next month", "next month"),
            ("Pay rent on March 5", "on March 5"),
            ("Renew passport by April 12", "by April 12"),
            ("Buy groceries on May 1", "on May 1"),
        ],
    )
    def test_extract_task_entities_due_date_patterns(
        self, command_parser, title, expected_due_date
    ):
        entities = command_parser._extract_task_entities(title)

        assert entities.get("due_date") == expected_due_date

    @pytest.mark.parametrize(
        "title, expected_due_time",
        [
            ("Meet client next tuesday at 11:00", "11:00"),
            ("Submit timesheet friday at noon", "noon"),
            ("Go jogging monday at 2pm", "2pm"),
            ("Coffee next friday at 9am", "9am"),
            ("Review notes wednesday at 7pm", "7pm"),
            ("Check report sunday at midnight", "midnight"),
        ],
    )
    def test_extract_task_entities_due_time_patterns(
        self, command_parser, title, expected_due_time
    ):
        entities = command_parser._extract_task_entities(title)

        assert entities.get("due_time") == expected_due_time

    @pytest.mark.parametrize(
        "title, expected_priority",
        [
            ("Urgent: fix bug", "high"),
            ("This is ASAP", "high"),
            ("Important call", "high"),
            ("Critical report", "high"),
            ("Low priority chore", "low"),
            ("Schedule when convenient", "low"),
            ("No rush on this", "low"),
            ("Regular task", None),
        ],
    )
    def test_extract_task_entities_priority_patterns(
        self, command_parser, title, expected_priority
    ):
        entities = command_parser._extract_task_entities(title)

        if expected_priority is None:
            assert "priority" not in entities
        else:
            assert entities.get("priority") == expected_priority

    @pytest.mark.parametrize(
        "message, expected_task_name",
        [
            ("I just brushed my teeth today", "teeth"),
            ("I washed my car, we can complete that task", "car"),
            ("I cleaned the kitchen today", "the kitchen"),
            ("I finished homework now", "homework"),
            ("I completed my notes just now", "notes"),
            ("I did laundry today", "laundry"),
            ("I cleaned my desk, so we can complete that task", "desk"),
            ("We completed the task", None),
        ],
    )
    def test_extract_task_name_from_context(
        self, command_parser, message, expected_task_name
    ):
        task_name = command_parser._extract_task_name_from_context(message)

        assert task_name == expected_task_name


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.tasks
class TestCommandParserUpdateEntityExtraction:
    """Coverage expansion for update entity extraction."""

    @pytest.mark.parametrize(
        "update_text, expected_fields",
        [
            ("priority high", {"priority": "high"}),
            ("priority to critical", {"priority": "critical"}),
            ("priority medium due tomorrow", {"priority": "medium", "due_date": "tomorrow"}),
            ("priority low due date next week", {"priority": "low", "due_date": "next week"}),
            ("due date friday", {"due_date": "friday"}),
            ("due next month", {"due_date": "next month"}),
            ("title \"New Name\"", {"title": "New Name"}),
            ("title Updated Task", {"title": "Updated Task"}),
            ("rename task to Fix login", {"title": "Fix login"}),
            ("rename to \"Plan trip\"", {"title": "Plan trip"}),
            ("priority urgent title \"Build docs\" due next week", {"priority": "urgent", "title": "Build docs", "due_date": "next week"}),
            ("priority low title Cleanup", {"priority": "low", "title": "Cleanup"}),
        ],
    )
    def test_extract_update_entities(self, command_parser, update_text, expected_fields):
        entities = command_parser._extract_update_entities(update_text)

        for key, value in expected_fields.items():
            assert entities.get(key) == value


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.ai
class TestCommandParserAiResponseExtraction:
    """Coverage expansion for AI response extraction helpers."""

    @pytest.mark.parametrize(
        "ai_response, expected_intent",
        [
            ("Please create task for today", "create_task"),
            ("Show list tasks now", "list_tasks"),
            ("Complete task 2", "complete_task"),
            ("Delete task 3", "delete_task"),
            ("Update task 4", "update_task"),
            ("Task stats for this week", "task_stats"),
            ("Start checkin now", "start_checkin"),
            ("Checkin status please", "checkin_status"),
            ("Show profile", "show_profile"),
            ("Update profile name", "update_profile"),
            ("Profile stats", "profile_stats"),
            ("Help me", "help"),
            ("Show commands", "commands"),
            ("Provide examples", "examples"),
        ],
    )
    def test_extract_intent_from_ai_response(
        self, command_parser, ai_response, expected_intent
    ):
        intent = command_parser._extract_intent_from_ai_response(ai_response)

        assert intent == expected_intent

    @pytest.mark.parametrize(
        "ai_response, expected_title, expected_task_id",
        [
            ("Create task \"Buy milk\"", "Buy milk", None),
            ("Complete task 12", None, "12"),
            ("Update task 5 titled \"New title\"", "New title", "5"),
            ("task 7 \"Plan trip\"", "Plan trip", "7"),
            ("Create task \"Alpha\" task 3", "Alpha", "3"),
            ("task 42", None, "42"),
            ("No quotes here", None, None),
            ("\"Draft report\" is the task 9", "Draft report", "9"),
        ],
    )
    def test_extract_entities_from_ai_response(
        self, command_parser, ai_response, expected_title, expected_task_id
    ):
        entities = command_parser._extract_entities_from_ai_response(ai_response)

        assert entities.get("title") == expected_title
        assert entities.get("task_identifier") == expected_task_id
