"""Focused tests for shared user-index lookup keys."""

import pytest

from storage.user_data_index import _index_entries_for_account


@pytest.mark.unit
@pytest.mark.storage
class TestIndexEntriesForAccount:
    def test_includes_username_and_contact_keys(self):
        entries = _index_entries_for_account(
            "user-1",
            {
                "internal_username": "julie",
                "email": "a@b.com",
                "discord_user_id": "123",
                "phone": "555",
            },
        )
        assert entries == {
            "julie": "user-1",
            "email:a@b.com": "user-1",
            "discord:123": "user-1",
            "phone:555": "user-1",
        }

    def test_contact_keys_exist_without_username(self):
        entries = _index_entries_for_account(
            "user-1",
            {"email": "a@b.com", "discord_user_id": "123", "phone": "555"},
        )
        assert entries == {
            "email:a@b.com": "user-1",
            "discord:123": "user-1",
            "phone:555": "user-1",
        }

    def test_empty_account_returns_no_keys(self):
        assert _index_entries_for_account("user-1", {}) == {}
        assert _index_entries_for_account("user-1", None) == {}
