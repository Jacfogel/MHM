"""
AI Advanced Functionality Tests

Tests for multi-turn conversations, response coherence, personality consistency, 
and error recovery scenarios.
"""

import os
from unittest.mock import patch

from tests.ai.ai_test_base import AITestBase
from tests.test_utilities import TestUserFactory
from core.user_management import get_user_id_by_identifier


class TestAIAdvanced(AITestBase):
    __test__ = False  # Not a pytest test class - run via custom runner
    """Test advanced AI functionality: multi-turn, coherence, personality, error recovery"""
    
    def test_multi_turn_conversations(self):
        """Test 14: Multi-Turn Conversation Quality"""
        print("=" * 60)
        print("TEST CATEGORY 14: Multi-Turn Conversation Quality")
        print("=" * 60)
        
        user_id = "test_multiturn_user"
        
        try:
            success = TestUserFactory.create_basic_user(
                user_id,
                enable_checkins=True,
                test_data_dir=self.test_data_dir
            )
            
            if not success:
                self.log_test("T-14.0", "Create user for multi-turn tests", "FAIL",
                            "", "Failed to create test user")
                return
            
            import core.config
            with patch.object(core.config, "BASE_DATA_DIR", self.test_data_dir), \
                 patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(self.test_data_dir, 'users')):
                actual_user_id = get_user_id_by_identifier(user_id)
            
            if not actual_user_id:
                self.log_test("T-14.0", "Get user UUID for multi-turn tests", "FAIL",
                            "", "Could not get user UUID")
                return
            
            # Test 14.1: Multi-turn conversation maintains context
            try:
                # Get context info before generating responses
                context_info_before = self._build_context_info(actual_user_id, include_history=True)
                
                prompts = [
                    "I'm feeling overwhelmed with work",
                    "How can I manage my stress better?",
                    "Can you suggest specific techniques?"
                ]
                responses = []
                
                for prompt in prompts:
                    response = self.chatbot.generate_contextual_response(actual_user_id, prompt)
                    responses.append(response)
                
                # Update context info after conversation
                context_info_after = self._build_context_info(actual_user_id, include_history=True)
                context_info = {
                    **context_info_before,
                    "conversation_history_after": context_info_after.get("conversation_history_count", 0)
                }
                
                # Check if responses build on each other
                mentions_stress = any("stress" in r.lower() or "overwhelm" in r.lower() for r in responses[1:])
                maintains_context = any("work" in r.lower() or "overwhelm" in r.lower() for r in responses[1:])
                
                # Include all responses for multi-turn conversations
                all_responses = " | ".join(responses) if responses else ""
                
                status = "PASS" if (mentions_stress and maintains_context) else "PARTIAL"
                notes = f"Generated {len(responses)} responses. Context maintained: {maintains_context}, Stress mentioned: {mentions_stress}"
                self.log_test("T-14.1", "Multi-turn conversation maintains context", status, notes,
                            prompt=" | ".join(prompts), response=all_responses, test_type="contextual", context_info=context_info)
            except Exception as e:
                self.log_test("T-14.1", "Multi-turn conversation maintains context", "FAIL",
                            "", f"Exception: {str(e)}")
            
            # Test 14.2: Response coherence across turns
            try:
                # Get context info before generating responses
                context_info_before = self._build_context_info(actual_user_id, include_history=True)
                
                prompt1 = "I love reading books"
                response1 = self.chatbot.generate_contextual_response(actual_user_id, prompt1)
                
                prompt2 = "What genres do you think I'd like?"
                response2 = self.chatbot.generate_contextual_response(actual_user_id, prompt2)
                
                # Update context info after first exchange
                context_info_after = self._build_context_info(actual_user_id, include_history=True)
                context_info = {
                    **context_info_before,
                    "conversation_history_after_first": context_info_after.get("conversation_history_count", 0)
                }
                
                # Check if second response references the first (books/reading)
                references_books = "book" in response2.lower() or "read" in response2.lower()
                
                # Include all responses for multi-turn conversations
                all_responses = f"{response1} | {response2}"
                
                status = "PASS" if references_books else "PARTIAL"
                notes = f"Response coherence: {references_books}"
                self.log_test("T-14.2", "Response coherence across turns", status, notes,
                            prompt=f"{prompt1} | {prompt2}", response=all_responses, test_type="contextual", context_info=context_info)
            except Exception as e:
                self.log_test("T-14.2", "Response coherence across turns", "FAIL",
                            "", f"Exception: {str(e)}")
        
        except Exception as e:
            self.log_test("T-14.0", "Multi-turn conversation setup", "FAIL",
                        "", f"Exception during setup: {str(e)}")
    
    def test_personality_consistency(self):
        """Test 15: Personality Consistency"""
        print("=" * 60)
        print("TEST CATEGORY 15: Personality Consistency")
        print("=" * 60)
        
        user_id = "test_personality_user"
        
        try:
            success = TestUserFactory.create_basic_user(
                user_id,
                enable_checkins=True,
                test_data_dir=self.test_data_dir
            )
            
            if not success:
                self.log_test("T-15.0", "Create user for personality tests", "FAIL",
                            "", "Failed to create test user")
                return
            
            import core.config
            with patch.object(core.config, "BASE_DATA_DIR", self.test_data_dir), \
                 patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(self.test_data_dir, 'users')):
                actual_user_id = get_user_id_by_identifier(user_id)
            
            if not actual_user_id:
                self.log_test("T-15.0", "Get user UUID for personality tests", "FAIL",
                            "", "Could not get user UUID")
                return
            
            # Test 15.1: Consistent supportive tone
            try:
                # Get context info before generating responses
                context_info_before = self._build_context_info(actual_user_id, include_history=True)
                
                prompts = [
                    "I'm having a bad day",
                    "Nothing seems to work out",
                    "I feel frustrated"
                ]
                
                supportive_keywords = ["support", "here", "help", "understand", "feel", "okay", "alright"]
                responses = []
                supportive_count = 0
                
                for prompt in prompts:
                    response = self.chatbot.generate_contextual_response(actual_user_id, prompt)
                    responses.append(response)
                    if any(keyword in response.lower() for keyword in supportive_keywords):
                        supportive_count += 1
                
                # Update context info after conversation
                context_info_after = self._build_context_info(actual_user_id, include_history=True)
                context_info = {
                    **context_info_before,
                    "conversation_history_after": context_info_after.get("conversation_history_count", 0)
                }
                
                # Check if at least 2/3 responses are supportive
                consistency = supportive_count >= 2
                
                status = "PASS" if consistency else "PARTIAL"
                notes = f"Supportive tone consistency: {supportive_count}/{len(prompts)} responses"
                # Include all responses for multi-turn conversation
                all_responses = " | ".join(responses) if responses else ""
                self.log_test("T-15.1", "Consistent supportive tone", status, notes,
                            prompt=" | ".join(prompts), response=all_responses, test_type="contextual", context_info=context_info)
            except Exception as e:
                self.log_test("T-15.1", "Consistent supportive tone", "FAIL",
                            "", f"Exception: {str(e)}")
            
            # Test 15.2: Personality traits remain consistent
            try:
                # Get context info before generating response
                context_info = self._build_context_info(actual_user_id, include_history=False)
                
                prompt = "Tell me about yourself"
                response = self.chatbot.generate_contextual_response(actual_user_id, prompt)
                
                # Check for key personality traits (supportive, calm, helpful)
                has_traits = any(trait in response.lower() for trait in [
                    "support", "help", "assist", "calm", "encourage", "motivate"
                ])
                
                status = "PASS" if has_traits else "PARTIAL"
                notes = f"Personality traits present: {has_traits}"
                self.log_test("T-15.2", "Personality traits remain consistent", status, notes,
                            prompt=prompt, response=response, test_type="contextual", context_info=context_info)
            except Exception as e:
                self.log_test("T-15.2", "Personality traits remain consistent", "FAIL",
                            "", f"Exception: {str(e)}")
        
        except Exception as e:
            self.log_test("T-15.0", "Personality consistency setup", "FAIL",
                        "", f"Exception during setup: {str(e)}")
    
    def test_error_recovery_scenarios(self):
        """Test 16: Error Recovery Scenarios"""
        print("=" * 60)
        print("TEST CATEGORY 16: Error Recovery Scenarios")
        print("=" * 60)
        
        user_id = "test_error_recovery_user"
        
        try:
            success = TestUserFactory.create_basic_user(
                user_id,
                enable_checkins=True,
                test_data_dir=self.test_data_dir
            )
            
            if not success:
                self.log_test("T-16.0", "Create user for error recovery tests", "FAIL",
                            "", "Failed to create test user")
                return
            
            import core.config
            with patch.object(core.config, "BASE_DATA_DIR", self.test_data_dir), \
                 patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(self.test_data_dir, 'users')):
                actual_user_id = get_user_id_by_identifier(user_id)
            
            if not actual_user_id:
                self.log_test("T-16.0", "Get user UUID for error recovery tests", "FAIL",
                            "", "Could not get user UUID")
                return
            
            # Test 16.1: Recovery after malformed input
            try:
                malformed_prompts = [
                    "..." * 50,  # Repeated punctuation
                    "a" * 200,   # Repetitive characters
                    "",           # Empty (already tested, but include here)
                ]
                
                recovery_success = 0
                for prompt in malformed_prompts[:2]:  # Skip empty
                    try:
                        response = self.chatbot.generate_contextual_response(actual_user_id, prompt)
                        if response and len(response.strip()) > 0:
                            recovery_success += 1
                    except Exception:
                        pass  # Count as failed recovery
                
                status = "PASS" if recovery_success >= 1 else "PARTIAL"
                notes = f"Error recovery: {recovery_success}/{len(malformed_prompts)-1} malformed prompts handled"
                self.log_test("T-16.1", "Recovery after malformed input", status, notes,
                            prompt=" | ".join([p[:50] + "..." if len(p) > 50 else p for p in malformed_prompts[:2]]))
            except Exception as e:
                self.log_test("T-16.1", "Recovery after malformed input", "FAIL",
                            "", f"Exception: {str(e)}")
            
            # Test 16.2: Graceful degradation when context unavailable
            try:
                # Get context info for user (should exist for actual_user_id)
                context_info = self._build_context_info(actual_user_id, include_history=False)
                
                # Force a response even if context might be incomplete
                prompt = "How am I doing?"
                response = self.chatbot.generate_contextual_response(actual_user_id, prompt)
                
                # Response should still be generated even if context is limited
                has_response = response and len(response.strip()) > 0
                is_helpful = "help" in response.lower() or "support" in response.lower() or "here" in response.lower()
                
                status = "PASS" if (has_response and is_helpful) else "PARTIAL"
                notes = f"Graceful degradation: Response generated: {has_response}, Helpful: {is_helpful}"
                self.log_test("T-16.2", "Graceful degradation when context unavailable", status, notes,
                            prompt=prompt, response=response, test_type="contextual", context_info=context_info)
            except Exception as e:
                self.log_test("T-16.2", "Graceful degradation when context unavailable", "FAIL",
                            "", f"Exception: {str(e)}")
        
        except Exception as e:
            self.log_test("T-16.0", "Error recovery setup", "FAIL",
                        "", f"Exception during setup: {str(e)}")

