"""Dependency-free validation for canonical MHM user identifiers."""


# ERROR_HANDLING_EXCLUDE: pure predicate with no I/O or exceptional operations.
def is_valid_user_id(user_id: str | None) -> bool:
    """Return whether *user_id* is safe for use as one filesystem path segment."""
    if not isinstance(user_id, str):
        return False
    if not user_id.strip() or len(user_id) > 100:
        return False
    return user_id.replace("_", "").replace("-", "").isalnum()
