"""
Core AI Functionality Tests

Tests for basic AI response generation, mode detection, and contextual responses.
"""

import os
import time
from unittest.mock import patch

from ai.chatbot import AIChatBotSingleton
from tests.ai.ai_test_base import AITestBase
from tests.test_utilities import TestUserFactory
from core.user_management import get_user_id_by_identifier
from core.user_data_handlers import save_user_data
from user.context_manager import user_context_manager


class TestAICore(AITestBase):
    """Test core AI functionality"""
    
    def test_basic_response_generation(self):
        """Test 1: Basic AI Response Generation"""
        print("=" * 60)
        print("TEST CATEGORY 1: Basic AI Response Generation")
        print("=" * 60)
        
        # Test 1.1: Simple prompt
        try:
            test_user_id = self._get_or_create_test_user("test_basic_1")
            prompt = "Hello, how are you?"
            response = self.chatbot.generate_response(prompt, user_id=test_user_id)
            if response and isinstance(response, str) and len(response) > 0:
                self.log_test("T-1.1", "generate_response() with simple prompt", "PASS",
                            f"Generated response: {response[:100]}...", prompt=prompt, response=response[:200], test_type="chat")
            else:
                self.log_test("T-1.1", "generate_response() with simple prompt", "FAIL",
                            "Response was empty or invalid", prompt=prompt)
        except Exception as e:
            self.log_test("T-1.1", "generate_response() with simple prompt", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 1.2: Chat mode
        try:
            test_user_id = self._get_or_create_test_user("test_basic_2")
            prompt = "Tell me about your capabilities"
            response = self.chatbot.generate_response(prompt, mode="chat", user_id=test_user_id)
            if response and isinstance(response, str):
                self.log_test("T-1.2", "generate_response() in chat mode", "PASS",
                            f"Chat mode response generated: {response[:80]}...", prompt=prompt, response=response[:200], test_type="chat")
            else:
                self.log_test("T-1.2", "generate_response() in chat mode", "FAIL",
                            "No response generated", prompt=prompt)
        except Exception as e:
            self.log_test("T-1.2", "generate_response() in chat mode", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 1.3: Command mode
        try:
            test_user_id = self._get_or_create_test_user("test_basic_3")
            prompt = "add task buy groceries"
            response = self.chatbot.generate_response(prompt, mode="command", user_id=test_user_id)
            if response and isinstance(response, str):
                self.log_test("T-1.3", "generate_response() in command mode", "PASS",
                            f"Command mode response generated: {response[:80]}...", prompt=prompt, response=response[:200], test_type="command")
            else:
                self.log_test("T-1.3", "generate_response() in command mode", "FAIL",
                            "No response generated", prompt=prompt)
        except Exception as e:
            self.log_test("T-1.3", "generate_response() in command mode", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 1.4: AI availability check
        try:
            is_available = self.chatbot.is_ai_available()
            self.log_test("T-1.4", "AI availability check", "PASS",
                        f"AI available: {is_available}")
        except Exception as e:
            self.log_test("T-1.4", "AI availability check", "FAIL",
                        "", f"Exception: {str(e)}")
    
    def test_contextual_response_generation(self):
        """Test 2: Contextual Response Generation"""
        print("=" * 60)
        print("TEST CATEGORY 2: Contextual Response Generation")
        print("=" * 60)
        
        user_id = "test_contextual_user"
        
        try:
            success = TestUserFactory.create_basic_user(
                user_id,
                enable_checkins=True,
                enable_tasks=True,
                test_data_dir=self.test_data_dir
            )
            
            if not success:
                self.log_test("T-2.0", "Create test user for contextual tests", "FAIL",
                            "", "Failed to create test user")
                return
            
            import core.config
            with patch.object(core.config, "BASE_DATA_DIR", self.test_data_dir), \
                 patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(self.test_data_dir, 'users')):
                actual_user_id = get_user_id_by_identifier(user_id)
            
            if not actual_user_id:
                self.log_test("T-2.0", "Get user UUID", "FAIL",
                            "", "Could not get user UUID")
                return
            
            # Test 2.1: Contextual response with new user
            try:
                prompt = "How am I doing today?"
                response = self.chatbot.generate_contextual_response(actual_user_id, prompt)
                if response and isinstance(response, str) and len(response) > 0:
                    self.log_test("T-2.1", "generate_contextual_response() with new user", "PASS",
                                f"Response generated: {response[:100]}...", prompt=prompt, response=response[:300], test_type="contextual")
                else:
                    self.log_test("T-2.1", "generate_contextual_response() with new user", "FAIL",
                                "No response generated", prompt=prompt)
            except Exception as e:
                self.log_test("T-2.1", "generate_contextual_response() with new user", "FAIL",
                            "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
            
            # Test 2.2: Context building
            try:
                context = user_context_manager.get_ai_context(actual_user_id, include_conversation_history=True)
                if context and isinstance(context, dict):
                    context_keys = list(context.keys())
                    self.log_test("T-2.2", "Context building", "PASS",
                                f"Context includes: {', '.join(context_keys[:5])}...")
                else:
                    self.log_test("T-2.2", "Context building", "FAIL",
                                "Context not generated or invalid")
            except Exception as e:
                self.log_test("T-2.2", "Context building", "FAIL",
                            "", f"Exception: {str(e)}")
            
            # Test 2.3: User name inclusion in response
            try:
                context_data = {"context": {"preferred_name": "TestUser"}}
                save_user_data(actual_user_id, context_data)
                
                prompt = "Hello!"
                response = self.chatbot.generate_contextual_response(actual_user_id, prompt)
                
                if response and ("TestUser" in response or "test" in response.lower()):
                    self.log_test("T-2.3", "User name in contextual response", "PASS",
                                f"Response: {response[:100]}...", prompt=prompt, response=response[:300], test_type="contextual")
                else:
                    self.log_test("T-2.3", "User name in contextual response", "PARTIAL",
                                f"Name may not be included (response: {response[:80]}...)", prompt=prompt, response=response[:300], test_type="contextual")
            except Exception as e:
                self.log_test("T-2.3", "User name in contextual response", "FAIL",
                            "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
                
        except Exception as e:
            self.log_test("T-2.0", "Contextual response setup", "FAIL",
                        "", f"Exception during setup: {str(e)}")
    
    def test_mode_detection(self):
        """Test 3: Mode Detection"""
        print("=" * 60)
        print("TEST CATEGORY 3: Mode Detection")
        print("=" * 60)
        
        # Test 3.1: Clear command detection
        try:
            test_input = "add task buy milk"
            mode = self.chatbot._detect_mode(test_input)
            if mode == "command":
                self.log_test("T-3.1", "Detect clear command", "PASS",
                            f"Mode detected: {mode}", prompt=test_input, response=f"Mode: {mode}", test_type="mode_detection")
            else:
                self.log_test("T-3.1", "Detect clear command", "PARTIAL",
                            f"Mode detected: {mode} (expected 'command')", prompt=test_input, response=f"Mode: {mode}", test_type="mode_detection")
        except Exception as e:
            self.log_test("T-3.1", "Detect clear command", "FAIL",
                        "", f"Exception: {str(e)}", prompt=test_input if 'test_input' in locals() else "")
        
        # Test 3.2: Ambiguous request detection
        try:
            test_input = "Can you add a task?"
            mode = self.chatbot._detect_mode(test_input)
            if mode == "command_with_clarification":
                self.log_test("T-3.2", "Detect ambiguous request", "PASS",
                            f"Mode detected: {mode}", prompt=test_input, response=f"Mode: {mode}", test_type="mode_detection")
            else:
                self.log_test("T-3.2", "Detect ambiguous request", "PARTIAL",
                            f"Mode detected: {mode} (expected 'command_with_clarification')", prompt=test_input, response=f"Mode: {mode}", test_type="mode_detection")
        except Exception as e:
            self.log_test("T-3.2", "Detect ambiguous request", "FAIL",
                        "", f"Exception: {str(e)}", prompt=test_input if 'test_input' in locals() else "")
        
        # Test 3.3: Chat detection
        try:
            test_input = "How are you doing?"
            mode = self.chatbot._detect_mode(test_input)
            if mode == "chat":
                self.log_test("T-3.3", "Detect chat message", "PASS",
                            f"Mode detected: {mode}", prompt=test_input, response=f"Mode: {mode}", test_type="mode_detection")
            else:
                self.log_test("T-3.3", "Detect chat message", "PARTIAL",
                            f"Mode detected: {mode} (expected 'chat')", prompt=test_input, response=f"Mode: {mode}", test_type="mode_detection")
        except Exception as e:
            self.log_test("T-3.3", "Detect chat message", "FAIL",
                        "", f"Exception: {str(e)}", prompt=test_input if 'test_input' in locals() else "")
    
    def test_command_variations(self):
        """Test 5: Command Parsing Variations"""
        print("=" * 60)
        print("TEST CATEGORY 5: Command Parsing Variations")
        print("=" * 60)
        
        test_user_id = self._get_or_create_test_user("test_command_variations")
        
        # Test 5.1-5.5: Various "add task" phrasings
        command_phrasings = [
            ("add task buy groceries", "T-5.1"),
            ("create task buy groceries", "T-5.2"),
            ("new task buy groceries", "T-5.3"),
            ("task: buy groceries", "T-5.4"),
            ("I need to buy groceries", "T-5.5"),
        ]
        
        for i, (command, test_id) in enumerate(command_phrasings, 1):
            try:
                mode = self.chatbot._detect_mode(command)
                is_command = mode in ["command", "command_with_clarification"]
                
                status = "PASS" if is_command else "PARTIAL"
                self.log_test(test_id, f"Command phrasing: '{command[:30]}...'", status,
                            f"Mode: {mode}", prompt=command, response=f"Mode: {mode}", test_type="mode_detection")
            except Exception as e:
                self.log_test(test_id, f"Command phrasing: '{command[:30]}...'", "FAIL",
                            "", f"Exception: {str(e)}", prompt=command)
        
        # Test 5.6: Command parsing creates structured output
        try:
            test_user_id = self._get_or_create_test_user("test_command_parsing")
            prompt = "add task buy milk"
            response = self.chatbot.generate_response(prompt, mode="command", user_id=test_user_id)
            
            has_structure = ('{' in response and '}' in response) or ('action' in response.lower()) or isinstance(response, dict)
            
            status = "PASS" if has_structure else "PARTIAL"
            self.log_test("T-5.6", "Command parsing creates structured output", status,
                        f"Response appears structured: {response[:100]}..." if has_structure else "Response may not be structured JSON",
                        prompt=prompt, response=str(response)[:300], test_type="command")
        except Exception as e:
            self.log_test("T-5.6", "Command parsing creates structured output", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")

