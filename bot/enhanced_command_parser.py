# bot/enhanced_command_parser.py

"""
Enhanced command parser that builds on existing AI chatbot capabilities.

This module provides sophisticated command parsing by combining:
1. Rule-based pattern matching (fast, reliable)
2. AI-powered parsing (flexible, intelligent)
3. Integration with interaction handlers
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from core.logger import get_logger
from core.error_handling import handle_errors
from bot.ai_chatbot import get_ai_chatbot
from bot.interaction_handlers import ParsedCommand, get_all_handlers

logger = get_logger(__name__)

@dataclass
class ParsingResult:
    """Result of command parsing with confidence and method used"""
    parsed_command: ParsedCommand
    confidence: float
    method: str  # 'rule_based', 'ai_enhanced', 'fallback'

class EnhancedCommandParser:
    """Enhanced command parser that combines rule-based and AI parsing"""
    
    def __init__(self):
        self.ai_chatbot = get_ai_chatbot()
        self.interaction_handlers = get_all_handlers()
        
        # Rule-based patterns for common intents
        self.intent_patterns = {
            'create_task': [
                r'create\s+(?:a\s+)?task\s+(?:to\s+)?(.+)',
                r'add\s+(?:a\s+)?task\s+(?:to\s+)?(.+)',
                r'new\s+task\s+(?:to\s+)?(.+)',
                r'i\s+need\s+to\s+(.+)',
                r'remind\s+me\s+to\s+(.+)',
                r'call\s+(.+?)(?:\s+tomorrow|\s+next\s+week|\s+on\s+\w+)',
                r'buy\s+(.+?)(?:\s+tomorrow|\s+next\s+week|\s+on\s+\w+)',
                r'schedule\s+(.+?)(?:\s+tomorrow|\s+next\s+week|\s+on\s+\w+)',
            ],
            'list_tasks': [
                r'show\s+(?:my\s+)?tasks?',
                r'list\s+(?:my\s+)?tasks?',
                r'what\s+(?:are\s+)?(?:my\s+)?tasks?',
                r'my\s+tasks?',
                r'tasks?\s+due',
                r'what\s+do\s+i\s+have\s+to\s+do',
            ],
            'complete_task': [
                r'complete\s+(?:task\s+)?(\d+|[^0-9]+)',
                r'done\s+(?:task\s+)?(\d+|[^0-9]+)',
                r'finished\s+(?:task\s+)?(\d+|[^0-9]+)',
                r'mark\s+(?:task\s+)?(\d+|[^0-9]+)\s+complete',
                r'task\s+(\d+|[^0-9]+)\s+done',
            ],
            'delete_task': [
                r'delete\s+(?:task\s+)?(\d+|[^0-9]+)',
                r'remove\s+(?:task\s+)?(\d+|[^0-9]+)',
                r'cancel\s+(?:task\s+)?(\d+|[^0-9]+)',
            ],
            'update_task': [
                r'update\s+(?:task\s+)?(\d+|[^0-9]+)\s+(.+)',
                r'change\s+(?:task\s+)?(\d+|[^0-9]+)\s+(.+)',
                r'edit\s+(?:task\s+)?(\d+|[^0-9]+)\s+(.+)',
            ],
            'task_stats': [
                r'task\s+stats',
                r'task\s+statistics',
                r'show\s+task\s+stats',
                r'my\s+task\s+progress',
                r'how\s+am\s+i\s+doing\s+with\s+tasks',
            ],
            'start_checkin': [
                r'start\s+(?:a\s+)?check.?in',
                r'begin\s+(?:a\s+)?check.?in',
                r'i\s+want\s+to\s+check\s+in',
                r'let\s+me\s+check\s+in',
                r'daily\s+check.?in',
                r'check\s+in',
            ],
            'checkin_status': [
                r'check.?in\s+status',
                r'show\s+check.?ins?',
                r'my\s+check.?in\s+history',
                r'how\s+am\s+i\s+doing',
                r'check.?in\s+progress',
            ],
            'show_profile': [
                r'show\s+(?:my\s+)?profile',
                r'my\s+profile',
                r'view\s+(?:my\s+)?profile',
                r'display\s+(?:my\s+)?profile',
            ],
            'update_profile': [
                r'update\s+(?:my\s+)?profile',
                r'change\s+(?:my\s+)?profile',
                r'edit\s+(?:my\s+)?profile',
                r'update\s+(name|gender_identity|email)\s+(.+)',
            ],
            'profile_stats': [
                r'profile\s+stats',
                r'my\s+statistics',
                r'my\s+stats',
                r'show\s+my\s+stats',
            ],
            'help': [
                r'help',
                r'help\s+(tasks?|check.?in|profile)',
                r'what\s+can\s+you\s+do',
                r'how\s+do\s+i\s+use\s+this',
            ],
            'commands': [
                r'commands?',
                r'available\s+commands?',
                r'what\s+commands?\s+are\s+available',
                r'list\s+commands?',
            ],
            'examples': [
                r'examples?',
                r'examples?\s+(tasks?|check.?in|profile)',
                r'show\s+examples?',
                r'give\s+me\s+examples?',
            ],
        }
        
        # Compile patterns for performance
        self.compiled_patterns = {}
        for intent, patterns in self.intent_patterns.items():
            self.compiled_patterns[intent] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    @handle_errors("parsing command", default_return=ParsingResult(
        ParsedCommand("unknown", {}, 0.0, ""), 0.0, "fallback"
    ))
    def parse(self, message: str) -> ParsingResult:
        """
        Parse a user message into a structured command.
        
        Returns:
            ParsingResult with parsed command, confidence, and method used
        """
        if not message or not message.strip():
            return ParsingResult(
                ParsedCommand("unknown", {}, 0.0, message),
                0.0, "fallback"
            )
        
        # Try rule-based parsing first (fast, reliable)
        rule_result = self._rule_based_parse(message)
        if rule_result.confidence > 0.8:
            return rule_result
        
        # Try AI-enhanced parsing (slower, more flexible)
        ai_result = self._ai_enhanced_parse(message)
        if ai_result.confidence > 0.6:
            return ai_result
        
        # Fall back to rule-based with lower confidence
        if rule_result.confidence > 0.3:
            return rule_result
        
        # Final fallback
        return ParsingResult(
            ParsedCommand("unknown", {}, 0.0, message),
            0.0, "fallback"
        )
    
    def _rule_based_parse(self, message: str) -> ParsingResult:
        """Parse using rule-based patterns"""
        message_lower = message.lower().strip()
        
        # Check each intent pattern
        for intent, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(message_lower)
                if match:
                    entities = self._extract_entities_rule_based(intent, match, message)
                    confidence = self._calculate_confidence(intent, match, message)
                    
                    return ParsingResult(
                        ParsedCommand(intent, entities, confidence, message),
                        confidence, "rule_based"
                    )
        
        # No pattern matched
        return ParsingResult(
            ParsedCommand("unknown", {}, 0.0, message),
            0.0, "rule_based"
        )
    
    def _ai_enhanced_parse(self, message: str) -> ParsingResult:
        """Parse using AI chatbot capabilities"""
        try:
            # Use existing AI chatbot command parsing
            ai_response = self.ai_chatbot.generate_response(
                message, 
                mode="command",
                timeout=5  # Short timeout for parsing
            )
            
            # Try to parse AI response as JSON
            try:
                parsed_data = json.loads(ai_response)
                intent = parsed_data.get('action', 'unknown')
                entities = parsed_data.get('details', {})
                
                # Validate intent against available handlers
                if self._is_valid_intent(intent):
                    confidence = 0.7  # AI parsing confidence
                    return ParsingResult(
                        ParsedCommand(intent, entities, confidence, message),
                        confidence, "ai_enhanced"
                    )
            except json.JSONDecodeError:
                # AI didn't return valid JSON, try to extract intent from text
                intent = self._extract_intent_from_ai_response(ai_response)
                if intent and self._is_valid_intent(intent):
                    entities = self._extract_entities_from_ai_response(ai_response)
                    return ParsingResult(
                        ParsedCommand(intent, entities, 0.6, message),
                        0.6, "ai_enhanced"
                    )
        
        except Exception as e:
            logger.debug(f"AI parsing failed: {e}")
        
        return ParsingResult(
            ParsedCommand("unknown", {}, 0.0, message),
            0.0, "ai_enhanced"
        )
    
    def _extract_entities_rule_based(self, intent: str, match: re.Match, message: str) -> Dict[str, Any]:
        """Extract entities using rule-based patterns"""
        entities = {}
        
        if intent == 'create_task':
            # Extract task title from capture group
            if match.groups():
                title = match.group(1).strip()
                entities['title'] = title
                
                # Extract additional entities
                entities.update(self._extract_task_entities(title))
        
        elif intent in ['complete_task', 'delete_task', 'update_task']:
            # Extract task identifier
            if match.groups():
                identifier = match.group(1).strip()
                entities['task_identifier'] = identifier
                
                # For update_task, extract update details
                if intent == 'update_task' and len(match.groups()) > 1:
                    update_text = match.group(2).strip()
                    entities.update(self._extract_update_entities(update_text))
        
        elif intent == 'update_profile':
            # Extract profile field and value
            if len(match.groups()) >= 2:
                field = match.group(1).strip()
                value = match.group(2).strip()
                entities[field] = value
        
        elif intent == 'help':
            # Extract help topic
            if match.groups():
                topic = match.group(1).strip()
                entities['topic'] = topic
        
        elif intent == 'examples':
            # Extract example category
            if match.groups():
                category = match.group(1).strip()
                entities['category'] = category
        
        return entities
    
    def _extract_task_entities(self, title: str) -> Dict[str, Any]:
        """Extract task-related entities from title"""
        entities = {}
        
        # Extract due date
        due_patterns = [
            r'tomorrow',
            r'next\s+week',
            r'next\s+month',
            r'on\s+(\w+\s+\d+)',
            r'by\s+(\w+\s+\d+)',
        ]
        
        for pattern in due_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                entities['due_date'] = match.group(0)
                break
        
        # Extract priority
        priority_patterns = {
            'high': [r'urgent', r'asap', r'important', r'critical'],
            'low': [r'low\s+priority', r'when\s+convenient', r'no\s+rush'],
        }
        
        for priority, patterns in priority_patterns.items():
            for pattern in patterns:
                if re.search(pattern, title, re.IGNORECASE):
                    entities['priority'] = priority
                    break
        
        return entities
    
    def _extract_update_entities(self, update_text: str) -> Dict[str, Any]:
        """Extract update entities from update text"""
        entities = {}
        
        # Extract priority
        if re.search(r'priority\s+(high|medium|low)', update_text, re.IGNORECASE):
            match = re.search(r'priority\s+(high|medium|low)', update_text, re.IGNORECASE)
            entities['priority'] = match.group(1)
        
        # Extract due date
        if re.search(r'due\s+(.+)', update_text, re.IGNORECASE):
            match = re.search(r'due\s+(.+)', update_text, re.IGNORECASE)
            entities['due_date'] = match.group(1)
        
        return entities
    
    def _extract_intent_from_ai_response(self, ai_response: str) -> Optional[str]:
        """Extract intent from AI response text"""
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
            'show profile': 'show_profile',
            'update profile': 'update_profile',
            'profile stats': 'profile_stats',
            'help': 'help',
            'commands': 'commands',
            'examples': 'examples',
        }
        
        ai_response_lower = ai_response.lower()
        for pattern, intent in intent_mappings.items():
            if pattern in ai_response_lower:
                return intent
        
        return None
    
    def _extract_entities_from_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Extract entities from AI response text"""
        entities = {}
        
        # Extract task title in quotes
        title_match = re.search(r'"([^"]+)"', ai_response)
        if title_match:
            entities['title'] = title_match.group(1)
        
        # Extract task number
        number_match = re.search(r'task\s+(\d+)', ai_response)
        if number_match:
            entities['task_identifier'] = number_match.group(1)
        
        return entities
    
    def _calculate_confidence(self, intent: str, match: re.Match, message: str) -> float:
        """Calculate confidence score for rule-based parsing"""
        base_confidence = 0.8
        
        # Boost confidence for exact matches
        if match.group(0).lower() == message.lower().strip():
            base_confidence += 0.1
        
        # Boost confidence for longer, more specific patterns
        pattern_length = len(match.group(0))
        message_length = len(message)
        if pattern_length / message_length > 0.8:
            base_confidence += 0.1
        
        # Reduce confidence for ambiguous patterns
        if intent in ['create_task', 'update_task'] and not match.groups():
            base_confidence -= 0.2
        
        return min(1.0, max(0.0, base_confidence))
    
    def _is_valid_intent(self, intent: str) -> bool:
        """Check if intent is supported by any handler"""
        for handler in self.interaction_handlers.values():
            if handler.can_handle(intent):
                return True
        return False
    
    def get_suggestions(self, partial_message: str) -> List[str]:
        """Get command suggestions based on partial input"""
        suggestions = []
        
        if not partial_message:
            # General suggestions
            suggestions = [
                "Create a task to call mom tomorrow",
                "Show me my tasks",
                "Start a check-in",
                "Show my profile",
                "Help with tasks"
            ]
        else:
            partial_lower = partial_message.lower()
            
            # Task-related suggestions
            if any(word in partial_lower for word in ['task', 'todo', 'remind']):
                suggestions = [
                    "Create a task to call mom tomorrow",
                    "Show me my tasks",
                    "Complete task 1",
                    "Delete task 2",
                    "Update task 1 priority high"
                ]
            
            # Check-in suggestions
            elif any(word in partial_lower for word in ['check', 'mood', 'feel']):
                suggestions = [
                    "Start a check-in",
                    "Show my check-in history",
                    "How am I doing this week?"
                ]
            
            # Profile suggestions
            elif any(word in partial_lower for word in ['profile', 'name', 'pronoun']):
                suggestions = [
                    "Show my profile",
                    "Update my name to Julie",
                    "Update my gender identity to Non-binary",
                    "Show my statistics"
                ]
            
            # Help suggestions
            elif any(word in partial_lower for word in ['help', 'how', 'what']):
                suggestions = [
                    "Help with tasks",
                    "Help with check-ins",
                    "Help with profile",
                    "Show available commands",
                    "Show examples"
                ]
        
        return suggestions[:5]  # Limit to 5 suggestions

# Global instance
_parser_instance = None

def get_enhanced_command_parser() -> EnhancedCommandParser:
    """Get the global enhanced command parser instance"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = EnhancedCommandParser()
    return _parser_instance

def parse_command(message: str) -> ParsingResult:
    """Convenience function to parse a command"""
    parser = get_enhanced_command_parser()
    return parser.parse(message) 