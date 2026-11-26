"""User-scoped cleanup of initialized AI state at account lifecycle boundaries."""

from core.error_handling import handle_errors


@handle_errors("clearing user AI runtime state", default_return=False)
def clear_user_ai_state(user_id: str) -> bool:
    """Forget runtime AI data without creating unused cache/history instances."""
    from ai.client import cache_manager
    from ai.context import history
    from user.context_manager import user_context_manager

    if not user_id:
        return False
    results = [user_context_manager.clear_user(user_id)]
    if cache_manager._response_cache is not None:
        results.append(cache_manager._response_cache.remove_user_entries(user_id) is not None)
    if cache_manager._context_cache is not None:
        results.append(cache_manager._context_cache.remove_user_entries(user_id))
    if history._conversation_history is not None:
        results.append(history._conversation_history.clear_history(user_id))
    return all(results)
