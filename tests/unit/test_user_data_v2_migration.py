import json
from pathlib import Path

import pytest

from core.user_data_v2 import (
    migrate_checkins,
    migrate_message_templates,
    migrate_notebook_entries,
    migrate_sent_messages,
    migrate_task_collections,
    migrate_user_data_root,
    validate_v2_document,
)
from core.message_management import get_recent_messages, load_user_messages, store_sent_message
from core.response_tracking import get_recent_checkins, store_user_response
from notebook.notebook_data_handlers import load_entries, save_entries
from tasks.task_data_handlers import load_active_tasks, load_completed_tasks, save_active_tasks

pytestmark = [pytest.mark.unit]

TIMESTAMP = "2026-04-26 09:15:00"


@pytest.mark.unit
@pytest.mark.core
def test_task_migration_consolidates_active_and_completed_records():
    active = {
        "tasks": [
            {
                "task_id": "11111111-1111-4111-8111-111111111111",
                "title": "Take meds",
                "description": "With breakfast",
                "category": "high",
                "due_date": "2026-04-27",
                "due_time": "08:00",
                "reminder_periods": ["morning"],
                "created_at": TIMESTAMP,
                "last_updated": TIMESTAMP,
            }
        ]
    }
    completed = {
        "completed_tasks": [
            {
                "task_id": "22222222-2222-4222-8222-222222222222",
                "title": "Drink water",
                "completed": True,
                "completed_at": TIMESTAMP,
                "completion_notes": "Done",
                "created_at": TIMESTAMP,
            }
        ]
    }

    migrated, report = migrate_task_collections(active, completed)

    assert migrated["schema_version"] == 2
    assert len(migrated["tasks"]) == 2
    active_task = migrated["tasks"][0]
    assert active_task["id"] == "11111111-1111-4111-8111-111111111111"
    assert active_task["short_id"].startswith("t")
    assert active_task["priority"] == "high"
    assert active_task["category"] == ""
    assert active_task["due"] == {"date": "2026-04-27", "time": "08:00"}
    assert active_task["reminders"] == [{"period": "morning", "kind": "scheduled"}]
    completed_task = migrated["tasks"][1]
    assert completed_task["status"] == "completed"
    assert completed_task["completion"]["completed"] is True
    assert completed_task["completion"]["notes"] == "Done"
    assert "task_id" not in active_task
    assert report["records_migrated"] == 2
    _normalized, validation_errors = validate_v2_document("tasks", migrated)
    assert validation_errors == []


@pytest.mark.unit
@pytest.mark.core
def test_notebook_migration_splits_journal_and_preserves_list_items():
    raw = {
        "schema_version": 1,
        "entries": [
            {
                "id": "33333333-3333-4333-8333-333333333333",
                "kind": "journal",
                "title": "Daily reflection",
                "body": "I did the hard thing.",
                "created_at": TIMESTAMP,
                "updated_at": TIMESTAMP,
            },
            {
                "id": "44444444-4444-4444-8444-444444444444",
                "kind": "list",
                "title": "Groceries",
                "items": [{"id": "item-1", "text": "Tea", "done": False, "order": 0}],
                "created_at": TIMESTAMP,
                "updated_at": TIMESTAMP,
            },
        ],
    }

    migrated, _report = migrate_notebook_entries(raw)

    journal = migrated["entries"][0]
    assert journal["kind"] == "journal_entry"
    assert journal["description"] == "I did the hard thing."
    assert journal["submitted_at"] == TIMESTAMP
    assert "body" not in journal
    list_entry = migrated["entries"][1]
    assert list_entry["kind"] == "list"
    assert list_entry["items"][0]["text"] == "Tea"


@pytest.mark.unit
@pytest.mark.core
def test_checkin_migration_wraps_array_and_moves_flat_answers_to_responses():
    migrated, _report = migrate_checkins(
        [
            {
                "timestamp": TIMESTAMP,
                "mood": "okay",
                "energy": "low",
                "questions_asked": ["mood", "energy"],
            }
        ]
    )

    assert migrated["schema_version"] == 2
    assert migrated["checkins"][0]["submitted_at"] == TIMESTAMP
    assert migrated["checkins"][0]["responses"] == {"mood": "okay", "energy": "low"}
    assert "timestamp" not in migrated["checkins"][0]


@pytest.mark.unit
@pytest.mark.core
def test_message_template_and_delivery_migrations_split_concepts():
    templates, template_report = migrate_message_templates(
        {
            "messages": [
                {
                    "message_id": "template-1",
                    "message": "You can do this.",
                    "days": ["Monday"],
                    "time_periods": ["morning"],
                    "timestamp": TIMESTAMP,
                }
            ]
        },
        "motivational",
    )
    deliveries, delivery_report = migrate_sent_messages(
        {
            "messages": [
                {
                    "message_id": "template-1",
                    "message": "You can do this.",
                    "category": "motivational",
                    "delivery_status": "sent",
                    "timestamp": TIMESTAMP,
                    "time_period": "morning",
                }
            ]
        }
    )

    message = templates["messages"][0]
    assert message["id"] == "template-1"
    assert message["text"] == "You can do this."
    assert message["schedule"] == {"days": ["Monday"], "periods": ["morning"]}
    assert "message" not in message

    delivery = deliveries["deliveries"][0]
    assert delivery["message_template_id"] == "template-1"
    assert delivery["sent_text"] == "You can do this."
    assert delivery["sent_at"] == TIMESTAMP
    assert "delivery_status" not in delivery

    assert set(template_report["fields_renamed"]) == {"days", "message", "message_id", "time_periods", "timestamp"}
    assert template_report["fields_dropped"] == []
    assert set(delivery_report["fields_renamed"]) == {"delivery_status", "message", "message_id", "timestamp"}
    assert delivery_report["fields_dropped"] == []
    _normalized_templates, template_errors = validate_v2_document("messages", templates)
    assert template_errors == []
    _normalized_deliveries, delivery_errors = validate_v2_document("deliveries", deliveries)
    assert delivery_errors == []


@pytest.mark.unit
@pytest.mark.core
def test_v2_validation_rejects_obsolete_fields():
    data = {
        "schema_version": 2,
        "updated_at": TIMESTAMP,
        "tasks": [
            {
                "id": "55555555-5555-4555-8555-555555555555",
                "short_id": "t555555",
                "kind": "task",
                "title": "Bad legacy field",
                "description": "",
                "category": "",
                "group": "",
                "tags": [],
                "priority": "medium",
                "status": "active",
                "task_id": "legacy",
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
            }
        ],
    }

    _normalized, errors = validate_v2_document("tasks", data)

    assert errors
    assert "task_id" in errors[0]


@pytest.mark.unit
@pytest.mark.core
def test_user_root_migration_dry_run_and_write_create_report_and_backup(tmp_path):
    user_root = tmp_path / "user-1"
    (user_root / "tasks").mkdir(parents=True)
    (user_root / "notebook").mkdir()
    (user_root / "messages").mkdir()
    (user_root / "tasks" / "active_tasks.json").write_text(
        json.dumps({"tasks": [{"task_id": "task-1", "title": "Plan", "created_at": TIMESTAMP}]}),
        encoding="utf-8",
    )
    (user_root / "tasks" / "completed_tasks.json").write_text(
        json.dumps({"completed_tasks": []}),
        encoding="utf-8",
    )
    (user_root / "tasks" / "task_schedules.json").write_text(
        json.dumps({"task_schedules": {}}),
        encoding="utf-8",
    )
    (user_root / "notebook" / "entries.json").write_text(
        json.dumps({"entries": []}),
        encoding="utf-8",
    )
    (user_root / "checkins.json").write_text(json.dumps([]), encoding="utf-8")
    (user_root / "messages" / "motivational.json").write_text(
        json.dumps({"messages": []}),
        encoding="utf-8",
    )
    (user_root / "messages" / "sent_messages.json").write_text(
        json.dumps({"messages": []}),
        encoding="utf-8",
    )

    dry_run = migrate_user_data_root(user_root, write=False)
    assert "tasks/tasks.json" in dry_run["payloads"]
    assert not (user_root / "tasks" / "tasks.json").exists()

    written = migrate_user_data_root(user_root, write=True)

    assert (user_root / "tasks" / "tasks.json").is_file()
    assert not (user_root / "migration_reports").exists()
    assert not (user_root / "tasks" / "active_tasks.json").exists()
    assert not (user_root / "tasks" / "completed_tasks.json").exists()
    assert not (user_root / "tasks" / "task_schedules.json").exists()
    assert written["backup_path"]
    assert Path(written["backup_path"]).exists()
    assert "tasks/tasks.json" in written["files_migrated"]
    assert "tasks/active_tasks.json" in written["files_removed"]

    reported = migrate_user_data_root(user_root, write=True, save_report=True)
    assert reported["migration_report_path"]
    assert Path(reported["migration_report_path"]).exists()


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
    monkeypatch.setattr("core.message_management.get_user_data_dir", lambda _user_id: str(user_root))

    messages = load_user_messages("user-1", "motivational")

    assert messages == [
        {
            "message_id": "template-1",
            "message": "Keep going.",
            "category": "motivational",
            "days": ["Monday"],
            "time_periods": ["morning"],
            "timestamp": TIMESTAMP,
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
    monkeypatch.setattr("core.message_management.determine_file_path", lambda _file_type, _user_id: str(sent_file))

    messages = get_recent_messages("user-1", category="motivational")

    assert messages[0]["message_id"] == "template-1"
    assert messages[0]["message"] == "Keep going."
    assert messages[0]["timestamp"] == TIMESTAMP


@pytest.mark.unit
@pytest.mark.core
def test_runtime_store_sent_message_writes_v2_delivery_when_file_is_v2(tmp_path, monkeypatch):
    sent_file = tmp_path / "sent_messages.json"
    sent_file.write_text(
        json.dumps({"schema_version": 2, "updated_at": TIMESTAMP, "deliveries": []}),
        encoding="utf-8",
    )
    monkeypatch.setattr("core.message_management.determine_file_path", lambda _file_type, _user_id: str(sent_file))
    monkeypatch.setattr("core.message_management.now_timestamp_full", lambda: TIMESTAMP)

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
    monkeypatch.setattr("core.response_tracking.get_user_file_path", lambda _user_id, _file_type: str(checkins_file))
    monkeypatch.setattr("core.response_tracking.now_timestamp_full", lambda: TIMESTAMP)

    recent = get_recent_checkins("user-1")
    assert recent[0]["timestamp"] == TIMESTAMP
    assert recent[0]["mood"] == "okay"
    assert recent[0]["responses"] == {"mood": "okay"}

    store_user_response("user-1", {"energy": "low", "questions_asked": ["energy"]}, "checkin")

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
    monkeypatch.setattr("core.user_item_storage.get_user_data_dir", lambda _user_id: str(user_root))

    active = load_active_tasks("user-1")
    completed = load_completed_tasks("user-1")

    assert active[0]["task_id"] == "task-active"
    assert active[0]["completed"] is False
    assert completed[0]["task_id"] == "task-completed"
    assert completed[0]["completed"] is True

    assert save_active_tasks(
        "user-1",
        [
            {
                "task_id": "task-new",
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
    assert entries[0].kind == "journal"
    assert entries[0].body == "Today was okay."

    save_entries("user-1", entries)

    data = json.loads(entries_file.read_text(encoding="utf-8"))
    assert data["schema_version"] == 2
    assert data["entries"][0]["kind"] == "journal_entry"
    assert data["entries"][0]["description"] == "Today was okay."
    assert "body" not in data["entries"][0]
