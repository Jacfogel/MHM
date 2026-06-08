"""Request-file actions for the admin UI."""

import contextlib
import json
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Any


_lazy_dependencies = import_module("ui.lazy_dependencies")
handle_errors = _lazy_dependencies.handle_errors
logger = _lazy_dependencies.get_component_logger("ui")
get_flags_dir = _lazy_dependencies.get_flags_dir
get_user_data = _lazy_dependencies.get_user_data
now_timestamp_full = _lazy_dependencies.now_timestamp_full
UserContext = _lazy_dependencies.UserContext


def _load_attr(module_name: str, attr_name: str):
    """Load a project attribute through the UI lazy dependency boundary."""
    # ERROR_HANDLING_EXCLUDE: low-level lazy import helper; callers are decorated or fail fast.
    return _lazy_dependencies.load_attr(module_name, attr_name)


@dataclass
class RequestActionOutcome:
    """UI-neutral result for a request action."""

    level: str
    title: str
    message: str
    request_file: Path | None = None
    data: dict[str, Any] = field(default_factory=dict)


@handle_errors("truncating request action dialog text", user_friendly=False)
def _truncate_for_dialog(value: str, max_length: int = 100) -> str:
    """Truncate long service response text for message boxes."""
    if len(value) > max_length:
        return value[: max_length - 3] + "..."
    return value


@handle_errors("polling request response file", default_return={})
def _poll_response_file(response_file: Path, *, attempts: int = 30) -> dict[str, Any]:
    """Wait briefly for a service response flag and return its decoded payload."""
    for _ in range(attempts):
        if response_file.exists():
            try:
                with open(response_file) as f:
                    response_data = json.load(f)
                with contextlib.suppress(Exception):
                    os.remove(response_file)
                return response_data
            except Exception as e:
                logger.debug(f"Could not read response file {response_file}: {e}")
        time.sleep(0.1)
    return {}


@handle_errors(
    "scheduling stale test message request cleanup",
    user_friendly=False,
    default_return=None,
)
def _schedule_stale_request_cleanup(request_file: Path) -> None:
    """Remove unprocessed test-message request files later in normal UI runs."""
    is_test_env = "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ
    if is_test_env:
        return

    @handle_errors(
        "cleaning up old request file", user_friendly=False, default_return=None
    )
    def cleanup_old_requests() -> None:
        try:
            time.sleep(300)
            if os.path.exists(request_file):
                os.remove(request_file)
                logger.debug(f"Cleaned up old request file: {request_file}")
        except Exception as e:
            logger.debug(f"Cleanup thread error (ignored): {e}")

    cleanup_thread = threading.Thread(target=cleanup_old_requests, daemon=True)
    cleanup_thread.start()


@handle_errors("creating test message request", default_return=None)
def create_test_message_request(
    user_id: str | None,
    category: str,
) -> RequestActionOutcome | None:
    """Create a test-message request for the running service."""
    if not category or not isinstance(category, str):
        logger.error(f"Invalid category: {category}")
        return None
    if not category.strip():
        logger.error("Empty category provided")
        return None

    original_user = UserContext().get_user_id()
    try:
        UserContext().set_user_id(user_id)
        logger.info(
            f"Admin Panel: Creating test message request for user {user_id}, category {category}"
        )

        base_dir = get_flags_dir()
        request_file = base_dir / f"test_message_request_{user_id}_{category}.flag"
        test_request = {
            "user_id": user_id,
            "category": category,
            "timestamp": now_timestamp_full(),
            "source": "admin_panel",
        }

        with open(request_file, "w") as f:
            json.dump(test_request, f, indent=2)
        logger.info(f"Admin Panel: Test message request file created: {request_file}")

        actual_message = "Message will be selected from your collection"
        response_file = base_dir / f"test_message_response_{user_id}_{category}.flag"
        response_data = _poll_response_file(response_file)
        actual_message = response_data.get("message", actual_message)

        prefs_result = get_user_data(user_id, "preferences", normalize_on_read=True)
        preferences = prefs_result.get("preferences", {})
        channel_name = preferences.get("channel", {}).get("type", "unknown")
        actual_message = _truncate_for_dialog(actual_message)

        _schedule_stale_request_cleanup(request_file)
        return RequestActionOutcome(
            level="info",
            title="Test Message Sent",
            message=(
                f"Test {category} message sent to {user_id} via {channel_name}.\n\n"
                f"Message: {actual_message}"
            ),
            request_file=request_file,
            data={"message": actual_message, "channel_name": channel_name},
        )
    finally:
        UserContext().set_user_id(original_user if original_user else None)


@handle_errors("creating check-in prompt request", default_return=None)
def create_checkin_prompt_request(user_id: str) -> RequestActionOutcome | None:
    """Create a check-in prompt request for the running service."""
    logger.info(f"Admin Panel: Sending check-in prompt to user {user_id}")

    prefs_result = get_user_data(user_id, "preferences", normalize_on_read=True)
    preferences = prefs_result.get("preferences")
    if not preferences:
        return RequestActionOutcome(
            level="warning",
            title="User Configuration Error",
            message=f"User preferences not found for {user_id}.",
        )

    messaging_service = preferences.get("channel", {}).get("type")
    if not messaging_service:
        return RequestActionOutcome(
            level="warning",
            title="User Configuration Error",
            message=f"No messaging service configured for {user_id}.",
        )

    base_dir = Path(__file__).parent.parent
    request_file = base_dir / f"checkin_prompt_request_{user_id}.flag"
    checkin_request = {
        "user_id": user_id,
        "timestamp": now_timestamp_full(),
        "source": "admin_panel",
    }

    with open(request_file, "w") as f:
        json.dump(checkin_request, f, indent=2)

    first_question = "Check-in questions"
    response_file = base_dir / f"checkin_prompt_response_{user_id}.flag"
    response_data = _poll_response_file(response_file)
    first_question = response_data.get("first_question", first_question)
    first_question = _truncate_for_dialog(first_question)

    logger.info(f"Admin Panel: Check-in prompt request file created: {request_file}")
    return RequestActionOutcome(
        level="info",
        title="Check-in Prompt Sent",
        message=(
            f"Check-in prompt sent to {user_id} via {messaging_service}.\n\n"
            f"First question: {first_question}"
        ),
        request_file=request_file,
        data={
            "first_question": first_question,
            "messaging_service": messaging_service,
        },
    )


@handle_errors("creating task reminder request", default_return=None)
def create_task_reminder_request(
    user_id: str,
    *,
    create_communication_manager,
) -> RequestActionOutcome | None:
    """Create a task reminder request for the running service."""
    logger.info(f"Admin Panel: Preparing task reminder for user {user_id}")

    try:
        prefs_result = get_user_data(user_id, "preferences", normalize_on_read=True)
        preferences = prefs_result.get("preferences")

        are_tasks_enabled = _load_attr("tasks", "are_tasks_enabled")
        load_active_tasks = _load_attr("tasks", "load_active_tasks")
        runtime_task_is_completed = _load_attr(
            "tasks.task_data_handlers", "runtime_task_is_completed"
        )

        if not are_tasks_enabled(user_id):
            return RequestActionOutcome(
                level="warning",
                title="Tasks Not Enabled",
                message=f"Tasks are not enabled for {user_id}.",
            )

        active_tasks = load_active_tasks(user_id)
        if not active_tasks:
            return RequestActionOutcome(
                level="warning",
                title="No Active Tasks",
                message=f"{user_id} has no active tasks to remind about.",
            )

        incomplete_tasks = [
            task for task in active_tasks if not runtime_task_is_completed(task)
        ]
        if not incomplete_tasks:
            return RequestActionOutcome(
                level="warning",
                title="No Incomplete Tasks",
                message=f"All tasks for {user_id} are already completed.",
            )

        SchedulerManager = _load_attr("scheduler.manager", "SchedulerManager")
        temp_comm_manager = create_communication_manager()
        scheduler_manager = SchedulerManager(temp_comm_manager)
        selected_task = scheduler_manager.select_task_for_reminder(incomplete_tasks)

        if not selected_task:
            return RequestActionOutcome(
                level="warning",
                title="Task Selection Error",
                message="Could not select a task for reminder.",
            )

        task_id = selected_task.get("id")
        task_title = selected_task.get("title", "Untitled Task")
        if not task_id:
            return RequestActionOutcome(
                level="warning",
                title="Invalid Task",
                message="Selected task has no id.",
            )

        messaging_service = (
            preferences.get("channel", {}).get("type") if preferences else None
        )
        channel_name = messaging_service if messaging_service else "unknown"
        base_dir = Path(__file__).parent.parent
        request_file = base_dir / f"task_reminder_request_{user_id}_{task_id}.flag"
        task_reminder_request = {
            "user_id": user_id,
            "task_identifier": task_id,
            "timestamp": now_timestamp_full(),
            "source": "admin_panel",
        }

        with open(request_file, "w") as f:
            json.dump(task_reminder_request, f, indent=2)

        logger.info(
            f"Admin Panel: Task reminder request file created: {request_file}"
        )
        return RequestActionOutcome(
            level="info",
            title="Task Reminder Sent",
            message=(
                f"Task reminder sent to {user_id} via {channel_name}.\n\n"
                f"Task: {task_title}"
            ),
            request_file=request_file,
            data={
                "channel_name": channel_name,
                "task_id": task_id,
                "task_title": task_title,
            },
        )
    except Exception as e:
        logger.error(f"Error sending task reminder: {e}")
        return RequestActionOutcome(
            level="critical",
            title="Error",
            message=f"Failed to send task reminder: {str(e)}",
        )
