"""
Scenario-style coverage for storage.user_data_read (get/load paths, ID repair).

Targets the core domain coverage gap around user data loading and validation.
"""

from __future__ import annotations

import json
import os
import uuid

import pytest

from core.file_operations import load_json_data
from core import clear_user_caches, get_user_data
from storage.user_data_operations import update_user_index
from storage.user_data_read import (
    ensure_unique_ids,
    get_user_data_with_metadata,
    load_and_ensure_ids,
)


@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.fast
class TestEnsureUniqueIds:
    """Pure transformations for message ID repair."""

    def test_ensure_unique_ids_passthrough_when_no_messages(self):
        assert ensure_unique_ids(None) is None
        assert ensure_unique_ids({}) == {}
        assert ensure_unique_ids({"other": []}) == {"other": []}

    def test_ensure_unique_ids_repairs_duplicates_and_missing(self):
        _body = "body"
        data = {
            "messages": [
                {"id": "dup", _body: "a"},
                {"id": "dup", _body: "b"},
                {_body: "no id yet"},
            ]
        }
        out = ensure_unique_ids(data)
        assert out is data
        ids = [m["id"] for m in out["messages"]]
        assert len(ids) == len(set(ids))
        assert ids[0] == "dup"
        for mid in ids[1:]:
            assert len(mid) >= 32


@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.fast
class TestGetUserDataFieldsPolicy:
    """Field-filtered get_user_data must not be expanded by test-only assembly."""

    def test_get_user_data_fields_not_backfilled_when_loader_empty(
        self, mock_user_data, monkeypatch
    ):
        """Field-filtered reads must not gain full preferences from test healing/shim."""
        import storage.user_data_registry as reg

        uid = mock_user_data["user_id"]
        clear_user_caches(uid)

        def _empty_preferences(_user_id: str, auto_create: bool = True):
            return None

        monkeypatch.setitem(
            reg.USER_DATA_LOADERS["preferences"],
            "loader",
            _empty_preferences,
        )
        clear_user_caches(uid)
        result = get_user_data(uid, "preferences", fields="channel")
        assert result == {}


@pytest.mark.integration
@pytest.mark.storage
class TestGetUserDataReadPath:
    """File-backed get_user_data scenarios."""

    def test_get_user_data_rejects_invalid_user_ids(self, mock_config):
        assert get_user_data("", "preferences") == {}
        assert get_user_data("   ", "preferences") == {}
        assert get_user_data("x" * 101, "preferences") == {}
        assert get_user_data(None, "preferences") == {}  # type: ignore[arg-type]

    def test_get_user_data_rejects_unknown_data_types(self, mock_user_data):
        uid = mock_user_data["user_id"]
        assert get_user_data(uid, ["preferences", "__invalid_type__"]) == {}

    def test_get_user_data_returns_empty_for_unknown_user_auto_create_off(
        self, mock_config
    ):
        uid = f"ghost-user-{uuid.uuid4().hex}"
        assert get_user_data(uid, "preferences", auto_create=False) == {}

    def test_get_user_data_fields_scalar_list_and_dict(self, mock_user_data):
        uid = mock_user_data["user_id"]
        prefs_path = os.path.join(mock_user_data["user_dir"], "preferences.json")
        assert os.path.isfile(prefs_path), "preferences.json must exist for field-filter reads"
        update_user_index(uid)
        clear_user_caches(uid)

        on_disk = load_json_data(prefs_path)
        assert isinstance(on_disk, dict) and on_disk.get("channel") == {"type": "email"}

        # Loaders return the on-disk preferences dict (channel, task_settings, ...).
        scalar = get_user_data(uid, "preferences", fields="channel")
        assert "preferences" in scalar, (
            f"field-filtered preferences read missing key; got {scalar!r}"
        )
        assert scalar["preferences"] == {"type": "email"}

        listed = get_user_data(
            uid, "preferences", fields=["channel", "task_settings"]
        )
        assert set(listed["preferences"].keys()) == {"channel", "task_settings"}

        mapped = get_user_data(
            uid, "preferences", fields={"preferences": ["channel"]}
        )
        assert mapped["preferences"] == {"channel": {"type": "email"}}

    def test_get_user_data_with_metadata_attaches_file_info(self, mock_user_data):
        uid = mock_user_data["user_id"]
        result = get_user_data_with_metadata(uid, "account")
        account = result.get("account")
        assert isinstance(account, dict)
        meta = account.get("_metadata")
        assert isinstance(meta, dict)
        assert meta.get("data_type") == "account"
        assert "file_path" in meta and os.path.isfile(meta["file_path"])

    def test_get_user_data_normalize_on_read_sets_default_timezone(
        self, mock_user_data
    ):
        uid = mock_user_data["user_id"]
        acc_path = os.path.join(mock_user_data["user_dir"], "account.json")
        with open(acc_path, encoding="utf-8") as fh:
            raw = json.load(fh)
        raw.pop("timezone", None)
        with open(acc_path, "w", encoding="utf-8") as fh:
            json.dump(raw, fh)
        clear_user_caches(uid)

        result = get_user_data(
            uid, "account", normalize_on_read=True, auto_create=True
        )
        account = result.get("account")
        assert isinstance(account, dict)
        assert account.get("timezone") == "UTC"


@pytest.mark.integration
@pytest.mark.storage
@pytest.mark.messages
class TestLoadAndEnsureIds:
    """End-to-end repair of category message files."""

    def test_load_and_ensure_ids_fixes_duplicate_template_ids(
        self, mock_user_data_with_messages
    ):
        info = mock_user_data_with_messages
        uid = info["user_id"]
        assert update_user_index(uid)

        msg_path = os.path.join(info["user_dir"], "messages", "motivational.json")
        _body = "body"
        payload = {
            "messages": [
                {"id": "duplicate-id", _body: "first"},
                {"id": "duplicate-id", _body: "second"},
                {_body: "third"},
            ]
        }
        with open(msg_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)

        load_and_ensure_ids(uid)

        reloaded = load_json_data(msg_path)
        assert reloaded and "messages" in reloaded
        ids = [m.get("id") for m in reloaded["messages"]]
        assert all(ids)
        assert len(ids) == len(set(ids))
