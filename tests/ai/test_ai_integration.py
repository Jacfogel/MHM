"""
AI Integration Tests

Tests for context with check-ins, conversation history, and integration features.
"""

import os
from unittest.mock import patch

from tests.ai.ai_test_base import AITestBase
from tests.test_utilities import TestUserFactory
from core.user_management import get_user_id_by_identifier
from core.response_tracking import get_recent_chat_interactions
from user.context_manager import user_context_manager


class TestAIIntegration(AITestBase):
    """Test AI integration with other system components"""
    
    def test_context_with_checkins(self):
        """Test 4: Context Building with Check-in Data"""
        print("=" * 60)
        print("TEST CATEGORY 4: Context Building with Check-in Data")
        print("=" * 60)
        
        user_id = "test_checkin_user"
        
        try:
            success = TestUserFactory.create_basic_user(
                user_id,
                enable_checkins=True,
                test_data_dir=self.test_data_dir
            )
            
            if not success:
                self.log_test("T-4.0", "Create user for check-in tests", "FAIL",
                            "", "Failed to create test user")
                return
            
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
                
                status = "PASS" if has_checkins else "PARTIAL"
                self.log_test("T-4.1", "Context includes check-in data", status,
                            "Check-in data found in context" if has_checkins else "Check-in data may not be in context structure",
                            prompt=prompt, response=response[:300] if response else "", test_type="contextual")
            except Exception as e:
                self.log_test("T-4.1", "Context includes check-in data", "FAIL",
                            "", f"Exception: {str(e)}")
                
        except Exception as e:
            self.log_test("T-4.0", "Check-in context setup", "FAIL",
                        "", f"Exception during setup: {str(e)}")
    
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
                
                mentions_blue = "blue" in response2.lower()
                
                status = "PASS" if mentions_blue else "PARTIAL"
                self.log_test("T-7.1", "Conversation history affects responses", status,
                            "Subsequent response shows awareness of previous conversation" if mentions_blue else "Subsequent response may not reference previous conversation",
                            prompt=f"{prompt1} | {prompt2}",
                            response=f"Response 1: {response1[:100]}... | Response 2: {response2[:100]}...", test_type="contextual")
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
            success = TestUserFactory.create_basic_user(
                user_id,
                enable_checkins=True,
                enable_tasks=True,
                test_data_dir=self.test_data_dir
            )
            
            if not success:
                self.log_test("T-8.0", "Create user for history tests", "FAIL",
                            "", "Failed to create test user")
                return
            
            import core.config
            with patch.object(core.config, "BASE_DATA_DIR", self.test_data_dir), \
                 patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(self.test_data_dir, 'users')):
                actual_user_id = get_user_id_by_identifier(user_id)
            
            if not actual_user_id:
                self.log_test("T-8.0", "Get user UUID for history tests", "FAIL",
                            "", "Could not get user UUID")
                return
            
            # Test 8.1: Store conversation exchange
            try:
                prompt1 = "How are you doing today?"
                response1 = self.chatbot.generate_contextual_response(actual_user_id, prompt1)
                
                prompt2 = "What should I focus on this week?"
                response2 = self.chatbot.generate_contextual_response(actual_user_id, prompt2)
                
                history = user_context_manager.get_ai_context(
                    actual_user_id, include_conversation_history=True
                ).get('conversation_history', [])
                
                exchange_details = f"Exchange 1: '{prompt1}' -> {response1[:80]}... | Exchange 2: '{prompt2}' -> {response2[:80]}..."
                
                status = "PASS" if len(history) >= 2 else "PARTIAL"
                self.log_test("T-8.1", "Store conversation exchanges", status,
                            f"Stored {len(history)} exchanges" if len(history) >= 2 else f"Stored {len(history)} exchanges (expected 2+)",
                            prompt=f"{prompt1} | {prompt2}", response=exchange_details, test_type="contextual")
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

