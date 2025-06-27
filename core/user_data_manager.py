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

from core.logger import get_logger
from core.config import (
    USE_USER_SUBDIRECTORIES,
    get_user_file_path,
    get_user_data_dir,
    BASE_DATA_DIR,
    MESSAGES_BY_CATEGORY_DIR_PATH,
)
from core.file_operations import load_json_data, save_json_data
from core.user_management import get_user_preferences, load_user_info_data, save_user_info_data

logger = get_logger(__name__)

class UserDataManager:
    """Enhanced user data management with references, backup, and indexing capabilities"""
    
    def __init__(self):
        self.index_file = os.path.join(BASE_DATA_DIR, "user_index.json")
        self.backup_dir = os.path.join(BASE_DATA_DIR, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def update_message_references(self, user_id: str) -> bool:
        """Add/update message file references in user profile"""
        try:
            if not USE_USER_SUBDIRECTORIES:
                logger.debug("Message references only supported in new user subdirectory structure")
                return False
                
            # Load user profile
            user_info = load_user_info_data(user_id)
            if not user_info:
                logger.error(f"User {user_id} not found")
                return False
            
            # Get user's categories
            categories = get_user_preferences(user_id, ['categories'])
            if not categories:
                logger.warning(f"No categories found for user {user_id}")
                return True
            
            # Build message references
            message_refs = {}
            for category in categories:
                message_file = os.path.join(MESSAGES_BY_CATEGORY_DIR_PATH, category, f"{user_id}.json")
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
            
            # Update profile with message references
            user_info["message_files"] = message_refs
            user_info["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Save directly to avoid circular dependency
            profile_file = get_user_file_path(user_id, 'profile')
            save_json_data(user_info, profile_file)
            logger.info(f"Updated message references for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating message references for user {user_id}: {e}")
            return False
    
    def get_user_message_files(self, user_id: str) -> Dict[str, str]:
        """Get all message file paths for a user"""
        try:
            user_info = load_user_info_data(user_id)
            if not user_info:
                return {}
            
            # Check if we have cached references
            if "message_files" in user_info:
                return {cat: info["path"] for cat, info in user_info["message_files"].items() if info["exists"]}
            
            # Fallback: build from categories
            categories = get_user_preferences(user_id, ['categories'])
            if not categories:
                return {}
            
            message_files = {}
            for category in categories:
                message_file = os.path.join(MESSAGES_BY_CATEGORY_DIR_PATH, category, f"{user_id}.json")
                if os.path.exists(message_file):
                    message_files[category] = message_file
            
            return message_files
            
        except Exception as e:
            logger.error(f"Error getting message files for user {user_id}: {e}")
            return {}
    
    def backup_user_data(self, user_id: str, include_messages: bool = True) -> str:
        """Create a complete backup of user's data"""
        try:
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
            
        except Exception as e:
            logger.error(f"Error creating backup for user {user_id}: {e}")
            raise
    
    def export_user_data(self, user_id: str, export_format: str = "json") -> Dict[str, Any]:
        """Export all user data to a structured format"""
        try:
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
            user_info = load_user_info_data(user_id)
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
            log_types = ["daily_checkins", "chat_interactions", "survey_responses"]
            for log_type in log_types:
                log_file = get_user_file_path(user_id, log_type)
                if os.path.exists(log_file):
                    export_data["logs"][log_type] = load_json_data(log_file) or []
            
            logger.info(f"User data exported for user {user_id}")
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting data for user {user_id}: {e}")
            raise
    
    def delete_user_completely(self, user_id: str, create_backup: bool = True) -> bool:
        """Completely remove all traces of a user from the system"""
        try:
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
            
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    def get_user_data_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a comprehensive summary of user's data"""
        try:
            summary = {
                "user_id": user_id,
                "profile": {"exists": False, "size": 0},
                "preferences": {"exists": False, "size": 0},
                "schedules": {"exists": False, "size": 0, "periods": 0},
                "messages": {},
                "sent_messages": {"exists": False, "size": 0, "count": 0},
                "logs": {},
                "total_files": 0,
                "total_size": 0
            }
            
            # Check user directory files
            user_dir = get_user_data_dir(user_id)
            if os.path.exists(user_dir):
                for file_type in ["profile", "preferences", "schedules", "sent_messages"]:
                    file_path = get_user_file_path(user_id, file_type)
                    if os.path.exists(file_path):
                        size = os.path.getsize(file_path)
                        summary[file_type]["exists"] = True
                        summary[file_type]["size"] = size
                        summary["total_files"] += 1
                        summary["total_size"] += size
                        
                        # Additional details for schedules
                        if file_type == "schedules":
                            data = load_json_data(file_path)
                            if data:
                                total_periods = sum(len(cat_schedules) for cat_schedules in data.values())
                                summary[file_type]["periods"] = total_periods
                        
                        # Additional details for sent messages
                        if file_type == "sent_messages":
                            data = load_json_data(file_path)
                            if data:
                                total_messages = sum(len(msgs) for msgs in data.values() if isinstance(msgs, list))
                                summary[file_type]["count"] = total_messages
            
            # Check message files
            message_files = self.get_user_message_files(user_id)
            for category, file_path in message_files.items():
                if os.path.exists(file_path):
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
                    summary["total_size"] += size
            
            # Check log files
            log_types = ["daily_checkins", "chat_interactions", "survey_responses"]
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
                    summary["total_size"] += size
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting data summary for user {user_id}: {e}")
            return {"error": str(e)}
    
    def update_user_index(self, user_id: str) -> bool:
        """Update the global user index with current user data locations"""
        try:
            # Load existing index
            index_data = load_json_data(self.index_file) or {}
            
            # Update user entry
            summary = self.get_user_data_summary(user_id)
            index_data[user_id] = {
                "active": True,
                "categories": sorted(set(get_user_preferences(user_id, ['categories']))),
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "message_count": summary["messages"].get(next(iter(summary["messages"])), {}).get("message_count", 0)
            }
            
            # Save updated index
            save_json_data(index_data, self.index_file)
            logger.debug(f"Updated user index for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user index for user {user_id}: {e}")
            return False
    
    def remove_from_index(self, user_id: str) -> bool:
        """Remove user from the global index"""
        try:
            index_data = load_json_data(self.index_file) or {}
            if user_id in index_data:
                del index_data[user_id]
                save_json_data(index_data, self.index_file)
                logger.info(f"Removed user {user_id} from index")
            return True
            
        except Exception as e:
            logger.error(f"Error removing user {user_id} from index: {e}")
            return False
    
    def rebuild_full_index(self) -> bool:
        """Rebuild the complete user index from scratch"""
        try:
            from core.user_management import get_all_user_ids
            
            index_data = {}
            user_ids = get_all_user_ids()
            
            for user_id in user_ids:
                if user_id:
                    summary = self.get_user_data_summary(user_id)
                    index_data[user_id] = {
                        "active": True,
                        "categories": sorted(set(get_user_preferences(user_id, ['categories']))),
                        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "message_count": summary["messages"].get(next(iter(summary["messages"])), {}).get("message_count", 0)
                    }
            
            save_json_data(index_data, self.index_file)
            logger.info(f"Rebuilt user index with {len(index_data)} users")
            return True
            
        except Exception as e:
            logger.error(f"Error rebuilding user index: {e}")
            return False
    
    def search_users(self, query: str, search_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Search users based on profile data or file patterns"""
        try:
            if search_fields is None:
                search_fields = ["internal_username", "preferred_name", "email"]
            
            index_data = load_json_data(self.index_file) or {}
            matches = []
            
            for user_id, user_index in index_data.items():
                # Load user profile for searching
                user_info = load_user_info_data(user_id)
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
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []


# Global instance
user_data_manager = UserDataManager()

# Convenience functions
def update_message_references(user_id: str) -> bool:
    """Update message file references for a user"""
    return user_data_manager.update_message_references(user_id)

def backup_user_data(user_id: str, include_messages: bool = True) -> str:
    """Create a backup of user's data"""
    return user_data_manager.backup_user_data(user_id, include_messages)

def export_user_data(user_id: str, export_format: str = "json") -> Dict[str, Any]:
    """Export user's data to structured format"""
    return user_data_manager.export_user_data(user_id, export_format)

def delete_user_completely(user_id: str, create_backup: bool = True) -> bool:
    """Completely remove a user from the system"""
    return user_data_manager.delete_user_completely(user_id, create_backup)

def get_user_data_summary(user_id: str) -> Dict[str, Any]:
    """Get summary of user's data"""
    return user_data_manager.get_user_data_summary(user_id)

def update_user_index(user_id: str) -> bool:
    """Update the user index"""
    return user_data_manager.update_user_index(user_id)

def rebuild_user_index() -> bool:
    """Rebuild the complete user index"""
    return user_data_manager.rebuild_full_index() 