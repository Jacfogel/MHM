"""User data disk summaries and analytics (ops/admin, not the hot read path)."""

from __future__ import annotations

import importlib
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from checkins.checkin_data_manager import checkin_runtime_timestamp
from core.error_handling import handle_errors
from core.file_operations import get_user_data_dir, get_user_file_path, load_json_data
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full
from core.user_management import get_all_user_ids
from messages.message_data_manager import get_recent_messages
from storage.user_data_read import get_user_data
from storage.user_data_user_info import (
    _get_user_categories,
    get_user_info_for_data_manager,
    get_user_message_files,
)
from storage.user_data_v2_base import SCHEMA_VERSION
from storage.user_data_v2_envelopes import validate_v2_document

logger = get_component_logger("main")


@handle_errors(
    "building empty file summary",
    default_return={
        "user_id": "",
        "files": {},
        "messages": {},
        "logs": {},
        "total_files": 0,
        "total_size_bytes": 0,
        "last_modified": None,
    },
)
def _empty_file_summary(user_id: str) -> dict[str, Any]:
    """Return the empty disk-summary skeleton for one user."""
    return {
        "user_id": user_id,
        "files": {},
        "messages": {},
        "logs": {},
        "total_files": 0,
        "total_size_bytes": 0,
        "last_modified": None,
    }


# not_duplicate: user_data_manager_api
@handle_errors("initializing user data summary")
def _get_user_data_summary__initialize_summary(user_id: str) -> dict[str, Any]:
    """Initialize the summary structure with default values."""
    try:
        return _empty_file_summary(user_id)
    except Exception as e:
        logger.error(f"Error initializing user data summary: {e}")
        return _empty_file_summary(user_id)


@handle_errors("processing file types for user data summary")
def _get_user_data_summary__process_file_types_with_adder(
    user_id: str,
    summary: dict[str, Any],
    file_types: list[str],
    adder: Callable[[str, str, dict[str, Any]], None],
) -> None:
    """Resolve path per type; if the file exists call adder(path, file_type, summary)."""
    for file_type in file_types:
        file_path = get_user_file_path(user_id, file_type)
        if os.path.exists(file_path):
            adder(file_path, file_type, summary)


# not_duplicate: user_data_summary_adders
@handle_errors("adding file info to user data summary")
def _get_user_data_summary__add_file_info(
    file_path: str, file_type: str, summary: dict[str, Any]
) -> None:
    """Add basic file information to the summary."""
    try:
        size = os.path.getsize(file_path)
        summary["files"].setdefault(file_type, {})
        summary["files"][file_type]["exists"] = True
        summary["files"][file_type]["size"] = size
        summary["total_files"] += 1
        summary["total_size_bytes"] += size
    except Exception as e:
        logger.error(f"Error adding file info to user data summary: {e}")


@handle_errors("adding JSON file detail to user data summary", default_return=None)
def _get_user_data_summary__add_json_file_detail(
    file_path: str,
    summary: dict[str, Any],
    file_type: str,
    detail_key: str,
    extractor: Callable[[Any], Any],
    log_label: str = "detail",
) -> None:
    """Load JSON and set summary["files"][file_type][detail_key] = extractor(data)."""
    try:
        data = load_json_data(file_path)
        if data:
            summary["files"][file_type][detail_key] = extractor(data)
    except Exception as e:
        logger.error(f"Error adding {log_label} to user data summary: {e}")


# not_duplicate: user_data_summary_adders
@handle_errors("adding special file details to user data summary")
def _get_user_data_summary__add_special_file_details(
    file_path: str, file_type: str, summary: dict[str, Any]
) -> None:
    """Add special details for specific file types (schedules, sent_messages)."""
    try:
        if file_type == "schedules":
            _get_user_data_summary__add_json_file_detail(
                file_path,
                summary,
                "schedules",
                "periods",
                lambda data: sum(len(cat_schedules) for cat_schedules in data.values()),
                log_label="schedule details",
            )
        elif file_type == "sent_messages":
            _get_user_data_summary__add_json_file_detail(
                file_path,
                summary,
                "sent_messages",
                "count",
                lambda data: sum(
                    len(msgs) for msgs in data.values() if isinstance(msgs, list)
                ),
                log_label="sent messages details",
            )
    except Exception as e:
        logger.error(f"Error adding special file details to user data summary: {e}")


# not_duplicate: user_data_summary_adders
@handle_errors("adding core file info to user data summary")
def _get_user_data_summary__add_core_file_info(
    file_path: str, file_type: str, summary: dict[str, Any]
) -> None:
    """Add file info and special details for a single core file."""
    _get_user_data_summary__add_file_info(file_path, file_type, summary)
    _get_user_data_summary__add_special_file_details(file_path, file_type, summary)


# not_duplicate: user_data_summary_process_phases
@handle_errors("processing core files for user data summary")
def _get_user_data_summary__process_core_files(
    user_id: str, summary: dict[str, Any]
) -> None:
    """Process core user data files (profile, preferences, schedules, etc.)."""
    try:
        USER_DATA_LOADERS = importlib.import_module(
            "storage.user_data_registry"
        ).USER_DATA_LOADERS

        dynamic_types = list(USER_DATA_LOADERS.keys()) + ["sent_messages"]
        _get_user_data_summary__process_file_types_with_adder(
            user_id, summary, dynamic_types, _get_user_data_summary__add_core_file_info
        )
    except Exception as e:
        logger.error(f"Error processing core files for user data summary: {e}")


# not_duplicate: user_data_summary_process_phases
@handle_errors("ensuring message files for user data summary")
def _get_user_data_summary__ensure_message_files(
    user_id: str, categories: list[str]
) -> None:
    """Ensure message files exist for all user categories."""
    try:
        if not categories:
            return

        _ensure = importlib.import_module(
            "messages.message_data_manager"
        ).ensure_user_message_files

        result = _ensure(user_id, categories)
        if result["success"]:
            logger.info(
                f"Message files validation for user {user_id}: checked {result['files_checked']} categories, created {result['files_created']} files, directory_created={result['directory_created']}"
            )
        else:
            logger.warning(
                f"Message files validation for user {user_id}: checked {result['files_checked']} categories, created {result['files_created']} files, some failures occurred"
            )
    except Exception as e:
        logger.error(
            f"Error ensuring message files during validation for user {user_id}: {e}"
        )


# not_duplicate: user_data_summary_adders
@handle_errors("adding message file info to user data summary")
def _get_user_data_summary__add_message_file_info(
    file_path: str,
    category: str,
    summary: dict[str, Any],
    orphaned: bool = False,
) -> None:
    """Add message file information to the summary."""
    try:
        size = os.path.getsize(file_path)
        data = load_json_data(file_path)
        message_count = len(data.get("messages", [])) if data else 0

        message_info = {
            "exists": True,
            "size": size,
            "message_count": message_count,
            "path": file_path,
        }
        if orphaned:
            message_info["orphaned"] = True

        summary["messages"][category] = message_info
        summary["total_files"] += 1
        summary["total_size_bytes"] += size
    except Exception as e:
        logger.error(f"Error adding message file info to user data summary: {e}")


# not_duplicate: user_data_summary_adders
@handle_errors("adding missing message file info to user data summary")
def _get_user_data_summary__add_missing_message_file_info(
    file_path: str, category: str, summary: dict[str, Any], user_id: str
) -> None:
    """Add information for missing message files."""
    try:
        summary["messages"][category] = {
            "exists": False,
            "size": 0,
            "message_count": 0,
            "path": file_path,
            "creation_failed": True,
        }
        logger.warning(
            f"Message file for category {category} still missing after ensure_user_message_files for user {user_id}"
        )
    except Exception as e:
        logger.error(
            f"Error adding missing message file info to user data summary: {e}"
        )


# not_duplicate: user_data_summary_process_phases
@handle_errors("processing enabled message files for user data summary")
def _get_user_data_summary__process_enabled_message_files(
    user_id: str, categories: list[str], summary: dict[str, Any]
) -> None:
    """Process message files for enabled categories."""
    try:
        for category in categories:
            file_path = str(
                Path(get_user_data_dir(user_id)) / "messages" / f"{category}.json"
            )
            if os.path.exists(file_path):
                _get_user_data_summary__add_message_file_info(
                    file_path, category, summary, orphaned=False
                )
            else:
                _get_user_data_summary__add_missing_message_file_info(
                    file_path, category, summary, user_id
                )
    except Exception as e:
        logger.error(
            f"Error processing enabled message files for user data summary: {e}"
        )


# not_duplicate: user_data_summary_process_phases
@handle_errors("processing orphaned message files for user data summary")
def _get_user_data_summary__process_orphaned_message_files(
    user_id: str,
    categories: list[str],
    message_files: dict[str, str],
    summary: dict[str, Any],
) -> None:
    """Process orphaned message files (categories not enabled but files exist)."""
    try:
        for category, file_path in message_files.items():
            if category not in categories and os.path.exists(file_path):
                _get_user_data_summary__add_message_file_info(
                    file_path, category, summary, orphaned=True
                )
    except Exception as e:
        logger.error(
            f"Error processing orphaned message files for user data summary: {e}"
        )


# not_duplicate: user_data_summary_process_phases
@handle_errors("processing message files for user data summary")
def _get_user_data_summary__process_message_files(
    user_id: str, summary: dict[str, Any]
) -> None:
    """Process message files for all user categories."""
    try:
        prefs_result = get_user_data(user_id, "preferences")
        categories = prefs_result.get("preferences", {}).get("categories", [])
        _get_user_data_summary__ensure_message_files(user_id, categories)
        message_files = get_user_message_files(user_id)
        _get_user_data_summary__process_enabled_message_files(
            user_id, categories, summary
        )
        _get_user_data_summary__process_orphaned_message_files(
            user_id, categories, message_files, summary
        )
    except Exception as e:
        logger.error(f"Error processing message files for user data summary: {e}")


# not_duplicate: user_data_summary_adders
@handle_errors("adding log file info to user data summary")
def _get_user_data_summary__add_log_file_info(
    log_file: str, log_type: str, summary: dict[str, Any]
) -> None:
    """Add log file information to the summary."""
    try:
        size = os.path.getsize(log_file)
        data = load_json_data(log_file)
        entry_count = len(data) if isinstance(data, list) else 0
        summary["logs"][log_type] = {
            "exists": True,
            "size": size,
            "entry_count": entry_count,
        }
        summary["total_files"] += 1
        summary["total_size_bytes"] += size
    except Exception as e:
        logger.error(f"Error adding log file info to user data summary: {e}")


# not_duplicate: user_data_summary_process_phases
@handle_errors("processing log files for user data summary")
def _get_user_data_summary__process_log_files(
    user_id: str, summary: dict[str, Any]
) -> None:
    """Process log files (checkins, chat_interactions)."""
    try:
        _get_user_data_summary__process_file_types_with_adder(
            user_id,
            summary,
            ["checkins", "chat_interactions"],
            _get_user_data_summary__add_log_file_info,
        )
    except Exception as e:
        logger.error(f"Error processing log files for user data summary: {e}")


@handle_errors("getting last interaction", default_return="1970-01-01 00:00:00")
def _get_last_interaction(user_id: str) -> str:
    """Return ISO timestamp of last interaction, or a default if none found."""
    try:
        try:
            from checkins.checkin_data_manager import get_recent_checkins

            recent_checkins = get_recent_checkins(user_id, limit=1)
            if recent_checkins:
                ts = checkin_runtime_timestamp(recent_checkins[0])
                if ts:
                    return ts
        except Exception as e:
            logger.warning(f"Error getting recent check-ins for user {user_id}: {e}")

        try:
            from core.response_tracking import get_recent_responses

            recent_chats = get_recent_responses(user_id, "chat_interaction", limit=1)
            if recent_chats:
                ts = recent_chats[0].get("timestamp")
                return str(ts).strip() if ts else "1970-01-01 00:00:00"
        except Exception as e:
            logger.warning(
                f"Error getting recent chat interactions for user {user_id}: {e}"
            )

        try:
            recent_deliveries = get_recent_messages(user_id, category=None, limit=1)
            if recent_deliveries:
                d0 = recent_deliveries[0]
                sa = str(d0.get("sent_at") or "").strip()
                if sa:
                    return sa
        except Exception as e:
            logger.warning(
                f"Error getting recent sent messages for user {user_id}: {e}"
            )

        user_data_result = get_user_data(user_id, "account")
        user_account = user_data_result.get("account") or {}
        return user_account.get("created_at", "1970-01-01 00:00:00")

    except Exception as e:
        logger.warning(f"Error getting last interaction for user {user_id}: {e}")
        return "1970-01-01 00:00:00"


# not_duplicate: user_data_manager_api
@handle_errors(
    "getting user data summary", default_return={"error": "Failed to get summary"}
)
def get_user_data_summary(user_id: str) -> dict[str, Any]:
    """Get a comprehensive summary of user data including file counts and sizes."""
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return {"error": f"Invalid user_id: {user_id}"}

    if not user_id.strip():
        logger.error("Empty user_id provided")
        return {"error": "Empty user_id provided"}

    summary = _get_user_data_summary__initialize_summary(user_id)
    user_dir = get_user_data_dir(user_id)
    if os.path.exists(user_dir):
        _get_user_data_summary__process_core_files(user_id, summary)
    _get_user_data_summary__process_message_files(user_id, summary)
    _get_user_data_summary__process_log_files(user_id, summary)
    return summary


# not_duplicate: user_data_manager_api
@handle_errors("getting user summary", default_return={})
def get_user_summary(user_id: str) -> dict[str, Any]:
    """Get a summary of user data and message statistics."""
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return {}

    if not user_id.strip():
        logger.error("Empty user_id provided")
        return {}

    try:
        user_info = get_user_info_for_data_manager(user_id)
        if not user_info:
            return {}

        categories = _get_user_categories(user_id)
        message_stats = {}
        total_messages = 0

        for category in categories:
            category_path = str(
                Path(get_user_data_dir(user_id)) / "messages" / f"{category}.json"
            )
            if os.path.exists(category_path):
                try:
                    with open(category_path, encoding="utf-8") as f:
                        data = json.load(f)
                        if (
                            not isinstance(data, dict)
                            or data.get("schema_version") != SCHEMA_VERSION
                        ):
                            logger.warning(
                                f"Skipping non-v2 message template file for summary: {category_path}"
                            )
                            message_stats[category] = 0
                            continue
                        normalized, errors = validate_v2_document("messages", data)
                        if errors:
                            logger.warning(
                                f"Validation issues in {category_path}: {'; '.join(errors)}"
                            )
                        message_count = len(normalized.get("messages", []))
                        message_stats[category] = message_count
                        total_messages += message_count
                except Exception as e:
                    logger.warning(f"Error reading message file {category_path}: {e}")
                    message_stats[category] = 0
            else:
                message_stats[category] = 0

        return {
            "user_id": user_id,
            "internal_username": user_info.get("internal_username", ""),
            "preferred_name": user_info.get("preferred_name", ""),
            "active": user_info.get("active", False),
            "categories": categories,
            "message_stats": message_stats,
            "total_messages": total_messages,
            "last_updated": now_timestamp_full(),
        }

    except Exception as e:
        logger.error(f"Error getting user summary for {user_id}: {e}")
        return {}


@handle_errors("getting all user summaries", default_return=[])
def get_all_user_summaries() -> list[dict[str, Any]]:
    """Get summaries for all users."""
    try:
        user_ids = get_all_user_ids()
        summaries = []
        for user_id in user_ids:
            try:
                summary = get_user_summary(user_id)
                if summary:
                    summaries.append(summary)
            except Exception as e:
                logger.error(f"Error getting summary for user {user_id}: {e}")
                continue
        return summaries
    except Exception as e:
        logger.error(f"Error getting all user summaries: {e}")
        return []


# not_duplicate: user_data_manager_api
@handle_errors(
    "getting user analytics summary",
    default_return={"error": "Failed to get analytics summary"},
)
def get_user_analytics_summary(user_id: str) -> dict[str, Any]:
    """Get an analytics summary including interaction patterns and data usage."""
    try:
        summary = get_user_summary(user_id)
        if not summary:
            return {"error": "User not found"}

        analytics = {
            "user_id": user_id,
            "data_summary": summary,
            "interaction_patterns": {},
            "data_usage": {},
            "recommendations": [],
        }

        interaction_sources = [
            ("sent_messages", "Message Interactions"),
            ("checkins", "Check-in Activity"),
            ("chat_interactions", "Chat Activity"),
        ]

        for source, _label in interaction_sources:
            file_path = get_user_file_path(user_id, source)
            if not os.path.exists(file_path):
                continue
            raw = load_json_data(file_path)
            if raw is None:
                continue
            count = 0
            last_ix = "None"

            if source == "checkins":
                if isinstance(raw, dict) and raw.get("schema_version") == SCHEMA_VERSION:
                    arr = raw.get("checkins") or []
                    if isinstance(arr, list):
                        count = len(arr)
                        if arr and isinstance(arr[-1], dict):
                            last_ix = checkin_runtime_timestamp(arr[-1]) or "Unknown"
                elif isinstance(raw, list):
                    count = len(raw)
                    if raw and isinstance(raw[-1], dict):
                        last_ix = checkin_runtime_timestamp(raw[-1]) or "Unknown"

            elif source == "sent_messages":
                count = 0
                if isinstance(raw, dict) and raw.get("schema_version") == SCHEMA_VERSION:
                    arr = raw.get("deliveries") or []
                    if isinstance(arr, list):
                        count = len(arr)
                        if arr and isinstance(arr[0], dict):
                            sa = arr[0].get("sent_at")
                            last_ix = str(sa).strip() if sa else "Unknown"
                if last_ix == "None" and count:
                    recent = get_recent_messages(user_id, category=None, limit=1)
                    if recent and isinstance(recent[0], dict):
                        sa = recent[0].get("sent_at")
                        last_ix = str(sa).strip() if sa else "Unknown"

            elif source == "chat_interactions" and isinstance(raw, list):
                count = len(raw)
                if raw and isinstance(raw[-1], dict):
                    last_ix = str(raw[-1].get("timestamp") or "Unknown")

            analytics["interaction_patterns"][source] = {
                "count": count,
                "last_interaction": last_ix,
                "frequency": (
                    "High" if count > 10 else "Medium" if count > 5 else "Low"
                ),
            }

        if analytics["interaction_patterns"].get("checkins", {}).get("count", 0) < 3:
            analytics["recommendations"].append(
                "Consider enabling check-ins for better engagement"
            )
        if (
            analytics["interaction_patterns"]
            .get("chat_interactions", {})
            .get("count", 0)
            < 5
        ):
            analytics["recommendations"].append(
                "Try using the chat feature for personalized interactions"
            )

        return analytics

    except Exception as e:
        logger.error(f"Error getting analytics summary for user {user_id}: {e}")
        return {"error": f"Failed to get analytics: {str(e)}"}
