"""
Interaction Handlers Behavior Tests

Tests for bot/interaction_handlers.py focusing on real behavior and side effects.
These tests verify that the interaction handlers actually work and produce expected
side effects rather than just returning values.
"""

import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta

# Import the modules we're testing
from communication.command_handlers.interaction_handlers import (
    TaskManagementHandler, CheckinHandler, ProfileHandler,
    ScheduleManagementHandler, AnalyticsHandler, HelpHandler,
    get_interaction_handler, get_all_handlers
)
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from core.user_data_handlers import get_user_data, save_user_data
from tasks.task_management import create_task, load_active_tasks, complete_task, delete_task
from tests.test_utilities import TestUserFactory, create_test_user


class TestInteractionHandlersBehavior:
    """Test interaction handlers real behavior and side effects."""
    
    def _create_test_user(self, user_id: str, enable_checkins: bool = True, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, enable_checkins=enable_checkins, test_data_dir=test_data_dir)
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_handler_registry_creates_all_handlers(self):
        """Test that all handlers are properly registered and accessible."""
        handlers = get_all_handlers()
        
        # Check that all expected handlers exist
        expected_handlers = [
            'TaskManagementHandler', 'CheckinHandler', 'ProfileHandler',
            'ScheduleManagementHandler', 'AnalyticsHandler', 'HelpHandler'
        ]
        
        for handler_name in expected_handlers:
            assert handler_name in str(type(handlers.get(handler_name))), f"Handler {handler_name} not found"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_get_interaction_handler_returns_correct_handler(self):
        """Test that get_interaction_handler returns the correct handler for each intent."""
        # Test task management intents
        task_handler = get_interaction_handler('create_task')
        assert isinstance(task_handler, TaskManagementHandler), "Should return TaskManagementHandler for create_task"
        
        # Test check-in intents
        checkin_handler = get_interaction_handler('start_checkin')
        assert isinstance(checkin_handler, CheckinHandler), "Should return CheckinHandler for start_checkin"
        
        # Test profile intents
        profile_handler = get_interaction_handler('show_profile')
        assert isinstance(profile_handler, ProfileHandler), "Should return ProfileHandler for show_profile"
        
        # Test unknown intent
        unknown_handler = get_interaction_handler('unknown_intent')
        assert unknown_handler is None, "Should return None for unknown intent"
    
    @pytest.mark.behavior
    @pytest.mark.tasks
    def test_task_management_handler_can_handle_intents(self):
        """Test that TaskManagementHandler can handle all expected intents."""
        handler = TaskManagementHandler()
        
        expected_intents = ['create_task', 'list_tasks', 'complete_task', 'delete_task', 'update_task', 'task_stats']
        for intent in expected_intents:
            assert handler.can_handle(intent), f"TaskManagementHandler should handle {intent}"
        
        # Test that it doesn't handle other intents
        assert not handler.can_handle('start_checkin'), "TaskManagementHandler should not handle start_checkin"
        assert not handler.can_handle('show_profile'), "TaskManagementHandler should not handle show_profile"
    
    @pytest.mark.behavior
    @pytest.mark.checkins
    def test_checkin_handler_can_handle_intents(self):
        """Test that CheckinHandler can handle all expected intents."""
        handler = CheckinHandler()
        
        expected_intents = ['start_checkin', 'continue_checkin', 'checkin_status']
        for intent in expected_intents:
            assert handler.can_handle(intent), f"CheckinHandler should handle {intent}"
        
        # Test that it doesn't handle other intents
        assert not handler.can_handle('create_task'), "CheckinHandler should not handle create_task"
        assert not handler.can_handle('show_profile'), "CheckinHandler should not handle show_profile"
    
    @pytest.mark.behavior
    @pytest.mark.user_management
    def test_profile_handler_can_handle_intents(self):
        """Test that ProfileHandler can handle all expected intents."""
        handler = ProfileHandler()
        
        expected_intents = ['show_profile', 'update_profile', 'profile_stats']
        for intent in expected_intents:
            assert handler.can_handle(intent), f"ProfileHandler should handle {intent}"
        
        # Test that it doesn't handle other intents
        assert not handler.can_handle('create_task'), "ProfileHandler should not handle create_task"
        assert not handler.can_handle('start_checkin'), "ProfileHandler should not handle start_checkin"
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    def test_schedule_management_handler_can_handle_intents(self):
        """Test that ScheduleManagementHandler can handle all expected intents."""
        handler = ScheduleManagementHandler()
        
        expected_intents = ['show_schedule', 'update_schedule', 'schedule_status', 'add_schedule_period', 'edit_schedule_period']
        for intent in expected_intents:
            assert handler.can_handle(intent), f"ScheduleManagementHandler should handle {intent}"
        
        # Test that it doesn't handle other intents
        assert not handler.can_handle('create_task'), "ScheduleManagementHandler should not handle create_task"
        assert not handler.can_handle('start_checkin'), "ScheduleManagementHandler should not handle start_checkin"
    
    @pytest.mark.behavior
    @pytest.mark.analytics
    def test_analytics_handler_can_handle_intents(self):
        """Test that AnalyticsHandler can handle all expected intents."""
        handler = AnalyticsHandler()
        
        expected_intents = ['show_analytics', 'mood_trends', 'habit_analysis', 'sleep_analysis', 'wellness_score']
        for intent in expected_intents:
            assert handler.can_handle(intent), f"AnalyticsHandler should handle {intent}"
        
        # Test that it doesn't handle other intents
        assert not handler.can_handle('create_task'), "AnalyticsHandler should not handle create_task"
        assert not handler.can_handle('start_checkin'), "AnalyticsHandler should not handle start_checkin"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_help_handler_can_handle_intents(self):
        """Test that HelpHandler can handle all expected intents."""
        handler = HelpHandler()
        
        expected_intents = ['help', 'commands', 'examples']
        for intent in expected_intents:
            assert handler.can_handle(intent), f"HelpHandler should handle {intent}"
        
        # Test that it doesn't handle other intents
        assert not handler.can_handle('create_task'), "HelpHandler should not handle create_task"
        assert not handler.can_handle('start_checkin'), "HelpHandler should not handle start_checkin"
    
    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_task_management_handler_creates_actual_task(self, test_data_dir):
        """Test that TaskManagementHandler actually creates a task in the system."""
        handler = TaskManagementHandler()
        user_id = "test_user_123"
        
        # Create test user
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a parsed command for creating a task
        parsed_command = ParsedCommand(
            intent="create_task",
            entities={"title": "Test task", "due_date": "tomorrow"},
            confidence=0.9,
            original_message="create task Test task tomorrow"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert "created" in response.message.lower() or "added" in response.message.lower(), "Should indicate task was created"
        
        # Verify task was actually created in the system
        tasks = load_active_tasks(user_id)
        assert any(task.get('title') == 'Test task' for task in tasks), "Task should be created in the system"
    
    def test_task_management_handler_lists_actual_tasks(self, test_data_dir):
        """Test that TaskManagementHandler actually lists tasks from the system."""
        handler = TaskManagementHandler()
        user_id = "test_user_456"
        
        # Create test user
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create some test tasks first
        create_task(user_id, "Task 1", "2025-08-02")
        create_task(user_id, "Task 2", "2025-08-03")
        
        # Create a parsed command for listing tasks
        parsed_command = ParsedCommand(
            intent="list_tasks",
            entities={},
            confidence=0.9,
            original_message="show my tasks"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert "Task 1" in response.message or "Task 2" in response.message, "Should list created tasks"
    
    def test_task_management_handler_completes_actual_task(self, test_data_dir):
        """Test that TaskManagementHandler actually completes a task in the system."""
        handler = TaskManagementHandler()
        user_id = "test_user_789"

        # Create test user with tasks enabled
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Get the actual UUID for the created user
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "Should be able to get UUID for created user"

        # Create a test task first
        task_id = create_task(actual_user_id, "Task to complete", "2025-08-02")
        assert task_id is not None, "Task creation should succeed"

        # Verify task exists before trying to complete it
        tasks = load_active_tasks(actual_user_id)
        assert any(task.get('task_id') == task_id for task in tasks), "Task should exist before completion"

        # Create a parsed command for completing the task
        parsed_command = ParsedCommand(
            intent="complete_task",
            entities={"task_identifier": str(task_id)},
            confidence=0.9,
            original_message=f"complete task {task_id}"
        )

        # Handle the command
        response = handler.handle(actual_user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert "completed" in response.message.lower(), "Should indicate task was completed"
        
        # Verify task was actually completed in the system
        tasks = load_active_tasks(actual_user_id)
        assert not any(task.get('task_id') == task_id for task in tasks), "Task should be removed from active tasks"
    
    def test_checkin_handler_starts_checkin_flow(self, test_data_dir):
        """Test that CheckinHandler starts a check-in flow."""
        handler = CheckinHandler()
        user_id = "test_user_checkin"
        
        # Create test user with check-ins enabled and questions configured
        from tests.test_utilities import TestUserFactory
        success = TestUserFactory.create_user_with_complex_checkins(user_id, test_data_dir=test_data_dir)
        assert success, "Failed to create test user with check-ins"
        
        # Create a parsed command for starting check-in
        parsed_command = ParsedCommand(
            intent="start_checkin",
            entities={},
            confidence=0.9,
            original_message="start check-in"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        # Check-in might complete immediately if no questions are configured, or start a flow
        assert "check" in response.message.lower() or "feeling" in response.message.lower() or "mood" in response.message.lower(), "Should mention check-in related content"
    
    def test_profile_handler_shows_actual_profile(self, test_data_dir):
        """Test that ProfileHandler shows actual user profile data."""
        handler = ProfileHandler()
        user_id = "test_user_profile"
        
        # Create test user using centralized utilities
        from tests.test_utilities import TestUserFactory
        from core.user_management import get_user_id_by_identifier
        success = TestUserFactory.create_basic_user(user_id, enable_checkins=True, enable_tasks=True, test_data_dir=test_data_dir)
        assert success, "Failed to create test user"
        
        # Get the actual UUID for the created user
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "Should be able to get UUID for created user"
        
        # Update user context with profile-specific data
        from core.user_management import update_user_context
        update_success = update_user_context(actual_user_id, {
            'preferred_name': 'Test User',
            'gender_identity': ['they/them']
        })
        assert update_success, "User context should be updated successfully"
        
        # Create a parsed command for showing profile
        parsed_command = ParsedCommand(
            intent="show_profile",
            entities={},
            confidence=0.9,
            original_message="show my profile"
        )
        
        # Handle the command
        response = handler.handle(actual_user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert "Test User" in response.message, "Should show user name"
        assert "they/them" in response.message, "Should show pronouns"
    
    def test_help_handler_provides_help(self):
        """Test that HelpHandler provides helpful information."""
        handler = HelpHandler()
        user_id = "test_user_help"
        
        # Create a parsed command for help
        parsed_command = ParsedCommand(
            intent="help",
            entities={},
            confidence=0.9,
            original_message="help"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert "help" in response.message.lower() or "command" in response.message.lower(), "Should provide help information"
        assert len(response.message) > 50, "Help should be substantial"
    
    def test_all_handlers_return_proper_help(self):
        """Test that all handlers return proper help text."""
        handlers = get_all_handlers()
        
        for handler_name, handler in handlers.items():
            help_text = handler.get_help()
            assert isinstance(help_text, str), f"{handler_name} should return string help"
            assert len(help_text) > 10, f"{handler_name} help should be substantial"
            assert "help" in help_text.lower() or "command" in help_text.lower(), f"{handler_name} help should be helpful"
    
    def test_all_handlers_return_proper_examples(self):
        """Test that all handlers return proper example commands."""
        handlers = get_all_handlers()
        
        for handler_name, handler in handlers.items():
            examples = handler.get_examples()
            assert isinstance(examples, list), f"{handler_name} should return list of examples"
            assert len(examples) > 0, f"{handler_name} should have examples"
            
            for example in examples:
                assert isinstance(example, str), f"{handler_name} examples should be strings"
                assert len(example) > 3, f"{handler_name} examples should be substantial (minimum 4 characters)"
    
    def test_handler_error_handling(self, test_data_dir):
        """Test that handlers handle errors gracefully."""
        handler = TaskManagementHandler()
        user_id = "test_user_error"
        
        # Create test user
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a parsed command with invalid data
        parsed_command = ParsedCommand(
            intent="create_task",
            entities={"title": "", "due_date": "invalid_date"},  # Invalid data
            confidence=0.9,
            original_message="create task"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response - should ask for task name instead of showing error
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse even on error"
        assert "name" in response.message.lower() or "title" in response.message.lower(), "Should ask for task name"
        assert not response.completed, "Should not be completed when asking for more info"
    
    def test_handler_response_structure(self):
        """Test that all handlers return properly structured responses."""
        handlers = get_all_handlers()
        
        for handler_name, handler in handlers.items():
            # Test with a simple intent that should work
            if handler_name == "HelpHandler":
                parsed_command = ParsedCommand(
                    intent="help",
                    entities={},
                    confidence=0.9,
                    original_message="help"
                )
            elif handler_name == "TaskManagementHandler":
                parsed_command = ParsedCommand(
                    intent="task_stats",
                    entities={},
                    confidence=0.9,
                    original_message="task stats"
                )
            else:
                # Skip other handlers for this test to avoid complex setup
                continue
            
            response = handler.handle("test_user", parsed_command)
            
            # Verify response structure
            assert isinstance(response, InteractionResponse), f"{handler_name} should return InteractionResponse"
            assert isinstance(response.message, str), f"{handler_name} should return string message"
            assert isinstance(response.completed, bool), f"{handler_name} should return boolean completed"
            assert response.message.strip() != "", f"{handler_name} should return non-empty message" 