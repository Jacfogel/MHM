# TOOL_TIER: supporting
# TOOL_PORTABILITY: portable

"""
File rotation utility for AI development tools.
Uses the existing MHM log rotation infrastructure for consistency.
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
        self.archive_dir = self.base_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
        
        # Use MHM's existing rotation settings
        self.max_versions = 7  # Same as log rotation (7 days)
        self.rotation_suffix = "%Y-%m-%d_%H%M%S"  # Timestamp format
    
    def rotate_file(self, file_path: str, max_versions: int = None) -> str:
        """
        Rotate a file by backing up existing versions and creating a new one.
        Uses MHM's existing rotation patterns for consistency.
        
        Args:
            file_path: Path to the file to rotate
            max_versions: Maximum number of backup versions to keep (defaults to MHM setting)
            
        Returns:
            Path to the new file (same as input)
        """
        # Skip rotation if disabled (e.g., during tests) - same as MHM log rotation
        if os.environ.get('DISABLE_LOG_ROTATION') == '1':
            return str(file_path)
            
        if max_versions is None:
            max_versions = self.max_versions
            
        file_path = Path(file_path)
        
        # If file doesn't exist, just return the path
        if not file_path.exists():
            return str(file_path)
        
        # Create timestamp for this rotation (using MHM format)
        timestamp = datetime.now().strftime(self.rotation_suffix)
        
        # Move existing file to archive with timestamp
        archive_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        archive_path = self.archive_dir / archive_name
        
        shutil.move(str(file_path), str(archive_path))
        
        # Log the rotation (using MHM logger if available)
        if logger:
            logger.info(f"Rotated file {file_path} to {archive_path}")
        
        # Clean up old versions if we have too many
        self._cleanup_old_versions(file_path.stem, max_versions)
        
        return str(file_path)
    
    def _cleanup_old_versions(self, base_name: str, max_versions: int):
        """Remove old versions beyond max_versions limit."""
        pattern = f"{base_name}_*"
        existing_files = list(self.archive_dir.glob(pattern))
        
        if len(existing_files) > max_versions:
            # Sort by modification time (oldest first)
            existing_files.sort(key=lambda x: x.stat().st_mtime)
            
            # Remove oldest files beyond the limit
            files_to_remove = existing_files[:-max_versions]
            for file_path in files_to_remove:
                file_path.unlink()
    
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
        pattern = f"{base_name}_*"
        existing_files = list(self.archive_dir.glob(pattern))
        
        # Sort by modification time (newest first)
        existing_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return existing_files


def create_output_file(file_path: str, content: str, rotate: bool = True, max_versions: int = None) -> str:
    """
    Create an output file with optional rotation.
    
    Args:
        file_path: Path to the output file
        content: Content to write to the file
        rotate: Whether to rotate existing files
        max_versions: Maximum number of backup versions to keep
        
    Returns:
        Path to the created file
    """
    file_path = Path(file_path)
    
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Rotate if requested and file exists
    if rotate and file_path.exists():
        rotator = FileRotator()
        file_path = Path(rotator.rotate_file(str(file_path), max_versions))
    
    # Write content to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(file_path)


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
