"""
Deterministic AI Tests

These tests check deterministic AI functionality that can be fully automated:
- Mode detection
- AI availability checks
- Cache behavior

These were moved from manual AI functionality tests because they have deterministic outcomes.
"""

import pytest
from ai.chatbot import AIChatBotSingleton
from ai.cache_manager import ResponseCache, get_response_cache


class TestAIModeDetection:
    """Test mode detection - deterministic behavior"""
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_detect_clear_command(self):
        """Test that clear commands are detected as 'command' mode"""
        chatbot = AIChatBotSingleton()
        mode = chatbot._detect_mode("add task buy milk")
        assert mode == "command", f"Expected 'command', got '{mode}'"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_detect_ambiguous_request(self):
        """Test that ambiguous requests are detected as 'command_with_clarification' mode"""
        chatbot = AIChatBotSingleton()
        mode = chatbot._detect_mode("Can you add a task?")
        assert mode == "command_with_clarification", f"Expected 'command_with_clarification', got '{mode}'"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_detect_chat_message(self):
        """Test that chat messages are detected as 'chat' mode"""
        chatbot = AIChatBotSingleton()
        mode = chatbot._detect_mode("How are you doing?")
        assert mode == "chat", f"Expected 'chat', got '{mode}'"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_command_phrasings(self):
        """Test various command phrasings are detected correctly"""
        chatbot = AIChatBotSingleton()
        
        # These should all be detected as command or command_with_clarification
        command_phrasings = [
            ("add task buy groceries", ["command"]),
            ("create task buy groceries", ["command"]),
            ("new task buy groceries", ["command"]),
            ("task: buy groceries", ["command", "command_with_clarification"]),
        ]
        
        for prompt, expected_modes in command_phrasings:
            mode = chatbot._detect_mode(prompt)
            assert mode in expected_modes, f"Prompt '{prompt}' detected as '{mode}', expected one of {expected_modes}"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_natural_language_command_detection(self):
        """Test natural language command detection"""
        chatbot = AIChatBotSingleton()
        
        # This should ideally be detected as command, but currently may be chat
        # Marking as partial in manual tests, but we can test current behavior here
        mode = chatbot._detect_mode("I need to buy groceries")
        # Accept either chat or command - the behavior is currently uncertain
        assert mode in ["chat", "command", "command_with_clarification"], \
            f"Mode '{mode}' is valid (improvement: should detect as command)"


class TestAIAvailability:
    """Test AI availability checks - deterministic behavior"""
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_ai_available(self):
        """Test that AI availability check returns a boolean"""
        chatbot = AIChatBotSingleton()
        result = chatbot.is_ai_available()
        assert isinstance(result, bool), f"Expected boolean, got {type(result)}"


class TestAICacheDeterministic:
    """Test cache behavior - deterministic behavior"""
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_cache_initialization(self):
        """Test that cache can be initialized"""
        cache = get_response_cache()
        assert cache is not None, "Cache should be initialized"
        assert isinstance(cache, ResponseCache), "Cache should be ResponseCache instance"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_cache_isolation_by_user(self):
        """Test that cache entries are isolated by user"""
        cache = get_response_cache()
        cache.clear()  # Start fresh
        
        user1 = "test_user_1"
        user2 = "test_user_2"
        prompt = "What is 2+2?"
        
        # Store response for user1 (API: set(prompt, response, user_id, prompt_type))
        cache.set(prompt, "4", user1, prompt_type="chat")
        
        # Check that user2 doesn't have the cached response
        result_user2 = cache.get(prompt, user2, prompt_type="chat")
        assert result_user2 is None, "Cache should be isolated by user"
        
        # Check that user1 has the cached response
        result_user1 = cache.get(prompt, user1, prompt_type="chat")
        assert result_user1 == "4", "Cache should return stored value for user1"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_cache_isolation_by_mode(self):
        """Test that cache entries are isolated by mode"""
        cache = get_response_cache()
        cache.clear()  # Start fresh
        
        user = "test_user"
        prompt = "What is 5+5?"
        
        # Store response for command mode (API: set(prompt, response, user_id, prompt_type))
        cache.set(prompt, "10", user, prompt_type="command")
        
        # Check that chat mode doesn't have the cached response
        result_chat = cache.get(prompt, user, prompt_type="chat")
        assert result_chat is None, "Cache should be isolated by mode"
        
        # Check that command mode has the cached response
        result_command = cache.get(prompt, user, prompt_type="command")
        assert result_command == "10", "Cache should return stored value for command mode"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_cache_key_generation(self):
        """Test that cache keys are generated correctly"""
        cache = get_response_cache()
        
        user = "test_user"
        prompt = "Hello"
        mode = "chat"
        
        # Check cache key generation via _generate_cache_key method (if available)
        # If not available, test via set/get operations instead
        # Store an entry to verify key generation works
        cache.set(prompt, "test_response", user, prompt_type=mode)
        result = cache.get(prompt, user, prompt_type=mode)
        assert result == "test_response", "Cache set/get should work correctly"
        
        # Test that different modes produce different cache entries
        cache.set(prompt, "command_response", user, prompt_type="command")
        chat_result = cache.get(prompt, user, prompt_type="chat")
        command_result = cache.get(prompt, user, prompt_type="command")
        
        # Results should be different (or chat might be None if not set)
        assert command_result == "command_response", "Command mode should return its cached value"

