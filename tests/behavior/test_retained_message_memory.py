"""Isolated repeated-message state workload; no provider or user-file access."""

import gc
import tracemalloc

import psutil
import pytest

from ai.client.cache_manager import ContextCache
from user.context_manager import UserContextManager


@pytest.mark.behavior
@pytest.mark.ai
def test_repeated_message_retention(monkeypatch):
    """Record RSS and live Python bytes through warm, churn, and expiry phases."""
    clock = [1000.0]
    monkeypatch.setattr("ai.client.cache_manager.time.time", lambda: clock[0])
    import user.context_manager as context_module
    import types
    monkeypatch.setattr(context_module, "time", types.SimpleNamespace(monotonic=lambda: clock[0]), raising=False)
    cache = ContextCache(ttl=300)
    manager = UserContextManager()
    process = psutil.Process()
    tracemalloc.start()
    samples = []

    def sample(phase):
        gc.collect()
        live, _ = tracemalloc.get_traced_memory()
        samples.append((phase, live, process.memory_info().rss))

    try:
        sample("before")
        for batch in range(2):
            for index in range(batch * 1000, (batch + 1) * 1000):
                uid = f"memory-user-{index}"
                for turn in range(4):
                    text = f"{uid}-{turn}:" + "x" * 2048
                    manager.add_conversation_exchange(uid, text, text + "reply")
                    cache.set(uid, {"message": text + "context"})
            sample(f"batch-{batch+1}")
        print("MEMORY containers", len(cache.cache), len(manager.conversation_history))
        clock[0] += 7200
        # Maintenance is the same explicit sweep used for cache lifecycle checks.
        cache.clear_expired()
        if hasattr(manager, "clear_expired"):
            manager.clear_expired()
        sample("idle-expiry")
        for phase, live, rss in samples:
            print(f"MEMORY {phase}: python_bytes={live} rss_bytes={rss}")
        if hasattr(cache, "max_size"):
            assert len(cache.cache) <= cache.max_size
            assert not manager.conversation_history
            assert samples[-1][1] < samples[2][1] / 3
    finally:
        tracemalloc.stop()


@pytest.mark.unit
@pytest.mark.ai
def test_context_eviction_and_session_expiry_preserve_isolation(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr("ai.client.cache_manager.time.time", lambda: clock[0])
    import user.context_manager as context_module
    import types
    monkeypatch.setattr(context_module, "time", types.SimpleNamespace(monotonic=lambda: clock[0]))
    cache = ContextCache(ttl=10, max_size=2)
    cache.set("a", {"setting": "old"})
    cache.set("b", {"setting": "b"})
    assert cache.get("a") == {"setting": "old"}
    cache.set("c", {"setting": "c"})
    assert cache.get("b") is None
    cache.set("a", {"setting": "new"})
    assert cache.get("a") == {"setting": "new"}
    clock[0] += 11
    cache.set("d", {"setting": "d"})
    assert set(cache.cache) == {"d"}
    manager = UserContextManager(max_users=2, session_ttl=10)
    manager.add_conversation_exchange("a", "private-a", "reply-a")
    clock[0] += 1
    manager.add_conversation_exchange("b", "private-b", "reply-b")
    clock[0] += 1
    assert manager.get_session_conversation_history("a")[0]["user_message"] == "private-a"
    manager.add_conversation_exchange("c", "private-c", "reply-c")
    assert not manager.get_session_conversation_history("b")
    assert manager.get_session_conversation_history("c")[0]["user_message"] == "private-c"
    clock[0] += 11
    assert not manager.get_session_conversation_history("a")
    assert not manager.conversation_history
