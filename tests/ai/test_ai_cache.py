"""Cache contracts use distinct seeded payloads, never stochastic reply equality."""

from unittest.mock import patch

from ai.client.cache_manager import ResponseCache
from tests.ai.ai_test_base import AITestBase


class TestAICache(AITestBase):
    __test__ = False

    def _cache_result(self, test_id, name, checks, evidence):
        failures = [label for label, passed in checks.items() if not passed]
        self.log_test(
            test_id, name, "FAIL" if failures else "PASS",
            notes="All cache assertions passed" if not failures else " | ".join(failures),
            metrics={"assertions": checks, "evidence": evidence},
            test_type="cache_contract",
            turns=[{"prompt": "seeded cache fixture", "response": evidence,
                    "source": "cache_fixture", "events": [], "error": None}],
        )

    def test_cache_basic(self):
        cache = ResponseCache(max_size=10, ttl=300)
        with patch("ai.client.cache_manager.AI_CACHE_RESPONSES", True):
            cache.set("same prompt", "fixture-user-A: buy milk", "user-A", "command")
            actual = cache.get("same prompt", "user-A", "command")
        self._cache_result("T-1.5", "Cache stores and retrieves payload", {
            "exact payload retrieved": actual == "fixture-user-A: buy milk",
            "one entry stored": cache.get_stats()["total_entries"] == 1,
        }, {"retrieved": actual})

    def test_cache_comprehensive(self):
        cache = ResponseCache(max_size=10, ttl=300)
        prompt = "same prompt"
        with patch("ai.client.cache_manager.AI_CACHE_RESPONSES", True):
            cache.set(prompt, "user-A private payload", "user-A", "command")
            cache.set(prompt, "user-B different payload", "user-B", "command")
            first = cache.get(prompt, "user-A", "command")
            second = cache.get(prompt, "user-B", "command")
            missing = cache.get(prompt, "user-C", "command")
            self._cache_result("T-11.1", "Cache isolation by user", {
                "user A retrieves only A": first == "user-A private payload",
                "user B retrieves only B": second == "user-B different payload",
                "unseeded user misses": missing is None,
                "distinct user keys": cache._generate_key(prompt, "user-A", "command")
                != cache._generate_key(prompt, "user-B", "command"),
            }, {"user_A": first, "user_B": second, "user_C": missing})

            cache.set(prompt, "contextual payload", "user-A", "contextual")
            contextual = cache.get(prompt, "user-A", "contextual")
            command = cache.get(prompt, "user-A", "command")
            self._cache_result("T-11.2", "Cache isolation by mode", {
                "contextual retrieves contextual": contextual == "contextual payload",
                "command retains command": command == "user-A private payload",
                "unseeded mode misses": cache.get(prompt, "user-A", "other") is None,
            }, {"contextual": contextual, "command": command})

            # Advance only the entry's age; no sleeps or global clock changes.
            key = cache._generate_key(prompt, "user-A", "contextual")
            cache.cache[key].timestamp -= cache.ttl + 1
            expired = cache.get(prompt, "user-A", "contextual")
            self._cache_result("T-11.3", "Cache TTL expiry", {
                "expired payload not returned": expired is None,
                "other mode remains available": cache.get(prompt, "user-A", "command")
                == "user-A private payload",
            }, {"expired": expired})
