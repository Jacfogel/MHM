# communication/message_processing/command_parser.py

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
from core.logger import get_logger, get_component_logger
from core.error_handling import handle_errors
from core.config import (
    AI_RULE_BASED_HIGH_CONFIDENCE_THRESHOLD, AI_AI_ENHANCED_CONFIDENCE_THRESHOLD,
    AI_RULE_BASED_FALLBACK_THRESHOLD, AI_AI_PARSING_BASE_CONFIDENCE,
    AI_AI_PARSING_PARTIAL_CONFIDENCE, AI_COMMAND_PARSING_TIMEOUT
)
from ai.chatbot import get_ai_chatbot
from communication.command_handlers.shared_types import ParsedCommand
from communication.command_handlers.interaction_handlers import get_all_handlers

parser_logger = get_component_logger('ai')
logger = parser_logger

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
                r'^my\s+tasks?$',
                r'tasks?\s+due',
                r'what\s+do\s+i\s+have\s+to\s+do\s+(?:today|tomorrow)',
                r'what\s+are\s+my\s+tasks?\s+(?:for\s+today|for\s+tomorrow)',
                r'show\s+me\s+my\s+tasks?',
            ],
            'complete_task': [
                r'complete\s+(?:task\s+)?(\d+|[^0-9]+)',
                r'done\s+(?:task\s+)?(\d+|[^0-9]+)',
                r'finished\s+(?:task\s+)?(\d+|[^0-9]+)',
                r'mark\s+(?:task\s+)?(\d+|[^0-9]+)\s+complete',
                r'task\s+(\d+|[^0-9]+)\s+done',
                # Natural language patterns for task completion
                r'i\s+(?:just\s+)?(?:brushed|washed|cleaned|did|completed|finished)\s+(?:my\s+)?(.+?)(?:\s+today|\s+now|\s+just\s+now)?(?:\s*,?\s*we\s+can\s+complete\s+that\s+task)?',
                r'i\s+(?:just\s+)?(?:brushed|washed|cleaned|did|completed|finished)\s+(?:my\s+)?(.+?)(?:\s+today|\s+now|\s+just\s+now)?(?:\s*,?\s*so\s+we\s+can\s+complete\s+that\s+task)?',
                r'(?:we\s+can\s+complete\s+that\s+task|so\s+we\s+can\s+complete\s+that\s+task)(?:\s*because\s+i\s+(?:just\s+)?(?:brushed|washed|cleaned|did|completed|finished)\s+(?:my\s+)?(.+?))?',
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
                # Dynamic time period patterns
                r'how\s+am\s+i\s+doing\s+with\s+(?:my\s+)?tasks?\s+(this\s+week|last\s+week|this\s+month|last\s+month|this\s+year|last\s+year|\d+\s+weeks?|\d+\s+months?|\d+\s+days?)',
                r'task\s+stats\s+(?:for\s+)?(this\s+week|last\s+week|this\s+month|last\s+month|this\s+year|last\s+year|\d+\s+weeks?|\d+\s+months?|\d+\s+days?)',
                r'my\s+task\s+progress\s+(?:for\s+)?(this\s+week|last\s+week|this\s+month|last\s+month|this\s+year|last\s+year|\d+\s+weeks?|\d+\s+months?|\d+\s+days?)',
                r'task\s+summary\s+(?:for\s+)?(this\s+week|last\s+week|this\s+month|last\s+month|this\s+year|last\s+year|\d+\s+weeks?|\d+\s+months?|\d+\s+days?)',
            ],
            'task_analytics': [
                r'task\s+analytics',
                r'task\s+analysis',
                r'analyze\s+(?:my\s+)?tasks?',
                r'analyze\s+my\s+task\s+performance',
                r'task\s+performance\s+analysis',
                r'how\s+am\s+i\s+performing\s+with\s+tasks?',
                r'task\s+insights',
                r'task\s+trends',
                r'my\s+task\s+analytics',
            ],
            'start_checkin': [
                r'start\s+(?:a\s+)?check.?in',
                r'begin\s+(?:a\s+)?check.?in',
                r'i\s+want\s+to\s+check\s+in',
                r'i\s+want\s+to\s+have\s+a\s+check.?in',
                r'i\s+want\s+a\s+check.?in',
                r'let\s+me\s+check\s+in',
                r'let\s+me\s+have\s+a\s+check.?in',
                r'daily\s+check.?in',
                r'^check\s+in$',
                r'^checkin$',
                r'check.?in\s+now',
                r'can\s+i\s+check\s+in',
                r'can\s+i\s+have\s+a\s+check.?in',
            ],
            'checkin_status': [
                r'check.?in\s+status',
                r'show\s+check.?ins?',
                r'how\s+am\s+i\s+doing\s+(?:overall|in\s+general|with\s+check.?ins?)',
                r'check.?in\s+progress',
            ],
            'checkin_history': [
                r'tell\s+me\s+about\s+my\s+check.?in\s+history',
                r'about\s+my\s+check.?in\s+history',
                r'check.?in\s+history',
                r'show\s+(?:my\s+)?check.?in\s+history',
                r'my\s+check.?in\s+history',
                r'check.?in\s+records',
                r'past\s+check.?ins?',
                r'check.?in\s+log',
            ],
            'checkin_analysis': [
                r'analyse\s+(?:my\s+)?check.?in\s+responses?',
                r'analyze\s+(?:my\s+)?check.?in\s+responses?',
                r'check.?in\s+analysis',
                r'analyse\s+my\s+check.?ins?',
                r'analyze\s+my\s+check.?ins?',
                r'check.?in\s+analytics',
                r'my\s+check.?in\s+analysis',
                r'check.?in\s+insights',
                r'check.?in\s+trends',
            ],
            'completion_rate': [
                r'completion\s+rate',
                r'what\s+is\s+my\s+completion\s+rate',
                r'how\s+am\s+i\s+doing\s+with\s+completion',
                r'task\s+completion\s+rate',
                r'my\s+completion\s+rate',
                r'completion\s+percentage',
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
                r'how\s+do\s+i\s+create\s+a\s+task',
                r'how\s+do\s+i\s+create\s+tasks?',
                r'how\s+to\s+create\s+a\s+task',
                r'how\s+to\s+create\s+tasks?',
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
            'status': [
                r'status',
                r'system\s+status',
                r'how\s+am\s+i\s+doing',
                r'what\s+is\s+my\s+status',
                r'check\s+status',
                r'my\s+status',
                r'current\s+status',
            ],
            'messages': [
                r'messages?',
                r'show\s+(?:my\s+)?messages?',
                r'my\s+messages?',
                r'view\s+(?:my\s+)?messages?',
                r'display\s+(?:my\s+)?messages?',
                r'message\s+history',
                r'recent\s+messages?',
            ],
            # Schedule Management Patterns
            'show_schedule': [
                r'show\s+(?:my\s+)?schedule',
                r'my\s+schedule',
                r'view\s+(?:my\s+)?schedule',
                r'display\s+(?:my\s+)?schedule',
                r'schedule\s+for\s+(tasks?|check.?ins?|messages?)',
                r'when\s+are\s+(?:my\s+)?(tasks?|check.?ins?|messages?)\s+scheduled',
            ],
            'update_schedule': [
                r'update\s+(?:my\s+)?schedule',
                r'change\s+(?:my\s+)?schedule',
                r'enable\s+(?:my\s+)?(tasks?|check.?ins?|messages?)\s+schedule',
                r'disable\s+(?:my\s+)?(tasks?|check.?ins?|messages?)\s+schedule',
                r'turn\s+(on|off)\s+(?:my\s+)?(tasks?|check.?ins?|messages?)\s+schedule',
            ],
            'schedule_status': [
                r'schedule\s+status',
                r'are\s+(?:my\s+)?schedules?\s+active',
                r'check\s+schedule\s+status',
                r'schedule\s+info',
            ],
            'add_schedule_period': [
                r'add\s+(?:a\s+)?(?:new\s+)?schedule\s+period',
                r'add\s+(?:a\s+)?period\s+called\s+(\w+)\s+to\s+(?:my\s+)?(\w+)\s+schedule',
                r'create\s+(?:a\s+)?new\s+period\s+for\s+(?:my\s+)?(\w+)\s+schedule',
            ],
            'edit_schedule_period': [
                r'edit\s+(?:the\s+)?(\w+)\s+period\s+in\s+(?:my\s+)?(\w+)\s+schedule',
                r'change\s+(?:the\s+)?(\w+)\s+period\s+to\s+(.+)',
                r'update\s+(?:the\s+)?(\w+)\s+period\s+time',
            ],
            # Analytics Patterns
            'show_analytics': [
                r'show\s+(?:my\s+)?analytics',
                r'my\s+analytics',
                r'view\s+(?:my\s+)?analytics',
                r'display\s+(?:my\s+)?analytics',
                r'analytics\s+(?:for\s+)?(\d+)\s+days?',
                r'how\s+am\s+i\s+doing\s+(?:overall|in\s+general)',
            ],
            'mood_trends': [
                r'mood\s+trends?',
                r'how\s+has\s+(?:my\s+)?mood\s+been',
                r'mood\s+analysis',
                r'mood\s+over\s+time',
                r'mood\s+(?:for\s+)?(\d+)\s+days?',
                r'what\s*[\'s]?\s*(?:has\s+)?my\s+mood\s+been\s+like\s+(?:lately|recently)',
                r'what.*mood.*been.*like.*lately',
                r'how\s+has\s+my\s+mood\s+been\s+(?:lately|recently)',
                r'my\s+mood\s+history',
                r'mood\s+tracking',
                r'track\s+my\s+mood',
                r'my\s+mood\s+tracking',
                r'mood\s+patterns',
            ],
            'habit_analysis': [
                r'habit\s+analysis',
                r'how\s+am\s+i\s+doing\s+with\s+habits?',
                r'habit\s+progress',
                r'habit\s+completion',
                r'habit\s+(?:for\s+)?(\d+)\s+days?',
            ],
            'sleep_analysis': [
                r'sleep\s+analysis',
                r'how\s+am\s+i\s+sleeping',
                r'sleep\s+patterns?',
                r'sleep\s+quality',
                r'sleep\s+(?:for\s+)?(\d+)\s+days?',
            ],
            'wellness_score': [
                r'wellness\s+score',
                r'my\s+wellness\s+score',
                r'calculate\s+(?:my\s+)?wellness\s+score',
                r'overall\s+wellness',
                r'wellness\s+(?:for\s+)?(\d+)\s+days?',
            ],
        }
        
        # Compile patterns for performance
        self.compiled_patterns = {}
        for intent, patterns in self.intent_patterns.items():
            self.compiled_patterns[intent] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    
    @handle_errors("parsing command", default_return=ParsingResult(
        ParsedCommand("unknown", {}, 0.0, ""), 0.0, "fallback"
    ))
    def parse(self, message: str, user_id: str = None) -> ParsingResult:
        """
        Parse a user message into a structured command.
        
        Returns:
            ParsingResult with parsed command, confidence, and method used
        """
        from core.logger import get_component_logger
        logger = get_component_logger('communication_manager')
        logger.info(f"COMMAND_PARSER: Parsing message for user {user_id}: '{message[:50]}...'")
        
        if not message or not message.strip():
            return ParsingResult(
                ParsedCommand("unknown", {}, 0.0, message),
                0.0, "fallback"
            )
        
        # Try rule-based parsing first (fast, reliable)
        rule_result = self._rule_based_parse(message)
        if rule_result.confidence > AI_RULE_BASED_HIGH_CONFIDENCE_THRESHOLD:
            return rule_result
        
        # If rule-based parsing has zero confidence, it's clearly not a command - skip AI parsing
        if rule_result.confidence == 0.0:
            return rule_result
        
        # Try AI-enhanced parsing only for ambiguous cases (confidence > 0 but < high threshold)
        ai_result = self._ai_enhanced_parse(message, user_id)
        if ai_result.confidence >= AI_AI_ENHANCED_CONFIDENCE_THRESHOLD:
            return ai_result
        
        # Fall back to rule-based with lower confidence
        if rule_result.confidence > AI_RULE_BASED_FALLBACK_THRESHOLD:
            return rule_result
        
        # Final fallback
        return ParsingResult(
            ParsedCommand("unknown", {}, 0.0, message),
            0.0, "fallback"
        )
    
    @handle_errors("parsing with rule-based patterns")
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
    
    @handle_errors("parsing with AI enhancement")
    def _ai_enhanced_parse(self, message: str, user_id: str = None) -> ParsingResult:
        """Parse using AI chatbot capabilities"""
        try:
            # Use existing AI chatbot command parsing
            ai_response = self.ai_chatbot.generate_response(
                message, 
                mode="command",
                user_id=user_id,
                timeout=AI_COMMAND_PARSING_TIMEOUT
            )
            
            logger.debug(f"AI response: {ai_response}")
            
            # Try to parse AI response as JSON
            try:
                parsed_data = json.loads(ai_response)
                intent = parsed_data.get('action', 'unknown')
                entities = parsed_data.get('details', {})
                
                # Validate intent against available handlers
                if self._is_valid_intent(intent):
                    confidence = AI_AI_PARSING_BASE_CONFIDENCE
                    return ParsingResult(
                        ParsedCommand(intent, entities, confidence, message),
                        confidence, "ai_enhanced"
                    )
            except json.JSONDecodeError:
                # Try to extract JSON from partial response
                try:
                    # Look for JSON-like structure in the response
                    start_idx = ai_response.find('{')
                    end_idx = ai_response.rfind('}')
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        json_part = ai_response[start_idx:end_idx + 1]
                        parsed_data = json.loads(json_part)
                        intent = parsed_data.get('action', 'unknown')
                        entities = parsed_data.get('details', {})
                        
                        if self._is_valid_intent(intent):
                            confidence = AI_AI_PARSING_PARTIAL_CONFIDENCE
                            return ParsingResult(
                                ParsedCommand(intent, entities, confidence, message),
                                confidence, "ai_enhanced"
                            )
                except (json.JSONDecodeError, ValueError):
                    pass
                
                # AI didn't return valid JSON, try to extract intent from text
                intent = self._extract_intent_from_ai_response(ai_response)
                if intent and self._is_valid_intent(intent):
                    entities = self._extract_entities_from_ai_response(ai_response)
                    return ParsingResult(
                        ParsedCommand(intent, entities, 0.5, message),
                        0.5, "ai_enhanced"
                    )
                
                # If AI response contains the system prompt, it's not following instructions
                if "command parser" in ai_response.lower() or "available actions" in ai_response.lower():
                    logger.debug("AI returned system prompt instead of JSON, using fallback")
                    return ParsingResult(
                        ParsedCommand("unknown", {}, 0.0, message),
                        0.0, "ai_enhanced"
                    )
        
        except Exception as e:
            logger.debug(f"AI parsing failed: {e}")
        
        return ParsingResult(
            ParsedCommand("unknown", {}, 0.0, message),
            0.0, "ai_enhanced"
        )
    
    @handle_errors("extracting entities from rule-based patterns")
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
                
                # Handle natural language patterns for task completion
                if intent == 'complete_task' and identifier.lower() in ['that task', 'the task', 'this task']:
                    # Extract the actual task name from the message context
                    task_name = self._extract_task_name_from_context(message)
                    if task_name:
                        entities['task_identifier'] = task_name
                    else:
                        entities['task_identifier'] = identifier
                else:
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
        
        elif intent == 'task_stats':
            # Extract time period if specified
            if match.groups():
                time_period = match.group(1).strip()
                parsed_period = self._parse_time_period(time_period)
                entities.update(parsed_period)
            else:
                # Default to current week if no time period specified
                entities['days'] = 7
                entities['period_name'] = 'this week'
        
        # Schedule Management Entity Extraction
        elif intent == 'show_schedule':
            # Extract category if specified
            if match.groups():
                category = match.group(1).strip()
                entities['category'] = category
            else:
                entities['category'] = 'all'
        
        elif intent == 'update_schedule':
            # Extract action and category
            if match.groups():
                if len(match.groups()) >= 2:
                    action = match.group(1).strip()
                    category = match.group(2).strip()
                    entities['action'] = action
                    entities['category'] = category
                else:
                    # Handle enable/disable patterns
                    action_match = re.search(r'(enable|disable|turn\s+(on|off))', message.lower())
                    if action_match:
                        action = action_match.group(1)
                        if 'turn' in action:
                            action = 'enable' if 'on' in action else 'disable'
                        entities['action'] = action
                    
                    # Extract category
                    category_match = re.search(r'(tasks?|check.?ins?|messages?)', message.lower())
                    if category_match:
                        entities['category'] = category_match.group(1)
        
        elif intent == 'add_schedule_period':
            # Extract period name and category
            if len(match.groups()) >= 2:
                period_name = match.group(1).strip()
                category = match.group(2).strip()
                entities['period_name'] = period_name
                entities['category'] = category
                
                # Extract time information
                time_match = re.search(r'from\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s+to\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', message.lower())
                if time_match:
                    entities['start_time'] = time_match.group(1)
                    entities['end_time'] = time_match.group(2)
        
        elif intent == 'edit_schedule_period':
            # Extract period name and category
            if len(match.groups()) >= 2:
                period_name = match.group(1).strip()
                category = match.group(2).strip()
                entities['period_name'] = period_name
                entities['category'] = category
                
                # Extract new time information
                time_match = re.search(r'to\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s+to\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', message.lower())
                if time_match:
                    entities['new_start_time'] = time_match.group(1)
                    entities['new_end_time'] = time_match.group(2)
        
        # Analytics Entity Extraction
        elif intent in ['show_analytics', 'mood_trends', 'habit_analysis', 'sleep_analysis', 'wellness_score']:
            # Extract number of days if specified
            days_match = re.search(r'(\d+)\s+days?', message.lower())
            if days_match:
                entities['days'] = int(days_match.group(1))
            else:
                entities['days'] = 30  # Default to 30 days
        
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
    
    def _extract_task_name_from_context(self, message: str) -> Optional[str]:
        """Extract task name from natural language context"""
        # Look for patterns like "I brushed my teeth" -> extract "teeth" or "brush teeth"
        patterns = [
            r'i\s+(?:just\s+)?(?:brushed|washed|cleaned|did|completed|finished)\s+(?:my\s+)?(.+?)(?:\s+today|\s+now|\s+just\s+now|\s*,?\s*we\s+can\s+complete|\s*,?\s*so\s+we\s+can\s+complete)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                task_name = match.group(1).strip()
                return task_name
        
        return None
    
    def _extract_update_entities(self, update_text: str) -> Dict[str, Any]:
        """Extract update entities from update text"""
        entities = {}
        
        # Extract priority
        if re.search(r'priority\s+(high|medium|low)', update_text, re.IGNORECASE):
            match = re.search(r'priority\s+(high|medium|low)', update_text, re.IGNORECASE)
            entities['priority'] = match.group(1)
        
        # Extract due date (support 'due ...' and 'due date ...')
        due_match = re.search(r'(?:due\s+date|due)\s+(.+)', update_text, re.IGNORECASE)
        if due_match:
            entities['due_date'] = due_match.group(1)
        
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
    
    @handle_errors("calculating confidence score")
    def _calculate_confidence(self, intent: str, match: re.Match, message: str) -> float:
        """Calculate confidence score for a parsed command"""
        base_confidence = 0.8
        
        # Boost confidence for exact matches
        if match.group(0).lower() == message.lower().strip():
            base_confidence = 1.0
        
        # Boost confidence for specific intents
        high_confidence_intents = ['help', 'commands', 'examples', 'checkin_history', 'completion_rate', 'task_weekly_stats']
        if intent in high_confidence_intents:
            base_confidence = min(1.0, base_confidence + 0.1)
        
        # Reduce confidence for very short matches
        if len(match.group(0)) < 5:
            base_confidence *= 0.8
        
        # Boost confidence for question marks (indicates intent)
        if '?' in message:
            base_confidence = min(1.0, base_confidence + 0.1)
        
        return min(1.0, base_confidence)
    
    @handle_errors("checking if intent is valid")
    def _is_valid_intent(self, intent: str) -> bool:
        """Check if intent is supported by any handler"""
        for handler in self.interaction_handlers.values():
            if handler.can_handle(intent):
                return True
        return False
    
    @handle_errors("getting command suggestions")
    def get_suggestions(self, partial_message: str) -> List[str]:
        """Get command suggestions based on partial input"""
        suggestions = []
        
        if not partial_message:
            # General suggestions
            suggestions = [
                "Create a task to call mom tomorrow",
                "Show me my tasks",
                "Start a check-in",
                "Show my analytics",
                "Show my schedule"
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
                    "How am I doing this week?",
                    "Mood trends for 7 days"
                ]
            
            # Profile suggestions
            elif any(word in partial_lower for word in ['profile', 'name', 'pronoun']):
                suggestions = [
                    "Show my profile",
                    "Update my name to Julie",
                    "Update my gender identity to Non-binary",
                    "Show my statistics"
                ]
            
            # Schedule suggestions
            elif any(word in partial_lower for word in ['schedule', 'time', 'when', 'reminder']):
                suggestions = [
                    "Show my schedule",
                    "Schedule status",
                    "Enable my task schedule",
                    "Add a new period called morning to my task schedule from 9am to 11am"
                ]
            
            # Analytics suggestions
            elif any(word in partial_lower for word in ['analytics', 'trend', 'analysis', 'how am i doing', 'progress']):
                suggestions = [
                    "Show my analytics",
                    "Mood trends for 7 days",
                    "Habit analysis",
                    "Sleep analysis",
                    "Wellness score"
                ]
            
            # Help suggestions
            elif any(word in partial_lower for word in ['help', 'how', 'what']):
                suggestions = [
                    "Help with tasks",
                    "Help with check-ins",
                    "Help with profile",
                    "Help with schedule",
                    "Help with analytics",
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