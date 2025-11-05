"""
Message Router Behavior Tests

Tests for communication/message_processing/message_router.py focusing on real behavior and side effects.
These tests verify that the message router actually works and produces expected
routing results rather than just returning values.
"""

import pytest
from unittest.mock import patch, MagicMock

# Import the modules we're testing
from communication.message_processing.message_router import (
    MessageRouter,
    MessageType,
    RoutingResult,
    get_message_router
)


class TestMessageRouterBehavior:
    """Test message router real behavior and side effects."""
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_initialization(self):
        """Test that MessageRouter initializes correctly."""
        router = MessageRouter()
        
        assert router is not None, "Router should be initialized"
        assert hasattr(router, '_command_definitions'), "Should have command definitions"
        assert hasattr(router, 'slash_command_map'), "Should have slash command map"
        assert hasattr(router, 'bang_command_map'), "Should have bang command map"
        assert len(router._command_definitions) > 0, "Should have command definitions"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_get_command_definitions(self):
        """Test that MessageRouter returns command definitions."""
        router = MessageRouter()
        definitions = router.get_command_definitions()
        
        assert isinstance(definitions, list), "Should return list"
        assert len(definitions) > 0, "Should have definitions"
        for cmd in definitions:
            assert 'name' in cmd, "Each command should have name"
            assert 'mapped_message' in cmd, "Each command should have mapped_message"
            assert 'description' in cmd, "Each command should have description"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_get_slash_command_map(self):
        """Test that MessageRouter returns slash command map."""
        router = MessageRouter()
        cmd_map = router.get_slash_command_map()
        
        assert isinstance(cmd_map, dict), "Should return dict"
        assert len(cmd_map) > 0, "Should have mappings"
        # Verify all values are strings
        for key, value in cmd_map.items():
            assert isinstance(key, str), "Keys should be strings"
            assert isinstance(value, str), "Values should be strings"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_get_bang_command_map(self):
        """Test that MessageRouter returns bang command map."""
        router = MessageRouter()
        cmd_map = router.get_bang_command_map()
        
        assert isinstance(cmd_map, dict), "Should return dict"
        assert len(cmd_map) > 0, "Should have mappings"
        # Verify all values are strings
        for key, value in cmd_map.items():
            assert isinstance(key, str), "Keys should be strings"
            assert isinstance(value, str), "Values should be strings"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_route_message_invalid_input(self):
        """Test that MessageRouter handles invalid input gracefully."""
        router = MessageRouter()
        
        # Test None input
        result = router.route_message(None)
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.UNKNOWN, "Should return UNKNOWN for None"
        
        # Test empty string
        result = router.route_message("")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.UNKNOWN, "Should return UNKNOWN for empty string"
        
        # Test whitespace only
        result = router.route_message("   ")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.UNKNOWN, "Should return UNKNOWN for whitespace"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_route_slash_command_known(self):
        """Test that MessageRouter routes known slash commands correctly."""
        router = MessageRouter()
        
        # Test known commands
        test_cases = [
            ("/tasks", MessageType.SLASH_COMMAND, "tasks", "show my tasks"),
            ("/profile", MessageType.SLASH_COMMAND, "profile", "show profile"),
            ("/schedule", MessageType.SLASH_COMMAND, "schedule", "show schedule"),
            ("/analytics", MessageType.SLASH_COMMAND, "analytics", "show analytics"),
            ("/help", MessageType.SLASH_COMMAND, "help", "help"),
        ]
        
        for message, expected_type, expected_cmd, expected_mapped in test_cases:
            result = router.route_message(message)
            assert isinstance(result, RoutingResult), f"Should return RoutingResult for {message}"
            assert result.message_type == expected_type, f"Should return {expected_type} for {message}"
            assert result.command_name == expected_cmd, f"Should have command name {expected_cmd}"
            assert result.mapped_message == expected_mapped, f"Should map to {expected_mapped}"
            assert result.should_continue_parsing == True, "Should continue parsing for regular commands"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_route_slash_command_flow(self):
        """Test that MessageRouter routes flow commands correctly."""
        router = MessageRouter()
        
        # Test flow command (checkin)
        result = router.route_message("/checkin")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.FLOW_COMMAND, "Should be FLOW_COMMAND"
        assert result.command_name == "checkin", "Should have command name"
        assert result.mapped_message == "start checkin", "Should map correctly"
        assert result.should_continue_parsing == False, "Should not continue parsing for flow commands"
        assert result.flow_command == True, "Should be marked as flow command"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_route_slash_command_cancel(self):
        """Test that MessageRouter routes /cancel correctly."""
        router = MessageRouter()
        
        result = router.route_message("/cancel")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.FLOW_COMMAND, "Should be FLOW_COMMAND"
        assert result.command_name == "cancel", "Should have command name"
        assert result.mapped_message == "/cancel", "Should map correctly"
        assert result.should_continue_parsing == False, "Should not continue parsing"
        assert result.flow_command == True, "Should be marked as flow command"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_route_slash_command_unknown(self):
        """Test that MessageRouter routes unknown slash commands correctly."""
        router = MessageRouter()
        
        result = router.route_message("/unknown_command")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.SLASH_COMMAND, "Should be SLASH_COMMAND"
        assert result.should_continue_parsing == True, "Should continue parsing for unknown commands"
        assert result.command_name is None or result.command_name != "unknown_command", "Should not have unknown command name"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_route_bang_command_known(self):
        """Test that MessageRouter routes known bang commands correctly."""
        router = MessageRouter()
        
        # Test known commands
        test_cases = [
            ("!tasks", MessageType.BANG_COMMAND, "tasks", "show my tasks"),
            ("!profile", MessageType.BANG_COMMAND, "profile", "show profile"),
            ("!schedule", MessageType.BANG_COMMAND, "schedule", "show schedule"),
            ("!analytics", MessageType.BANG_COMMAND, "analytics", "show analytics"),
        ]
        
        for message, expected_type, expected_cmd, expected_mapped in test_cases:
            result = router.route_message(message)
            assert isinstance(result, RoutingResult), f"Should return RoutingResult for {message}"
            assert result.message_type == expected_type, f"Should return {expected_type} for {message}"
            assert result.command_name == expected_cmd, f"Should have command name {expected_cmd}"
            assert result.mapped_message == expected_mapped, f"Should map to {expected_mapped}"
            assert result.should_continue_parsing == True, "Should continue parsing for regular commands"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_route_bang_command_flow(self):
        """Test that MessageRouter routes flow bang commands correctly."""
        router = MessageRouter()
        
        # Test flow command (checkin)
        result = router.route_message("!checkin")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.FLOW_COMMAND, "Should be FLOW_COMMAND"
        assert result.command_name == "checkin", "Should have command name"
        assert result.mapped_message == "start checkin", "Should map correctly"
        assert result.should_continue_parsing == False, "Should not continue parsing for flow commands"
        assert result.flow_command == True, "Should be marked as flow command"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_route_bang_command_unknown(self):
        """Test that MessageRouter routes unknown bang commands correctly."""
        router = MessageRouter()
        
        result = router.route_message("!unknown_command")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.BANG_COMMAND, "Should be BANG_COMMAND"
        assert result.should_continue_parsing == True, "Should continue parsing for unknown commands"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_route_conversational(self):
        """Test that MessageRouter routes conversational messages correctly."""
        router = MessageRouter()
        
        # Test conversational messages (no slash or bang)
        test_messages = [
            "How are you?",
            "Show me my tasks",
            "What's my schedule?",
            "I'm feeling good today"
        ]
        
        for message in test_messages:
            result = router.route_message(message)
            assert isinstance(result, RoutingResult), f"Should return RoutingResult for {message}"
            assert result.message_type == MessageType.STRUCTURED_COMMAND, f"Should be STRUCTURED_COMMAND for {message}"
            assert result.should_continue_parsing == True, "Should continue parsing"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_is_flow_command(self):
        """Test that MessageRouter correctly identifies flow commands."""
        router = MessageRouter()
        
        # Test flow command
        assert router.is_flow_command("checkin") == True, "checkin should be flow command"
        
        # Test non-flow commands
        assert router.is_flow_command("tasks") == False, "tasks should not be flow command"
        assert router.is_flow_command("profile") == False, "profile should not be flow command"
        assert router.is_flow_command("schedule") == False, "schedule should not be flow command"
        
        # Test unknown command
        assert router.is_flow_command("unknown") == False, "unknown should not be flow command"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_is_flow_command_invalid(self):
        """Test that MessageRouter handles invalid input for is_flow_command."""
        router = MessageRouter()
        
        # Test None
        result = router.is_flow_command(None)
        assert result == False, "Should return False for None"
        
        # Test empty string
        result = router.is_flow_command("")
        assert result == False, "Should return False for empty string"
        
        # Test whitespace
        result = router.is_flow_command("   ")
        assert result == False, "Should return False for whitespace"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_get_command_mapping(self):
        """Test that MessageRouter returns command mappings correctly."""
        router = MessageRouter()
        
        # Test known commands
        assert router.get_command_mapping("tasks") == "show my tasks", "Should map tasks correctly"
        assert router.get_command_mapping("profile") == "show profile", "Should map profile correctly"
        assert router.get_command_mapping("schedule") == "show schedule", "Should map schedule correctly"
        assert router.get_command_mapping("checkin") == "start checkin", "Should map checkin correctly"
        
        # Test unknown command
        assert router.get_command_mapping("unknown") is None, "Should return None for unknown command"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_get_command_mapping_invalid(self):
        """Test that MessageRouter handles invalid input for get_command_mapping."""
        router = MessageRouter()
        
        # Test None
        result = router.get_command_mapping(None)
        assert result is None, "Should return None for None"
        
        # Test empty string
        result = router.get_command_mapping("")
        assert result is None, "Should return None for empty string"
        
        # Test whitespace
        result = router.get_command_mapping("   ")
        assert result is None, "Should return None for whitespace"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_route_slash_command_with_args(self):
        """Test that MessageRouter handles slash commands with arguments."""
        router = MessageRouter()
        
        # Test commands with arguments
        result = router.route_message("/tasks today")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.SLASH_COMMAND, "Should be SLASH_COMMAND"
        assert result.command_name == "tasks", "Should extract command name correctly"
        assert result.mapped_message == "show my tasks", "Should map correctly"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_route_bang_command_with_args(self):
        """Test that MessageRouter handles bang commands with arguments."""
        router = MessageRouter()
        
        # Test commands with arguments
        result = router.route_message("!profile update")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.BANG_COMMAND, "Should be BANG_COMMAND"
        assert result.command_name == "profile", "Should extract command name correctly"
        assert result.mapped_message == "show profile", "Should map correctly"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_route_case_insensitive(self):
        """Test that MessageRouter handles case-insensitive commands."""
        router = MessageRouter()
        
        # Test uppercase
        result = router.route_message("/TASKS")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.SLASH_COMMAND, "Should be SLASH_COMMAND"
        assert result.command_name == "tasks", "Should handle uppercase"
        
        # Test mixed case
        result = router.route_message("/PrOfIlE")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.SLASH_COMMAND, "Should be SLASH_COMMAND"
        assert result.command_name == "profile", "Should handle mixed case"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_get_message_router_singleton(self):
        """Test that get_message_router returns singleton instance."""
        import communication.message_processing.message_router as router_module
        
        # Store original router for cleanup
        original_router = router_module._message_router
        
        try:
            # Clear any existing router
            router_module._message_router = None
            
            # Get first instance
            router1 = get_message_router()
            assert router1 is not None, "Should return router instance"
            assert isinstance(router1, MessageRouter), "Should be MessageRouter instance"
            
            # Get second instance - should be same
            router2 = get_message_router()
            assert router2 is router1, "Should return same instance (singleton)"
        finally:
            # Restore original router to prevent state pollution
            router_module._message_router = original_router
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_route_slash_command_edge_cases(self):
        """Test that MessageRouter handles edge cases for slash commands."""
        router = MessageRouter()
        
        # Test just slash
        result = router.route_message("/")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.SLASH_COMMAND, "Should be SLASH_COMMAND"
        assert result.should_continue_parsing == True, "Should continue parsing"
        
        # Test slash with spaces
        result = router.route_message("/ tasks")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        # Should handle spacing correctly
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_route_bang_command_edge_cases(self):
        """Test that MessageRouter handles edge cases for bang commands."""
        router = MessageRouter()
        
        # Test just bang
        result = router.route_message("!")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.BANG_COMMAND, "Should be BANG_COMMAND"
        assert result.should_continue_parsing == True, "Should continue parsing"
        
        # Test bang with spaces
        result = router.route_message("! tasks")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        # Should handle spacing correctly
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_router_all_defined_commands(self):
        """Test that all defined commands can be routed correctly."""
        router = MessageRouter()
        definitions = router.get_command_definitions()
        
        # Test all defined commands work
        for cmd_def in definitions:
            cmd_name = cmd_def['name']
            
            # Test slash command
            result = router.route_message(f"/{cmd_name}")
            assert isinstance(result, RoutingResult), f"Should return RoutingResult for /{cmd_name}"
            assert result.command_name == cmd_name, f"Should have correct command name for /{cmd_name}"
            
            # Test bang command
            result = router.route_message(f"!{cmd_name}")
            assert isinstance(result, RoutingResult), f"Should return RoutingResult for !{cmd_name}"
            assert result.command_name == cmd_name, f"Should have correct command name for !{cmd_name}"
            
            # Test is_flow_command
            is_flow = router.is_flow_command(cmd_name)
            assert isinstance(is_flow, bool), f"Should return bool for is_flow_command({cmd_name})"
            
            # Test get_command_mapping
            mapping = router.get_command_mapping(cmd_name)
            assert mapping == cmd_def['mapped_message'], f"Should return correct mapping for {cmd_name}"

