"""
AI Integration Tests

Tests for context with check-ins, conversation history, and integration features.
"""

import os
from unittest.mock import patch
from datetime import datetime

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
                
                # Get check-in status information
                from core.response_tracking import get_recent_checkins
                recent_checkins = get_recent_checkins(actual_user_id, limit=10) if actual_user_id else []  # get_recent_checkins uses limit, not days
                checkins_today = [c for c in recent_checkins if c.get('timestamp', '').startswith(datetime.now().strftime('%Y-%m-%d'))]
                
                prompt = "How have I been doing with my check-ins?"
                response = self.chatbot.generate_contextual_response(actual_user_id, prompt)
                
                # Build context info for report
                context_info = {
                    "has_checkin_data": has_checkins,
                    "checkins_today": len(checkins_today),
                    "recent_checkins_count": len(recent_checkins),
                    "context_keys": list(context.keys()) if isinstance(context, dict) else []
                }
                
                # Validate that AI doesn't claim check-ins exist when there are none
                has_incorrect_claim = False
                if len(recent_checkins) == 0 and len(checkins_today) == 0:
                    # Check if AI incorrectly claims they've been checking in
                    incorrect_phrases = [
                        "you've been checking in",
                        "checking in consistently",
                        "your check-ins",
                        "been doing check-ins"
                    ]
                    response_lower = response.lower() if response else ""
                    has_incorrect_claim = any(phrase in response_lower for phrase in incorrect_phrases)
                
                # Test passes if context structure includes check-in fields, but fails if AI makes incorrect claims
                if has_incorrect_claim:
                    status = "FAIL"
                    notes = f"AI incorrectly claims check-ins exist when there are none (0 recent, 0 today). Check-in context structure exists: {has_checkins}"
                else:
                    status = "PASS" if has_checkins else "PARTIAL"
                    notes = f"Check-in context structure: {has_checkins}. Today's check-ins: {len(checkins_today)}, Recent: {len(recent_checkins)}"
                
                self.log_test("T-4.1", "Context includes check-in data", status, notes,
                            prompt=prompt, response=response, 
                            test_type="contextual", context_info=context_info)
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
                # Get context info before generating responses
                context_info_before = self._build_context_info(actual_user_id, include_history=True)
                
                prompt1 = "My favorite color is blue"
                response1 = self.chatbot.generate_contextual_response(actual_user_id, prompt1)
                
                prompt2 = "What's my favorite color?"
                response2 = self.chatbot.generate_contextual_response(actual_user_id, prompt2)
                
                # Update context info after first exchange
                context_info_after = self._build_context_info(actual_user_id, include_history=True)
                context_info = {
                    **context_info_before,
                    "conversation_history_after_first": context_info_after.get("conversation_history_count", 0)
                }
                
                mentions_blue = "blue" in response2.lower()
                
                status = "PASS" if mentions_blue else "PARTIAL"
                # Include all responses for multi-turn conversations (separated by |)
                all_responses = f"{response1} | {response2}"
                notes = f"Subsequent response shows awareness of previous conversation" if mentions_blue else f"Subsequent response may not reference previous conversation"
                self.log_test("T-7.1", "Conversation history affects responses", status,
                            notes,
                            prompt=f"{prompt1} | {prompt2}",
                            response=all_responses, test_type="contextual", context_info=context_info)
            except Exception as e:
                self.log_test("T-7.1", "Conversation history affects responses", "FAIL",
                            "", f"Exception: {str(e)}")
            
            # Test 7.2: Conversation history included in context
            # NOTE: This is a deterministic test that verifies context structure includes conversation_history.
            # It could potentially be moved to unit tests, but remains here to verify integration with context manager.
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
                # Check if check-in data exists before first response
                from core.response_tracking import get_recent_checkins
                from datetime import datetime
                checkins_before = get_recent_checkins(actual_user_id, limit=10) if actual_user_id else []
                
                prompt1 = "How are you doing today?"
                response1 = self.chatbot.generate_contextual_response(actual_user_id, prompt1)
                
                prompt2 = "What should I focus on this week?"
                response2 = self.chatbot.generate_contextual_response(actual_user_id, prompt2)
                
                history = user_context_manager.get_ai_context(
                    actual_user_id, include_conversation_history=True
                ).get('conversation_history', [])
                
                # Check if AI inappropriately references check-in data that doesn't exist
                checkin_issues = []
                if len(checkins_before) == 0:
                    # No check-in data exists - AI should not reference specific check-in stats
                    inappropriate_claims = [
                        "you've been eating breakfast",
                        "eating breakfast 90",
                        "breakfast 90%",
                        "90% of the time"
                    ]
                    combined_responses = f"{response1} {response2}".lower()
                    for claim in inappropriate_claims:
                        if claim in combined_responses:
                            checkin_issues.append(f"AI references breakfast stats when no check-in data exists")
                            break
                
                # Include all responses for multi-turn conversations
                all_responses = f"{response1} | {response2}"
                
                status = "PASS" if len(history) >= 2 else "PARTIAL"
                if checkin_issues:
                    status = "FAIL"
                    notes = f"Stored {len(history)} exchanges. Issues: {'; '.join(checkin_issues)}"
                else:
                    notes = f"Stored {len(history)} exchanges"
                
                # Include context info about check-ins
                context_info = {
                    "checkins_before_prompts": len(checkins_before),
                    "history_count": len(history)
                }
                
                self.log_test("T-8.1", "Store conversation exchanges", status,
                            notes,
                            prompt=f"{prompt1} | {prompt2}", response=all_responses, 
                            test_type="contextual", context_info=context_info)
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

