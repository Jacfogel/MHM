"""
Checkin Handler Behavior Tests

Tests for communication/command_handlers/checkin_handler.py focusing on real behavior and side effects.
These tests verify that the checkin handler actually works and produces expected
side effects rather than just returning values.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date, datetime

# Import the modules we're testing
from communication.command_handlers.checkin_handler import CheckinHandler
from communication.command_handlers.shared_types import (
    InteractionResponse,
    ParsedCommand,
)
from tests.test_utilities import TestUserFactory
from core.time_utilities import DATE_ONLY, format_timestamp


class TestCheckinHandlerBehavior:
    """Test checkin handler real behavior and side effects."""

    def _create_test_user(
        self, user_id: str, enable_checkins: bool = True, test_data_dir: str = None
    ) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(
            user_id, enable_checkins=enable_checkins, test_data_dir=test_data_dir
        )

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.checkins
    def test_checkin_handler_can_handle_intents(self):
        """Test that CheckinHandler can handle all expected intents."""
        handler = CheckinHandler()

        expected_intents = ["start_checkin", "continue_checkin", "checkin_status"]
        for intent in expected_intents:
            assert handler.can_handle(intent), f"CheckinHandler should handle {intent}"

        # Test that it doesn't handle other intents
        assert not handler.can_handle(
            "create_task"
        ), "CheckinHandler should not handle create_task"
        assert not handler.can_handle(
            "show_schedule"
        ), "CheckinHandler should not handle show_schedule"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.checkins
    def test_checkin_handler_get_help(self):
        """Test that CheckinHandler returns help text."""
        handler = CheckinHandler()
        help_text = handler.get_help()

        assert isinstance(help_text, str), "Should return help text as string"
        assert len(help_text) > 0, "Help text should not be empty"
        assert "check" in help_text.lower(), "Help text should mention check-in"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.checkins
    def test_checkin_handler_get_examples(self):
        """Test that CheckinHandler returns example commands."""
        handler = CheckinHandler()
        examples = handler.get_examples()

        assert isinstance(examples, list), "Should return examples as list"
        assert len(examples) > 0, "Should have at least one example"
        for example in examples:
            assert isinstance(example, str), "Each example should be a string"
            assert len(example) > 0, "Each example should not be empty"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.checkins
    def test_checkin_handler_unknown_intent(self):
        """Test that CheckinHandler handles unknown intents gracefully."""
        handler = CheckinHandler()
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
    @pytest.mark.checkins
    @pytest.mark.file_io
    @patch("communication.command_handlers.checkin_handler.is_user_checkins_enabled")
    def test_checkin_handler_start_checkin_not_enabled(
        self, mock_is_enabled, test_data_dir
    ):
        """Test that CheckinHandler rejects check-in when not enabled."""
        handler = CheckinHandler()
        user_id = "test_user_checkin_not_enabled"
        assert self._create_test_user(
            user_id, enable_checkins=False, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Mock check-ins disabled
        mock_is_enabled.return_value = False

        parsed_command = ParsedCommand(
            intent="start_checkin",
            entities={},
            confidence=0.9,
            original_message="start checkin",
        )

        # Handle the command
        response = handler.handle(user_id, parsed_command)

        # Verify response
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert (
            "not enabled" in response.message.lower()
        ), "Should indicate check-ins are not enabled"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.checkins
    @pytest.mark.file_io
    @pytest.mark.no_parallel
    @patch(
        "communication.message_processing.conversation_flow_manager.conversation_manager.start_checkin"
    )
    @patch("communication.command_handlers.checkin_handler.get_recent_checkins")
    @patch("communication.command_handlers.checkin_handler.is_user_checkins_enabled")
    def test_checkin_handler_start_checkin_success(
        self, mock_is_enabled, mock_get_recent, mock_start_checkin, test_data_dir
    ):
        """Test that CheckinHandler starts check-in successfully."""
        handler = CheckinHandler()
        user_id = "test_user_checkin_start"
        assert self._create_test_user(
            user_id, enable_checkins=True, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Mock check-ins enabled
        mock_is_enabled.return_value = True

        # Mock no recent check-ins today
        mock_get_recent.return_value = []

        # Mock conversation manager starting check-in
        mock_start_checkin.return_value = (
            "Let's start your check-in. How are you feeling today?",
            False,
        )

        parsed_command = ParsedCommand(
            intent="start_checkin",
            entities={},
            confidence=0.9,
            original_message="start checkin",
        )

        # Handle the command
        response = handler.handle(user_id, parsed_command)

        # Verify response
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert not response.completed, "Check-in should not be completed yet"
        assert (
            "check-in" in response.message.lower()
            or "feeling" in response.message.lower()
        ), "Should indicate check-in started"
        mock_start_checkin.assert_called_once_with(user_id)

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.checkins
    @pytest.mark.file_io
    @patch("communication.command_handlers.checkin_handler.get_recent_checkins")
    @patch("communication.command_handlers.checkin_handler.is_user_checkins_enabled")
    def test_checkin_handler_start_checkin_already_done_today(
        self, mock_is_enabled, mock_get_recent, test_data_dir
    ):
        """Test that CheckinHandler prevents duplicate check-ins today."""
        handler = CheckinHandler()
        user_id = "test_user_checkin_duplicate"
        assert self._create_test_user(
            user_id, enable_checkins=True, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Mock check-ins enabled
        mock_is_enabled.return_value = True

        # Mock check-in already done today
        today_date = date.today()
        today_dt = datetime.combine(today_date, datetime.min.time())
        today_str = format_timestamp(today_dt, DATE_ONLY)

        mock_get_recent.return_value = [
            {"timestamp": f"{today_str} 10:00:00", "date": today_str, "mood": 4}
        ]

        parsed_command = ParsedCommand(
            intent="start_checkin",
            entities={},
            confidence=0.9,
            original_message="start checkin",
        )

        # Handle the command
        response = handler.handle(user_id, parsed_command)

        # Verify response
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert (
            "already" in response.message.lower() or "today" in response.message.lower()
        ), "Should indicate check-in already done"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.checkins
    @pytest.mark.file_io
    @patch(
        "communication.message_processing.conversation_flow_manager.conversation_manager.start_checkin"
    )
    @patch("communication.command_handlers.checkin_handler.get_recent_checkins")
    @patch("communication.command_handlers.checkin_handler.is_user_checkins_enabled")
    def test_checkin_handler_start_checkin_conversation_manager_error(
        self, mock_is_enabled, mock_get_recent, mock_start_checkin, test_data_dir
    ):
        """Test that CheckinHandler handles conversation manager errors gracefully."""
        handler = CheckinHandler()
        user_id = "test_user_checkin_error"
        assert self._create_test_user(
            user_id, enable_checkins=True, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Mock check-ins enabled
        mock_is_enabled.return_value = True

        # Mock no recent check-ins
        mock_get_recent.return_value = []

        # Mock conversation manager raising exception
        mock_start_checkin.side_effect = Exception("Database connection error")

        parsed_command = ParsedCommand(
            intent="start_checkin",
            entities={},
            confidence=0.9,
            original_message="start checkin",
        )

        # Handle the command
        response = handler.handle(user_id, parsed_command)

        # Verify response
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert (
            "trouble" in response.message.lower()
            or "try again" in response.message.lower()
        ), "Should indicate error"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.checkins
    @pytest.mark.file_io
    def test_checkin_handler_continue_checkin(self, test_data_dir):
        """Test that CheckinHandler handles continue check-in."""
        handler = CheckinHandler()
        user_id = "test_user_checkin_continue"
        assert self._create_test_user(
            user_id, enable_checkins=True, test_data_dir=test_data_dir
        ), "Failed to create test user"

        parsed_command = ParsedCommand(
            intent="continue_checkin",
            entities={"response": "feeling good"},
            confidence=0.9,
            original_message="continue checkin",
        )

        # Handle the command
        response = handler.handle(user_id, parsed_command)

        # Verify response
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert (
            "not yet implemented" in response.message.lower()
            or "use" in response.message.lower()
        ), "Should indicate not implemented"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.checkins
    @pytest.mark.file_io
    @patch("communication.command_handlers.checkin_handler.get_recent_checkins")
    @patch("communication.command_handlers.checkin_handler.is_user_checkins_enabled")
    def test_checkin_handler_checkin_status_not_enabled(
        self, mock_is_enabled, mock_get_recent, test_data_dir
    ):
        """Test that CheckinHandler shows status when check-ins not enabled."""
        handler = CheckinHandler()
        user_id = "test_user_checkin_status_not_enabled"
        assert self._create_test_user(
            user_id, enable_checkins=False, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Mock check-ins disabled
        mock_is_enabled.return_value = False

        parsed_command = ParsedCommand(
            intent="checkin_status",
            entities={},
            confidence=0.9,
            original_message="checkin status",
        )

        # Handle the command
        response = handler.handle(user_id, parsed_command)

        # Verify response
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert (
            "not enabled" in response.message.lower()
        ), "Should indicate check-ins are not enabled"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.checkins
    @pytest.mark.file_io
    @patch("communication.command_handlers.checkin_handler.get_recent_checkins")
    @patch("communication.command_handlers.checkin_handler.is_user_checkins_enabled")
    def test_checkin_handler_checkin_status_no_checkins(
        self, mock_is_enabled, mock_get_recent, test_data_dir
    ):
        """Test that CheckinHandler shows status when no check-ins exist."""
        handler = CheckinHandler()
        user_id = "test_user_checkin_status_none"
        assert self._create_test_user(
            user_id, enable_checkins=True, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Mock check-ins enabled
        mock_is_enabled.return_value = True

        # Mock no recent check-ins
        mock_get_recent.return_value = []

        parsed_command = ParsedCommand(
            intent="checkin_status",
            entities={},
            confidence=0.9,
            original_message="checkin status",
        )

        # Handle the command
        response = handler.handle(user_id, parsed_command)

        # Verify response
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert (
            "no check-ins" in response.message.lower()
            or "recorded" in response.message.lower()
        ), "Should indicate no check-ins"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.checkins
    @pytest.mark.file_io
    @patch("communication.command_handlers.checkin_handler.get_recent_checkins")
    @patch("communication.command_handlers.checkin_handler.is_user_checkins_enabled")
    def test_checkin_handler_checkin_status_with_checkins(
        self, mock_is_enabled, mock_get_recent, test_data_dir
    ):
        """Test that CheckinHandler shows status with recent check-ins."""
        handler = CheckinHandler()
        user_id = "test_user_checkin_status_with_data"
        assert self._create_test_user(
            user_id, enable_checkins=True, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Mock check-ins enabled
        mock_is_enabled.return_value = True

        # Mock recent check-ins
        today_date = date.today()
        today_dt = datetime.combine(today_date, datetime.min.time())
        today_str = format_timestamp(today_dt, DATE_ONLY)

        yesterday_date = today_date - date.resolution
        yesterday_dt = datetime.combine(yesterday_date, datetime.min.time())
        yesterday_str = format_timestamp(yesterday_dt, DATE_ONLY)

        two_days_ago_date = today_date - (date.resolution * 2)
        two_days_ago_dt = datetime.combine(two_days_ago_date, datetime.min.time())
        two_days_ago_str = format_timestamp(two_days_ago_dt, DATE_ONLY)

        mock_get_recent.return_value = [
            {"date": today_str, "mood": 4, "timestamp": f"{today_str} 10:00:00"},
            {
                "date": yesterday_str,
                "mood": 3,
                "timestamp": f"{yesterday_str} 14:00:00",
            },
            {
                "date": two_days_ago_str,
                "mood": 5,
                "timestamp": f"{two_days_ago_str} 09:00:00",
            },
        ]

        parsed_command = ParsedCommand(
            intent="checkin_status",
            entities={},
            confidence=0.9,
            original_message="checkin status",
        )

        # Handle the command
        response = handler.handle(user_id, parsed_command)

        # Verify response
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert (
            "check-in" in response.message.lower()
            or "recent" in response.message.lower()
        ), "Should show check-in status"
        assert (
            today_str in response.message or "mood" in response.message.lower()
        ), "Should include check-in data"

        parsed_command = ParsedCommand(
            intent="checkin_status",
            entities={},
            confidence=0.9,
            original_message="checkin status",
        )

        # Handle the command
        response = handler.handle(user_id, parsed_command)

        # Verify response
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert (
            "check-in" in response.message.lower()
            or "recent" in response.message.lower()
        ), "Should show check-in status"
        assert (
            today_str in response.message or "mood" in response.message.lower()
        ), "Should include check-in data"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.checkins
    @pytest.mark.file_io
    @patch("communication.command_handlers.checkin_handler.get_recent_checkins")
    @patch("communication.command_handlers.checkin_handler.is_user_checkins_enabled")
    def test_checkin_handler_checkin_status_many_checkins(
        self, mock_is_enabled, mock_get_recent, test_data_dir
    ):
        """Test that CheckinHandler shows status with many check-ins (truncates to 5)."""
        handler = CheckinHandler()
        user_id = "test_user_checkin_status_many"
        assert self._create_test_user(
            user_id, enable_checkins=True, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Mock check-ins enabled
        mock_is_enabled.return_value = True

        # Mock many recent check-ins (more than 5)
        today_date = date.today()
        mock_get_recent.return_value = [
            {
                "date": format_timestamp(
                    datetime.combine(
                        today_date - (date.resolution * i), datetime.min.time()
                    ),
                    DATE_ONLY,
                ),
                "mood": i % 5 + 1,
                "timestamp": (
                    f"{format_timestamp(datetime.combine(today_date - (date.resolution * i), datetime.min.time()), DATE_ONLY)} 10:00:00"
                ),
            }
            for i in range(7)
        ]

        parsed_command = ParsedCommand(
            intent="checkin_status",
            entities={},
            confidence=0.9,
            original_message="checkin status",
        )

        # Handle the command
        response = handler.handle(user_id, parsed_command)

        # Verify response
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert (
            "more" in response.message.lower() or "and" in response.message.lower()
        ), "Should indicate more check-ins exist"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.checkins
    @pytest.mark.file_io
    @patch("communication.command_handlers.checkin_handler.get_recent_checkins")
    @patch("communication.command_handlers.checkin_handler.is_user_checkins_enabled")
    def test_checkin_handler_start_checkin_with_old_checkin(
        self, mock_is_enabled, mock_get_recent, test_data_dir
    ):
        """Test that CheckinHandler allows check-in when last check-in was yesterday."""
        handler = CheckinHandler()
        user_id = "test_user_checkin_old_allowed"
        assert self._create_test_user(
            user_id, enable_checkins=True, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Mock check-ins enabled
        mock_is_enabled.return_value = True

        # Mock check-in from yesterday (not today)
        yesterday_date = date.today() - date.resolution
        yesterday_dt = datetime.combine(yesterday_date, datetime.min.time())
        yesterday_str = format_timestamp(yesterday_dt, DATE_ONLY)

        mock_get_recent.return_value = [
            {"timestamp": f"{yesterday_str} 10:00:00", "date": yesterday_str, "mood": 4}
        ]

        # Mock conversation manager starting check-in
        with patch(
            "communication.message_processing.conversation_flow_manager.conversation_manager.start_checkin"
        ) as mock_start_checkin:
            mock_start_checkin.return_value = (
                "Let's start your check-in. How are you feeling today?",
                False,
            )

            parsed_command = ParsedCommand(
                intent="start_checkin",
                entities={},
                confidence=0.9,
                original_message="start checkin",
            )

            # Handle the command
            response = handler.handle(user_id, parsed_command)

            # Verify response - should allow check-in since yesterday's check-in doesn't count
            assert isinstance(
                response, InteractionResponse
            ), "Should return InteractionResponse"
            # Should proceed to start check-in (not blocked by yesterday's check-in)
            mock_start_checkin.assert_called_once_with(user_id)
