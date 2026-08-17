#!/usr/bin/env python3
"""
User data operations facade — backup, export, indexing, analytics summaries.

Implementation lives in:
- ``user_data_user_info`` (user-info leaf)
- ``user_data_summaries``
- ``user_data_index``
- ``user_data_backup``

For ``get_user_data`` / ``save_user_data`` see ``user_data_read`` / ``user_data_write``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from core.config import BASE_DATA_DIR, get_backups_dir
from core.error_handling import handle_errors
from core.logger import get_component_logger
from storage.user_data_backup import (
    backup_user_data,
    delete_user_completely,
    export_user_data,
)
from storage.user_data_index import (
    build_user_index,
    rebuild_full_index,
    rebuild_user_index,
    remove_from_index,
    search_users,
    update_user_index,
)
from storage.user_data_summaries import (
    _get_last_interaction,
    get_all_user_summaries,
    get_user_analytics_summary,
    get_user_data_summary,
    get_user_summary,
)
from storage.user_data_user_info import (
    _get_user_categories,
    get_user_info_for_data_manager,
    get_user_message_files,
    update_message_references,
)

logger = get_component_logger("main")


class UserDataManager:
    """Ops/admin facade for backup, export, index, and summaries."""

    @handle_errors("initializing user data manager", default_return=None)
    def __init__(self):
        """Set backup directory and index file path for the current BASE_DATA_DIR."""
        try:
            self.index_file = str(Path(BASE_DATA_DIR) / "user_index.json")
            self.backup_dir = get_backups_dir()
            os.makedirs(self.backup_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Error initializing user data manager: {e}")
            raise

    @handle_errors("updating message references", default_return=False)
    def update_message_references(self, user_id: str) -> bool:
        return update_message_references(user_id)

    @handle_errors("getting user message files", default_return={})
    def get_user_message_files(self, user_id: str) -> dict[str, str]:
        return get_user_message_files(user_id)

    # not_duplicate: user_data_manager_api
    @handle_errors("backing up user data", default_return="")
    def backup_user_data(self, user_id: str, include_messages: bool = True) -> str:
        return backup_user_data(
            user_id, include_messages=include_messages, backup_dir=self.backup_dir
        )

    # not_duplicate: user_data_manager_api
    @handle_errors("exporting user data", default_return={})
    def export_user_data(
        self, user_id: str, export_format: str = "json"
    ) -> dict[str, Any]:
        return export_user_data(user_id, export_format)

    # not_duplicate: delete_user_completely
    @handle_errors("deleting user completely", default_return=False)
    def delete_user_completely(self, user_id: str, create_backup: bool = True) -> bool:
        return delete_user_completely(
            user_id,
            create_backup=create_backup,
            backup_dir=self.backup_dir,
            index_file=self.index_file,
        )

    # not_duplicate: user_data_manager_api
    @handle_errors(
        "getting user data summary", default_return={"error": "Failed to get summary"}
    )
    def get_user_data_summary(self, user_id: str) -> dict[str, Any]:
        return get_user_data_summary(user_id)

    @handle_errors("getting last interaction", default_return="1970-01-01 00:00:00")
    def _get_last_interaction(self, user_id: str) -> str:
        return _get_last_interaction(user_id)

    # not_duplicate: update_user_index
    @handle_errors("updating user index", default_return=False)
    def update_user_index(self, user_id: str) -> bool:
        return update_user_index(user_id, index_file=self.index_file)

    @handle_errors("removing from index", default_return=False)
    def remove_from_index(self, user_id: str) -> bool:
        return remove_from_index(user_id, index_file=self.index_file)

    @handle_errors("rebuilding full index", default_return=False)
    def rebuild_full_index(self) -> bool:
        return rebuild_full_index(index_file=self.index_file)

    @handle_errors("searching users", default_return=[])
    def search_users(
        self, query: str, search_fields: list[str] | None = None
    ) -> list[dict[str, Any]]:
        return search_users(query, search_fields)


user_data_manager = UserDataManager()


__all__ = [
    "UserDataManager",
    "user_data_manager",
    "_get_user_categories",
    "backup_user_data",
    "build_user_index",
    "delete_user_completely",
    "export_user_data",
    "get_all_user_summaries",
    "get_user_analytics_summary",
    "get_user_data_summary",
    "get_user_info_for_data_manager",
    "get_user_message_files",
    "get_user_summary",
    "rebuild_full_index",
    "rebuild_user_index",
    "remove_from_index",
    "search_users",
    "update_message_references",
    "update_user_index",
]
