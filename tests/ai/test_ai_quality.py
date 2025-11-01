"""
AI Quality and Edge Case Tests

Tests for response quality validation, formatting, and edge case handling.
"""

import os
from unittest.mock import patch

from tests.ai.ai_test_base import AITestBase
from tests.test_utilities import TestUserFactory
from core.user_management import get_user_id_by_identifier
from core.user_data_handlers import save_user_data


class TestAIQuality(AITestBase):
    """Test AI response quality and edge cases"""
    
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
                                prompt=prompt, response=response[:200], test_type="chat")
                else:
                    status = "FAIL" if is_empty or is_only_whitespace else "PARTIAL"
                    self.log_test("T-12.1", "Response non-empty validation", status,
                                f"Response may be too short or empty: {len(response_trimmed)} chars",
                                prompt=prompt, response=response[:200], test_type="chat")
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
                error_patterns = [
                    "error", "exception", "failed", "unable to",
                    "cannot", "null", "undefined", "none"
                ]
                error_found = any(pattern in response.lower() for pattern in error_patterns)
                helpful_errors = ["i'm having trouble", "please try again", "help", "support"]
                is_helpful_error = any(phrase in response.lower() for phrase in helpful_errors)
                
                if not error_found or is_helpful_error:
                    self.log_test("T-12.2", "Response error message validation", "PASS",
                                f"Response does not contain unexpected errors: {response[:100]}...",
                                prompt=prompt, response=response[:200], test_type="chat")
                else:
                    self.log_test("T-12.2", "Response error message validation", "PARTIAL",
                                f"Response may contain error patterns: {response[:100]}...",
                                prompt=prompt, response=response[:200], test_type="chat")
            else:
                self.log_test("T-12.2", "Response error message validation", "FAIL",
                            "No response generated", prompt=prompt)
        except Exception as e:
            self.log_test("T-12.2", "Response error message validation", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 12.3: Contextual response should reference user context
        try:
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
                        save_user_data(contextual_user_id, {"context": {"preferred_name": "QualityTest"}})
                        
                        prompt = "How am I doing?"
                        response = self.chatbot.generate_contextual_response(contextual_user_id, prompt)
                        
                        if response:
                            has_user_ref = "QualityTest" in response or "qualitytest" in response.lower()
                            has_contextual_language = any(word in response.lower() for word in [
                                "you", "your", "today", "recent", "check", "activity"
                            ])
                            
                            is_contextual = has_user_ref or has_contextual_language
                            status = "PASS" if is_contextual else "PARTIAL"
                            self.log_test("T-12.3", "Contextual response quality", status,
                                        f"Response appears {'contextual' if is_contextual else 'generic'}: {response[:100]}...",
                                        prompt=prompt, response=response[:300], test_type="contextual")
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
        
        # Test 12.4: Response format validation
        try:
            test_user_id = self._get_or_create_test_user("test_format_validation")
            prompt = "Tell me a fact"
            response = self.chatbot.generate_response(prompt, user_id=test_user_id)
            
            if response:
                has_multiple_newlines = response.count('\n\n\n') > 0
                has_trailing_newlines = response.endswith('\n\n') or response.endswith('\n\n\n')
                has_leading_whitespace = response.startswith(' ') or response.startswith('\t')
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
                                prompt=prompt, response=response[:200], test_type="chat")
                else:
                    self.log_test("T-12.4", "Response format validation", "PARTIAL",
                                f"Format issues detected: {', '.join(issues)}",
                                prompt=prompt, response=response[:200], test_type="chat")
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
            long_prompt = "Tell me " + "about yourself " * 50
            response = self.chatbot.generate_response(long_prompt, user_id=test_user_id)
            
            if response and len(response) > 0:
                status = "PASS" if len(response) >= 10 else "PARTIAL"
                self.log_test("T-13.1", "Very long prompt handling", status,
                            f"Response generated for long prompt ({len(long_prompt)} chars): {response[:100]}...",
                            prompt=f"{long_prompt[:50]}... ({len(long_prompt)} chars)", response=response[:200], test_type="chat")
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
                            prompt=special_prompt, response=response[:200], test_type="chat")
            else:
                self.log_test("T-13.2", "Special characters handling", "FAIL",
                            "No response to special character prompt", prompt=special_prompt)
        except Exception as e:
            self.log_test("T-13.2", "Special characters handling", "FAIL",
                        "", f"Exception: {str(e)}", prompt="(special characters)")
        
        # Test 13.3: Unicode/emoji in prompt (skip emoji to avoid Windows console encoding issues)
        try:
            test_user_id = self._get_or_create_test_user("test_unicode")
            # Use Unicode text instead of emoji to avoid Windows console encoding errors
            unicode_prompt = "How are you feeling? (with special characters: é, ñ, ü)"
            response = self.chatbot.generate_response(unicode_prompt, user_id=test_user_id)
            
            if response and len(response) > 0:
                self.log_test("T-13.3", "Unicode character handling", "PASS",
                            f"Response generated with unicode: {response[:100]}...",
                            prompt=unicode_prompt, response=response[:200], test_type="chat")
            else:
                self.log_test("T-13.3", "Unicode character handling", "FAIL",
                            "No response to unicode prompt", prompt=unicode_prompt)
        except Exception as e:
            error_msg = str(e)
            if "unicode" in error_msg.lower() or "encode" in error_msg.lower():
                self.log_test("T-13.3", "Unicode character handling", "PARTIAL",
                            f"Unicode handling may have issues: {error_msg[:100]}...", prompt=unicode_prompt)
            else:
                self.log_test("T-13.3", "Unicode character handling", "FAIL",
                            "", f"Exception: {error_msg}")
        
        # Test 13.4: Multiple consecutive spaces/normalization
        try:
            test_user_id = self._get_or_create_test_user("test_normalization")
            messy_prompt = "Hello     there    how   are   you?"
            response = self.chatbot.generate_response(messy_prompt, user_id=test_user_id)
            
            if response and len(response) > 0:
                self.log_test("T-13.4", "Prompt normalization", "PASS",
                            f"Response generated despite messy spacing: {response[:100]}...",
                            prompt=messy_prompt, response=response[:200], test_type="chat")
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
                self.log_test("T-13.5", "Numeric-only prompt", "PASS",
                            f"Response generated to numeric prompt: {response[:100]}...",
                            prompt=numeric_prompt, response=response[:200], test_type="chat")
            else:
                self.log_test("T-13.5", "Numeric-only prompt", "PARTIAL",
                            "No response to numeric prompt (may be expected)", prompt=numeric_prompt)
        except Exception as e:
            self.log_test("T-13.5", "Numeric-only prompt", "FAIL",
                        "", f"Exception: {str(e)}", prompt=numeric_prompt)

