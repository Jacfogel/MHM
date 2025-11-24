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

from core.logger import get_logger, get_component_logger
import core.config
from core.error_handling import handle_errors
from core.user_data_handlers import get_user_data, get_all_user_ids

logger = get_component_logger('file_ops')
backup_logger = get_component_logger('main')

class BackupManager:
    """Manages automatic backups and rollback operations."""
    
    def __init__(self):
        """
        Initialize the BackupManager with default settings.
        
        Sets up backup directory, maximum backup count, and ensures backup directory exists.
        """
        # Redirect backups under tests/data when in test mode
        self.backup_dir = core.config.get_backups_dir()
        self.ensure_backup_directory()
        # Keep last 10 backups by default; also enforce age-based retention
        self.max_backups = 10
        try:
            self.backup_retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
        except Exception:
            self.backup_retention_days = 30
    
    @handle_errors("ensuring backup directory exists", default_return=False)
    def ensure_backup_directory(self) -> bool:
        """
        Ensure backup directory exists with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        os.makedirs(self.backup_dir, exist_ok=True)
        logger.debug(f"Backup directory ensured: {self.backup_dir}")
        return True
    
    @handle_errors("setting up backup parameters", default_return=("", ""))
    def _create_backup__setup_backup(self, backup_name: Optional[str]) -> Tuple[str, str]:
        """Setup backup name and path parameters."""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"mhm_backup_{timestamp}"
        
        backup_path = Path(self.backup_dir) / f"{backup_name}.zip"
        return backup_name, str(backup_path)
    
    @handle_errors("creating zip file", default_return=None)
    def _create_backup__create_zip_file(self, backup_path: str, backup_name: str, 
                                       include_users: bool, include_config: bool, include_logs: bool) -> None:
        """Create the backup zip file with all specified components."""
        # Ensure backup directory exists before creating zip
        os.makedirs(self.backup_dir, exist_ok=True)
        
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
    
    @handle_errors("cleaning up old backups", default_return=None)
    def _create_backup__cleanup_old_backups(self) -> None:
        """Clean up old backups by count and age."""
        self._cleanup_old_backups()
    
    @handle_errors("creating backup", default_return=None)
    def create_backup(self, 
                     backup_name: Optional[str] = None,
                     include_users: bool = True,
                     include_config: bool = True,
                     include_logs: bool = False) -> Optional[str]:
        """
        Create a comprehensive backup with validation.
        
        Returns:
            Optional[str]: Path to backup file, None if failed
        """
        # Validate inputs
        if backup_name is not None and not isinstance(backup_name, str):
            logger.error(f"Invalid backup_name type: {type(backup_name)}")
            return None
            
        if backup_name is not None and not backup_name.strip():
            logger.error("Empty backup_name provided")
            return None
            
        if not isinstance(include_users, bool):
            logger.error(f"Invalid include_users: {include_users}")
            return None
            
        if not isinstance(include_config, bool):
            logger.error(f"Invalid include_config: {include_config}")
            return None
            
        if not isinstance(include_logs, bool):
            logger.error(f"Invalid include_logs: {include_logs}")
            return None
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
        # Setup backup parameters
        backup_name, backup_path = self._create_backup__setup_backup(backup_name)
        
        # Create the backup zip file
        self._create_backup__create_zip_file(backup_path, backup_name, include_users, include_config, include_logs)
        
        # Verify backup file was actually created before proceeding
        if not os.path.exists(backup_path):
            logger.error(f"Backup file was not created at {backup_path}")
            return None
        
        # Clean up old backups (only after verifying new backup exists)
        self._create_backup__cleanup_old_backups()
        
        logger.info(f"Backup created successfully: {backup_path}")
        return backup_path
    
    @handle_errors("backing up user data")
    def _backup_user_data(self, zipf: zipfile.ZipFile) -> None:
        """Backup all user data directories."""
        user_info_path = Path(core.config.USER_INFO_DIR_PATH)
        if not user_info_path.exists():
            logger.warning(f"User data directory does not exist: {core.config.USER_INFO_DIR_PATH}")
            return
        
        user_count = 0
        for user_dir in user_info_path.iterdir():
            if user_dir.is_dir():
                try:
                    self._add_directory_to_zip(zipf, str(user_dir), f"users/{user_dir.name}")
                    user_count += 1
                except Exception as e:
                    logger.warning(f"Failed to backup user directory {user_dir.name}: {e}")
        
        logger.debug(f"User data backed up successfully ({user_count} users)")
    
    @handle_errors("backing up config files")
    def _backup_config_files(self, zipf: zipfile.ZipFile) -> None:
        """Backup configuration files."""
        config_files = [
            ".env",
            "requirements.txt",
            "user_index.json"
        ]
        
        base_data_path = Path(core.config.BASE_DATA_DIR)
        for config_file in config_files:
            # Use configurable base directory instead of hardcoded assumption
            config_path = base_data_path / config_file
            if config_path.exists():
                zipf.write(str(config_path), f"config/{config_file}")
        
        logger.debug("Configuration files backed up successfully")
    
    @handle_errors("backing up log files")
    def _backup_log_files(self, zipf: zipfile.ZipFile) -> None:
        """Backup log files."""
        # Use configurable log paths instead of hardcoded assumptions
        from core.config import LOG_MAIN_FILE, LOG_DISCORD_FILE, LOG_AI_FILE, LOG_USER_ACTIVITY_FILE, LOG_ERRORS_FILE
        
        log_files = [
            ("app.log", LOG_MAIN_FILE),
            ("discord.log", LOG_DISCORD_FILE),
            ("ai.log", LOG_AI_FILE),
            ("user_activity.log", LOG_USER_ACTIVITY_FILE),
            ("errors.log", LOG_ERRORS_FILE)
        ]
        
        for log_name, log_path in log_files:
            if os.path.exists(log_path):
                zipf.write(log_path, f"logs/{log_name}")
        
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
        directory_path = Path(directory)
        zip_path_base = Path(zip_path)
        # Track added files to prevent duplicates (handles symlinks and multiple calls)
        added_files = set()
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                arc_path = zip_path_base / file_path.relative_to(directory_path)
                arc_path_str = str(arc_path)
                # Only add if not already in zip (prevents duplicate warnings)
                if arc_path_str not in added_files:
                    try:
                        zipf.write(str(file_path), arc_path_str)
                        added_files.add(arc_path_str)
                    except zipfile.BadZipFile:
                        # Skip if zip is in a bad state
                        logger.warning(f"Skipping file {file_path} due to zip error")
                    except Exception as e:
                        # Log but continue for other errors
                        logger.debug(f"Error adding {file_path} to zip: {e}")
    
    @handle_errors("cleaning up old backups")
    def _cleanup_old_backups(self) -> None:
        """Remove old backups by count and age retention policy."""
        try:
            # Ensure backup directory exists before iterating (race condition fix)
            if not os.path.exists(self.backup_dir):
                return
            
            # Gather .zip backups with mtime
            backup_files: list[tuple[str, float]] = []
            now_ts = time.time()
            backup_dir_path = Path(self.backup_dir)
            
            # Re-check directory exists (parallel tests may delete it)
            if not backup_dir_path.exists():
                return
                
            try:
                for file_path in backup_dir_path.iterdir():
                    if file_path.is_file() and file_path.suffix == '.zip':
                        try:
                            mtime = file_path.stat().st_mtime
                            backup_files.append((str(file_path), mtime))
                        except Exception:
                            continue
            except Exception:
                # Directory might have been deleted by another process
                return

            if not backup_files:
                return

            # Age-based retention: remove files older than BACKUP_RETENTION_DAYS
            age_cutoff = now_ts - (self.backup_retention_days * 24 * 3600)
            for file_path, mtime in list(backup_files):
                if mtime < age_cutoff:
                    try:
                        # Re-check file exists before deleting (race condition fix)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            logger.debug(f"Removed backup by age (> {self.backup_retention_days}d): {file_path}")
                            backup_files.remove((file_path, mtime))
                    except Exception as e:
                        logger.warning(f"Failed to remove old backup {file_path}: {e}")

            # Count-based retention: keep newest self.max_backups
            backup_files.sort(key=lambda x: x[1], reverse=True)
            for file_path, _ in backup_files[self.max_backups:]:
                try:
                    # Re-check file exists before deleting (race condition fix)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.debug(f"Removed backup by count (>{self.max_backups}): {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove old backup {file_path}: {e}")
        except Exception as e:
            logger.warning(f"Backup cleanup encountered an error: {e}")
    
    @handle_errors("listing available backups", default_return=[])
    def list_backups(self) -> List[Dict]:
        """List all available backups with metadata."""
        backups = []
        
        # Ensure backup directory exists
        backup_dir_path = Path(self.backup_dir)
        if not backup_dir_path.exists():
            logger.warning(f"Backup directory does not exist: {self.backup_dir}")
            return backups
        
        try:
            for file_path in backup_dir_path.iterdir():
                if file_path.is_file() and file_path.suffix == '.zip':
                    try:
                        backup_info = self._get_backup_info(str(file_path))
                        # Only include backups with valid info (non-empty dict)
                        if backup_info:
                            backups.append(backup_info)
                    except Exception as e:
                        logger.warning(f"Failed to get info for backup {file_path.name}: {e}")
        except Exception as e:
            logger.error(f"Error listing backups from {self.backup_dir}: {e}")
        
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
        Restore backup with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        # Validate backup_path
        if not backup_path or not isinstance(backup_path, str):
            logger.error(f"Invalid backup_path: {backup_path}")
            return False
            
        if not backup_path.strip():
            logger.error("Empty backup_path provided")
            return False
            
        # Validate boolean parameters
        if not isinstance(restore_users, bool):
            logger.error(f"Invalid restore_users: {restore_users}")
            return False
            
        if not isinstance(restore_config, bool):
            logger.error(f"Invalid restore_config: {restore_config}")
            return False
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
                    try:
                        self._restore_user_data(zipf)
                    except Exception as e:
                        logger.error(f"Failed to restore user data: {e}")
                        raise
                
                # Restore configuration
                if restore_config:
                    try:
                        self._restore_config_files(zipf)
                    except Exception as e:
                        logger.error(f"Failed to restore config files: {e}")
                        raise
                
                logger.info(f"Backup restored successfully from: {backup_path}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            import traceback
            logger.error(f"Restore traceback: {traceback.format_exc()}")
            return False
    
    @handle_errors("restoring user data")
    def _restore_user_data(self, zipf: zipfile.ZipFile) -> None:
        """Restore user data from backup."""
        # Ensure base directory exists
        base_dir = Path(core.config.BASE_DATA_DIR)
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear existing user data
        user_info_path = Path(core.config.USER_INFO_DIR_PATH)
        if user_info_path.exists():
            try:
                shutil.rmtree(user_info_path)
            except Exception as e:
                logger.warning(f"Failed to remove existing user data directory: {e}")
        
        # Extract user data from backup
        extracted_count = 0
        for file_info in zipf.infolist():
            if file_info.filename.startswith('users/'):
                try:
                    zipf.extract(file_info, base_dir)
                    extracted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to extract {file_info.filename}: {e}")
        
        logger.info(f"User data restored successfully ({extracted_count} files extracted)")
    
    @handle_errors("restoring config files")
    def _restore_config_files(self, zipf: zipfile.ZipFile) -> None:
        """Restore configuration files from backup."""
        # Ensure base directory exists
        base_dir = Path(core.config.BASE_DATA_DIR)
        base_dir.mkdir(parents=True, exist_ok=True)
        
        extracted_count = 0
        for file_info in zipf.infolist():
            if file_info.filename.startswith('config/'):
                try:
                    zipf.extract(file_info, base_dir)
                    extracted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to extract {file_info.filename}: {e}")
        
        logger.info(f"Configuration files restored successfully ({extracted_count} files extracted)")
    
    @handle_errors("checking backup file exists", default_return=False)
    def _validate_backup__check_file_exists(self, backup_path: str, errors: List[str]) -> bool:
        """Check if the backup file exists and add error if not."""
        if not os.path.exists(backup_path):
            errors.append(f"Backup file not found: {backup_path}")
            return False
        return True
    
    @handle_errors("validating zip file contents", default_return=[])
    def _validate_backup__validate_zip_file(self, backup_path: str) -> List[str]:
        """Validate zip file integrity and contents."""
        errors = []
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Validate file integrity
                self._validate_backup__check_file_integrity(zipf, errors)
                
                # Validate manifest
                self._validate_backup__validate_manifest(zipf, errors)
                
                # Validate content requirements
                self._validate_backup__validate_content_requirements(zipf, errors)
                
        except Exception as e:
            errors.append(f"Failed to open backup file: {e}")
        
        return errors
    
    @handle_errors("checking file integrity", default_return=None)
    def _validate_backup__check_file_integrity(self, zipf: zipfile.ZipFile, errors: List[str]) -> None:
        """Check if the zip file is not corrupted."""
        try:
            zipf.testzip()
        except Exception as e:
            errors.append(f"Backup file is corrupted: {e}")
    
    @handle_errors("validating manifest", default_return=None)
    def _validate_backup__validate_manifest(self, zipf: zipfile.ZipFile, errors: List[str]) -> None:
        """Validate the backup manifest file."""
        if 'manifest.json' not in zipf.namelist():
            errors.append("Backup missing manifest.json")
            return
        
        try:
            manifest_content = zipf.read('manifest.json')
            manifest = json.loads(manifest_content)
            
            # Validate required manifest fields
            if not manifest.get('created_at'):
                errors.append("Manifest missing creation timestamp")
            
            if not manifest.get('backup_name'):
                errors.append("Manifest missing backup name")
                
        except json.JSONDecodeError:
            errors.append("Manifest.json is not valid JSON")
    
    @handle_errors("validating content requirements", default_return=None)
    def _validate_backup__validate_content_requirements(self, zipf: zipfile.ZipFile, errors: List[str]) -> None:
        """Validate that backup contains required content."""
        # Check for required user data
        # Note: Backups can be created without users (e.g., config-only backups)
        # Only warn if manifest indicates users should be included but none are found
        user_files = [f for f in zipf.namelist() if f.startswith('users/')]
        try:
            manifest_data = zipf.read('manifest.json')
            import json
            manifest = json.loads(manifest_data)
            if manifest.get('includes', {}).get('users', False) and not user_files:
                errors.append("Backup manifest indicates users should be included but no user data found")
        except Exception:
            # If manifest can't be read or parsed, skip this check
            # The manifest validation will catch manifest issues separately
            pass
    
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
        
        # Check if backup file exists
        if not self._validate_backup__check_file_exists(backup_path, errors):
            return False, errors
        
        # Validate zip file integrity and contents
        zip_errors = self._validate_backup__validate_zip_file(backup_path)
        errors.extend(zip_errors)
        
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

@handle_errors("validating user index", default_return=False)
@handle_errors("validating user index", default_return=False)
def _validate_system_state__validate_user_index() -> bool:
    """Validate the user index file and corresponding user directories."""
    user_index_path = Path(core.config.BASE_DATA_DIR) / "user_index.json"
    if not user_index_path.exists():
        return True  # Missing index is not an error, just means no users yet
    
    with open(user_index_path, 'r') as f:
        user_index = json.load(f)
    
    # Validate user index structure
    if not isinstance(user_index, dict):
        logger.error("User index is not a dictionary")
        return False
    
    # Check if UUID values in index have corresponding directories
    # Index now uses flat lookups: username/email/discord/phone → UUID
    # Extract unique UUIDs from the index values
    user_ids = set()
    for key, value in user_index.items():
        # Skip metadata keys
        if key in ['last_updated']:
            continue
        # Check if value looks like a UUID (flat lookup mapping)
        if isinstance(value, str) and len(value) > 20:
            user_ids.add(value)
    
    # Verify each user ID has a directory
    user_info_path = Path(core.config.USER_INFO_DIR_PATH)
    for user_id in user_ids:
        user_dir = user_info_path / user_id
        if not user_dir.exists():
            logger.warning(f"User directory missing for indexed user: {user_id}")
    
    return True

@handle_errors("ensuring user data directory exists", default_return=False)
def _validate_system_state__ensure_user_data_directory() -> bool:
    """Ensure the user data directory exists, creating it if necessary."""
    if not os.path.exists(core.config.USER_INFO_DIR_PATH):
        os.makedirs(core.config.USER_INFO_DIR_PATH, exist_ok=True)
        logger.warning("User data directory was missing; created during validation")
    
    return True

@handle_errors("validating system state", default_return=False)
def validate_system_state() -> bool:
    """
    Validate the current system state for consistency.
    
    Returns:
        True if system is in a valid state, False otherwise
    """
    try:
        # Validate user index and directories
        if not _validate_system_state__validate_user_index():
            return False
        
        # Ensure user data directory exists
        if not _validate_system_state__ensure_user_data_directory():
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