# bot/interaction_manager.py

"""
Interaction Manager - Main integration layer for user interactions.

This module provides a unified interface for handling user interactions by:
1. Parsing user messages using the enhanced command parser
2. Routing to appropriate interaction handlers
3. Integrating with existing AI chatbot for contextual responses
4. Managing the flow between structured commands and conversational chat
"""

from typing import Optional, Dict, Any
from core.logger import get_logger
from core.error_handling import handle_errors
from bot.enhanced_command_parser import get_enhanced_command_parser, ParsingResult
from bot.interaction_handlers import InteractionResponse, get_interaction_handler, get_all_handlers, ParsedCommand
from bot.ai_chatbot import get_ai_chatbot
from bot.conversation_manager import conversation_manager

logger = get_logger(__name__)

class InteractionManager:
    """Main manager for handling user interactions across all channels"""
    
    def __init__(self):
        self.command_parser = get_enhanced_command_parser()
        self.ai_chatbot = get_ai_chatbot()
        self.interaction_handlers = get_all_handlers()
        
        # Configuration
        self.min_command_confidence = 0.3  # Lowered from 0.6 to catch more commands
        self.enable_ai_enhancement = False  # Temporarily disabled to test raw responses
        self.fallback_to_chat = True        # Whether to fall back to contextual chat
    
    @handle_errors("handling user interaction", default_return=InteractionResponse(
        "I'm having trouble processing your request right now. Please try again in a moment.", True
    ))
    def handle_message(self, user_id: str, message: str, channel_type: str = "discord") -> InteractionResponse:
        """
        Main entry point for handling user messages.
        
        Args:
            user_id: The user's ID
            message: The user's message
            channel_type: Type of channel (discord, email, telegram, etc.)
            
        Returns:
            InteractionResponse with appropriate response
        """
        if not message or not message.strip():
            return InteractionResponse(
                "I didn't receive a message. How can I help you today?",
                True
            )
        
        # Check if user is in an active conversation flow
        user_state = conversation_manager.user_states.get(user_id, {"flow": 0, "state": 0, "data": {}})
        if user_state["flow"] != 0:
            # User is in a flow (like check-in), let conversation manager handle it
            logger.debug(f"User {user_id} in active flow {user_state['flow']}, delegating to conversation manager")
            reply_text, completed = conversation_manager.handle_inbound_message(user_id, message)
            return InteractionResponse(reply_text, completed)
        
        # Parse the message to determine intent
        parsing_result = self.command_parser.parse(message)
        logger.debug(f"Parsed message for user {user_id}: {parsing_result.method} method, "
                    f"intent: {parsing_result.parsed_command.intent}, "
                    f"confidence: {parsing_result.confidence}")
        
        # Handle structured commands
        if parsing_result.confidence >= self.min_command_confidence:
            return self._handle_structured_command(user_id, parsing_result, channel_type)
        
        # Fall back to contextual chat
        if self.fallback_to_chat:
            return self._handle_contextual_chat(user_id, message, channel_type)
        
        # No fallback, return help
        return self._get_help_response(user_id, message)
    
    def _handle_structured_command(self, user_id: str, parsing_result: ParsingResult, channel_type: str) -> InteractionResponse:
        """Handle a structured command using interaction handlers"""
        parsed_command = parsing_result.parsed_command
        intent = parsed_command.intent
        
        # Get the appropriate handler
        handler = get_interaction_handler(intent)
        if not handler:
            logger.warning(f"No handler found for intent: {intent}")
            return InteractionResponse(
                f"I understand you want to {intent}, but I'm not sure how to help with that yet. "
                "Try 'help' to see what I can do!",
                True
            )
        
        # Handle the command
        try:
            response = handler.handle(user_id, parsed_command)
            
            # Enhance response with AI if enabled
            if self.enable_ai_enhancement and self.ai_chatbot.is_ai_available():
                response = self._enhance_response_with_ai(user_id, response, parsed_command)
            
            # Add suggestions if response is incomplete and not a check-in flow
            if not response.completed and not response.suggestions and intent != 'start_checkin':
                response.suggestions = self.command_parser.get_suggestions(parsed_command.original_message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling command {intent} for user {user_id}: {e}")
            return InteractionResponse(
                f"I encountered an error while processing your request. Please try again or ask for help.",
                True
            )
    
    def _handle_contextual_chat(self, user_id: str, message: str, channel_type: str) -> InteractionResponse:
        """Handle contextual chat using AI chatbot"""
        try:
            # Use existing AI chatbot for contextual responses
            response_text = self.ai_chatbot.generate_contextual_response(user_id, message)
            
            # Add suggestions for next actions
            suggestions = self.command_parser.get_suggestions(message)
            
            return InteractionResponse(
                response_text,
                True,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Error in contextual chat for user {user_id}: {e}")
            return InteractionResponse(
                "I'm having trouble with contextual responses right now. "
                "Try using a specific command like 'help' or 'show my tasks'.",
                True
            )
    
    def _enhance_response_with_ai(self, user_id: str, response: InteractionResponse, parsed_command: ParsedCommand) -> InteractionResponse:
        """Enhance a structured response with AI contextual information"""
        try:
            # Create a context prompt for AI enhancement
            context_prompt = f"""
User requested: {parsed_command.original_message}
System response: {response.message}

Please enhance this response to be more personal and contextual for the user, 
while keeping the core information intact. Make it warm and encouraging.
"""
            
            enhanced_text = self.ai_chatbot.generate_response(
                context_prompt,
                user_id=user_id,
                timeout=3  # Short timeout for enhancement
            )
            
            # Only use enhanced response if it's reasonable
            if enhanced_text and len(enhanced_text) > 10:
                response.message = enhanced_text
            
        except Exception as e:
            logger.debug(f"AI enhancement failed: {e}")
            # Keep original response if enhancement fails
        
        return response
    
    def _get_help_response(self, user_id: str, message: str) -> InteractionResponse:
        """Get a help response when command parsing fails"""
        # Try to provide contextual help based on the message
        suggestions = self.command_parser.get_suggestions(message)
        
        help_text = (
            "I'm not sure what you'd like to do. Here are some things you can try:\n\n"
            "📋 **Task Management:**\n"
            "• Create a task: 'I need to call mom tomorrow'\n"
            "• List tasks: 'Show me my tasks'\n"
            "• Complete tasks: 'Complete task 1'\n\n"
            "✅ **Check-ins:**\n"
            "• Start check-in: 'I want to check in'\n"
            "• View history: 'Show my check-ins'\n\n"
            "👤 **Profile:**\n"
            "• View profile: 'Show my profile'\n"
            "• Update info: 'Update my name to Julie'\n\n"
            "Try one of these or ask for 'help' to learn more!"
        )
        
        return InteractionResponse(
            help_text,
            True,
            suggestions=suggestions
        )
    
    def get_available_commands(self, user_id: str) -> Dict[str, Any]:
        """Get list of available commands for the user"""
        commands = {}
        
        for handler_name, handler in self.interaction_handlers.items():
            commands[handler_name] = {
                'help': handler.get_help(),
                'examples': handler.get_examples(),
                'intents': [intent for intent in ['create_task', 'list_tasks', 'complete_task', 'delete_task', 'update_task', 'task_stats', 'start_checkin', 'checkin_status', 'show_profile', 'update_profile', 'profile_stats', 'help', 'commands', 'examples'] if handler.can_handle(intent)]
            }
        
        return commands
    
    def get_user_suggestions(self, user_id: str, context: str = "") -> list:
        """Get personalized suggestions for the user"""
        suggestions = []
        
        # Get task-related suggestions if user has tasks
        try:
            from tasks.task_management import load_active_tasks
            tasks = load_active_tasks(user_id)
            if tasks:
                suggestions.append("Show me my tasks")
                if len(tasks) > 0:
                    suggestions.append(f"Complete task 1")
        
        except Exception:
            pass
        
        # Get check-in suggestions
        try:
            from core.response_tracking import is_user_checkins_enabled
            if is_user_checkins_enabled(user_id):
                suggestions.append("Start a check-in")
                suggestions.append("Show my check-in history")
        except Exception:
            pass
        
        # Add general suggestions
        suggestions.extend([
            "Create a task to call mom tomorrow",
            "Show my profile",
            "Help with tasks"
        ])
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def handle_help_request(self, user_id: str, topic: str = "general") -> InteractionResponse:
        """Handle help requests with topic-specific information"""
        help_handler = get_interaction_handler('help')
        if help_handler:
            # Create a parsed command for help
            from bot.interaction_handlers import ParsedCommand
            parsed_command = ParsedCommand('help', {'topic': topic}, 1.0, f"help {topic}")
            return help_handler.handle(user_id, parsed_command)
        
        # Fallback help
        return InteractionResponse(
            "I'm here to help! Try these commands:\n"
            "• 'help tasks' - Task management help\n"
            "• 'help checkin' - Check-in help\n"
            "• 'help profile' - Profile management help\n"
            "• 'commands' - List all available commands",
            True
        )

# Global instance
_interaction_manager_instance = None

def get_interaction_manager() -> InteractionManager:
    """Get the global interaction manager instance"""
    global _interaction_manager_instance
    if _interaction_manager_instance is None:
        _interaction_manager_instance = InteractionManager()
    return _interaction_manager_instance

def handle_user_message(user_id: str, message: str, channel_type: str = "discord") -> InteractionResponse:
    """Convenience function to handle a user message"""
    manager = get_interaction_manager()
    return manager.handle_message(user_id, message, channel_type) 