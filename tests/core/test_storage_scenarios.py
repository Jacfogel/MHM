"""
Scenario-style coverage for storage.user_data_read, user_data_write, and user_data_operations.

Targets read normalization, write merge/validation paths, module-level wrappers, and analytics.
"""

from __future__ import annotations

import json
import os
import uuid
from unittest.mock import patch

import pytest

from core.file_operations import load_json_data, save_json_data
from core.time_utilities import now_timestamp_full
from storage.user_data_operations import (
    UserDataManager,
    backup_user_data,
    build_user_index,
    delete_user_completely,
    export_user_data,
    get_user_analytics_summary,
    get_user_data_summary,
    get_user_summary,
    update_message_references,
    update_user_index,
)
from storage.user_data_read import (
    clear_user_caches,
    ensure_unique_ids,
    get_user_data,
    load_and_ensure_ids,
)
from storage.user_data_v2_base import SCHEMA_VERSION
from storage.user_data_write import save_user_data, save_user_data_transaction
from tests.test_helpers.test_utilities import TestUserFactory


@pytest.mark.unit
@pytest.mark.storage
class TestUserDataReadEdgePaths:
    """Early returns and normalization branches in user_data_read."""

    def test_ensure_unique_ids_skips_non_dict_messages(self):
        data = {"messages": [{"id": "a", "body": "ok"}, "not-a-dict", {"body": "new"}]}
        out = ensure_unique_ids(data)
        assert out is data
        ids = [m["id"] for m in out["messages"] if isinstance(m, dict)]
        assert len(ids) == len(set(ids))

    def test_load_and_ensure_ids_no_categories_is_noop(self, mock_user_data):
        uid = mock_user_data["user_id"]
        clear_user_caches(uid)
        load_and_ensure_ids(uid)

    def test_load_and_ensure_ids_missing_preferences_returns_early(self, mock_config):
        uid = f"ghost-{uuid.uuid4().hex}"
        load_and_ensure_ids(uid)

    def test_normalize_on_read_preferences_merges_categories(self, mock_user_data):
        uid = mock_user_data["user_id"]
        prefs_path = os.path.join(mock_user_data["user_dir"], "preferences.json")
        raw = load_json_data(prefs_path)
        assert isinstance(raw, dict)
        raw["categories"] = ["motivational", "custom_cat"]
        save_json_data(raw, prefs_path)
        clear_user_caches(uid)

        result = get_user_data(uid, "preferences", normalize_on_read=True)
        prefs = result.get("preferences")
        assert isinstance(prefs, dict)
        assert "custom_cat" in prefs.get("categories", [])


@pytest.mark.integration
@pytest.mark.storage
class TestUserDataWriteScenarios:
    """Save pipeline merge, validation, and transaction paths."""

    def test_save_user_data_rejects_invalid_inputs(self):
        assert save_user_data("", {"account": {}}) == {}
        assert save_user_data("valid-user", None) == {}
        assert save_user_data("valid-user", {"__bad_type__": {}}) == {
            "__bad_type__": False
        }

    def test_save_user_data_merge_pops_none_values(self, test_data_dir):
        user_id = f"merge-none-{uuid.uuid4().hex[:8]}"
        assert TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        result = save_user_data(
            user_id,
            {"account": {"timezone": None, "internal_username": user_id}},
        )
        assert result.get("account") is True
        account = get_user_data(user_id, "account").get("account", {})
        assert "timezone" not in account or account.get("timezone") is not None

    def test_save_user_data_merges_feature_dict_updates(self, test_data_dir):
        user_id = f"merge-features-{uuid.uuid4().hex[:8]}"
        assert TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        result = save_user_data(
            user_id,
            {"account": {"features": {"checkins": "enabled"}}},
        )
        assert result.get("account") is True
        account = get_user_data(user_id, "account").get("account", {})
        feats = account.get("features", {})
        assert feats.get("checkins") == "enabled"

    @pytest.mark.no_parallel  # shared session tests/data dir races under xdist
    def test_save_user_data_cross_file_invariant_enables_messages(
        self, test_data_dir, mock_config
    ):
        user_id = f"cross-file-{uuid.uuid4().hex}"
        assert TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        clear_user_caches(user_id)
        save_user_data(
            user_id,
            {
                "account": {
                    "internal_username": user_id,
                    "features": {"automated_messages": "disabled"},
                }
            },
        )
        clear_user_caches(user_id)
        result = save_user_data(
            user_id,
            {"preferences": {"categories": ["motivational"]}},
        )
        assert result.get("preferences") is True
        clear_user_caches(user_id)
        account = get_user_data(user_id, "account").get("account", {})
        assert account.get("features", {}).get("automated_messages") == "enabled"

    @pytest.mark.no_parallel  # shared session tests/data dir races under xdist
    def test_save_and_read_schedules_with_normalize_on_read(
        self, mock_user_data_with_messages
    ):
        uid = mock_user_data_with_messages["user_id"]
        clear_user_caches(uid)
        result = save_user_data(
            uid,
            {
                "schedules": {
                    "motivational": {
                        "Morning": {"start": "08:00", "end": "12:00", "days": ["ALL"]}
                    }
                }
            },
        )
        assert result.get("schedules") is True
        loaded = get_user_data(uid, "schedules", normalize_on_read=True)
        schedules = loaded.get("schedules")
        assert isinstance(schedules, dict)
        assert "motivational" in schedules

    def test_save_user_data_transaction_index_failure_returns_false(
        self, test_data_dir
    ):
        user_id = f"txn-fail-{uuid.uuid4().hex[:8]}"
        assert TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        with patch(
            "storage.user_data_operations.update_user_index",
            side_effect=RuntimeError("index unavailable"),
        ):
            ok = save_user_data_transaction(
                user_id,
                {"account": {"timezone": "UTC"}},
                auto_create=True,
            )
        assert ok is False


@pytest.mark.unit
@pytest.mark.storage
class TestUserDataOperationsWrappers:
    """Module-level API validation and analytics helpers."""

    def test_module_wrappers_reject_invalid_inputs(self):
        assert backup_user_data(None) == ""
        assert backup_user_data("user", include_messages="yes") == ""
        assert export_user_data("", "json") == {}
        assert export_user_data("user", "xml") == {}
        assert delete_user_completely(None) is False
        assert delete_user_completely("user", create_backup="yes") is False
        assert get_user_data_summary("   ") == {"error": "Empty user_id provided"}
        assert update_user_index(None) is False

    def test_update_message_references_module_handles_manager_failure(self):
        with patch.object(
            UserDataManager,
            "update_message_references",
            side_effect=RuntimeError("manager error"),
        ):
            assert update_message_references("some-user") is False

    def test_get_user_message_files_fallback_builds_from_categories(
        self, mock_user_data_with_messages
    ):
        uid = mock_user_data_with_messages["user_id"]
        manager = UserDataManager()
        with patch(
            "storage.user_data_operations.get_user_info_for_data_manager",
            return_value={
                "user_id": uid,
                "internal_username": "test",
                "message_files": {},
            },
        ):
            files = manager.get_user_message_files(uid)
        assert isinstance(files, dict)

    def test_get_user_summary_counts_v2_message_templates(
        self, mock_user_data_with_messages
    ):
        info = mock_user_data_with_messages
        uid = info["user_id"]
        msg_path = os.path.join(info["user_dir"], "messages", "motivational.json")
        ts = now_timestamp_full()
        payload = {
            "schema_version": SCHEMA_VERSION,
            "category": "motivational",
            "updated_at": ts,
            "messages": [
                {
                    "id": "msg-1",
                    "kind": "message",
                    "text": "Hello",
                    "category": "motivational",
                    "active": True,
                    "schedule": {"days": ["ALL"], "periods": ["ALL"]},
                    "created_at": ts,
                    "updated_at": ts,
                }
            ],
        }
        with open(msg_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)

        summary = get_user_summary(uid)
        assert summary.get("user_id") == uid
        assert summary.get("total_messages", 0) >= 1
        assert summary.get("message_stats", {}).get("motivational", 0) >= 1

    def test_get_user_summary_skips_legacy_message_template_format(
        self, mock_user_data_with_messages
    ):
        info = mock_user_data_with_messages
        uid = info["user_id"]
        legacy_path = os.path.join(info["user_dir"], "messages", "health.json")
        with open(legacy_path, "w", encoding="utf-8") as fh:
            json.dump({"messages": [{"id": "legacy-1", "body": "old format"}]}, fh)

        summary = get_user_summary(uid)
        assert summary.get("message_stats", {}).get("health", 0) == 0

    def test_get_user_analytics_summary_includes_interaction_patterns(
        self, mock_user_data
    ):
        uid = mock_user_data["user_id"]
        user_dir = mock_user_data["user_dir"]
        ts = now_timestamp_full()

        checkins_path = os.path.join(user_dir, "checkins.json")
        with open(checkins_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "schema_version": SCHEMA_VERSION,
                    "updated_at": ts,
                    "checkins": [
                        {
                            "id": "c1",
                            "submitted_at": ts,
                            "created_at": ts,
                            "updated_at": ts,
                            "responses": {"mood": "ok"},
                        }
                    ],
                },
                fh,
            )

        chat_path = os.path.join(user_dir, "chat_interactions.json")
        with open(chat_path, "w", encoding="utf-8") as fh:
            json.dump(
                [{"timestamp": ts, "message": "hi", "response": "hello"}],
                fh,
            )

        analytics = get_user_analytics_summary(uid)
        assert analytics.get("user_id") == uid
        patterns = analytics.get("interaction_patterns", {})
        assert "checkins" in patterns
        assert patterns["checkins"]["count"] >= 1
        assert "chat_interactions" in patterns
        assert isinstance(analytics.get("recommendations"), list)

    def test_build_user_index_includes_indexed_users(
        self, mock_user_data_with_messages
    ):
        uid = mock_user_data_with_messages["user_id"]
        index = build_user_index()
        assert isinstance(index, dict)
        assert uid in index
        entry = index[uid]
        assert entry.get("active") is True
        assert "motivational" in entry.get("categories", [])
