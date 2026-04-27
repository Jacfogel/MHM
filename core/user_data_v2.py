"""
Canonical v2 user-data schemas plus transitional JSON migration helpers.

Runtime code imports the v2 models/validators from this module. Some migration
helpers are also imported temporarily by runtime adapters while v2-native task,
notebook, check-in, and message code is completed; track their retirement in
TODO.md before treating this module as stable runtime-only surface area.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Literal
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from core.config import get_backups_dir
from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import (
    now_timestamp_filename,
    now_timestamp_full,
    parse_date_only,
    parse_time_only_minute,
    parse_timestamp_full,
)

logger = get_component_logger(__name__)

SCHEMA_VERSION = 2

ItemKind = Literal["task", "note", "list", "journal_entry"]
TaskStatus = Literal["active", "completed", "cancelled", "archived", "deleted"]
NotebookStatus = Literal["active", "archived", "deleted"]
MessageTemplateStatus = Literal["active", "archived", "deleted"]
DeliveryStatus = Literal["sent", "failed", "skipped"]

OLD_FIELD_NAMES_BY_DOCUMENT: dict[str, set[str]] = {
    "task": {
        "task_id",
        "completed",
        "completed_at",
        "completion_notes",
        "due_date",
        "due_time",
        "reminder_periods",
        "quick_reminders",
        "recurrence_pattern",
        "recurrence_interval",
        "repeat_after_completion",
        "next_due_date",
        "last_updated",
    },
    "notebook": {"body", "archived"},
    "checkin": {"timestamp"},
    "message": {"message_id", "message", "days", "time_periods", "timestamp"},
    "delivery": {"message_id", "message", "delivery_status", "timestamp"},
}

TRANSFORMED_OLD_FIELD_NAMES = {
    field
    for fields in OLD_FIELD_NAMES_BY_DOCUMENT.values()
    for field in fields
}


class SourceModel(BaseModel):
    """Best-known origin of a migrated or newly written record."""

    model_config = ConfigDict(extra="forbid")

    system: str = "mhm"
    channel: str = ""
    actor: str = ""
    migration: str | None = None


class DueModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str | None = None
    time: str | None = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value and parse_date_only(value) is None:
            raise _schema_validation_error("due.date must use YYYY-MM-DD")
        return value

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: str | None) -> str | None:
        if value and parse_time_only_minute(value) is None:
            raise _schema_validation_error("due.time must use HH:MM")
        return value


class ScheduleModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    days: list[str] = Field(default_factory=lambda: ["ALL"])
    periods: list[str] = Field(default_factory=lambda: ["ALL"])


class CompletionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completed: bool = False
    completed_at: str | None = None
    notes: str = ""

    @field_validator("completed_at")
    @classmethod
    def validate_completed_at(cls, value: str | None) -> str | None:
        _validate_optional_timestamp(value, "completion.completed_at")
        return value


class RecurrenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern: str | None = None
    interval: int = 1
    repeat_after_completion: bool = True
    next_due_date: str | None = None

    @field_validator("next_due_date")
    @classmethod
    def validate_next_due_date(cls, value: str | None) -> str | None:
        if value and parse_date_only(value) is None:
            raise _schema_validation_error("recurrence.next_due_date must use YYYY-MM-DD")
        return value


class BaseItemModel(BaseModel):
    """Shared item fields for v2 task, notebook, list, and journal records."""

    model_config = ConfigDict(extra="forbid")

    id: str
    short_id: str
    kind: ItemKind
    title: str = ""
    description: str = ""
    category: str = ""
    group: str = ""
    tags: list[str] = Field(default_factory=list)
    status: str = "active"
    source: SourceModel = Field(default_factory=SourceModel)
    linked_item_ids: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    archived_at: str | None = None
    deleted_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_required_timestamp(cls, value: str) -> str:
        if parse_timestamp_full(value) is None:
            raise _schema_validation_error("timestamp must use canonical full timestamp format")
        return value

    @field_validator("archived_at", "deleted_at")
    @classmethod
    def validate_optional_timestamp(cls, value: str | None) -> str | None:
        _validate_optional_timestamp(value, "optional timestamp")
        return value

    @field_validator("tags", "linked_item_ids", mode="before")
    @classmethod
    def normalize_string_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise _schema_validation_error("value must be a list")
        return [str(item).strip() for item in value if str(item).strip()]


class TaskV2Model(BaseItemModel):
    kind: Literal["task"] = "task"
    status: TaskStatus = "active"
    priority: Literal["low", "medium", "high", "urgent", "critical"] = "medium"
    due: DueModel = Field(default_factory=DueModel)
    reminders: list[dict[str, Any]] = Field(default_factory=list)
    recurrence: RecurrenceModel = Field(default_factory=RecurrenceModel)
    completion: CompletionModel = Field(default_factory=CompletionModel)

    @model_validator(mode="after")
    def validate_completion_status(self) -> TaskV2Model:
        if self.status == "completed" and not self.completion.completed:
            raise _schema_validation_error("completed tasks must set completion.completed")
        return self


class NotebookV2Model(BaseItemModel):
    kind: Literal["note", "list", "journal_entry"]
    status: NotebookStatus = "active"
    pinned: bool = False
    submitted_at: str | None = None
    items: list[dict[str, Any]] | None = None

    @field_validator("submitted_at")
    @classmethod
    def validate_submitted_at(cls, value: str | None) -> str | None:
        _validate_optional_timestamp(value, "submitted_at")
        return value

    @model_validator(mode="after")
    def validate_kind_details(self) -> NotebookV2Model:
        if self.kind == "journal_entry" and not self.submitted_at:
            raise _schema_validation_error("journal_entry records require submitted_at")
        if self.kind == "list" and not self.items:
            raise _schema_validation_error("list records require items")
        if self.kind != "list" and self.items is not None:
            raise _schema_validation_error("only list records may include items")
        return self


class CheckinV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    submitted_at: str
    source: SourceModel = Field(default_factory=SourceModel)
    responses: dict[str, Any] = Field(default_factory=dict)
    questions_asked: list[str] = Field(default_factory=list)
    linked_item_ids: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    archived_at: str | None = None
    deleted_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("submitted_at", "created_at", "updated_at")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        if parse_timestamp_full(value) is None:
            raise _schema_validation_error("timestamp must use canonical full timestamp format")
        return value


class MessageTemplateV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: Literal["message"] = "message"
    text: str
    category: str
    active: bool = True
    schedule: ScheduleModel = Field(default_factory=ScheduleModel)
    created_at: str
    updated_at: str
    archived_at: str | None = None
    deleted_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        if parse_timestamp_full(value) is None:
            raise _schema_validation_error("timestamp must use canonical full timestamp format")
        return value


class MessageDeliveryV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    message_template_id: str
    sent_text: str
    category: str
    channel: str = ""
    status: DeliveryStatus = "sent"
    source: SourceModel = Field(default_factory=SourceModel)
    sent_at: str
    time_period: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("sent_at")
    @classmethod
    def validate_sent_at(cls, value: str) -> str:
        if parse_timestamp_full(value) is None:
            raise _schema_validation_error("sent_at must use canonical full timestamp format")
        return value


class TaskCollectionV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    tasks: list[TaskV2Model] = Field(default_factory=list)


class NotebookCollectionV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    entries: list[NotebookV2Model] = Field(default_factory=list)


class CheckinCollectionV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    checkins: list[CheckinV2Model] = Field(default_factory=list)


class MessageTemplateCollectionV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    category: str
    updated_at: str
    messages: list[MessageTemplateV2Model] = Field(default_factory=list)


class MessageDeliveryCollectionV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    deliveries: list[MessageDeliveryV2Model] = Field(default_factory=list)


@handle_errors("generating v2 short id", re_raise=True)
def generate_short_id(record_id: str, kind: str, length: int = 6) -> str:
    """Generate a mobile-friendly no-dash short ID from a UUID-like value."""
    prefix_map = {
        "task": "t",
        "note": "n",
        "list": "l",
        "journal": "j",
        "journal_entry": "j",
        "message": "m",
        "delivery": "d",
        "checkin": "c",
    }
    prefix = prefix_map.get(kind, kind[:1].lower())
    uuid_value = _stable_uuid(record_id)
    fragment = str(uuid_value).replace("-", "")[:length]
    return f"{prefix}{fragment}"


# error_handling_exclude: This validation API returns Pydantic errors as data.
def validate_v2_document(document_type: str, data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a v2 document and return normalized data plus validation errors."""
    model_by_type = {
        "tasks": TaskCollectionV2Model,
        "notebook": NotebookCollectionV2Model,
        "checkins": CheckinCollectionV2Model,
        "messages": MessageTemplateCollectionV2Model,
        "deliveries": MessageDeliveryCollectionV2Model,
    }
    model_cls = model_by_type.get(document_type)
    if model_cls is None:
        return data, [f"Unknown v2 document type: {document_type}"]
    obsolete = _find_obsolete_fields(data, document_type)
    if obsolete:
        return data, [f"Obsolete v1 fields are not allowed in v2 {document_type}: {sorted(obsolete)}"]
    try:
        model = model_cls.model_validate(data)
        return model.model_dump(mode="json"), []
    except Exception as exc:
        return data, [str(exc)]


@handle_errors("migrating task collections to v2", re_raise=True)
def migrate_task_collections(
    active_data: dict[str, Any] | None,
    completed_data: dict[str, Any] | None,
    task_schedules_data: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Migrate active/completed task files into one v2 task collection."""
    report = _new_report("tasks")
    tasks: list[dict[str, Any]] = []
    for item in _list_from_wrapper(active_data, "tasks"):
        tasks.append(_migrate_task(item, "active", report))
    for item in _list_from_wrapper(completed_data, "completed_tasks"):
        tasks.append(_migrate_task(item, "completed", report))
    if task_schedules_data:
        _append_report_field(report, "fields_moved_to_metadata", "task_schedules.json:task_schedules")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_timestamp_full(),
        "tasks": tasks,
    }
    return payload, report


@handle_errors("migrating notebook entries to v2", re_raise=True)
def migrate_notebook_entries(raw_data: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Migrate notebook entries into v2 note/list/journal_entry records."""
    report = _new_report("notebook")
    entries = []
    for item in _list_from_wrapper(raw_data, "entries"):
        entries.append(_migrate_notebook_entry(item, report))
    payload = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_timestamp_full(),
        "entries": entries,
    }
    return payload, report


@handle_errors("migrating checkins to v2", re_raise=True)
def migrate_checkins(raw_data: list[Any] | dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Migrate bare check-in arrays or partial v2-like documents to v2."""
    report = _new_report("checkins")
    if isinstance(raw_data, dict):
        records = raw_data.get("checkins", [])
    elif isinstance(raw_data, list):
        records = raw_data
    else:
        records = []
    checkins = []
    for item in records:
        if isinstance(item, dict):
            checkins.append(_migrate_checkin(item, report))
        else:
            report["records_requiring_review"].append({"reason": "checkin record is not an object", "record": item})
    payload = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_timestamp_full(),
        "checkins": checkins,
    }
    return payload, report


@handle_errors("migrating message templates to v2", re_raise=True)
def migrate_message_templates(
    raw_data: dict[str, Any] | None,
    category: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Migrate one category message template file to v2."""
    report = _new_report(f"messages/{category}")
    messages = []
    for item in _list_from_wrapper(raw_data, "messages"):
        messages.append(_migrate_message_template(item, category, report))
    payload = {
        "schema_version": SCHEMA_VERSION,
        "category": category,
        "updated_at": now_timestamp_full(),
        "messages": messages,
    }
    return payload, report


@handle_errors("migrating sent messages to v2", re_raise=True)
def migrate_sent_messages(raw_data: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Migrate sent-message history to v2 delivery records."""
    report = _new_report("messages/sent_messages")
    deliveries = []
    for item in _list_from_wrapper(raw_data, "messages"):
        deliveries.append(_migrate_delivery(item, report))
    payload = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_timestamp_full(),
        "deliveries": deliveries,
    }
    return payload, report


@handle_errors("migrating user data root to v2", re_raise=True)
def migrate_user_data_root(
    user_root: str | Path,
    *,
    write: bool = False,
    save_report: bool = False,
) -> dict[str, Any]:
    """
    Migrate one user data directory to v2 JSON documents.

    When write=False, returns the report and generated payloads without writing.
    When write=True, creates a backup under the configured backups directory,
    writes v2 files, and removes replaced v1 task files.
    """
    root = Path(user_root)
    timestamp = now_timestamp_filename()
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "user_root": str(root),
        "generated_at": now_timestamp_full(),
        "write": write,
        "backup_path": "",
        "files_migrated": [],
        "sections": [],
        "payloads": {},
    }
    if write:
        backups_dir = Path(get_backups_dir())
        backups_dir.mkdir(parents=True, exist_ok=True)
        backup_path = _unique_backup_path(backups_dir / f"{root.name}_backup_user_data_v2_{timestamp}")
        shutil.copytree(root, backup_path, dirs_exist_ok=False)
        report["backup_path"] = str(backup_path)

    payloads = _build_user_payloads(root, report)
    report["payloads"] = payloads

    if write:
        _write_user_payloads(root, payloads, report)
        if save_report:
            report_dir = Path(get_backups_dir()) / "migration_reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / f"{root.name}_user_data_v2_{timestamp}.json"
            report_to_write = dict(report)
            report_to_write.pop("payloads", None)
            report_path.write_text(json.dumps(report_to_write, indent=2), encoding="utf-8")
            report["migration_report_path"] = str(report_path)

    return report


@handle_errors("building v2 user data payloads", re_raise=True)
def _build_user_payloads(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    payloads: dict[str, Any] = {}
    tasks_payload, tasks_report = migrate_task_collections(
        _read_json(root / "tasks" / "active_tasks.json"),
        _read_json(root / "tasks" / "completed_tasks.json"),
        _read_json(root / "tasks" / "task_schedules.json"),
    )
    payloads["tasks/tasks.json"] = tasks_payload
    report["sections"].append(tasks_report)

    notebook_payload, notebook_report = migrate_notebook_entries(_read_json(root / "notebook" / "entries.json"))
    payloads["notebook/entries.json"] = notebook_payload
    report["sections"].append(notebook_report)

    checkin_payload, checkin_report = migrate_checkins(_read_json(root / "checkins.json"))
    payloads["checkins.json"] = checkin_payload
    report["sections"].append(checkin_report)

    messages_dir = root / "messages"
    if messages_dir.exists():
        for message_file in sorted(messages_dir.glob("*.json")):
            if message_file.name == "sent_messages.json":
                delivery_payload, delivery_report = migrate_sent_messages(_read_json(message_file))
                payloads["messages/sent_messages.json"] = delivery_payload
                report["sections"].append(delivery_report)
            else:
                category = message_file.stem
                template_payload, template_report = migrate_message_templates(_read_json(message_file), category)
                payloads[f"messages/{message_file.name}"] = template_payload
                report["sections"].append(template_report)
    return payloads


@handle_errors("writing v2 user data payloads", re_raise=True)
def _write_user_payloads(root: Path, payloads: dict[str, Any], report: dict[str, Any]) -> None:
    for relative_path, payload in payloads.items():
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        report["files_migrated"].append(relative_path)
    _remove_replaced_v1_task_files(root, report)


@handle_errors("removing replaced v1 task files", re_raise=True)
def _remove_replaced_v1_task_files(root: Path, report: dict[str, Any]) -> None:
    """Remove task files that are fully replaced by tasks/tasks.json."""
    if not (root / "tasks" / "tasks.json").exists():
        return
    for relative_path in (
        "tasks/active_tasks.json",
        "tasks/completed_tasks.json",
        "tasks/task_schedules.json",
    ):
        path = root / relative_path
        if path.exists():
            path.unlink()
            _append_report_field(report, "files_removed", relative_path)


@handle_errors("creating unique migration backup path", re_raise=True)
def _unique_backup_path(base_path: Path) -> Path:
    """Return a backup path that will not collide with a prior same-second run."""
    if not base_path.exists():
        return base_path
    suffix = 1
    while True:
        candidate = base_path.with_name(f"{base_path.name}_{suffix:02d}")
        if not candidate.exists():
            return candidate
        suffix += 1


@handle_errors("migrating one task record to v2", re_raise=True)
def _migrate_task(item: dict[str, Any], status: TaskStatus, report: dict[str, Any]) -> dict[str, Any]:
    old_id = str(item.get("task_id") or item.get("id") or uuid4())
    created_at = _timestamp_or_now(item.get("created_at"))
    updated_at = _timestamp_or_now(item.get("last_updated") or item.get("updated_at") or created_at)
    completed_at = item.get("completed_at") if status == "completed" else None
    category = str(item.get("category") or "")
    priority = str(item.get("priority") or "medium").lower()
    if category.lower() in {"low", "medium", "high", "urgent", "critical"} and not item.get("priority"):
        priority = category.lower()
        category = ""
        _append_report_field(report, "fields_renamed", "category->priority")
    if priority not in {"low", "medium", "high", "urgent", "critical"}:
        report["records_requiring_review"].append({"id": old_id, "reason": f"unknown priority {priority!r}; defaulted"})
        priority = "medium"
    migrated = {
        "id": old_id,
        "short_id": item.get("short_id") or generate_short_id(old_id, "task"),
        "kind": "task",
        "title": str(item.get("title") or ""),
        "description": str(item.get("description") or ""),
        "category": category,
        "group": str(item.get("group") or ""),
        "tags": item.get("tags") or [],
        "priority": priority,
        "status": status,
        "due": {"date": item.get("due_date"), "time": item.get("due_time")},
        "reminders": _build_reminders(item),
        "recurrence": {
            "pattern": item.get("recurrence_pattern"),
            "interval": item.get("recurrence_interval") or 1,
            "repeat_after_completion": item.get("repeat_after_completion", True),
            "next_due_date": item.get("next_due_date"),
        },
        "completion": {
            "completed": status == "completed",
            "completed_at": _timestamp_or_none(completed_at),
            "notes": str(item.get("completion_notes") or ""),
        },
        "source": _migration_source(),
        "linked_item_ids": item.get("linked_item_ids") or [],
        "created_at": created_at,
        "updated_at": updated_at,
        "archived_at": item.get("archived_at"),
        "deleted_at": item.get("deleted_at"),
        "metadata": _metadata_for_unmapped(item, OLD_FIELD_NAMES_BY_DOCUMENT["task"]),
    }
    _record_old_fields(item, OLD_FIELD_NAMES_BY_DOCUMENT["task"], report)
    return TaskV2Model.model_validate(migrated).model_dump(mode="json")


@handle_errors("migrating one notebook record to v2", re_raise=True)
def _migrate_notebook_entry(item: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    old_id = str(item.get("id") or uuid4())
    old_kind = item.get("kind") or "note"
    kind = "journal_entry" if old_kind == "journal" else old_kind
    created_at = _timestamp_or_now(item.get("created_at"))
    updated_at = _timestamp_or_now(item.get("updated_at") or created_at)
    archived = bool(item.get("archived", False))
    migrated = {
        "id": old_id,
        "short_id": item.get("short_id") or generate_short_id(old_id, str(kind)),
        "kind": kind,
        "title": str(item.get("title") or ""),
        "description": str(item.get("description") or item.get("body") or ""),
        "category": str(item.get("category") or ""),
        "group": str(item.get("group") or ""),
        "tags": item.get("tags") or [],
        "status": "archived" if archived else "active",
        "pinned": bool(item.get("pinned", False)),
        "submitted_at": _timestamp_or_now(item.get("submitted_at") or created_at) if kind == "journal_entry" else None,
        "items": item.get("items") if kind == "list" else None,
        "source": _migration_source(),
        "linked_item_ids": item.get("linked_item_ids") or [],
        "created_at": created_at,
        "updated_at": updated_at,
        "archived_at": updated_at if archived else item.get("archived_at"),
        "deleted_at": item.get("deleted_at"),
        "metadata": _metadata_for_unmapped(item, OLD_FIELD_NAMES_BY_DOCUMENT["notebook"]),
    }
    _record_old_fields(item, OLD_FIELD_NAMES_BY_DOCUMENT["notebook"], report)
    if old_kind == "journal":
        _append_report_field(report, "fields_renamed", "kind:journal->journal_entry")
    return NotebookV2Model.model_validate(migrated).model_dump(mode="json")


@handle_errors("migrating one checkin record to v2", re_raise=True)
def _migrate_checkin(item: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    submitted_at = _timestamp_or_now(item.get("submitted_at") or item.get("timestamp"))
    questions = item.get("questions_asked") or []
    responses = item.get("responses")
    if not isinstance(responses, dict):
        skipped = {"timestamp", "submitted_at", "questions_asked", "source", "linked_item_ids", "created_at", "updated_at"}
        responses = {key: value for key, value in item.items() if key not in skipped}
    migrated = {
        "id": str(item.get("id") or uuid4()),
        "submitted_at": submitted_at,
        "source": item.get("source") or _migration_source(),
        "responses": responses,
        "questions_asked": questions or list(responses.keys()),
        "linked_item_ids": item.get("linked_item_ids") or [],
        "created_at": _timestamp_or_now(item.get("created_at") or submitted_at),
        "updated_at": _timestamp_or_now(item.get("updated_at") or submitted_at),
        "archived_at": item.get("archived_at"),
        "deleted_at": item.get("deleted_at"),
        "metadata": _metadata_for_unmapped(item, OLD_FIELD_NAMES_BY_DOCUMENT["checkin"]),
    }
    _record_old_fields(item, OLD_FIELD_NAMES_BY_DOCUMENT["checkin"], report)
    return CheckinV2Model.model_validate(migrated).model_dump(mode="json")


@handle_errors("migrating one message template to v2", re_raise=True)
def _migrate_message_template(item: dict[str, Any], category: str, report: dict[str, Any]) -> dict[str, Any]:
    old_id = str(item.get("message_id") or item.get("id") or uuid4())
    created_at = _timestamp_or_now(item.get("created_at") or item.get("timestamp"))
    migrated = {
        "id": old_id,
        "kind": "message",
        "text": str(item.get("text") or item.get("message") or ""),
        "category": str(item.get("category") or category),
        "active": bool(item.get("active", True)),
        "schedule": {
            "days": item.get("days") or item.get("schedule", {}).get("days") or ["ALL"],
            "periods": item.get("time_periods") or item.get("schedule", {}).get("periods") or ["ALL"],
        },
        "created_at": created_at,
        "updated_at": _timestamp_or_now(item.get("updated_at") or created_at),
        "archived_at": item.get("archived_at"),
        "deleted_at": item.get("deleted_at"),
        "metadata": _metadata_for_unmapped(item, OLD_FIELD_NAMES_BY_DOCUMENT["message"]),
    }
    _record_old_fields(item, OLD_FIELD_NAMES_BY_DOCUMENT["message"], report)
    return MessageTemplateV2Model.model_validate(migrated).model_dump(mode="json")


@handle_errors("migrating one delivery record to v2", re_raise=True)
def _migrate_delivery(item: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    template_id = str(item.get("message_template_id") or item.get("message_id") or "")
    sent_at = _timestamp_or_now(item.get("sent_at") or item.get("timestamp"))
    migrated = {
        "id": str(item.get("id") or uuid4()),
        "message_template_id": template_id,
        "sent_text": str(item.get("sent_text") or item.get("message") or ""),
        "category": str(item.get("category") or ""),
        "channel": str(item.get("channel") or ""),
        "status": str(item.get("status") or item.get("delivery_status") or "sent"),
        "source": item.get("source") or _migration_source(actor="scheduler"),
        "sent_at": sent_at,
        "time_period": item.get("time_period"),
        "metadata": _metadata_for_unmapped(item, OLD_FIELD_NAMES_BY_DOCUMENT["delivery"]),
    }
    _record_old_fields(item, OLD_FIELD_NAMES_BY_DOCUMENT["delivery"], report)
    return MessageDeliveryV2Model.model_validate(migrated).model_dump(mode="json")


@handle_errors("building migrated task reminders", re_raise=True)
def _build_reminders(item: dict[str, Any]) -> list[dict[str, Any]]:
    reminders = []
    for period in item.get("reminder_periods") or []:
        reminders.append({"period": period, "kind": "scheduled"})
    for reminder in item.get("quick_reminders") or []:
        reminders.append({"value": reminder, "kind": "quick"})
    return reminders


@handle_errors("creating v2 migration report section", re_raise=True)
def _new_report(section: str) -> dict[str, Any]:
    """Create the standard per-section report structure."""
    return {
        "section": section,
        "records_migrated": 0,
        "fields_renamed": [],
        "fields_dropped": [],
        "fields_moved_to_metadata": [],
        "records_requiring_review": [],
    }


@handle_errors("recording v2 migration field handling", re_raise=True)
def _record_old_fields(item: dict[str, Any], old_fields: set[str], report: dict[str, Any]) -> None:
    report["records_migrated"] += 1
    for field in sorted(old_fields.intersection(item.keys())):
        if field in TRANSFORMED_OLD_FIELD_NAMES:
            _append_report_field(report, "fields_renamed", field)
        else:
            _append_report_field(report, "fields_dropped", field)


@handle_errors("appending unique v2 migration report field", re_raise=True)
def _append_report_field(report: dict[str, Any], key: str, field: str) -> None:
    """Append a field name to a report list once, keeping dry-run reports readable."""
    values = report.setdefault(key, [])
    if field not in values:
        values.append(field)


@handle_errors("collecting unmapped legacy fields", re_raise=True)
def _metadata_for_unmapped(item: dict[str, Any], old_fields: set[str]) -> dict[str, Any]:
    known_keep = old_fields.union(
        {
            "id",
            "short_id",
            "kind",
            "title",
            "description",
            "category",
            "group",
            "tags",
            "priority",
            "status",
            "source",
            "linked_item_ids",
            "created_at",
            "updated_at",
            "archived_at",
            "deleted_at",
            "metadata",
            "pinned",
            "items",
            "submitted_at",
            "responses",
            "questions_asked",
            "active",
            "schedule",
            "text",
            "sent_text",
            "message_template_id",
            "channel",
            "sent_at",
            "time_period",
        }
    )
    metadata = dict(item.get("metadata") or {})
    for key, value in item.items():
        if key not in known_keep:
            metadata[f"legacy_{key}"] = value
    return metadata


@handle_errors("finding obsolete v1 fields", re_raise=True)
def _find_obsolete_fields(data: Any, document_type: str) -> set[str]:
    """Find obsolete fields on v2 record objects without scanning nested v2 shapes."""
    obsolete_by_type = {
        "tasks": OLD_FIELD_NAMES_BY_DOCUMENT["task"],
        "notebook": OLD_FIELD_NAMES_BY_DOCUMENT["notebook"],
        "checkins": OLD_FIELD_NAMES_BY_DOCUMENT["checkin"],
        "messages": OLD_FIELD_NAMES_BY_DOCUMENT["message"],
        "deliveries": OLD_FIELD_NAMES_BY_DOCUMENT["delivery"],
    }
    obsolete = obsolete_by_type.get(document_type, set())
    found: set[str] = set()
    collection_key_by_type = {
        "tasks": "tasks",
        "notebook": "entries",
        "checkins": "checkins",
        "messages": "messages",
        "deliveries": "deliveries",
    }
    collection_key = collection_key_by_type.get(document_type)

    if isinstance(data, dict):
        found.update(obsolete.intersection(data.keys()))
        records = data.get(collection_key, []) if collection_key else []
    elif isinstance(data, list):
        records = data
    else:
        records = []

    for record in records:
        if isinstance(record, dict):
            found.update(obsolete.intersection(record.keys()))
    return found


@handle_errors("reading records from migration wrapper", re_raise=True)
def _list_from_wrapper(data: dict[str, Any] | None, key: str) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    records = data.get(key, [])
    return [record for record in records if isinstance(record, dict)]


@handle_errors("normalizing optional migration timestamp", re_raise=True)
def _timestamp_or_now(value: Any) -> str:
    """Return a canonical timestamp, using the current time when input is invalid."""
    if isinstance(value, str) and parse_timestamp_full(value) is not None:
        return value
    return now_timestamp_full()


@handle_errors("normalizing nullable migration timestamp", re_raise=True)
def _timestamp_or_none(value: Any) -> str | None:
    """Return a canonical timestamp or None when input is missing or invalid."""
    if isinstance(value, str) and parse_timestamp_full(value) is not None:
        return value
    return None


@handle_errors("validating optional migration timestamp", re_raise=True)
def _validate_optional_timestamp(value: str | None, field_name: str) -> None:
    if value and parse_timestamp_full(value) is None:
        raise _schema_validation_error(f"{field_name} must use canonical full timestamp format")


@handle_errors("coercing stable migration uuid", re_raise=True)
def _stable_uuid(value: str) -> UUID:
    """Return value as a UUID, deriving a stable UUID for old non-UUID IDs."""
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return uuid5(NAMESPACE_URL, str(value))


@handle_errors("building v2 migration source metadata", re_raise=True)
def _migration_source(actor: str = "") -> dict[str, str]:
    """Return the standard source block for records created by this migration."""
    return {"system": "mhm", "channel": "", "actor": actor, "migration": "user_data_v2"}


@handle_errors("building v2 schema validation error", re_raise=True)
def _schema_validation_error(message: str) -> PydanticCustomError:
    """Build a Pydantic-native validation error without generic exception raises."""
    return PydanticCustomError("user_data_v2_validation", "{message}", {"message": message})


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning(f"Could not read JSON for v2 migration at {path}: {exc}")
        return None
