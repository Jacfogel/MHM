"""
File locking utilities for safe concurrent file access.

Provides Windows-compatible file locking for operations that need to be
thread-safe or process-safe, particularly for user_index.json operations
in parallel test execution.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, Callable, Any
from contextlib import contextmanager
from core.logger import get_component_logger
from core.error_handling import handle_errors

logger = get_component_logger(__name__)

# Windows-specific file locking using lock files
if sys.platform == 'win32':
    @contextmanager
    def file_lock(file_path: str, timeout: float = 30.0, retry_interval: float = 0.1):
        """
        Context manager for file locking on Windows.
        
        Uses a separate lock file (file_path + '.lock') to coordinate access.
        File creation is atomic on Windows, so we use file existence as the lock.
        
        Args:
            file_path: Path to the file to lock
            timeout: Maximum time to wait for lock (seconds)
            retry_interval: Time between lock attempts (seconds)
            
        Yields:
            File handle (opened in 'r+b' mode)
            
        Raises:
            TimeoutError: If lock cannot be acquired within timeout
            OSError: If file operations fail
        """
        # Ensure directory exists
        lock_file_path = Path(file_path)
        lock_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Lock file path (separate file for coordination)
        lock_file = Path(str(file_path) + '.lock')
        lock_file.parent.mkdir(parents=True, exist_ok=True)
        
        start_time = time.time()
        lock_acquired = False
        
        try:
            # Try to acquire lock by creating lock file
            while not lock_acquired:
                try:
                    # Try to create lock file exclusively (fails if it exists)
                    # Use 'x' mode which fails if file exists (atomic on Windows)
                    lock_handle = open(lock_file, 'x')
                    lock_handle.close()
                    lock_acquired = True
                    break
                except FileExistsError:
                    # Lock file exists - another process has the lock
                    # Check timeout
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        raise TimeoutError(
                            f"Could not acquire lock on {file_path} within {timeout} seconds"
                        )
                    
                    # Wait before retrying
                    time.sleep(retry_interval)
                    continue
                except (OSError, IOError) as e:
                    # Other errors - check timeout
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        raise TimeoutError(
                            f"Could not acquire lock on {file_path} within {timeout} seconds: {e}"
                        )
                    
                    # Wait before retrying
                    time.sleep(retry_interval)
                    continue
            
            # Open the actual file for reading/writing
            file_handle = None
            try:
                # Open file in binary read-write mode
                file_handle = open(lock_file_path, 'r+b')
            except FileNotFoundError:
                # File doesn't exist - create it
                file_handle = open(lock_file_path, 'w+b')
            
            # Yield the file handle
            yield file_handle
            
        finally:
            # Close file handle
            if file_handle:
                try:
                    file_handle.close()
                except (OSError, IOError):
                    pass
            
            # Release lock by removing lock file
            if lock_acquired:
                try:
                    if lock_file.exists():
                        lock_file.unlink()
                except (OSError, IOError):
                    # Ignore errors during cleanup - lock file will be cleaned up eventually
                    logger.debug(f"Could not remove lock file {lock_file}, but continuing")
                    
else:
    # Unix/Linux file locking using fcntl
    import fcntl
    
    @contextmanager
    def file_lock(file_path: str, timeout: float = 30.0, retry_interval: float = 0.1):
        """
        Context manager for file locking on Unix/Linux.
        
        Uses fcntl.flock() to acquire an exclusive lock on a file.
        Retries if the file is locked by another process.
        
        Args:
            file_path: Path to the file to lock
            timeout: Maximum time to wait for lock (seconds)
            retry_interval: Time between lock attempts (seconds)
            
        Yields:
            File handle (opened in 'r+b' mode for locking)
            
        Raises:
            TimeoutError: If lock cannot be acquired within timeout
            OSError: If file operations fail
        """
        # Ensure directory exists
        lock_file_path = Path(file_path)
        lock_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create lock file if it doesn't exist (empty file)
        if not lock_file_path.exists():
            lock_file_path.touch()
        
        # Open file in binary read-write mode
        file_handle = None
        start_time = time.time()
        
        try:
            while True:
                try:
                    # Open file in binary read-write mode
                    file_handle = open(lock_file_path, 'r+b')
                    
                    # Try to acquire exclusive non-blocking lock
                    try:
                        fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        # Lock acquired successfully
                        break
                    except IOError:
                        # File is locked by another process
                        file_handle.close()
                        file_handle = None
                        
                        # Check timeout
                        elapsed = time.time() - start_time
                        if elapsed >= timeout:
                            raise TimeoutError(
                                f"Could not acquire lock on {file_path} within {timeout} seconds"
                            )
                        
                        # Wait before retrying
                        time.sleep(retry_interval)
                        continue
                        
                except (OSError, IOError) as e:
                    if file_handle:
                        file_handle.close()
                        file_handle = None
                    
                    # Check timeout
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        raise TimeoutError(
                            f"Could not acquire lock on {file_path} within {timeout} seconds: {e}"
                        )
                    
                    # Wait before retrying
                    time.sleep(retry_interval)
                    continue
            
            # Yield the file handle
            yield file_handle
            
        finally:
            # Release lock and close file
            if file_handle:
                try:
                    # Unlock the file
                    fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
                except (OSError, IOError):
                    # Ignore unlock errors during cleanup
                    pass
                finally:
                    file_handle.close()


def safe_json_read(file_path: str, default: Optional[dict] = None) -> dict:
    """
    Safely read JSON file with file locking.
    
    Args:
        file_path: Path to JSON file
        default: Default value to return if file doesn't exist or is invalid
        
    Returns:
        dict: Parsed JSON data or default value
    """
    import json
    
    if default is None:
        default = {}
    
    if not os.path.exists(file_path):
        return default
    
    try:
        with file_lock(file_path, timeout=10.0):
            # File is locked, safe to read
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError, TimeoutError) as e:
        logger.warning(f"Error reading JSON file {file_path}: {e}")
        return default


@handle_errors("writing JSON file with locking", user_friendly=False, default_return=False)
def safe_json_write(file_path: str, data: dict, indent: int = 2) -> bool:
    """
    Safely write JSON file with file locking and atomic write.
    
    Uses atomic write pattern: write to temp file, then rename.
    This prevents corruption if the process crashes during write.
    
    Args:
        file_path: Path to JSON file
        data: Data to write (must be JSON-serializable)
        indent: JSON indentation level
        
    Returns:
        bool: True if write succeeded, False otherwise
    """
    import json
    import tempfile
    import shutil
    
    file_path_obj = Path(file_path)
    file_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Use atomic write: write to temp file, then rename
    temp_file = None
    try:
        # Create temp file in same directory (required for atomic rename on Windows)
        temp_fd, temp_file = tempfile.mkstemp(
            dir=file_path_obj.parent,
            prefix='.tmp_',
            suffix='.json'
        )
        
        # Write JSON to temp file
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        # Acquire lock and perform atomic rename
        with file_lock(file_path, timeout=10.0):
            # Rename temp file to target (atomic on Windows)
            shutil.move(temp_file, file_path)
            temp_file = None  # Prevent cleanup
            
        return True
    finally:
        # Clean up temp file if it exists (only if move failed)
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass

