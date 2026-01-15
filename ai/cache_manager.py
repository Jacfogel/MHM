# cache_manager.py

import hashlib
import threading
import time
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass, field

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.config import AI_CACHE_RESPONSES, CONTEXT_CACHE_TTL, AI_RESPONSE_CACHE_TTL

# Route cache manager logs to AI component
cache_logger = get_component_logger("ai_cache")
logger = cache_logger


@dataclass
class CacheEntry:
    """Entry in the response cache"""

    response: str
    timestamp: float
    prompt_type: str
    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ResponseCache:
    """Simple in-memory cache for AI responses to avoid repeated calculations"""

    @handle_errors("initializing response cache", default_return=None)
    def __init__(self, max_size: int = 100, ttl: int = 300):
        """Initialize the response cache"""
        self.cache: dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.ttl = ttl
        self.access_times: dict[str, float] = {}
        self._lock = threading.Lock()

    @handle_errors("generating cache key")
    def _generate_key(
        self, prompt: str, user_id: str | None = None, prompt_type: str = "default"
    ) -> str:
        """Generate cache key from prompt, user context, and prompt type"""
        base_string = f"{user_id or 'anonymous'}:{prompt_type}:{prompt}"  # Hash the full prompt to avoid collisions
        return hashlib.md5(base_string.encode()).hexdigest()

    @handle_errors("getting cached response", default_return=None)
    def get(
        self, prompt: str, user_id: str | None = None, prompt_type: str = "default"
    ) -> str | None:
        """Get cached response if available and not expired"""
        if not AI_CACHE_RESPONSES:
            return None

        key = self._generate_key(prompt, user_id, prompt_type)
        current_time = time.time()

        with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                if current_time - entry.timestamp < self.ttl:
                    self.access_times[key] = current_time
                    logger.debug(
                        f"Cache hit for prompt type '{prompt_type}': {prompt[:50]}..."
                    )
                    return entry.response
                else:
                    # Expired, remove
                    self._remove_entry(key)

        return None

    @handle_errors("setting cached response")
    def set(
        self,
        prompt: str,
        response: str,
        user_id: str | None = None,
        prompt_type: str = "default",
        metadata: dict[str, Any] = None,
    ):
        """Cache a response"""
        if not AI_CACHE_RESPONSES:
            return

        key = self._generate_key(prompt, user_id, prompt_type)
        current_time = time.time()

        with self._lock:
            # Clean up if cache is full
            if len(self.cache) >= self.max_size:
                self._cleanup_lru()

            entry = CacheEntry(
                response=response,
                timestamp=current_time,
                prompt_type=prompt_type,
                user_id=user_id,
                metadata=metadata,
            )

            self.cache[key] = entry
            self.access_times[key] = current_time

            logger.debug(
                f"Cached response for prompt type '{prompt_type}': {prompt[:50]}..."
            )

    @handle_errors("removing cache entry")
    def _remove_entry(self, key: str):
        """Remove an entry from the cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_times:
            del self.access_times[key]

    @handle_errors("cleaning up LRU cache")
    def _cleanup_lru(self):
        """Remove least recently used items"""
        if not self.access_times:
            return

        items_to_remove = max(1, len(self.cache) // 5)
        sorted_items = sorted(self.access_times.items(), key=lambda x: x[1])

        for key, _ in sorted_items[:items_to_remove]:
            self._remove_entry(key)

        logger.debug(f"Cleaned up {items_to_remove} LRU cache entries")

    @handle_errors("clearing cache")
    def clear(self):
        """Clear all cached responses"""
        with self._lock:
            self.cache.clear()
            self.access_times.clear()
        logger.info("Response cache cleared")

    @handle_errors("clearing expired entries")
    def clear_expired(self):
        """Remove all expired entries from the cache"""
        current_time = time.time()
        expired_keys = []

        with self._lock:
            for key, entry in self.cache.items():
                if current_time - entry.timestamp >= self.ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                self._remove_entry(key)

        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")

    @handle_errors("getting cache statistics")
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            current_time = time.time()
            total_entries = len(self.cache)
            expired_entries = sum(
                1
                for entry in self.cache.values()
                if current_time - entry.timestamp >= self.ttl
            )

            # Count entries by prompt type
            prompt_type_counts = {}
            for entry in self.cache.values():
                prompt_type = entry.prompt_type
                prompt_type_counts[prompt_type] = (
                    prompt_type_counts.get(prompt_type, 0) + 1
                )

            return {
                "total_entries": total_entries,
                "expired_entries": expired_entries,
                "active_entries": total_entries - expired_entries,
                "max_size": self.max_size,
                "ttl_seconds": self.ttl,
                "prompt_type_counts": prompt_type_counts,
                "cache_enabled": AI_CACHE_RESPONSES,
            }

    @handle_errors("getting cache entries by type")
    def get_entries_by_type(self, prompt_type: str) -> dict[str, CacheEntry]:
        """Get all cache entries for a specific prompt type"""
        with self._lock:
            return {
                key: entry
                for key, entry in self.cache.items()
                if entry.prompt_type == prompt_type
            }

    @handle_errors("removing cache entries by type")
    def remove_entries_by_type(self, prompt_type: str) -> int:
        """Remove all cache entries for a specific prompt type"""
        keys_to_remove = []

        with self._lock:
            for key, entry in self.cache.items():
                if entry.prompt_type == prompt_type:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                self._remove_entry(key)

        logger.info(
            f"Removed {len(keys_to_remove)} cache entries for prompt type '{prompt_type}'"
        )
        return len(keys_to_remove)

    @handle_errors("removing user cache entries")
    def remove_user_entries(self, user_id: str) -> int:
        """Remove all cache entries for a specific user"""
        keys_to_remove = []

        with self._lock:
            for key, entry in self.cache.items():
                if entry.user_id == user_id:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                self._remove_entry(key)

        logger.info(f"Removed {len(keys_to_remove)} cache entries for user '{user_id}'")
        return len(keys_to_remove)


class ContextCache:
    """Cache for user context information"""

    @handle_errors("initializing context cache", default_return=None)
    def __init__(self, ttl: int = None):
        """Initialize the context cache"""
        self.cache: dict[str, tuple[dict[str, Any], float]] = {}
        self.ttl = ttl or CONTEXT_CACHE_TTL
        self._lock = threading.Lock()

    @handle_errors("getting cached context", default_return=None)
    def get(self, user_id: str) -> dict[str, Any] | None:
        """Get cached context for a user"""
        current_time = time.time()

        with self._lock:
            if user_id in self.cache:
                context, timestamp = self.cache[user_id]
                if current_time - timestamp < self.ttl:
                    return context
                else:
                    # Expired, remove
                    del self.cache[user_id]

        return None

    @handle_errors("setting cached context")
    def set(self, user_id: str, context: dict[str, Any]):
        """Cache context for a user"""
        current_time = time.time()

        with self._lock:
            self.cache[user_id] = (context, current_time)

    @handle_errors("clearing context cache")
    def clear(self):
        """Clear all cached contexts"""
        with self._lock:
            self.cache.clear()

    @handle_errors("clearing expired context cache")
    def clear_expired(self):
        """Remove all expired contexts"""
        current_time = time.time()
        expired_keys = []

        with self._lock:
            for user_id, (context, timestamp) in self.cache.items():
                if current_time - timestamp >= self.ttl:
                    expired_keys.append(user_id)

            for user_id in expired_keys:
                del self.cache[user_id]


# Global cache instances
_response_cache = None
_context_cache = None


@handle_errors("getting response cache instance")
def get_response_cache() -> ResponseCache:
    """Get the global response cache instance"""
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache(ttl=AI_RESPONSE_CACHE_TTL)
    return _response_cache


@handle_errors("getting context cache instance")
def get_context_cache() -> ContextCache:
    """Get the global context cache instance"""
    global _context_cache
    if _context_cache is None:
        _context_cache = ContextCache()
    return _context_cache
