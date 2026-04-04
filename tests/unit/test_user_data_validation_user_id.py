"""Unit tests for core.user_data_validation.is_valid_user_id."""

import pytest

from core.user_data_validation import is_valid_user_id


@pytest.mark.unit
class TestIsValidUserId:
    def test_accepts_uuid_like_and_simple_ids(self):
        assert is_valid_user_id("550e8400-e29b-41d4-a716-446655440000") is True
        assert is_valid_user_id("user_123-test") is True
        assert is_valid_user_id("a") is True
        assert is_valid_user_id("a" * 100) is True

    def test_rejects_none_wrong_type_empty(self):
        assert is_valid_user_id(None) is False
        assert is_valid_user_id(123) is False  # type: ignore[arg-type]
        assert is_valid_user_id("") is False
        assert is_valid_user_id("   ") is False

    def test_rejects_too_long(self):
        assert is_valid_user_id("a" * 101) is False

    def test_rejects_unsafe_or_odd_characters(self):
        for bad in (
            "user@host",
            "user 1",
            "user.name",
            "../x",
            "user#1",
        ):
            assert is_valid_user_id(bad) is False, bad
