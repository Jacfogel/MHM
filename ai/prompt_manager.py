# prompt_manager.py

import os
from typing import Dict, Optional
from dataclasses import dataclass

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.config import AI_SYSTEM_PROMPT_PATH, AI_USE_CUSTOM_PROMPT

# Route prompt manager logs to AI component
prompt_logger = get_component_logger('ai_prompt')
logger = prompt_logger

@dataclass
class PromptTemplate:
    """Template for AI prompts"""
    name: str
    content: str
    description: str
    max_tokens: Optional[int] = None
    temperature: float = 0.7

class PromptManager:
    """Manages AI prompts and templates"""
    
    def __init__(self):
        """Initialize the prompt manager"""
        self._custom_prompt = None
        self._prompt_templates: Dict[str, PromptTemplate] = {}
        self._fallback_prompts = {
            'wellness': PromptTemplate(
                name='wellness',
                content=("You are a supportive wellness assistant. Keep responses helpful, "
                        "encouraging, and under 150 words. Important: You cannot diagnose or treat "
                        "medical conditions. For serious concerns, recommend professional help."),
                description="Default wellness assistant prompt",
                max_tokens=200,
                temperature=0.7
            ),
            'command': PromptTemplate(
                name='command',
                content=("You are a command parser. Your ONLY job is to extract the user's intent and return it as JSON. "
                       "Available actions: create_task, list_tasks, complete_task, delete_task, update_task, task_stats, "
                       "start_checkin, checkin_status, show_profile, update_profile, profile_stats, show_schedule, "
                       "schedule_status, add_schedule_period, show_analytics, mood_trends, habit_analysis, sleep_analysis, "
                       "wellness_score, help, commands, examples, status, messages. "
                       "You MUST respond with ONLY valid JSON in this exact format: "
                       '{"action": "action_name", "details": {}}'),
                description="Command parsing prompt",
                max_tokens=100,
                temperature=0.1
            ),
            'neurodivergent_support': PromptTemplate(
                name='neurodivergent_support',
                content=("You are an AI assistant with the personality and capabilities "
                        "of a calm, loyal, emotionally intelligent companion. Your purpose "
                        "is to support and motivate a neurodivergent user (with ADHD and depression), "
                        "helping them with task switching, emotional regulation, and personal development. "
                        "You are warm but not overbearing, intelligent but humble, and always context-aware. "
                        "Keep responses helpful, encouraging, and under 150 words."),
                description="Neurodivergent support prompt",
                max_tokens=200,
                temperature=0.7
            ),
            'checkin': PromptTemplate(
                name='checkin',
                content=("You are a supportive check-in assistant. Help users reflect on their day "
                        "and track their wellness. Be encouraging and non-judgmental. "
                        "Keep responses concise and supportive."),
                description="Check-in assistant prompt",
                max_tokens=150,
                temperature=0.6
            ),
            'task_assistant': PromptTemplate(
                name='task_assistant',
                content=("You are a helpful task management assistant. Help users organize, "
                        "prioritize, and complete their tasks. Be practical and encouraging. "
                        "Keep responses focused and actionable."),
                description="Task management prompt",
                max_tokens=150,
                temperature=0.5
            )
        }
        
        # Load custom prompt
        self._load_custom_prompt()
    
    @handle_errors("loading custom prompt")
    def _load_custom_prompt(self):
        """Load the custom system prompt from file"""
        if not AI_USE_CUSTOM_PROMPT:
            logger.info("Custom system prompt disabled via configuration")
            return
        
        try:
            if os.path.exists(AI_SYSTEM_PROMPT_PATH):
                with open(AI_SYSTEM_PROMPT_PATH, 'r', encoding='utf-8') as f:
                    self._custom_prompt = f.read().strip()
                logger.info(f"Loaded custom system prompt from {AI_SYSTEM_PROMPT_PATH}")
            else:
                logger.warning(f"Custom system prompt file not found: {AI_SYSTEM_PROMPT_PATH}")
        except Exception as e:
            logger.error(f"Error loading custom system prompt: {e}")
    
    def get_prompt(self, prompt_type: str = 'wellness') -> str:
        """
        Get the appropriate prompt for the given type
        
        Args:
            prompt_type: Type of prompt ('wellness', 'command', 'neurodivergent_support', etc.)
            
        Returns:
            The prompt string
        """
        # If custom prompt is available and type is wellness/neurodivergent_support, use it
        if self._custom_prompt and prompt_type in ['wellness', 'neurodivergent_support']:
            return self._custom_prompt
        
        # Otherwise use fallback prompts
        template = self._fallback_prompts.get(prompt_type)
        if template:
            return template.content
        
        # Default to wellness prompt
        return self._fallback_prompts['wellness'].content
    
    def get_prompt_template(self, prompt_type: str) -> Optional[PromptTemplate]:
        """
        Get the full prompt template for the given type
        
        Args:
            prompt_type: Type of prompt
            
        Returns:
            PromptTemplate object or None if not found
        """
        # Check custom templates first
        if prompt_type in self._prompt_templates:
            return self._prompt_templates[prompt_type]
        
        # Check fallback templates
        return self._fallback_prompts.get(prompt_type)
    
    def add_prompt_template(self, template: PromptTemplate):
        """
        Add a custom prompt template
        
        Args:
            template: PromptTemplate to add
        """
        self._prompt_templates[template.name] = template
        logger.info(f"Added custom prompt template: {template.name}")
    
    def remove_prompt_template(self, prompt_type: str) -> bool:
        """
        Remove a custom prompt template
        
        Args:
            prompt_type: Name of the template to remove
            
        Returns:
            True if template was removed, False if not found
        """
        if prompt_type in self._prompt_templates:
            del self._prompt_templates[prompt_type]
            logger.info(f"Removed custom prompt template: {prompt_type}")
            return True
        return False
    
    def reload_custom_prompt(self):
        """Reload the custom prompt from file (useful for development)"""
        self._load_custom_prompt()
        logger.info("Custom system prompt reloaded")
    
    def get_available_prompts(self) -> Dict[str, str]:
        """
        Get all available prompt types and their descriptions
        
        Returns:
            Dictionary mapping prompt types to descriptions
        """
        prompts = {}
        
        # Add custom templates
        for name, template in self._prompt_templates.items():
            prompts[name] = template.description
        
        # Add fallback templates
        for name, template in self._fallback_prompts.items():
            prompts[name] = template.description
        
        return prompts
    
    def create_contextual_prompt(self, base_prompt: str, context: str, user_input: str) -> str:
        """
        Create a contextual prompt by combining base prompt, context, and user input
        
        Args:
            base_prompt: Base system prompt
            context: Contextual information
            user_input: User's input
            
        Returns:
            Combined contextual prompt
        """
        return f"{base_prompt}\n\nContext: {context}\n\nUser: {user_input}\n\nAssistant:"
    
    def create_task_prompt(self, task_description: str, user_context: str = "") -> str:
        """
        Create a task-specific prompt
        
        Args:
            task_description: Description of the task
            user_context: User context information
            
        Returns:
            Task-specific prompt
        """
        base_prompt = self.get_prompt('task_assistant')
        context = f"Task: {task_description}"
        if user_context:
            context += f"\nUser Context: {user_context}"
        
        return self.create_contextual_prompt(base_prompt, context, "Help me with this task")
    
    def create_checkin_prompt(self, checkin_type: str = "daily", user_context: str = "") -> str:
        """
        Create a check-in specific prompt
        
        Args:
            checkin_type: Type of check-in (daily, weekly, etc.)
            user_context: User context information
            
        Returns:
            Check-in specific prompt
        """
        base_prompt = self.get_prompt('checkin')
        context = f"Check-in Type: {checkin_type}"
        if user_context:
            context += f"\nUser Context: {user_context}"
        
        return self.create_contextual_prompt(base_prompt, context, "Let's do a check-in")

# Global prompt manager instance
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
