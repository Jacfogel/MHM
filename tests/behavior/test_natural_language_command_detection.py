"""
Behavior tests for natural language command detection.

Tests verify that natural language task requests like "I need to buy groceries"
are properly detected as command_with_clarification mode instead of chat mode.
"""

import pytest
from ai.chatbot import get_ai_chatbot


class TestNaturalLanguageCommandDetection:
    """Test that natural language task requests are detected correctly."""

    @pytest.mark.behavior
    def test_i_need_to_buy_groceries_detects_clarification_mode(self):
        """Test that 'I need to buy groceries' is detected as command_with_clarification."""
        bot = get_ai_chatbot()
        
        mode = bot._detect_mode("I need to buy groceries")
        
        # Should be detected as command_with_clarification, not chat
        assert mode == "command_with_clarification", (
            f"Expected 'command_with_clarification', got '{mode}'. "
            "Natural language task requests should trigger clarification mode."
        )

    @pytest.mark.behavior
    def test_i_should_call_mom_detects_clarification_mode(self):
        """Test that 'I should call mom' is detected as command_with_clarification."""
        bot = get_ai_chatbot()
        
        mode = bot._detect_mode("I should call mom")
        
        assert mode == "command_with_clarification", (
            f"Expected 'command_with_clarification', got '{mode}'"
        )

    @pytest.mark.behavior
    def test_i_want_to_schedule_dentist_detects_clarification_mode(self):
        """Test that 'I want to schedule dentist' is detected as command_with_clarification."""
        bot = get_ai_chatbot()
        
        mode = bot._detect_mode("I want to schedule dentist")
        
        assert mode == "command_with_clarification", (
            f"Expected 'command_with_clarification', got '{mode}'"
        )

    @pytest.mark.behavior
    def test_i_need_to_get_milk_detects_clarification_mode(self):
        """Test that 'I need to get milk' is detected as command_with_clarification."""
        bot = get_ai_chatbot()
        
        mode = bot._detect_mode("I need to get milk")
        
        assert mode == "command_with_clarification", (
            f"Expected 'command_with_clarification', got '{mode}'"
        )

    @pytest.mark.behavior
    def test_explicit_commands_still_work(self):
        """Test that explicit commands like 'add task buy groceries' still work."""
        bot = get_ai_chatbot()
        
        # Explicit commands should still be detected as command mode
        mode1 = bot._detect_mode("add task buy groceries")
        assert mode1 == "command", f"Expected 'command', got '{mode1}'"
        
        mode2 = bot._detect_mode("create task call mom")
        assert mode2 == "command", f"Expected 'command', got '{mode2}'"

    @pytest.mark.behavior
    def test_chat_messages_still_detected_as_chat(self):
        """Test that regular chat messages are still detected as chat mode."""
        bot = get_ai_chatbot()
        
        # Regular chat should still be chat mode
        mode1 = bot._detect_mode("How are you doing today?")
        assert mode1 == "chat", f"Expected 'chat', got '{mode1}'"
        
        mode2 = bot._detect_mode("I'm feeling good")
        assert mode2 == "chat", f"Expected 'chat', got '{mode2}'"
        
        mode3 = bot._detect_mode("Tell me about yourself")
        assert mode3 == "chat", f"Expected 'chat', got '{mode3}'"

