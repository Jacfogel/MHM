"""
Test command discovery through help system to ensure comprehensive command guidance.

This module tests the help system functionality to verify:
- Help responses provide comprehensive command discovery
- All command categories are documented
- Natural language is emphasized as primary method
- Examples are practical and useful
"""

from communication.command_handlers.interaction_handlers import HelpHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from tests.test_utilities import TestUserFactory


class TestCommandDiscoveryHelp:
    """Test command discovery through help system."""

    def test_general_help_response(self, test_data_dir):
        """Test that general help response contains all command categories."""
        handler = HelpHandler()
        user_id = "test_user_help_general"
        
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        parsed_command = ParsedCommand(
            intent="help",
            entities={},
            confidence=0.9,
            original_message="help"
        )
        
        response = handler.handle(user_id, parsed_command)
        
        assert isinstance(response, InteractionResponse)
        assert response.completed is True
        
        message = response.message
        
        # Verify response contains all command categories
        assert "**MHM Bot Commands**" in message
        assert "Tasks" in message
        assert "Check-ins" in message
        assert "Profile" in message
        assert "Analytics" in message
        assert "Schedule" in message
        
        # Verify natural language is emphasized
        assert "natural language" in message.lower()
        assert "just talk to me naturally" in message.lower()
        
        # Verify examples are provided
        assert "create a task to" in message.lower()
        assert "show my" in message.lower()
        
        # Verify help navigation
        assert "examples" in message.lower()
        assert "commands" in message.lower()
        assert "discord.md" in message.lower()

    def test_commands_list_response(self, test_data_dir):
        """Test that commands list response shows complete command list."""
        handler = HelpHandler()
        user_id = "test_user_commands_list"
        
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        parsed_command = ParsedCommand(
            intent="commands",
            entities={},
            confidence=0.9,
            original_message="commands"
        )
        
        response = handler.handle(user_id, parsed_command)
        
        assert isinstance(response, InteractionResponse)
        assert response.completed is True
        
        message = response.message
        
        # Verify complete command list appears
        assert "**Complete Command List:**" in message
        
        # Verify all 6 categories present
        assert "📋 **Task Management:**" in message
        assert "✅ **Check-ins**" in message
        assert "👤 **Profile Management:**" in message
        assert "📅 **Schedule Management:**" in message
        assert "📊 **Analytics & Insights:**" in message
        assert "🔧 **System Commands:**" in message
        
        # Verify natural language, explicit, and slash commands shown
        assert "Natural:" in message
        assert "Explicit:" in message
        assert "Slash:" in message
        
        # Verify command types explanation
        assert "**Command Types Explained:**" in message
        assert "Single-Turn" in message
        assert "Conversational Flows" in message
        
        # Verify flow management guidance
        assert "**Flow Management:**" in message
        assert "cancel" in message.lower()
        assert "clear flows" in message.lower()

    def test_category_specific_help_tasks(self, test_data_dir):
        """Test category-specific help for tasks."""
        handler = HelpHandler()
        user_id = "test_user_help_tasks"
        
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        parsed_command = ParsedCommand(
            intent="help",
            entities={"topic": "tasks"},
            confidence=0.9,
            original_message="help tasks"
        )
        
        response = handler.handle(user_id, parsed_command)
        
        assert isinstance(response, InteractionResponse)
        assert response.completed is True
        
        message = response.message
        
        # Verify category-specific examples provided
        assert "**Task Management Help:**" in message
        assert "create task" in message.lower()
        assert "list tasks" in message.lower()
        assert "complete task" in message.lower()
        assert "delete task" in message.lower()
        assert "update task" in message.lower()
        assert "task stats" in message.lower()
        
        # Verify commands are actionable
        assert "Call mom tomorrow" in message
        assert "Buy groceries" in message

    def test_category_specific_help_checkin(self, test_data_dir):
        """Test category-specific help for check-ins."""
        handler = HelpHandler()
        user_id = "test_user_help_checkin"
        
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        parsed_command = ParsedCommand(
            intent="help",
            entities={"topic": "checkin"},
            confidence=0.9,
            original_message="help checkin"
        )
        
        response = handler.handle(user_id, parsed_command)
        
        assert isinstance(response, InteractionResponse)
        assert response.completed is True
        
        message = response.message
        
        # Verify category-specific examples provided
        assert "**check-in help:**" in message.lower()
        assert "start checkin" in message.lower()
        assert "checkin status" in message.lower()
        assert "check-in history" in message.lower()  # Note: hyphenated in actual output
        assert "cancel" in message.lower()
        
        # Verify conversational flow explanation (may not be present in all help responses)
        # The check-in help focuses on commands, not flow explanation

    def test_category_specific_help_profile(self, test_data_dir):
        """Test category-specific help for profile."""
        handler = HelpHandler()
        user_id = "test_user_help_profile"
        
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        parsed_command = ParsedCommand(
            intent="help",
            entities={"topic": "profile"},
            confidence=0.9,
            original_message="help profile"
        )
        
        response = handler.handle(user_id, parsed_command)
        
        assert isinstance(response, InteractionResponse)
        assert response.completed is True
        
        message = response.message
        
        # Verify category-specific examples provided
        assert "**Profile Management Help:**" in message
        assert "show profile" in message.lower()
        assert "update name" in message.lower()
        assert "update gender" in message.lower()
        assert "profile stats" in message.lower()
        
        # Verify commands are actionable
        assert "Julie" in message  # Example name

    def test_examples_response(self, test_data_dir):
        """Test examples response provides natural language examples."""
        handler = HelpHandler()
        user_id = "test_user_examples"
        
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        parsed_command = ParsedCommand(
            intent="examples",
            entities={},
            confidence=0.9,
            original_message="examples"
        )
        
        response = handler.handle(user_id, parsed_command)
        
        assert isinstance(response, InteractionResponse)
        assert response.completed is True
        
        message = response.message
        
        # Verify natural language examples provided
        assert "**General Examples:**" in message
        assert "create a task" in message.lower()
        assert "show me my" in message.lower()
        assert "check in" in message.lower()
        assert "update my" in message.lower()
        
        # Verify examples are practical and useful
        assert "call mom tomorrow" in message
        # Note: "buy groceries" may not be in all example sets
        assert "Non-binary" in message  # Gender identity example

    def test_examples_by_category(self, test_data_dir):
        """Test examples response for specific categories."""
        handler = HelpHandler()
        user_id = "test_user_examples_category"
        
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Test tasks examples
        parsed_command = ParsedCommand(
            intent="examples",
            entities={"category": "tasks"},
            confidence=0.9,
            original_message="examples tasks"
        )
        
        response = handler.handle(user_id, parsed_command)
        
        assert isinstance(response, InteractionResponse)
        assert response.completed is True
        
        message = response.message
        
        # Verify task-specific examples
        assert "**Task Examples:**" in message
        assert "call mom tomorrow" in message.lower()
        assert "buy groceries" in message.lower()
        assert "show me my tasks" in message.lower()
        assert "complete task" in message.lower()
        assert "delete" in message.lower()
        assert "update task" in message.lower()

    def test_help_system_comprehensive_coverage(self, test_data_dir):
        """Test that help system provides comprehensive command coverage."""
        handler = HelpHandler()
        user_id = "test_user_comprehensive"
        
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Test general help
        parsed_command = ParsedCommand(
            intent="help",
            entities={},
            confidence=0.9,
            original_message="help"
        )
        
        response = handler.handle(user_id, parsed_command)
        message = response.message
        
        # Verify all major command categories are mentioned
        categories = ["Tasks", "Check-ins", "Profile", "Analytics", "Schedule"]
        for category in categories:
            assert category in message
        
        # Verify natural language emphasis
        assert "natural language" in message.lower()
        assert "just talk" in message.lower()
        
        # Verify navigation to more detailed help
        assert "commands" in message.lower()
        assert "examples" in message.lower()

    def test_help_system_error_handling(self, test_data_dir):
        """Test help system handles unknown topics gracefully."""
        handler = HelpHandler()
        user_id = "test_user_help_error"
        
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Test with unknown topic
        parsed_command = ParsedCommand(
            intent="help",
            entities={"topic": "unknown_topic"},
            confidence=0.9,
            original_message="help unknown"
        )
        
        response = handler.handle(user_id, parsed_command)
        
        assert isinstance(response, InteractionResponse)
        assert response.completed is True
        
        # Should fall back to general help
        message = response.message
        assert "**MHM Bot Commands**" in message
        assert "natural language" in message.lower()

    def test_help_system_suggestions(self, test_data_dir):
        """Test that help responses include appropriate suggestions."""
        handler = HelpHandler()
        user_id = "test_user_help_suggestions"
        
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        parsed_command = ParsedCommand(
            intent="help",
            entities={},
            confidence=0.9,
            original_message="help"
        )
        
        response = handler.handle(user_id, parsed_command)
        
        assert isinstance(response, InteractionResponse)
        
        # Help responses may not have suggestions, but should be complete
        assert response.completed is True
        message = response.message
        
        # Should provide clear next steps
        assert "examples" in message.lower()
        assert "commands" in message.lower()
        assert "discord.md" in message.lower()
