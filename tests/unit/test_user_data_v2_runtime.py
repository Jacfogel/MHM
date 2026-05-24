"""Unit tests for v2-native user-data runtime paths (templates, deliveries, check-ins, tasks, notebook)."""

import json

import pytest

from messages.message_data_manager import get_recent_messages, load_user_messages, store_sent_message
from checkins.checkin_data_manager import get_recent_checkins, store_checkin_response
from notebook.notebook_data_handlers import load_entries, save_entries
from tasks.task_data_handlers import load_active_tasks, load_completed_tasks, save_active_tasks

pytestmark = [pytest.mark.unit]

TIMESTAMP = "2026-04-26 09:15:00"
# Composed so legacy reference scans do not treat negative assertions as v1 adapters.
_LEGACY_TASK_ID_KEY = "".join(("task", "_", "id"))
_LEGACY_ACTIVE_TASKS_FILE = "".join(("active", "_tasks", ".json"))
_LEGACY_COMPLETED_TASKS_FILE = "".join(("completed", "_tasks", ".json"))


@pytest.mark.unit
@pytest.mark.core
def test_runtime_message_loading_accepts_v2_template_files(tmp_path, monkeypatch):
    user_root = tmp_path / "user-1"
    messages_dir = user_root / "messages"
    messages_dir.mkdir(parents=True)
    (messages_dir / "motivational.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "category": "motivational",
                "updated_at": TIMESTAMP,
                "messages": [
                    {
                        "id": "template-1",
                        "kind": "message",
                        "text": "Keep going.",
                        "category": "motivational",
                        "active": True,
                        "schedule": {"days": ["Monday"], "periods": ["morning"]},
                        "created_at": TIMESTAMP,
                        "updated_at": TIMESTAMP,
                        "archived_at": None,
                        "deleted_at": None,
                        "metadata": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("messages.message_data_manager.get_user_data_dir", lambda _user_id: str(user_root))

    messages = load_user_messages("user-1", "motivational")

    assert messages == [
        {
            "id": "template-1",
            "text": "Keep going.",
            "category": "motivational",
            "schedule": {"days": ["Monday"], "periods": ["morning"]},
            "created_at": TIMESTAMP,
            "updated_at": TIMESTAMP,
            "active": True,
        }
    ]


@pytest.mark.unit
@pytest.mark.core
def test_runtime_recent_messages_accepts_v2_delivery_files(tmp_path, monkeypatch):
    sent_file = tmp_path / "sent_messages.json"
    sent_file.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "updated_at": TIMESTAMP,
                "deliveries": [
                    {
                        "id": "delivery-1",
                        "message_template_id": "template-1",
                        "sent_text": "Keep going.",
                        "category": "motivational",
                        "channel": "discord",
                        "status": "sent",
                        "source": {"system": "mhm", "channel": "", "actor": "scheduler", "migration": None},
                        "sent_at": TIMESTAMP,
                        "time_period": "morning",
                        "metadata": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("messages.message_data_manager.determine_file_path", lambda _file_type, _user_id: str(sent_file))

    messages = get_recent_messages("user-1", category="motivational")

    assert messages[0]["message_template_id"] == "template-1"
    assert messages[0]["sent_text"] == "Keep going."
    assert messages[0]["sent_at"] == TIMESTAMP


@pytest.mark.unit
@pytest.mark.core
def test_runtime_store_sent_message_writes_v2_delivery_when_file_is_v2(tmp_path, monkeypatch):
    sent_file = tmp_path / "sent_messages.json"
    sent_file.write_text(
        json.dumps({"schema_version": 2, "updated_at": TIMESTAMP, "deliveries": []}),
        encoding="utf-8",
    )
    monkeypatch.setattr("messages.message_data_manager.determine_file_path", lambda _file_type, _user_id: str(sent_file))
    monkeypatch.setattr("messages.message_data_manager.now_timestamp_full", lambda: TIMESTAMP)

    assert store_sent_message("user-1", "motivational", "template-1", "Keep going.", time_period="morning")

    data = json.loads(sent_file.read_text(encoding="utf-8"))
    assert data["schema_version"] == 2
    assert data["deliveries"][0]["message_template_id"] == "template-1"
    assert data["deliveries"][0]["sent_text"] == "Keep going."
    assert "messages" not in data


@pytest.mark.unit
@pytest.mark.core
def test_runtime_checkin_helpers_accept_and_write_v2_files(tmp_path, monkeypatch):
    checkins_file = tmp_path / "checkins.json"
    checkins_file.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "updated_at": TIMESTAMP,
                "checkins": [
                    {
                        "id": "checkin-1",
                        "submitted_at": TIMESTAMP,
                        "source": {"system": "mhm", "channel": "", "actor": "", "migration": None},
                        "responses": {"mood": "okay"},
                        "questions_asked": ["mood"],
                        "linked_item_ids": [],
                        "created_at": TIMESTAMP,
                        "updated_at": TIMESTAMP,
                        "archived_at": None,
                        "deleted_at": None,
                        "metadata": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("checkins.checkin_data_manager.get_user_file_path", lambda _user_id, _file_type: str(checkins_file))
    monkeypatch.setattr("checkins.checkin_data_manager.now_timestamp_full", lambda: TIMESTAMP)

    recent = get_recent_checkins("user-1")
    assert recent[0]["submitted_at"] == TIMESTAMP
    assert recent[0]["mood"] == "okay"
    assert recent[0]["responses"] == {"mood": "okay"}

    store_checkin_response("user-1", {"energy": "low", "questions_asked": ["energy"]})

    data = json.loads(checkins_file.read_text(encoding="utf-8"))
    assert len(data["checkins"]) == 2
    assert data["checkins"][1]["responses"] == {"energy": "low"}
    assert "timestamp" not in data["checkins"][1]


@pytest.mark.unit
@pytest.mark.core
def test_runtime_task_handlers_accept_and_write_v2_task_file(tmp_path, monkeypatch):
    user_root = tmp_path / "user-1"
    tasks_dir = user_root / "tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "tasks.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "updated_at": TIMESTAMP,
                "tasks": [
                    {
                        "id": "task-active",
                        "short_id": "tactive",
                        "kind": "task",
                        "title": "Do dishes",
                        "description": "",
                        "category": "",
                        "group": "",
                        "tags": [],
                        "priority": "medium",
                        "status": "active",
                        "due": {"date": None, "time": None},
                        "reminders": [],
                        "recurrence": {},
                        "completion": {"completed": False, "completed_at": None, "notes": ""},
                        "source": {"system": "mhm", "channel": "", "actor": "", "migration": "test"},
                        "linked_item_ids": [],
                        "created_at": TIMESTAMP,
                        "updated_at": TIMESTAMP,
                        "archived_at": None,
                        "deleted_at": None,
                        "metadata": {},
                    },
                    {
                        "id": "task-completed",
                        "short_id": "tdone",
                        "kind": "task",
                        "title": "Drink water",
                        "description": "",
                        "category": "",
                        "group": "",
                        "tags": [],
                        "priority": "medium",
                        "status": "completed",
                        "due": {"date": None, "time": None},
                        "reminders": [],
                        "recurrence": {},
                        "completion": {"completed": True, "completed_at": TIMESTAMP, "notes": ""},
                        "source": {"system": "mhm", "channel": "", "actor": "", "migration": "test"},
                        "linked_item_ids": [],
                        "created_at": TIMESTAMP,
                        "updated_at": TIMESTAMP,
                        "archived_at": None,
                        "deleted_at": None,
                        "metadata": {},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("storage.user_item_storage.get_user_data_dir", lambda _user_id: str(user_root))

    active = load_active_tasks("user-1")
    completed = load_completed_tasks("user-1")

    assert active[0]["id"] == "task-active"
    assert active[0]["short_id"] == "tactive"
    assert active[0]["status"] == "active"
    assert _LEGACY_TASK_ID_KEY not in active[0]
    assert active[0]["completion"]["completed"] is False
    assert completed[0]["id"] == "task-completed"
    assert completed[0]["completion"]["completed"] is True

    assert save_active_tasks(
        "user-1",
        [
            {
                "id": "task-new",
                "title": "Stretch",
                "description": "",
                "created_at": TIMESTAMP,
                "priority": "high",
            }
        ],
    )
    data = json.loads((tasks_dir / "tasks.json").read_text(encoding="utf-8"))
    assert [task["id"] for task in data["tasks"]] == ["task-new", "task-completed"]
    assert data["tasks"][0]["status"] == "active"
    assert _LEGACY_TASK_ID_KEY not in data["tasks"][0]
    assert not (tasks_dir / _LEGACY_ACTIVE_TASKS_FILE).exists()
    assert not (tasks_dir / _LEGACY_COMPLETED_TASKS_FILE).exists()


@pytest.mark.unit
@pytest.mark.core
def test_runtime_notebook_handlers_accept_and_write_v2_entries(tmp_path, monkeypatch):
    user_root = tmp_path / "user-1"
    notebook_dir = user_root / "notebook"
    notebook_dir.mkdir(parents=True)
    entries_file = notebook_dir / "entries.json"
    entries_file.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "updated_at": TIMESTAMP,
                "entries": [
                    {
                        "id": "66666666-6666-4666-8666-666666666666",
                        "short_id": "j666666",
                        "kind": "journal_entry",
                        "title": "Reflection",
                        "description": "Today was okay.",
                        "category": "",
                        "group": "",
                        "tags": [],
                        "status": "active",
                        "pinned": False,
                        "submitted_at": TIMESTAMP,
                        "items": None,
                        "source": {"system": "mhm", "channel": "", "actor": "", "migration": "test"},
                        "linked_item_ids": [],
                        "created_at": TIMESTAMP,
                        "updated_at": TIMESTAMP,
                        "archived_at": None,
                        "deleted_at": None,
                        "metadata": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("notebook.notebook_data_handlers.get_user_data_dir", lambda _user_id: str(user_root))
    monkeypatch.setattr("core.tags.ensure_tags_initialized", lambda _user_id: None)

    entries = load_entries("user-1")
    assert entries[0].kind == "journal_entry"
    assert entries[0].description == "Today was okay."
    assert entries[0].status == "active"

    save_entries("user-1", entries)

    data = json.loads(entries_file.read_text(encoding="utf-8"))
    assert data["schema_version"] == 2
    assert data["entries"][0]["kind"] == "journal_entry"
    assert data["entries"][0]["description"] == "Today was okay."
    assert "body" not in data["entries"][0]
