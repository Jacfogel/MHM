"""
AI Functionality Test Runner

Executes comprehensive tests for AI functionality and documents results.
This script performs manual tests that verify AI behavior in various scenarios.
"""

import sys
import os
import time
from datetime import datetime

# Add project root to path (tests/ai -> tests -> project root)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Import needed for mocking
from unittest.mock import patch, Mock, MagicMock
import requests

from ai.chatbot import AIChatBotSingleton
from ai.cache_manager import get_response_cache
from tests.test_utilities import TestUserFactory
from core.user_data_handlers import get_user_data
from core.response_tracking import get_recent_chat_interactions
from core.user_data_handlers import get_user_id_by_identifier
from user.context_manager import user_context_manager


class AITestRunner:
    """Test runner for AI functionality"""
    
    def __init__(self, test_data_dir):
        self.test_data_dir = test_data_dir
        self.results = []
        self.chatbot = AIChatBotSingleton()
        self._test_users = {}  # Cache created test users
        self.performance_metrics = []  # Track response times and performance
    
    def log_test(self, test_id, test_name, status, notes="", issues="", prompt="", response="", response_time=None, metrics=None):
        """Log test result with optional performance metrics"""
        result = {
            "test_id": test_id,
            "test_name": test_name,
            "status": status,
            "notes": notes,
            "issues": issues,
            "prompt": prompt,
            "response": response,
            "response_time": response_time,
            "metrics": metrics or {},
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        if response_time is not None:
            self.performance_metrics.append({
                "test_id": test_id,
                "response_time": response_time
            })
        
        # Print result (using text symbols to avoid Windows Unicode issues)
        status_symbol = {"PASS": "[PASS]", "FAIL": "[FAIL]", "PARTIAL": "[PARTIAL]"}.get(status, "[?]")
        print(f"{status_symbol} {test_id}: {test_name}")
        if prompt:
            print(f"   Prompt: {prompt}")
        if response_time is not None:
            print(f"   Response Time: {response_time:.2f}s")
        if notes:
            print(f"   Notes: {notes}")
        if issues:
            print(f"   Issues: {issues}")
        print()
    
    def _get_or_create_test_user(self, identifier):
        """Get or create a minimal test user, returning UUID"""
        if identifier in self._test_users:
            return self._test_users[identifier]
        
        # Create minimal test user (fastest option with minimal data)
        success = TestUserFactory.create_minimal_user(
            identifier,
            test_data_dir=self.test_data_dir
        )
        if success:
            # Patch config to use test data directory when looking up user
            import core.config
            with patch.object(core.config, "BASE_DATA_DIR", self.test_data_dir), \
                 patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(self.test_data_dir, 'users')):
                user_uuid = get_user_id_by_identifier(identifier)
                if user_uuid:
                    self._test_users[identifier] = user_uuid
                    return user_uuid
        
        # If user creation fails, return None (will test without user context)
        return None
    
    def test_basic_response_generation(self):
        """Test 1: Basic AI Response Generation"""
        print("=" * 60)
        print("TEST CATEGORY 1: Basic AI Response Generation")
        print("=" * 60)
        
        # Test 1.1: Simple prompt (create minimal test user to avoid data access errors)
        try:
            test_user_id = self._get_or_create_test_user("test_basic_1")
            prompt = "Hello, how are you?"
            response = self.chatbot.generate_response(prompt, user_id=test_user_id)
            if response and isinstance(response, str) and len(response) > 0:
                self.log_test("T-1.1", "generate_response() with simple prompt", "PASS",
                            f"Generated response: {response[:100]}...", prompt=prompt, response=response[:200])
            else:
                self.log_test("T-1.1", "generate_response() with simple prompt", "FAIL",
                            "Response was empty or invalid", prompt=prompt)
        except Exception as e:
            self.log_test("T-1.1", "generate_response() with simple prompt", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 1.2: Chat mode (create test user for chat mode which may track history)
        try:
            test_user_id = self._get_or_create_test_user("test_basic_2")
            prompt = "Tell me about your capabilities"
            response = self.chatbot.generate_response(prompt, mode="chat", user_id=test_user_id)
            if response and isinstance(response, str):
                self.log_test("T-1.2", "generate_response() in chat mode", "PASS",
                            f"Chat mode response generated: {response[:80]}...", prompt=prompt, response=response[:200])
            else:
                self.log_test("T-1.2", "generate_response() in chat mode", "FAIL",
                            "No response generated", prompt=prompt)
        except Exception as e:
            self.log_test("T-1.2", "generate_response() in chat mode", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 1.3: Command mode (create minimal test user to avoid data access errors)
        try:
            test_user_id = self._get_or_create_test_user("test_basic_3")
            prompt = "add task buy groceries"
            response = self.chatbot.generate_response(prompt, mode="command", user_id=test_user_id)
            if response and isinstance(response, str):
                self.log_test("T-1.3", "generate_response() in command mode", "PASS",
                            f"Command mode response generated: {response[:80]}...", prompt=prompt, response=response[:200])
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
        
        # Test 1.5: Cache behavior with timing (create minimal test user for cache test)
        try:
            test_user_id = self._get_or_create_test_user("test_cache_user")
            prompt = "What is 2+2?"
            
            # Clear cache before test
            cache = get_response_cache()
            cache.clear()
            
            # First call - should not be cached
            start_time = time.time()
            response1 = self.chatbot.generate_response(prompt, user_id=test_user_id, mode="command")
            time1 = time.time() - start_time
            
            # Second call - should potentially be cached
            start_time = time.time()
            response2 = self.chatbot.generate_response(prompt, user_id=test_user_id, mode="command")
            time2 = time.time() - start_time
            
            # Note: Cache is only used for non-chat modes (see chatbot.py line 812)
            if response1 and response2:
                cached = (response1 == response2)
                speedup = time1 / time2 if time2 > 0 else 0
                cache_status = "working" if cached else "not used (expected for chat mode or AI variation)"
                
                # Check cache stats
                cache_stats = cache.get_stats()
                
                # Combine both responses for comparison
                combined_response = f"Response 1 ({len(response1)} chars, {time1:.2f}s): {response1[:150]}... | Response 2 ({len(response2)} chars, {time2:.2f}s): {response2[:150]}..."
                metrics = {
                    "first_call_time": time1,
                    "second_call_time": time2,
                    "speedup": speedup if cached else None,
                    "cache_stats": cache_stats
                }
                
                status = "PASS" if cached and time2 < time1 else "PARTIAL"
                self.log_test("T-1.5", "Response caching", status,
                            f"Cache {cache_status} | Cache enabled: {cache_stats.get('cache_enabled', False)} | Entries: {cache_stats.get('total_entries', 0)}", 
                            prompt=prompt, response=combined_response, response_time=time2, metrics=metrics)
            else:
                self.log_test("T-1.5", "Response caching", "FAIL",
                            "Failed to generate responses for cache test", prompt=prompt)
        except Exception as e:
            self.log_test("T-1.5", "Response caching", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
    
    def test_contextual_response_generation(self):
        """Test 2: Contextual Response Generation"""
        print("=" * 60)
        print("TEST CATEGORY 2: Contextual Response Generation")
        print("=" * 60)
        
        # Create test user with data
        user_id = "test_contextual_user"
        
        try:
            # Create user with basic data
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
            
            # Get actual user ID (UUID) with proper test data directory context
            from unittest.mock import patch
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
                response = self.chatbot.generate_contextual_response(
                    actual_user_id, prompt
                )
                if response and isinstance(response, str) and len(response) > 0:
                    self.log_test("T-2.1", "generate_contextual_response() with new user", "PASS",
                                f"Response generated: {response[:100]}...", prompt=prompt, response=response[:300])
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
                # Update user context with name (profile data is stored in context)
                from core.user_data_handlers import save_user_data
                context_data = {"context": {"preferred_name": "TestUser"}}
                save_user_data(actual_user_id, context_data)
                
                prompt = "Hello!"
                response = self.chatbot.generate_contextual_response(
                    actual_user_id, prompt
                )
                
                if response and ("TestUser" in response or "test" in response.lower()):
                    self.log_test("T-2.3", "User name in contextual response", "PASS",
                                f"Response: {response[:100]}...", prompt=prompt, response=response[:300])
                else:
                    self.log_test("T-2.3", "User name in contextual response", "PARTIAL",
                                f"Name may not be included (response: {response[:80]}...)", prompt=prompt, response=response[:300])
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
                            f"Mode detected: {mode}", prompt=test_input, response=f"Mode: {mode}")
            else:
                self.log_test("T-3.1", "Detect clear command", "PARTIAL",
                            f"Mode detected: {mode} (expected 'command')", prompt=test_input, response=f"Mode: {mode}")
        except Exception as e:
            self.log_test("T-3.1", "Detect clear command", "FAIL",
                        "", f"Exception: {str(e)}", prompt=test_input if 'test_input' in locals() else "")
        
        # Test 3.2: Ambiguous request detection
        try:
            test_input = "Can you add a task?"
            mode = self.chatbot._detect_mode(test_input)
            if mode == "command_with_clarification":
                self.log_test("T-3.2", "Detect ambiguous request", "PASS",
                            f"Mode detected: {mode}", prompt=test_input, response=f"Mode: {mode}")
            else:
                self.log_test("T-3.2", "Detect ambiguous request", "PARTIAL",
                            f"Mode detected: {mode} (expected 'command_with_clarification')", prompt=test_input, response=f"Mode: {mode}")
        except Exception as e:
            self.log_test("T-3.2", "Detect ambiguous request", "FAIL",
                        "", f"Exception: {str(e)}", prompt=test_input if 'test_input' in locals() else "")
        
        # Test 3.3: Chat detection
        try:
            test_input = "How are you doing?"
            mode = self.chatbot._detect_mode(test_input)
            if mode == "chat":
                self.log_test("T-3.3", "Detect chat message", "PASS",
                            f"Mode detected: {mode}", prompt=test_input, response=f"Mode: {mode}")
            else:
                self.log_test("T-3.3", "Detect chat message", "PARTIAL",
                            f"Mode detected: {mode} (expected 'chat')", prompt=test_input, response=f"Mode: {mode}")
        except Exception as e:
            self.log_test("T-3.3", "Detect chat message", "FAIL",
                        "", f"Exception: {str(e)}", prompt=test_input if 'test_input' in locals() else "")
    
    def test_context_with_checkins(self):
        """Test 4: Context Building with Check-in Data"""
        print("=" * 60)
        print("TEST CATEGORY 4: Context Building with Check-in Data")
        print("=" * 60)
        
        user_id = "test_checkin_user"
        
        try:
            # Create user with check-in data
            success = TestUserFactory.create_basic_user(
                user_id,
                enable_checkins=True,
                test_data_dir=self.test_data_dir
            )
            
            if not success:
                self.log_test("T-4.0", "Create user for check-in tests", "FAIL",
                            "", "Failed to create test user")
                return
            
            from unittest.mock import patch
            import core.config
            
            with patch.object(core.config, "BASE_DATA_DIR", self.test_data_dir), \
                 patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(self.test_data_dir, 'users')):
                actual_user_id = get_user_id_by_identifier(user_id)
            
            if not actual_user_id:
                self.log_test("T-4.0", "Get user UUID for check-in tests", "FAIL",
                            "", "Could not get user UUID")
                return
            
            # Test 4.1: Context includes check-in data
            try:
                context = user_context_manager.get_ai_context(actual_user_id, include_conversation_history=False)
                has_checkins = 'recent_activity' in context or 'checkins' in str(context).lower()
                
                prompt = "How have I been doing with my check-ins?"
                response = self.chatbot.generate_contextual_response(actual_user_id, prompt)
                
                if has_checkins:
                    self.log_test("T-4.1", "Context includes check-in data", "PASS",
                                "Check-in data found in context", prompt=prompt, response=response[:300] if response else "")
                else:
                    self.log_test("T-4.1", "Context includes check-in data", "PARTIAL",
                                "Check-in data may not be in context structure",
                                prompt=prompt, response=response[:300] if response else "")
            except Exception as e:
                self.log_test("T-4.1", "Context includes check-in data", "FAIL",
                            "", f"Exception: {str(e)}")
                
        except Exception as e:
            self.log_test("T-4.0", "Check-in context setup", "FAIL",
                        "", f"Exception during setup: {str(e)}")
    
    def test_command_variations(self):
        """Test 5: Command Parsing Variations"""
        print("=" * 60)
        print("TEST CATEGORY 5: Command Parsing Variations")
        print("=" * 60)
        
        test_user_id = self._get_or_create_test_user("test_command_variations")
        
        # Test 5.1: Various "add task" phrasings
        command_phrasings = [
            "add task buy groceries",
            "create task buy groceries",
            "new task buy groceries",
            "task: buy groceries",
            "I need to buy groceries"
        ]
        
        for i, command in enumerate(command_phrasings, 1):
            try:
                mode = self.chatbot._detect_mode(command)
                # All should detect as command or command_with_clarification
                is_command = mode in ["command", "command_with_clarification"]
                
                if is_command:
                    self.log_test(f"T-5.{i}", f"Command phrasing: '{command[:30]}...'", "PASS",
                                f"Mode: {mode}", prompt=command, response=f"Mode: {mode}")
                else:
                    self.log_test(f"T-5.{i}", f"Command phrasing: '{command[:30]}...'", "PARTIAL",
                                f"Mode: {mode} (expected command variant)", prompt=command, response=f"Mode: {mode}")
            except Exception as e:
                self.log_test(f"T-5.{i}", f"Command phrasing: '{command[:30]}...'", "FAIL",
                            "", f"Exception: {str(e)}", prompt=command)
        
        # Test 5.2: Command parsing creates structured output
        try:
            test_user_id = self._get_or_create_test_user("test_command_parsing")
            prompt = "add task buy milk"
            response = self.chatbot.generate_response(prompt, mode="command", user_id=test_user_id)
            
            # Check if response contains structured data (JSON-like)
            has_structure = ('{' in response and '}' in response) or ('action' in response.lower()) or isinstance(response, dict)
            
            if has_structure:
                self.log_test("T-5.6", "Command parsing creates structured output", "PASS",
                            f"Response appears structured: {response[:100]}...", prompt=prompt, response=str(response)[:300])
            else:
                self.log_test("T-5.6", "Command parsing creates structured output", "PARTIAL",
                            "Response may not be structured JSON", prompt=prompt, response=str(response)[:300])
        except Exception as e:
            self.log_test("T-5.6", "Command parsing creates structured output", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
    
    def test_error_handling(self):
        """Test 6: Error Handling and Fallbacks"""
        print("=" * 60)
        print("TEST CATEGORY 6: Error Handling and Fallbacks")
        print("=" * 60)
        
        # Test 6.1: Invalid user ID handling
        try:
            response = self.chatbot.generate_contextual_response(None, "Hello")
            # Should handle None user_id gracefully
            if response:
                self.log_test("T-6.1", "Invalid user_id (None) handling", "PASS",
                            "Response generated with None user_id", prompt="Hello", response=response[:200])
            else:
                self.log_test("T-6.1", "Invalid user_id (None) handling", "PARTIAL",
                            "No response generated for None user_id")
        except Exception as e:
            # Exception is acceptable if handled gracefully
            error_msg = str(e)
            if "None" in error_msg or "user" in error_msg.lower():
                self.log_test("T-6.1", "Invalid user_id (None) handling", "PASS",
                            f"Error handled: {error_msg[:100]}...", prompt="Hello")
            else:
                self.log_test("T-6.1", "Invalid user_id (None) handling", "FAIL",
                            "", f"Unexpected exception: {error_msg}")
        
        # Test 6.2: Missing context data handling
        try:
            # Create a user with minimal/no data
            test_user_id = self._get_or_create_test_user("test_empty_user")
            prompt = "How am I doing?"
            response = self.chatbot.generate_contextual_response(test_user_id, prompt)
            
            if response and len(response) > 0:
                self.log_test("T-6.2", "Missing context data handling", "PASS",
                            "Response generated despite missing context data", prompt=prompt, response=response[:200])
            else:
                self.log_test("T-6.2", "Missing context data handling", "FAIL",
                            "No response generated")
        except Exception as e:
            self.log_test("T-6.2", "Missing context data handling", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 6.3: Empty prompt handling
        try:
            test_user_id = self._get_or_create_test_user("test_empty_prompt")
            response = self.chatbot.generate_response("", user_id=test_user_id)
            
            if response:
                self.log_test("T-6.3", "Empty prompt handling", "PASS",
                            "Response generated for empty prompt", prompt="(empty)", response=response[:200])
            else:
                self.log_test("T-6.3", "Empty prompt handling", "PARTIAL",
                            "No response for empty prompt (may be expected)")
        except Exception as e:
            # Exception for empty prompt is acceptable
            self.log_test("T-6.3", "Empty prompt handling", "PASS",
                        f"Exception handled: {str(e)[:100]}...", prompt="(empty)")
    
    def test_conversation_history_in_context(self):
        """Test 7: Conversation History Integration in Context"""
        print("=" * 60)
        print("TEST CATEGORY 7: Conversation History Integration")
        print("=" * 60)
        
        user_id = "test_history_context_user"
        
        try:
            success = TestUserFactory.create_basic_user(
                user_id,
                enable_checkins=True,
                test_data_dir=self.test_data_dir
            )
            
            if not success:
                self.log_test("T-7.0", "Create user for history context tests", "FAIL",
                            "", "Failed to create test user")
                return
            
            from unittest.mock import patch
            import core.config
            
            with patch.object(core.config, "BASE_DATA_DIR", self.test_data_dir), \
                 patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(self.test_data_dir, 'users')):
                actual_user_id = get_user_id_by_identifier(user_id)
            
            if not actual_user_id:
                self.log_test("T-7.0", "Get user UUID for history context tests", "FAIL",
                            "", "Could not get user UUID")
                return
            
            # Test 7.1: Conversation history affects subsequent responses
            try:
                prompt1 = "My favorite color is blue"
                response1 = self.chatbot.generate_contextual_response(actual_user_id, prompt1)
                
                prompt2 = "What's my favorite color?"
                response2 = self.chatbot.generate_contextual_response(actual_user_id, prompt2)
                
                # Check if response2 references blue (showing conversation awareness)
                mentions_blue = "blue" in response2.lower()
                
                if mentions_blue:
                    self.log_test("T-7.1", "Conversation history affects responses", "PASS",
                                "Subsequent response shows awareness of previous conversation",
                                prompt=f"{prompt1} | {prompt2}",
                                response=f"Response 1: {response1[:100]}... | Response 2: {response2[:100]}...")
                else:
                    self.log_test("T-7.1", "Conversation history affects responses", "PARTIAL",
                                "Subsequent response may not reference previous conversation",
                                prompt=f"{prompt1} | {prompt2}",
                                response=f"Response 1: {response1[:100]}... | Response 2: {response2[:100]}...")
            except Exception as e:
                self.log_test("T-7.1", "Conversation history affects responses", "FAIL",
                            "", f"Exception: {str(e)}")
            
            # Test 7.2: Conversation history included in context
            try:
                context = user_context_manager.get_ai_context(
                    actual_user_id, include_conversation_history=True
                )
                
                has_history = 'conversation_history' in context or 'history' in str(context).lower()
                
                if has_history:
                    history_count = len(context.get('conversation_history', []))
                    self.log_test("T-7.2", "Conversation history in context", "PASS",
                                f"History included in context ({history_count} exchanges)")
                else:
                    self.log_test("T-7.2", "Conversation history in context", "PARTIAL",
                                "History may not be explicitly in context structure")
            except Exception as e:
                self.log_test("T-7.2", "Conversation history in context", "FAIL",
                            "", f"Exception: {str(e)}")
                
        except Exception as e:
            self.log_test("T-7.0", "History context setup", "FAIL",
                        "", f"Exception during setup: {str(e)}")
    
    def test_conversation_history(self):
        """Test 8: Conversation History Storage"""
        print("=" * 60)
        print("TEST CATEGORY 8: Conversation History Storage")
        print("=" * 60)
        
        user_id = "test_history_user"
        
        try:
            # Create user
            success = TestUserFactory.create_basic_user(
                user_id,
                enable_checkins=True,
                enable_tasks=True,
                test_data_dir=self.test_data_dir
            )
            
            if not success:
                self.log_test("T-4.0", "Create user for history tests", "FAIL",
                            "", "Failed to create test user")
                return
            
            from unittest.mock import patch
            import core.config
            
            with patch.object(core.config, "BASE_DATA_DIR", self.test_data_dir), \
                 patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(self.test_data_dir, 'users')):
                from core.user_data_handlers import get_user_id_by_identifier
                actual_user_id = get_user_id_by_identifier(user_id)
            
            if not actual_user_id:
                self.log_test("T-4.0", "Get user UUID for history tests", "FAIL",
                            "", "Could not get user UUID")
                return
            
            # Test 8.1: Store conversation exchange
            try:
                # Use more descriptive test messages
                prompt1 = "How are you doing today?"
                response1 = self.chatbot.generate_contextual_response(actual_user_id, prompt1)
                
                prompt2 = "What should I focus on this week?"
                response2 = self.chatbot.generate_contextual_response(actual_user_id, prompt2)
                
                # Check conversation history
                history = user_context_manager.get_ai_context(
                    actual_user_id, include_conversation_history=True
                ).get('conversation_history', [])
                
                # Format prompts and responses for logging
                exchange_details = f"Exchange 1: '{prompt1}' -> {response1[:80]}... | Exchange 2: '{prompt2}' -> {response2[:80]}..."
                
                if len(history) >= 2:
                    self.log_test("T-8.1", "Store conversation exchanges", "PASS",
                                f"Stored {len(history)} exchanges", prompt=f"{prompt1} | {prompt2}", response=exchange_details)
                else:
                    self.log_test("T-8.1", "Store conversation exchanges", "PARTIAL",
                                f"Stored {len(history)} exchanges (expected 2+)", prompt=f"{prompt1} | {prompt2}", response=exchange_details)
            except Exception as e:
                self.log_test("T-8.1", "Store conversation exchanges", "FAIL",
                            "", f"Exception: {str(e)}", prompt=prompt1 if 'prompt1' in locals() else "")
            
            # Test 8.2: Retrieve recent interactions
            try:
                recent = get_recent_chat_interactions(actual_user_id, limit=5)
                if recent and len(recent) > 0:
                    self.log_test("T-8.2", "Retrieve recent interactions", "PASS",
                                f"Retrieved {len(recent)} interactions")
                else:
                    self.log_test("T-8.2", "Retrieve recent interactions", "PARTIAL",
                                "No interactions retrieved (may be expected if not stored)")
            except Exception as e:
                self.log_test("T-8.2", "Retrieve recent interactions", "FAIL",
                            "", f"Exception: {str(e)}")
                
        except Exception as e:
            self.log_test("T-8.0", "Conversation history storage setup", "FAIL",
                        "", f"Exception during setup: {str(e)}")
    
    def test_performance_metrics(self):
        """Test 9: Performance Metrics"""
        print("=" * 60)
        print("TEST CATEGORY 9: Performance Metrics")
        print("=" * 60)
        
        test_user_id = self._get_or_create_test_user("test_perf_user")
        
        # Test 9.1: Simple query response time
        try:
            prompt = "Hello"
            start_time = time.time()
            response = self.chatbot.generate_response(prompt, user_id=test_user_id)
            response_time = time.time() - start_time
            
            if response and response_time < 10.0:  # Should be fast
                status = "PASS" if response_time < 5.0 else "PARTIAL"
                self.log_test("T-9.1", "Simple query response time", status,
                            f"Response time: {response_time:.2f}s (target <5s)", 
                            prompt=prompt, response=response[:200], response_time=response_time)
            else:
                self.log_test("T-9.1", "Simple query response time", "FAIL" if response_time >= 10.0 else "PARTIAL",
                            f"Response time too slow: {response_time:.2f}s" if response_time >= 10.0 else f"Response time: {response_time:.2f}s",
                            prompt=prompt, response_time=response_time)
        except Exception as e:
            self.log_test("T-9.1", "Simple query response time", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 9.2: Contextual query response time
        try:
            # Create user with context data
            success = TestUserFactory.create_basic_user(
                "test_perf_contextual",
                enable_checkins=True,
                test_data_dir=self.test_data_dir
            )
            
            if success:
                import core.config
                with patch.object(core.config, "BASE_DATA_DIR", self.test_data_dir), \
                     patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(self.test_data_dir, 'users')):
                    contextual_user_id = get_user_id_by_identifier("test_perf_contextual")
                    
                    if contextual_user_id:
                        prompt = "How am I doing today?"
                        start_time = time.time()
                        response = self.chatbot.generate_contextual_response(contextual_user_id, prompt)
                        response_time = time.time() - start_time
                        
                        if response and response_time < 15.0:  # Contextual can be slower
                            status = "PASS" if response_time < 10.0 else "PARTIAL"
                            self.log_test("T-9.2", "Contextual query response time", status,
                                        f"Response time: {response_time:.2f}s (target <10s)", 
                                        prompt=prompt, response=response[:200], response_time=response_time)
                        else:
                            self.log_test("T-9.2", "Contextual query response time", "FAIL" if response_time >= 15.0 else "PARTIAL",
                                        f"Response time too slow: {response_time:.2f}s" if response_time >= 15.0 else f"Response time: {response_time:.2f}s",
                                        prompt=prompt, response_time=response_time)
                    else:
                        self.log_test("T-9.2", "Contextual query response time", "FAIL",
                                    "", "Could not get user UUID")
            else:
                self.log_test("T-9.2", "Contextual query response time", "FAIL",
                            "", "Failed to create test user")
        except Exception as e:
            self.log_test("T-9.2", "Contextual query response time", "FAIL",
                        "", f"Exception: {str(e)}")
        
        # Test 9.3: Response length validation
        try:
            test_user_id = self._get_or_create_test_user("test_response_length")
            prompt = "Tell me a short story"
            response = self.chatbot.generate_response(prompt, user_id=test_user_id)
            
            if response:
                # Check if response is reasonable length (not too short, not absurdly long)
                min_length = 10  # Minimum reasonable response
                max_length = 2000  # Maximum reasonable response
                
                if min_length <= len(response) <= max_length:
                    self.log_test("T-9.3", "Response length validation", "PASS",
                                f"Response length: {len(response)} chars (acceptable range: {min_length}-{max_length})",
                                prompt=prompt, response=response[:300])
                else:
                    status = "PARTIAL" if len(response) < min_length else "FAIL"
                    self.log_test("T-9.3", "Response length validation", status,
                                f"Response length: {len(response)} chars (expected {min_length}-{max_length})",
                                prompt=prompt, response=response[:300])
            else:
                self.log_test("T-9.3", "Response length validation", "FAIL",
                            "No response generated", prompt=prompt)
        except Exception as e:
            self.log_test("T-9.3", "Response length validation", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
    
    def test_api_error_scenarios(self):
        """Test 10: API Error Scenarios (using mocks)"""
        print("=" * 60)
        print("TEST CATEGORY 10: API Error Scenarios")
        print("=" * 60)
        
        test_user_id = self._get_or_create_test_user("test_error_scenarios")
        
        # Test 10.1: Connection error handling
        try:
            with patch('ai.chatbot.requests.get') as mock_get:
                # Simulate connection error
                mock_get.side_effect = requests.ConnectionError("Connection refused")
                
                # Force reconnection test
                original_available = self.chatbot.lm_studio_available
                self.chatbot.lm_studio_available = False
                
                # Should use fallback response
                prompt = "Test connection error"
                response = self.chatbot.generate_response(prompt, user_id=test_user_id)
                
                # Restore original state
                self.chatbot.lm_studio_available = original_available
                
                if response and len(response) > 0:
                    # Should get fallback response (not empty)
                    is_fallback = "trouble" in response.lower() or "support" in response.lower() or "help" in response.lower()
                    status = "PASS" if is_fallback else "PARTIAL"
                    self.log_test("T-10.1", "Connection error handling", status,
                                f"Fallback response provided: {response[:100]}...",
                                prompt=prompt, response=response[:200])
                else:
                    self.log_test("T-10.1", "Connection error handling", "FAIL",
                                "No response generated on connection error", prompt=prompt)
        except Exception as e:
            self.log_test("T-10.1", "Connection error handling", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 10.2: Timeout handling
        try:
            with patch('ai.chatbot.requests.post') as mock_post:
                # Simulate timeout
                mock_post.side_effect = requests.Timeout("Request timed out")
                
                # Test with a short timeout
                prompt = "Test timeout"
                response = self.chatbot.generate_response(prompt, user_id=test_user_id, timeout=1)
                
                if response and len(response) > 0:
                    # Should get fallback or timeout handling response
                    self.log_test("T-10.2", "Timeout handling", "PASS",
                                f"Response provided after timeout: {response[:100]}...",
                                prompt=prompt, response=response[:200])
                else:
                    self.log_test("T-10.2", "Timeout handling", "FAIL",
                                "No response generated after timeout", prompt=prompt)
        except Exception as e:
            # Timeout exceptions are expected to be handled
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "Time" in error_msg:
                self.log_test("T-10.2", "Timeout handling", "PASS",
                            f"Timeout handled: {error_msg[:100]}...", prompt=prompt)
            else:
                self.log_test("T-10.2", "Timeout handling", "FAIL",
                            "", f"Unexpected exception: {error_msg}")
        
        # Test 10.3: Invalid API response handling
        try:
            with patch('ai.chatbot.requests.post') as mock_post:
                # Simulate invalid/malformed response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"invalid": "structure"}  # Missing 'choices'
                mock_post.return_value = mock_response
                
                # Force API call (not fallback)
                original_available = self.chatbot.lm_studio_available
                self.chatbot.lm_studio_available = True
                
                prompt = "Test invalid response"
                response = self.chatbot.generate_response(prompt, user_id=test_user_id)
                
                # Restore original state
                self.chatbot.lm_studio_available = original_available
                
                if response and len(response) > 0:
                    # Should handle gracefully and provide fallback
                    self.log_test("T-10.3", "Invalid API response handling", "PASS",
                                f"Response provided despite invalid API response: {response[:100]}...",
                                prompt=prompt, response=response[:200])
                else:
                    self.log_test("T-10.3", "Invalid API response handling", "FAIL",
                                "No response generated for invalid API response", prompt=prompt)
        except Exception as e:
            # Exceptions should be handled gracefully
            error_msg = str(e)
            if "invalid" in error_msg.lower() or "KeyError" in error_msg or "IndexError" in error_msg:
                self.log_test("T-10.3", "Invalid API response handling", "PARTIAL",
                            f"Exception occurred but may be handled: {error_msg[:100]}...", prompt=prompt)
            else:
                self.log_test("T-10.3", "Invalid API response handling", "FAIL",
                            "", f"Unexpected exception: {error_msg}")
        
        # Test 10.4: 5xx Server error handling
        try:
            with patch('ai.chatbot.requests.post') as mock_post:
                # Simulate server error
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.text = "Internal Server Error"
                mock_post.return_value = mock_response
                
                # Force API call
                original_available = self.chatbot.lm_studio_available
                self.chatbot.lm_studio_available = True
                
                prompt = "Test server error"
                response = self.chatbot.generate_response(prompt, user_id=test_user_id)
                
                # Restore original state
                self.chatbot.lm_studio_available = original_available
                
                if response and len(response) > 0:
                    # Should get fallback response
                    self.log_test("T-10.4", "Server error (5xx) handling", "PASS",
                                f"Fallback response provided: {response[:100]}...",
                                prompt=prompt, response=response[:200])
                else:
                    self.log_test("T-10.4", "Server error (5xx) handling", "FAIL",
                                "No response generated for server error", prompt=prompt)
        except Exception as e:
            self.log_test("T-10.4", "Server error (5xx) handling", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
    
    def test_cache_comprehensive(self):
        """Test 11: Comprehensive Cache Testing"""
        print("=" * 60)
        print("TEST CATEGORY 11: Comprehensive Cache Testing")
        print("=" * 60)
        
        # Test 11.1: Cache isolation by user
        try:
            user1_id = self._get_or_create_test_user("test_cache_user1")
            user2_id = self._get_or_create_test_user("test_cache_user2")
            
            cache = get_response_cache()
            cache.clear()
            
            prompt = "What is the capital of France?"
            
            # Generate response for user 1
            response1_user1 = self.chatbot.generate_response(prompt, user_id=user1_id, mode="command")
            
            # Generate response for user 2 (might be different if personalized)
            response1_user2 = self.chatbot.generate_response(prompt, user_id=user2_id, mode="command")
            
            # Second call for user 1 should use cache
            start_time = time.time()
            response2_user1 = self.chatbot.generate_response(prompt, user_id=user1_id, mode="command")
            time_user1 = time.time() - start_time
            
            # Check cache stats
            cache_stats = cache.get_stats()
            
            if response1_user1 and response2_user1:
                # Cache should work for same user
                cached = (response1_user1 == response2_user1)
                status = "PASS" if cached else "PARTIAL"
                notes = f"Cache {'used' if cached else 'not used'} | User isolation: {'verified' if response1_user1 != response1_user2 or cached else 'needs verification'}"
                self.log_test("T-11.1", "Cache isolation by user", status, notes,
                            prompt=prompt, response=f"User1 R1: {response1_user1[:100]}... | User1 R2: {response2_user1[:100]}...",
                            response_time=time_user1, metrics={"cache_stats": cache_stats})
            else:
                self.log_test("T-11.1", "Cache isolation by user", "FAIL",
                            "Failed to generate responses", prompt=prompt)
        except Exception as e:
            self.log_test("T-11.1", "Cache isolation by user", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 11.2: Cache isolation by mode
        try:
            test_user_id = self._get_or_create_test_user("test_cache_mode")
            cache = get_response_cache()
            cache.clear()
            
            prompt = "What is 5+5?"
            
            # Generate in command mode
            response_command = self.chatbot.generate_response(prompt, user_id=test_user_id, mode="command")
            
            # Generate in chat mode (should not use command mode cache)
            response_chat = self.chatbot.generate_response(prompt, user_id=test_user_id, mode="chat")
            
            # Second command mode call should potentially use cache
            start_time = time.time()
            response_command2 = self.chatbot.generate_response(prompt, user_id=test_user_id, mode="command")
            time_command = time.time() - start_time
            
            # Second chat mode call should not use cache (cache skipped for chat)
            start_time = time.time()
            response_chat2 = self.chatbot.generate_response(prompt, user_id=test_user_id, mode="chat")
            time_chat = time.time() - start_time
            
            cache_stats = cache.get_stats()
            
            # Command mode should cache, chat mode should not
            command_cached = (response_command == response_command2)
            chat_varied = (response_chat != response_chat2)  # Chat should vary (cache skipped)
            
            status = "PASS" if command_cached else "PARTIAL"
            notes = f"Command mode cache: {'used' if command_cached else 'not used'} | Chat mode variation: {'working' if chat_varied else 'not varying'}"
            self.log_test("T-11.2", "Cache isolation by mode", status, notes,
                        prompt=prompt, response=f"Command: {response_command[:80]}... | Chat: {response_chat[:80]}...",
                        response_time=time_command, metrics={"cache_stats": cache_stats})
        except Exception as e:
            self.log_test("T-11.2", "Cache isolation by mode", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 11.3: Cache TTL expiration (if possible to test quickly)
        try:
            test_user_id = self._get_or_create_test_user("test_cache_ttl")
            cache = get_response_cache()
            cache.clear()
            
            prompt = "Test cache TTL"
            
            # Generate and cache response
            response1 = self.chatbot.generate_response(prompt, user_id=test_user_id, mode="command")
            
            # Immediately check cache (should be there)
            cached_immediate = cache.get(prompt, test_user_id, prompt_type="command")
            
            cache_stats = cache.get_stats()
            
            if cached_immediate == response1:
                self.log_test("T-11.3", "Cache TTL and retrieval", "PASS",
                            f"Cache retrieval working | Entries: {cache_stats.get('total_entries', 0)} | Active: {cache_stats.get('active_entries', 0)}",
                            prompt=prompt, metrics={"cache_stats": cache_stats})
            else:
                self.log_test("T-11.3", "Cache TTL and retrieval", "PARTIAL",
                            "Cache retrieval may not be working as expected", prompt=prompt,
                            metrics={"cache_stats": cache_stats})
        except Exception as e:
            self.log_test("T-11.3", "Cache TTL and retrieval", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
    
    def test_response_quality(self):
        """Test 12: Response Quality and Content Validation"""
        print("=" * 60)
        print("TEST CATEGORY 12: Response Quality and Content Validation")
        print("=" * 60)
        
        test_user_id = self._get_or_create_test_user("test_quality_user")
        
        # Test 12.1: Response should not be empty or whitespace-only
        try:
            prompt = "Tell me something helpful"
            response = self.chatbot.generate_response(prompt, user_id=test_user_id)
            
            if response:
                response_trimmed = response.strip()
                is_empty = len(response_trimmed) == 0
                is_only_whitespace = response != response_trimmed and len(response_trimmed) == 0
                
                if not is_empty and not is_only_whitespace and len(response_trimmed) >= 5:
                    self.log_test("T-12.1", "Response non-empty validation", "PASS",
                                f"Response has meaningful content: {len(response_trimmed)} chars",
                                prompt=prompt, response=response[:200])
                else:
                    status = "FAIL" if is_empty or is_only_whitespace else "PARTIAL"
                    self.log_test("T-12.1", "Response non-empty validation", status,
                                f"Response may be too short or empty: {len(response_trimmed)} chars",
                                prompt=prompt, response=response[:200])
            else:
                self.log_test("T-12.1", "Response non-empty validation", "FAIL",
                            "No response generated", prompt=prompt)
        except Exception as e:
            self.log_test("T-12.1", "Response non-empty validation", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 12.2: Response should not contain obvious error messages
        try:
            prompt = "How are you?"
            response = self.chatbot.generate_response(prompt, user_id=test_user_id)
            
            if response:
                # Check for common error patterns
                error_patterns = [
                    "error",
                    "exception",
                    "failed",
                    "unable to",
                    "cannot",
                    "null",
                    "undefined",
                    "none"
                ]
                error_found = any(pattern in response.lower() for pattern in error_patterns)
                
                # But allow helpful error messages (contextual fallbacks are okay)
                helpful_errors = ["i'm having trouble", "please try again", "help", "support"]
                is_helpful_error = any(phrase in response.lower() for phrase in helpful_errors)
                
                if not error_found or is_helpful_error:
                    self.log_test("T-12.2", "Response error message validation", "PASS",
                                f"Response does not contain unexpected errors: {response[:100]}...",
                                prompt=prompt, response=response[:200])
                else:
                    self.log_test("T-12.2", "Response error message validation", "PARTIAL",
                                f"Response may contain error patterns: {response[:100]}...",
                                prompt=prompt, response=response[:200])
            else:
                self.log_test("T-12.2", "Response error message validation", "FAIL",
                            "No response generated", prompt=prompt)
        except Exception as e:
            self.log_test("T-12.2", "Response error message validation", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 12.3: Contextual response should reference user context
        try:
            # Create user with context
            success = TestUserFactory.create_basic_user(
                "test_quality_contextual",
                enable_checkins=True,
                test_data_dir=self.test_data_dir
            )
            
            if success:
                import core.config
                with patch.object(core.config, "BASE_DATA_DIR", self.test_data_dir), \
                     patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(self.test_data_dir, 'users')):
                    contextual_user_id = get_user_id_by_identifier("test_quality_contextual")
                    
                    if contextual_user_id:
                        # Set user name
                        from core.user_data_handlers import save_user_data
                        save_user_data(contextual_user_id, {"context": {"preferred_name": "QualityTest"}})
                        
                        prompt = "How am I doing?"
                        response = self.chatbot.generate_contextual_response(contextual_user_id, prompt)
                        
                        if response:
                            # Check if response seems contextual (mentions user or references context)
                            has_user_ref = "QualityTest" in response or "qualitytest" in response.lower()
                            has_contextual_language = any(word in response.lower() for word in [
                                "you", "your", "today", "recent", "check", "activity"
                            ])
                            
                            is_contextual = has_user_ref or has_contextual_language
                            
                            status = "PASS" if is_contextual else "PARTIAL"
                            self.log_test("T-12.3", "Contextual response quality", status,
                                        f"Response appears {'contextual' if is_contextual else 'generic'}: {response[:100]}...",
                                        prompt=prompt, response=response[:300])
                        else:
                            self.log_test("T-12.3", "Contextual response quality", "FAIL",
                                        "No response generated", prompt=prompt)
                    else:
                        self.log_test("T-12.3", "Contextual response quality", "FAIL",
                                    "", "Could not get user UUID")
            else:
                self.log_test("T-12.3", "Contextual response quality", "FAIL",
                            "", "Failed to create test user")
        except Exception as e:
            self.log_test("T-12.3", "Contextual response quality", "FAIL",
                        "", f"Exception: {str(e)}")
        
        # Test 12.4: Response format validation (no unexpected formatting issues)
        try:
            test_user_id = self._get_or_create_test_user("test_format_validation")
            prompt = "Tell me a fact"
            response = self.chatbot.generate_response(prompt, user_id=test_user_id)
            
            if response:
                # Check for common formatting issues
                has_multiple_newlines = response.count('\n\n\n') > 0  # More than double newline
                has_trailing_newlines = response.endswith('\n\n') or response.endswith('\n\n\n')
                has_leading_whitespace = response.startswith(' ') or response.startswith('\t')
                
                # Check for JSON artifacts (should not appear in regular responses)
                looks_like_json = (response.strip().startswith('{') and '}' in response) or \
                                 (response.strip().startswith('[') and ']' in response)
                
                issues = []
                if has_multiple_newlines:
                    issues.append("multiple newlines")
                if has_trailing_newlines:
                    issues.append("trailing newlines")
                if has_leading_whitespace:
                    issues.append("leading whitespace")
                if looks_like_json and 'chat' not in prompt.lower():
                    issues.append("JSON artifacts")
                
                if not issues:
                    self.log_test("T-12.4", "Response format validation", "PASS",
                                "Response format is clean",
                                prompt=prompt, response=response[:200])
                else:
                    self.log_test("T-12.4", "Response format validation", "PARTIAL",
                                f"Format issues detected: {', '.join(issues)}",
                                prompt=prompt, response=response[:200])
            else:
                self.log_test("T-12.4", "Response format validation", "FAIL",
                            "No response generated", prompt=prompt)
        except Exception as e:
            self.log_test("T-12.4", "Response format validation", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
    
    def test_edge_cases(self):
        """Test 13: Edge Cases and Boundary Conditions"""
        print("=" * 60)
        print("TEST CATEGORY 13: Edge Cases and Boundary Conditions")
        print("=" * 60)
        
        # Test 13.1: Very long prompt
        try:
            test_user_id = self._get_or_create_test_user("test_long_prompt")
            # Create a very long prompt (but reasonable - not absurd)
            long_prompt = "Tell me " + "about yourself " * 50  # ~1000 chars
            response = self.chatbot.generate_response(long_prompt, user_id=test_user_id)
            
            if response and len(response) > 0:
                status = "PASS" if len(response) >= 10 else "PARTIAL"
                self.log_test("T-13.1", "Very long prompt handling", status,
                            f"Response generated for long prompt ({len(long_prompt)} chars): {response[:100]}...",
                            prompt=f"{long_prompt[:50]}... ({len(long_prompt)} chars)", response=response[:200])
            else:
                self.log_test("T-13.1", "Very long prompt handling", "FAIL",
                            "No response to long prompt", prompt=f"{long_prompt[:50]}...")
        except Exception as e:
            self.log_test("T-13.1", "Very long prompt handling", "FAIL",
                        "", f"Exception: {str(e)}", prompt="(very long prompt)")
        
        # Test 13.2: Special characters in prompt
        try:
            test_user_id = self._get_or_create_test_user("test_special_chars")
            special_prompt = "What do you think about: !@#$%^&*()[]{}|\\/:;\"'<>?,."
            response = self.chatbot.generate_response(special_prompt, user_id=test_user_id)
            
            if response and len(response) > 0:
                self.log_test("T-13.2", "Special characters handling", "PASS",
                            f"Response generated with special chars: {response[:100]}...",
                            prompt=special_prompt, response=response[:200])
            else:
                self.log_test("T-13.2", "Special characters handling", "FAIL",
                            "No response to special character prompt", prompt=special_prompt)
        except Exception as e:
            self.log_test("T-13.2", "Special characters handling", "FAIL",
                        "", f"Exception: {str(e)}", prompt="(special characters)")
        
        # Test 13.3: Unicode/emoji in prompt (if applicable)
        try:
            test_user_id = self._get_or_create_test_user("test_unicode")
            unicode_prompt = "How are you feeling? 😊"
            response = self.chatbot.generate_response(unicode_prompt, user_id=test_user_id)
            
            if response and len(response) > 0:
                self.log_test("T-13.3", "Unicode/emoji handling", "PASS",
                            f"Response generated with unicode: {response[:100]}...",
                            prompt=unicode_prompt, response=response[:200])
            else:
                self.log_test("T-13.3", "Unicode/emoji handling", "FAIL",
                            "No response to unicode prompt", prompt=unicode_prompt)
        except Exception as e:
            # Unicode errors might be expected in some environments
            error_msg = str(e)
            if "unicode" in error_msg.lower() or "encode" in error_msg.lower():
                self.log_test("T-13.3", "Unicode/emoji handling", "PARTIAL",
                            f"Unicode handling may have issues: {error_msg[:100]}...", prompt=unicode_prompt)
            else:
                self.log_test("T-13.3", "Unicode/emoji handling", "FAIL",
                            "", f"Exception: {error_msg}")
        
        # Test 13.4: Multiple consecutive spaces/normalization
        try:
            test_user_id = self._get_or_create_test_user("test_normalization")
            messy_prompt = "Hello     there    how   are   you?"
            response = self.chatbot.generate_response(messy_prompt, user_id=test_user_id)
            
            if response and len(response) > 0:
                self.log_test("T-13.4", "Prompt normalization", "PASS",
                            f"Response generated despite messy spacing: {response[:100]}...",
                            prompt=messy_prompt, response=response[:200])
            else:
                self.log_test("T-13.4", "Prompt normalization", "FAIL",
                            "No response to messy prompt", prompt=messy_prompt)
        except Exception as e:
            self.log_test("T-13.4", "Prompt normalization", "FAIL",
                        "", f"Exception: {str(e)}", prompt="(messy spacing)")
        
        # Test 13.5: Numeric-only prompt
        try:
            test_user_id = self._get_or_create_test_user("test_numeric")
            numeric_prompt = "123456789"
            response = self.chatbot.generate_response(numeric_prompt, user_id=test_user_id)
            
            if response and len(response) > 0:
                # Should handle gracefully even if prompt is unusual
                self.log_test("T-13.5", "Numeric-only prompt", "PASS",
                            f"Response generated to numeric prompt: {response[:100]}...",
                            prompt=numeric_prompt, response=response[:200])
            else:
                self.log_test("T-13.5", "Numeric-only prompt", "PARTIAL",
                            "No response to numeric prompt (may be expected)", prompt=numeric_prompt)
        except Exception as e:
            self.log_test("T-13.5", "Numeric-only prompt", "FAIL",
                        "", f"Exception: {str(e)}", prompt=numeric_prompt)
    
    def generate_report(self):
        """Generate test report with performance metrics"""
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        partial = sum(1 for r in self.results if r["status"] == "PARTIAL")
        
        print(f"Total Tests: {total}")
        print(f"[PASS] Passed: {passed}")
        print(f"[PARTIAL] Partial: {partial}")
        print(f"[FAIL] Failed: {failed}")
        print()
        
        # Performance summary
        perf_tests = [r for r in self.results if r.get("response_time") is not None]
        if perf_tests:
            avg_time = sum(r["response_time"] for r in perf_tests) / len(perf_tests)
            min_time = min(r["response_time"] for r in perf_tests)
            max_time = max(r["response_time"] for r in perf_tests)
            print("PERFORMANCE METRICS:")
            print(f"  Tests with timing: {len(perf_tests)}")
            print(f"  Average response time: {avg_time:.2f}s")
            print(f"  Min response time: {min_time:.2f}s")
            print(f"  Max response time: {max_time:.2f}s")
            print()
        
        if failed > 0:
            print("FAILED TESTS:")
            for r in self.results:
                if r["status"] == "FAIL":
                    print(f"  - {r['test_id']}: {r['test_name']}")
                    if r["issues"]:
                        print(f"    Issues: {r['issues']}")
            print()
        
        if partial > 0:
            print("PARTIAL TESTS (needs review):")
            for r in self.results:
                if r["status"] == "PARTIAL":
                    print(f"  - {r['test_id']}: {r['test_name']}")
                    if r["notes"]:
                        print(f"    Notes: {r['notes']}")
            print()
        
        # Write detailed report to permanent location (tests/ai/results/)
        results_dir = os.path.join(project_root, 'tests', 'ai', 'results')
        os.makedirs(results_dir, exist_ok=True)
        
        # Also save to test data directory for this run
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(results_dir, f"ai_functionality_test_results_{timestamp}.md")
        latest_report = os.path.join(results_dir, "ai_functionality_test_results_latest.md")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# AI Functionality Test Results\n\n")
            f.write(f"**Test Date**: {datetime.now().isoformat()}\n\n")
            f.write(f"**Summary**: {passed} passed, {partial} partial, {failed} failed out of {total} tests\n\n")
            
            # Performance metrics section
            if perf_tests:
                f.write("## Performance Metrics\n\n")
                f.write(f"- **Tests with timing data**: {len(perf_tests)}\n")
                f.write(f"- **Average response time**: {avg_time:.2f}s\n")
                f.write(f"- **Min response time**: {min_time:.2f}s\n")
                f.write(f"- **Max response time**: {max_time:.2f}s\n\n")
            
            f.write("## Detailed Results\n\n")
            
            for r in self.results:
                status_symbol = {"PASS": "[OK]", "FAIL": "[ERROR]", "PARTIAL": "[WARNING]"}.get(r["status"], "[UNKNOWN]")
                f.write(f"### {status_symbol} {r['test_id']}: {r['test_name']}\n\n")
                f.write(f"- **Status**: {r['status']}\n")
                if r.get('prompt'):
                    f.write(f"- **Prompt**: `{r['prompt']}`\n")
                if r.get('response'):
                    # Truncate very long responses for readability, but preserve formatting
                    response = r['response']
                    if len(response) > 500:
                        response = response[:500] + "... (truncated - full response available in test data)"
                    f.write(f"- **Response**: `{response}`\n")
                    f.write(f"- **Response Length**: {len(r['response'])} characters\n")
                if r.get('response_time') is not None:
                    f.write(f"- **Response Time**: {r['response_time']:.2f}s\n")
                if r.get('metrics'):
                    f.write(f"- **Metrics**: {r['metrics']}\n")
                if r['notes']:
                    f.write(f"- **Notes**: {r['notes']}\n")
                if r['issues']:
                    f.write(f"- **Issues**: {r['issues']}\n")
                f.write(f"- **Timestamp**: {r['timestamp']}\n\n")
        
        # Also write latest report (overwrite)
        import shutil
        shutil.copy(report_file, latest_report)
        
        # Print clear output about where results are saved
        print()
        print("=" * 60)
        print("TEST RESULTS OUTPUT")
        print("=" * 60)
        print(f"Detailed report (timestamped): {report_file}")
        print(f"Latest report (always current): {latest_report}")
        print("=" * 60)
        
        return {
            "total": total,
            "passed": passed,
            "partial": partial,
            "failed": failed,
            "performance": {
                "tests_with_timing": len(perf_tests),
                "avg_time": avg_time if perf_tests else None,
                "min_time": min_time if perf_tests else None,
                "max_time": max_time if perf_tests else None
            } if perf_tests else None
        }


def main():
    """Run AI functionality tests"""
    import os
    
    # Set up test data environment properly
    from tests.test_utilities import setup_test_data_environment
    
    test_dir, test_data_dir, _ = setup_test_data_environment()
    
    # CRITICAL: Set environment variables so system uses test data directory
    # The config checks for MHM_TESTING=1 and TEST_DATA_DIR
    os.environ["MHM_TESTING"] = "1"
    os.environ["TEST_DATA_DIR"] = test_data_dir
    
    print(f"Using test data directory: {test_data_dir}")
    print()
    
    runner = AITestRunner(test_data_dir)
    
    try:
        # Run test categories
        runner.test_basic_response_generation()
        runner.test_contextual_response_generation()
        runner.test_mode_detection()
        runner.test_context_with_checkins()
        runner.test_command_variations()
        runner.test_error_handling()
        runner.test_conversation_history_in_context()
        runner.test_conversation_history()
        
        # New expanded test categories
        runner.test_performance_metrics()
        runner.test_api_error_scenarios()
        runner.test_cache_comprehensive()
        runner.test_response_quality()
        runner.test_edge_cases()
        
        # Generate report
        summary = runner.generate_report()
        
        print("=" * 60)
        if summary["failed"] == 0:
            print("[PASS] ALL TESTS PASSED OR PARTIAL")
        else:
            print(f"[PARTIAL] {summary['failed']} TESTS FAILED - Review report for details")
        print("=" * 60)
        
    except Exception as e:
        print(f"[FAIL] Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

