"""
Unit tests for AI chatbot helper methods.

Tests for ai/chatbot.py focusing on helper methods and utility functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ai.chatbot import get_ai_chatbot


@pytest.fixture(scope="module")
def chatbot_instance():
    """Create chatbot instance once per module (shared across all tests in this file)."""
    # Mock LM Studio connection to avoid actual API calls
    with patch('ai.chatbot.AIChatBotSingleton._test_lm_studio_connection'), \
         patch('ai.lm_studio_manager.is_lm_studio_ready', return_value=False):
        # Get or create singleton instance
        chatbot = get_ai_chatbot()
        chatbot.lm_studio_available = False  # Set to False to avoid actual API calls
        return chatbot


@pytest.mark.unit
@pytest.mark.ai
class TestAIChatBotHelpers:
    """Test helper methods in AIChatBotSingleton."""

    def test_make_cache_key_inputs_valid(self, chatbot_instance):
        """Test _make_cache_key_inputs with valid inputs."""
        result = chatbot_instance._make_cache_key_inputs("chat", "Hello", "user123")
        
        assert isinstance(result, tuple), "Should return tuple"
        assert len(result) == 3, "Should return 3 elements"
        assert result[0] == "Hello", "Should return user_prompt"
        assert result[1] == "user123", "Should return user_id"
        assert result[2] == "chat", "Should return mode"

    def test_make_cache_key_inputs_invalid_mode(self, chatbot_instance):
        """Test _make_cache_key_inputs with invalid mode."""
        # Test None mode
        result = chatbot_instance._make_cache_key_inputs(None, "Hello", "user123")
        assert result == ("", "", ""), "Should return empty tuple for None mode"
        
        # Test non-string mode
        result = chatbot_instance._make_cache_key_inputs(123, "Hello", "user123")
        assert result == ("", "", ""), "Should return empty tuple for non-string mode"

    def test_detect_mode_chat(self, chatbot_instance):
        """Test _detect_mode detects chat mode."""
        # Simple greeting
        result = chatbot_instance._detect_mode("Hello, how are you?")
        assert result == "chat", "Should detect chat mode for greeting"
        
        # Question without command keywords
        result = chatbot_instance._detect_mode("What's the weather like?")
        assert result == "chat", "Should detect chat mode for general question"

    def test_detect_mode_command(self, chatbot_instance):
        """Test _detect_mode detects command mode."""
        # Explicit command with details and detail markers
        result = chatbot_instance._detect_mode("create task to buy groceries for dinner tomorrow")
        assert result in ["command", "command_with_clarification"], "Should detect command mode (or clarification) for create task"
        
        # Command with multiple detail markers - may still need clarification depending on complexity
        result = chatbot_instance._detect_mode("delete task number 5")
        assert result in ["command", "command_with_clarification"], "Should detect command mode (or clarification) for delete task"
        
        # Simple command with clear action
        result = chatbot_instance._detect_mode("schedule appointment with doctor for next week")
        assert result in ["command", "command_with_clarification"], "Should detect command mode (or clarification) for schedule"

    def test_detect_mode_command_with_clarification(self, chatbot_instance):
        """Test _detect_mode detects command_with_clarification mode."""
        # Minimal command
        result = chatbot_instance._detect_mode("remind me")
        assert result == "command_with_clarification", "Should detect clarification needed for minimal command"
        
        # Short command
        result = chatbot_instance._detect_mode("add task")
        assert result == "command_with_clarification", "Should detect clarification needed for short command"
        
        # Question pattern
        result = chatbot_instance._detect_mode("should i create a task?")
        assert result == "command_with_clarification", "Should detect clarification needed for question"

    def test_detect_mode_task_intent_phrases(self, chatbot_instance):
        """Test _detect_mode detects task intent phrases."""
        # Natural language task request
        result = chatbot_instance._detect_mode("I need to buy groceries")
        assert result == "command_with_clarification", "Should detect clarification for natural task request"
        
        # Task intent with verb
        result = chatbot_instance._detect_mode("I want to call mom")
        assert result == "command_with_clarification", "Should detect clarification for task intent"

    def test_detect_mode_empty_prompt(self, chatbot_instance):
        """Test _detect_mode with empty prompt."""
        result = chatbot_instance._detect_mode("")
        assert result == "chat", "Should default to chat for empty prompt"
        
        result = chatbot_instance._detect_mode("   ")
        assert result == "chat", "Should default to chat for whitespace"

    def test_clean_system_prompt_leaks_user_context(self, chatbot_instance):
        """Test _clean_system_prompt_leaks removes user context markers."""
        response = "User Context: Some context here\n\nActual response text"
        result = chatbot_instance._clean_system_prompt_leaks(response)
        
        assert "User Context:" not in result, "Should remove User Context marker"
        assert "Actual response text" in result, "Should keep actual response"

    def test_clean_system_prompt_leaks_important_markers(self, chatbot_instance):
        """Test _clean_system_prompt_leaks removes IMPORTANT markers."""
        response = "IMPORTANT - Feature availability: check-ins enabled\n\nResponse here"
        result = chatbot_instance._clean_system_prompt_leaks(response)
        
        assert "IMPORTANT - Feature availability" not in result, "Should remove IMPORTANT marker"
        assert "Response here" in result, "Should keep actual response"

    def test_clean_system_prompt_leaks_instruction_keywords(self, chatbot_instance):
        """Test _clean_system_prompt_leaks removes instruction keywords."""
        response = "- Use the context to provide meaningful responses\n\nActual response"
        result = chatbot_instance._clean_system_prompt_leaks(response)
        
        assert "Use the context" not in result, "Should remove instruction lines"
        assert "Actual response" in result, "Should keep actual response"

    def test_clean_system_prompt_leaks_feature_availability(self, chatbot_instance):
        """Test _clean_system_prompt_leaks removes feature availability lines."""
        response = "check-ins are disabled - do NOT mention check-ins\n\nResponse text"
        result = chatbot_instance._clean_system_prompt_leaks(response)
        
        assert "check-ins are disabled" not in result, "Should remove feature availability line"
        assert "Response text" in result, "Should keep actual response"

    def test_clean_system_prompt_leaks_no_leaks(self, chatbot_instance):
        """Test _clean_system_prompt_leaks with no leaks."""
        response = "This is a normal response without any system prompt leaks."
        result = chatbot_instance._clean_system_prompt_leaks(response)
        
        assert result == response, "Should return unchanged response when no leaks"

    def test_clean_system_prompt_leaks_empty(self, chatbot_instance):
        """Test _clean_system_prompt_leaks with empty response."""
        result = chatbot_instance._clean_system_prompt_leaks("")
        assert result == "", "Should return empty string for empty input"
        
        result = chatbot_instance._clean_system_prompt_leaks(None)
        assert result is None or result == "", "Should handle None gracefully"

    def test_smart_truncate_response_within_limit(self, chatbot_instance):
        """Test _smart_truncate_response when text is within limit."""
        text = "This is a short response."
        result = chatbot_instance._smart_truncate_response(text, max_chars=100)
        
        assert result == text, "Should return unchanged text when within limit"

    def test_smart_truncate_response_exceeds_chars(self, chatbot_instance):
        """Test _smart_truncate_response when text exceeds character limit."""
        text = "This is a very long response that exceeds the character limit and should be truncated."
        result = chatbot_instance._smart_truncate_response(text, max_chars=30)
        
        assert len(result) <= 30 + 1, "Should truncate to max_chars (plus ellipsis)"
        assert "…" in result or result.endswith("."), "Should add ellipsis or end at sentence"

    def test_smart_truncate_response_with_max_words(self, chatbot_instance):
        """Test _smart_truncate_response with word limit."""
        text = "This is a very long response with many words that should be truncated."
        result = chatbot_instance._smart_truncate_response(text, max_chars=1000, max_words=5)
        
        words = result.split()
        assert len(words) <= 5, "Should respect word limit"
        assert "…" in result, "Should add ellipsis when truncated"

    def test_smart_truncate_response_sentence_boundary(self, chatbot_instance):
        """Test _smart_truncate_response cuts at sentence boundary."""
        text = "First sentence. Second sentence. Third sentence that is very long."
        result = chatbot_instance._smart_truncate_response(text, max_chars=30)
        
        # Should try to cut at sentence boundary
        assert "." in result or "!" in result or "?" in result, "Should cut at sentence boundary when possible"

    def test_extract_command_from_response_json(self, chatbot_instance):
        """Test _extract_command_from_response extracts JSON."""
        response = '{"action": "create_task", "title": "Buy groceries"}'
        result = chatbot_instance._extract_command_from_response(response)
        
        assert "create_task" in result, "Should extract JSON command"
        assert "Buy groceries" in result, "Should include task details"

    def test_extract_command_from_response_key_value(self, chatbot_instance):
        """Test _extract_command_from_response extracts key-value format."""
        response = "ACTION: create_task\nTITLE: Buy groceries\nPRIORITY: high"
        result = chatbot_instance._extract_command_from_response(response)
        
        assert "ACTION: create_task" in result, "Should extract ACTION"
        assert "TITLE: Buy groceries" in result, "Should extract TITLE"
        assert "PRIORITY: high" in result, "Should extract PRIORITY"

    def test_extract_command_from_response_skips_code(self, chatbot_instance):
        """Test _extract_command_from_response skips code blocks."""
        response = "```python\nimport os\n```\nACTION: create_task\nTITLE: Test"
        result = chatbot_instance._extract_command_from_response(response)
        
        assert "import os" not in result, "Should skip code blocks"
        assert "ACTION: create_task" in result, "Should keep command lines"

    def test_extract_command_from_response_empty(self, chatbot_instance):
        """Test _extract_command_from_response with empty response."""
        result = chatbot_instance._extract_command_from_response("")
        assert result == "", "Should return empty string for empty input"
        
        result = chatbot_instance._extract_command_from_response(None)
        assert result == "" or result is None, "Should handle None gracefully"

    def test_extract_command_from_response_natural_language(self, chatbot_instance):
        """Test _extract_command_from_response handles natural language."""
        response = "I want to create a task to buy groceries"
        result = chatbot_instance._extract_command_from_response(response)
        
        # Should return the response as-is or extract what it can
        assert isinstance(result, str), "Should return string"

    def test_optimize_prompt_basic(self, chatbot_instance):
        """Test _optimize_prompt creates basic prompt structure."""
        with patch('ai.chatbot.prompt_manager.get_prompt', return_value="System prompt"):
            result = chatbot_instance._optimize_prompt("Hello")
            
            assert isinstance(result, list), "Should return list"
            assert len(result) == 2, "Should have system and user messages"
            assert result[0]["role"] == "system", "Should have system message"
            assert result[1]["role"] == "user", "Should have user message"

    def test_optimize_prompt_with_context(self, chatbot_instance):
        """Test _optimize_prompt includes context when provided."""
        with patch('ai.chatbot.prompt_manager.get_prompt', return_value="System prompt"):
            result = chatbot_instance._optimize_prompt("Hello", context="User context")
            
            assert "Context:" in result[1]["content"], "Should include context in user message"
            assert "Hello" in result[1]["content"], "Should include user prompt"

    def test_optimize_prompt_context_too_large(self, chatbot_instance):
        """Test _optimize_prompt skips context if too large."""
        large_context = "x" * 300  # Larger than 200 char limit
        with patch('ai.chatbot.prompt_manager.get_prompt', return_value="System prompt"):
            result = chatbot_instance._optimize_prompt("Hello", context=large_context)
            
            assert "Context:" not in result[1]["content"], "Should skip context if too large"
            assert result[1]["content"] == "Hello", "Should only include user prompt"

    def test_get_fallback_personalized_message_with_name(self, chatbot_instance):
        """Test _get_fallback_personalized_message includes user name."""
        with patch('ai.chatbot.get_user_data') as mock_get_data, \
             patch('ai.chatbot.get_recent_responses', return_value=[]):
            mock_get_data.return_value = {
                'context': {
                    'preferred_name': 'TestUser'
                }
            }
            
            result = chatbot_instance._get_fallback_personalized_message("user123")
            
            assert "TestUser" in result, "Should include user name"

    def test_get_fallback_personalized_message_with_mood(self, chatbot_instance):
        """Test _get_fallback_personalized_message adapts to mood."""
        with patch('ai.chatbot.get_user_data') as mock_get_data, \
             patch('ai.chatbot.get_recent_responses') as mock_recent:
            mock_get_data.return_value = {'context': {}}
            mock_recent.return_value = [
                {'mood': 5, 'energy': 5}
            ]
            
            result = chatbot_instance._get_fallback_personalized_message("user123")
            
            assert "doing great" in result.lower() or "positive" in result.lower() or "progress" in result.lower(), "Should adapt to positive mood"

    def test_get_fallback_personalized_message_low_mood(self, chatbot_instance):
        """Test _get_fallback_personalized_message adapts to low mood."""
        with patch('ai.chatbot.get_user_data') as mock_get_data, \
             patch('ai.chatbot.get_recent_responses') as mock_recent:
            mock_get_data.return_value = {'context': {}}
            mock_recent.return_value = [
                {'mood': 1, 'energy': 1}
            ]
            
            result = chatbot_instance._get_fallback_personalized_message("user123")
            
            assert "challenging" in result.lower() or "tough" in result.lower() or "temporary" in result.lower(), "Should adapt to low mood"

    def test_get_fallback_personalized_message_no_data(self, chatbot_instance):
        """Test _get_fallback_personalized_message with no user data."""
        with patch('ai.chatbot.get_user_data', return_value={}), \
             patch('ai.chatbot.get_recent_responses', return_value=[]):
            
            result = chatbot_instance._get_fallback_personalized_message("user123")
            
            assert isinstance(result, str), "Should return string"
            assert len(result) > 0, "Should return non-empty message"

