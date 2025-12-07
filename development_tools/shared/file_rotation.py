# TOOL_TIER: supporting

"""
File rotation utility for AI development tools.
Provides file rotation, backup, and archiving functionality.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.logger import get_component_logger

logger = get_component_logger("development_tools")


class FileRotator:
    """Handles file rotation, backup, and archiving for AI development tools."""
    
    def __init__(self, base_dir: str = "development_tools"):
        self.base_dir = Path(base_dir)
        # If base_dir is development_tools/, archive goes to reports/archive
        if self.base_dir.name == "development_tools" or str(self.base_dir).endswith(os.sep + "development_tools"):
            self.archive_dir = self.base_dir / "reports" / "archive"
        else:
            self.archive_dir = self.base_dir / "archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Default rotation settings
        self.max_versions = 7  # Default: keep 7 versions
        self.rotation_suffix = "%Y-%m-%d_%H%M%S"  # Timestamp format
        self._rotation_counter = 0  # Counter to ensure unique filenames
    
    def rotate_file(self, file_path: str, max_versions: int = None) -> str:
        """
        Rotate a file by backing up existing versions and creating a new one.
        
        Args:
            file_path: Path to the file to rotate
            max_versions: Maximum number of backup versions to keep (defaults to 7)
            
        Returns:
            Path to the new file (same as input)
        """
        # Skip rotation if disabled (e.g., during tests)
        if os.environ.get('DISABLE_LOG_ROTATION') == '1':
            return str(file_path)
            
        if max_versions is None:
            max_versions = self.max_versions
            
        file_path = Path(file_path)
        
        # If file doesn't exist, just return the path
        if not file_path.exists():
            return str(file_path)
        
        # Create timestamp for this rotation
        # Add counter to ensure uniqueness even if rotations happen in the same second
        timestamp = datetime.now().strftime(self.rotation_suffix)
        self._rotation_counter += 1
        archive_name = f"{file_path.stem}_{timestamp}_{self._rotation_counter:04d}{file_path.suffix}"
        archive_path = self.archive_dir / archive_name
        
        # If file already exists (shouldn't happen with counter, but be safe), append counter
        counter = 1
        while archive_path.exists():
            archive_name = f"{file_path.stem}_{timestamp}_{self._rotation_counter:04d}_{counter}{file_path.suffix}"
            archive_path = self.archive_dir / archive_name
            counter += 1
        
        shutil.move(str(file_path), str(archive_path))
        
        # Log the rotation
        if logger:
            logger.info(f"Rotated file {file_path} to {archive_path}")
        
        # Clean up old versions if we have too many
        self._cleanup_old_versions(file_path.stem, max_versions)
        
        return str(file_path)
    
    def _cleanup_old_versions(self, base_name: str, max_versions: int):
        """Remove old versions beyond max_versions limit."""
        pattern = f"{base_name}_*"
        existing_files = list(self.archive_dir.glob(pattern))
        
        # Filter to ensure we only get files that match the expected pattern
        filtered_files = [f for f in existing_files if f.name.startswith(f"{base_name}_")]
        
        if len(filtered_files) > max_versions:
            # Sort by modification time (oldest first)
            filtered_files.sort(key=lambda x: x.stat().st_mtime)
            
            # Remove oldest files beyond the limit
            files_to_remove = filtered_files[:-max_versions]
            for file_path in files_to_remove:
                try:
                    file_path.unlink()
                except (OSError, FileNotFoundError):
                    # File may have been removed already, ignore
                    pass
    
    def get_latest_archive(self, base_name: str) -> Optional[Path]:
        """Get the most recent archived version of a file."""
        pattern = f"{base_name}_*"
        existing_files = list(self.archive_dir.glob(pattern))
        
        if not existing_files:
            return None
        
        # Return the most recently modified file
        return max(existing_files, key=lambda x: x.stat().st_mtime)
    
    def list_archives(self, base_name: str) -> list:
        """List all archived versions of a file."""
        # Match files that start with base_name followed by underscore and timestamp
        # Pattern should match: base_name_YYYY-MM-DD_HHMMSS.ext
        pattern = f"{base_name}_*"
        existing_files = list(self.archive_dir.glob(pattern))
        
        # Filter to ensure we only get files that match the expected pattern
        # (base_name followed by underscore, not just any file starting with base_name)
        filtered_files = [f for f in existing_files if f.name.startswith(f"{base_name}_")]
        
        # Sort by modification time (newest first)
        filtered_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return filtered_files


def create_output_file(file_path: str, content: str, rotate: bool = True, max_versions: int = None, project_root: Optional[Path] = None) -> Path:
    """
    Create an output file with optional rotation.
    
    Args:
        file_path: Path to the output file (relative to project_root if project_root provided)
        content: Content to write to the file
        rotate: Whether to rotate existing files
        max_versions: Maximum number of backup versions to keep
        project_root: Optional project root to resolve relative paths against
        
    Returns:
        Path object pointing to the created file
    """
    # Check if this is a status file write during audit (defensive check)
    file_name = Path(file_path).name if isinstance(file_path, (str, Path)) else str(file_path)
    status_files = ['AI_STATUS.md', 'AI_PRIORITIES.md', 'consolidated_report.txt']
    if file_name in status_files:
        # Check if audit is in progress by looking for the global flag in operations module
        try:
            import sys
            if 'development_tools.shared.operations' in sys.modules:
                operations_module = sys.modules['development_tools.shared.operations']
                # Check both in-memory flag and file-based lock (for cross-process protection)
                # Use the helper function if available, otherwise fall back to direct check
                if hasattr(operations_module, '_is_audit_in_progress'):
                    # Use helper function that checks both in-memory and file-based lock
                    # Use project_root parameter if provided, otherwise try to infer from file_path
                    check_project_root = None
                    if project_root is not None:
                        # Use provided project_root parameter (most reliable)
                        check_project_root = Path(project_root).resolve()
                    else:
                        # Try to infer from file_path (fallback)
                        try:
                            inferred_root = Path(file_path).resolve()
                            # Go up to project root (file_path is like project_root/development_tools/AI_STATUS.md)
                            while inferred_root.name != 'development_tools' and inferred_root.parent != inferred_root:
                                inferred_root = inferred_root.parent
                            if inferred_root.name == 'development_tools':
                                inferred_root = inferred_root.parent
                            check_project_root = inferred_root
                        except Exception as e:
                            from core.logger import get_component_logger
                            debug_logger = get_component_logger("development_tools")
                            debug_logger.warning(f"Failed to infer project root from file_path for {file_name}: {e}")
                    
                    if check_project_root:
                        try:
                            is_in_progress = operations_module._is_audit_in_progress(check_project_root)
                            # Check result logged only if blocking (see warning below)
                        except Exception as e:
                            # If check fails, assume not in progress (defensive - don't block if we can't check)
                            from core.logger import get_component_logger
                            debug_logger = get_component_logger("development_tools")
                            debug_logger.warning(f"Failed to check audit status for {file_name}: {e}")
                            is_in_progress = False
                    else:
                        # Can't determine project root, assume not in progress (defensive)
                        is_in_progress = False
                elif hasattr(operations_module, '_AUDIT_IN_PROGRESS_GLOBAL') and operations_module._AUDIT_IN_PROGRESS_GLOBAL:
                    is_in_progress = True
                else:
                    is_in_progress = False
                
                if is_in_progress:
                    from core.logger import get_component_logger
                    logger = get_component_logger("development_tools")
                    logger.warning(f"create_output_file() called to write {file_name} during audit! Blocking write to prevent mid-audit status file changes.")
                    import traceback
                    call_stack = ''.join(traceback.format_stack())
                    logger.debug(f"Call stack for blocked {file_name} write attempt:\n{call_stack}")
                    # Raise exception to prevent the write
                    raise RuntimeError(f"Cannot write {file_name} during audit - status files should only be written at the end of audit")
        except RuntimeError:
            # Re-raise our blocking exception
            raise
        except Exception:
            # If check fails, continue (defensive check only - don't block if we can't check)
            pass
    
    # Status files are logged at DEBUG level when actually written (see operations.py for audit context)
    
    # Ensure file_path is a Path object
    if isinstance(file_path, str):
        file_path = Path(file_path)
    else:
        file_path = Path(file_path)
    
    # Resolve relative paths against project_root if provided
    if project_root is not None:
        if not file_path.is_absolute():
            file_path = project_root / file_path
        else:
            # If absolute, use as-is
            pass
    else:
        # Try to get project_root from config if not provided
        try:
            from ..config import config
            config_project_root = config.get_project_root()
            if config_project_root and not file_path.is_absolute():
                file_path = Path(config_project_root) / file_path
        except (ImportError, AttributeError):
            # If config not available, use path as-is
            pass
    
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Rotate if requested and file exists
    if rotate and file_path.exists():
        # For files in development_tools/, use reports/archive instead of archive
        file_path_obj = Path(file_path)
        # Check if file is directly in development_tools/ (not in a subdirectory)
        if file_path_obj.parent.name == "development_tools" or str(file_path_obj.parent).endswith(os.sep + "development_tools"):
            base_dir = file_path_obj.parent / "reports"
        else:
            base_dir = file_path_obj.parent
        # Ensure base_dir is a Path object before converting to string
        if isinstance(base_dir, str):
            base_dir = Path(base_dir)
        rotator = FileRotator(base_dir=str(base_dir))
        rotated_path = rotator.rotate_file(str(file_path), max_versions)
        # Ensure rotated_path is converted back to Path
        file_path = Path(rotated_path) if isinstance(rotated_path, str) else rotated_path
    
    # Write content to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return file_path


def append_to_log(log_file: str, content: str, max_size_mb: int = 10) -> str:
    """
    Append content to a log file with size-based rotation.
    
    Args:
        log_file: Path to the log file
        content: Content to append
        max_size_mb: Maximum size in MB before rotation
        
    Returns:
        Path to the log file
    """
    log_path = Path(log_file)
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists and is too large
    if log_path.exists() and log_path.stat().st_size > max_size_mb * 1024 * 1024:
        rotator = FileRotator()
        rotator.rotate_file(str(log_path))
    
    # Append content with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {content}\n"
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    return str(log_path)
