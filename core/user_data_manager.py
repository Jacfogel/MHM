#!/usr/bin/env python3
"""
User Data Manager - Enhanced utilities for user-centric operations
Provides tools for message references, backup, export, and indexing
"""

import os
import json
import shutil
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from core.logger import get_component_logger
from core.config import (
    get_user_file_path, get_user_data_dir, BASE_DATA_DIR, get_backups_dir
)
from core.file_operations import load_json_data, save_json_data, get_user_file_path, get_user_data_dir
from core.user_data_handlers import get_user_data
from core.user_data_handlers import get_all_user_ids
from core.error_handling import handle_errors

logger = get_component_logger('main')
data_manager_logger = get_component_logger('user_activity')

class UserDataManager:
    """Enhanced user data management with references, backup, and indexing capabilities"""
    
    @handle_errors("initializing user data manager", default_return=None)
    def __init__(self):
        """
        Initialize the UserDataManager.
        
        Sets up backup directory and index file path for user data management operations.
        """
        try:
            # Read BASE_DATA_DIR dynamically to support test isolation
            from core.config import BASE_DATA_DIR as current_base_dir
            self.index_file = str(Path(current_base_dir) / "user_index.json")
            # Redirect backups under tests/data when in test mode
            self.backup_dir = get_backups_dir()
            os.makedirs(self.backup_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Error initializing user data manager: {e}")
            raise
    
    @handle_errors("updating message references", default_return=False)
    def update_message_references(self, user_id: str) -> bool:
        """Add/update message file references in user profile"""
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return False
            
        if not user_id.strip():
            logger.error("Empty user_id provided")
            return False
        
        # Check if user directory exists (prevents auto-creation by get_user_info_for_data_manager)
        user_dir = get_user_data_dir(user_id)
        if not os.path.exists(user_dir):
            logger.error(f"User {user_id} not found: user directory does not exist")
            return False
        
        # Load user profile
        # Retry in case of race conditions with file writes in parallel execution
        import time
        user_info = None
        for attempt in range(3):
            user_info = get_user_info_for_data_manager(user_id)
            if user_info:
                break
            if attempt < 2:
                time.sleep(0.1)  # Brief delay before retry
        
        if not user_info:
            logger.error(f"User {user_id} not found after retries")
            return False
        
        # Check if automated messages are enabled
        # Retry in case of race conditions
        account_result = None
        account_data = {}
        for attempt in range(3):
            account_result = get_user_data(user_id, 'account')
            account_data = account_result.get('account', {})
            if account_data:
                break
            if attempt < 2:
                time.sleep(0.1)  # Brief delay before retry
        
        features = account_data.get('features', {})
        automated_messages_enabled = features.get('automated_messages', 'disabled') == 'enabled'
        
        # Get user's categories
        # Retry in case of race conditions
        prefs_result = None
        categories = []
        for attempt in range(3):
            prefs_result = get_user_data(user_id, 'preferences')
            categories = prefs_result.get('preferences', {}).get('categories', [])
            if categories or attempt == 2:  # Accept empty categories on last attempt
                break
            if attempt < 2:
                time.sleep(0.1)  # Brief delay before retry
        if not categories:
            if automated_messages_enabled:
                logger.warning(f"No categories found for user {user_id} (automated messages enabled)")
            else:
                logger.debug(f"No categories found for user {user_id} (automated messages disabled)")
            return True
        
        # Build message references
        message_refs = {}
        for category in categories:
            message_file = str(Path(get_user_data_dir(user_id)) / 'messages' / f"{category}.json")
            if os.path.exists(message_file):
                message_refs[category] = {
                    "path": message_file,
                    "exists": True,
                    "last_modified": os.path.getmtime(message_file)
                }
            else:
                message_refs[category] = {
                    "path": message_file,
                    "exists": False,
                    "last_modified": None
                }
        
        # Log the message references but don't save to profile.json (legacy file)
        logger.info(f"Updated message references for user {user_id}: {list(message_refs.keys())}")
        return True
    
    @handle_errors("getting user message files", default_return={})
    def get_user_message_files(self, user_id: str) -> Dict[str, str]:
        """Get all message file paths for a user"""
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return {}
            
        if not user_id.strip():
            logger.error("Empty user_id provided")
            return {}
        
        user_info = get_user_info_for_data_manager(user_id)
        if not user_info:
            return {}
        
        # Check if we have cached references
        if "message_files" in user_info:
            return {cat: info["path"] for cat, info in user_info["message_files"].items() if info["exists"]}
        
        # Fallback: build from categories
        prefs_result = get_user_data(user_id, 'preferences')
        categories = prefs_result.get('preferences', {}).get('categories', [])
        if not categories:
            return {}
        
        message_files = {}
        for category in categories:
            message_file = str(Path(get_user_data_dir(user_id)) / 'messages' / f"{category}.json")
            if os.path.exists(message_file):
                message_files[category] = message_file
        
        return message_files
    
    @handle_errors("backing up user data", default_return="")
    def backup_user_data(self, user_id: str, include_messages: bool = True) -> str:
        """
        Create a complete backup of user's data with validation.
        
        Returns:
            str: Path to backup file, empty string if failed
        """
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return ""
            
        if not user_id.strip():
            logger.error("Empty user_id provided")
            return ""
            
        # Validate include_messages
        if not isinstance(include_messages, bool):
            logger.error(f"Invalid include_messages: {include_messages}")
            return ""
        """Create a complete backup of user's data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"user_backup_{user_id}_{timestamp}.zip"
            backup_path = str(Path(self.backup_dir) / backup_filename)
            
            # Ensure backup directory exists
            Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup user directory (profile, preferences, schedules, etc.)
                user_dir = Path(get_user_data_dir(user_id))
                if user_dir.exists():
                    for file_path in user_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = os.path.relpath(str(file_path), BASE_DATA_DIR)
                            zipf.write(str(file_path), arcname)
                
                # Backup message files if requested
                if include_messages:
                    message_files = self.get_user_message_files(user_id)
                    for category, file_path in message_files.items():
                        if os.path.exists(file_path):
                            arcname = os.path.relpath(file_path, BASE_DATA_DIR)
                            zipf.write(file_path, arcname)
                
                # Add metadata
                metadata = {
                    "user_id": user_id,
                    "backup_date": datetime.now().isoformat(),
                    "backup_type": "complete",
                    "includes_messages": include_messages,
                    "files_backed_up": zipf.namelist()
                }
                zipf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
            
            logger.info(f"User backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Error creating backup for user {user_id}: {e}")
            return ""
    
    @handle_errors("exporting user data", default_return={})
    def export_user_data(self, user_id: str, export_format: str = "json") -> Dict[str, Any]:
        """
        Export all user data to a structured format with validation.
        
        Returns:
            Dict[str, Any]: Exported data, empty dict if failed
        """
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return {}
            
        if not user_id.strip():
            logger.error("Empty user_id provided")
            return {}
            
        # Validate export_format
        if not export_format or not isinstance(export_format, str):
            logger.error(f"Invalid export_format: {export_format}")
            return {}
            
        if export_format not in ["json", "csv", "yaml"]:
            logger.error(f"Unsupported export_format: {export_format}")
            return {}
        """Export all user data to a structured format"""
        export_data = {
            "user_id": user_id,
            "export_date": datetime.now().isoformat(),
            "profile": {},
            "preferences": {},
            "schedules": {},
            "messages": {},
            "sent_messages": {},
            "logs": {}
        }
        
        # Export profile data
        user_info = get_user_info_for_data_manager(user_id)
        if user_info:
            export_data["profile"] = user_info
        
        # Export preferences
        prefs_file = get_user_file_path(user_id, 'preferences')
        if os.path.exists(prefs_file):
            export_data["preferences"] = load_json_data(prefs_file) or {}
        
        # Export schedules
        schedules_file = get_user_file_path(user_id, 'schedules')
        if os.path.exists(schedules_file):
            export_data["schedules"] = load_json_data(schedules_file) or {}
        
        # Export messages
        message_files = self.get_user_message_files(user_id)
        for category, file_path in message_files.items():
            if os.path.exists(file_path):
                export_data["messages"][category] = load_json_data(file_path) or {}
        
        # Export sent messages
        sent_file = get_user_file_path(user_id, 'sent_messages')
        if os.path.exists(sent_file):
            export_data["sent_messages"] = load_json_data(sent_file) or {}
        
        # Export logs
        log_types = ["checkins", "chat_interactions"]
        for log_type in log_types:
            log_file = get_user_file_path(user_id, log_type)
            if os.path.exists(log_file):
                export_data["logs"][log_type] = load_json_data(log_file) or []
        
        logger.info(f"User data exported for user {user_id}")
        return export_data
    
    @handle_errors("deleting user completely", default_return=False)
    def delete_user_completely(self, user_id: str, create_backup: bool = True) -> bool:
        """
        Completely remove all traces of a user from the system with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return False
            
        if not user_id.strip():
            logger.error("Empty user_id provided")
            return False
            
        # Validate create_backup
        if not isinstance(create_backup, bool):
            logger.error(f"Invalid create_backup: {create_backup}")
            return False
        
        if create_backup:
            backup_path = self.backup_user_data(user_id, include_messages=True)
            if backup_path:
                logger.info(f"Backup created before deletion: {backup_path}")
        
        # Delete user directory
        user_dir = get_user_data_dir(user_id)
        if os.path.exists(user_dir):
            try:
                shutil.rmtree(user_dir)
                logger.info(f"Deleted user directory: {user_dir}")
            except Exception as e:
                logger.warning(f"Error deleting user directory {user_dir}: {e}")
                # Continue with other cleanup steps
        
        # Delete message files
        try:
            message_files = self.get_user_message_files(user_id)
            for category, file_path in message_files.items():
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted message file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Error deleting message file {file_path}: {e}")
        except Exception as e:
            logger.warning(f"Error getting message files for user {user_id}: {e}")
        
        # Update user index (remove from index even if directory doesn't exist)
        try:
            self.remove_from_index(user_id)
        except Exception as e:
            logger.warning(f"Error removing user {user_id} from index: {e}")
        
        logger.info(f"User {user_id} completely removed from system")
        return True
    
    @handle_errors("getting user data summary", default_return={"error": "Failed to get summary"})
    def get_user_data_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive summary of user data with validation.
        
        Returns:
            Dict[str, Any]: User data summary, error dict if failed
        """
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return {"error": f"Invalid user_id: {user_id}"}
            
        if not user_id.strip():
            logger.error("Empty user_id provided")
            return {"error": "Empty user_id provided"}
        """
        Get a comprehensive summary of user data including file counts and sizes.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dict containing summary information about the user's data
        """
        summary = self._get_user_data_summary__initialize_summary(user_id)
        
        # Check user directory files
        user_dir = get_user_data_dir(user_id)
        if os.path.exists(user_dir):
            self._get_user_data_summary__process_core_files(user_id, summary)
        
        # Process message files
        self._get_user_data_summary__process_message_files(user_id, summary)
        
        # Process log files
        self._get_user_data_summary__process_log_files(user_id, summary)
        
        return summary

    @handle_errors("initializing user data summary")
    def _get_user_data_summary__initialize_summary(self, user_id: str) -> Dict[str, Any]:
        """Initialize the summary structure with default values."""
        try:
            return {
                "user_id": user_id,
                "files": {},        # generic file-type map, e.g. files['profile']
                "messages": {},     # per-category message file info
                "logs": {},         # per-type log info
                "total_files": 0,
                "total_size_bytes": 0,
                "last_modified": None,
            }
        except Exception as e:
            logger.error(f"Error initializing user data summary: {e}")
            return {"user_id": user_id, "files": {}, "messages": {}, "logs": {}, "total_files": 0, "total_size_bytes": 0, "last_modified": None}

    @handle_errors("processing core files for user data summary")
    def _get_user_data_summary__process_core_files(self, user_id: str, summary: Dict[str, Any]) -> None:
        """Process core user data files (profile, preferences, schedules, etc.)."""
        try:
            from core.user_data_handlers import USER_DATA_LOADERS

            # Build list of core file types dynamically from registered loaders
            dynamic_types = list(USER_DATA_LOADERS.keys()) + ["sent_messages"]

            for file_type in dynamic_types:
                file_path = get_user_file_path(user_id, file_type)
                if os.path.exists(file_path):
                    self._get_user_data_summary__add_file_info(file_path, file_type, summary)
                    self._get_user_data_summary__add_special_file_details(file_path, file_type, summary)
        except Exception as e:
            logger.error(f"Error processing core files for user data summary: {e}")

    @handle_errors("adding file info to user data summary")
    def _get_user_data_summary__add_file_info(self, file_path: str, file_type: str, summary: Dict[str, Any]) -> None:
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

    @handle_errors("adding special file details to user data summary")
    def _get_user_data_summary__add_special_file_details(self, file_path: str, file_type: str, summary: Dict[str, Any]) -> None:
        """Add special details for specific file types (schedules, sent_messages)."""
        try:
            if file_type == "schedules":
                self._get_user_data_summary__add_schedule_details(file_path, summary)
            elif file_type == "sent_messages":
                self._get_user_data_summary__add_sent_messages_details(file_path, summary)
        except Exception as e:
            logger.error(f"Error adding special file details to user data summary: {e}")

    @handle_errors("adding schedule details to user data summary")
    def _get_user_data_summary__add_schedule_details(self, file_path: str, summary: Dict[str, Any]) -> None:
        """Add schedule-specific details to the summary."""
        try:
            data = load_json_data(file_path)
            if data:
                total_periods = sum(len(cat_schedules) for cat_schedules in data.values())
                summary["files"]["schedules"]["periods"] = total_periods
        except Exception as e:
            logger.error(f"Error adding schedule details to user data summary: {e}")

    @handle_errors("adding sent messages details to user data summary")
    def _get_user_data_summary__add_sent_messages_details(self, file_path: str, summary: Dict[str, Any]) -> None:
        """Add sent messages count to the summary."""
        try:
            data = load_json_data(file_path)
            if data:
                total_messages = sum(len(msgs) for msgs in data.values() if isinstance(msgs, list))
                summary["files"]["sent_messages"]["count"] = total_messages
        except Exception as e:
            logger.error(f"Error adding sent messages details to user data summary: {e}")

    @handle_errors("processing message files for user data summary")
    def _get_user_data_summary__process_message_files(self, user_id: str, summary: Dict[str, Any]) -> None:
        """Process message files for all user categories."""
        try:
            # Get user categories
            prefs_result = get_user_data(user_id, 'preferences')
            categories = prefs_result.get('preferences', {}).get('categories', [])
            
            # Ensure message files exist
            self._get_user_data_summary__ensure_message_files(user_id, categories)
            
            # Get existing message files
            message_files = self.get_user_message_files(user_id)
            
            # Process enabled category message files
            self._get_user_data_summary__process_enabled_message_files(user_id, categories, summary)
            
            # Process orphaned message files
            self._get_user_data_summary__process_orphaned_message_files(user_id, categories, message_files, summary)
        except Exception as e:
            logger.error(f"Error processing message files for user data summary: {e}")

    @handle_errors("ensuring message files for user data summary")
    def _get_user_data_summary__ensure_message_files(self, user_id: str, categories: List[str]) -> None:
        """Ensure message files exist for all user categories."""
        try:
            if not categories:
                return
                
            from core.message_management import ensure_user_message_files
            # This will check which files are missing and create them
            result = ensure_user_message_files(user_id, categories)
            if result["success"]:
                logger.info(f"Message files validation for user {user_id}: checked {result['files_checked']} categories, created {result['files_created']} files, directory_created={result['directory_created']}")
            else:
                logger.warning(f"Message files validation for user {user_id}: checked {result['files_checked']} categories, created {result['files_created']} files, some failures occurred")
        except Exception as e:
            logger.error(f"Error ensuring message files during validation for user {user_id}: {e}")

    @handle_errors("processing enabled message files for user data summary")
    def _get_user_data_summary__process_enabled_message_files(self, user_id: str, categories: List[str], summary: Dict[str, Any]) -> None:
        """Process message files for enabled categories."""
        try:
            for category in categories:
                file_path = str(Path(get_user_data_dir(user_id)) / 'messages' / f"{category}.json")
                
                if os.path.exists(file_path):
                    self._get_user_data_summary__add_message_file_info(file_path, category, summary, orphaned=False)
                else:
                    self._get_user_data_summary__add_missing_message_file_info(file_path, category, summary, user_id)
        except Exception as e:
            logger.error(f"Error processing enabled message files for user data summary: {e}")

    @handle_errors("processing orphaned message files for user data summary")
    def _get_user_data_summary__process_orphaned_message_files(self, user_id: str, categories: List[str], message_files: Dict[str, str], summary: Dict[str, Any]) -> None:
        """Process orphaned message files (categories not enabled but files exist)."""
        try:
            for category, file_path in message_files.items():
                if category not in categories and os.path.exists(file_path):
                    self._get_user_data_summary__add_message_file_info(file_path, category, summary, orphaned=True)
        except Exception as e:
            logger.error(f"Error processing orphaned message files for user data summary: {e}")

    @handle_errors("adding message file info to user data summary")
    def _get_user_data_summary__add_message_file_info(self, file_path: str, category: str, summary: Dict[str, Any], orphaned: bool = False) -> None:
        """Add message file information to the summary."""
        try:
            size = os.path.getsize(file_path)
            data = load_json_data(file_path)
            message_count = len(data.get("messages", [])) if data else 0
            
            message_info = {
                "exists": True,
                "size": size,
                "message_count": message_count,
                "path": file_path
            }
            
            if orphaned:
                message_info["orphaned"] = True  # Mark as orphaned for potential cleanup
                
            summary["messages"][category] = message_info
            summary["total_files"] += 1
            summary["total_size_bytes"] += size
        except Exception as e:
            logger.error(f"Error adding message file info to user data summary: {e}")

    @handle_errors("adding missing message file info to user data summary")
    def _get_user_data_summary__add_missing_message_file_info(self, file_path: str, category: str, summary: Dict[str, Any], user_id: str) -> None:
        """Add information for missing message files."""
        try:
            summary["messages"][category] = {
                "exists": False,
                "size": 0,
                "message_count": 0,
                "path": file_path,
                "creation_failed": True
            }
            logger.warning(f"Message file for category {category} still missing after ensure_user_message_files for user {user_id}")
        except Exception as e:
            logger.error(f"Error adding missing message file info to user data summary: {e}")

    @handle_errors("processing log files for user data summary")
    def _get_user_data_summary__process_log_files(self, user_id: str, summary: Dict[str, Any]) -> None:
        """Process log files (checkins, chat_interactions)."""
        try:
            log_types = ["checkins", "chat_interactions"]
            for log_type in log_types:
                log_file = get_user_file_path(user_id, log_type)
                if os.path.exists(log_file):
                    self._get_user_data_summary__add_log_file_info(log_file, log_type, summary)
        except Exception as e:
            logger.error(f"Error processing log files for user data summary: {e}")

    @handle_errors("adding log file info to user data summary")
    def _get_user_data_summary__add_log_file_info(self, log_file: str, log_type: str, summary: Dict[str, Any]) -> None:
        """Add log file information to the summary."""
        try:
            size = os.path.getsize(log_file)
            data = load_json_data(log_file)
            entry_count = len(data) if isinstance(data, list) else 0
            
            summary["logs"][log_type] = {
                "exists": True,
                "size": size,
                "entry_count": entry_count
            }
            summary["total_files"] += 1
            summary["total_size_bytes"] += size
        except Exception as e:
            logger.error(f"Error adding log file info to user data summary: {e}")
    
    @handle_errors("getting last interaction", default_return="1970-01-01 00:00:00")
    def _get_last_interaction(self, user_id: str) -> str:
        """
        Get the timestamp of the user's last interaction with the system.
        
        Args:
            user_id: The user's ID
            
        Returns:
            str: ISO format timestamp of last interaction, or default if none found
        """
        try:
            # Check recent check-ins
            try:
                from core.response_tracking import get_recent_checkins
                recent_checkins = get_recent_checkins(user_id, limit=1)
                if recent_checkins:
                    return recent_checkins[0].get('timestamp', '1970-01-01 00:00:00')
            except Exception as e:
                logger.warning(f"Error getting recent check-ins for user {user_id}: {e}")

            # Check recent chat interactions
            try:
                from core.response_tracking import get_recent_responses
                recent_chats = get_recent_responses(user_id, 'chat_interaction', limit=1)
                if recent_chats:
                    return recent_chats[0].get('timestamp', '1970-01-01 00:00:00')
            except Exception as e:
                logger.warning(f"Error getting recent chat interactions for user {user_id}: {e}")

            # Check sent messages
            sent_file = get_user_file_path(user_id, 'sent_messages')
            if os.path.exists(sent_file):
                sent_data = load_json_data(sent_file) or {}
                all_messages = []
                for category_messages in sent_data.values():
                    if isinstance(category_messages, list):
                        all_messages.extend(category_messages)
                
                if all_messages:
                    # Sort by timestamp and get the most recent
                    sorted_messages = sorted(
                        all_messages,
                        key=lambda x: x.get('timestamp', '1970-01-01 00:00:00'),
                        reverse=True
                    )
                    return sorted_messages[0].get('timestamp', '1970-01-01 00:00:00')
            
            # Fallback to account creation date
            user_data_result = get_user_data(user_id, 'account')
            user_account = user_data_result.get('account') or {}
            return user_account.get('created_at', '1970-01-01 00:00:00')
                
        except Exception as e:
            logger.warning(f"Error getting last interaction for user {user_id}: {e}")
            return '1970-01-01 00:00:00'
    
    @handle_errors("updating user index", default_return=False)
    def update_user_index(self, user_id: str) -> bool:
        """
        Update user index with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return False
            
        if not user_id.strip():
            logger.error("Empty user_id provided")
            return False
        """
        Update the user index with current information for a specific user.
        
        Creates flat lookup mappings for fast O(1) user lookups:
        - {"internal_username": "UUID", "email:email": "UUID", "discord:discord_id": "UUID", "phone:phone": "UUID"}
        
        All detailed user data is stored in account.json, not duplicated in the index.
        
        Args:
            user_id: The user's ID (UUID)
            
        Returns:
            bool: True if index was updated successfully
        """
        try:
            # Use file locking for user_index.json to prevent race conditions in parallel execution
            from core.file_locking import safe_json_read, safe_json_write
            
            # Load existing index with file locking
            index_data = safe_json_read(self.index_file, default={"last_updated": None})
            
            # Get user account for identifiers
            # Retry in case of race conditions in parallel execution (e.g., account file just created)
            user_data_result = None
            user_account = {}
            max_retries = 5  # Increased from 3 to handle parallel test execution
            retry_delay = 0.2  # Increased from 0.1s to 0.2s for better reliability
            import time
            
            for attempt in range(max_retries):
                try:
                    user_data_result = get_user_data(user_id, 'account')
                    user_account = user_data_result.get('account') or {}
                    if user_account and user_account.get('internal_username'):
                        break
                except Exception as e:
                    logger.debug(f"Attempt {attempt + 1}/{max_retries} to get account data for {user_id} failed: {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            
            # Get identifiers for fast lookups
            internal_username = user_account.get('internal_username', '')
            email = user_account.get('email', '')
            discord_user_id = user_account.get('discord_user_id', '')
            phone = user_account.get('phone', '')
            
            if not internal_username:
                logger.warning(f"No internal_username found for user {user_id} after {max_retries} attempts (account keys: {list(user_account.keys())})")
                return False
            
            # Update flat lookup mappings for fast O(1) user ID resolution
            # Each identifier type maps directly to UUID for instant lookup
            # Simple username mapping (most common lookup)
            if internal_username not in index_data or index_data[internal_username] == user_id:
                index_data[internal_username] = user_id
            
            # Prefixed identifier mappings for contact methods
            if email:
                index_data[f"email:{email}"] = user_id
            if discord_user_id:
                index_data[f"discord:{discord_user_id}"] = user_id
            if phone:
                index_data[f"phone:{phone}"] = user_id
            
            # Add metadata
            index_data["last_updated"] = datetime.now().isoformat()
            
            # Save updated index with file locking
            # Retry write operation in case of temporary lock contention
            max_write_retries = 3
            write_retry_delay = 0.15
            for write_attempt in range(max_write_retries):
                if safe_json_write(self.index_file, index_data, indent=4):
                    logger.debug(f"Updated user index for user {user_id} (internal_username: {internal_username})")
                    return True
                if write_attempt < max_write_retries - 1:
                    logger.debug(f"Write attempt {write_attempt + 1}/{max_write_retries} failed for {user_id}, retrying...")
                    time.sleep(write_retry_delay)
            
            logger.error(f"Failed to save user index for user {user_id} after {max_write_retries} attempts")
            return False
        except Exception as e:
            logger.error(f"Error updating user index for user {user_id}: {e}")
            return False
    
    @handle_errors("removing from index", default_return=False)
    def remove_from_index(self, user_id: str) -> bool:
        """
        Remove user from index with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return False
            
        if not user_id.strip():
            logger.error("Empty user_id provided")
            return False
        """
        Remove a user from the index.
        
        Removes all identifier mappings (internal_username, email, discord_user_id, phone).
        
        Args:
            user_id: The user's ID (UUID)
            
        Returns:
            bool: True if user was removed from index successfully
        """
        try:
            # Use file locking for user_index.json to prevent race conditions in parallel execution
            from core.file_locking import safe_json_read, safe_json_write
            
            # Load existing index with file locking
            index_data = safe_json_read(self.index_file, default={"last_updated": None})
            
            # Get the user info from account.json to find all identifier mappings
            user_data_result = get_user_data(user_id, 'account')
            user_account = user_data_result.get('account') or {}
            
            internal_username = user_account.get('internal_username')
            email = user_account.get('email')
            discord_user_id = user_account.get('discord_user_id')
            phone = user_account.get('phone')
            
            # Remove all identifier mappings
            if internal_username and internal_username in index_data:
                del index_data[internal_username]
            
            if email and f"email:{email}" in index_data:
                del index_data[f"email:{email}"]
            
            if discord_user_id and f"discord:{discord_user_id}" in index_data:
                del index_data[f"discord:{discord_user_id}"]
            
            if phone and f"phone:{phone}" in index_data:
                del index_data[f"phone:{phone}"]
            
            # Update metadata
            index_data["last_updated"] = datetime.now().isoformat()
            
            # Save updated index with file locking
            if not safe_json_write(self.index_file, index_data, indent=4):
                logger.error(f"Failed to save user index after removing user {user_id}")
                return False
            
            logger.info(f"Removed user {user_id} (internal_username: {internal_username}) from index")
            return True
            
        except Exception as e:
            logger.error(f"Error removing user {user_id} from index: {e}")
            return False
    
    @handle_errors("rebuilding full index", default_return=False)
    def rebuild_full_index(self) -> bool:
        """
        Rebuild full user index with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        """
        Rebuild the complete user index from scratch.
        
        Creates flat lookup mappings for fast O(1) user lookups:
        - {"internal_username": "UUID", "email:email": "UUID", "discord:discord_id": "UUID", "phone:phone": "UUID"}
        
        All detailed user data is stored in account.json, not duplicated in the index.
        
        Returns:
            bool: True if index was rebuilt successfully
        """
        try:
            logger.info("Starting full user index rebuild...")
            
            # Get all user IDs
            user_ids = get_all_user_ids()
            if not user_ids:
                logger.warning("No users found during index rebuild")
                # Return True for empty case - this is a valid state
                return True

            # Use file locking for user_index.json to prevent race conditions in parallel execution
            from core.file_locking import safe_json_write
            import time
            
            # Initialize flat lookup structure
            index_data = {
                "last_updated": datetime.now().isoformat()
            }
            
            # Track successful and failed user indexings
            successful_count = 0
            failed_count = 0
            max_retries = 3
            retry_delay = 0.2
            
            for user_id in user_ids:
                if not user_id:
                    continue
                    
                # Get user account for identifiers with retries for race conditions
                user_account = {}
                for attempt in range(max_retries):
                    try:
                        user_data_result = get_user_data(user_id, 'account')
                        user_account = user_data_result.get('account') or {}
                        if user_account and user_account.get('internal_username'):
                            break
                    except Exception as e:
                        logger.debug(f"Attempt {attempt + 1}/{max_retries} to get account data for {user_id} during rebuild failed: {e}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                
                # Get identifiers for fast lookups (outside retry loop)
                internal_username = user_account.get('internal_username', '')
                email = user_account.get('email', '')
                discord_user_id = user_account.get('discord_user_id', '')
                phone = user_account.get('phone', '')
                
                if not internal_username:
                    logger.warning(f"No internal_username found for user {user_id} after {max_retries} attempts, skipping")
                    failed_count += 1
                    continue
                
                # Add all identifier mappings for fast lookups
                index_data[internal_username] = user_id
                
                # Add prefixed identifier mappings
                if email:
                    index_data[f"email:{email}"] = user_id
                if discord_user_id:
                    index_data[f"discord:{discord_user_id}"] = user_id
                if phone:
                    index_data[f"phone:{phone}"] = user_id
                
                successful_count += 1
            
            # Save rebuilt index with file locking (retry on failure)
            max_write_retries = 3
            write_retry_delay = 0.15
            write_success = False
            for write_attempt in range(max_write_retries):
                if safe_json_write(self.index_file, index_data, indent=4):
                    write_success = True
                    break
                if write_attempt < max_write_retries - 1:
                    logger.debug(f"Write attempt {write_attempt + 1}/{max_write_retries} failed during rebuild, retrying...")
                    time.sleep(write_retry_delay)
            
            if not write_success:
                logger.error("Failed to save rebuilt user index after retries")
                return False
            
            # Rebuild is considered successful if we indexed at least some users
            # (partial success is better than total failure)
            if successful_count > 0:
                logger.info(f"Rebuilt user index with {successful_count} users (skipped {failed_count} users)")
                return True
            elif failed_count > 0:
                # All users failed - this is a real problem
                logger.error(f"Failed to index any users during rebuild ({failed_count} users failed)")
                return False
            else:
                # No users to index (edge case)
                logger.info("Rebuilt user index (no users to index)")
                return True
                
        except Exception as e:
            logger.error(f"Error rebuilding full user index: {e}", exc_info=True)
            return False
    
    @handle_errors("searching users", default_return=[])
    def search_users(self, query: str, search_fields: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search users with validation.
        
        Returns:
            List[Dict[str, Any]]: Search results, empty list if failed
        """
        # Validate query
        if not query or not isinstance(query, str):
            logger.error(f"Invalid query: {query}")
            return []
            
        if not query.strip():
            logger.error("Empty query provided")
            return []
            
        # Validate search_fields
        if search_fields is not None and not isinstance(search_fields, list):
            logger.error(f"Invalid search_fields: {search_fields}")
            return []
        """
        Search for users based on query string and specified fields.
        
        Args:
            query: Search query string
            search_fields: List of fields to search in (default: all fields)
            
        Returns:
            List of user summaries matching the search criteria
        """
        if not query.strip():
            return []
        
        # Get all user IDs
        user_ids = get_all_user_ids()
        if not user_ids:
            return []

        matches = []
        
        # Search through each user's account data
        for user_id in user_ids:
            user_data_result = get_user_data(user_id, 'account')
            user_account = user_data_result.get('account') or {}
            
            # Check if query matches any search fields
            match_found = False
            for field in search_fields:
                field_value = str(user_account.get(field, "")).lower()
                if query.lower() in field_value:
                    match_found = True
                    break
            
            if match_found:
                # Get full user summary for matched users
                user_summary = self.get_user_data_summary(user_id)
                matches.append({
                    "user_id": user_id,
                    "profile": user_account,
                    "summary": user_summary
                })
        
        return matches


# Global instance
user_data_manager = UserDataManager()

# Convenience functions
@handle_errors("updating message references", default_return=False)
def update_message_references(user_id: str) -> bool:
    """
    Update message references with validation.
    
    Returns:
        bool: True if successful, False if failed
    """
    # Validate user_id
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return False
        
    if not user_id.strip():
        logger.error("Empty user_id provided")
        return False
    """
    Update message file references for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        bool: True if references were updated successfully
    """
    try:
        manager = UserDataManager()
        return manager.update_message_references(user_id)
    except Exception as e:
        logger.error(f"Error updating message references: {e}")
        return False

@handle_errors("backing up user data", default_return="")
def backup_user_data(user_id: str, include_messages: bool = True) -> str:
    """
    Create a complete backup of user's data with validation.
    
    Returns:
        str: Path to backup file, empty string if failed
    """
    # Validate user_id
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return ""
        
    if not user_id.strip():
        logger.error("Empty user_id provided")
        return ""
        
    # Validate include_messages
    if not isinstance(include_messages, bool):
        logger.error(f"Invalid include_messages: {include_messages}")
        return ""
    """
    Create a backup of user data.
    
    Args:
        user_id: The user's ID
        include_messages: Whether to include message files in backup
        
    Returns:
        str: Path to the created backup file
    """
    try:
        manager = UserDataManager()
        return manager.backup_user_data(user_id, include_messages)
    except Exception as e:
        logger.error(f"Error backing up user data: {e}")
        return ""

@handle_errors("exporting user data", default_return={})
def export_user_data(user_id: str, export_format: str = "json") -> Dict[str, Any]:
    """
    Export all user data to a structured format with validation.
    
    Returns:
        Dict[str, Any]: Exported data, empty dict if failed
    """
    # Validate user_id
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return {}
        
    if not user_id.strip():
        logger.error("Empty user_id provided")
        return {}
        
    # Validate export_format
    if not export_format or not isinstance(export_format, str):
        logger.error(f"Invalid export_format: {export_format}")
        return {}
        
    if export_format not in ["json", "csv", "yaml"]:
        logger.error(f"Unsupported export_format: {export_format}")
        return {}
    """
    Export user data to a structured format.
    
    Args:
        user_id: The user's ID
        export_format: Format for export (currently only "json" supported)
        
    Returns:
        Dict containing all user data in structured format
    """
    try:
        manager = UserDataManager()
        return manager.export_user_data(user_id, export_format)
    except Exception as e:
        logger.error(f"Error exporting user data: {e}")
        return {}

@handle_errors("deleting user completely", default_return=False)
def delete_user_completely(user_id: str, create_backup: bool = True) -> bool:
    """
    Completely remove all traces of a user from the system with validation.
    
    Returns:
        bool: True if successful, False if failed
    """
    # Validate user_id
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return False
        
    if not user_id.strip():
        logger.error("Empty user_id provided")
        return False
        
    # Validate create_backup
    if not isinstance(create_backup, bool):
        logger.error(f"Invalid create_backup: {create_backup}")
        return False
    """
    Completely delete a user and all their data.
    
    Args:
        user_id: The user's ID
        create_backup: Whether to create a backup before deletion
        
    Returns:
        bool: True if user was deleted successfully
    """
    try:
        manager = UserDataManager()
        return manager.delete_user_completely(user_id, create_backup)
    except Exception as e:
        logger.error(f"Error deleting user completely: {e}")
        return False

@handle_errors("getting user data summary", default_return={"error": "Failed to get summary"})
def get_user_data_summary(user_id: str) -> Dict[str, Any]:
    """
    Get comprehensive summary of user data with validation.
    
    Returns:
        Dict[str, Any]: User data summary, error dict if failed
    """
    # Validate user_id
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return {"error": f"Invalid user_id: {user_id}"}
        
    if not user_id.strip():
        logger.error("Empty user_id provided")
        return {"error": "Empty user_id provided"}
    """
    Get a summary of user data.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Dict containing user data summary
    """
    try:
        manager = UserDataManager()
        return manager.get_user_data_summary(user_id)
    except Exception as e:
        logger.error(f"Error getting user data summary: {e}")
        return {}

@handle_errors("updating user index", default_return=False)
def update_user_index(user_id: str) -> bool:
    """
    Update user index with validation.
    
    Returns:
        bool: True if successful, False if failed
    """
    # Validate user_id
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return False
        
    if not user_id.strip():
        logger.error("Empty user_id provided")
        return False
    """
    Update the user index for a specific user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        bool: True if index was updated successfully
    """
    try:
        manager = UserDataManager()
        return manager.update_user_index(user_id)
    except Exception as e:
        logger.error(f"Error updating user index: {e}")
        return False

@handle_errors("rebuilding user index", default_return=False)
def rebuild_user_index() -> bool:
    """
    Rebuild the complete user index.
    
    Returns:
        bool: True if index was rebuilt successfully
    """
    manager = UserDataManager()
    return manager.rebuild_full_index()

@handle_errors("getting user info for data manager", default_return=None)
def get_user_info_for_data_manager(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user info using the new centralized data structure with validation.
    
    Returns:
        Optional[Dict[str, Any]]: User info dict or None if failed
    """
    # Validate user_id
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return None
        
    if not user_id.strip():
        logger.error("Empty user_id provided")
        return None
    """Get user info using the new centralized data structure."""
    try:
        from core.user_data_handlers import get_user_data
        
        # Get all user data with retry logic for parallel execution race conditions
        import time
        user_data = None
        for attempt in range(3):
            user_data = get_user_data(user_id, 'all', auto_create=True)
            # Check if user_data is valid (has at least account data)
            if user_data and isinstance(user_data, dict) and len(user_data) > 0:
                account_data = user_data.get('account', {})
                if account_data and account_data.get('internal_username'):
                    break
            if attempt < 2:
                time.sleep(0.1)  # Brief delay before retry
        
        # Check if user_data is None or empty (error case)
        # Empty dict from get_user_data means error occurred (due to error handling default_return={})
        if not user_data or (isinstance(user_data, dict) and len(user_data) == 0):
            return None
        
        # Build user info structure
        account_data = user_data.get('account', {})
        context_data = user_data.get('context', {})
        
        user_info = {
            "user_id": user_id,
            "internal_username": account_data.get('internal_username', ''),
            "preferred_name": context_data.get('preferred_name', ''),
            "account_status": account_data.get('account_status', 'unknown'),
            "email": account_data.get('email', ''),
            "message_files": {}  # Will be populated below
        }
        
        # Get message files
        from core.user_management import get_user_categories
        categories = get_user_categories(user_id)
        
        for category in categories:
            category_path = str(Path(get_user_data_dir(user_id)) / 'messages' / f'{category}.json')
            user_info["message_files"][category] = {
                "path": category_path,
                "exists": os.path.exists(category_path)
            }
        
        return user_info
        
    except Exception as e:
        logger.error(f"Error getting user info for data manager: {e}")
        return None

# Import get_user_categories from user_management to avoid duplication
from core.user_management import get_user_categories

@handle_errors("building user index", default_return={})
def build_user_index() -> Dict[str, Any]:
    """
    Build an index of all users and their message data with validation.
    
    Returns:
        Dict[str, Any]: User index, empty dict if failed
    """
    """Build an index of all users and their message data."""
    try:
        user_ids = get_all_user_ids()
        index_data = {}
        
        for user_id in user_ids:
            try:
                # Get user info using new structure
                user_info = get_user_info_for_data_manager(user_id)
                if not user_info:
                    continue
                
                # Get message count
                message_count = 0
                categories = get_user_categories(user_id)
                
                for category in categories:
                    category_path = str(Path(get_user_data_dir(user_id)) / 'messages' / f'{category}.json')
                    if os.path.exists(category_path):
                        try:
                            with open(category_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                message_count += len(data.get('messages', []))
                        except Exception as e:
                            logger.warning(f"Error reading message file {category_path}: {e}")
                
                # Build index entry
                index_data[user_id] = {
                    "active": True,
                    "categories": sorted(set(categories)),
                    "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "message_count": message_count
                }
                
            except Exception as e:
                logger.error(f"Error processing user {user_id} for index: {e}")
                continue
        
        return index_data
        
    except Exception as e:
        logger.error(f"Error building user index: {e}")
        return {}

@handle_errors("getting user summary", default_return={})
def get_user_summary(user_id: str) -> Dict[str, Any]:
    """
    Get a summary of user data and message statistics with validation.
    
    Returns:
        Dict[str, Any]: User summary, empty dict if failed
    """
    # Validate user_id
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return {}
        
    if not user_id.strip():
        logger.error("Empty user_id provided")
        return {}
    """Get a summary of user data and message statistics."""
    try:
        # Get user info using new structure
        user_info = get_user_info_for_data_manager(user_id)
        if not user_info:
            return {}
        
        # Get categories
        categories = get_user_categories(user_id)
        
        # Get message statistics
        message_stats = {}
        total_messages = 0
        
        for category in categories:
            category_path = str(Path(get_user_data_dir(user_id)) / 'messages' / f'{category}.json')
            if os.path.exists(category_path):
                try:
                    with open(category_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        message_count = len(data.get('messages', []))
                        message_stats[category] = message_count
                        total_messages += message_count
                except Exception as e:
                    logger.warning(f"Error reading message file {category_path}: {e}")
                    message_stats[category] = 0
            else:
                message_stats[category] = 0
        
        # Build summary
        summary = {
            "user_id": user_id,
            "internal_username": user_info.get("internal_username", ""),
            "preferred_name": user_info.get("preferred_name", ""),
            "active": user_info.get("active", False),
            "categories": categories,
            "message_stats": message_stats,
            "total_messages": total_messages,
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting user summary for {user_id}: {e}")
        return {}

@handle_errors("getting all user summaries", default_return=[])
def get_all_user_summaries() -> List[Dict[str, Any]]:
    """
    Get summaries for all users with validation.
    
    Returns:
        List[Dict[str, Any]]: List of user summaries, empty list if failed
    """
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

@handle_errors("getting user analytics summary", default_return={"error": "Failed to get analytics summary"})
def get_user_analytics_summary(user_id: str) -> Dict[str, Any]:
    """
    Get an analytics summary for a user including interaction patterns and data usage.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Dict containing analytics summary information
    """
    try:
        # Get basic summary
        summary = get_user_summary(user_id)
        if not summary:
            return {"error": "User not found"}
        
        # Add analytics data
        analytics = {
            "user_id": user_id,
            "data_summary": summary,
            "interaction_patterns": {},
            "data_usage": {},
            "recommendations": []
        }
        
        # Analyze interaction patterns
        interaction_sources = [
            ('sent_messages', 'Message Interactions'),
            ('checkins', 'Check-in Activity'),
            ('chat_interactions', 'Chat Activity')
        ]
        
        for source, label in interaction_sources:
            file_path = get_user_file_path(user_id, source)
            if os.path.exists(file_path):
                data = load_json_data(file_path) or []
                if isinstance(data, list):
                    analytics["interaction_patterns"][source] = {
                        "count": len(data),
                        "last_interaction": data[-1].get('timestamp', 'Unknown') if data else 'None',
                        "frequency": "High" if len(data) > 10 else "Medium" if len(data) > 5 else "Low"
                    }
        
        # Generate recommendations
        if analytics["interaction_patterns"].get('checkins', {}).get('count', 0) < 3:
            analytics["recommendations"].append("Consider enabling check-ins for better engagement")
        
        if analytics["interaction_patterns"].get('chat_interactions', {}).get('count', 0) < 5:
            analytics["recommendations"].append("Try using the chat feature for personalized interactions")
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting analytics summary for user {user_id}: {e}")
        return {"error": f"Failed to get analytics: {str(e)}"} 