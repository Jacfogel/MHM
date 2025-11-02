"""
AI Performance Tests

Tests for response times, performance metrics, and quality validation.
"""

import time
import os
from unittest.mock import patch

from tests.ai.ai_test_base import AITestBase
from tests.test_utilities import TestUserFactory
from core.user_management import get_user_id_by_identifier


class TestAIPerformance(AITestBase):
    __test__ = False  # Not a pytest test class - run via custom runner
    """Test AI performance metrics"""
    
    def test_performance_metrics(self):
        """Test 9: Performance Metrics"""
        print("=" * 60)
        print("TEST CATEGORY 9: Performance Metrics")
        print("=" * 60)
        
        test_user_id = self._get_or_create_test_user("test_perf_user")
        
        # Test 9.1: Simple query response time
        try:
            # Non-contextual response - minimal context
            context_info = self._build_context_info(None)
            context_info["note"] = "Non-contextual response (minimal context provided)"
            
            prompt = "Hello"
            start_time = time.time()
            response = self.chatbot.generate_response(prompt, user_id=test_user_id)
            response_time = time.time() - start_time
            
            if response and response_time < 10.0:
                status = "PASS" if response_time < 5.0 else "PARTIAL"
                self.log_test("T-9.1", "Simple query response time", status,
                            f"Response time: {response_time:.2f}s (target <5s)", 
                            prompt=prompt, response=response, response_time=response_time, test_type="chat", context_info=context_info)
            else:
                self.log_test("T-9.1", "Simple query response time", "FAIL" if response_time >= 10.0 else "PARTIAL",
                            f"Response time too slow: {response_time:.2f}s" if response_time >= 10.0 else f"Response time: {response_time:.2f}s",
                            prompt=prompt, response_time=response_time)
        except Exception as e:
            self.log_test("T-9.1", "Simple query response time", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 9.2: Contextual query response time
        try:
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
                        # Get context info before generating response
                        context_info = self._build_context_info(contextual_user_id, include_history=False)
                        
                        prompt = "How am I doing today?"
                        start_time = time.time()
                        response = self.chatbot.generate_contextual_response(contextual_user_id, prompt)
                        response_time = time.time() - start_time
                        
                        if response and response_time < 15.0:
                            status = "PASS" if response_time < 10.0 else "PARTIAL"
                            self.log_test("T-9.2", "Contextual query response time", status,
                                        f"Response time: {response_time:.2f}s (target <10s)", 
                                        prompt=prompt, response=response, response_time=response_time, test_type="contextual", context_info=context_info)
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
            # Non-contextual response - minimal context
            context_info = self._build_context_info(None)
            context_info["note"] = "Non-contextual response (minimal context provided)"
            
            prompt = "Tell me a short story"
            response = self.chatbot.generate_response(prompt, user_id=test_user_id)
            
            if response:
                min_length = 10
                max_length = 2000
                
                # Validate response actually matches prompt (should mention story or storytelling)
                story_indicators = ["story", "tale", "once", "narrative"]
                matches_prompt = any(indicator in response.lower() for indicator in story_indicators)
                
                if min_length <= len(response) <= max_length:
                    notes = f"Response length: {len(response)} chars (acceptable range: {min_length}-{max_length})"
                    if not matches_prompt:
                        notes += ". Response may not match prompt ('Tell me a short story')"
                    status = "PASS" if matches_prompt else "PARTIAL"
                    self.log_test("T-9.3", "Response length validation", status,
                                notes,
                                prompt=prompt, response=response, test_type="chat", context_info=context_info)
                else:
                    status = "PARTIAL" if len(response) < min_length else "FAIL"
                    self.log_test("T-9.3", "Response length validation", status,
                                f"Response length: {len(response)} chars (expected {min_length}-{max_length})",
                                prompt=prompt, response=response[:300], test_type="chat")
            else:
                self.log_test("T-9.3", "Response length validation", "FAIL",
                            "No response generated", prompt=prompt)
        except Exception as e:
            self.log_test("T-9.3", "Response length validation", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")

