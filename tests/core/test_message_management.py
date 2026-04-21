"""
Tests for core/message_management.py
"""

import json
import pytest
import os
from datetime import datetime, timezone
from unittest.mock import patch

from core.message_management import (

    archive_old_messages,
    get_message_categories,
    store_sent_message,
)

pytestmark = [pytest.mark.core]



def _patch_message_mgmt_utc_now(monkeypatch, fixed_now: datetime) -> None:
    """Make archive_old_messages use a fixed UTC 'now' (cutoff math)."""

    class _PatchedDatetime:
        min = datetime.min
        max = datetime.max

        @staticmethod
        def now(tz=None):
            return fixed_now

    monkeypatch.setattr("core.message_management.datetime", _PatchedDatetime)


@pytest.mark.unit
@pytest.mark.messages
@pytest.mark.core
class TestGetMessageCategories:
    """Test get_message_categories function."""
    
    def test_get_message_categories_from_json(self):
        """Test getting categories from JSON format."""
        with patch.dict(os.environ, {'CATEGORIES': '["motivational", "reminder", "checkin"]'}):
            result = get_message_categories()
            assert result == ["motivational", "reminder", "checkin"]
    
    def test_get_message_categories_from_comma_separated(self):
        """Test getting categories from comma-separated format."""
        with patch.dict(os.environ, {'CATEGORIES': 'motivational,reminder,checkin'}):
            result = get_message_categories()
            assert result == ["motivational", "reminder", "checkin"]
    
    def test_get_message_categories_empty(self):
        """Test getting categories when CATEGORIES is empty."""
        with patch.dict(os.environ, {'CATEGORIES': ''}, clear=True):
            result = get_message_categories()
            assert result == []
    
    def test_get_message_categories_none(self):
        """Test getting categories when CATEGORIES is not set."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_message_categories()
            assert result == []


@pytest.mark.unit
@pytest.mark.messages
@pytest.mark.core
class TestStoreSentMessage:
    """Test store_sent_message function."""
    
    def test_store_sent_message_success(self):
        """Test storing a sent message successfully."""
        with patch('core.message_management.load_json_data', return_value={"sent_messages": []}):
            with patch('core.message_management.save_json_data', return_value=True):
                result = store_sent_message("test_user", "motivational", "msg1", "Test message")
                assert result is True


@pytest.mark.unit
@pytest.mark.messages
@pytest.mark.core
class TestArchiveOldMessages:
    """Tests for archive_old_messages (retention / sent_messages.json)."""

    def test_archive_old_messages_none_user(self):
        assert archive_old_messages(None, days_to_keep=30) is False

    def test_archive_old_messages_no_file_messages_key(self, tmp_path, monkeypatch):
        sent = tmp_path / "sent_messages.json"
        sent.write_text(json.dumps({}), encoding="utf-8")
        monkeypatch.setattr(
            "core.message_management.determine_file_path",
            lambda _ft, _uid: str(sent),
        )
        assert archive_old_messages("user-1", days_to_keep=30) is True

    def test_archive_old_messages_skips_when_nothing_stale(self, tmp_path, monkeypatch):
        fixed_now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        _patch_message_mgmt_utc_now(monkeypatch, fixed_now)

        sent = tmp_path / "sent_messages.json"
        payload = {
            "messages": [
                {
                    "message_id": "m1",
                    "timestamp": "2026-06-10 10:00:00",
                    "message": "recent",
                    "category": "motivational",
                }
            ],
            "metadata": {"total_messages": 1},
        }
        sent.write_text(json.dumps(payload), encoding="utf-8")
        monkeypatch.setattr(
            "core.message_management.determine_file_path",
            lambda _ft, _uid: str(sent),
        )
        assert archive_old_messages("user-1", days_to_keep=30) is True
        archives = tmp_path / "archives"
        assert not archives.exists()

        data = json.loads(sent.read_text(encoding="utf-8"))
        assert len(data["messages"]) == 1

    def test_archive_old_messages_moves_stale_rows(self, tmp_path, monkeypatch):
        fixed_now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        _patch_message_mgmt_utc_now(monkeypatch, fixed_now)

        sent = tmp_path / "sent_messages.json"
        payload = {
            "messages": [
                {
                    "message_id": "old",
                    "timestamp": "2026-05-01 10:00:00",
                    "message": "stale",
                    "category": "motivational",
                },
                {
                    "message_id": "new",
                    "timestamp": "2026-06-10 10:00:00",
                    "message": "keep",
                    "category": "reminder",
                },
            ],
            "metadata": {"total_messages": 2},
        }
        sent.write_text(json.dumps(payload), encoding="utf-8")
        monkeypatch.setattr(
            "core.message_management.determine_file_path",
            lambda _ft, _uid: str(sent),
        )
        monkeypatch.setattr(
            "core.message_management.now_timestamp_filename", lambda: "test_archive_ts"
        )

        assert archive_old_messages("user-1", days_to_keep=30) is True

        archive_dir = tmp_path / "archives"
        archive_file = archive_dir / "sent_messages_archive_test_archive_ts.json"
        assert archive_file.is_file()

        archived = json.loads(archive_file.read_text(encoding="utf-8"))
        assert len(archived["messages"]) == 1
        assert archived["messages"][0]["message_id"] == "old"

        active = json.loads(sent.read_text(encoding="utf-8"))
        assert len(active["messages"]) == 1
        assert active["messages"][0]["message_id"] == "new"
        assert active["metadata"]["total_messages"] == 1
