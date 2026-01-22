"""
Task Handler Behavior Tests

Tests for communication/command_handlers/task_handler.py focusing on real behavior and side effects.
These tests verify that the task handler actually works and produces expected
side effects rather than just returning values.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Import the modules we're testing
from communication.command_handlers.task_handler import TaskManagementHandler
from communication.command_handlers.shared_types import (
    InteractionResponse,
    ParsedCommand,
)
from tests.test_utilities import TestUserFactory
from core.time_utilities import DATE_ONLY, format_timestamp, now_datetime_full


class TestTaskHandlerBehavior:
    """Test task handler real behavior and side effects."""

    def _create_test_user(
        self, user_id: str, enable_checkins: bool = True, test_data_dir: str = None
    ) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(
            user_id, enable_checkins=enable_checkins, test_data_dir=test_data_dir
        )

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_can_handle_intents(self):
        """Test that TaskManagementHandler can handle all expected intents."""
        handler = TaskManagementHandler()

        expected_intents = [
            "create_task",
            "list_tasks",
            "complete_task",
            "delete_task",
            "update_task",
            "task_stats",
        ]
        for intent in expected_intents:
            assert handler.can_handle(
                intent
            ), f"TaskManagementHandler should handle {intent}"

        # Test that it doesn't handle other intents
        assert not handler.can_handle(
            "start_checkin"
        ), "TaskManagementHandler should not handle start_checkin"
        assert not handler.can_handle(
            "show_profile"
        ), "TaskManagementHandler should not handle show_profile"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_get_help(self):
        """Test that TaskManagementHandler returns help text."""
        handler = TaskManagementHandler()
        help_text = handler.get_help()

        assert isinstance(help_text, str), "Should return help text as string"
        assert len(help_text) > 0, "Help text should not be empty"
        assert "task" in help_text.lower(), "Help text should mention tasks"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_get_examples(self):
        """Test that TaskManagementHandler returns example commands."""
        handler = TaskManagementHandler()
        examples = handler.get_examples()

        assert isinstance(examples, list), "Should return examples as list"
        assert len(examples) > 0, "Should have at least one example"
        assert all(
            isinstance(ex, str) for ex in examples
        ), "All examples should be strings"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_unknown_intent(self):
        """Test that TaskManagementHandler handles unknown intents gracefully."""
        handler = TaskManagementHandler()
        parsed_command = ParsedCommand(
            intent="unknown_intent",
            entities={},
            confidence=0.5,
            original_message="unknown command",
        )

        response = handler.handle("test_user", parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert (
            "don't understand" in response.message.lower()
            or "try" in response.message.lower()
        ), "Should indicate unknown command"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @pytest.mark.file_io
    @patch("communication.command_handlers.task_handler.create_task")
    def test_task_handler_create_task_success(self, mock_create_task, test_data_dir):
        """Test that TaskManagementHandler creates tasks successfully."""
        handler = TaskManagementHandler()
        user_id = "test_user_task_create"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        mock_create_task.return_value = "task_123"
        parsed_command = ParsedCommand(
            intent="create_task",
            entities={"title": "Test Task", "priority": "high", "due_date": "tomorrow"},
            confidence=0.9,
            original_message="create task 'Test Task' priority high due tomorrow",
        )

        # Deterministic "now" for production-behavior-sensitive relative date parsing.
        test_now_dt = datetime(2026, 1, 20, 12, 0, 0)
        with (
            patch(
                "core.time_utilities.now_datetime_full",
                return_value=test_now_dt,
            ),
            patch(
                "communication.command_handlers.task_handler.now_datetime_full",
                return_value=test_now_dt,
                create=True,
            ),
        ):
            response = handler.handle(user_id, parsed_command)

        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert "created" in response.message.lower(), "Should indicate task was created"
        assert "Test Task" in response.message, "Should include task title"
        assert not response.completed, "Should ask about reminder periods"

        # Verify actual system changes: Check that create_task was called with correct data
        mock_create_task.assert_called_once()
        call_args = mock_create_task.call_args
        call_kwargs = call_args[1] if call_args[1] else {}
        assert (
            call_kwargs.get("user_id") == user_id
        ), "Should create task for correct user"
        assert (
            call_kwargs.get("title") == "Test Task"
        ), "Should create task with correct title"
        assert (
            call_kwargs.get("priority") == "high"
        ), "Should create task with correct priority"
        assert (
            call_kwargs.get("due_date") is not None
        ), "Should parse and include due_date"

        # Verify due_date was parsed from 'tomorrow' to actual date
        expected_date = format_timestamp((test_now_dt + timedelta(days=1)), DATE_ONLY)
        assert (
            call_kwargs.get("due_date") == expected_date
        ), f"Should parse 'tomorrow' to {expected_date}"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_create_task_missing_title(self):
        """Test that TaskManagementHandler asks for title when missing."""
        handler = TaskManagementHandler()
        parsed_command = ParsedCommand(
            intent="create_task",
            entities={},
            confidence=0.9,
            original_message="create task",
        )

        response = handler.handle("test_user", parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert not response.completed, "Should ask for title"
        assert (
            "name" in response.message.lower() or "title" in response.message.lower()
        ), "Should ask for task name"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @pytest.mark.file_io
    @patch("communication.command_handlers.task_handler.create_task")
    def test_task_handler_create_task_with_recurrence(
        self, mock_create_task, test_data_dir
    ):
        """Test that TaskManagementHandler creates recurring tasks."""
        handler = TaskManagementHandler()
        user_id = "test_user_task_recurring"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        mock_create_task.return_value = "task_456"
        parsed_command = ParsedCommand(
            intent="create_task",
            entities={
                "title": "Daily Task",
                "recurrence_pattern": "daily",
                "recurrence_interval": 1,
            },
            confidence=0.9,
            original_message="create task 'Daily Task' repeat daily",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert "created" in response.message.lower(), "Should indicate task was created"
        assert (
            "repeats" in response.message.lower()
            or "repeat" in response.message.lower()
        ), "Should mention recurrence"
        assert mock_create_task.called, "Should call create_task"
        call_kwargs = (
            mock_create_task.call_args[1] if mock_create_task.call_args else {}
        )
        assert (
            call_kwargs.get("recurrence_pattern") == "daily"
        ), "Should set recurrence pattern"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_parse_relative_date_today(self):
        """Test that TaskManagementHandler parses 'today' correctly."""
        handler = TaskManagementHandler()

        # Deterministic "now" for production-behavior-sensitive relative date parsing.
        test_now_dt = datetime(2026, 1, 20, 12, 0, 0)
        with (
            patch(
                "core.time_utilities.now_datetime_full",
                return_value=test_now_dt,
            ),
            patch(
                "communication.command_handlers.task_handler.now_datetime_full",
                return_value=test_now_dt,
                create=True,
            ),
        ):
            result = handler._handle_create_task__parse_relative_date("today")
            expected = format_timestamp(test_now_dt, DATE_ONLY)

        assert result == expected, f"Should parse 'today' as {expected}, got {result}"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_parse_relative_date_tomorrow(self):
        """Test that TaskManagementHandler parses 'tomorrow' correctly."""
        handler = TaskManagementHandler()

        # Deterministic "now" for production-behavior-sensitive relative date parsing.
        test_now_dt = datetime(2026, 1, 20, 12, 0, 0)
        with (
            patch(
                "core.time_utilities.now_datetime_full",
                return_value=test_now_dt,
            ),
            patch(
                "communication.command_handlers.task_handler.now_datetime_full",
                return_value=test_now_dt,
                create=True,
            ),
        ):
            result = handler._handle_create_task__parse_relative_date("tomorrow")
            expected = format_timestamp((test_now_dt + timedelta(days=1)), DATE_ONLY)

        assert (
            result == expected
        ), f"Should parse 'tomorrow' as {expected}, got {result}"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_parse_relative_date_next_week(self):
        """Test that TaskManagementHandler parses 'next week' correctly."""
        handler = TaskManagementHandler()

        # Deterministic "now" for production-behavior-sensitive relative date parsing.
        test_now_dt = datetime(2026, 1, 20, 12, 0, 0)
        with (
            patch(
                "core.time_utilities.now_datetime_full",
                return_value=test_now_dt,
            ),
            patch(
                "communication.command_handlers.task_handler.now_datetime_full",
                return_value=test_now_dt,
                create=True,
            ),
        ):
            result = handler._handle_create_task__parse_relative_date("next week")
            expected = format_timestamp((test_now_dt + timedelta(days=7)), DATE_ONLY)

        assert (
            result == expected
        ), f"Should parse 'next week' as {expected}, got {result}"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_parse_relative_date_absolute_date(self):
        """Test that TaskManagementHandler passes through absolute dates."""
        handler = TaskManagementHandler()
        absolute_date = "2024-12-25"
        result = handler._handle_create_task__parse_relative_date(absolute_date)
        assert (
            result == absolute_date
        ), f"Should pass through absolute date {absolute_date}, got {result}"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @pytest.mark.file_io
    @patch("communication.command_handlers.task_handler.load_active_tasks")
    def test_task_handler_list_tasks_success(self, mock_load_tasks, test_data_dir):
        """Test that TaskManagementHandler lists tasks successfully."""
        handler = TaskManagementHandler()
        user_id = "test_user_task_list"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        mock_load_tasks.return_value = [
            {
                "title": "Task 1",
                "priority": "high",
                "due_date": "2024-12-20",
                "task_id": "task_1",
            },
            {
                "title": "Task 2",
                "priority": "medium",
                "due_date": None,
                "task_id": "task_2",
            },
        ]

        parsed_command = ParsedCommand(
            intent="list_tasks",
            entities={},
            confidence=0.9,
            original_message="list tasks",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "task" in response.message.lower(), "Should mention tasks"
        assert (
            "Task 1" in response.message or "Task 2" in response.message
        ), "Should include task titles"
        mock_load_tasks.assert_called_once_with(user_id)

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @pytest.mark.file_io
    @patch("communication.command_handlers.task_handler.load_active_tasks")
    def test_task_handler_list_tasks_no_tasks(self, mock_load_tasks, test_data_dir):
        """Test that TaskManagementHandler handles no tasks gracefully."""
        handler = TaskManagementHandler()
        user_id = "test_user_task_empty"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        mock_load_tasks.return_value = []

        parsed_command = ParsedCommand(
            intent="list_tasks",
            entities={},
            confidence=0.9,
            original_message="list tasks",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert (
            "no" in response.message.lower()
            or "empty" in response.message.lower()
            or "great job" in response.message.lower()
        ), "Should indicate no tasks"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @pytest.mark.file_io
    @patch("communication.command_handlers.task_handler.get_tasks_due_soon")
    @patch("communication.command_handlers.task_handler.load_active_tasks")
    def test_task_handler_list_tasks_filter_due_soon(
        self, mock_load_tasks, mock_due_soon, test_data_dir
    ):
        """Test that TaskManagementHandler filters tasks by due_soon."""
        handler = TaskManagementHandler()
        user_id = "test_user_task_filter"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        mock_load_tasks.return_value = [
            {
                "title": "Task 1",
                "priority": "high",
                "due_date": "2024-12-20",
                "task_id": "task_1",
            }
        ]
        mock_due_soon.return_value = [
            {
                "title": "Due Task",
                "priority": "medium",
                "due_date": "2024-12-20",
                "task_id": "task_2",
            }
        ]

        parsed_command = ParsedCommand(
            intent="list_tasks",
            entities={"filter": "due_soon"},
            confidence=0.9,
            original_message="list tasks due soon",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        mock_due_soon.assert_called_once_with(user_id, days_ahead=7)

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @pytest.mark.file_io
    @patch("communication.command_handlers.task_handler.complete_task")
    @patch("communication.command_handlers.task_handler.load_active_tasks")
    def test_task_handler_complete_task_success(
        self, mock_load_tasks, mock_complete_task, test_data_dir
    ):
        """Test that TaskManagementHandler completes tasks successfully."""
        handler = TaskManagementHandler()
        user_id = "test_user_task_complete"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        mock_load_tasks.return_value = [
            {"title": "Task 1", "priority": "high", "task_id": "task_1"},
            {"title": "Task 2", "priority": "medium", "task_id": "task_2"},
        ]
        mock_complete_task.return_value = True

        parsed_command = ParsedCommand(
            intent="complete_task",
            entities={"task_identifier": "1"},
            confidence=0.9,
            original_message="complete task 1",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert (
            "completed" in response.message.lower()
        ), "Should indicate task was completed"
        assert "Task 1" in response.message, "Should include task title"

        # Verify actual system changes: Check that complete_task was called with correct parameters
        mock_complete_task.assert_called_once_with(user_id, "task_1")
        # Verify the task was found correctly by number (1 = first task)
        mock_load_tasks.assert_called_once_with(user_id)

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @pytest.mark.file_io
    @patch("communication.command_handlers.task_handler.load_active_tasks")
    def test_task_handler_complete_task_not_found(self, mock_load_tasks, test_data_dir):
        """Test that TaskManagementHandler handles task not found."""
        handler = TaskManagementHandler()
        user_id = "test_user_task_notfound"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        mock_load_tasks.return_value = [
            {"title": "Task 1", "priority": "high", "task_id": "task_1"}
        ]

        parsed_command = ParsedCommand(
            intent="complete_task",
            entities={"task_identifier": "999"},
            confidence=0.9,
            original_message="complete task 999",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "not found" in response.message.lower(), "Should indicate task not found"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_complete_task_missing_identifier(self):
        """Test that TaskManagementHandler asks for task identifier when missing."""
        handler = TaskManagementHandler()
        parsed_command = ParsedCommand(
            intent="complete_task",
            entities={},
            confidence=0.9,
            original_message="complete task",
        )

        response = handler.handle("test_user", parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert not response.completed, "Should ask for identifier"
        assert (
            "which" in response.message.lower() or "specify" in response.message.lower()
        ), "Should ask for task identifier"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @pytest.mark.file_io
    @patch("communication.command_handlers.task_handler.delete_task")
    @patch("communication.command_handlers.task_handler.load_active_tasks")
    def test_task_handler_delete_task_success(
        self, mock_load_tasks, mock_delete_task, test_data_dir
    ):
        """Test that TaskManagementHandler deletes tasks successfully."""
        handler = TaskManagementHandler()
        user_id = "test_user_task_delete"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        mock_load_tasks.return_value = [
            {"title": "Task 1", "priority": "high", "task_id": "task_1"}
        ]
        mock_delete_task.return_value = True

        parsed_command = ParsedCommand(
            intent="delete_task",
            entities={
                "task_identifier": "1"
            },  # Use numeric identifier for immediate deletion
            confidence=0.9,
            original_message="delete task 1",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "deleted" in response.message.lower(), "Should indicate task was deleted"
        assert "Task 1" in response.message, "Should include task title"

        # Verify actual system changes: Check that delete_task was called with correct parameters
        mock_delete_task.assert_called_once_with(user_id, "task_1")
        # Verify the task was found correctly by name
        mock_load_tasks.assert_called_once_with(user_id)

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @pytest.mark.file_io
    @patch("communication.command_handlers.task_handler.update_task")
    @patch("communication.command_handlers.task_handler.load_active_tasks")
    def test_task_handler_update_task_success(
        self, mock_load_tasks, mock_update_task, test_data_dir
    ):
        """Test that TaskManagementHandler updates tasks successfully."""
        handler = TaskManagementHandler()
        user_id = "test_user_task_update"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        mock_load_tasks.return_value = [
            {"title": "Task 1", "priority": "medium", "task_id": "task_1"}
        ]
        mock_update_task.return_value = True

        parsed_command = ParsedCommand(
            intent="update_task",
            entities={"task_identifier": "1", "priority": "high"},
            confidence=0.9,
            original_message="update task 1 priority high",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "updated" in response.message.lower(), "Should indicate task was updated"

        # Verify actual system changes: Check that update_task was called with correct data
        mock_update_task.assert_called_once()
        # update_task is called with positional args: (user_id, task_id, updates)
        call_args = mock_update_task.call_args
        call_user_id = call_args[0][0] if call_args[0] else call_args[1].get("user_id")
        call_task_id = (
            call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("task_id")
        )
        updates = (
            call_args[0][2]
            if len(call_args[0]) > 2
            else call_args[1].get("updates", {})
        )

        assert call_user_id == user_id, "Should update task for correct user"
        assert call_task_id == "task_1", "Should update correct task"
        assert updates.get("priority") == "high", "Should update priority to high"
        assert len(updates) == 1, "Should only update priority field"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @pytest.mark.file_io
    @patch("communication.command_handlers.task_handler.load_active_tasks")
    def test_task_handler_update_task_missing_updates(
        self, mock_load_tasks, test_data_dir
    ):
        """Test that TaskManagementHandler asks for updates when missing."""
        handler = TaskManagementHandler()
        user_id = "test_user_task_update_missing"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        mock_load_tasks.return_value = [
            {"title": "Task 1", "priority": "medium", "task_id": "task_1"}
        ]

        parsed_command = ParsedCommand(
            intent="update_task",
            entities={"task_identifier": "1"},
            confidence=0.9,
            original_message="update task 1",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert not response.completed, "Should ask for updates"
        assert (
            "what" in response.message.lower() or "update" in response.message.lower()
        ), "Should ask what to update"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @pytest.mark.file_io
    @patch("core.checkin_analytics.CheckinAnalytics")
    @patch("communication.command_handlers.task_handler.get_user_task_stats")
    def test_task_handler_task_stats_success(
        self, mock_get_stats, mock_analytics_class, test_data_dir
    ):
        """Test that TaskManagementHandler shows task statistics successfully."""
        handler = TaskManagementHandler()
        user_id = "test_user_task_stats"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        mock_get_stats.return_value = {
            "active_tasks": 5,
            "completed_tasks": 10,
            "total_tasks": 15,
        }

        mock_analytics_instance = mock_analytics_class.return_value
        mock_analytics_instance.get_task_weekly_stats.return_value = {
            "Task 1": {"completion_rate": 80, "completed_days": 8, "total_days": 10},
            "Task 2": {"completion_rate": 60, "completed_days": 6, "total_days": 10},
        }

        parsed_command = ParsedCommand(
            intent="task_stats",
            entities={"days": 7, "period_name": "this week"},
            confidence=0.9,
            original_message="task stats",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert (
            "statistics" in response.message.lower()
            or "stats" in response.message.lower()
        ), "Should mention statistics"
        # Check for task stats content (task names, completion rates, or overall stats)
        assert (
            "task" in response.message.lower()
            or "habit" in response.message.lower()
            or "progress" in response.message.lower()
        ), "Should include task stats"
        mock_get_stats.assert_called_once_with(user_id)
        mock_analytics_instance.get_task_weekly_stats.assert_called_once_with(
            user_id, 7
        )

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_find_task_by_number(self):
        """Test that TaskManagementHandler finds tasks by number."""
        handler = TaskManagementHandler()
        tasks = [
            {"title": "Task 1", "task_id": "task_1"},
            {"title": "Task 2", "task_id": "task_2"},
            {"title": "Task 3", "task_id": "task_3"},
        ]

        task = handler._handle_complete_task__find_task_by_identifier(tasks, "2")
        assert task is not None, "Should find task by number"
        assert task["title"] == "Task 2", "Should find correct task"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_find_task_by_name(self):
        """Test that TaskManagementHandler finds tasks by name."""
        handler = TaskManagementHandler()
        tasks = [
            {"title": "Brush Teeth", "task_id": "task_1"},
            {"title": "Wash Dishes", "task_id": "task_2"},
        ]

        task = handler._handle_complete_task__find_task_by_identifier(
            tasks, "Brush Teeth"
        )
        assert task is not None, "Should find task by name"
        assert task["title"] == "Brush Teeth", "Should find correct task"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_find_task_by_partial_name(self):
        """Test that TaskManagementHandler finds tasks by partial name."""
        handler = TaskManagementHandler()
        tasks = [
            {"title": "Brush Teeth Every Morning", "task_id": "task_1"},
            {"title": "Wash Dishes After Dinner", "task_id": "task_2"},
        ]

        task = handler._handle_complete_task__find_task_by_identifier(tasks, "teeth")
        assert task is not None, "Should find task by partial name"
        assert "Teeth" in task["title"], "Should find correct task"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_find_task_by_task_id(self):
        """Test that TaskManagementHandler finds tasks by task_id."""
        handler = TaskManagementHandler()
        tasks = [
            {"title": "Task 1", "task_id": "task_123"},
            {"title": "Task 2", "task_id": "task_456"},
        ]

        task = handler._handle_complete_task__find_task_by_identifier(tasks, "task_123")
        assert task is not None, "Should find task by task_id"
        assert task["task_id"] == "task_123", "Should find correct task"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_sort_tasks_by_priority(self):
        """Test that TaskManagementHandler sorts tasks by priority."""
        handler = TaskManagementHandler()
        tasks = [
            {"title": "Low Priority", "priority": "low", "due_date": "2024-12-20"},
            {"title": "High Priority", "priority": "high", "due_date": "2024-12-25"},
            {
                "title": "Medium Priority",
                "priority": "medium",
                "due_date": "2024-12-22",
            },
        ]

        sorted_tasks = handler._handle_list_tasks__sort_tasks(tasks)
        assert (
            sorted_tasks[0]["priority"] == "high"
        ), "High priority tasks should come first"
        assert (
            sorted_tasks[1]["priority"] == "medium"
        ), "Medium priority tasks should come second"
        assert (
            sorted_tasks[2]["priority"] == "low"
        ), "Low priority tasks should come last"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_format_due_date_overdue(self):
        """Test that TaskManagementHandler formats overdue dates correctly."""
        handler = TaskManagementHandler()

        # Deterministic "now" for production-behavior-sensitive due date formatting.
        test_now_dt = datetime(2026, 1, 20, 12, 0, 0)
        with (
            patch(
                "core.time_utilities.now_datetime_full",
                return_value=test_now_dt,
            ),
            patch(
                "communication.command_handlers.task_handler.now_datetime_full",
                return_value=test_now_dt,
                create=True,
            ),
        ):
            yesterday = format_timestamp((test_now_dt - timedelta(days=1)), DATE_ONLY)
            result = handler._handle_list_tasks__format_due_date(yesterday)

        assert "OVERDUE" in result.upper(), "Should indicate overdue date"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_format_due_date_today(self):
        """Test that TaskManagementHandler formats today's dates correctly."""
        handler = TaskManagementHandler()

        # Deterministic "now" for production-behavior-sensitive due date formatting.
        test_now_dt = datetime(2026, 1, 20, 12, 0, 0)
        with (
            patch(
                "core.time_utilities.now_datetime_full",
                return_value=test_now_dt,
            ),
            patch(
                "communication.command_handlers.task_handler.now_datetime_full",
                return_value=test_now_dt,
                create=True,
            ),
        ):
            today = format_timestamp(test_now_dt, DATE_ONLY)
            result = handler._handle_list_tasks__format_due_date(today)

        assert "TODAY" in result.upper(), "Should indicate today's date"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_handler_format_due_date_future(self):
        """Test that TaskManagementHandler formats future dates correctly."""
        handler = TaskManagementHandler()

        # Deterministic "now" for production-behavior-sensitive due date formatting.
        test_now_dt = datetime(2026, 1, 20, 12, 0, 0)
        with (
            patch(
                "core.time_utilities.now_datetime_full",
                return_value=test_now_dt,
            ),
            patch(
                "communication.command_handlers.task_handler.now_datetime_full",
                return_value=test_now_dt,
                create=True,
            ),
        ):
            tomorrow = format_timestamp((test_now_dt + timedelta(days=1)), DATE_ONLY)
            result = handler._handle_list_tasks__format_due_date(tomorrow)

        assert "due" in result.lower(), "Should indicate future date"
        assert tomorrow in result, "Should include the date"
