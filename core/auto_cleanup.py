#!/usr/bin/env python3
"""
Automated Python cache cleanup module.
Tracks when cleanup was last performed and only runs if more than 30 days have passed.
"""

import os
import shutil
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import core.config
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)
from core.logger import get_component_logger

# Get component logger for this module
logger = get_component_logger('main')

# File to track last cleanup timestamp
CLEANUP_TRACKER_FILE = ".last_cache_cleanup"
DEFAULT_CLEANUP_INTERVAL_DAYS = 30

@handle_errors("getting last cleanup timestamp", default_return=0)
def get_last_cleanup_timestamp():
    """Get the timestamp of the last cleanup from tracker file."""
    if os.path.exists(CLEANUP_TRACKER_FILE):
        with open(CLEANUP_TRACKER_FILE, 'r') as f:
            data = json.load(f)
            return data.get('last_cleanup_timestamp', 0)
    logger.debug("No valid cleanup tracker file found")
    return 0

@handle_errors("updating cleanup timestamp")
def update_cleanup_timestamp():
    """Update the cleanup tracker file with current timestamp."""
    data = {
        'last_cleanup_timestamp': time.time(),
        'last_cleanup_date': datetime.now().isoformat()
    }
    with open(CLEANUP_TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    logger.debug(f"Updated cleanup timestamp: {data['last_cleanup_date']}")

@handle_errors("checking if cleanup should run", default_return=False)
def should_run_cleanup(interval_days=DEFAULT_CLEANUP_INTERVAL_DAYS):
    """Check if cleanup should run based on last cleanup time."""
    last_cleanup = get_last_cleanup_timestamp()
    if last_cleanup == 0:
        # Never cleaned up before
        return True
    
    time_since_cleanup = time.time() - last_cleanup
    days_since_cleanup = time_since_cleanup / (24 * 60 * 60)
    
    should_cleanup = days_since_cleanup >= interval_days
    
    if should_cleanup:
        logger.info(f"Cache cleanup needed: {days_since_cleanup:.1f} days since last cleanup")
    else:
        logger.debug(f"Cache cleanup not needed: {days_since_cleanup:.1f} days since last cleanup")
    
    return should_cleanup

@handle_errors("finding pycache directories", default_return=[])
def find_pycache_dirs(root_path):
    """Find all __pycache__ directories recursively."""
    pycache_dirs = []
    for root, dirs, files in os.walk(root_path):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            pycache_dirs.append(pycache_path)
    return pycache_dirs

@handle_errors("finding pyc files", default_return=[])
def find_pyc_files(root_path):
    """Find all .pyc files recursively."""
    pyc_files = []
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if file.endswith('.pyc') or file.endswith('.pyo'):
                pyc_files.append(os.path.join(root, file))
    return pyc_files

@handle_errors("calculating cache size", default_return=0)
def calculate_cache_size(pycache_dirs, pyc_files):
    """Calculate total size of cache files."""
    total_size = 0
    
    # Calculate size of __pycache__ directories
    for pycache_dir in pycache_dirs:
        try:
            if os.path.exists(pycache_dir):
                for root, dirs, files in os.walk(pycache_dir):
                    for file in files:
                        filepath = os.path.join(root, file)
                        if os.path.exists(filepath):
                            total_size += os.path.getsize(filepath)
        except Exception as e:
            logger.warning(f"Error calculating size for {pycache_dir}: {e}")
    
    # Calculate size of standalone .pyc files
    for pyc_file in pyc_files:
        try:
            if os.path.exists(pyc_file):
                total_size += os.path.getsize(pyc_file)
        except Exception as e:
            logger.warning(f"Error calculating size for {pyc_file}: {e}")
    
    return total_size

@handle_errors("discovering cache files", default_return=([], []))
def _perform_cleanup__discover_cache_files(root_path):
    """Discover all cache files and directories in the given root path."""
    pycache_dirs = find_pycache_dirs(root_path)
    pyc_files = find_pyc_files(root_path)
    return pycache_dirs, pyc_files

@handle_errors("logging discovery results", default_return=0)
def _perform_cleanup__log_discovery_results(pycache_dirs, pyc_files):
    """Calculate total size and log discovery results."""
    total_size = calculate_cache_size(pycache_dirs, pyc_files)
    
    logger.info(f"Found {len(pycache_dirs)} __pycache__ directories and {len(pyc_files)} .pyc files")
    logger.info(f"Total cache size: {total_size / 1024:.1f} KB ({total_size / (1024*1024):.2f} MB)")
    
    return total_size

@handle_errors("removing cache files", default_return=(0, 0))
def _perform_cleanup__remove_cache_files(pycache_dirs, pyc_files):
    """Remove all discovered cache directories and files."""
    # Remove __pycache__ directories
    removed_dirs = _perform_cleanup__remove_cache_directories(pycache_dirs)
    
    # Remove standalone .pyc files
    removed_files = _perform_cleanup__remove_cache_files_list(pyc_files)
    
    return removed_dirs, removed_files

@handle_errors("removing cache directories", default_return=0)
def _perform_cleanup__remove_cache_directories(pycache_dirs):
    """Remove all __pycache__ directories."""
    removed_dirs = 0
    for pycache_dir in pycache_dirs:
        try:
            if os.path.exists(pycache_dir):
                shutil.rmtree(pycache_dir)
                removed_dirs += 1
                logger.debug(f"Removed directory: {pycache_dir}")
        except Exception as e:
            logger.warning(f"Failed to remove directory {pycache_dir}: {e}")
    return removed_dirs

@handle_errors("removing cache files list", default_return=0)
def _perform_cleanup__remove_cache_files_list(pyc_files):
    """Remove all standalone .pyc files."""
    removed_files = 0
    for pyc_file in pyc_files:
        try:
            if os.path.exists(pyc_file):
                os.remove(pyc_file)
                removed_files += 1
                logger.debug(f"Removed file: {pyc_file}")
        except Exception as e:
            logger.warning(f"Failed to remove file {pyc_file}: {e}")
    return removed_files

@handle_errors("logging completion results")
def _perform_cleanup__log_completion_results(removed_dirs, removed_files, total_size):
    """Log the final cleanup results and statistics."""
    logger.info(f"Cleanup complete: Removed {removed_dirs} directories and {removed_files} files")
    logger.info(f"Freed up {total_size / 1024:.1f} KB ({total_size / (1024*1024):.2f} MB)")

@handle_errors("performing cleanup", default_return=False)
def perform_cleanup(root_path='.'):
    """Perform the actual cleanup of cache files."""
    root_path = Path(root_path).resolve()
    
    logger.info(f"Starting automatic cache cleanup in: {root_path}")
    
    # Find cache files
    pycache_dirs, pyc_files = _perform_cleanup__discover_cache_files(root_path)
    
    if not pycache_dirs and not pyc_files:
        logger.info("No cache files found to clean up")
        return True
    
    # Calculate total size and log discovery results
    total_size = _perform_cleanup__log_discovery_results(pycache_dirs, pyc_files)
    
    # Remove cache files
    removed_dirs, removed_files = _perform_cleanup__remove_cache_files(pycache_dirs, pyc_files)
    
    # Log final results
    _perform_cleanup__log_completion_results(removed_dirs, removed_files, total_size)
    
    return True

@handle_errors("auto cleanup if needed", default_return=False)
def auto_cleanup_if_needed(root_path='.', interval_days=DEFAULT_CLEANUP_INTERVAL_DAYS):
    """
    Main function to check if cleanup is needed and perform it if so.
    Returns True if cleanup was performed, False if not needed.
    """
    if not should_run_cleanup(interval_days):
        return False
    
    success = perform_cleanup(root_path)
    if success:
        # Also archive old messages during monthly cleanup
        try:
            archive_old_messages_for_all_users()
        except Exception as e:
            logger.warning(f"Message archiving failed during cleanup (non-critical): {e}")
        
        update_cleanup_timestamp()
        return True
    else:
        logger.error("Cleanup failed")
        return False

@handle_errors("archiving old messages for all users", default_return=False)
def archive_old_messages_for_all_users():
    """
    Archive old messages for all users during monthly cleanup.
    This runs alongside the cache cleanup to maintain message file sizes.
    """
    try:
        from core.user_data_handlers import get_all_user_ids
        from core.message_management import archive_old_messages
        
        user_ids = get_all_user_ids()
        if not user_ids:
            logger.debug("No users found for message archiving")
            return True
        
        logger.info(f"Starting message archiving for {len(user_ids)} users")
        
        archived_count = 0
        for user_id in user_ids:
            try:
                if archive_old_messages(user_id, days_to_keep=365):
                    archived_count += 1
                    logger.debug(f"Successfully archived messages for user {user_id}")
                else:
                    logger.debug(f"No messages to archive for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to archive messages for user {user_id}: {e}")
        
        logger.info(f"Message archiving completed: {archived_count}/{len(user_ids)} users processed")
        return True
        
    except Exception as e:
        logger.error(f"Error during message archiving: {e}")
        return False

@handle_errors("getting cleanup status", default_return={"error": "Failed to get status"})
def get_cleanup_status():
    """Get information about the cleanup status."""
    last_cleanup_timestamp = get_last_cleanup_timestamp()
    if last_cleanup_timestamp == 0:
        return {
            'last_cleanup': 'Never',
            'days_since': float('inf'),
            'next_cleanup': 'On next startup'
        }
    
    # Convert timestamp to datetime
    last_date = datetime.fromtimestamp(last_cleanup_timestamp)
    days_since = (datetime.now() - last_date).days
    next_cleanup_date = last_date + timedelta(days=DEFAULT_CLEANUP_INTERVAL_DAYS)
    
    return {
        'last_cleanup': last_date.strftime('%Y-%m-%d %H:%M:%S'),
        'days_since': days_since,
        'next_cleanup': next_cleanup_date.strftime('%Y-%m-%d') if next_cleanup_date > datetime.now() else 'Overdue'
    }

if __name__ == "__main__":
    # For testing purposes
    import sys
    from core.logger import setup_logging
    setup_logging()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        print("Force cleaning...")
        perform_cleanup()
        update_cleanup_timestamp()
    elif len(sys.argv) > 1 and sys.argv[1] == "--status":
        status = get_cleanup_status()
        print(f"Last cleanup: {status['last_cleanup']}")
        print(f"Days since cleanup: {status['days_since']}")
        print(f"Next cleanup: {status['next_cleanup']}")
    else:
        result = auto_cleanup_if_needed()
        print(f"Cleanup performed: {result}") 