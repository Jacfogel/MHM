"""
Message Route Classifier Behavior Tests

Tests for communication/message_processing/message_route_classifier.py focusing on real behavior and side effects.
"""

import pytest

from communication.message_processing.message_route_classifier import (
    MessageRouteClassifier,
    MessageType,
    RoutingResult,
)


class TestMessageRouteClassifierBehavior:
    """Test message route classifier real behavior and side effects."""

    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_route_classifier_initialization(self):
        """Test that MessageRouteClassifier initializes correctly."""
        classifier = MessageRouteClassifier()
        
        assert classifier is not None, "Classifier should be initialized"
        assert hasattr(classifier, '_command_definitions'), "Should have command definitions"
        assert hasattr(classifier, 'slash_command_map'), "Should have slash command map"
        assert hasattr(classifier, 'bang_command_map'), "Should have bang command map"
        assert len(classifier._command_definitions) > 0, "Should have command definitions"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_get_command_definitions(self):
        """Test that MessageRouteClassifier returns command definitions."""
        classifier = MessageRouteClassifier()
        definitions = classifier.get_command_definitions()
        
        assert isinstance(definitions, list), "Should return list"
        assert len(definitions) > 0, "Should have definitions"
        for cmd in definitions:
            assert 'name' in cmd, "Each command should have name"
            assert 'mapped_message' in cmd, "Each command should have mapped_message"
            assert 'description' in cmd, "Each command should have description"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_get_slash_command_map(self):
        """Test that MessageRouteClassifier returns slash command map."""
        classifier = MessageRouteClassifier()
        cmd_map = classifier.get_slash_command_map()
        
        assert isinstance(cmd_map, dict), "Should return dict"
        assert len(cmd_map) > 0, "Should have mappings"
        # Verify all values are strings
        for key, value in cmd_map.items():
            assert isinstance(key, str), "Keys should be strings"
            assert isinstance(value, str), "Values should be strings"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_get_bang_command_map(self):
        """Test that MessageRouteClassifier returns bang command map."""
        classifier = MessageRouteClassifier()
        cmd_map = classifier.get_bang_command_map()
        
        assert isinstance(cmd_map, dict), "Should return dict"
        assert len(cmd_map) > 0, "Should have mappings"
        # Verify all values are strings
        for key, value in cmd_map.items():
            assert isinstance(key, str), "Keys should be strings"
            assert isinstance(value, str), "Values should be strings"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_route_message_invalid_input(self):
        """Test that MessageRouteClassifier handles invalid input gracefully."""
        classifier = MessageRouteClassifier()
        
        # Test None input
        result = classifier.route_message(None)
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.UNKNOWN, "Should return UNKNOWN for None"
        
        # Test empty string
        result = classifier.route_message("")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.UNKNOWN, "Should return UNKNOWN for empty string"
        
        # Test whitespace only
        result = classifier.route_message("   ")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.UNKNOWN, "Should return UNKNOWN for whitespace"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_route_slash_command_known(self):
        """Test that MessageRouteClassifier routes known slash commands correctly."""
        classifier = MessageRouteClassifier()
        
        # Test known commands
        test_cases = [
            ("/tasks", MessageType.SLASH_COMMAND, "tasks", "show my tasks"),
            ("/profile", MessageType.SLASH_COMMAND, "profile", "show profile"),
            ("/schedule", MessageType.SLASH_COMMAND, "schedule", "show schedule"),
            ("/analytics", MessageType.SLASH_COMMAND, "analytics", "show analytics"),
            ("/help", MessageType.SLASH_COMMAND, "help", "help"),
        ]
        
        for message, expected_type, expected_cmd, expected_mapped in test_cases:
            result = classifier.route_message(message)
            assert isinstance(result, RoutingResult), f"Should return RoutingResult for {message}"
            assert result.message_type == expected_type, f"Should return {expected_type} for {message}"
            assert result.command_name == expected_cmd, f"Should have command name {expected_cmd}"
            assert result.mapped_message == expected_mapped, f"Should map to {expected_mapped}"
            assert result.should_continue_parsing, "Should continue parsing for regular commands"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_route_slash_command_flow(self):
        """Test that MessageRouteClassifier routes flow commands correctly."""
        classifier = MessageRouteClassifier()
        
        # Test flow command (checkin)
        result = classifier.route_message("/checkin")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.FLOW_COMMAND, "Should be FLOW_COMMAND"
        assert result.command_name == "checkin", "Should have command name"
        assert result.mapped_message == "start checkin", "Should map correctly"
        assert not result.should_continue_parsing, "Should not continue parsing for flow commands"
        assert result.flow_command, "Should be marked as flow command"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_route_slash_command_cancel(self):
        """Test that MessageRouteClassifier routes /cancel correctly."""
        classifier = MessageRouteClassifier()
        
        result = classifier.route_message("/cancel")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.FLOW_COMMAND, "Should be FLOW_COMMAND"
        assert result.command_name == "cancel", "Should have command name"
        assert result.mapped_message == "/cancel", "Should map correctly"
        assert not result.should_continue_parsing, "Should not continue parsing"
        assert result.flow_command, "Should be marked as flow command"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_route_slash_command_unknown(self):
        """Test that MessageRouteClassifier routes unknown slash commands correctly."""
        classifier = MessageRouteClassifier()
        
        result = classifier.route_message("/unknown_command")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.SLASH_COMMAND, "Should be SLASH_COMMAND"
        assert result.should_continue_parsing, "Should continue parsing for unknown commands"
        assert result.command_name is None or result.command_name != "unknown_command", "Should not have unknown command name"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_route_bang_command_known(self):
        """Test that MessageRouteClassifier routes known bang commands correctly."""
        classifier = MessageRouteClassifier()
        
        # Test known commands
        test_cases = [
            ("!tasks", MessageType.BANG_COMMAND, "tasks", "show my tasks"),
            ("!profile", MessageType.BANG_COMMAND, "profile", "show profile"),
            ("!schedule", MessageType.BANG_COMMAND, "schedule", "show schedule"),
            ("!analytics", MessageType.BANG_COMMAND, "analytics", "show analytics"),
        ]
        
        for message, expected_type, expected_cmd, expected_mapped in test_cases:
            result = classifier.route_message(message)
            assert isinstance(result, RoutingResult), f"Should return RoutingResult for {message}"
            assert result.message_type == expected_type, f"Should return {expected_type} for {message}"
            assert result.command_name == expected_cmd, f"Should have command name {expected_cmd}"
            assert result.mapped_message == expected_mapped, f"Should map to {expected_mapped}"
            assert result.should_continue_parsing, "Should continue parsing for regular commands"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_route_bang_command_flow(self):
        """Test that MessageRouteClassifier routes flow bang commands correctly."""
        classifier = MessageRouteClassifier()
        
        # Test flow command (checkin)
        result = classifier.route_message("!checkin")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.FLOW_COMMAND, "Should be FLOW_COMMAND"
        assert result.command_name == "checkin", "Should have command name"
        assert result.mapped_message == "start checkin", "Should map correctly"
        assert not result.should_continue_parsing, "Should not continue parsing for flow commands"
        assert result.flow_command, "Should be marked as flow command"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_route_bang_command_unknown(self):
        """Test that MessageRouteClassifier routes unknown bang commands correctly."""
        classifier = MessageRouteClassifier()
        
        result = classifier.route_message("!unknown_command")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.BANG_COMMAND, "Should be BANG_COMMAND"
        assert result.should_continue_parsing, "Should continue parsing for unknown commands"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_route_conversational(self):
        """Test that MessageRouteClassifier routes conversational messages correctly."""
        classifier = MessageRouteClassifier()
        
        # Test conversational messages (no slash or bang)
        test_messages = [
            "How are you?",
            "Show me my tasks",
            "What's my schedule?",
            "I'm feeling good today"
        ]
        
        for message in test_messages:
            result = classifier.route_message(message)
            assert isinstance(result, RoutingResult), f"Should return RoutingResult for {message}"
            assert result.message_type == MessageType.STRUCTURED_COMMAND, f"Should be STRUCTURED_COMMAND for {message}"
            assert result.should_continue_parsing, "Should continue parsing"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_is_flow_command(self):
        """Test that MessageRouteClassifier correctly identifies flow commands."""
        classifier = MessageRouteClassifier()
        
        # Test flow command
        assert classifier.is_flow_command("checkin"), "checkin should be flow command"
        
        # Test non-flow commands
        assert not classifier.is_flow_command("tasks"), "tasks should not be flow command"
        assert not classifier.is_flow_command("profile"), "profile should not be flow command"
        assert not classifier.is_flow_command("schedule"), "schedule should not be flow command"
        
        # Test unknown command
        assert not classifier.is_flow_command("unknown"), "unknown should not be flow command"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_is_flow_command_invalid(self):
        """Test that MessageRouteClassifier handles invalid input for is_flow_command."""
        classifier = MessageRouteClassifier()
        
        # Test None
        result = classifier.is_flow_command(None)
        assert not result, "Should return False for None"
        
        # Test empty string
        result = classifier.is_flow_command("")
        assert not result, "Should return False for empty string"
        
        # Test whitespace
        result = classifier.is_flow_command("   ")
        assert not result, "Should return False for whitespace"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_get_command_mapping(self):
        """Test that MessageRouteClassifier returns command mappings correctly."""
        classifier = MessageRouteClassifier()
        
        # Test known commands
        assert classifier.get_command_mapping("tasks") == "show my tasks", "Should map tasks correctly"
        assert classifier.get_command_mapping("profile") == "show profile", "Should map profile correctly"
        assert classifier.get_command_mapping("schedule") == "show schedule", "Should map schedule correctly"
        assert classifier.get_command_mapping("checkin") == "start checkin", "Should map checkin correctly"
        
        # Test unknown command
        assert classifier.get_command_mapping("unknown") is None, "Should return None for unknown command"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_get_command_mapping_invalid(self):
        """Test that MessageRouteClassifier handles invalid input for get_command_mapping."""
        classifier = MessageRouteClassifier()
        
        # Test None
        result = classifier.get_command_mapping(None)
        assert result is None, "Should return None for None"
        
        # Test empty string
        result = classifier.get_command_mapping("")
        assert result is None, "Should return None for empty string"
        
        # Test whitespace
        result = classifier.get_command_mapping("   ")
        assert result is None, "Should return None for whitespace"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_route_slash_command_with_args(self):
        """Test that MessageRouteClassifier handles slash commands with arguments."""
        classifier = MessageRouteClassifier()
        
        # Test commands with arguments
        result = classifier.route_message("/tasks today")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.SLASH_COMMAND, "Should be SLASH_COMMAND"
        assert result.command_name == "tasks", "Should extract command name correctly"
        assert result.mapped_message == "show my tasks", "Should map correctly"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_route_bang_command_with_args(self):
        """Test that MessageRouteClassifier handles bang commands with arguments."""
        classifier = MessageRouteClassifier()
        
        # Test commands with arguments
        result = classifier.route_message("!profile update")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.BANG_COMMAND, "Should be BANG_COMMAND"
        assert result.command_name == "profile", "Should extract command name correctly"
        assert result.mapped_message == "show profile", "Should map correctly"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_route_case_insensitive(self):
        """Test that MessageRouteClassifier handles case-insensitive commands."""
        classifier = MessageRouteClassifier()
        
        # Test uppercase
        result = classifier.route_message("/TASKS")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.SLASH_COMMAND, "Should be SLASH_COMMAND"
        assert result.command_name == "tasks", "Should handle uppercase"
        
        # Test mixed case
        result = classifier.route_message("/PrOfIlE")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.SLASH_COMMAND, "Should be SLASH_COMMAND"
        assert result.command_name == "profile", "Should handle mixed case"

    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_route_classifier_route_slash_command_edge_cases(self):
        """Test that MessageRouteClassifier handles edge cases for slash commands."""
        classifier = MessageRouteClassifier()
        
        # Test just slash
        result = classifier.route_message("/")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.SLASH_COMMAND, "Should be SLASH_COMMAND"
        assert result.should_continue_parsing, "Should continue parsing"
        
        # Test slash with spaces
        result = classifier.route_message("/ tasks")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        # Should handle spacing correctly
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_route_bang_command_edge_cases(self):
        """Test that MessageRouteClassifier handles edge cases for bang commands."""
        classifier = MessageRouteClassifier()
        
        # Test just bang
        result = classifier.route_message("!")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        assert result.message_type == MessageType.BANG_COMMAND, "Should be BANG_COMMAND"
        assert result.should_continue_parsing, "Should continue parsing"
        
        # Test bang with spaces
        result = classifier.route_message("! tasks")
        assert isinstance(result, RoutingResult), "Should return RoutingResult"
        # Should handle spacing correctly
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_message_classifier_all_defined_commands(self):
        """Test that all defined commands can be routed correctly."""
        classifier = MessageRouteClassifier()
        definitions = classifier.get_command_definitions()
        
        # Test all defined commands work
        for cmd_def in definitions:
            cmd_name = cmd_def['name']
            
            # Test slash command
            result = classifier.route_message(f"/{cmd_name}")
            assert isinstance(result, RoutingResult), f"Should return RoutingResult for /{cmd_name}"
            assert result.command_name == cmd_name, f"Should have correct command name for /{cmd_name}"
            
            # Test bang command
            result = classifier.route_message(f"!{cmd_name}")
            assert isinstance(result, RoutingResult), f"Should return RoutingResult for !{cmd_name}"
            assert result.command_name == cmd_name, f"Should have correct command name for !{cmd_name}"
            
            # Test is_flow_command
            is_flow = classifier.is_flow_command(cmd_name)
            assert isinstance(is_flow, bool), f"Should return bool for is_flow_command({cmd_name})"
            
            # Test get_command_mapping
            mapping = classifier.get_command_mapping(cmd_name)
            assert mapping == cmd_def['mapped_message'], f"Should return correct mapping for {cmd_name}"

