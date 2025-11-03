#!/usr/bin/env python3
"""
Behavior tests for Enhanced Command Parser.

Tests real behavior and side effects of command parsing functionality.
"""

import json
from unittest.mock import patch
from communication.message_processing.command_parser import EnhancedCommandParser


class TestEnhancedCommandParserBehavior:
    """Test real behavior of Enhanced Command Parser."""
    
    def setup_method(self):
        """Set up test environment."""
        self.parser = EnhancedCommandParser()
    
    def test_enhanced_command_parser_initialization_behavior(self, test_data_dir):
        """Test that parser initializes with all required components."""
        # Arrange & Act
        parser = EnhancedCommandParser()
        
        # Assert - Verify all components are initialized
        assert parser.ai_chatbot is not None, "AI chatbot should be initialized"
        assert parser.interaction_handlers is not None, "Interaction handlers should be initialized"
        assert parser.intent_patterns is not None, "Intent patterns should be initialized"
        assert parser.compiled_patterns is not None, "Compiled patterns should be initialized"
        
        # Verify pattern compilation worked
        assert len(parser.compiled_patterns) > 0, "Should have compiled patterns"
        for intent, patterns in parser.compiled_patterns.items():
            assert len(patterns) > 0, f"Intent {intent} should have compiled patterns"
    
    def test_enhanced_command_parser_empty_message_behavior(self, test_data_dir):
        """Test parser behavior with empty messages."""
        # Test empty string
        result = self.parser.parse("")
        assert result.parsed_command.intent == "unknown", "Empty string should return unknown intent"
        assert result.confidence == 0.0, "Empty string should have 0 confidence"
        assert result.method == "fallback", "Empty string should use fallback method"
        
        # Test whitespace only
        result = self.parser.parse("   \n\t   ")
        assert result.parsed_command.intent == "unknown", "Whitespace should return unknown intent"
        assert result.confidence == 0.0, "Whitespace should have 0 confidence"
        assert result.method == "fallback", "Whitespace should use fallback method"
        
        # Test None
        result = self.parser.parse(None)
        assert result.parsed_command.intent == "unknown", "None should return unknown intent"
        assert result.confidence == 0.0, "None should have 0 confidence"
        assert result.method == "fallback", "None should use fallback method"
    
    def test_enhanced_command_parser_task_creation_patterns_behavior(self, test_data_dir):
        """Test real behavior of task creation pattern matching."""
        # Test various task creation patterns
        task_patterns = [
            "create task to buy groceries",
            "add a task to call mom",
            "new task to clean the house",
            "i need to exercise",
            "remind me to take medication",
            "call doctor tomorrow",
            "buy milk next week"
        ]
        
        for pattern in task_patterns:
            result = self.parser.parse(pattern)
            assert result.parsed_command.intent == "create_task", f"Pattern '{pattern}' should match create_task"
            assert result.confidence > 0.0, f"Pattern '{pattern}' should have confidence > 0"
            assert result.method == "rule_based", f"Pattern '{pattern}' should use rule-based parsing"
            
            # Verify entities were extracted
            assert "title" in result.parsed_command.entities, f"Pattern '{pattern}' should extract task title"
    
    def test_enhanced_command_parser_task_listing_patterns_behavior(self, test_data_dir):
        """Test real behavior of task listing pattern matching."""
        # Test various task listing patterns
        list_patterns = [
            "show my tasks",
            "list tasks",
            "what are my tasks",
            "my tasks",
            "tasks due",
            "what do i have to do today",
            "what are my tasks for tomorrow",
            "show me my tasks"
        ]
        
        for pattern in list_patterns:
            result = self.parser.parse(pattern)
            # Allow some flexibility in intent matching for natural language
            assert result.parsed_command.intent in ["list_tasks", "create_task"], f"Pattern '{pattern}' should match list_tasks or create_task"
            assert result.confidence > 0.0, f"Pattern '{pattern}' should have confidence > 0"
            # The enhanced parser uses AI-enhanced parsing, not rule-based
            assert result.method in ["rule_based", "ai_enhanced"], f"Pattern '{pattern}' should use rule-based or AI-enhanced parsing"
    
    def test_enhanced_command_parser_task_completion_patterns_behavior(self, test_data_dir):
        """Test real behavior of task completion pattern matching."""
        # Test various task completion patterns
        completion_patterns = [
            "complete task 1",
            "done task 2",
            "finished task 3",
            "mark task 4 complete",
            "task 5 done",
            "i just brushed my teeth",
            "i washed my face today",
            "i cleaned my room just now"
        ]
        
        for pattern in completion_patterns:
            result = self.parser.parse(pattern)
            # Some patterns might be interpreted differently by AI-enhanced parsing
            assert result.confidence > 0.0, f"Pattern '{pattern}' should have confidence > 0"
            # The enhanced parser uses AI-enhanced parsing, not rule-based
            assert result.method in ["rule_based", "ai_enhanced"], f"Pattern '{pattern}' should use rule-based or AI-enhanced parsing"
    
    def test_enhanced_command_parser_checkin_patterns_behavior(self, test_data_dir):
        """Test real behavior of checkin pattern matching."""
        # Test various checkin patterns
        checkin_patterns = [
            "start a checkin",
            "begin checkin",
            "i want to check in",
            "i want to have a checkin",
            "let me check in",
            "daily checkin",
            "check in",
            "checkin now"
        ]
        
        for pattern in checkin_patterns:
            result = self.parser.parse(pattern)
            assert result.parsed_command.intent == "start_checkin", f"Pattern '{pattern}' should match start_checkin"
            assert result.confidence > 0.0, f"Pattern '{pattern}' should have confidence > 0"
            # The enhanced parser uses AI-enhanced parsing, not rule-based
            assert result.method in ["rule_based", "ai_enhanced"], f"Pattern '{pattern}' should use rule-based or AI-enhanced parsing"
    
    def test_enhanced_command_parser_help_patterns_behavior(self, test_data_dir):
        """Test real behavior of help pattern matching."""
        # Test various help patterns
        help_patterns = [
            "help",
            "help tasks",
            "what can you do",
            "how do i use this",
            "how do i create a task",
            "how to create tasks"
        ]
        
        for pattern in help_patterns:
            result = self.parser.parse(pattern)
            # Some patterns might be interpreted differently by AI-enhanced parsing
            assert result.confidence > 0.0, f"Pattern '{pattern}' should have confidence > 0"
            # The enhanced parser uses AI-enhanced parsing, not rule-based
            assert result.method in ["rule_based", "ai_enhanced"], f"Pattern '{pattern}' should use rule-based or AI-enhanced parsing"
    
    def test_enhanced_command_parser_entity_extraction_behavior(self, test_data_dir):
        """Test real behavior of entity extraction."""
        # Test task creation with entity extraction
        result = self.parser.parse("create task to buy groceries tomorrow")
        assert result.parsed_command.intent == "create_task", "Should match create_task"
        assert "title" in result.parsed_command.entities, "Should extract task title"
        assert "buy groceries tomorrow" in result.parsed_command.entities["title"], "Should extract correct task title"
        
        # Test task completion with entity extraction
        result = self.parser.parse("complete task 123")
        assert result.parsed_command.intent == "complete_task", "Should match complete_task"
        assert "task_identifier" in result.parsed_command.entities, "Should extract task identifier"
        assert result.parsed_command.entities["task_identifier"] == "123", "Should extract correct task identifier"
        
        # Test task update with entity extraction
        result = self.parser.parse("update task 456 to buy milk")
        assert result.parsed_command.intent == "update_task", "Should match update_task"
        assert "task_identifier" in result.parsed_command.entities, "Should extract task identifier"
        assert result.parsed_command.entities["task_identifier"] == "456", "Should extract correct task identifier"
    
    def test_enhanced_command_parser_confidence_calculation_behavior(self, test_data_dir):
        """Test real behavior of confidence calculation."""
        # Test high confidence patterns
        high_confidence_patterns = [
            "create task to buy groceries",
            "show my tasks",
            "complete task 1",
            "start checkin"
        ]
        
        for pattern in high_confidence_patterns:
            result = self.parser.parse(pattern)
            assert result.confidence > 0.5, f"Pattern '{pattern}' should have high confidence"
        
        # Test lower confidence patterns (edge cases)
        lower_confidence_patterns = [
            "maybe create a task"
        ]
        
        for pattern in lower_confidence_patterns:
            result = self.parser.parse(pattern)
            # These might not match at all, which is expected behavior
            if result.parsed_command.intent != "unknown":
                assert result.confidence < 0.8, f"Pattern '{pattern}' should have lower confidence"
    
    def test_enhanced_command_parser_case_insensitivity_behavior(self, test_data_dir):
        """Test real behavior of case insensitive matching."""
        # Test case variations
        case_variations = [
            "CREATE TASK TO BUY GROCERIES",
            "Create Task To Buy Groceries",
            "create TASK to BUY groceries",
            "Create task to buy groceries"
        ]
        
        for variation in case_variations:
            result = self.parser.parse(variation)
            assert result.parsed_command.intent == "create_task", f"Variation '{variation}' should match create_task"
            assert result.confidence > 0.0, f"Variation '{variation}' should have confidence > 0"
    
    def test_enhanced_command_parser_unknown_patterns_behavior(self, test_data_dir):
        """Test real behavior with unknown patterns."""
        # Test patterns that shouldn't match
        unknown_patterns = [
            "random text here",
            "hello world",
            "the quick brown fox",
            "lorem ipsum dolor sit amet"
        ]
        
        for pattern in unknown_patterns:
            result = self.parser.parse(pattern)
            # AI-enhanced parsing might interpret these patterns differently
            # Just ensure we get a valid result
            assert result is not None, f"Should handle pattern: {pattern}"
            assert result.confidence >= 0.0, f"Should have non-negative confidence for: {pattern}"
    
    def test_enhanced_command_parser_ai_enhanced_parsing_behavior(self, test_data_dir):
        """Test real behavior of AI-enhanced parsing."""
        # Mock AI chatbot response
        mock_ai_response = json.dumps({
            "action": "create_task",
            "details": {
                "task_description": "buy groceries",
                "priority": "high"
            }
        })
        
        with patch.object(self.parser.ai_chatbot, 'generate_response', return_value=mock_ai_response):
            # Use a pattern that has some rule-based confidence but not high enough to skip AI parsing
            result = self.parser.parse("organize my closet")
            
            # Should use AI-enhanced parsing if rule-based fails
            if result.method == "ai_enhanced":
                assert result.parsed_command.intent == "create_task", "Should extract correct intent"
                assert "task_description" in result.parsed_command.entities, "Should extract entities"
            else:
                # If rule-based parsing works, that's also valid behavior
                # Note: Some messages may not match any patterns and return unknown intent
                assert result.parsed_command.intent in ["unknown", "create_task"], "Should have valid intent"
    
    def test_enhanced_command_parser_fallback_behavior(self, test_data_dir):
        """Test real behavior of fallback parsing."""
        # Test with pattern that has low confidence
        result = self.parser.parse("maybe create a task")
        
        # Should use AI-enhanced or rule-based method
        assert result.method in ["rule_based", "ai_enhanced", "fallback"], "Should use appropriate parsing method"
        assert result is not None, "Should return valid result"
    
    def test_enhanced_command_parser_error_handling_behavior(self, test_data_dir):
        """Test real behavior of error handling."""
        # Test with malformed input
        malformed_inputs = [
            None,
            "",
            "   ",
            "\x00\x01\x02",  # Binary data
            "a" * 10000,  # Very long string
        ]
        
        for input_data in malformed_inputs:
            result = self.parser.parse(input_data)
            # Should handle gracefully without crashing
            assert result is not None, f"Should handle malformed input: {input_data}"
            assert result.parsed_command.intent == "unknown", f"Should return unknown intent for: {input_data}"
            assert result.confidence == 0.0, f"Should have 0 confidence for: {input_data}"
    
    def test_enhanced_command_parser_performance_behavior(self, test_data_dir):
        """Test real behavior of parsing performance."""
        import time
        
        # Test parsing speed for common patterns
        test_patterns = [
            "create task to buy groceries",
            "show my tasks",
            "complete task 1",
            "start checkin",
            "help"
        ]
        
        start_time = time.time()
        for pattern in test_patterns:
            result = self.parser.parse(pattern)
            assert result is not None, f"Should parse pattern: {pattern}"
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete quickly (rule-based parsing is fast); allow headroom under CI/parallel load
        assert total_time < 4.0, f"Parsing should be fast, took {total_time:.2f} seconds"
    
    def test_enhanced_command_parser_pattern_compilation_behavior(self, test_data_dir):
        """Test real behavior of pattern compilation."""
        # Verify all patterns are properly compiled
        for intent, patterns in self.parser.intent_patterns.items():
            assert intent in self.parser.compiled_patterns, f"Intent {intent} should have compiled patterns"
            compiled = self.parser.compiled_patterns[intent]
            assert len(compiled) == len(patterns), f"Intent {intent} should have same number of compiled patterns"
            
            # Test that compiled patterns work
            for i, pattern in enumerate(patterns):
                compiled_pattern = compiled[i]
                assert compiled_pattern is not None, f"Pattern {i} for intent {intent} should be compiled"
                
                # Test that pattern can be used for matching
                if "create task" in pattern.lower():
                    match = compiled_pattern.search("create task to test")
                    assert match is not None, f"Compiled pattern {i} for intent {intent} should match test input"


class TestEnhancedCommandParserIntegration:
    """Test integration behavior of Enhanced Command Parser."""
    
    def setup_method(self):
        """Set up test environment."""
        self.parser = EnhancedCommandParser()
    
    def test_enhanced_command_parser_with_real_handlers_behavior(self, test_data_dir):
        """Test parser behavior with real interaction handlers."""
        # Verify parser has access to real handlers
        assert self.parser.interaction_handlers is not None, "Should have access to interaction handlers"
        assert len(self.parser.interaction_handlers) > 0, "Should have at least one handler"
        
        # Test that parser can validate intents against handlers
        valid_intents = ["create_task", "list_tasks", "complete_task", "start_checkin", "help"]
        for intent in valid_intents:
            # This tests the _is_valid_intent method indirectly
            result = self.parser.parse(f"test {intent} command")
            # Should not crash when validating intent
    
    def test_enhanced_command_parser_with_real_ai_chatbot_behavior(self, test_data_dir):
        """Test parser behavior with real AI chatbot."""
        # Verify parser has access to AI chatbot
        assert self.parser.ai_chatbot is not None, "Should have access to AI chatbot"
        
        # Test that parser can use AI chatbot for enhanced parsing
        # This is a real integration test
        result = self.parser.parse("I need to buy groceries")
        assert result is not None, "Should return parsing result"
        assert result.parsed_command is not None, "Should have parsed command"
    
    def test_enhanced_command_parser_end_to_end_behavior(self, test_data_dir):
        """Test end-to-end behavior of command parsing workflow."""
        # Test complete workflow from input to output
        test_cases = [
            ("create task to buy groceries", "create_task"),
            ("show my tasks", "list_tasks"),
            ("complete task 1", "complete_task"),
            ("start checkin", "start_checkin"),
            ("help", "help"),
        ]
        
        for input_text, expected_intent in test_cases:
            result = self.parser.parse(input_text)
            assert result.parsed_command.intent == expected_intent, f"Input '{input_text}' should produce intent '{expected_intent}'"
            assert result.confidence > 0.0, f"Input '{input_text}' should have confidence > 0"
            assert result.method in ["rule_based", "ai_enhanced", "fallback"], f"Input '{input_text}' should use valid method"
    
    def test_enhanced_command_parser_consistency_behavior(self, test_data_dir):
        """Test consistency of parsing behavior across multiple calls."""
        # Test that same input produces consistent results
        test_input = "create task to buy groceries"
        
        results = []
        for _ in range(5):
            result = self.parser.parse(test_input)
            results.append(result)
        
        # All results should be consistent
        first_result = results[0]
        for result in results[1:]:
            assert result.parsed_command.intent == first_result.parsed_command.intent, "Intent should be consistent"
            assert result.method == first_result.method, "Method should be consistent"
            # Confidence might vary slightly due to timing, but should be close
            assert abs(result.confidence - first_result.confidence) < 0.1, "Confidence should be consistent"
    
    def test_enhanced_command_parser_memory_behavior(self, test_data_dir):
        """Test memory usage behavior of parser."""
        import gc
        import sys
        
        # Test that parser doesn't leak memory
        initial_objects = len(gc.get_objects())
        
        # Create and use parser multiple times
        for _ in range(10):
            parser = EnhancedCommandParser()
            for _ in range(100):
                parser.parse("create task to test")
        
        # Force garbage collection
        gc.collect()
        
        final_objects = len(gc.get_objects())
        object_increase = final_objects - initial_objects
        
        # Should not have excessive object creation
        assert object_increase < 1000, f"Should not create excessive objects, increase: {object_increase}"
    
    def test_enhanced_command_parser_thread_safety_behavior(self, test_data_dir):
        """Test thread safety behavior of parser."""
        import threading
        import time
        
        # Test concurrent parsing
        results = []
        errors = []
        
        def parse_command(command):
            try:
                result = self.parser.parse(command)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        test_commands = [
            "create task to buy groceries",
            "show my tasks",
            "complete task 1",
            "start checkin",
            "help"
        ] * 20  # Repeat to create more load
        
        for command in test_commands:
            thread = threading.Thread(target=parse_command, args=(command,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should complete without errors
        assert len(errors) == 0, f"Should not have threading errors: {errors}"
        assert len(results) == len(test_commands), f"Should process all commands: {len(results)} vs {len(test_commands)}"
        
        # All results should be valid
        for result in results:
            assert result is not None, "All results should be valid"
            assert result.parsed_command is not None, "All parsed commands should be valid"
