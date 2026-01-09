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
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from core.logger import get_component_logger
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
    
    @handle_errors("initializing enhanced command parser")
    def __init__(self):
        """
        Initialize the enhanced command parser.
        
        Sets up the parser with AI chatbot integration and interaction handlers,
        and initializes rule-based intent patterns for common commands.
        """
        self.ai_chatbot = get_ai_chatbot()
        self.interaction_handlers = get_all_handlers()
        
        # Rule-based patterns for common intents
        self.intent_patterns = {
            'create_task': [
                r'^nt\s+(.+)$',
                r'^ntask\s+(.+)$',
                r'^newt\s+(.+)$',
                r'^newtask\s+(.+)$',
                r'^ct\s+(.+)$',
                r'^ctask\s+(.+)$',
                r'^createtask\s+(.+)$',
                r'^createt\s+(.+)$',
                r'^task\s+(.+)$',
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
                r'^show\s+my\s+tasks?$',  # Match "show my tasks" first (more specific)
                r'^show\s+tasks?$',  # Then match "show tasks"
                r'^list\s+my\s+tasks?$',
                r'^list\s+tasks?$',
                r'^what\s+are\s+my\s+tasks?$',
                r'^what\s+are\s+tasks?$',
                r'^my\s+tasks?$',
                r'^tasks?\s+due$',
                r'^what\s+do\s+i\s+have\s+to\s+do\s+(?:today|tomorrow)$',
                r'^what\s+are\s+my\s+tasks?\s+(?:for\s+today|for\s+tomorrow)$',
                r'^show\s+me\s+my\s+tasks?$',
            ],
            'complete_task': [
                r'^complete\s+(.+)$',
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
            'edit_schedule_period': [
                # Edit schedule period even without times, capturing period name and category
                r'edit\s+(?:the\s+)?([\w\-]+)\s+period\s+in\s+my\s+(tasks?|check.?ins?|messages?)\s+schedule',
                r'edit\s+schedule\s+period\s+([\w\-]+)\s+(tasks?|check.?ins?|messages?)',
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
                r'^help$',  # Exact match for "help" - check first
                r'^help\s+(tasks?|check.?in|profile)$',
                r'^what\s+can\s+you\s+do$',
                r'^how\s+do\s+i\s+use\s+this$',
                r'^how\s+do\s+i\s+create\s+a\s+task$',
                r'^how\s+do\s+i\s+create\s+tasks?$',
                r'^how\s+to\s+create\s+a\s+task$',
                r'^how\s+to\s+create\s+tasks?$',
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
            # Notebook Patterns
            'create_note': [
                r'^nn\s+(.+)$',
                r'^nnote\s+(.+)$',
                r'^newn\s+(.+)$',
                r'^newnote\s+(.+)$',
                r'^cn\s+(.+)$',
                r'^cnote\s+(.+)$',
                r'^createnote\s+(.+)$',
                r'^createn\s+(.+)$',
                r'^n\s+(.+)$',
                r'^note\s+(.+)$',
                r'^n\s+(.+)$',
                r'^note\s+(.+)',
                r'note\s+(.+)',
                r'new\s+note\s+(.+)',
                r'create\s+note\s+(?:about\s+)?(.+)',  # Match "create note about X" without hallucinating details
            ],
            'list_recent_entries': [
                r'^recent(?:\s+(\d+))?$',
                r'^r(?:\s+(\d+))?$',
                r'^recent(?:\s+(\d+))?$',
                r'recent\s+entries?(?:\s+(\d+))?',
                r'show\s+recent(?:\s+(\d+))?',
            ],
            'list_recent_notes': [
                r'^recentn(?:\s+(\d+))?$',
                r'^rnote(?:\s+(\d+))?$',
                r'^rnotes(?:\s+(\d+))?$',
                r'^recentnote(?:\s+(\d+))?$',
                r'^recentnotes(?:\s+(\d+))?$',
                r'^shown(?:\s+(\d+))?$',
                r'^shownote(?:\s+(\d+))?$',
                r'^shownotes(?:\s+(\d+))?$',
            ],
            'show_entry': [
                r'^show\s+(?!my\s+tasks?$|me\s+my\s+tasks?$)(.+)$',  # Exclude "show my tasks" - handled by list_tasks
                r'^display\s+(?!my\s+tasks?$)(.+)$',
                r'^view\s+(?!my\s+tasks?$)(.+)$',
            ],
            'append_to_entry': [
                r'^append\s+(\S+)\s+(.+)$',
                r'^add\s+(\S+)\s+(.+)$',
                r'^addto\s+(\S+)\s+(.+)$',
                r'add\s+to\s+(\S+)\s+(.+)',
            ],
            'add_tags_to_entry': [
                r'^tag\s+(\S+)\s+(.+)$',
                r'^tag\s+(\S+)\s+(.+)$',
                r'add\s+tags?\s+to\s+(\S+)\s+(.+)',
            ],
            'remove_tags_from_entry': [
                r'^untag\s+(\S+)\s+(.+)$',
                r'^untag\s+(\S+)\s+(.+)$',
                r'remove\s+tags?\s+from\s+(\S+)\s+(.+)',
            ],
            'search_entries': [
                r'^search\s+(.+)$',
                r'^s\s+(.+)$',
                r'^s\s+(.+)$',
                r'search\s+(.+)',
                r'find\s+(.+)',
            ],
            'pin_entry': [
                r'^pin\s+(.+)$',
                r'^pin\s+(.+)$',
            ],
            'unpin_entry': [
                r'^!unpin\s+(.+)$',
                r'^unpin\s+(.+)$',
            ],
            'archive_entry': [
                r'^archive\s+(.+)$',
                r'^archive\s+(.+)$',
            ],
            'unarchive_entry': [
                r'^unarchive\s+(.+)$',
                r'^unarchive\s+(.+)$',
            ],
            'create_list': [
                r'^l\s+(.+)$',
                r'^list\s+(.+)$',
                r'^nl\s+(.+)$',
                r'^nlist\s+(.+)$',
                r'^newl\s+(.+)$',
                r'^newlist\s+(.+)$',
                r'^cl\s+(.+)$',
                r'^clist\s+(.+)$',
                r'^createlist\s+(.+)$',
                r'^createl\s+(.+)$',
                r'^l\s+new\s+(.+)$',
                r'^l\s+new\s+(.+)$',
                r'new\s+list\s+(.+)',
            ],
            'add_list_item': [
                r'^l\s+add\s+(\S+)\s+(.+)$',
                r'^l\s+add\s+(\S+)\s+(.+)$',
            ],
            'toggle_list_item_done': [
                r'^l\s+done\s+(\S+)\s+(\d+)$',
                r'^l\s+done\s+(\S+)\s+(\d+)$',
            ],
            'toggle_list_item_undone': [
                r'^l\s+undo\s+(\S+)\s+(\d+)$',
                r'^l\s+undo\s+(\S+)\s+(\d+)$',
            ],
            'remove_list_item': [
                r'^l\s+remove\s+(\S+)\s+(\d+)$',
                r'^l\s+remove\s+(\S+)\s+(\d+)$',
            ],
            'set_entry_group': [
                r'^group\s+(\S+)\s+(.+)$',
                r'^group\s+(\S+)\s+(.+)$',
            ],
            'list_entries_by_group': [
                r'^group\s+(.+)$',
                r'^group\s+(.+)$',
            ],
            'list_pinned_entries': [
                r'^pinned$',
                r'^pinned$',
            ],
            'list_inbox_entries': [
                r'^inbox$',
                r'^inbox$',
            ],
            'list_entries_by_tag': [
                r'^t\s+(.+)$',
                r'^t\s+(.+)$',
            ],
        }
        
        # Compile patterns for performance
        # Use DOTALL flag so . matches newlines (for multi-line command input)
        self.compiled_patterns = {}
        for intent, patterns in self.intent_patterns.items():
            self.compiled_patterns[intent] = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in patterns]
    
    
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
        
        # Special handling: Check high-priority patterns first to ensure they take precedence
        # Check help patterns first (simple, common command) - use exact match check
        if message_lower == 'help':
            # Direct match for simple "help" command to avoid any pattern issues
            return ParsingResult(
                ParsedCommand('help', {}, 1.0, message),
                1.0, "rule_based"
            )
        
        # Check other help patterns
        if 'help' in self.compiled_patterns:
            for pattern in self.compiled_patterns['help']:
                match = pattern.match(message_lower)
                if match:
                    entities = self._extract_entities_rule_based('help', match, message)
                    confidence = self._calculate_confidence('help', match, message)
                    
                    return ParsingResult(
                        ParsedCommand('help', entities, confidence, message),
                        confidence, "rule_based"
                    )
        
        # Check list_tasks patterns second to ensure they take precedence over show_entry patterns
        if 'list_tasks' in self.compiled_patterns:
            for pattern in self.compiled_patterns['list_tasks']:
                match = pattern.match(message_lower)
                if match:
                    entities = self._extract_entities_rule_based('list_tasks', match, message)
                    confidence = self._calculate_confidence('list_tasks', match, message)
                    
                    return ParsingResult(
                        ParsedCommand('list_tasks', entities, confidence, message),
                        confidence, "rule_based"
                    )
        
        # Check each intent pattern (excluding help and list_tasks which were already checked)
        for intent, patterns in self.compiled_patterns.items():
            if intent in ['help', 'list_tasks']:  # Skip, already checked above
                continue
            for pattern in patterns:
                # Use match() for patterns that start with ^, search() for others
                match = pattern.match(message_lower) if pattern.pattern.startswith('^') else pattern.search(message_lower)
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
            
            # Try to parse AI response - support multiple formats:
            # 1. JSON format (legacy): {"action": "...", "details": {...}}
            # 2. Key-value format (preferred): ACTION: ... \n TITLE: ...
            # 3. Natural language (fallback)
            
            # Strategy 1: Try key-value format (new preferred format - AI-friendly)
            if 'ACTION:' in ai_response or 'action:' in ai_response:
                intent, entities = self._parse_key_value_format(ai_response)
                if intent and self._is_valid_intent(intent):
                    confidence = AI_AI_PARSING_BASE_CONFIDENCE
                    return ParsingResult(
                        ParsedCommand(intent, entities, confidence, message),
                        confidence, "ai_enhanced"
                    )
            
            # Strategy 2: Try JSON format (legacy support)
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
    
    @handle_errors("parsing key-value format")
    def _parse_key_value_format(self, response: str) -> tuple:
        """
        Parse key-value format (ACTION: ..., TITLE: ..., etc.)
        Returns (intent, entities) tuple
        """
        intent = None
        entities = {}
        
        lines = response.split('\n')
        for line in lines:
            line_stripped = line.strip()
            if ':' not in line_stripped:
                continue
            
            key, value = line_stripped.split(':', 1)
            key = key.strip().upper()
            value = value.strip()
            
            if key == 'ACTION':
                intent = value.lower().strip()
                # Map common variations
                if intent == 'create task':
                    intent = 'create_task'
                elif intent == 'list tasks':
                    intent = 'list_tasks'
                elif intent == 'complete task':
                    intent = 'complete_task'
                # Add other common mappings as needed
            elif key == 'TITLE':
                entities['title'] = value
            elif key == 'TASK_ID' or key == 'TASKID':
                entities['task_identifier'] = value
            elif key == 'PRIORITY':
                entities['priority'] = value.lower()
            elif key == 'DUE_DATE' or key == 'DUEDATE':
                entities['due_date'] = value
            elif key == 'DETAILS':
                # Details might be a JSON string or key-value pairs
                try:
                    entities.update(json.loads(value))
                except:
                    # If not JSON, just store as string
                    entities['details'] = value
        
        return (intent, entities)
    
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
                
                # Strip "task " prefix if present (e.g., "task 1" -> "1")
                if identifier.lower().startswith('task '):
                    identifier = identifier[5:].strip()  # Remove "task " prefix
                
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
        
        # Notebook Entity Extraction
        elif intent == 'create_note':
            if match.groups():
                content = match.group(1).strip()
                # Check for title : body format or newline separator
                if ':' in content and '\n' not in content:
                    # Single line with colon separator
                    parts = content.split(':', 1)
                    entities['title'] = parts[0].strip()
                    entities['body'] = parts[1].strip() if len(parts) > 1 else None
                elif '\n' in content:
                    # Multi-line: first line is title, rest is body
                    lines = content.split('\n', 1)
                    entities['title'] = lines[0].strip()
                    entities['body'] = lines[1].strip() if len(lines) > 1 else None
                else:
                    # Just title/body, no separator - will prompt for body in flow
                    entities['title'] = content
                    entities['body'] = None
        
        elif intent in ['list_recent_entries', 'list_recent_notes']:
            if match.groups():
                limit = match.group(1)
                try:
                    entities['limit'] = int(limit)
                except (ValueError, TypeError):
                    entities['limit'] = 5
            else:
                entities['limit'] = 5
        
        elif intent == 'show_entry':
            if match.groups():
                entities['entry_ref'] = match.group(1).strip()
        
        elif intent == 'append_to_entry':
            if len(match.groups()) >= 2:
                entities['entry_ref'] = match.group(1).strip()
                entities['text'] = match.group(2).strip()
        
        elif intent == 'add_tags_to_entry':
            if len(match.groups()) >= 2:
                entities['entry_ref'] = match.group(1).strip()
                # Parse tags from text (supports #tag and space-separated)
                tag_text = match.group(2).strip()
                tags = []
                # Extract #tags
                tags.extend(re.findall(r'#(\w+)', tag_text))
                # Extract space-separated tags
                remaining = re.sub(r'#\w+', '', tag_text).strip()
                if remaining:
                    tags.extend(remaining.split())
                entities['tags'] = tags
        
        elif intent == 'remove_tags_from_entry':
            if len(match.groups()) >= 2:
                entities['entry_ref'] = match.group(1).strip()
                tag_text = match.group(2).strip()
                tags = []
                tags.extend(re.findall(r'#(\w+)', tag_text))
                remaining = re.sub(r'#\w+', '', tag_text).strip()
                if remaining:
                    tags.extend(remaining.split())
                entities['tags'] = tags
        
        elif intent == 'search_entries':
            if match.groups():
                entities['query'] = match.group(1).strip()
        
        elif intent in ['pin_entry', 'unpin_entry', 'archive_entry', 'unarchive_entry']:
            if match.groups():
                entities['entry_ref'] = match.group(1).strip()
        
        elif intent == 'create_list':
            if match.groups():
                content = match.group(1).strip()
                # Check for title : items or newline separator
                if ':' in content and '\n' not in content:
                    # Single line with colon separator
                    parts = content.split(':', 1)
                    title = parts[0].strip()
                    items_text = parts[1].strip() if len(parts) > 1 else ''
                    # Parse items (comma, semicolon separated)
                    items = []
                    if ',' in items_text:
                        items = [item.strip() for item in items_text.split(',')]
                    elif ';' in items_text:
                        items = [item.strip() for item in items_text.split(';')]
                    elif items_text:
                        items = [items_text]
                    entities['items'] = items
                elif '\n' in content:
                    # Multi-line: first line is title, rest are items
                    lines = content.split('\n')
                    title = lines[0].strip()
                    items = [line.strip() for line in lines[1:] if line.strip()]
                    entities['items'] = items
                else:
                    # Just title, no items - will prompt in flow
                    title = content
                    entities['items'] = []
                
                # Parse title and tags
                from core.tags import parse_tags_from_text
                title, tags = parse_tags_from_text(title)
                entities['title'] = title
                if tags:
                    entities['tags'] = tags
        
        elif intent == 'add_list_item':
            if len(match.groups()) >= 2:
                entities['entry_ref'] = match.group(1).strip()
                entities['item_text'] = match.group(2).strip()
        
        elif intent in ['toggle_list_item_done', 'toggle_list_item_undone']:
            if len(match.groups()) >= 2:
                entities['entry_ref'] = match.group(1).strip()
                try:
                    entities['item_index'] = int(match.group(2))
                except (ValueError, TypeError):
                    pass
                # For undone, set done=False
                if intent == 'toggle_list_item_undone':
                    entities['done'] = False
        
        elif intent == 'remove_list_item':
            if len(match.groups()) >= 2:
                entities['entry_ref'] = match.group(1).strip()
                try:
                    entities['item_index'] = int(match.group(2))
                except (ValueError, TypeError):
                    pass
        
        elif intent == 'set_entry_group':
            if len(match.groups()) >= 2:
                entities['entry_ref'] = match.group(1).strip()
                entities['group'] = match.group(2).strip()
        
        elif intent == 'list_entries_by_group':
            if match.groups():
                entities['group'] = match.group(1).strip()
        
        elif intent == 'list_entries_by_tag':
            if match.groups():
                entities['tag'] = match.group(1).strip()
        
        return entities
    
    @handle_errors("extracting task entities")
    def _extract_task_entities(self, title: str) -> Dict[str, Any]:
        """Extract task-related entities from title"""
        try:
            entities = {}
            
            # Extract due date - order matters! More specific patterns first
            due_patterns = [
                r'in\s+(\d+)\s+hours?',  # "in 48 hours", "in 1 hour" - check before days
                r'in\s+(\d+)\s+days?',  # "in 11 days", "in 1 day", "in 6 days"
                r'in\s+(\d+)\s+weeks?',  # "in 2 weeks", "in 1 week"
                r'next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)',  # "next Tuesday at 11:00"
                r'next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',  # "next Tuesday", "next Monday"
                r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)',  # "Friday at noon", "Monday at 2pm"
                r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',  # "Friday", "Monday"
                r'tomorrow',
                r'next\s+week',
                r'next\s+month',
                r'on\s+(\w+\s+\d+)',
                r'by\s+(\w+\s+\d+)',
            ]
            
            # Try to find the longest/best match by checking all patterns and picking the best one
            best_match = None
            best_pattern_index = -1
            
            for i, pattern in enumerate(due_patterns):
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    # Prefer earlier patterns (more specific) and longer matches
                    if best_match is None or len(match.group(0)) > len(best_match.group(0)) or i < best_pattern_index:
                        best_match = match
                        best_pattern_index = i
            
            if best_match:
                entities['due_date'] = best_match.group(0)
                # If pattern has time component (day of week + time), extract time separately
                # Check if this is a "next [day] at [time]" or "[day] at [time]" pattern
                if len(best_match.groups()) >= 2:
                    # Pattern like "next Tuesday at 11:00" - group(1) is day, group(2) is time
                    # Pattern like "Friday at noon" - group(1) is day, group(2) is time
                    if best_match.group(2):  # Time component exists
                        time_str = best_match.group(2).strip()
                        entities['due_time'] = time_str
            
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
        except Exception as e:
            logger.error(f"Error extracting task entities: {e}")
            return {}

    @handle_errors("extracting task name from context")
    def _extract_task_name_from_context(self, message: str) -> Optional[str]:
        """Extract task name from natural language context"""
        try:
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
        except Exception as e:
            logger.error(f"Error extracting task name from context: {e}")
            return None

    @handle_errors("extracting update entities")
    def _extract_update_entities(self, update_text: str) -> Dict[str, Any]:
        """Extract update entities from update text"""
        try:
            entities = {}
            
            # Extract priority (high, medium, low, urgent, critical)
            # Pattern allows for "priority high", "priority to high", etc.
            priority_match = re.search(r'priority\s+(?:to\s+)?(high|medium|low|urgent|critical)', update_text, re.IGNORECASE)
            if priority_match:
                entities['priority'] = priority_match.group(1).lower()
            
            # Extract due date (support 'due ...' and 'due date ...')
            due_match = re.search(r'(?:due\s+date|due)\s+(.+)', update_text, re.IGNORECASE)
            if due_match:
                entities['due_date'] = due_match.group(1)

            # Extract title (support: title New Name, title "New Name", rename to New Name)
            title_match = re.search(r'(?:title\s+"([^"]+)"|title\s+([^\n]+)|rename\s+(?:task\s+)?(?:to\s+)?"?([^"\n]+)"?)', update_text, re.IGNORECASE)
            if title_match:
                new_title = title_match.group(1) or title_match.group(2) or title_match.group(3)
                if new_title:
                    entities['title'] = new_title.strip()
            
            return entities
        except Exception as e:
            logger.error(f"Error extracting update entities: {e}")
            return {}

    @handle_errors("extracting intent from AI response")
    def _extract_intent_from_ai_response(self, ai_response: str) -> Optional[str]:
        """Extract intent from AI response text"""
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
        except Exception as e:
            logger.error(f"Error extracting intent from AI response: {e}")
            return None

    @handle_errors("extracting entities from AI response")
    def _extract_entities_from_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Extract entities from AI response text"""
        try:
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
        except Exception as e:
            logger.error(f"Error extracting entities from AI response: {e}")
            return {}

    @handle_errors("calculating confidence score")
    def _calculate_confidence(self, intent: str, match: re.Match, message: str) -> float:
        """Calculate confidence score for a parsed command"""
        try:
            base_confidence = 0.8
            
            # Boost confidence for exact matches
            if match.group(0).lower() == message.lower().strip():
                base_confidence = 1.0
            
            # Boost confidence for specific intents
            high_confidence_intents = ['help', 'commands', 'examples', 'checkin_history', 'completion_rate', 'task_weekly_stats', 'list_tasks']
            if intent in high_confidence_intents:
                base_confidence = min(1.0, base_confidence + 0.1)
            
            # Ensure help gets maximum confidence for exact match
            if intent == 'help' and match.group(0).lower() == message.lower().strip():
                base_confidence = 1.0
            
            # Reduce confidence for very short matches
            if len(match.group(0)) < 5:
                base_confidence *= 0.8
            
            # Boost confidence for question marks (indicates intent)
            if '?' in message:
                base_confidence = min(1.0, base_confidence + 0.1)
        
            return min(1.0, base_confidence)
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5
    
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
    
    @handle_errors("getting command suggestions")
    def get_suggestions(self, partial_message: str) -> List[str]:
        """Get command suggestions based on partial input"""
        try:
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
        except Exception as e:
            logger.error(f"Error getting command suggestions: {e}")
            return ["Help", "Show my tasks", "Start a check-in"]

# Global instance
_parser_instance = None

@handle_errors("getting enhanced command parser")
def get_enhanced_command_parser() -> EnhancedCommandParser:
    """Get the global enhanced command parser instance"""
    try:
        global _parser_instance
        if _parser_instance is None:
            _parser_instance = EnhancedCommandParser()
        return _parser_instance
    except Exception as e:
        logger.error(f"Error getting enhanced command parser: {e}")
        raise

@handle_errors("parsing command", default_return=ParsingResult(
    ParsedCommand("unknown", {}, 0.0, ""), 0.0, "fallback"
))
def parse_command(message: str) -> ParsingResult:
    """Convenience function to parse a command"""
    try:
        parser = get_enhanced_command_parser()
        return parser.parse(message)
    except Exception as e:
        logger.error(f"Error parsing command: {e}")
        return ParsingResult(
            ParsedCommand("unknown", {}, 0.0, message),
            0.0, "fallback"
        ) 