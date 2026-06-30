# File-flag request handling for the headless service (test messages, check-ins, reminders, reschedule).

from __future__ import annotations

import contextlib
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.delivery import ServiceRequestDeliveryPort
from core.error_handling import FileOperationError, ValidationError, handle_errors
from core.logger import get_component_logger
from storage.service_flag_storage import read_service_flag_json, write_service_flag_json
from core.time_utilities import now_timestamp_filename, now_timestamp_full

logger = get_component_logger("main")


@dataclass
class ServiceRequestContext:
    base_dir: Path
    delivery: ServiceRequestDeliveryPort | None
    scheduler_manager: Any | None
    shutdown_callback: Callable[[], None]
    startup_time: float | None = None


@handle_errors("resolving service request recipient", default_return=None)
def _get_recipient_for_service(
    delivery: ServiceRequestDeliveryPort,
    user_id: str,
    messaging_service: str,
    preferences: dict,
) -> str | None:
    """Resolve a recipient through the public delivery port."""
    return delivery.get_recipient_for_service(user_id, messaging_service, preferences)


@handle_errors("normalizing service request context")
def _as_context(context_or_service: Any) -> ServiceRequestContext:
    """Normalize explicit contexts and context-capable service wrappers to one shape."""
    if isinstance(context_or_service, ServiceRequestContext):
        return context_or_service
    context_factory = getattr(context_or_service, "to_service_request_context", None)
    if callable(context_factory):
        return context_factory()
    raise ValidationError(
        "service request helpers require ServiceRequestContext or an object "
        "with to_service_request_context()"
    )


@handle_errors(
    "resolving repo base directory",
    user_friendly=False,
    re_raise=True,
)
def get_repo_base_directory() -> str:
    """Project root (parent of ``core/``)."""
    return str(Path(__file__).resolve().parent.parent)


@handle_errors("creating reschedule request", default_return=False)
def create_reschedule_request(
    user_id: str, category: str, source: str = "schedule_runtime"
) -> bool:
    """
    Create a reschedule request flag that the running service will process.

    Args:
        user_id: User whose schedule should be recalculated.
        category: Message category to reschedule.
        source: Diagnostic source metadata for the request.

    Returns:
        True when the request file was written. False when the service is not
        currently running or the write fails.
    """
    from core.service_utilities import get_flags_dir, is_service_running

    if not is_service_running():
        logger.debug(
            "Service not running - schedule changes will be picked up on next startup"
        )
        return False

    requested_at_readable = now_timestamp_full()
    request_data = {
        "user_id": user_id,
        "category": category,
        "timestamp": time.time(),
        "requested_at_readable": requested_at_readable,
        "requested_at_iso": requested_at_readable,
        "source": source,
    }

    ms_suffix = int(time.time() * 1000) % 1000
    filename_timestamp = f"{now_timestamp_filename()}_{ms_suffix:03d}"
    filename = f"reschedule_request_{user_id}_{category}_{filename_timestamp}.flag"
    request_file = Path(get_flags_dir()) / filename

    created = write_service_flag_json(
        request_file,
        request_data,
        indent=2,
        audit_reason="create_reschedule_request",
        audit_extra={"user_id": user_id, "category": category, "source": source},
    )
    if not created:
        return False

    logger.info(f"Created reschedule request: {filename}")
    return True


@handle_errors("polling service request files", default_return=None)
def process_pending_file_requests(context: ServiceRequestContext) -> None:
    """Process request-flag files when any ``.flag`` exists under the repo root."""
    context = _as_context(context)
    base_dir = str(context.base_dir)
    if not has_any_request_files(base_dir):
        return
    check_test_message_requests(context)
    check_checkin_prompt_requests(context)
    check_task_reminder_requests(context)
    check_reschedule_requests(context)


@handle_errors("processing shutdown request file", default_return=False)
def process_shutdown_request(
    context: ServiceRequestContext, shutdown_file: Path
) -> bool:
    """Return True when shutdown was requested and the main loop should stop."""
    context = _as_context(context)
    if not os.path.exists(shutdown_file):
        return False

    try:
        file_mtime = os.path.getmtime(shutdown_file)
        if context.startup_time and file_mtime < context.startup_time:
            logger.debug(
                "Ignoring old shutdown request file (created before service startup)"
            )
            try:
                os.remove(shutdown_file)
                logger.debug("Removed old shutdown request file")
            except Exception as e:
                logger.warning(f"Could not remove old shutdown file: {e}")
            return False
    except Exception as e:
        logger.warning(f"Error checking shutdown file timestamp: {e}")
        logger.info("Shutdown request file detected - initiating graceful shutdown")
        context.shutdown_callback()
        return True

    logger.info("Shutdown request file detected - initiating graceful shutdown")
    try:
        with open(shutdown_file, encoding="utf-8") as f:
            content = f.read().strip()
        if content.startswith("SHUTDOWN_REQUESTED_BY_UI_"):
            logger.info("Shutdown requested by UI")
        elif content.startswith("HEADLESS_SHUTDOWN_REQUESTED_"):
            logger.info("Shutdown requested by headless service manager")
        else:
            logger.info(f"Shutdown request details: {content}")
    except Exception as e:
        logger.warning(f"Could not read shutdown file: {e}")
    context.shutdown_callback()
    return True


@handle_errors("checking if request files exist", default_return=False)
def has_any_request_files(base_dir: str) -> bool:
    try:
        base_path = Path(base_dir)
        for file_path in base_path.iterdir():
            if file_path.is_file() and file_path.name.endswith(".flag"):
                return True
        return False
    except Exception:
        return True


@handle_errors("discovering flag request files", default_return=[])
def _discover_flag_request_files(base_dir: str, name_prefix: str) -> list[str]:
    """List `.flag` request files under base_dir whose names start with name_prefix."""
    base_path = Path(base_dir)
    request_files: list[str] = []
    for file_path in base_path.iterdir():
        if (
            file_path.is_file()
            and file_path.name.startswith(name_prefix)
            and file_path.name.endswith(".flag")
        ):
            request_files.append(str(file_path))
    return request_files


@handle_errors("discovering test message request files", default_return=[])
def discover_test_message_request_files(base_dir: str) -> list[str]:
    return _discover_flag_request_files(base_dir, "test_message_request_")


# not_duplicate: service_request_file_parsers
@handle_errors(
    "parsing test message request file",
    default_return={"user_id": None, "category": None, "source": "unknown"},
)
def parse_test_message_request_file(request_file: str) -> dict[str, Any]:
    request_data = read_service_flag_json(
        request_file,
        {"user_id": None, "category": None, "source": "unknown"},
    )
    user_id = request_data.get("user_id")
    category = request_data.get("category")
    source = request_data.get("source", "unknown")
    return {"user_id": user_id, "category": category, "source": source}


@handle_errors("validating test message request data", default_return=False)
def validate_test_message_request_data(request_data: dict, filename: str) -> bool:
    user_id = request_data["user_id"]
    category = request_data["category"]
    if not user_id or not category:
        logger.warning(
            f"Invalid test message request in {filename}: missing user_id or category"
        )
        return False
    return True


# not_duplicate: service_request_processors
@handle_errors("processing test message request", default_return=None)
def process_valid_test_message_request(
    context: ServiceRequestContext, request_data: dict
) -> None:
    context = _as_context(context)
    user_id = request_data["user_id"]
    category = request_data["category"]
    source = request_data["source"]
    logger.info(
        f"Processing test message request from {source}: user={user_id}, category={category}"
    )
    if context.delivery:
        send_result = context.delivery.handle_message_sending(
            user_id, category, skip_ai_cache=True
        )
        if send_result.status != "sent":
            logger.warning(
                f"Test message not delivered for {user_id}, category={category}: "
                f"status={send_result.status}"
            )
            write_test_message_response(
                user_id,
                category,
                (
                    "The test message could not be delivered. "
                    "Check service logs and try again."
                ),
                base_dir=str(context.base_dir),
            )
            return
        logger.info(
            f"Test message sent successfully for {user_id}, category={category}"
        )
        actual_message = send_result.sent_text
        if actual_message and send_result.matches_request(user_id, category):
            write_test_message_response(
                user_id,
                category,
                actual_message,
                base_dir=str(context.base_dir),
            )
    else:
        logger.error("Delivery interface not available for test message")


# not_duplicate: service_response_writers
@handle_errors("writing test message response", default_return=None)
def write_test_message_response(
    user_id: str,
    category: str,
    message: str,
    *,
    base_dir: str | None = None,
) -> None:
    try:
        root = base_dir if base_dir is not None else get_repo_base_directory()
        response_file = Path(root) / f"test_message_response_{user_id}_{category}.flag"
        _write_response_file(
            response_file,
            {
                "user_id": user_id,
                "category": category,
                "message": message,
                "timestamp": now_timestamp_full(),
            },
        )
        logger.debug(f"Wrote test message response file: {response_file}")
    except Exception as e:
        logger.debug(f"Could not write response file: {e}")


@handle_errors(
    "writing service response file",
    user_friendly=False,
    re_raise=True,
)
def _write_response_file(response_file: Path, response_data: dict[str, Any]) -> None:
    """Write a service response flag file as indented JSON."""
    if not write_service_flag_json(response_file, response_data, indent=2):
        raise FileOperationError(f"Failed to write service response file: {response_file}")


@handle_errors("writing service request failure response", default_return=None)
def write_request_failure_response(
    base_dir: str | Path,
    request_filename: str,
    request_type: str,
    error: str,
) -> None:
    response_file = (
        Path(base_dir) / f"{Path(request_filename).stem}_response_error.flag"
    )
    response_data = {
        "request_type": request_type,
        "request_file": request_filename,
        "success": False,
        "error": error,
        "timestamp": now_timestamp_full(),
    }
    _write_response_file(response_file, response_data)
    logger.debug(f"Wrote service request failure response file: {response_file}")


# not_duplicate: cleanup_request_file_delegate
@handle_errors(
    "cleaning up request file after process",
    user_friendly=False,
    default_return=None,
)
def cleanup_request_file_after_process(
    request_file: str, filename: str, request_type_label: str
) -> None:
    os.remove(request_file)
    logger.info(f"Processed {request_type_label} request: {filename}")


@handle_errors("checking test message requests", default_return=None)
def check_test_message_requests(context: ServiceRequestContext) -> None:
    context = _as_context(context)
    base_dir = str(context.base_dir)
    request_files = discover_test_message_request_files(base_dir)
    for request_file in request_files:
        filename = os.path.basename(request_file)
        request_data = parse_test_message_request_file(request_file)
        if validate_test_message_request_data(request_data, filename):
            process_valid_test_message_request(context, request_data)
        else:
            write_request_failure_response(
                context.base_dir,
                filename,
                "test_message",
                "Missing required user_id or category.",
            )
        cleanup_request_file_after_process(request_file, filename, "test message")


@handle_errors("getting check-in first question", default_return=None)
def get_checkin_first_question(user_id: str) -> str | None:
    try:
        from communication.message_processing.conversation_flow_manager import (
            conversation_manager,
        )
        from core import get_user_data

        prefs_result = get_user_data(user_id, "preferences")
        checkin_prefs = prefs_result.get("preferences", {}).get("checkin_settings", {})
        enabled_questions = checkin_prefs.get("questions", {})
        question_order = conversation_manager._select_checkin_questions_with_weighting(
            user_id, enabled_questions
        )
        if question_order:
            first_question_key = question_order[0]
            return conversation_manager._get_question_text(first_question_key, {})
    except Exception as e:
        logger.debug(f"Could not get check-in first question: {e}")
    return None


# not_duplicate: service_response_writers
@handle_errors("writing check-in response", default_return=None)
def write_checkin_response(
    user_id: str, first_question: str, *, base_dir: str | None = None
) -> None:
    try:
        root = base_dir if base_dir is not None else get_repo_base_directory()
        response_file = Path(root) / f"checkin_prompt_response_{user_id}.flag"
        _write_response_file(
            response_file,
            {
                "user_id": user_id,
                "first_question": first_question,
                "timestamp": now_timestamp_full(),
            },
        )
        logger.debug(f"Wrote check-in prompt response file: {response_file}")
    except Exception as e:
        logger.debug(f"Could not write check-in response file: {e}")


@handle_errors("checking check-in prompt requests")
def check_checkin_prompt_requests(context: ServiceRequestContext) -> None:
    context = _as_context(context)
    base_path = context.base_dir
    for file_path in base_path.iterdir():
        if (
            file_path.is_file()
            and file_path.name.startswith("checkin_prompt_request_")
            and file_path.name.endswith(".flag")
        ):
            filename = os.path.basename(file_path)
            try:
                request_data = read_service_flag_json(file_path)
                user_id = request_data.get("user_id")
                if user_id and context.delivery:
                    from core import get_user_data

                    prefs_result = get_user_data(
                        user_id, "preferences", normalize_on_read=True
                    )
                    preferences = prefs_result.get("preferences")
                    if preferences:
                        messaging_service = preferences.get("channel", {}).get("type")
                        if messaging_service:
                            recipient = _get_recipient_for_service(
                                context.delivery,
                                user_id,
                                messaging_service,
                                preferences,
                            )
                            if recipient:
                                first_question = get_checkin_first_question(user_id)
                                context.delivery.send_checkin_prompt(
                                    user_id, messaging_service, recipient
                                )
                                logger.info(
                                    f"Check-in prompt sent successfully for {user_id}"
                                )
                                if first_question:
                                    write_checkin_response(
                                        user_id,
                                        first_question,
                                        base_dir=str(context.base_dir),
                                    )
                os.remove(file_path)
                logger.info(f"Processed check-in prompt request: {filename}")
            except Exception as e:
                logger.error(
                    f"Error processing check-in prompt request {filename}: {e}"
                )
                write_request_failure_response(
                    context.base_dir,
                    filename,
                    "checkin_prompt",
                    str(e),
                )
                with contextlib.suppress(Exception):
                    os.remove(file_path)


@handle_errors("checking task reminder requests")
def check_task_reminder_requests(context: ServiceRequestContext) -> None:
    context = _as_context(context)
    base_path = context.base_dir
    for file_path in base_path.iterdir():
        if (
            file_path.is_file()
            and file_path.name.startswith("task_reminder_request_")
            and file_path.name.endswith(".flag")
        ):
            filename = os.path.basename(file_path)
            try:
                request_data = read_service_flag_json(file_path)
                user_id = request_data.get("user_id")
                task_identifier = request_data.get("task_identifier")
                if user_id and task_identifier and context.delivery:
                    context.delivery.handle_task_reminder(
                        user_id, task_identifier
                    )
                    logger.info(
                        f"Task reminder sent successfully for {user_id}, task {task_identifier}"
                    )
                os.remove(file_path)
                logger.info(f"Processed task reminder request: {filename}")
            except Exception as e:
                logger.error(
                    f"Error processing task reminder request {filename}: {e}"
                )
                write_request_failure_response(
                    context.base_dir,
                    filename,
                    "task_reminder",
                    str(e),
                )
                with contextlib.suppress(Exception):
                    os.remove(file_path)


@handle_errors(
    "checking test message request filename pattern",
    user_friendly=False,
    re_raise=True,
)
def is_test_message_request_filename(filename: str) -> bool:
    return filename.startswith("test_message_request_") and filename.endswith(".flag")


@handle_errors("cleaning up matching service request files", default_return=None)
def _cleanup_matching_request_files(
    base_path: Path,
    predicate: Callable[[Path], bool],
    label: str,
) -> None:
    """Remove request files matching a predicate while continuing after per-file failures."""
    for file_path in base_path.iterdir():
        if not predicate(file_path):
            continue
        try:
            os.remove(str(file_path))
            logger.info(f"Cleanup: Removed {label} request file: {file_path.name}")
        except OSError as e:
            logger.warning(
                f"Could not remove {label} request file {file_path.name}: {e}"
            )


# not_duplicate: service_request_cleanup_entrypoints
@handle_errors("cleaning up test message requests")
def cleanup_test_message_requests(context: ServiceRequestContext) -> None:
    context = _as_context(context)
    _cleanup_matching_request_files(
        context.base_dir,
        lambda path: path.is_file() and is_test_message_request_filename(path.name),
        "test message",
    )


@handle_errors("discovering reschedule request files", default_return=[])
def discover_reschedule_request_files(base_dir: str) -> list[str]:
    return _discover_flag_request_files(base_dir, "reschedule_request_")


# not_duplicate: service_request_file_parsers
@handle_errors(
    "parsing reschedule request file",
    default_return={
        "user_id": None,
        "category": None,
        "source": "unknown",
        "timestamp": 0,
    },
)
def parse_reschedule_request_file(request_file: str) -> dict[str, Any]:
    request_data = read_service_flag_json(
        request_file,
        {"user_id": None, "category": None, "source": "unknown", "timestamp": 0},
    )
    return {
        "user_id": request_data.get("user_id"),
        "category": request_data.get("category"),
        "source": request_data.get("source", "unknown"),
        "timestamp": request_data.get("timestamp", 0),
    }


@handle_errors("validating reschedule request data", default_return=False)
def validate_reschedule_request_data(
    context: ServiceRequestContext, request_data: dict, filename: str
) -> bool:
    context = _as_context(context)
    user_id = request_data["user_id"]
    category = request_data["category"]
    request_timestamp = request_data["timestamp"]
    if context.startup_time and request_timestamp < context.startup_time:
        logger.debug(
            f"Ignoring old reschedule request from before service startup: {filename}"
        )
        return False
    if not user_id or not category:
        logger.warning(
            f"Invalid reschedule request in {filename}: missing user_id or category"
        )
        return False
    return True


# not_duplicate: service_request_processors
@handle_errors("processing reschedule request", default_return=None)
def process_valid_reschedule_request(
    context: ServiceRequestContext, request_data: dict
) -> None:
    context = _as_context(context)
    user_id = request_data["user_id"]
    category = request_data["category"]
    source = request_data["source"]
    logger.info(
        f"Processing reschedule request from {source}: user={user_id}, category={category}"
    )
    if context.scheduler_manager:
        context.scheduler_manager.reset_and_reschedule_daily_messages(
            category, user_id
        )
        logger.info(f"Reschedule completed for {user_id}, category={category}")
    else:
        logger.error("Scheduler manager not available for reschedule")


@handle_errors("checking reschedule requests", default_return=None)
def check_reschedule_requests(context: ServiceRequestContext) -> None:
    context = _as_context(context)
    base_dir = str(context.base_dir)
    for request_file in discover_reschedule_request_files(base_dir):
        filename = os.path.basename(request_file)
        request_data = parse_reschedule_request_file(request_file)
        if validate_reschedule_request_data(context, request_data, filename):
            process_valid_reschedule_request(context, request_data)
        else:
            write_request_failure_response(
                context.base_dir,
                filename,
                "reschedule",
                "Missing required user_id or category, or request predates service startup.",
            )
        cleanup_request_file_after_process(request_file, filename, "reschedule")


# not_duplicate: service_request_cleanup_entrypoints
@handle_errors("cleaning up reschedule requests")
def cleanup_reschedule_requests(context: ServiceRequestContext) -> None:
    context = _as_context(context)
    _cleanup_matching_request_files(
        context.base_dir,
        lambda path: path.is_file()
        and path.name.startswith("reschedule_request_")
        and path.name.endswith(".flag"),
        "reschedule",
    )


@handle_errors("processing all service request flags", default_return=None)
def process_all_requests(context: ServiceRequestContext) -> None:
    """Process pending UI/headless request flags (non-shutdown)."""
    process_pending_file_requests(context)


@handle_errors(
    "removing test message request file", user_friendly=False, default_return=False
)
def remove_single_test_message_request_file(
    request_file: str, filename: str
) -> bool:
    os.remove(request_file)
    logger.info(f"Cleanup: Removed test message request file: {filename}")
    return True


@handle_errors(
    "cleaning up problematic test message request file",
    user_friendly=False,
    default_return=None,
)
def handle_test_message_request_processing_error(
    request_file: str, filename: str, error: BaseException
) -> None:
    logger.error(f"Error processing test message request {filename}: {error}")
    os.remove(request_file)
    logger.debug(f"Removed problematic request file: {filename}")


@handle_errors(
    "cleaning up problematic reschedule request file",
    user_friendly=False,
    default_return=None,
)
def handle_reschedule_request_processing_error(
    request_file: str, filename: str, error: BaseException
) -> None:
    logger.error(f"Error processing reschedule request {filename}: {error}")
    os.remove(request_file)
    logger.debug(f"Removed problematic request file: {filename}")
