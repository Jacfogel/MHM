#!/usr/bin/env python3
"""
User Data Manager - Enhanced utilities for user-centric operations
Provides tools for message references, backup, export, and indexing
"""

import os
import json
import shutil
import zipfile
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from core.logger import get_logger, get_component_logger
from core.config import (
    USER_INFO_DIR_PATH,
    get_user_file_path, ensure_user_directory, get_user_data_dir, BASE_DATA_DIR, get_backups_dir
)
from core.file_operations import load_json_data, save_json_data, get_user_file_path, get_user_data_dir
from core.user_data_handlers import get_user_data
from core.user_data_handlers import get_all_user_ids
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

logger = get_logger(__name__)
data_manager_logger = get_component_logger('user_activity')

class UserDataManager:
    """Enhanced user data management with references, backup, and indexing capabilities"""
    
    def __init__(self):
        """
        Initialize the UserDataManager.
        
        Sets up backup directory and index file path for user data management operations.
        """
        self.index_file = os.path.join(BASE_DATA_DIR, "user_index.json")
        # Redirect backups under tests/data when in test mode
        self.backup_dir = get_backups_dir()
        os.makedirs(self.backup_dir, exist_ok=True)
    
    @handle_errors("updating message references", default_return=False)
    def update_message_references(self, user_id: str) -> bool:
        """Add/update message file references in user profile"""
        # Load user profile
        user_info = get_user_info_for_data_manager(user_id)
        if not user_info:
            logger.error(f"User {user_id} not found")
            return False
        
        # Check if automated messages are enabled
        account_result = get_user_data(user_id, 'account')
        account_data = account_result.get('account', {})
        features = account_data.get('features', {})
        automated_messages_enabled = features.get('automated_messages', 'disabled') == 'enabled'
        # Get user's categories
        prefs_result = get_user_data(user_id, 'preferences')
        categories = prefs_result.get('preferences', {}).get('categories', [])
        if not categories:
            if automated_messages_enabled:
                logger.warning(f"No categories found for user {user_id} (automated messages enabled)")
            else:
                logger.debug(f"No categories found for user {user_id} (automated messages disabled)")
            return True
        
        # Build message references
        message_refs = {}
        for category in categories:
            message_file = os.path.join(get_user_data_dir(user_id), 'messages', f"{category}.json")
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
            message_file = os.path.join(get_user_data_dir(user_id), 'messages', f"{category}.json")
            if os.path.exists(message_file):
                message_files[category] = message_file
        
        return message_files
    
    @handle_errors("backing up user data")
    def backup_user_data(self, user_id: str, include_messages: bool = True) -> str:
        """Create a complete backup of user's data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"user_backup_{user_id}_{timestamp}.zip"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Backup user directory (profile, preferences, schedules, etc.)
            user_dir = get_user_data_dir(user_id)
            if os.path.exists(user_dir):
                for root, dirs, files in os.walk(user_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, BASE_DATA_DIR)
                        zipf.write(file_path, arcname)
            
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
    
    @handle_errors("exporting user data")
    def export_user_data(self, user_id: str, export_format: str = "json") -> Dict[str, Any]:
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
        """Completely remove all traces of a user from the system"""
        if create_backup:
            backup_path = self.backup_user_data(user_id, include_messages=True)
            logger.info(f"Backup created before deletion: {backup_path}")
        
        # Delete user directory
        user_dir = get_user_data_dir(user_id)
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
            logger.info(f"Deleted user directory: {user_dir}")
        
        # Delete message files
        message_files = self.get_user_message_files(user_id)
        for category, file_path in message_files.items():
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted message file: {file_path}")
        
        # Update user index
        self.remove_from_index(user_id)
        
        logger.info(f"User {user_id} completely removed from system")
        return True
    
    @handle_errors("getting user data summary", default_return={"error": "Failed to get summary"})
    def get_user_data_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a comprehensive summary of user data including file counts and sizes.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dict containing summary information about the user's data
        """
        # Resilient summary structure – nested dicts so we don’t hit KeyError when
        # assigning sub-fields.
        summary: Dict[str, Any] = {
            "user_id": user_id,
            "files": {},        # generic file-type map, e.g. files['profile']
            "messages": {},     # per-category message file info
            "logs": {},         # per-type log info
            "total_files": 0,
            "total_size_bytes": 0,
            "last_modified": None,
        }
        
        # Check user directory files
        user_dir = get_user_data_dir(user_id)
        if os.path.exists(user_dir):
            from core.user_data_handlers import USER_DATA_LOADERS

            # Build list of core file types dynamically from registered loaders
            dynamic_types = list(USER_DATA_LOADERS.keys()) + ["sent_messages"]

            for file_type in dynamic_types:
                file_path = get_user_file_path(user_id, file_type)
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    summary["files"].setdefault(file_type, {})
                    summary["files"][file_type]["exists"] = True
                    summary["files"][file_type]["size"] = size
                    summary["total_files"] += 1
                    summary["total_size_bytes"] += size
                    
                    # Additional details for schedules
                    if file_type == "schedules":
                        data = load_json_data(file_path)
                        if data:
                            total_periods = sum(len(cat_schedules) for cat_schedules in data.values())
                            summary["files"][file_type]["periods"] = total_periods
                    
                    # Additional details for sent messages
                    if file_type == "sent_messages":
                        data = load_json_data(file_path)
                        if data:
                            total_messages = sum(len(msgs) for msgs in data.values() if isinstance(msgs, list))
                            summary["files"][file_type]["count"] = total_messages
        
        # Check message files using ensure_user_message_files
        prefs_result = get_user_data(user_id, 'preferences')
        categories = prefs_result.get('preferences', {}).get('categories', [])
        
        if categories:
            try:
                from core.message_management import ensure_user_message_files
                # This will check which files are missing and create them
                result = ensure_user_message_files(user_id, categories)
                if result["success"]:
                    logger.info(f"Message files validation for user {user_id}: checked {result['files_checked']} categories, created {result['files_created']} files, directory_created={result['directory_created']}")
                else:
                    logger.warning(f"Message files validation for user {user_id}: checked {result['files_checked']} categories, created {result['files_created']} files, some failures occurred")
            except Exception as e:
                logger.error(f"Error ensuring message files during validation for user {user_id}: {e}")
        
        # Now get the message files (after ensuring they exist)
        message_files = self.get_user_message_files(user_id)
        
        # Report on all message files
        for category in categories:
            file_path = os.path.join(get_user_data_dir(user_id), 'messages', f"{category}.json")
            
            if os.path.exists(file_path):
                # File exists, report its details
                size = os.path.getsize(file_path)
                data = load_json_data(file_path)
                message_count = len(data.get("messages", [])) if data else 0
                
                summary["messages"][category] = {
                    "exists": True,
                    "size": size,
                    "message_count": message_count,
                    "path": file_path
                }
                summary["total_files"] += 1
                summary["total_size_bytes"] += size
            else:
                # File still missing after ensure_user_message_files
                summary["messages"][category] = {
                    "exists": False,
                    "size": 0,
                    "message_count": 0,
                    "path": file_path,
                    "creation_failed": True
                }
                logger.warning(f"Message file for category {category} still missing after ensure_user_message_files for user {user_id}")
        
        # Also check any existing message files that might not be in enabled categories
        for category, file_path in message_files.items():
            if category not in categories and os.path.exists(file_path):
                # This is an orphaned message file (category not enabled but file exists)
                size = os.path.getsize(file_path)
                data = load_json_data(file_path)
                message_count = len(data.get("messages", [])) if data else 0
                
                summary["messages"][category] = {
                    "exists": True,
                    "size": size,
                    "message_count": message_count,
                    "path": file_path,
                    "orphaned": True  # Mark as orphaned for potential cleanup
                }
                summary["total_files"] += 1
                summary["total_size_bytes"] += size
        
        # Check log files
        log_types = ["checkins", "chat_interactions"]
        for log_type in log_types:
            log_file = get_user_file_path(user_id, log_type)
            if os.path.exists(log_file):
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
        
        return summary
    
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
        Update the user index with current information for a specific user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            bool: True if index was updated successfully
        """
        try:
            # Load existing index
            index_data = load_json_data(self.index_file) or {"users": {}, "last_updated": None}
            
            # Get current user summary
            user_summary = get_user_summary(user_id)
            if not user_summary:
                logger.warning(f"Could not get summary for user {user_id}")
                return False

            # Safely get message count - handle case where no message categories exist
            message_count = user_summary.get("total_messages", 0)
            
            # Get user account, preferences, and context for additional info
            user_data_result = get_user_data(user_id, 'account')
            user_account = user_data_result.get('account') or {}
            prefs_result = get_user_data(user_id, 'preferences')
            user_preferences = prefs_result.get('preferences') or {}
            context_result = get_user_data(user_id, 'context')
            user_context = context_result.get('context') or {}
            
            # Determine enabled features
            enabled_features = []
            features = user_account.get('features', {})
            
            if features.get('automated_messages') == 'enabled':
                enabled_features.append('automated_messages')
                # Include categories only if automated messages are enabled
                categories = user_preferences.get('categories', [])
                enabled_features.extend(categories)
            
            if features.get('checkins') == 'enabled':
                enabled_features.append('checkins')
                
            if features.get('task_management') == 'enabled':
                enabled_features.append('task_management')
            
            # Get channel type
            channel_type = user_preferences.get('channel', {}).get('type', 'email')
            
            # Get last interaction (most recent activity)
            last_interaction = self._get_last_interaction(user_id)
            
            index_data[user_id] = {
                "internal_username": user_account.get('internal_username', ''),
                "active": user_account.get('account_status') == 'active',
                "channel_type": channel_type,
                "enabled_features": sorted(enabled_features),
                "last_interaction": last_interaction,
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Save updated index
            save_json_data(index_data, self.index_file)
            logger.debug(f"Updated user index for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating user index for user {user_id}: {e}")
            return False
    
    @handle_errors("removing from index", default_return=False)
    def remove_from_index(self, user_id: str) -> bool:
        """
        Remove a user from the index.
        
        Args:
            user_id: The user's ID
            
        Returns:
            bool: True if user was removed from index successfully
        """
        try:
            index_data = load_json_data(self.index_file) or {"users": {}, "last_updated": None}
            if user_id in index_data["users"]:
                del index_data["users"][user_id]
                index_data["last_updated"] = datetime.now().isoformat()
                save_json_data(index_data, self.index_file)
                logger.info(f"Removed user {user_id} from index")
                return True
            return True  # User wasn't in index, that's fine
        except Exception as e:
            logger.error(f"Error removing user {user_id} from index: {e}")
            return False
    
    @handle_errors("rebuilding full index", default_return=False)
    def rebuild_full_index(self) -> bool:
        """
        Rebuild the complete user index from scratch.
        
        Scans all user directories and creates a fresh index with current information.
        
        Returns:
            bool: True if index was rebuilt successfully
        """
        try:
            logger.info("Starting full user index rebuild...")
            
            # Get all user IDs
            user_ids = get_all_user_ids()
            if not user_ids:
                logger.warning("No users found during index rebuild")
                return True

            index_data = {}
            for user_id in user_ids:
                if user_id:
                    summary = self.get_user_data_summary(user_id)
                    
                    # Get user account, preferences, and context for additional info
                    user_data_result = get_user_data(user_id, 'account')
                    user_account = user_data_result.get('account') or {}
                    prefs_result = get_user_data(user_id, 'preferences')
                    user_preferences = prefs_result.get('preferences') or {}
                    context_result = get_user_data(user_id, 'context')
                    user_context = context_result.get('context') or {}
                    
                    # Determine enabled features
                    enabled_features = []
                    features = user_account.get('features', {})
                    
                    if features.get('automated_messages') == 'enabled':
                        enabled_features.append('automated_messages')
                        # Include categories only if automated messages are enabled
                        categories = user_preferences.get('categories', [])
                        enabled_features.extend(categories)
                    
                    if features.get('checkins') == 'enabled':
                        enabled_features.append('checkins')
                        
                    if features.get('task_management') == 'enabled':
                        enabled_features.append('task_management')
                    
                    # Get channel type
                    channel_type = user_preferences.get('channel', {}).get('type', 'email')
                    
                    # Get last interaction (most recent activity)
                    last_interaction = self._get_last_interaction(user_id)
                    
                    index_data[user_id] = {
                        "internal_username": user_account.get('internal_username', ''),
                        "active": user_account.get('account_status') == 'active',
                        "channel_type": channel_type,
                        "enabled_features": sorted(enabled_features),
                        "last_interaction": last_interaction,
                        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
            
            save_json_data(index_data, self.index_file)
            logger.info(f"Rebuilt user index with {len(index_data)} users")
            return True
        except Exception as e:
            logger.error(f"Error rebuilding full user index: {e}")
            return False
    
    @handle_errors("searching users", default_return=[])
    def search_users(self, query: str, search_fields: List[str] = None) -> List[Dict[str, Any]]:
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
        
        # Load index
        index_data = load_json_data(self.index_file) or {"users": {}, "last_updated": None}
        users = index_data.get("users", {})
        
        if not users:
            return []

        matches = []
        
        for user_id, user_index in users.items():
            # Load user profile for searching
            user_info = get_user_info_for_data_manager(user_id)
            if not user_info:
                continue
            
            # Check if query matches any search fields
            match_found = False
            for field in search_fields:
                field_value = str(user_info.get(field, "")).lower()
                if query.lower() in field_value:
                    match_found = True
                    break
            
            if match_found:
                matches.append({
                    "user_id": user_id,
                    "profile": user_info,
                    "summary": user_index.get("summary", {})
                })
        
        return matches


# Global instance
user_data_manager = UserDataManager()

# Convenience functions
def update_message_references(user_id: str) -> bool:
    """
    Update message file references for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        bool: True if references were updated successfully
    """
    manager = UserDataManager()
    return manager.update_message_references(user_id)

def backup_user_data(user_id: str, include_messages: bool = True) -> str:
    """
    Create a backup of user data.
    
    Args:
        user_id: The user's ID
        include_messages: Whether to include message files in backup
        
    Returns:
        str: Path to the created backup file
    """
    manager = UserDataManager()
    return manager.backup_user_data(user_id, include_messages)

def export_user_data(user_id: str, export_format: str = "json") -> Dict[str, Any]:
    """
    Export user data to a structured format.
    
    Args:
        user_id: The user's ID
        export_format: Format for export (currently only "json" supported)
        
    Returns:
        Dict containing all user data in structured format
    """
    manager = UserDataManager()
    return manager.export_user_data(user_id, export_format)

def delete_user_completely(user_id: str, create_backup: bool = True) -> bool:
    """
    Completely delete a user and all their data.
    
    Args:
        user_id: The user's ID
        create_backup: Whether to create a backup before deletion
        
    Returns:
        bool: True if user was deleted successfully
    """
    manager = UserDataManager()
    return manager.delete_user_completely(user_id, create_backup)

def get_user_data_summary(user_id: str) -> Dict[str, Any]:
    """
    Get a summary of user data.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Dict containing user data summary
    """
    manager = UserDataManager()
    return manager.get_user_data_summary(user_id)

def update_user_index(user_id: str) -> bool:
    """
    Update the user index for a specific user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        bool: True if index was updated successfully
    """
    manager = UserDataManager()
    return manager.update_user_index(user_id)

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
    """Get user info for data manager operations - uses new hybrid structure."""
    if not user_id:
        return None
    
    # Use the hybrid function to get account data
    user_data = get_user_data(user_id, 'account')
    account_data = user_data.get('account')
    
    if not account_data:
        logger.warning(f"No account data found for user {user_id}")
        return None
    
    # Extract relevant fields from account data
    user_info = {
        "user_id": account_data.get("user_id", user_id),
        "internal_username": account_data.get("internal_username", ""),
        "active": account_data.get("account_status") == "active",
        "preferred_name": account_data.get("preferred_name", ""),
        "chat_id": account_data.get("chat_id", ""),
        "phone": account_data.get("phone", ""),
        "email": account_data.get("email", ""),
        "created_at": account_data.get("created_at", ""),
        "last_updated": account_data.get("updated_at", "")
    }
    
    return user_info

@handle_errors("getting user categories", default_return=[])
def get_user_categories(user_id: str) -> List[str]:
    """Get user's message categories."""
    try:
        prefs_result = get_user_data(user_id, 'preferences')
        categories = prefs_result.get('preferences', {}).get('categories', [])
        if categories is None:
            return []
        elif isinstance(categories, list):
            return categories
        elif isinstance(categories, dict):
            return list(categories.keys())
        else:
            return []
    except Exception as e:
        logger.error(f"Error getting categories for user {user_id}: {e}")
        return []

@handle_errors("building user index", default_return={})
def build_user_index() -> Dict[str, Any]:
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
                    category_path = os.path.join(get_user_data_dir(user_id), 'messages', f'{category}.json')
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
            category_path = os.path.join(get_user_data_dir(user_id), 'messages', f'{category}.json')
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