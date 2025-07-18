# backup_manager.py
"""
Backup management system for MHM.
Provides automatic backup creation, validation, and rollback capabilities.
"""

import os
import json
import shutil
import zipfile
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from core.logger import get_logger
from core.config import BASE_DATA_DIR, USER_INFO_DIR_PATH
from core.error_handling import handle_errors
from core.user_management import get_user_data, get_all_user_ids

logger = get_logger(__name__)

class BackupManager:
    """Manages automatic backups and rollback operations."""
    
    def __init__(self):
        """
        Initialize the BackupManager with default settings.
        
        Sets up backup directory, maximum backup count, and ensures backup directory exists.
        """
        self.backup_dir = os.path.join(BASE_DATA_DIR, "backups")
        self.ensure_backup_directory()
        self.max_backups = 10  # Keep last 10 backups
    
    @handle_errors("ensuring backup directory exists")
    def ensure_backup_directory(self) -> bool:
        """Ensure backup directory exists."""
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            logger.debug(f"Backup directory ensured: {self.backup_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup directory: {e}")
            return False
    
    @handle_errors("creating backup", default_return=None)
    def create_backup(self, 
                     backup_name: Optional[str] = None,
                     include_users: bool = True,
                     include_config: bool = True,
                     include_logs: bool = False) -> Optional[str]:
        """
        Create a comprehensive backup of the system.
        
        Args:
            backup_name: Custom name for the backup (auto-generated if None)
            include_users: Whether to include user data
            include_config: Whether to include configuration files
            include_logs: Whether to include log files
        
        Returns:
            Path to the backup file, or None if failed
        """
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"mhm_backup_{timestamp}"
        
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup user data
                if include_users:
                    self._backup_user_data(zipf)
                
                # Backup configuration
                if include_config:
                    self._backup_config_files(zipf)
                
                # Backup logs (optional)
                if include_logs:
                    self._backup_log_files(zipf)
                
                # Create backup manifest
                self._create_backup_manifest(zipf, backup_name, include_users, include_config, include_logs)
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    @handle_errors("backing up user data")
    def _backup_user_data(self, zipf: zipfile.ZipFile) -> None:
        """Backup all user data directories."""
        if not os.path.exists(USER_INFO_DIR_PATH):
            logger.warning(f"User data directory does not exist: {USER_INFO_DIR_PATH}")
            return
        
        for user_dir in os.listdir(USER_INFO_DIR_PATH):
            user_path = os.path.join(USER_INFO_DIR_PATH, user_dir)
            if os.path.isdir(user_path):
                self._add_directory_to_zip(zipf, user_path, f"users/{user_dir}")
        
        logger.debug("User data backed up successfully")
    
    @handle_errors("backing up config files")
    def _backup_config_files(self, zipf: zipfile.ZipFile) -> None:
        """Backup configuration files."""
        config_files = [
            ".env",
            "requirements.txt",
            "user_index.json"
        ]
        
        for config_file in config_files:
            config_path = os.path.join(BASE_DATA_DIR, config_file)
            if os.path.exists(config_path):
                zipf.write(config_path, f"config/{config_file}")
        
        logger.debug("Configuration files backed up successfully")
    
    @handle_errors("backing up log files")
    def _backup_log_files(self, zipf: zipfile.ZipFile) -> None:
        """Backup log files."""
        log_files = [
            "app.log",
            "service.log"
        ]
        
        for log_file in log_files:
            log_path = os.path.join(BASE_DATA_DIR, log_file)
            if os.path.exists(log_path):
                zipf.write(log_path, f"logs/{log_file}")
        
        logger.debug("Log files backed up successfully")
    
    @handle_errors("creating backup manifest")
    def _create_backup_manifest(self, 
                               zipf: zipfile.ZipFile, 
                               backup_name: str,
                               include_users: bool,
                               include_config: bool,
                               include_logs: bool) -> None:
        """Create a manifest file describing the backup contents."""
        manifest = {
            "backup_name": backup_name,
            "created_at": datetime.now().isoformat(),
            "includes": {
                "users": include_users,
                "config": include_config,
                "logs": include_logs
            },
            "system_info": {
                "total_users": len(get_all_user_ids()),
                "backup_size": "unknown"  # Will be updated after creation
            }
        }
        
        manifest_content = json.dumps(manifest, indent=2)
        zipf.writestr("manifest.json", manifest_content)
    
    @handle_errors("adding directory to zip")
    def _add_directory_to_zip(self, zipf: zipfile.ZipFile, directory: str, zip_path: str) -> None:
        """Recursively add a directory to the zip file."""
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.join(zip_path, os.path.relpath(file_path, directory))
                zipf.write(file_path, arc_path)
    
    @handle_errors("cleaning up old backups")
    def _cleanup_old_backups(self) -> None:
        """Remove old backups to keep only the most recent ones."""
        backup_files = []
        for file in os.listdir(self.backup_dir):
            if file.endswith('.zip'):
                file_path = os.path.join(self.backup_dir, file)
                backup_files.append((file_path, os.path.getmtime(file_path)))
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old backups
        for file_path, _ in backup_files[self.max_backups:]:
            try:
                os.remove(file_path)
                logger.debug(f"Removed old backup: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to remove old backup {file_path}: {e}")
    
    @handle_errors("listing available backups", default_return=[])
    def list_backups(self) -> List[Dict]:
        """List all available backups with metadata."""
        backups = []
        
        for file in os.listdir(self.backup_dir):
            if file.endswith('.zip'):
                file_path = os.path.join(self.backup_dir, file)
                try:
                    backup_info = self._get_backup_info(file_path)
                    backups.append(backup_info)
                except Exception as e:
                    logger.warning(f"Failed to get info for backup {file}: {e}")
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return backups
    
    @handle_errors("getting backup info", default_return={})
    def _get_backup_info(self, backup_path: str) -> Dict:
        """Get information about a specific backup."""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                if 'manifest.json' in zipf.namelist():
                    manifest_content = zipf.read('manifest.json')
                    manifest = json.loads(manifest_content)
                    
                    return {
                        'file_path': backup_path,
                        'file_name': os.path.basename(backup_path),
                        'file_size': os.path.getsize(backup_path),
                        'created_at': manifest.get('created_at'),
                        'backup_name': manifest.get('backup_name'),
                        'includes': manifest.get('includes', {}),
                        'system_info': manifest.get('system_info', {})
                    }
                else:
                    # Fallback for backups without manifest
                    return {
                        'file_path': backup_path,
                        'file_name': os.path.basename(backup_path),
                        'file_size': os.path.getsize(backup_path),
                        'created_at': datetime.fromtimestamp(os.path.getmtime(backup_path)).isoformat(),
                        'backup_name': 'Unknown',
                        'includes': {},
                        'system_info': {}
                    }
        except Exception as e:
            logger.error(f"Failed to read backup info for {backup_path}: {e}")
            return {}
    
    @handle_errors("restoring backup", default_return=False)
    def restore_backup(self, backup_path: str, 
                      restore_users: bool = True,
                      restore_config: bool = False) -> bool:
        """
        Restore from a backup file.
        
        Args:
            backup_path: Path to the backup file
            restore_users: Whether to restore user data
            restore_config: Whether to restore configuration files
        
        Returns:
            True if restoration was successful, False otherwise
        """
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            # Create a temporary backup before restoration
            logger.info("Creating safety backup before restoration...")
            safety_backup = self.create_backup("pre_restore_safety_backup")
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Restore user data
                if restore_users:
                    self._restore_user_data(zipf)
                
                # Restore configuration
                if restore_config:
                    self._restore_config_files(zipf)
                
                logger.info(f"Backup restored successfully from: {backup_path}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    @handle_errors("restoring user data")
    def _restore_user_data(self, zipf: zipfile.ZipFile) -> None:
        """Restore user data from backup."""
        # Clear existing user data
        if os.path.exists(USER_INFO_DIR_PATH):
            shutil.rmtree(USER_INFO_DIR_PATH)
        
        # Extract user data from backup
        for file_info in zipf.infolist():
            if file_info.filename.startswith('users/'):
                zipf.extract(file_info, BASE_DATA_DIR)
        
        logger.info("User data restored successfully")
    
    @handle_errors("restoring config files")
    def _restore_config_files(self, zipf: zipfile.ZipFile) -> None:
        """Restore configuration files from backup."""
        for file_info in zipf.infolist():
            if file_info.filename.startswith('config/'):
                zipf.extract(file_info, BASE_DATA_DIR)
        
        logger.info("Configuration files restored successfully")
    
    @handle_errors("validating backup", default_return=(False, ["Validation failed"]))
    def validate_backup(self, backup_path: str) -> Tuple[bool, List[str]]:
        """
        Validate a backup file for integrity and completeness.
        
        Args:
            backup_path: Path to the backup file
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not os.path.exists(backup_path):
            errors.append(f"Backup file not found: {backup_path}")
            return False, errors
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Check if manifest exists
                if 'manifest.json' not in zipf.namelist():
                    errors.append("Backup missing manifest.json")
                
                # Check for required user data
                user_files = [f for f in zipf.namelist() if f.startswith('users/')]
                if not user_files:
                    errors.append("Backup contains no user data")
                
                # Check file integrity
                try:
                    zipf.testzip()
                except Exception as e:
                    errors.append(f"Backup file is corrupted: {e}")
                
                # Check manifest content
                if 'manifest.json' in zipf.namelist():
                    try:
                        manifest_content = zipf.read('manifest.json')
                        manifest = json.loads(manifest_content)
                        
                        if not manifest.get('created_at'):
                            errors.append("Manifest missing creation timestamp")
                        
                        if not manifest.get('backup_name'):
                            errors.append("Manifest missing backup name")
                            
                    except json.JSONDecodeError:
                        errors.append("Manifest.json is not valid JSON")
                
        except Exception as e:
            errors.append(f"Failed to open backup file: {e}")
        
        return len(errors) == 0, errors

# Global backup manager instance
backup_manager = BackupManager()

# Convenience functions for easy access
@handle_errors("creating automatic backup", default_return=None)
def create_automatic_backup(operation_name: str = "automatic") -> Optional[str]:
    """
    Create an automatic backup before major operations.
    
    Args:
        operation_name: Name of the operation being performed
    
    Returns:
        Path to the backup file, or None if failed
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"auto_{operation_name}_{timestamp}"
    
    logger.info(f"Creating automatic backup: {backup_name}")
    return backup_manager.create_backup(backup_name)

@handle_errors("validating system state", default_return=False)
def validate_system_state() -> bool:
    """
    Validate the current system state for consistency.
    
    Returns:
        True if system is in a valid state, False otherwise
    """
    try:
        # Check if user index exists and is valid
        user_index_path = os.path.join(BASE_DATA_DIR, "user_index.json")
        if os.path.exists(user_index_path):
            with open(user_index_path, 'r') as f:
                user_index = json.load(f)
            
            # Validate user index structure
            if not isinstance(user_index, dict):
                logger.error("User index is not a dictionary")
                return False
            
            # Check if all users in index have corresponding directories
            for user_id in user_index.keys():
                user_dir = os.path.join(USER_INFO_DIR_PATH, user_id)
                if not os.path.exists(user_dir):
                    logger.warning(f"User directory missing for indexed user: {user_id}")
        
        # Check if user data directory exists
        if not os.path.exists(USER_INFO_DIR_PATH):
            logger.error("User data directory does not exist")
            return False
        
        logger.info("System state validation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"System state validation failed: {e}")
        return False

@handle_errors("performing safe operation", default_return=False)
def perform_safe_operation(operation_func, *args, **kwargs) -> bool:
    """
    Perform an operation with automatic backup and rollback capability.
    
    Args:
        operation_func: Function to perform
        *args: Arguments for the operation function
        **kwargs: Keyword arguments for the operation function
    
    Returns:
        True if operation succeeded, False if it failed and was rolled back
    """
    # Create backup before operation
    backup_path = create_automatic_backup("safe_operation")
    if not backup_path:
        logger.error("Failed to create backup before safe operation")
        return False
    
    try:
        # Perform the operation
        result = operation_func(*args, **kwargs)
        
        # Validate system state after operation
        if not validate_system_state():
            logger.error("System state invalid after operation, rolling back...")
            backup_manager.restore_backup(backup_path)
            return False
        
        logger.info("Safe operation completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Operation failed, rolling back: {e}")
        backup_manager.restore_backup(backup_path)
        return False 