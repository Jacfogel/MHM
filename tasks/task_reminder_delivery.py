"""Persist task reminder attempts before calling the delivery channel."""

from uuid import uuid4

from core.error_handling import handle_errors
from core.file_operations import update_json_data
from core.time_utilities import now_timestamp_full
from storage.user_item_storage import get_user_subdir_path
from tasks.task_data_handlers import TASKS_SUBDIR

_PROCESS_ID = uuid4().hex
_FILENAME = "reminder_delivery.json"


@handle_errors("recording task reminder delivery", default_return=None)
def record_reminder_attempt(
    user_id: str,
    task_id: str,
    kind: str,
    occurrence: str,
    *,
    outcome: str | None = None,
    attempt_id: str | None = None,
    message_id: str | None = None,
) -> dict | None:
    """Claim an occurrence or record the outcome of the current attempt.

    Keep the latest daily reminder and latest deferral for each task. An
    unfinished attempt left by a previous process has an unknown outcome.
    """
    task_dir = get_user_subdir_path(user_id, TASKS_SUBDIR)
    if task_dir is None:
        return None
    record = None

    # ERROR_HANDLING_EXCLUDE: Called inside the guarded JSON transaction.
    def apply(data):
        """Claim a new attempt or update the matching attempt already on disk."""
        nonlocal record
        deliveries = data.setdefault(task_id, {})
        previous = deliveries.get(kind, {})
        same_occurrence = previous.get("occurrence") == occurrence
        if outcome is not None:
            if same_occurrence and previous.get("attempt_id") == attempt_id:
                previous.update(
                    status=outcome, message_id=message_id, updated_at=now_timestamp_full()
                )
                record = previous.copy()
        elif same_occurrence and previous["status"] not in {"failed", "skipped"}:
            if previous["status"] == "attempting" and previous["process_id"] != _PROCESS_ID:
                previous.update(status="unconfirmed", updated_at=now_timestamp_full())
            record = previous.copy()
        else:
            record = {
                "occurrence": occurrence,
                "status": "attempting",
                "process_id": _PROCESS_ID,
                "attempt_id": uuid4().hex,
                "message_id": previous.get("message_id") if same_occurrence else None,
                "updated_at": now_timestamp_full(),
            }
            deliveries[kind] = record.copy()
            record["claimed"] = True
        return data

    if update_json_data(task_dir / _FILENAME, apply, default={}):
        return record
    return None
