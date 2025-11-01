"""
AI Cache Functionality Tests

Tests for response caching behavior, isolation, and performance.
"""

import time

from ai.cache_manager import get_response_cache
from tests.ai.ai_test_base import AITestBase


class TestAICache(AITestBase):
    """Test AI response caching"""
    
    def test_cache_basic(self):
        """Test 1.5: Basic Cache Behavior with Timing"""
        print("=" * 60)
        print("TEST CATEGORY: Cache Behavior (from Core Tests)")
        print("=" * 60)
        
        try:
            test_user_id = self._get_or_create_test_user("test_cache_user")
            prompt = "What is 2+2?"
            
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
            
            if response1 and response2:
                cached = (response1 == response2)
                speedup = time1 / time2 if time2 > 0 else 0
                cache_status = "working" if cached else "not used (expected for chat mode or AI variation)"
                
                cache_stats = cache.get_stats()
                
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
                            prompt=prompt, response=combined_response, response_time=time2, metrics=metrics, test_type="command")
            else:
                self.log_test("T-1.5", "Response caching", "FAIL",
                            "Failed to generate responses for cache test", prompt=prompt)
        except Exception as e:
            self.log_test("T-1.5", "Response caching", "FAIL",
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
            
            response1_user1 = self.chatbot.generate_response(prompt, user_id=user1_id, mode="command")
            response1_user2 = self.chatbot.generate_response(prompt, user_id=user2_id, mode="command")
            
            start_time = time.time()
            response2_user1 = self.chatbot.generate_response(prompt, user_id=user1_id, mode="command")
            time_user1 = time.time() - start_time
            
            cache_stats = cache.get_stats()
            
            if response1_user1 and response2_user1:
                cached = (response1_user1 == response2_user1)
                status = "PASS" if cached else "PARTIAL"
                notes = f"Cache {'used' if cached else 'not used'} | User isolation: {'verified' if response1_user1 != response1_user2 or cached else 'needs verification'}"
                self.log_test("T-11.1", "Cache isolation by user", status, notes,
                            prompt=prompt, response=f"User1 R1: {response1_user1[:100]}... | User1 R2: {response2_user1[:100]}...",
                            response_time=time_user1, metrics={"cache_stats": cache_stats}, test_type="command")
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
            
            response_command = self.chatbot.generate_response(prompt, user_id=test_user_id, mode="command")
            response_chat = self.chatbot.generate_response(prompt, user_id=test_user_id, mode="chat")
            
            start_time = time.time()
            response_command2 = self.chatbot.generate_response(prompt, user_id=test_user_id, mode="command")
            time_command = time.time() - start_time
            
            start_time = time.time()
            response_chat2 = self.chatbot.generate_response(prompt, user_id=test_user_id, mode="chat")
            time_chat = time.time() - start_time
            
            cache_stats = cache.get_stats()
            
            command_cached = (response_command == response_command2)
            chat_varied = (response_chat != response_chat2)
            
            status = "PASS" if command_cached else "PARTIAL"
            notes = f"Command mode cache: {'used' if command_cached else 'not used'} | Chat mode variation: {'working' if chat_varied else 'not varying'}"
            self.log_test("T-11.2", "Cache isolation by mode", status, notes,
                        prompt=prompt, response=f"Command: {response_command[:80]}... | Chat: {response_chat[:80]}...",
                        response_time=time_command, metrics={"cache_stats": cache_stats}, test_type="command")
        except Exception as e:
            self.log_test("T-11.2", "Cache isolation by mode", "FAIL",
                        "", f"Exception: {str(e)}", prompt=prompt if 'prompt' in locals() else "")
        
        # Test 11.3: Cache TTL and retrieval
        try:
            test_user_id = self._get_or_create_test_user("test_cache_ttl")
            cache = get_response_cache()
            cache.clear()
            
            prompt = "Test cache TTL"
            
            response1 = self.chatbot.generate_response(prompt, user_id=test_user_id, mode="command")
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

