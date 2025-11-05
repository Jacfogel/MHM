"""
Tests for ai/cache_manager.py - Cache eviction and expiry functionality.
"""

import pytest
import time
from unittest.mock import patch, Mock
from ai.cache_manager import ResponseCache, ContextCache, CacheEntry, get_response_cache, get_context_cache


class TestResponseCache:
    """Test ResponseCache functionality."""
    
    def test_cache_initialization(self):
        """Test cache initialization with default parameters."""
        cache = ResponseCache()
        assert cache.max_size == 100
        assert cache.ttl == 300
        assert len(cache.cache) == 0
        assert len(cache.access_times) == 0
    
    def test_cache_initialization_custom_params(self):
        """Test cache initialization with custom parameters."""
        cache = ResponseCache(max_size=50, ttl=600)
        assert cache.max_size == 50
        assert cache.ttl == 600
    
    def test_generate_key(self):
        """Test cache key generation."""
        cache = ResponseCache()
        
        # Test with different parameters
        key1 = cache._generate_key("test prompt", "user1", "test_type")
        key2 = cache._generate_key("test prompt", "user1", "test_type")
        key3 = cache._generate_key("test prompt", "user2", "test_type")
        key4 = cache._generate_key("different prompt", "user1", "test_type")
        
        # Same parameters should generate same key
        assert key1 == key2
        
        # Different parameters should generate different keys
        assert key1 != key3
        assert key1 != key4
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = ResponseCache()
        
        # Test setting and getting a response
        cache.set("test prompt", "test response", "user1", "test_type")
        result = cache.get("test prompt", "user1", "test_type")
        
        assert result == "test response"
    
    def test_cache_miss(self):
        """Test cache miss scenarios."""
        cache = ResponseCache()
        
        # Test getting non-existent entry
        result = cache.get("non-existent prompt", "user1", "test_type")
        assert result is None
        
        # Test getting entry with different parameters
        cache.set("test prompt", "test response", "user1", "test_type")
        result = cache.get("test prompt", "user2", "test_type")  # Different user
        assert result is None
        
        result = cache.get("test prompt", "user1", "different_type")  # Different type
        assert result is None
    
    @pytest.mark.slow
    def test_cache_expiry(self):
        """Test cache entry expiry."""
        cache = ResponseCache(ttl=1)  # 1 second TTL
        
        # Set an entry
        cache.set("test prompt", "test response", "user1", "test_type")
        
        # Should be available immediately
        result = cache.get("test prompt", "user1", "test_type")
        assert result == "test response"
        
        # Wait for expiry
        time.sleep(1.1)
        
        # Should be expired now
        result = cache.get("test prompt", "user1", "test_type")
        assert result is None
    
    def test_cache_disabled(self):
        """Test cache behavior when disabled."""
        with patch('ai.cache_manager.AI_CACHE_RESPONSES', False):
            cache = ResponseCache()
            
            # Set should not store anything
            cache.set("test prompt", "test response", "user1", "test_type")
            
            # Get should return None
            result = cache.get("test prompt", "user1", "test_type")
            assert result is None
    
    def test_cache_max_size_eviction(self):
        """Test cache eviction when max size is reached."""
        cache = ResponseCache(max_size=3, ttl=300)
        
        # Fill cache to max size
        cache.set("prompt1", "response1", "user1", "type1")
        cache.set("prompt2", "response2", "user1", "type2")
        cache.set("prompt3", "response3", "user1", "type3")
        
        # All should be available
        assert cache.get("prompt1", "user1", "type1") == "response1"
        assert cache.get("prompt2", "user1", "type2") == "response2"
        assert cache.get("prompt3", "user1", "type3") == "response3"
        
        # Add one more entry - should trigger eviction
        cache.set("prompt4", "response4", "user1", "type4")
        
        # One of the original entries should be evicted (LRU)
        # We can't predict which one, but at least one should be gone
        results = [
            cache.get("prompt1", "user1", "type1"),
            cache.get("prompt2", "user1", "type2"),
            cache.get("prompt3", "user1", "type3")
        ]
        
        # At least one should be None (evicted)
        assert None in results
    
    def test_cache_clear(self):
        """Test cache clearing."""
        cache = ResponseCache()
        
        # Add some entries
        cache.set("prompt1", "response1", "user1", "type1")
        cache.set("prompt2", "response2", "user1", "type2")
        
        # Clear cache
        cache.clear()
        
        # All entries should be gone
        assert cache.get("prompt1", "user1", "type1") is None
        assert cache.get("prompt2", "user1", "type2") is None
        assert len(cache.cache) == 0
        assert len(cache.access_times) == 0
    
    @pytest.mark.slow
    def test_cache_clear_expired(self):
        """Test clearing expired entries."""
        cache = ResponseCache(ttl=1)
        
        # Add entries with different timestamps
        cache.set("prompt1", "response1", "user1", "type1")
        time.sleep(0.5)
        cache.set("prompt2", "response2", "user1", "type2")
        time.sleep(0.6)  # Total 1.1 seconds, first entry should be expired
        
        # Clear expired entries
        cache.clear_expired()
        
        # First entry should be gone, second should remain
        assert cache.get("prompt1", "user1", "type1") is None
        assert cache.get("prompt2", "user1", "type2") == "response2"
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = ResponseCache(max_size=100, ttl=300)
        
        # Add some entries
        cache.set("prompt1", "response1", "user1", "type1")
        cache.set("prompt2", "response2", "user1", "type2")
        cache.set("prompt3", "response3", "user2", "type1")
        
        stats = cache.get_stats()
        
        assert stats["total_entries"] == 3
        assert stats["expired_entries"] == 0
        assert stats["active_entries"] == 3
        assert stats["max_size"] == 100
        assert stats["ttl_seconds"] == 300
        assert stats["prompt_type_counts"]["type1"] == 2
        assert stats["prompt_type_counts"]["type2"] == 1
    
    def test_get_entries_by_type(self):
        """Test getting entries by prompt type."""
        cache = ResponseCache()
        
        # Add entries with different types
        cache.set("prompt1", "response1", "user1", "type1")
        cache.set("prompt2", "response2", "user1", "type2")
        cache.set("prompt3", "response3", "user2", "type1")
        
        # Get entries by type
        type1_entries = cache.get_entries_by_type("type1")
        type2_entries = cache.get_entries_by_type("type2")
        type3_entries = cache.get_entries_by_type("type3")
        
        assert len(type1_entries) == 2
        assert len(type2_entries) == 1
        assert len(type3_entries) == 0
        
        # Check entry content
        assert any(entry.response == "response1" for entry in type1_entries.values())
        assert any(entry.response == "response3" for entry in type1_entries.values())
        assert any(entry.response == "response2" for entry in type2_entries.values())
    
    def test_remove_entries_by_type(self):
        """Test removing entries by prompt type."""
        cache = ResponseCache()
        
        # Add entries with different types
        cache.set("prompt1", "response1", "user1", "type1")
        cache.set("prompt2", "response2", "user1", "type2")
        cache.set("prompt3", "response3", "user2", "type1")
        
        # Remove entries by type
        removed_count = cache.remove_entries_by_type("type1")
        
        assert removed_count == 2
        
        # Check remaining entries
        assert cache.get("prompt1", "user1", "type1") is None
        assert cache.get("prompt2", "user1", "type2") == "response2"
        assert cache.get("prompt3", "user2", "type1") is None
    
    def test_remove_user_entries(self):
        """Test removing entries by user."""
        cache = ResponseCache()
        
        # Add entries for different users
        cache.set("prompt1", "response1", "user1", "type1")
        cache.set("prompt2", "response2", "user1", "type2")
        cache.set("prompt3", "response3", "user2", "type1")
        
        # Remove entries for user1
        removed_count = cache.remove_user_entries("user1")
        
        assert removed_count == 2
        
        # Check remaining entries
        assert cache.get("prompt1", "user1", "type1") is None
        assert cache.get("prompt2", "user1", "type2") is None
        assert cache.get("prompt3", "user2", "type1") == "response3"
    
    def test_cache_entry_metadata(self):
        """Test cache entry with metadata."""
        cache = ResponseCache()
        
        metadata = {"source": "test", "confidence": 0.95}
        cache.set("test prompt", "test response", "user1", "test_type", metadata)
        
        # Get the entry and check metadata
        key = cache._generate_key("test prompt", "user1", "test_type")
        entry = cache.cache[key]
        
        assert entry.metadata == metadata
        assert entry.response == "test response"
        assert entry.prompt_type == "test_type"
        assert entry.user_id == "user1"


class TestContextCache:
    """Test ContextCache functionality."""
    
    def test_context_cache_initialization(self):
        """Test context cache initialization."""
        cache = ContextCache()
        assert len(cache.cache) == 0
        assert cache.ttl == 300  # Default TTL from config
    
    def test_context_cache_initialization_custom_ttl(self):
        """Test context cache initialization with custom TTL."""
        cache = ContextCache(ttl=1800)
        assert cache.ttl == 1800
    
    def test_context_set_and_get(self):
        """Test basic context set and get operations."""
        cache = ContextCache(ttl=300)
        
        context = {"name": "John", "age": 30, "preferences": ["music", "books"]}
        cache.set("user1", context)
        
        result = cache.get("user1")
        assert result == context
    
    def test_context_cache_miss(self):
        """Test context cache miss scenarios."""
        cache = ContextCache()
        
        # Test getting non-existent context
        result = cache.get("non-existent-user")
        assert result is None
    
    @pytest.mark.slow
    def test_context_cache_expiry(self):
        """Test context cache expiry."""
        cache = ContextCache(ttl=1)  # 1 second TTL
        
        context = {"name": "John", "age": 30}
        cache.set("user1", context)
        
        # Should be available immediately
        result = cache.get("user1")
        assert result == context
        
        # Wait for expiry
        time.sleep(1.1)
        
        # Should be expired now
        result = cache.get("user1")
        assert result is None
    
    def test_context_cache_clear(self):
        """Test context cache clearing."""
        cache = ContextCache()
        
        # Add some contexts
        cache.set("user1", {"name": "John"})
        cache.set("user2", {"name": "Jane"})
        
        # Clear cache
        cache.clear()
        
        # All contexts should be gone
        assert cache.get("user1") is None
        assert cache.get("user2") is None
        assert len(cache.cache) == 0
    
    @pytest.mark.slow
    def test_context_cache_clear_expired(self):
        """Test clearing expired contexts."""
        cache = ContextCache(ttl=1)
        
        # Add contexts with different timestamps
        cache.set("user1", {"name": "John"})
        time.sleep(0.5)
        cache.set("user2", {"name": "Jane"})
        time.sleep(0.6)  # Total 1.1 seconds, first context should be expired
        
        # Clear expired contexts
        cache.clear_expired()
        
        # First context should be gone, second should remain
        assert cache.get("user1") is None
        assert cache.get("user2") == {"name": "Jane"}


class TestGlobalCacheInstances:
    """Test global cache instance functions."""
    
    def test_get_response_cache_singleton(self):
        """Test that get_response_cache returns a singleton."""
        cache1 = get_response_cache()
        cache2 = get_response_cache()
        
        assert cache1 is cache2
        assert isinstance(cache1, ResponseCache)
    
    def test_get_context_cache_singleton(self):
        """Test that get_context_cache returns a singleton."""
        cache1 = get_context_cache()
        cache2 = get_context_cache()
        
        assert cache1 is cache2
        assert isinstance(cache1, ContextCache)
    
    def test_global_cache_configuration(self):
        """Test global cache configuration."""
        import ai.cache_manager as cache_module
        
        # Store original cache instances for cleanup
        original_response_cache = getattr(cache_module, '_response_cache', None)
        original_context_cache = getattr(cache_module, '_context_cache', None)
        
        try:
            with patch('ai.cache_manager.AI_RESPONSE_CACHE_TTL', 600):
                with patch('ai.cache_manager.CONTEXT_CACHE_TTL', 1800):
                    # Reset global instances
                    cache_module._response_cache = None
                    cache_module._context_cache = None
                    
                    response_cache = get_response_cache()
                    context_cache = get_context_cache()
                    
                    assert response_cache.ttl == 600
                    assert context_cache.ttl == 1800
        finally:
            # Restore original cache instances to prevent state pollution
            cache_module._response_cache = original_response_cache
            cache_module._context_cache = original_context_cache


class TestCacheEntry:
    """Test CacheEntry dataclass."""
    
    def test_cache_entry_creation(self):
        """Test CacheEntry creation with required fields."""
        entry = CacheEntry(
            response="test response",
            timestamp=1234567890.0,
            prompt_type="test_type"
        )
        
        assert entry.response == "test response"
        assert entry.timestamp == 1234567890.0
        assert entry.prompt_type == "test_type"
        assert entry.user_id is None
        assert entry.metadata == {}
    
    def test_cache_entry_creation_with_optional_fields(self):
        """Test CacheEntry creation with optional fields."""
        metadata = {"source": "test", "confidence": 0.95}
        entry = CacheEntry(
            response="test response",
            timestamp=1234567890.0,
            prompt_type="test_type",
            user_id="user1",
            metadata=metadata
        )
        
        assert entry.response == "test response"
        assert entry.timestamp == 1234567890.0
        assert entry.prompt_type == "test_type"
        assert entry.user_id == "user1"
        assert entry.metadata == metadata


class TestCacheThreadSafety:
    """Test cache thread safety."""
    
    def test_concurrent_access(self):
        """Test concurrent access to cache."""
        import threading
        
        cache = ResponseCache(max_size=100, ttl=300)
        results = []
        
        def worker(worker_id):
            for i in range(10):
                prompt = f"prompt_{worker_id}_{i}"
                response = f"response_{worker_id}_{i}"
                cache.set(prompt, response, f"user_{worker_id}", "test_type")
                result = cache.get(prompt, f"user_{worker_id}", "test_type")
                results.append(result)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All results should be successful
        assert len(results) == 50
        assert all(result is not None for result in results)
    
    def test_concurrent_context_access(self):
        """Test concurrent access to context cache."""
        import threading
        
        cache = ContextCache(ttl=300)
        results = []
        
        def worker(worker_id):
            for i in range(10):
                user_id = f"user_{worker_id}_{i}"
                context = {"worker": worker_id, "iteration": i}
                cache.set(user_id, context)
                result = cache.get(user_id)
                results.append(result)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All results should be successful
        assert len(results) == 50
        assert all(result is not None for result in results)
