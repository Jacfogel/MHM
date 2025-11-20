# communication/message_processing/interaction_manager.py

"""
Interaction Manager - Main integration layer for user interactions.

This module provides a unified interface for handling user interactions by:
1. Parsing user messages using the enhanced command parser
2. Routing to appropriate interaction handlers
3. Integrating with existing AI chatbot for contextual responses
4. Managing the flow between structured commands and conversational chat
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.config import AI_MAX_RESPONSE_LENGTH
from communication.message_processing.command_parser import get_enhanced_command_parser, ParsingResult
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from communication.command_handlers.interaction_handlers import get_interaction_handler, get_all_handlers
from ai.chatbot import get_ai_chatbot
from communication.message_processing.conversation_flow_manager import conversation_manager

logger = get_component_logger('communication_manager')
interaction_logger = logger


@dataclass
class CommandDefinition:
    name: str
    mapped_message: str
    description: str
    is_flow: bool = False

class InteractionManager:
    """Main manager for handling user interactions across all channels"""
    
    @handle_errors("initializing interaction manager")
    def __init__(self):
        try:
            self.command_parser = get_enhanced_command_parser()
            self.ai_chatbot = get_ai_chatbot()
            self.interaction_handlers = get_all_handlers()
            
            # Configuration
            self.min_command_confidence = 0.3  # Lowered from 0.6 to catch more commands
            self.enable_ai_enhancement = True   # Enable AI enhancement for better command parsing
            self.fallback_to_chat = True        # Whether to fall back to contextual chat
            
            # Channel-agnostic command definitions for discoverability across channels
            self._command_definitions: List[CommandDefinition] = [
            CommandDefinition("start", "start", "Get started with MHM - receive welcome message and setup instructions", is_flow=False),
            CommandDefinition("tasks", "show my tasks", "Show your tasks", is_flow=False),
            CommandDefinition("profile", "show profile", "Show your profile", is_flow=False),
            CommandDefinition("schedule", "show schedule", "Show your schedules", is_flow=False),
            CommandDefinition("messages", "show messages", "Show your messages", is_flow=False),
            CommandDefinition("analytics", "show analytics", "Show wellness analytics and insights", is_flow=False),
            CommandDefinition("status", "status", "Show system/user status", is_flow=False),
            CommandDefinition("help", "help", "Show help and examples", is_flow=False),
            CommandDefinition("checkin", "start checkin", "Start a check-in", is_flow=True),
            CommandDefinition("restart", "restart checkin", "Restart check-in (clears current)", is_flow=True),
            CommandDefinition("clear", "clear flows", "Clear stuck conversation flows", is_flow=True),
            CommandDefinition("cancel", "/cancel", "Cancel current flow", is_flow=False),
            ]

            # Build the legacy map for quick lookup, derived from definitions
            self.slash_command_map = {f"/{c.name}": c.mapped_message for c in self._command_definitions}
        except Exception as e:
            logger.error(f"Error initializing interaction manager: {e}")
            raise
    
    @handle_errors("handling user interaction", default_return=InteractionResponse(
        "I'm having trouble processing your request right now. Please try again in a moment.", True
    ))
    def handle_message(self, user_id: str, message: str, channel_type: str = "discord") -> InteractionResponse:
        """
        Main entry point for handling user messages.
        
        Args:
            user_id: The user's ID
            message: The user's message
            channel_type: Type of channel (discord, email)
            
        Returns:
            InteractionResponse with appropriate response
        """
        if not message or not message.strip():
            return InteractionResponse(
                "I didn't receive a message. How can I help you today?",
                True
            )
        
        # Handle explicit slash-commands first to preserve legacy flow behavior
        message_stripped = message.strip() if message else ""
        logger.info(f"COMMAND_DETECTION: Processing message '{message_stripped[:50]}...' for user {user_id}")
        # Optional prefix processing for channel-agnostic handling
        if message_stripped.startswith("/"):
            logger.info(f"SLASH_COMMAND: Detected slash command '{message_stripped}' for user {user_id}")
            lowered = message_stripped.lower()
            # Extract the command name after '/'
            parts = lowered.split()
            cmd_name = parts[0][1:] if parts and parts[0].startswith('/') else ''

            # /cancel remains universal and handled by conversation manager
            if cmd_name == 'cancel':
                reply_text, completed = conversation_manager.handle_inbound_message(user_id, '/cancel')
                return InteractionResponse(reply_text, completed)

            # Look up command definition
            cmd_def = next((c for c in self._command_definitions if c.name == cmd_name), None)

            # Flow-marked commands delegate to conversation manager starters
            if cmd_def and cmd_def.is_flow:
                if cmd_name == 'checkin':
                    reply_text, completed = conversation_manager.start_checkin(user_id)
                    return InteractionResponse(reply_text, completed)
                elif cmd_name == 'restart':
                    reply_text, completed = conversation_manager.restart_checkin(user_id)
                    return InteractionResponse(reply_text, completed)
                elif cmd_name == 'clear':
                    reply_text, completed = conversation_manager.clear_stuck_flows(user_id)
                    return InteractionResponse(reply_text, completed)
                starter_name = f'start_{cmd_name}_flow'
                starter_fn = getattr(conversation_manager, starter_name, None)
                if callable(starter_fn):
                    reply_text, completed = starter_fn(user_id)
                    return InteractionResponse(reply_text, completed)
                else:
                    return InteractionResponse(f"Flow '{cmd_name}' is not available yet.", True)

            # Otherwise, map to single-turn intent via mapped message
            for key, mapped in self.slash_command_map.items():
                if lowered == key or lowered.startswith(key + ' '):
                    return self.handle_message(user_id, mapped, channel_type)

            # Unknown slash command → drop prefix and continue to structured parsing below
            message = message_stripped[1:]

        elif message_stripped.startswith("!"):
            # Handle bang-prefixed commands (like !tasks, !help, etc.)
            logger.info(f"BANG_COMMAND: Detected bang command '{message_stripped}' for user {user_id}")
            lowered = message_stripped.lower()
            # Extract the command name after '!'
            parts = lowered.split()
            cmd_name = parts[0][1:] if parts and parts[0].startswith('!') else ''

            # Look up command definition
            cmd_def = next((c for c in self._command_definitions if c.name == cmd_name), None)

            # Flow-marked commands delegate to conversation manager starters
            if cmd_def and cmd_def.is_flow:
                if cmd_name == 'checkin':
                    reply_text, completed = conversation_manager.start_checkin(user_id)
                    return InteractionResponse(reply_text, completed)
                elif cmd_name == 'restart':
                    reply_text, completed = conversation_manager.restart_checkin(user_id)
                    return InteractionResponse(reply_text, completed)
                elif cmd_name == 'clear':
                    reply_text, completed = conversation_manager.clear_stuck_flows(user_id)
                    return InteractionResponse(reply_text, completed)
                starter_name = f'start_{cmd_name}_flow'
                starter_fn = getattr(conversation_manager, starter_name, None)
                if callable(starter_fn):
                    reply_text, completed = starter_fn(user_id)
                    return InteractionResponse(reply_text, completed)
                else:
                    return InteractionResponse(f"Flow '{cmd_name}' is not available yet.", True)

            # For non-flow commands, handle them directly using the mapped message
            elif cmd_def:
                return self.handle_message(user_id, cmd_def.mapped_message, channel_type)

            # Unknown bang command → drop prefix and continue to structured parsing below
            message = message_stripped[1:]

        # Check if user is in an active conversation flow
        user_state = conversation_manager.user_states.get(user_id, {"flow": 0, "state": 0, "data": {}})
        logger.info(f"FLOW_CHECK: User {user_id} flow state: {user_state.get('flow', 'None')} (type: {type(user_state.get('flow'))})")
        if user_state["flow"] != 0:
            # User is in a flow, but check if they're trying to issue a command
            # Commands should bypass the flow and be processed normally
            message_lower = message.strip().lower()
            command_keywords = ['update task', 'complete task', 'delete task', 'show tasks', 'list tasks', 
                               'create task', 'add task', 'new task', '/cancel', 'cancel']
            is_command = any(message_lower.startswith(keyword) for keyword in command_keywords)
            
            if is_command:
                # User is issuing a command, clear the flow and process the command
                logger.info(f"User {user_id} in flow {user_state['flow']} but issued command, clearing flow and processing command")
                conversation_manager.user_states.pop(user_id, None)
                conversation_manager._save_user_states()
            else:
                # User is in a flow and not issuing a command, let conversation manager handle it
                logger.info(f"User {user_id} in active flow {user_state['flow']}, delegating to conversation manager")
                reply_text, completed = conversation_manager.handle_inbound_message(user_id, message)
                return InteractionResponse(reply_text, completed)
        
        logger.info(f"User {user_id} not in active flow or command detected, proceeding with command parsing")
        
        # Simple confirm-delete shortcut: bypass parsing
        if message.strip().lower() == "confirm delete":
            try:
                from communication.command_handlers.interaction_handlers import TaskManagementHandler
                from communication.command_handlers.shared_types import ParsedCommand
                handler = TaskManagementHandler()
                resp = handler._handle_delete_task(user_id, {"task_identifier": None})
                return self._augment_suggestions(ParsedCommand('delete_task', {}, 1.0, message), resp)
            except Exception:
                pass

        # Simple complete-task prompt shortcut (no identifier provided)
        if message.strip().lower() == "complete task":
            try:
                from communication.command_handlers.interaction_handlers import TaskManagementHandler
                from communication.command_handlers.shared_types import ParsedCommand
                handler = TaskManagementHandler()
                resp = handler._handle_complete_task(user_id, {})
                return self._augment_suggestions(ParsedCommand('complete_task', {}, 1.0, message), resp)
            except Exception:
                pass

        # Schedule edit shortcut: recognize edit period without times and coerce intent
        try:
            import re
            low = message.lower().strip()
            m1 = re.search(r'^edit\s+schedule\s+period\s+([\w\-]+)\s+(tasks?|check.?ins?|messages?)', low, re.IGNORECASE)
            m2 = re.search(r'^edit\s+(?:the\s+)?([\w\-]+)\s+period\s+in\s+my\s+(tasks?|check.?ins?|messages?)\s+schedule', low, re.IGNORECASE)
            m = m1 or m2
            if m:
                period_name = m.group(1)
                category = m.group(2)
                from communication.command_handlers.shared_types import ParsedCommand
                from communication.message_processing.command_parser import ParsingResult
                parsed_cmd = ParsedCommand('edit_schedule_period', {'period_name': period_name, 'category': category}, 0.95, message)
                parsing_result = ParsingResult(parsed_command=parsed_cmd, confidence=0.95, method='rule_based')
                resp = self._handle_structured_command(user_id, parsing_result, channel_type)
                return self._augment_suggestions(parsed_cmd, resp)
        except Exception:
            pass

        # Parse the message to determine intent
        parsing_result = self.command_parser.parse(message, user_id)

        # Safety: if user clearly asked to update a task but parser was unsure, coerce minimal entities
        try:
            if parsing_result.parsed_command.intent == 'unknown' and message.lower().strip().startswith('update task'):
                import re
                coerced_entities = {}
                # identifier right after 'update task' - extract number or first word/phrase
                # Match: "update task <identifier>" where identifier is a number or word(s) before field keywords
                # For "update task 1 priority high", we want identifier="1"
                m_id = re.search(r'^update\s+task\s+(\d+|\w+)(?=\s+(?:title|priority|due|description)|$)', message, re.IGNORECASE)
                if m_id:
                    ident = m_id.group(1).strip().strip('"')
                    coerced_entities['task_identifier'] = ident
                # fields
                m_due = re.search(r'(?:due\s+date|due)\s+(.+)', message, re.IGNORECASE)
                if m_due:
                    coerced_entities['due_date'] = m_due.group(1).strip()
                m_pri = re.search(r'priority\s+(?:to\s+)?(high|medium|low|urgent|critical)', message, re.IGNORECASE)
                if m_pri:
                    coerced_entities['priority'] = m_pri.group(1).lower()
                m_title = re.search(r'(?:title\s+"([^"]+)"|title\s+([^\n]+)|rename\s+(?:task\s+)?(?:to\s+)?"?([^"\n]+)"?)', message, re.IGNORECASE)
                if m_title:
                    new_title = m_title.group(1) or m_title.group(2) or m_title.group(3)
                    if new_title:
                        coerced_entities['title'] = new_title.strip()
                if coerced_entities.get('task_identifier') and any(k in coerced_entities for k in ['due_date','priority','title']):
                    from communication.command_handlers.shared_types import ParsedCommand
                    parsing_result.parsed_command = ParsedCommand('update_task', coerced_entities, 0.9, message)
                    parsing_result.confidence = 0.9
        except Exception:
            pass
        logger.info(f"INTERACTION_MANAGER: Parsed message for user {user_id}: {parsing_result.method} method, "
                    f"intent: {parsing_result.parsed_command.intent}, "
                    f"confidence: {parsing_result.confidence}")
        
        # Handle structured commands
        if parsing_result.confidence >= self.min_command_confidence:
            # Guard against misclassification: "update task ..." should never be treated as completion
            try:
                low_msg = message.lower().strip()
                if low_msg.startswith('update task'):
                    from communication.command_handlers.shared_types import ParsedCommand
                    # Build minimal entities if needed
                    import re
                    coerced_entities = parsing_result.parsed_command.entities.copy()
                    if 'task_identifier' not in coerced_entities:
                        # Extract identifier (number or word) before field keywords
                        m_id = re.search(r'^update\s+task\s+(\d+|\w+)(?=\s+(?:title|priority|due|description)|$)', message, re.IGNORECASE)
                        if m_id:
                            ident = m_id.group(1).strip().strip('"')
                            coerced_entities['task_identifier'] = ident
                    if 'due_date' not in coerced_entities:
                        m_due = re.search(r'(?:due\s+date|due)\s+(.+)', message, re.IGNORECASE)
                        if m_due:
                            coerced_entities['due_date'] = m_due.group(1).strip()
                    if 'priority' not in coerced_entities:
                        # Match priority values: high, medium, low, urgent, critical
                        # Pattern allows for "priority high", "priority to high", etc.
                        m_pri = re.search(r'priority\s+(?:to\s+)?(high|medium|low|urgent|critical)', message, re.IGNORECASE)
                        if m_pri:
                            coerced_entities['priority'] = m_pri.group(1).lower()
                    if 'title' not in coerced_entities:
                        m_title = re.search(r'(?:title\s+"([^"]+)"|title\s+([^\n]+)|rename\s+(?:task\s+)?(?:to\s+)?"?([^"\n]+)"?)', message, re.IGNORECASE)
                        if m_title:
                            new_title = m_title.group(1) or m_title.group(2) or m_title.group(3)
                            if new_title:
                                coerced_entities['title'] = new_title.strip()
                    parsing_result.parsed_command = ParsedCommand('update_task', coerced_entities, 0.95, message)
                    parsing_result.confidence = 0.95
            except Exception:
                pass
            # Quick augmentation for update_task: extract fields if missing
            try:
                if parsing_result.parsed_command.intent == 'update_task' and 'due_date' not in parsing_result.parsed_command.entities:
                    import re
                    m = re.search(r'(?:due\s+date|due)\s+(.+)', parsing_result.parsed_command.original_message, re.IGNORECASE)
                    if m:
                        parsing_result.parsed_command.entities['due_date'] = m.group(1)
                if parsing_result.parsed_command.intent == 'update_task' and 'priority' not in parsing_result.parsed_command.entities:
                    import re
                    # Match priority values: high, medium, low, urgent, critical
                    # Pattern allows for "priority high", "priority to high", etc.
                    p = re.search(r'priority\s+(?:to\s+)?(high|medium|low|urgent|critical)', parsing_result.parsed_command.original_message, re.IGNORECASE)
                    if p:
                        parsing_result.parsed_command.entities['priority'] = p.group(1).lower()
                if parsing_result.parsed_command.intent == 'update_task' and 'title' not in parsing_result.parsed_command.entities:
                    import re
                    # Accept: title New Name  OR  title "New Name"  OR rename to New Name
                    t = re.search(r'(?:title\s+"?([^"\n]+)"?$|rename\s+(?:task\s+)?(?:to\s+)?"?([^"\n]+)"?$)',
                                  parsing_result.parsed_command.original_message, re.IGNORECASE)
                    if t:
                        new_title = t.group(1) or t.group(2)
                        if new_title:
                            parsing_result.parsed_command.entities['title'] = new_title.strip()
            except Exception:
                pass
            logger.info(f"INTERACTION_MANAGER: Handling as structured command: {parsing_result.parsed_command.intent}")
            resp = self._handle_structured_command(user_id, parsing_result, channel_type)
            # Augment suggestions for targeted prompts
            return self._augment_suggestions(parsing_result.parsed_command, resp)
        
        # Fall back to contextual chat
        if self.fallback_to_chat:
            logger.info(f"INTERACTION_MANAGER: Handling as contextual chat: confidence {parsing_result.confidence} < {self.min_command_confidence}")
            print(f"DEBUG: Going to contextual chat with confidence {parsing_result.confidence}")
            return self._handle_contextual_chat(user_id, message, channel_type)
        
        # No fallback, return help
        logger.debug("No fallback to chat, returning help")
        return self._get_help_response(user_id, message)

    @handle_errors("getting slash command map")
    def get_slash_command_map(self) -> dict:
        """Expose slash command mappings without coupling callers to internals.
        Returns a dict like {'tasks': 'show my tasks', ...} suitable for Discord registration.
        """
        try:
            result = {}
            for c in self._command_definitions:
                result[c.name] = c.mapped_message
            return result
        except Exception as e:
            logger.error(f"Error getting slash command map: {e}")
            return {}

    @handle_errors("getting command definitions")
    def get_command_definitions(self) -> List[Dict[str, str]]:
        """Return canonical command definitions: name, mapped_message, description."""
        try:
            return [
                {"name": c.name, "mapped_message": c.mapped_message, "description": c.description}
                for c in self._command_definitions
            ]
        except Exception as e:
            logger.error(f"Error getting command definitions: {e}")
            return []
    
    @handle_errors("handling structured command", default_return=InteractionResponse(
        "I encountered an error while processing your request. Please try again or ask for help.", True
    ))
    def _handle_structured_command(self, user_id: str, parsing_result: ParsingResult, channel_type: str) -> InteractionResponse:
        """Handle a structured command using interaction handlers"""
        parsed_command = parsing_result.parsed_command
        intent = parsed_command.intent

        # Built-in intents that don't use a specific handler (no AI enhancement needed)
        if intent in ['help']:
            return self._get_help_response(user_id, parsed_command.original_message)
        if intent in ['commands']:
            return self._get_commands_response()

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
        response = handler.handle(user_id, parsed_command)
        
        # Enhance response with AI if enabled
        if self.enable_ai_enhancement and self.ai_chatbot.is_ai_available():
            response = self._enhance_response_with_ai(user_id, response, parsed_command)
        
        # Add suggestions only when helpful; suppress for targeted prompts like update_task
        if (
            not response.completed
            and intent not in ['start_checkin', 'update_task']
            and (response.suggestions is None)
        ):
            response.suggestions = self.command_parser.get_suggestions(parsed_command.original_message)
        
        return response
    
    @handle_errors("handling contextual chat", default_return=InteractionResponse(
        "I'm having trouble processing your message right now. Please try again.", True
    ))
    def _handle_contextual_chat(self, user_id: str, message: str, channel_type: str) -> InteractionResponse:
        """Handle contextual chat using AI chatbot with mixed intent support"""
        # Generate a single AI response that can handle both conversational and actionable content
        ai_chatbot = get_ai_chatbot()
        response = ai_chatbot.generate_response(message, user_id=user_id, mode="chat")
        return InteractionResponse(response, True)
    
    @handle_errors("enhancing response with AI")
    def _enhance_response_with_ai(self, user_id: str, response: InteractionResponse, parsed_command: ParsedCommand) -> InteractionResponse:
        """Enhance a structured response with AI contextual information"""
        # If enhancement fails, return original response (handled by inner try/except and function always returns response)
        try:
            # Only enhance certain types of responses
            if not self.enable_ai_enhancement:
                return response
            
            # Don't enhance well-structured or report-style responses (avoid length limits/truncation)
            # Includes help/commands, task ops, check-ins, profile/schedule/analytics/status/messages, and stats
            excluded_intents = {
                'help', 'commands', 'examples',
                'checkin_history', 'start_checkin', 'checkin_status',
                'completion_rate', 'task_weekly_stats', 'task_stats',
                'list_tasks', 'create_task', 'complete_task', 'delete_task', 'update_task',
                'show_profile', 'profile_stats',
                'show_schedule', 'schedule_status',
                'show_analytics', 'analytics',
                'messages', 'show_messages',
                'status'
            }
            intent = parsed_command.intent or ''
            if intent in excluded_intents or any(k in intent for k in ['profile', 'schedule', 'analytics', 'messages']):
                return response
            
            # Create a context prompt for AI enhancement
            context_prompt = f"""
User requested: {parsed_command.original_message}
Current response: {response.message}

Please enhance this response to be more personal and contextual for the user, 
while keeping the core information intact. Make it warm and encouraging.
Return ONLY the enhanced response, no prefixes, formatting, or system prompts.
"""
            
            enhanced_text = self.ai_chatbot.generate_response(
                context_prompt,
                user_id=user_id,
                timeout=3  # Short timeout for enhancement
            )
            
            # Validate enhanced response - check for common issues
            if enhanced_text and len(enhanced_text) > 10:
                # Check for system prompt leakage
                system_indicators = [
                    "System response:", "Exercise", "You are a chatbot", 
                    "Your job is to", "Please enhance", "Return ONLY",
                    "```python", "```json", "{'action':", '{"action":'
                ]
                
                has_system_content = any(indicator in enhanced_text for indicator in system_indicators)
                
                if not has_system_content:
                    # Apply length guard only for AI chat-like enhancements; report-style are excluded above
                    # Use centralized response length limits
                    if len(enhanced_text) > AI_MAX_RESPONSE_LENGTH:
                        # Smart truncation at sentence boundary
                        cut = enhanced_text[:AI_MAX_RESPONSE_LENGTH]
                        for mark in (". ", "! ", "? "):
                            idx = cut.rfind(mark)
                            if idx >= 0 and idx > AI_MAX_RESPONSE_LENGTH * 0.6:
                                enhanced_text = cut[:idx+1]
                                break
                        else:
                            enhanced_text = cut.rstrip() + "..."
                    response.message = enhanced_text.strip()
                else:
                    logger.debug(f"AI enhancement returned system content, keeping original response")
            
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
            "📅 **Schedule Management:**\n"
            "• View schedule: 'Show my schedule'\n"
            "• Check status: 'Schedule status'\n"
            "• Enable/disable: 'Enable my task schedule'\n\n"
            "📊 **Analytics & Insights:**\n"
            "• View analytics: 'Show my analytics'\n"
            "• Mood trends: 'Mood trends for 7 days'\n"
            "• Habit analysis: 'Habit analysis'\n\n"
            "Try one of these or ask for 'help' to learn more!"
        )

        # Append concise command list for quick discovery
        try:
            defs = self.get_command_definitions()
            names = [f"/{d['name']}" for d in defs]
            if names:
                help_text += "\n\nQuick commands: " + ", ".join(names)
        except Exception:
            pass
        
        return InteractionResponse(
            help_text,
            True,
            suggestions=suggestions
        )

    @handle_errors("getting commands response", default_return=InteractionResponse("Error getting commands", "error"))
    def _get_commands_response(self) -> InteractionResponse:
        """Return a concise, channel-agnostic commands list for quick discovery."""
        defs = self.get_command_definitions()
        # Order with flows and common actions first
        preferred = [
            'checkin', 'tasks', 'profile', 'schedule', 'messages', 'analytics', 'status', 'help', 'cancel'
        ]
        sorted_defs = sorted(defs, key=lambda d: preferred.index(d['name']) if d['name'] in preferred else 999)

        lines: List[str] = ["**Available Commands**"]
        lines.append("Slash commands (type in Discord):")
        for d in sorted_defs:
            slash = f"/{d['name']}"
            lines.append(f"- {slash} — {d['description']}")
        lines.append("")
        lines.append("Classic commands (if enabled): !tasks, !profile, !schedule, !messages, !analytics, !status")

        text = "\n".join(lines)
        return InteractionResponse(text, True)
    
    @handle_errors("getting available commands", default_return={})
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
        
        # Get schedule suggestions
        try:
            from core.user_management import get_user_categories
            categories = get_user_categories(user_id)
            if categories:
                suggestions.append("Show my schedule")
                suggestions.append("Schedule status")
        except Exception:
            pass
        
        # Get analytics suggestions
        try:
            from core.response_tracking import get_recent_checkins
            checkins = get_recent_checkins(user_id, limit=5)
            if checkins:
                suggestions.append("Show my analytics")
                suggestions.append("Mood trends")
        except Exception:
            pass
        
        # Add general suggestions
        suggestions.extend([
            "Create a task to call mom tomorrow",
            "Show my profile",
            "Help with tasks"
        ])
        
        return suggestions[:5]  # Limit to 5 suggestions

    @handle_errors("checking if AI response is command")
    def _is_ai_command_response(self, ai_response: str) -> bool:
        """Check if AI response indicates this was a command"""
        try:
            # Look for JSON structure or command indicators
            if ai_response.strip().startswith('{') and ai_response.strip().endswith('}'):
                return True
            
            # Look for command action keywords
            command_indicators = ['action', 'intent', 'command', 'task', 'checkin', 'profile', 'schedule']
            return any(indicator in ai_response.lower() for indicator in command_indicators)
        except Exception as e:
            logger.error(f"Error checking if AI response is command: {e}")
            return False
    
    @handle_errors("parsing AI command response")
    def _parse_ai_command_response(self, ai_response: str, original_message: str) -> Optional[ParsedCommand]:
        """Parse AI command response into ParsedCommand"""
        try:
            import json
            # Try to parse as JSON first
            if ai_response.strip().startswith('{') and ai_response.strip().endswith('}'):
                data = json.loads(ai_response)
                return ParsedCommand(
                    intent=data.get('intent', 'unknown'),
                    entities=data.get('entities', {}),
                    confidence=data.get('confidence', 0.7),
                    original_message=original_message
                )
            
            # Fallback: try to extract intent from text response
            ai_response_lower = ai_response.lower()
            if 'checkin' in ai_response_lower:
                return ParsedCommand(intent='start_checkin', entities={}, confidence=0.6, original_message=original_message)
            elif 'task' in ai_response_lower:
                return ParsedCommand(intent='list_tasks', entities={}, confidence=0.6, original_message=original_message)
            elif 'profile' in ai_response_lower:
                return ParsedCommand(intent='show_profile', entities={}, confidence=0.6, original_message=original_message)
            elif 'mood' in ai_response_lower or 'analytics' in ai_response_lower:
                return ParsedCommand(intent='show_analytics', entities={}, confidence=0.6, original_message=original_message)
            
            return None
        except Exception as e:
            logger.error(f"Error parsing AI command response: {e}")
            return None
    
    @handle_errors("checking if AI response is clarification request")
    def _is_clarification_request(self, ai_response: str) -> bool:
        """Check if AI response is asking for clarification"""
        try:
            clarification_indicators = [
            'could you clarify', 'can you clarify', 'please clarify',
            'what do you mean', 'could you be more specific',
            'are you asking', 'do you want', 'would you like',
            'i\'m not sure what you mean', 'i need more information',
            'which one', 'what type', 'when', 'how'
        ]
        
            response_lower = ai_response.lower()
            return any(indicator in response_lower for indicator in clarification_indicators)
        except Exception as e:
            logger.error(f"Error checking if AI response is clarification request: {e}")
            return False
    
    @handle_errors("extracting intent from text")
    def _extract_intent_from_text(self, text: str) -> Optional[str]:
        """Extract intent from AI text response"""
        try:
            # Map common AI response patterns to intents
            intent_mappings = {
            'create task': 'create_task',
            'list tasks': 'list_tasks',
            'complete task': 'complete_task',
            'delete task': 'delete_task',
            'update task': 'update_task',
            'task stats': 'task_stats',
            'start checkin': 'start_checkin',
            'checkin status': 'checkin_status',
            'checkin history': 'checkin_history',
            'checkin analysis': 'checkin_analysis',
            'show profile': 'show_profile',
            'update profile': 'update_profile',
            'profile stats': 'profile_stats',
            'mood trends': 'mood_trends',
            'habit analysis': 'habit_analysis',
            'sleep analysis': 'sleep_analysis',
            'wellness score': 'wellness_score',
            'show analytics': 'show_analytics',
            'help': 'help',
            'commands': 'commands',
            'examples': 'examples',
        }
        
            text_lower = text.lower()
            for pattern, intent in intent_mappings.items():
                if pattern in text_lower:
                    return intent
            
            return None
        except Exception as e:
            logger.error(f"Error extracting intent from text: {e}")
            return None
    
    @handle_errors("checking if intent is valid")
    def _is_valid_intent(self, intent: str) -> bool:
        """Check if intent is supported by any handler"""
        try:
            for handler in self.interaction_handlers.values():
                if handler.can_handle(intent):
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking if intent is valid: {e}")
            return False

    @handle_errors("trying AI command parsing")
    def _try_ai_command_parsing(self, user_id: str, message: str, channel_type: str) -> Optional[InteractionResponse]:
        """Attempt to parse ambiguous messages using AI command parsing."""
        try:
            # First try regular command parsing
            ai_response = self.ai_chatbot.generate_response(
                message, 
                mode="command",
                timeout=5  # Short timeout for command parsing
            )
            
            # Check if AI detected this as a command
            if self._is_ai_command_response(ai_response):
                # AI thinks this is a command, try to parse it
                parsed_command = self._parse_ai_command_response(ai_response, message)
                if parsed_command and parsed_command.intent != "unknown":
                    logger.debug(f"AI detected command: {parsed_command.intent}")
                    return self._handle_structured_command(user_id, 
                        ParsingResult(parsed_command, 0.7, "ai_command"), channel_type)
            
            # If regular command parsing didn't work, try clarification mode
            clarification_response = self.ai_chatbot.generate_response(
                message,
                mode="command_with_clarification", 
                timeout=8  # Slightly longer timeout for clarification
            )
            
            # Check if AI is asking for clarification
            if self._is_clarification_request(clarification_response):
                return InteractionResponse(clarification_response, True)
            
            # If clarification mode found a command, handle it
            if self._is_ai_command_response(clarification_response):
                parsed_command = self._parse_ai_command_response(clarification_response, message)
                if parsed_command and parsed_command.intent != "unknown":
                    logger.debug(f"AI detected command in clarification mode: {parsed_command.intent}")
                    return self._handle_structured_command(user_id, 
                        ParsingResult(parsed_command, 0.6, "ai_command_clarified"), channel_type)
                        
        except Exception as e:
            logger.error(f"Error trying AI command parsing: {e}")
        
        return None

    def _augment_suggestions(self, parsed_command: ParsedCommand, response: InteractionResponse) -> InteractionResponse:
        try:
            if response.completed:
                return response
            msg = (response.message or "").lower()
            suggestions: List[str] = []
            if "multiple matching tasks" in msg:
                suggestions = ["list tasks", "cancel"]
            elif "confirm delete" in msg:
                suggestions = ["confirm delete", "cancel"]
            elif "did you want to complete this task" in msg:
                suggestions = ["complete task 1", "cancel"]
            elif "what would you like to update for" in msg:
                if parsed_command.intent == "edit_schedule_period":
                    suggestions = ["from 9am to 11am", "active off"]
                else:
                    suggestions = ["due date tomorrow", "priority high"]
            elif parsed_command.intent in ["update_task", "complete_task", "delete_task"] and "which task" in msg:
                suggestions = ["list tasks", "cancel"]
            # Cap at 2
            if suggestions:
                response.suggestions = suggestions[:2]
            return response
        except Exception:
            return response

# Global instance
_interaction_manager_instance = None

@handle_errors("getting interaction manager")
def get_interaction_manager() -> InteractionManager:
    """Get the global interaction manager instance"""
    try:
        global _interaction_manager_instance
        if _interaction_manager_instance is None:
            _interaction_manager_instance = InteractionManager()
        return _interaction_manager_instance
    except Exception as e:
        logger.error(f"Error getting interaction manager: {e}")
        raise

@handle_errors("handling user message", default_return=InteractionResponse(
    "I'm having trouble processing your request right now. Please try again in a moment.", True
))
def handle_user_message(user_id: str, message: str, channel_type: str = "discord") -> InteractionResponse:
    """Convenience function to handle a user message"""
    try:
        manager = get_interaction_manager()
        return manager.handle_message(user_id, message, channel_type)
    except Exception as e:
        logger.error(f"Error handling user message: {e}")
        return InteractionResponse(
            "I'm having trouble processing your request right now. Please try again in a moment.",
            True
        ) 
