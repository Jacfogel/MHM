"""Focused tests for shared user-index lookup keys."""

from types import SimpleNamespace
from typing import cast

import pytest

import core.error_handling as error_handling
import core.file_locking as file_locking
import core.user_management as user_management
import storage.user_data_index as user_data_index
from core.user_management import generate_internal_alias
from storage.user_data_index import _index_entries_for_account


@pytest.mark.unit
@pytest.mark.storage
class TestIndexEntriesForAccount:
    def test_generated_internal_alias_is_opaque_and_legacy_compatible(self):
        alias = generate_internal_alias("12345678-1234-5678-9abc-def012345678")
        assert alias == "mhm_12345678123456789abcdef01234"
        assert len(alias) == 32

    def test_generated_internal_alias_reports_invalid_identifier(
        self, monkeypatch
    ):
        class InvalidIdentifier:
            def __str__(self) -> str:
                raise RuntimeError("cannot stringify identifier")

        handled_errors = []
        monkeypatch.setattr(
            error_handling.error_handler,
            "handle_error",
            lambda *args, **kwargs: handled_errors.append((args, kwargs)) or False,
        )
        with pytest.raises(RuntimeError, match="cannot stringify identifier"):
            generate_internal_alias(cast(str, InvalidIdentifier()))

        assert handled_errors

    def test_generated_internal_alias_uses_unique_fallback_for_empty_identifier(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            user_management.uuid,
            "uuid4",
            lambda: SimpleNamespace(hex="f" * 32),
        )

        assert generate_internal_alias("") == f"mhm_{'f' * 28}"

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
            "user-1": "user-1",
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
            "user-1": "user-1",
            "email:a@b.com": "user-1",
            "discord:123": "user-1",
            "phone:555": "user-1",
        }

    def test_empty_account_still_indexes_canonical_user_id(self):
        assert _index_entries_for_account("user-1", {}) == {"user-1": "user-1"}
        assert _index_entries_for_account("user-1", None) == {"user-1": "user-1"}

    def test_update_succeeds_without_internal_username(self, monkeypatch):
        saved = {}
        monkeypatch.setattr(
            user_data_index,
            "get_user_data",
            lambda user_id, file_type: {
                "account": {"email": "person@example.com", "account_status": "active"}
            },
        )
        monkeypatch.setattr(file_locking, "safe_json_read", lambda *args, **kwargs: {})

        def save(_path, value, indent=4):
            saved.update(value)
            return True

        monkeypatch.setattr(file_locking, "safe_json_write", save)
        assert user_data_index.update_user_index("user-1", index_file="unused.json")
        assert saved["user-1"] == "user-1"
        assert saved["email:person@example.com"] == "user-1"
