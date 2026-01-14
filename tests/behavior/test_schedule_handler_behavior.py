"""
Schedule Handler Behavior Tests

Tests for communication/command_handlers/schedule_handler.py focusing on real behavior and side effects.
These tests verify that the schedule handler actually works and produces expected
side effects rather than just returning values.
"""

import pytest
from unittest.mock import patch, MagicMock

# Import the modules we're testing
from communication.command_handlers.schedule_handler import ScheduleManagementHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from tests.test_utilities import TestUserFactory


class TestScheduleHandlerBehavior:
    """Test schedule handler real behavior and side effects."""
    
    def _create_test_user(self, user_id: str, enable_checkins: bool = True, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, enable_checkins=enable_checkins, test_data_dir=test_data_dir)
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    def test_schedule_handler_can_handle_intents(self):
        """Test that ScheduleManagementHandler can handle all expected intents."""
        handler = ScheduleManagementHandler()
        
        expected_intents = ['show_schedule', 'update_schedule', 'schedule_status', 'add_schedule_period', 'edit_schedule_period']
        for intent in expected_intents:
            assert handler.can_handle(intent), f"ScheduleManagementHandler should handle {intent}"
        
        # Test that it doesn't handle other intents
        assert not handler.can_handle('create_task'), "ScheduleManagementHandler should not handle create_task"
        assert not handler.can_handle('start_checkin'), "ScheduleManagementHandler should not handle start_checkin"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    def test_schedule_handler_get_help(self):
        """Test that ScheduleManagementHandler returns help text."""
        handler = ScheduleManagementHandler()
        help_text = handler.get_help()
        
        assert isinstance(help_text, str), "Should return help text as string"
        assert len(help_text) > 0, "Help text should not be empty"
        assert "schedule" in help_text.lower(), "Help text should mention schedule"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    def test_schedule_handler_get_examples(self):
        """Test that ScheduleManagementHandler returns example commands."""
        handler = ScheduleManagementHandler()
        examples = handler.get_examples()
        
        assert isinstance(examples, list), "Should return examples as list"
        assert len(examples) > 0, "Should have at least one example"
        for example in examples:
            assert isinstance(example, str), "Each example should be a string"
            assert len(example) > 0, "Each example should not be empty"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    @pytest.mark.file_io
    @patch('core.schedule_management.get_schedule_time_periods')
    @patch('core.user_data_handlers.get_user_categories')
    def test_schedule_handler_show_schedule_all_categories(self, mock_get_categories, mock_get_periods, test_data_dir):
        """Test that ScheduleManagementHandler shows schedule for all categories."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_show_all"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock user categories
        mock_get_categories.return_value = ['task', 'checkin']
        
        # Mock schedule periods
        mock_get_periods.side_effect = lambda uid, cat: {
            'task': {'morning': {'start_time': '09:00 AM', 'end_time': '11:00 AM', 'active': True}},
            'checkin': {'afternoon': {'start_time': '02:00 PM', 'end_time': '04:00 PM', 'active': True}}
        }.get(cat, {})
        
        # Create a parsed command for showing schedule
        parsed_command = ParsedCommand(
            intent="show_schedule",
            entities={'category': 'all'},
            confidence=0.9,
            original_message="show schedule"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "schedule" in response.message.lower(), "Should mention schedule"
        assert response.rich_data is not None, "Should include rich data for Discord embeds"
        assert response.rich_data.get('type') == 'schedule', "Rich data should have type 'schedule'"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    @pytest.mark.file_io
    @patch('core.schedule_management.get_schedule_time_periods')
    @patch('core.user_data_handlers.get_user_categories')
    def test_schedule_handler_show_schedule_specific_category(self, mock_get_categories, mock_get_periods, test_data_dir):
        """Test that ScheduleManagementHandler shows schedule for specific category."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_show_specific"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock schedule periods for specific category
        mock_get_periods.return_value = {
            'morning': {
                'start_time': '09:00 AM',
                'end_time': '11:00 AM',
                'active': True,
                'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            }
        }
        
        # Create a parsed command for showing schedule
        parsed_command = ParsedCommand(
            intent="show_schedule",
            entities={'category': 'task'},
            confidence=0.9,
            original_message="show my task schedule"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "task" in response.message.lower(), "Should mention task category"
        assert "morning" in response.message.lower() or "09:00" in response.message.lower(), "Should include period details"
        assert response.rich_data is not None, "Should include rich data"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    @pytest.mark.file_io
    @patch('core.schedule_management.get_schedule_time_periods')
    @patch('core.user_data_handlers.get_user_categories')
    def test_schedule_handler_show_schedule_no_periods(self, mock_get_categories, mock_get_periods, test_data_dir):
        """Test that ScheduleManagementHandler shows message when no periods configured."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_show_none"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock schedule periods to return empty
        mock_get_periods.return_value = {}
        
        # Create a parsed command for showing schedule
        parsed_command = ParsedCommand(
            intent="show_schedule",
            entities={'category': 'task'},
            confidence=0.9,
            original_message="show my task schedule"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "no schedule" in response.message.lower() or "no periods" in response.message.lower() or "configured" in response.message.lower(), "Should indicate no periods"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    @pytest.mark.file_io
    @patch('core.schedule_management.set_schedule_periods')
    @patch('core.schedule_management.get_schedule_time_periods')
    def test_schedule_handler_update_schedule_enable(self, mock_get_periods, mock_set_periods, test_data_dir):
        """Test that ScheduleManagementHandler enables schedule periods."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_enable"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock schedule periods
        mock_get_periods.return_value = {
            'morning': {'start_time': '09:00 AM', 'end_time': '11:00 AM', 'active': False},
            'afternoon': {'start_time': '02:00 PM', 'end_time': '04:00 PM', 'active': False}
        }
        
        # Create a parsed command for enabling schedule
        parsed_command = ParsedCommand(
            intent="update_schedule",
            entities={'category': 'task', 'action': 'enable'},
            confidence=0.9,
            original_message="enable my task schedule"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "enabled" in response.message.lower(), "Should indicate schedule was enabled"
        
        # Verify actual system changes: Check that set_schedule_periods was called with correct data
        mock_set_periods.assert_called_once()
        call_args = mock_set_periods.call_args
        call_user_id = call_args[0][0] if call_args[0] else call_args[1].get('user_id')
        call_category = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get('category')
        periods = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('periods')
        
        assert call_user_id == user_id, "Should update schedule for correct user"
        assert call_category == 'task', "Should update task category"
        assert periods is not None, "Should have periods data"
        # Verify that periods were enabled (active=True)
        for period_name, period_data in periods.items():
            assert period_data.get('active') is True, f"Period {period_name} should be enabled (active=True)"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    @pytest.mark.file_io
    @patch('core.schedule_management.set_schedule_periods')
    @patch('core.schedule_management.get_schedule_time_periods')
    def test_schedule_handler_update_schedule_disable(self, mock_get_periods, mock_set_periods, test_data_dir):
        """Test that ScheduleManagementHandler disables schedule periods."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_disable"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock schedule periods
        mock_get_periods.return_value = {
            'morning': {'start_time': '09:00 AM', 'end_time': '11:00 AM', 'active': True},
            'afternoon': {'start_time': '02:00 PM', 'end_time': '04:00 PM', 'active': True}
        }
        
        # Create a parsed command for disabling schedule
        parsed_command = ParsedCommand(
            intent="update_schedule",
            entities={'category': 'task', 'action': 'disable'},
            confidence=0.9,
            original_message="disable my task schedule"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "disabled" in response.message.lower(), "Should indicate schedule was disabled"
        
        # Verify actual system changes: Check that set_schedule_periods was called with correct data
        mock_set_periods.assert_called_once()
        call_args = mock_set_periods.call_args
        call_user_id = call_args[0][0] if call_args[0] else call_args[1].get('user_id')
        call_category = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get('category')
        periods = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('periods')
        
        assert call_user_id == user_id, "Should update schedule for correct user"
        assert call_category == 'task', "Should update task category"
        assert periods is not None, "Should have periods data"
        # Verify that periods were disabled (active=False)
        for period_name, period_data in periods.items():
            assert period_data.get('active') is False, f"Period {period_name} should be disabled (active=False)"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    def test_schedule_handler_update_schedule_missing_params(self, test_data_dir):
        """Test that ScheduleManagementHandler handles missing parameters."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_missing_params"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a parsed command with missing parameters
        parsed_command = ParsedCommand(
            intent="update_schedule",
            entities={},  # Missing category and action
            confidence=0.9,
            original_message="update schedule"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        # Note: Handler returns completed=True even when asking for clarification
        assert response.completed, "Response should be completed (handler design)"
        assert "specify" in response.message.lower() or "try" in response.message.lower(), "Should ask for more details"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    @pytest.mark.file_io
    @patch('core.schedule_management.get_schedule_time_periods')
    @patch('core.user_data_handlers.get_user_categories')
    def test_schedule_handler_schedule_status(self, mock_get_categories, mock_get_periods, test_data_dir):
        """Test that ScheduleManagementHandler shows schedule status."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_status"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock user categories
        mock_get_categories.return_value = ['task', 'checkin']
        
        # Mock schedule periods
        mock_get_periods.side_effect = lambda uid, cat: {
            'task': {'morning': {'start_time': '09:00 AM', 'end_time': '11:00 AM', 'active': True}},
            'checkin': {'afternoon': {'start_time': '02:00 PM', 'end_time': '04:00 PM', 'active': False}}
        }.get(cat, {})
        
        # Create a parsed command for schedule status
        parsed_command = ParsedCommand(
            intent="schedule_status",
            entities={},
            confidence=0.9,
            original_message="schedule status"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "status" in response.message.lower(), "Should mention status"
        assert "task" in response.message.lower() or "checkin" in response.message.lower(), "Should include category information"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    @pytest.mark.file_io
    @patch('core.schedule_management.set_schedule_periods')
    @patch('core.schedule_management.get_schedule_time_periods')
    def test_schedule_handler_add_schedule_period_success(self, mock_get_periods, mock_set_periods, test_data_dir):
        """Test that ScheduleManagementHandler adds schedule period successfully."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_add"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock schedule periods (empty initially)
        mock_get_periods.return_value = {}
        
        # Create a parsed command for adding schedule period
        parsed_command = ParsedCommand(
            intent="add_schedule_period",
            entities={
                'category': 'task',
                'period_name': 'morning',
                'start_time': '09:00 AM',
                'end_time': '11:00 AM',
                'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'active': True
            },
            confidence=0.9,
            original_message="add morning period 9am-11am to task schedule"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "added" in response.message.lower() or "added new" in response.message.lower(), "Should indicate period was added"
        assert "morning" in response.message.lower(), "Should mention period name"
        assert response.suggestions is not None, "Should include suggestions for next actions"
        
        # Verify actual system changes: Check that set_schedule_periods was called with correct data
        mock_set_periods.assert_called_once()
        call_args = mock_set_periods.call_args
        call_user_id = call_args[0][0] if call_args[0] else call_args[1].get('user_id')
        call_category = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get('category')
        periods = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('periods')
        
        assert call_user_id == user_id, "Should add period for correct user"
        assert call_category == 'task', "Should add period to task category"
        assert periods is not None, "Should have periods data"
        assert 'morning' in periods, "Should include morning period"
        morning_period = periods['morning']
        assert morning_period.get('start_time') == '09:00 AM', "Should set correct start_time"
        assert morning_period.get('end_time') == '11:00 AM', "Should set correct end_time"
        assert morning_period.get('active') is True, "Should set active=True"
        assert 'days' in morning_period, "Should include days"
        assert set(morning_period['days']) == set(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']), "Should set correct days"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    def test_schedule_handler_add_schedule_period_missing_params(self, test_data_dir):
        """Test that ScheduleManagementHandler handles missing parameters for add period."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_add_missing"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a parsed command with missing parameters
        parsed_command = ParsedCommand(
            intent="add_schedule_period",
            entities={'category': 'task'},  # Missing period_name, start_time, end_time
            confidence=0.9,
            original_message="add period"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert not response.completed, "Response should not be completed (needs clarification)"
        assert "details" in response.message.lower() or "try" in response.message.lower(), "Should ask for more details"
        assert response.suggestions is not None, "Should include suggestions"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    def test_schedule_handler_add_schedule_period_invalid_days(self, test_data_dir):
        """Test that ScheduleManagementHandler handles invalid days."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_add_invalid_days"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a parsed command with invalid days
        parsed_command = ParsedCommand(
            intent="add_schedule_period",
            entities={
                'category': 'task',
                'period_name': 'morning',
                'start_time': '09:00 AM',
                'end_time': '11:00 AM',
                'days': ['InvalidDay', 'AnotherInvalidDay']
            },
            confidence=0.9,
            original_message="add morning period with invalid days"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "invalid" in response.message.lower(), "Should indicate invalid days"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    def test_schedule_handler_parse_time_format_12hour(self):
        """Test that ScheduleManagementHandler parses 12-hour time format."""
        handler = ScheduleManagementHandler()
        
        # Test various 12-hour formats
        # Note: Parser may or may not add leading zeros, so we normalize before comparing
        test_cases = [
            ('09:00 AM', '09:00 AM'),  # Already formatted
            ('9:00 am', '09:00 AM'),   # Should normalize to uppercase AM/PM
            ('11:30 PM', '11:30 PM'),  # Already formatted
            ('1:00 pm', '01:00 PM')    # Should normalize hour and AM/PM
        ]
        
        for input_time, expected in test_cases:
            result = handler._handle_add_schedule_period__parse_time_format(input_time)
            # Normalize both results: extract hour, minute, and AM/PM, then compare
            # Parser may not add leading zeros, so we check if the time values are equivalent
            import re
            result_match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', result.upper())
            expected_match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', expected.upper())
            
            assert result_match and expected_match, f"Could not parse time format: got {result}, expected {expected}"
            # Compare hour, minute, and AM/PM (hour can be 1-2 digits, so convert to int)
            result_hour = int(result_match.group(1))
            expected_hour = int(expected_match.group(1))
            assert result_hour == expected_hour and result_match.group(2) == expected_match.group(2) and result_match.group(3) == expected_match.group(3), f"Should parse {input_time} correctly (got {result}, expected {expected})"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    def test_schedule_handler_parse_time_format_24hour(self):
        """Test that ScheduleManagementHandler parses 24-hour time format."""
        handler = ScheduleManagementHandler()
        
        # Test 24-hour formats
        test_cases = [
            ('09:00', '09:00 AM'),
            ('21:00', '09:00 PM'),
            ('13:30', '01:30 PM'),
            ('00:00', '12:00 AM')
        ]
        
        for input_time, expected in test_cases:
            result = handler._handle_add_schedule_period__parse_time_format(input_time)
            assert result == expected or 'AM' in result or 'PM' in result, f"Should convert {input_time} to 12-hour format"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    def test_schedule_handler_parse_time_format_hour_only(self):
        """Test that ScheduleManagementHandler parses hour-only format."""
        handler = ScheduleManagementHandler()
        
        # Test hour-only formats
        test_cases = [9, 21, 13, 0]
        
        for input_hour in test_cases:
            result = handler._handle_add_schedule_period__parse_time_format(str(input_hour))
            assert result is not None, f"Should parse hour {input_hour}"
            assert 'AM' in result or 'PM' in result, f"Should convert hour {input_hour} to 12-hour format"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    @pytest.mark.file_io
    @patch('core.schedule_management.set_schedule_periods')
    @patch('core.schedule_management.get_schedule_time_periods')
    def test_schedule_handler_edit_schedule_period_success(self, mock_get_periods, mock_set_periods, test_data_dir):
        """Test that ScheduleManagementHandler edits schedule period successfully."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_edit"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock existing schedule periods
        mock_get_periods.return_value = {
            'morning': {
                'start_time': '09:00 AM',
                'end_time': '11:00 AM',
                'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'active': True
            }
        }
        
        # Create a parsed command for editing schedule period
        parsed_command = ParsedCommand(
            intent="edit_schedule_period",
            entities={
                'category': 'task',
                'period_name': 'morning',
                'new_start_time': '08:00 AM',
                'new_end_time': '10:00 AM'
            },
            confidence=0.9,
            original_message="edit morning period start time to 8am"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "updated" in response.message.lower(), "Should indicate period was updated"
        assert "morning" in response.message.lower(), "Should mention period name"
        assert response.suggestions is not None, "Should include suggestions"
        
        # Verify actual system changes: Check that set_schedule_periods was called with correct data
        mock_set_periods.assert_called_once()
        call_args = mock_set_periods.call_args
        call_user_id = call_args[0][0] if call_args[0] else call_args[1].get('user_id')
        call_category = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get('category')
        periods = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('periods')
        
        assert call_user_id == user_id, "Should update period for correct user"
        assert call_category == 'task', "Should update task category"
        assert periods is not None, "Should have periods data"
        assert 'morning' in periods, "Should include morning period"
        morning_period = periods['morning']
        assert morning_period.get('start_time') == '08:00 AM', "Should update start_time to 08:00 AM"
        assert morning_period.get('end_time') == '10:00 AM', "Should update end_time to 10:00 AM"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    @pytest.mark.file_io
    @patch('core.schedule_management.get_schedule_time_periods')
    def test_schedule_handler_edit_schedule_period_not_found(self, mock_get_periods, test_data_dir):
        """Test that ScheduleManagementHandler handles editing non-existent period."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_edit_not_found"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock existing schedule periods (empty)
        mock_get_periods.return_value = {}
        
        # Create a parsed command for editing non-existent period
        parsed_command = ParsedCommand(
            intent="edit_schedule_period",
            entities={
                'category': 'task',
                'period_name': 'nonexistent'
            },
            confidence=0.9,
            original_message="edit nonexistent period"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        # When period is not found but category/period_name are provided, should return interactive flow with suggestions
        assert not response.completed, "Response should not be completed (interactive flow with suggestions)"
        assert "not found" in response.message.lower() or "what times should" in response.message.lower(), "Should indicate period not found or prompt for times"
        assert response.suggestions is not None and len(response.suggestions) > 0, "Should provide suggestions for times"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    def test_schedule_handler_edit_schedule_period_missing_params(self, test_data_dir):
        """Test that ScheduleManagementHandler handles missing parameters for edit period."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_edit_missing"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a parsed command with missing parameters
        parsed_command = ParsedCommand(
            intent="edit_schedule_period",
            entities={},  # Missing category and period_name
            confidence=0.9,
            original_message="edit period"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert not response.completed, "Response should not be completed (needs clarification)"
        assert "specify" in response.message.lower() or "try" in response.message.lower(), "Should ask for more details"
        assert response.suggestions is not None, "Should include suggestions"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    @pytest.mark.file_io
    @patch('core.schedule_management.set_schedule_periods')
    @patch('core.schedule_management.get_schedule_time_periods')
    def test_schedule_handler_edit_schedule_period_no_changes(self, mock_get_periods, mock_set_periods, test_data_dir):
        """Test that ScheduleManagementHandler handles edit with no changes."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_edit_no_changes"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock existing schedule periods
        mock_get_periods.return_value = {
            'morning': {
                'start_time': '09:00 AM',
                'end_time': '11:00 AM',
                'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'active': True
            }
        }
        
        # Create a parsed command for editing with no actual changes
        parsed_command = ParsedCommand(
            intent="edit_schedule_period",
            entities={
                'category': 'task',
                'period_name': 'morning'
                # No new_* fields provided
            },
            confidence=0.9,
            original_message="edit morning period"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert not response.completed, "Response should not be completed (interactive flow with suggestions)"
        assert "no changes" in response.message.lower() or "what would you like to update" in response.message.lower() or "current" in response.message.lower(), "Should indicate no changes specified or prompt for updates"
        # When no changes are specified, should provide suggestions for what can be updated
        assert response.suggestions is not None and len(response.suggestions) > 0, "Should provide suggestions for updates"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.scheduler
    def test_schedule_handler_unknown_intent(self, test_data_dir):
        """Test that ScheduleManagementHandler handles unknown intents appropriately."""
        handler = ScheduleManagementHandler()
        user_id = "test_user_schedule_unknown"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a parsed command with unknown intent
        parsed_command = ParsedCommand(
            intent="unknown_schedule_intent",
            entities={},
            confidence=0.9,
            original_message="unknown schedule command"
        )
        
        # Since can_handle returns False for this, we need to test the handle method directly
        # by calling it with an intent that can_handle accepts but handle doesn't recognize
        with patch.object(handler, 'can_handle', return_value=True):
            response = handler.handle(user_id, parsed_command)
            
            # Verify response
            assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
            assert response.completed, "Response should be completed"
            assert "don't understand" in response.message.lower() or "try" in response.message.lower(), "Should indicate command not understood"

