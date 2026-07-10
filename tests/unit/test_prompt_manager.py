"""
Prompt Manager Test Coverage Expansion

This module provides comprehensive test coverage for ai/prompt_manager.py.
Focuses on real behavior testing to verify actual side effects and system changes.

Coverage Areas:
- PromptManager initialization
- Custom prompt loading
- Prompt retrieval (get_prompt, get_prompt_template)
- Prompt template management (add, remove)
- Contextual prompt creation
- Error handling and edge cases
"""

import pytest
from unittest.mock import patch, mock_open

from ai.prompts.manager import (
    PromptManager,
    PromptTemplate,
    get_persona_prompt_text,
    get_prompt_manager,
    MINIMAL_CHAT_SYSTEM_PROMPT,
)


pytestmark = [pytest.mark.ai]

@pytest.mark.unit
@pytest.mark.ai
class TestPromptManager:
    """Comprehensive test coverage for PromptManager class."""
    
    @pytest.fixture
    def temp_prompt_file(self, tmp_path):
        """Create a temporary prompt file."""
        prompt_file = tmp_path / "custom_prompt.txt"
        prompt_file.write_text("Custom system prompt content")
        return str(prompt_file)
    
    @pytest.fixture
    def prompt_manager(self):
        """Create a PromptManager instance."""
        with patch('ai.prompts.manager.AI_USE_CUSTOM_PROMPT', False):
            return PromptManager()
    
    def test_prompt_manager_initialization_real_behavior(self):
        """Test PromptManager initialization."""
        with patch('ai.prompts.manager.AI_USE_CUSTOM_PROMPT', False):
            manager = PromptManager()
            
            assert manager._custom_prompt is None
            assert isinstance(manager._prompt_templates, dict)
            assert len(manager._fallback_prompts) > 0
            assert 'chat_response' in manager._fallback_prompts
            assert 'command' in manager._fallback_prompts
    
    def test_prompt_manager_initialization_with_custom_prompt_disabled_real_behavior(self, temp_prompt_file):
        """Test initialization when custom prompt is disabled."""
        with patch('ai.prompts.manager.AI_USE_CUSTOM_PROMPT', False), \
             patch('ai.prompts.manager.AI_SYSTEM_PROMPT_PATH', temp_prompt_file):
            manager = PromptManager()
            
            # Custom prompt should not be loaded when disabled
            assert manager._custom_prompt is None
    
    def test_load_custom_prompt_file_exists_real_behavior(self, temp_prompt_file):
        """Test loading custom prompt when file exists."""
        with patch('ai.prompts.manager.AI_USE_CUSTOM_PROMPT', True), \
             patch('ai.prompts.manager.AI_SYSTEM_PROMPT_PATH', temp_prompt_file), \
             patch('builtins.open', mock_open(read_data="Custom prompt content")):
            manager = PromptManager()
            
            # Custom prompt should be loaded
            assert manager._custom_prompt == "Custom prompt content"
    
    def test_load_custom_prompt_file_not_exists_real_behavior(self, tmp_path):
        """Test loading custom prompt when file doesn't exist."""
        non_existent_file = str(tmp_path / "nonexistent.txt")
        
        with patch('ai.prompts.manager.AI_USE_CUSTOM_PROMPT', True), \
             patch('ai.prompts.manager.AI_SYSTEM_PROMPT_PATH', non_existent_file):
            manager = PromptManager()
            
            # Custom prompt should be None when file doesn't exist
            assert manager._custom_prompt is None
    
    def test_load_custom_prompt_error_handling_real_behavior(self, temp_prompt_file):
        """Test error handling when loading custom prompt fails."""
        with patch('ai.prompts.manager.AI_USE_CUSTOM_PROMPT', True), \
             patch('ai.prompts.manager.AI_SYSTEM_PROMPT_PATH', temp_prompt_file), \
             patch('builtins.open', side_effect=PermissionError("Access denied")):
            manager = PromptManager()
            
            # Should handle error gracefully
            assert manager._custom_prompt is None
    
    def test_get_prompt_persona_alias_real_behavior(self, prompt_manager):
        """Wellness alias routes to persona prompt text."""
        prompt = prompt_manager.get_prompt('wellness')
        assert prompt == get_persona_prompt_text()

    def test_get_persona_prompt_text_loads_canonical_persona(self):
        """Persona helper returns category file text, not composed chat prompt."""
        persona = get_persona_prompt_text()
        assert isinstance(persona, str)
        assert len(persona) > 0
        assert "MHM" in persona or "supportive" in persona.lower()
        assert MINIMAL_CHAT_SYSTEM_PROMPT
        assert "supportive" in MINIMAL_CHAT_SYSTEM_PROMPT.lower()
    
    def test_get_prompt_command_type_real_behavior(self, prompt_manager):
        """Test getting command prompt."""
        prompt = prompt_manager.get_prompt('command')
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert 'command parser' in prompt.lower() or 'extract' in prompt.lower()
    
    def test_get_prompt_custom_persona_override_real_behavior(self, temp_prompt_file):
        """Custom override file is reflected in get_persona_prompt_text."""
        from pathlib import Path

        custom_content = "Custom wellness prompt"
        Path(temp_prompt_file).write_text(custom_content, encoding="utf-8")

        with patch('ai.prompts.manager.AI_USE_CUSTOM_PROMPT', True), \
             patch('ai.prompts.manager.AI_SYSTEM_PROMPT_PATH', temp_prompt_file):
            prompt = get_persona_prompt_text()

            assert prompt == custom_content
    
    def test_get_prompt_neurodivergent_alias_real_behavior(self, temp_prompt_file):
        """Neurodivergent alias routes to persona prompt text."""
        with patch('ai.prompts.manager.AI_USE_CUSTOM_PROMPT', False):
            manager = PromptManager()
            prompt = manager.get_prompt('neurodivergent_support')
            assert prompt == get_persona_prompt_text()
    
    def test_get_prompt_custom_prompt_not_used_for_command_real_behavior(self, temp_prompt_file):
        """Test that custom prompt is not used for command type."""
        custom_content = "Custom prompt"
        
        with patch('ai.prompts.manager.AI_USE_CUSTOM_PROMPT', True), \
             patch('ai.prompts.manager.AI_SYSTEM_PROMPT_PATH', temp_prompt_file), \
             patch('builtins.open', mock_open(read_data=custom_content)):
            manager = PromptManager()
            prompt = manager.get_prompt('command')
            
            # Should use fallback, not custom
            assert prompt != custom_content
            assert 'command parser' in prompt.lower() or 'extract' in prompt.lower()
    
    def test_get_prompt_unknown_type_real_behavior(self, prompt_manager):
        """Test getting prompt for unknown type defaults to wellness."""
        prompt = prompt_manager.get_prompt('unknown_type')
        
        # Should default to persona prompt text
        assert isinstance(prompt, str)
        assert prompt == get_persona_prompt_text()
    
    def test_get_prompt_error_handling_real_behavior(self):
        """Test get_prompt error handling."""
        with patch('ai.prompts.manager.AI_USE_CUSTOM_PROMPT', False):
            manager = PromptManager()
            # Simulate error accessing fallback prompts
            original_fallbacks = manager._fallback_prompts
            manager._fallback_prompts = {}
            
            try:
                prompt = manager.get_prompt('wellness')
                # Should return default fallback string due to @handle_errors decorator
                assert isinstance(prompt, str)
                assert len(prompt) > 0
            finally:
                manager._fallback_prompts = original_fallbacks
    
    def test_get_prompt_template_existing_fallback_real_behavior(self, prompt_manager):
        """Test getting existing fallback template."""
        template = prompt_manager.get_prompt_template('chat_response')
        
        assert template is not None
        assert isinstance(template, PromptTemplate)
        assert template.name == 'chat_response'
        assert len(template.content) > 0
    
    def test_get_prompt_template_custom_template_real_behavior(self, prompt_manager):
        """Test getting custom template."""
        custom_template = PromptTemplate(
            name='custom',
            content='Custom content',
            description='Custom description'
        )
        prompt_manager.add_prompt_template(custom_template)
        
        template = prompt_manager.get_prompt_template('custom')
        
        assert template is not None
        assert template == custom_template
    
    def test_get_prompt_template_custom_overrides_fallback_real_behavior(self, prompt_manager):
        """Test that custom template overrides fallback."""
        custom_template = PromptTemplate(
            name='chat_response',
            content='Custom chat response content',
            description='Custom description'
        )
        prompt_manager.add_prompt_template(custom_template)
        
        template = prompt_manager.get_prompt_template('chat_response')
        
        # Should return custom template, not fallback
        assert template == custom_template
        assert template.content == 'Custom chat response content'
    
    def test_get_prompt_template_not_found_real_behavior(self, prompt_manager):
        """Test getting template that doesn't exist."""
        template = prompt_manager.get_prompt_template('nonexistent')
        
        assert template is None
    
    def test_get_prompt_template_error_handling_real_behavior(self, prompt_manager):
        """Test get_prompt_template error handling."""
        # Simulate error accessing custom templates
        original_templates = prompt_manager._prompt_templates
        prompt_manager._prompt_templates = None
        
        try:
            template = prompt_manager.get_prompt_template('chat_response')
            # Should return None on error due to @handle_errors decorator
            assert template is None
        finally:
            prompt_manager._prompt_templates = original_templates
    
    def test_add_prompt_template_real_behavior(self, prompt_manager):
        """Test adding a custom prompt template."""
        template = PromptTemplate(
            name='test_template',
            content='Test content',
            description='Test description',
            max_tokens=100,
            temperature=0.5
        )
        
        result = prompt_manager.add_prompt_template(template)
        
        # Should return True (no error)
        assert result is not False
        assert 'test_template' in prompt_manager._prompt_templates
        assert prompt_manager._prompt_templates['test_template'] == template
    
    def test_add_prompt_template_overwrites_existing_real_behavior(self, prompt_manager):
        """Test that adding template overwrites existing one."""
        template1 = PromptTemplate(
            name='test',
            content='Content 1',
            description='Description 1'
        )
        template2 = PromptTemplate(
            name='test',
            content='Content 2',
            description='Description 2'
        )
        
        prompt_manager.add_prompt_template(template1)
        prompt_manager.add_prompt_template(template2)
        
        # Should have only one template with latest content
        assert len(prompt_manager._prompt_templates) == 1
        assert prompt_manager._prompt_templates['test'].content == 'Content 2'
    
    def test_add_prompt_template_error_handling_real_behavior(self, prompt_manager):
        """Test add_prompt_template error handling."""
        template = PromptTemplate(
            name='test',
            content='Content',
            description='Description'
        )
        
        # The function doesn't return a value, so we test that it doesn't raise
        # Simulate error accessing _prompt_templates
        original_templates = prompt_manager._prompt_templates
        prompt_manager._prompt_templates = None
        
        # Should not raise exception due to @handle_errors decorator
        try:
            result = prompt_manager.add_prompt_template(template)
            # Function may return None or not return anything
            assert result is None or result is False
        finally:
            prompt_manager._prompt_templates = original_templates
    
    def test_remove_prompt_template_existing_real_behavior(self, prompt_manager):
        """Test removing an existing custom template."""
        template = PromptTemplate(
            name='test',
            content='Content',
            description='Description'
        )
        prompt_manager.add_prompt_template(template)
        
        result = prompt_manager.remove_prompt_template('test')
        
        assert result is True
        assert 'test' not in prompt_manager._prompt_templates
    
    def test_remove_prompt_template_not_found_real_behavior(self, prompt_manager):
        """Test removing a template that doesn't exist."""
        result = prompt_manager.remove_prompt_template('nonexistent')
        
        assert result is False
    
    def test_remove_prompt_template_error_handling_real_behavior(self, prompt_manager):
        """Test remove_prompt_template error handling."""
        template = PromptTemplate(
            name='test',
            content='Content',
            description='Description'
        )
        prompt_manager.add_prompt_template(template)
        
        # Simulate error
        with patch.object(prompt_manager, '_prompt_templates', side_effect=Exception("Error")):
            result = prompt_manager.remove_prompt_template('test')
            # Should return False on error due to @handle_errors decorator
            assert result is False
    
    def test_reload_custom_prompt_real_behavior(self, temp_prompt_file):
        """Test reloading custom prompt."""
        initial_content = "Initial content"
        updated_content = "Updated content"
        
        with patch('ai.prompts.manager.AI_USE_CUSTOM_PROMPT', True), \
             patch('ai.prompts.manager.AI_SYSTEM_PROMPT_PATH', temp_prompt_file):
            # Create manager with initial content
            with patch('builtins.open', mock_open(read_data=initial_content)):
                manager = PromptManager()
                assert manager._custom_prompt == initial_content
            
            # Reload with updated content
            with patch('builtins.open', mock_open(read_data=updated_content)):
                manager.reload_custom_prompt()
                assert manager._custom_prompt == updated_content
    
    def test_reload_custom_prompt_error_handling_real_behavior(self, prompt_manager):
        """Test reload_custom_prompt error handling."""
        # Simulate error in _load_custom_prompt
        with patch.object(prompt_manager, '_load_custom_prompt', side_effect=Exception("Error")):
            result = prompt_manager.reload_custom_prompt()
            # Should return False on error due to @handle_errors decorator
            assert result is False
    
    def test_has_custom_prompt_true_real_behavior(self, temp_prompt_file):
        """Test has_custom_prompt returns True when custom prompt exists."""
        with patch('ai.prompts.manager.AI_USE_CUSTOM_PROMPT', True), \
             patch('ai.prompts.manager.AI_SYSTEM_PROMPT_PATH', temp_prompt_file), \
             patch('builtins.open', mock_open(read_data="Custom prompt")):
            manager = PromptManager()
            
            assert manager.has_custom_prompt() is True
    
    def test_has_custom_prompt_false_real_behavior(self, prompt_manager):
        """Test has_custom_prompt returns False when no custom prompt."""
        assert prompt_manager.has_custom_prompt() is False
    
    def test_has_custom_prompt_error_handling_real_behavior(self, prompt_manager):
        """Test has_custom_prompt with None custom prompt."""
        # Set custom prompt to None explicitly
        prompt_manager._custom_prompt = None
        result = prompt_manager.has_custom_prompt()
        # Should return False when custom prompt is None
        assert result is False
    
    def test_custom_prompt_length_with_prompt_real_behavior(self, temp_prompt_file):
        """Test custom_prompt_length returns correct length."""
        prompt_content = "Custom prompt content"
        
        with patch('ai.prompts.manager.AI_USE_CUSTOM_PROMPT', True), \
             patch('ai.prompts.manager.AI_SYSTEM_PROMPT_PATH', temp_prompt_file), \
             patch('builtins.open', mock_open(read_data=prompt_content)):
            manager = PromptManager()
            
            assert manager.custom_prompt_length() == len(prompt_content)
    
    def test_custom_prompt_length_no_prompt_real_behavior(self, prompt_manager):
        """Test custom_prompt_length returns 0 when no custom prompt."""
        assert prompt_manager.custom_prompt_length() == 0
    
    def test_custom_prompt_length_error_handling_real_behavior(self, prompt_manager):
        """Test custom_prompt_length error handling."""
        # Simulate error
        with patch.object(prompt_manager, '_custom_prompt', side_effect=Exception("Error")):
            result = prompt_manager.custom_prompt_length()
            # Should return 0 on error due to @handle_errors decorator
            assert result == 0
    
    def test_fallback_prompt_keys_real_behavior(self, prompt_manager):
        """Test fallback_prompt_keys returns list of keys."""
        keys = prompt_manager.fallback_prompt_keys()
        
        assert isinstance(keys, list)
        assert len(keys) > 0
        assert 'chat_response' in keys
        assert 'command' in keys
    
    def test_fallback_prompt_keys_error_handling_real_behavior(self, prompt_manager):
        """Test fallback_prompt_keys error handling."""
        # Simulate error
        with patch.object(prompt_manager, '_fallback_prompts', side_effect=Exception("Error")):
            result = prompt_manager.fallback_prompt_keys()
            # Should return empty list on error due to @handle_errors decorator
            assert result == []
    
    def test_get_available_prompts_real_behavior(self, prompt_manager):
        """Test getting all available prompts."""
        # Add a custom template
        custom_template = PromptTemplate(
            name='custom',
            content='Content',
            description='Custom description'
        )
        prompt_manager.add_prompt_template(custom_template)
        
        prompts = prompt_manager.get_available_prompts()
        
        assert isinstance(prompts, dict)
        assert 'custom' in prompts
        assert 'chat_response' in prompts
        assert 'command' in prompts
        assert prompts['custom'] == 'Custom description'
    
    def test_get_available_prompts_only_fallbacks_real_behavior(self, prompt_manager):
        """Test getting available prompts with only fallbacks."""
        prompts = prompt_manager.get_available_prompts()
        
        assert isinstance(prompts, dict)
        assert len(prompts) > 0
        assert 'chat_response' in prompts
    
    def test_get_available_prompts_error_handling_real_behavior(self, prompt_manager):
        """Test get_available_prompts error handling."""
        # Simulate error accessing _prompt_templates
        original_templates = prompt_manager._prompt_templates
        prompt_manager._prompt_templates = None
        
        try:
            result = prompt_manager.get_available_prompts()
            # Should return empty dict on error due to @handle_errors decorator
            assert result == {}
        finally:
            prompt_manager._prompt_templates = original_templates
    
    def test_create_contextual_prompt_real_behavior(self, prompt_manager):
        """Test creating contextual prompt."""
        base = "Base prompt"
        context = "User context"
        user_input = "User question"
        
        result = prompt_manager.create_contextual_prompt(base, context, user_input)
        
        assert isinstance(result, str)
        assert base in result
        assert context in result
        assert user_input in result
        assert "Context:" in result
        assert "User:" in result
        assert "Assistant:" in result
    
    def test_create_contextual_prompt_empty_context_real_behavior(self, prompt_manager):
        """Test creating contextual prompt with empty context."""
        base = "Base prompt"
        context = ""
        user_input = "User question"
        
        result = prompt_manager.create_contextual_prompt(base, context, user_input)
        
        assert isinstance(result, str)
        assert base in result
        assert user_input in result
    
    def test_create_contextual_prompt_error_handling_real_behavior(self, prompt_manager):
        """Test create_contextual_prompt error handling."""
        # Avoid patching builtins.len (breaks unittest.mock internals); fail on debug log instead
        with patch("ai.prompts.manager.logger.debug", side_effect=Exception("Error")):
            result = prompt_manager.create_contextual_prompt("base", "context", "input")
            # Should return empty string on error due to @handle_errors decorator
            assert result == ""

    def test_compose_product_prompt_chat_response_real_behavior(self, prompt_manager):
        """Test compose_product_prompt for chat_response flow."""
        template = prompt_manager.compose_product_prompt(
            "chat_response",
            context_view={"prompt_text": "User Context:\ntasks enabled"},
        )

        assert template is not None
        assert template.name == "product_ai_chat_response"
        assert "[persona]" in template.content
        assert "tasks enabled" in template.content
    
    def test_get_prompt_manager_singleton_real_behavior(self):
        """Test that get_prompt_manager returns singleton instance."""
        # Reset global instance
        import ai.prompts.manager
        ai.prompts.manager._prompt_manager = None
        
        manager1 = get_prompt_manager()
        manager2 = get_prompt_manager()
        
        # Should return same instance
        assert manager1 is manager2
        assert isinstance(manager1, PromptManager)
    
    def test_get_prompt_manager_error_handling_real_behavior(self):
        """Test get_prompt_manager error handling."""
        # Reset global instance
        import ai.prompts.manager
        ai.prompts.manager._prompt_manager = None
        
        # Simulate error in PromptManager initialization
        with patch('ai.prompts.manager.PromptManager', side_effect=Exception("Error")):
            result = get_prompt_manager()
            # Should return None on error due to @handle_errors decorator
            assert result is None
    
    def test_prompt_template_dataclass_real_behavior(self):
        """Test PromptTemplate dataclass."""
        template = PromptTemplate(
            name='test',
            content='Content',
            description='Description',
            max_tokens=100,
            temperature=0.5
        )
        
        assert template.name == 'test'
        assert template.content == 'Content'
        assert template.description == 'Description'
        assert template.max_tokens == 100
        assert template.temperature == 0.5
    
    def test_prompt_template_default_values_real_behavior(self):
        """Test PromptTemplate with default values."""
        template = PromptTemplate(
            name='test',
            content='Content',
            description='Description'
        )
        
        assert template.max_tokens is None
        assert template.temperature == 0.7

