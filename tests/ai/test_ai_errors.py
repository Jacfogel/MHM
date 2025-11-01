"""
AI Error Handling Tests

Tests for error scenarios, fallbacks, and edge cases.
"""

from unittest.mock import patch, MagicMock
import requests

from tests.ai.ai_test_base import AITestBase


class TestAIErrors(AITestBase):
    """Test AI error handling and fallbacks"""
    
    def test_error_handling(self):
        """Test 6: Error Handling and Fallbacks"""
        print("=" * 60)
        print("TEST CATEGORY 6: Error Handling and Fallbacks")
        print("=" * 60)
        
        # Test 6.1: Invalid user ID handling
        try:
            response = self.chatbot.generate_contextual_response(None, "Hello")
            if response:
                self.log_test("T-6.1", "Invalid user_id (None) handling", "PASS",
                            "Response generated with None user_id", prompt="Hello", response=response[:200])
            else:
                self.log_test("T-6.1", "Invalid user_id (None) handling", "PARTIAL",
                            "No response generated for None user_id")
        except Exception as e:
            error_msg = str(e)
            if "None" in error_msg or "user" in error_msg.lower():
                self.log_test("T-6.1", "Invalid user_id (None) handling", "PASS",
                            f"Error handled: {error_msg[:100]}...", prompt="Hello")
            else:
                self.log_test("T-6.1", "Invalid user_id (None) handling", "FAIL",
                            "", f"Unexpected exception: {error_msg}")
        
        # Test 6.2: Missing context data handling
        try:
            test_user_id = self._get_or_create_test_user("test_empty_user")
            prompt = "How am I doing?"
            response = self.chatbot.generate_contextual_response(test_user_id, prompt)
            
            if response and len(response) > 0:
                self.log_test("T-6.2", "Missing context data handling", "PASS",
                            "Response generated despite missing context data", prompt=prompt, response=response[:200], test_type="contextual")
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
                            "Response generated for empty prompt", prompt="(empty)", response=response[:200], test_type="chat")
            else:
                self.log_test("T-6.3", "Empty prompt handling", "PARTIAL",
                            "No response for empty prompt (may be expected)")
        except Exception as e:
            self.log_test("T-6.3", "Empty prompt handling", "PASS",
                        f"Exception handled: {str(e)[:100]}...", prompt="(empty)")
    
    def test_api_error_scenarios(self):
        """Test 10: API Error Scenarios (using mocks)"""
        print("=" * 60)
        print("TEST CATEGORY 10: API Error Scenarios")
        print("=" * 60)
        
        test_user_id = self._get_or_create_test_user("test_error_scenarios")
        
        # Test 10.1: Connection error handling
        try:
            with patch('ai.chatbot.requests.get') as mock_get:
                mock_get.side_effect = requests.ConnectionError("Connection refused")
                
                original_available = self.chatbot.lm_studio_available
                self.chatbot.lm_studio_available = False
                
                prompt = "Test connection error"
                response = self.chatbot.generate_response(prompt, user_id=test_user_id)
                
                self.chatbot.lm_studio_available = original_available
                
                if response and len(response) > 0:
                    is_fallback = "trouble" in response.lower() or "support" in response.lower() or "help" in response.lower()
                    status = "PASS" if is_fallback else "PARTIAL"
                    self.log_test("T-10.1", "Connection error handling", status,
                                f"Fallback response provided: {response[:100]}...",
                                prompt=prompt, response=response[:200], test_type="chat")
                else:
                    self.log_test("T-10.1", "Connection error handling", "FAIL",
                                "No response generated on connection error", prompt=prompt)
        except Exception as e:
            self.log_test("T-10.1", "Connection error handling", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 10.2: Timeout handling
        try:
            with patch('ai.chatbot.requests.post') as mock_post:
                mock_post.side_effect = requests.Timeout("Request timed out")
                
                prompt = "Test timeout"
                response = self.chatbot.generate_response(prompt, user_id=test_user_id, timeout=1)
                
                if response and len(response) > 0:
                    self.log_test("T-10.2", "Timeout handling", "PASS",
                                f"Response provided after timeout: {response[:100]}...",
                                prompt=prompt, response=response[:200], test_type="chat")
                else:
                    self.log_test("T-10.2", "Timeout handling", "FAIL",
                                "No response generated after timeout", prompt=prompt)
        except Exception as e:
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
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"invalid": "structure"}
                mock_post.return_value = mock_response
                
                original_available = self.chatbot.lm_studio_available
                self.chatbot.lm_studio_available = True
                
                prompt = "Test invalid response"
                response = self.chatbot.generate_response(prompt, user_id=test_user_id)
                
                self.chatbot.lm_studio_available = original_available
                
                if response and len(response) > 0:
                    self.log_test("T-10.3", "Invalid API response handling", "PASS",
                                f"Response provided despite invalid API response: {response[:100]}...",
                                prompt=prompt, response=response[:200], test_type="chat")
                else:
                    self.log_test("T-10.3", "Invalid API response handling", "FAIL",
                                "No response generated for invalid API response", prompt=prompt)
        except Exception as e:
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
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.text = "Internal Server Error"
                mock_post.return_value = mock_response
                
                original_available = self.chatbot.lm_studio_available
                self.chatbot.lm_studio_available = True
                
                prompt = "Test server error"
                response = self.chatbot.generate_response(prompt, user_id=test_user_id)
                
                self.chatbot.lm_studio_available = original_available
                
                if response and len(response) > 0:
                    self.log_test("T-10.4", "Server error (5xx) handling", "PASS",
                                f"Fallback response provided: {response[:100]}...",
                                prompt=prompt, response=response[:200], test_type="chat")
                else:
                    self.log_test("T-10.4", "Server error (5xx) handling", "FAIL",
                                "No response generated for server error", prompt=prompt)
        except Exception as e:
            self.log_test("T-10.4", "Server error (5xx) handling", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")

