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
from core import get_user_data, get_all_user_ids
from core.time_utilities import (
    now_timestamp_filename,
    now_timestamp_full,
    TIMESTAMP_FULL,
    format_timestamp,
)

logger = get_component_logger("file_ops")
backup_logger = get_component_logger("main")


class BackupManager:
    """Manages automatic backups and rollback operations."""

    @handle_errors("initializing backup manager", default_return=None)
    def __init__(self):
        """
        Initialize the BackupManager with default settings.

        Sets up backup directory, maximum backup count, and ensures backup directory exists.
        """
        # Redirect backups under tests/data when in test mode
        self.backup_dir = core.config.get_backups_dir()
        self.ensure_backup_directory()
        # Keep last 10 non-weekly backups by default; also enforce age-based retention
        self.max_backups = 10
        try:
            self.weekly_max_backups = int(os.getenv("WEEKLY_BACKUP_MAX_KEEP", "4"))
        except (ValueError, TypeError):
            self.weekly_max_backups = 4
        # Parse backup retention days from environment, default to 30 if invalid
        try:
            self.backup_retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
        except (ValueError, TypeError):
            self.backup_retention_days = 30
        # Backups are always directory-based; legacy BACKUP_FORMAT=zip support has been removed.
        self.backup_format = "directory"

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
    def _create_backup__setup_backup(self, backup_name: str | None) -> tuple[str, str]:
        """Setup backup name and path parameters."""
        if not backup_name:
            timestamp = now_timestamp_filename()
            backup_name = f"mhm_backup_{timestamp}"
        backup_path = Path(self.backup_dir) / backup_name
        return backup_name, str(backup_path)

    @handle_errors("creating directory backup payload", default_return=False)
    def _create_backup__create_directory_payload(
        self,
        backup_dir_path: str,
        backup_name: str,
        include_users: bool,
        include_config: bool,
        include_logs: bool,
        include_code: bool = False,
    ) -> bool:
        """Create non-zipped directory backup payload."""
        backup_root = Path(backup_dir_path)
        if backup_root.exists():
            if backup_root.is_file():
                backup_root.unlink()
            else:
                shutil.rmtree(backup_root, ignore_errors=True)
        backup_root.mkdir(parents=True, exist_ok=True)

        if include_users:
            self._backup_user_data_to_directory(backup_root)
        if include_config:
            self._backup_config_files_to_directory(backup_root)
        if include_logs:
            self._backup_log_files_to_directory(backup_root)
        if include_code:
            self._backup_project_code_to_directory(backup_root)

        manifest = {
            "backup_name": backup_name,
            "created_at": now_timestamp_full(),
            "format": "directory",
            "includes": {
                "users": include_users,
                "config": include_config,
                "logs": include_logs,
                "code": include_code,
            },
            "system_info": {
                "total_users": len(get_all_user_ids()),
                "backup_size": "unknown",
            },
        }
        with open(backup_root / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        return True

    @handle_errors("creating zip file", default_return=None)
    def _create_backup__create_zip_file(
        self,
        backup_path: str,
        backup_name: str,
        include_users: bool,
        include_config: bool,
        include_logs: bool,
        include_code: bool = False,
    ) -> None:
        """Create the backup zip file with all specified components."""
        # Ensure backup directory exists before creating zip
        os.makedirs(self.backup_dir, exist_ok=True)

        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Backup user data
            if include_users:
                self._backup_user_data(zipf)

            # Backup configuration
            if include_config:
                self._backup_config_files(zipf)

            # Backup logs (optional)
            if include_logs:
                self._backup_log_files(zipf)

            # Backup project code (optional, for full project backups)
            if include_code:
                self._backup_project_code(zipf)

            self._create_backup_manifest(
                zipf,
                backup_name,
                include_users,
                include_config,
                include_logs,
                include_code,
            )

    @handle_errors("cleaning up old backups", default_return=None)
    def _create_backup__cleanup_old_backups(self) -> None:
        """Clean up old backups by count and age."""
        self._cleanup_old_backups()

    @handle_errors("creating backup", default_return=None)
    def create_backup(
        self,
        backup_name: str | None = None,
        include_users: bool = True,
        include_config: bool = True,
        include_logs: bool = False,
        include_code: bool = False,
    ) -> str | None:
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

        if not isinstance(include_code, bool):
            logger.error(f"Invalid include_code: {include_code}")
            return None
        """
        Create a comprehensive backup of the system.
        
        Args:
            backup_name: Custom name for the backup (auto-generated if None)
            include_users: Whether to include user data
            include_config: Whether to include configuration files
            include_logs: Whether to include log files
            include_code: Whether to include project code (Python files, etc.)
        
        Returns:
            Path to the backup file, or None if failed
        """
        backup_name, backup_path = self._create_backup__setup_backup(backup_name)
        created_ok = self._create_backup__create_directory_payload(
            backup_path,
            backup_name,
            include_users,
            include_config,
            include_logs,
            include_code,
        )
        if not created_ok:
            logger.error(f"Directory backup payload creation failed: {backup_path}")
            return None

        # Verify backup file was actually created before proceeding
        if not os.path.exists(backup_path):
            logger.error(f"Backup file was not created at {backup_path}")
            return None

        # Verify backup integrity
        is_valid, errors = self.validate_backup(backup_path)
        if not is_valid:
            logger.error(f"Backup verification failed: {errors}")
            # Don't delete the backup - it might still be useful, but log the errors
            logger.warning(
                f"Backup created but verification found issues: {backup_path}"
            )
        else:
            logger.info(f"Backup verified successfully: {backup_path}")

        created_backup_path = backup_path

        # Get backup size for logging
        try:
            backup_size = self._get_backup_artifact_size_bytes(created_backup_path)
            backup_size_mb = backup_size / (1024 * 1024)
            logger.info(f"Backup size: {backup_size_mb:.2f} MB")
        except Exception as e:
            logger.debug(f"Could not get backup size: {e}")

        self._create_backup__cleanup_old_backups()

        logger.info(f"Backup created successfully: {created_backup_path}")
        return created_backup_path

    @handle_errors("backing up user data")
    def _backup_user_data(self, zipf: zipfile.ZipFile) -> None:
        """Backup all user data directories."""
        user_info_path = Path(core.config.USER_INFO_DIR_PATH)
        if not user_info_path.exists():
            logger.warning(
                f"User data directory does not exist: {core.config.USER_INFO_DIR_PATH}"
            )
            return

        user_count = 0
        for user_dir in user_info_path.iterdir():
            if user_dir.is_dir():
                try:
                    self._add_directory_to_zip(
                        zipf, str(user_dir), f"users/{user_dir.name}"
                    )
                    user_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to backup user directory {user_dir.name}: {e}"
                    )

        logger.debug(f"User data backed up successfully ({user_count} users)")

    @handle_errors("backing up user data to directory")
    def _backup_user_data_to_directory(self, backup_root: Path) -> None:
        """Backup all user data directories to a directory payload."""
        user_info_path = Path(core.config.USER_INFO_DIR_PATH)
        if not user_info_path.exists():
            logger.warning(
                f"User data directory does not exist: {core.config.USER_INFO_DIR_PATH}"
            )
            return
        users_target = backup_root / "users"
        users_target.mkdir(parents=True, exist_ok=True)
        for user_dir in user_info_path.iterdir():
            if not user_dir.is_dir():
                continue
            target = users_target / user_dir.name
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            shutil.copytree(user_dir, target)

    @handle_errors("backing up config files")
    def _backup_config_files(self, zipf: zipfile.ZipFile) -> None:
        """Backup configuration files."""
        config_files = [".env", "requirements.txt", "user_index.json"]

        base_data_path = Path(core.config.BASE_DATA_DIR)
        for config_file in config_files:
            # Use configurable base directory instead of hardcoded assumption
            config_path = base_data_path / config_file
            if config_path.exists():
                zipf.write(str(config_path), f"config/{config_file}")

        logger.debug("Configuration files backed up successfully")

    @handle_errors("backing up config files to directory")
    def _backup_config_files_to_directory(self, backup_root: Path) -> None:
        """Backup configuration files to a directory payload."""
        config_files = [".env", "requirements.txt", "user_index.json"]
        target = backup_root / "config"
        target.mkdir(parents=True, exist_ok=True)
        base_data_path = Path(core.config.BASE_DATA_DIR)
        for config_file in config_files:
            config_path = base_data_path / config_file
            if config_path.exists() and config_path.is_file():
                shutil.copy2(config_path, target / config_file)

    @handle_errors("backing up log files")
    def _backup_log_files(self, zipf: zipfile.ZipFile) -> None:
        """Backup log files."""
        # Use configurable log paths instead of hardcoded assumptions
        from core.config import (
            LOG_MAIN_FILE,
            LOG_DISCORD_FILE,
            LOG_AI_FILE,
            LOG_USER_ACTIVITY_FILE,
            LOG_ERRORS_FILE,
        )

        log_files = [
            ("app.log", LOG_MAIN_FILE),
            ("discord.log", LOG_DISCORD_FILE),
            ("ai.log", LOG_AI_FILE),
            ("user_activity.log", LOG_USER_ACTIVITY_FILE),
            ("errors.log", LOG_ERRORS_FILE),
        ]

        for log_name, log_path in log_files:
            if os.path.exists(log_path):
                zipf.write(log_path, f"logs/{log_name}")

        logger.debug("Log files backed up successfully")

    @handle_errors("backing up log files to directory")
    def _backup_log_files_to_directory(self, backup_root: Path) -> None:
        """Backup log files to a directory payload."""
        from core.config import (
            LOG_MAIN_FILE,
            LOG_DISCORD_FILE,
            LOG_AI_FILE,
            LOG_USER_ACTIVITY_FILE,
            LOG_ERRORS_FILE,
        )
        log_files = [
            ("app.log", LOG_MAIN_FILE),
            ("discord.log", LOG_DISCORD_FILE),
            ("ai.log", LOG_AI_FILE),
            ("user_activity.log", LOG_USER_ACTIVITY_FILE),
            ("errors.log", LOG_ERRORS_FILE),
        ]
        target = backup_root / "logs"
        target.mkdir(parents=True, exist_ok=True)
        for log_name, log_path in log_files:
            if os.path.exists(log_path):
                shutil.copy2(log_path, target / log_name)

    @handle_errors("backing up project code")
    def _backup_project_code(self, zipf: zipfile.ZipFile) -> None:
        """Backup project code files (Python files, configs, etc.)."""
        import core.config as config

        project_root = (
            Path(config.BASE_DATA_DIR).parent
            if hasattr(config, "BASE_DATA_DIR")
            else Path(".")
        )

        # Directories to include
        code_directories = [
            "core",
            "communication",
            "ai",
            "ui",
            "tasks",
            "user",
            "development_tools",
            "scripts",
            "resources",
            "styles",
        ]

        # Files to include at root
        root_files = [
            "requirements.txt",
            "pyproject.toml",
            "README.md",
            "HOW_TO_RUN.md",
            "ARCHITECTURE.md",
            "DEVELOPMENT_WORKFLOW.md",
            "PROJECT_VISION.md",
            ".env.example",
        ]

        # Add root files
        for root_file in root_files:
            file_path = project_root / root_file
            if file_path.exists() and file_path.is_file():
                zipf.write(str(file_path), f"code/{root_file}")

        # Add code directories (Python files only to keep size manageable)
        for code_dir in code_directories:
            dir_path = project_root / code_dir
            if dir_path.exists() and dir_path.is_dir():
                for py_file in dir_path.rglob("*.py"):
                    # Skip test files and generated files
                    if "test" in str(py_file) or "generated" in str(py_file):
                        continue
                    arcname = f"code/{py_file.relative_to(project_root)}"
                    zipf.write(str(py_file), arcname)

        logger.debug("Project code backed up successfully")

    @handle_errors("backing up project code to directory")
    def _backup_project_code_to_directory(self, backup_root: Path) -> None:
        """Backup project code files to a directory payload."""
        import core.config as config

        project_root = (
            Path(config.BASE_DATA_DIR).parent
            if hasattr(config, "BASE_DATA_DIR")
            else Path(".")
        )
        code_root = backup_root / "code"
        code_root.mkdir(parents=True, exist_ok=True)
        code_directories = [
            "core",
            "communication",
            "ai",
            "ui",
            "tasks",
            "user",
            "development_tools",
            "scripts",
            "resources",
            "styles",
        ]
        root_files = [
            "requirements.txt",
            "pyproject.toml",
            "README.md",
            "HOW_TO_RUN.md",
            "ARCHITECTURE.md",
            "DEVELOPMENT_WORKFLOW.md",
            "PROJECT_VISION.md",
            ".env.example",
        ]
        for root_file in root_files:
            file_path = project_root / root_file
            if file_path.exists() and file_path.is_file():
                target = code_root / root_file
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, target)
        for code_dir in code_directories:
            dir_path = project_root / code_dir
            if dir_path.exists() and dir_path.is_dir():
                for py_file in dir_path.rglob("*.py"):
                    if "test" in str(py_file) or "generated" in str(py_file):
                        continue
                    rel = py_file.relative_to(project_root)
                    target = code_root / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(py_file, target)

    @handle_errors("creating backup manifest")
    def _create_backup_manifest(
        self,
        zipf: zipfile.ZipFile,
        backup_name: str,
        include_users: bool,
        include_config: bool,
        include_logs: bool,
        include_code: bool = False,
    ) -> None:
        """Create a manifest file describing the backup contents."""

        manifest = {
            "backup_name": backup_name,
            "created_at": now_timestamp_full(),
            "format": "zip",
            "includes": {
                "users": include_users,
                "config": include_config,
                "logs": include_logs,
                "code": include_code,
            },
            "system_info": {
                "total_users": len(get_all_user_ids()),
                "backup_size": "unknown",  # Will be updated after creation
            },
        }

        manifest_content = json.dumps(manifest, indent=2)
        zipf.writestr("manifest.json", manifest_content)

    @handle_errors("adding directory to zip")
    def _add_directory_to_zip(
        self, zipf: zipfile.ZipFile, directory: str, zip_path: str
    ) -> None:
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

    @handle_errors("materializing directory backup", default_return=False)
    def _materialize_directory_backup(
        self, zip_backup_path: str, directory_backup_path: str
    ) -> bool:
        """Extract a zip payload to a directory backup and remove zip payload."""
        source_zip = Path(zip_backup_path)
        target_dir = Path(directory_backup_path)
        if not source_zip.exists():
            return False
        if target_dir.exists():
            if target_dir.is_file():
                target_dir.unlink()
            else:
                shutil.rmtree(target_dir, ignore_errors=True)
        target_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(source_zip, "r") as zipf:
            zipf.extractall(target_dir)
        manifest_path = target_dir / "manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                if isinstance(manifest, dict):
                    manifest["format"] = "directory"
                    with open(manifest_path, "w", encoding="utf-8") as f:
                        json.dump(manifest, f, indent=2)
            except Exception:
                pass
        source_zip.unlink(missing_ok=True)
        return True

    @handle_errors("checking directory backup path", default_return=False)
    def _is_directory_backup_path(self, file_path: Path) -> bool:
        """Return True when path is a backup directory with manifest."""
        return file_path.is_dir() and (file_path / "manifest.json").exists()

    @handle_errors("getting backup artifact size", default_return=0)
    def _get_backup_artifact_size_bytes(self, backup_path: str) -> int:
        """Return size in bytes for file or directory backup artifact."""
        path = Path(backup_path)
        if path.is_file():
            return path.stat().st_size
        if path.is_dir():
            total = 0
            for child in path.rglob("*"):
                if child.is_file():
                    total += child.stat().st_size
            return total
        return 0

    @handle_errors("cleaning up old backups")
    def _cleanup_old_backups(self) -> None:
        """Remove old backups by count and age retention policy."""
        try:
            # Ensure backup directory exists before iterating (race condition fix)
            if not os.path.exists(self.backup_dir):
                return

            # Gather backup artifacts (zip files and directory backups) with mtime
            backup_files: list[tuple[str, float]] = []
            now_ts = time.time()
            backup_dir_path = Path(self.backup_dir)

            # Re-check directory exists (parallel tests may delete it)
            if not backup_dir_path.exists():
                return

            try:
                for file_path in backup_dir_path.iterdir():
                    if file_path.is_file() and file_path.suffix == ".zip":
                        try:
                            mtime = file_path.stat().st_mtime
                            backup_files.append((str(file_path), mtime))
                        except Exception:
                            continue
                    elif self._is_directory_backup_path(file_path):
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
                            if Path(file_path).is_dir():
                                shutil.rmtree(file_path, ignore_errors=True)
                            else:
                                os.remove(file_path)
                            logger.debug(
                                f"Removed backup by age (> {self.backup_retention_days}d): {file_path}"
                            )
                            backup_files.remove((file_path, mtime))
                    except Exception as e:
                        logger.warning(f"Failed to remove old backup {file_path}: {e}")

            # Count-based retention:
            # - Keep weekly backups in a dedicated bucket so frequent auto backups
            #   do not evict weekly recovery points.
            # - Keep non-weekly backups in the standard bucket.
            weekly_backups: list[tuple[str, float]] = []
            non_weekly_backups: list[tuple[str, float]] = []
            for file_path, mtime in backup_files:
                if self._is_weekly_backup_artifact(file_path):
                    weekly_backups.append((file_path, mtime))
                else:
                    non_weekly_backups.append((file_path, mtime))

            weekly_backups.sort(key=lambda x: x[1], reverse=True)
            non_weekly_backups.sort(key=lambda x: x[1], reverse=True)

            for file_path, _ in weekly_backups[self.weekly_max_backups :]:
                try:
                    if os.path.exists(file_path):
                        if Path(file_path).is_dir():
                            shutil.rmtree(file_path, ignore_errors=True)
                        else:
                            os.remove(file_path)
                        logger.debug(
                            f"Removed weekly backup by count (>{self.weekly_max_backups}): {file_path}"
                        )
                except Exception as e:
                    logger.warning(f"Failed to remove old weekly backup {file_path}: {e}")

            for file_path, _ in non_weekly_backups[self.max_backups :]:
                try:
                    if os.path.exists(file_path):
                        if Path(file_path).is_dir():
                            shutil.rmtree(file_path, ignore_errors=True)
                        else:
                            os.remove(file_path)
                        logger.debug(
                            f"Removed backup by count (>{self.max_backups}): {file_path}"
                        )
                except Exception as e:
                    logger.warning(f"Failed to remove old backup {file_path}: {e}")
        except Exception as e:
            logger.warning(f"Backup cleanup encountered an error: {e}")

    @handle_errors("checking if backup artifact is weekly", default_return=False)
    def _is_weekly_backup_artifact(self, file_path: str) -> bool:
        """Return True when backup artifact name indicates weekly cadence."""
        artifact_name = Path(file_path).name
        return artifact_name.startswith("weekly_backup_")

    @handle_errors("listing available backups", default_return=[])
    def list_backups(self) -> list[dict]:
        """List all available backups with metadata."""
        backups = []

        # Ensure backup directory exists
        backup_dir_path = Path(self.backup_dir)
        if not backup_dir_path.exists():
            logger.warning(f"Backup directory does not exist: {self.backup_dir}")
            return backups

        try:
            for file_path in backup_dir_path.iterdir():
                if (file_path.is_file() and file_path.suffix == ".zip") or self._is_directory_backup_path(file_path):
                    try:
                        backup_info = self._get_backup_info(str(file_path))
                        # Only include backups with valid info (non-empty dict)
                        if backup_info:
                            backups.append(backup_info)
                    except Exception as e:
                        logger.warning(
                            f"Failed to get info for backup {file_path.name}: {e}"
                        )
        except Exception as e:
            logger.error(f"Error listing backups from {self.backup_dir}: {e}")

        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return backups

    @handle_errors("getting backup info", default_return={})
    def _get_backup_info(self, backup_path: str) -> dict:
        """Get information about a specific backup."""
        try:
            backup_obj = Path(backup_path)
            if backup_obj.is_dir():
                manifest_path = backup_obj / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                    return {
                        "file_path": backup_path,
                        "file_name": backup_obj.name,
                        "file_size": self._get_backup_artifact_size_bytes(backup_path),
                        "created_at": manifest.get("created_at"),
                        "backup_name": manifest.get("backup_name"),
                        "includes": manifest.get("includes", {}),
                        "system_info": manifest.get("system_info", {}),
                    }
                created_at_dt = datetime.fromtimestamp(os.path.getmtime(backup_path))
                created_at = format_timestamp(created_at_dt, TIMESTAMP_FULL)
                return {
                    "file_path": backup_path,
                    "file_name": backup_obj.name,
                    "file_size": self._get_backup_artifact_size_bytes(backup_path),
                    "created_at": created_at,
                    "backup_name": backup_obj.name,
                    "includes": {},
                    "system_info": {},
                }
            # LEGACY COMPATIBILITY: Zip backup read support retained for historical artifacts.
            logger.info(
                f"LEGACY COMPATIBILITY: Reading zip backup metadata: {backup_obj.name}"
            )
            with zipfile.ZipFile(backup_path, "r") as zipf:
                if "manifest.json" in zipf.namelist():
                    manifest_content = zipf.read("manifest.json")
                    manifest = json.loads(manifest_content)
                    return {
                        "file_path": backup_path,
                        "file_name": os.path.basename(backup_path),
                        "file_size": os.path.getsize(backup_path),
                        "created_at": manifest.get("created_at"),
                        "backup_name": manifest.get("backup_name"),
                        "includes": manifest.get("includes", {}),
                        "system_info": manifest.get("system_info", {}),
                    }
                # Fallback for backups without manifest
                created_at_dt = datetime.fromtimestamp(os.path.getmtime(backup_path))
                created_at = format_timestamp(created_at_dt, TIMESTAMP_FULL)
                return {
                    "file_path": backup_path,
                    "file_name": os.path.basename(backup_path),
                    "file_size": os.path.getsize(backup_path),
                    "created_at": created_at,
                    "backup_name": "Unknown",
                    "includes": {},
                    "system_info": {},
                }
        except Exception as e:
            logger.error(f"Failed to read backup info for {backup_path}: {e}")
            return {}

    @handle_errors("restoring backup", default_return=False)
    def restore_backup(
        self, backup_path: str, restore_users: bool = True, restore_config: bool = False
    ) -> bool:
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
            backup_obj = Path(backup_path)
            if backup_obj.is_dir():
                if restore_users:
                    self._restore_user_data_from_directory(backup_obj)
                if restore_config:
                    self._restore_config_files_from_directory(backup_obj)
                logger.info(f"Directory backup restored successfully from: {backup_path}")
                return True

            # LEGACY COMPATIBILITY: Zip backup restore path for historical artifacts.
            logger.info(
                f"LEGACY COMPATIBILITY: Restoring from zip backup artifact: {backup_obj.name}"
            )
            with zipfile.ZipFile(backup_path, "r") as zipf:
                if restore_users:
                    try:
                        self._restore_user_data(zipf)
                    except Exception as e:
                        logger.error(f"Failed to restore user data: {e}")
                        raise

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

    @handle_errors("restoring backup to isolated destination", default_return=False)
    def restore_backup_to_path(
        self,
        backup_path: str,
        destination: str,
        restore_users: bool = True,
        restore_config: bool = False,
    ) -> bool:
        """
        Restore backup contents into an isolated destination path.

        This API is non-destructive to active runtime data directories.
        """
        if not backup_path or not isinstance(backup_path, str):
            logger.error(f"Invalid backup_path: {backup_path}")
            return False
        if not destination or not isinstance(destination, str):
            logger.error(f"Invalid destination: {destination}")
            return False
        if not isinstance(restore_users, bool):
            logger.error(f"Invalid restore_users: {restore_users}")
            return False
        if not isinstance(restore_config, bool):
            logger.error(f"Invalid restore_config: {restore_config}")
            return False
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False

        is_valid, errors = self.validate_backup(backup_path)
        if not is_valid:
            logger.error(f"Backup validation failed for isolated restore: {errors}")
            return False

        destination_path = Path(destination).resolve()
        destination_path.mkdir(parents=True, exist_ok=True)

        extracted_total = 0
        backup_obj = Path(backup_path)
        if backup_obj.is_dir():
            if restore_users:
                extracted_total += self._copy_directory_prefix_to_destination(
                    backup_obj, prefix="users", destination=destination_path
                )
            if restore_config:
                extracted_total += self._copy_directory_prefix_to_destination(
                    backup_obj, prefix="config", destination=destination_path
                )
        else:
            # LEGACY COMPATIBILITY: Zip backup drill support for historical artifacts.
            logger.info(
                f"LEGACY COMPATIBILITY: Drill restore from zip backup artifact: {backup_obj.name}"
            )
            with zipfile.ZipFile(backup_path, "r") as zipf:
                if restore_users:
                    extracted_total += self._extract_zip_prefix_to_destination(
                        zipf, prefix="users/", destination=destination_path
                    )
                if restore_config:
                    extracted_total += self._extract_zip_prefix_to_destination(
                        zipf, prefix="config/", destination=destination_path
                    )
        if extracted_total <= 0:
            logger.warning(
                "Isolated restore completed but no files were extracted from backup"
            )
        logger.info(
            f"Isolated restore completed successfully: {backup_path} -> {destination_path} ({extracted_total} files)"
        )
        return True

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

        extracted_count = self._extract_zip_prefix_to_destination(
            zipf, prefix="users/", destination=base_dir
        )

        logger.info(
            f"User data restored successfully ({extracted_count} files extracted)"
        )

    @handle_errors("restoring config files")
    def _restore_config_files(self, zipf: zipfile.ZipFile) -> None:
        """Restore configuration files from backup."""
        # Ensure base directory exists
        base_dir = Path(core.config.BASE_DATA_DIR)
        base_dir.mkdir(parents=True, exist_ok=True)

        extracted_count = self._extract_zip_prefix_to_destination(
            zipf, prefix="config/", destination=base_dir
        )

        logger.info(
            f"Configuration files restored successfully ({extracted_count} files extracted)"
        )

    @handle_errors("restoring user data from directory")
    def _restore_user_data_from_directory(self, backup_root: Path) -> None:
        """Restore user data from directory backup."""
        base_dir = Path(core.config.BASE_DATA_DIR)
        base_dir.mkdir(parents=True, exist_ok=True)
        user_info_path = Path(core.config.USER_INFO_DIR_PATH)
        if user_info_path.exists():
            shutil.rmtree(user_info_path, ignore_errors=True)
        source = backup_root / "users"
        if source.exists() and source.is_dir():
            target = base_dir / "users"
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            shutil.copytree(source, target)

    @handle_errors("restoring config files from directory")
    def _restore_config_files_from_directory(self, backup_root: Path) -> None:
        """Restore config files from directory backup."""
        base_dir = Path(core.config.BASE_DATA_DIR)
        base_dir.mkdir(parents=True, exist_ok=True)
        source = backup_root / "config"
        if not source.exists() or not source.is_dir():
            return
        target = base_dir / "config"
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(source, target)

    @handle_errors("copying directory prefix to destination", default_return=0)
    def _copy_directory_prefix_to_destination(
        self, backup_root: Path, prefix: str, destination: Path
    ) -> int:
        """Copy files from backup_root/<prefix> to destination/<prefix>."""
        source_root = backup_root / prefix
        if not source_root.exists() or not source_root.is_dir():
            return 0
        copied = 0
        destination = destination.resolve()
        for source_file in source_root.rglob("*"):
            if not source_file.is_file():
                continue
            rel = source_file.relative_to(source_root)
            target = (destination / prefix / rel).resolve()
            if destination not in target.parents and target != destination:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target)
            copied += 1
        return copied

    @handle_errors("extracting zip prefix to destination", default_return=0)
    def _extract_zip_prefix_to_destination(
        self, zipf: zipfile.ZipFile, prefix: str, destination: Path
    ) -> int:
        """Safely extract zip entries under prefix into destination."""
        extracted_count = 0
        destination = destination.resolve()
        for file_info in zipf.infolist():
            filename = file_info.filename
            if not filename.startswith(prefix):
                continue
            if filename.endswith("/"):
                continue
            try:
                target_path = (destination / filename).resolve()
            except Exception as e:
                logger.warning(f"Failed to resolve extraction path for {filename}: {e}")
                continue
            try:
                if destination not in target_path.parents and target_path != destination:
                    logger.warning(
                        f"Skipping unsafe path traversal attempt during restore: {filename}"
                    )
                    continue
            except Exception:
                logger.warning(f"Skipping untrusted extraction target: {filename}")
                continue
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zipf.open(file_info, "r") as source_file:
                    with open(target_path, "wb") as output_file:
                        shutil.copyfileobj(source_file, output_file)
                extracted_count += 1
            except Exception as e:
                logger.warning(f"Failed to extract {filename}: {e}")
        return extracted_count

    @handle_errors("checking backup file exists", default_return=False)
    def _validate_backup__check_file_exists(
        self, backup_path: str, errors: list[str]
    ) -> bool:
        """Check if the backup file exists and add error if not."""
        if not os.path.exists(backup_path):
            errors.append(f"Backup file not found: {backup_path}")
            return False
        return True

    @handle_errors("validating zip file contents", default_return=[])
    def _validate_backup__validate_zip_file(self, backup_path: str) -> list[str]:
        """Validate zip file integrity and contents."""
        errors = []

        try:
            with zipfile.ZipFile(backup_path, "r") as zipf:
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
    def _validate_backup__check_file_integrity(
        self, zipf: zipfile.ZipFile, errors: list[str]
    ) -> None:
        """Check if the zip file is not corrupted."""
        try:
            zipf.testzip()
        except Exception as e:
            errors.append(f"Backup file is corrupted: {e}")

    @handle_errors("validating manifest", default_return=None)
    def _validate_backup__validate_manifest(
        self, zipf: zipfile.ZipFile, errors: list[str]
    ) -> None:
        """Validate the backup manifest file."""
        if "manifest.json" not in zipf.namelist():
            errors.append("Backup missing manifest.json")
            return

        try:
            manifest_content = zipf.read("manifest.json")
            manifest = json.loads(manifest_content)

            # Validate required manifest fields
            if not manifest.get("created_at"):
                errors.append("Manifest missing creation timestamp")

            if not manifest.get("backup_name"):
                errors.append("Manifest missing backup name")

        except json.JSONDecodeError:
            errors.append("Manifest.json is not valid JSON")

    @handle_errors("validating content requirements", default_return=None)
    def _validate_backup__validate_content_requirements(
        self, zipf: zipfile.ZipFile, errors: list[str]
    ) -> None:
        """Validate that backup contains required content."""
        # Check for required user data
        # Note: Backups can be created without users (e.g., config-only backups)
        # Only warn if manifest indicates users should be included but none are found
        user_files = [f for f in zipf.namelist() if f.startswith("users/")]
        try:
            manifest_data = zipf.read("manifest.json")
            import json

            manifest = json.loads(manifest_data)
            if manifest.get("includes", {}).get("users", False) and not user_files:
                errors.append(
                    "Backup manifest indicates users should be included but no user data found"
                )
        except Exception:
            # If manifest can't be read or parsed, skip this check
            # The manifest validation will catch manifest issues separately
            pass

    @handle_errors("validating directory backup", default_return=[])
    def _validate_backup__validate_directory_backup(self, backup_path: str) -> list[str]:
        """Validate directory backup integrity and contents."""
        errors: list[str] = []
        backup_root = Path(backup_path)
        if not backup_root.is_dir():
            errors.append(f"Backup directory not found: {backup_path}")
            return errors
        manifest_path = backup_root / "manifest.json"
        if not manifest_path.exists():
            errors.append("Backup missing manifest.json")
            return errors
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            if not manifest.get("created_at"):
                errors.append("Manifest missing creation timestamp")
            if not manifest.get("backup_name"):
                errors.append("Manifest missing backup name")
            includes = manifest.get("includes", {})
            if includes.get("users", False):
                users_root = backup_root / "users"
                has_user_files = users_root.exists() and any(
                    p.is_file() for p in users_root.rglob("*")
                )
                if not has_user_files:
                    errors.append(
                        "Backup manifest indicates users should be included but no user data found"
                    )
        except json.JSONDecodeError:
            errors.append("Manifest.json is not valid JSON")
        except Exception as e:
            errors.append(f"Failed to read directory backup manifest: {e}")
        return errors

    @handle_errors("validating backup", default_return=(False, ["Validation failed"]))
    def validate_backup(self, backup_path: str) -> tuple[bool, list[str]]:
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

        backup_obj = Path(backup_path)
        if backup_obj.is_dir():
            dir_errors = self._validate_backup__validate_directory_backup(backup_path)
            errors.extend(dir_errors)
        else:
            # LEGACY COMPATIBILITY: Zip backup validation retained for historical artifacts.
            logger.info(
                f"LEGACY COMPATIBILITY: Validating zip backup artifact: {backup_obj.name}"
            )
            # Validate zip file integrity and contents
            zip_errors = self._validate_backup__validate_zip_file(backup_path)
            errors.extend(zip_errors)

        return len(errors) == 0, errors


# Global backup manager instance
backup_manager = BackupManager()


# Convenience functions for easy access
@handle_errors("creating automatic backup", default_return=None)
def create_automatic_backup(operation_name: str = "automatic") -> str | None:
    """
    Create an automatic backup before major operations.

    Args:
        operation_name: Name of the operation being performed

    Returns:
        Path to the backup file, or None if failed
    """
    timestamp = now_timestamp_filename()
    backup_name = f"auto_{operation_name}_{timestamp}"

    logger.info(f"Creating automatic backup: {backup_name}")
    return backup_manager.create_backup(backup_name)


@handle_errors("validating user index", default_return=False)
def _validate_system_state__validate_user_index() -> bool:
    """Validate the user index file and corresponding user directories."""
    user_index_path = Path(core.config.BASE_DATA_DIR) / "user_index.json"
    if not user_index_path.exists():
        return True  # Missing index is not an error, just means no users yet

    with open(user_index_path) as f:
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
        if key in ["last_updated"]:
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
