#!/usr/bin/env python3
"""
MHM Test Data Cleanup Script
Removes test users, old backup files, and unnecessary scripts
"""

import os
import shutil
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from core
sys.path.append(str(Path(__file__).parent.parent))

from core.logger import get_logger

logger = get_logger(__name__)

def get_script_dir():
    """Get the MHM root directory"""
    return Path(__file__).parent.parent

def cleanup_test_users():
    """Remove test user directories"""
    users_dir = get_script_dir() / "data" / "users"
    
    # Test users to remove (based on the names in your list)
    test_users = [
        "fake_user_12345",
        "test_user_12345", 
        "test_user_cancel",
        "test_user_checkin_prefs",
        "test_user_daily_checkin",
        "test_user_validation"
    ]
    
    removed_count = 0
    for test_user in test_users:
        user_path = users_dir / test_user
        if user_path.exists() and user_path.is_dir():
            try:
                shutil.rmtree(user_path)
                logger.info(f"Removed test user directory: {test_user}")
                print(f"✓ Removed test user: {test_user}")
                removed_count += 1
            except Exception as e:
                logger.error(f"Failed to remove test user {test_user}: {e}")
                print(f"✗ Failed to remove test user {test_user}: {e}")
        else:
            print(f"- Test user {test_user} not found")
    
    print(f"\nRemoved {removed_count} test user directories")

def cleanup_backup_files():
    """Remove backup files from migration and testing"""
    root_dir = get_script_dir()
    removed_count = 0
    
    # Patterns to look for
    backup_patterns = [
        "*.backup_*",
        "*_backup_*"
    ]
    
    # Directories to search
    search_dirs = [
        root_dir / "data",
        root_dir / "scripts"
    ]
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        for pattern in backup_patterns:
            for backup_file in search_dir.rglob(pattern):
                if backup_file.is_file():
                    try:
                        backup_file.unlink()
                        logger.info(f"Removed backup file: {backup_file}")
                        print(f"✓ Removed backup: {backup_file.name}")
                        removed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to remove backup {backup_file}: {e}")
                        print(f"✗ Failed to remove backup {backup_file}: {e}")
                elif backup_file.is_dir():
                    try:
                        shutil.rmtree(backup_file)
                        logger.info(f"Removed backup directory: {backup_file}")
                        print(f"✓ Removed backup directory: {backup_file.name}")
                        removed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to remove backup directory {backup_file}: {e}")
                        print(f"✗ Failed to remove backup directory {backup_file}: {e}")
    
    print(f"Removed {removed_count} backup files/directories")

def cleanup_old_scripts():
    """Remove old migration and testing scripts that are no longer needed"""
    scripts_dir = get_script_dir() / "scripts"
    
    # Scripts and directories we can safely remove
    items_to_remove = [
        # Migration scripts - migration is complete
        "migration/timestamp_migration.py",
        "migration/data_migration.py", 
        "migration/migrate_data.py",
        "migration/__pycache__",
        
        # Testing scripts - no longer needed
        "testing/simple_timestamp_check.py",
        "testing/audit_timestamps.py",
        "testing/test_migration_complete.py",
        "testing/test_migration_fix.py",
        "testing/test_timestamp_migration.py",
        "testing/__pycache__",
        "testing/test_checkin_preferences.py",
        "testing/test_daily_checkin.py",
        "testing/test_lm_studio.py",
        
        # Cleanup scripts - the old timestamp cleanup is done
        "cleanup/remove_timestamp_backward_compatibility.py",
        
        # Top-level script that's been superseded
        "remove_backwards_compatibility.py",
        
        # Empty planning directory
        "planning"
    ]
    
    removed_count = 0
    for item_path in items_to_remove:
        full_path = scripts_dir / item_path
        if full_path.exists():
            try:
                if full_path.is_file():
                    full_path.unlink()
                    logger.info(f"Removed script file: {item_path}")
                    print(f"✓ Removed script: {item_path}")
                elif full_path.is_dir():
                    shutil.rmtree(full_path)
                    logger.info(f"Removed script directory: {item_path}")
                    print(f"✓ Removed script directory: {item_path}")
                removed_count += 1
            except Exception as e:
                logger.error(f"Failed to remove {item_path}: {e}")
                print(f"✗ Failed to remove {item_path}: {e}")
        else:
            print(f"- Script {item_path} not found")
    
    print(f"Removed {removed_count} old script files/directories")

def main():
    """Run the cleanup process"""
    print("🧹 MHM Test Data Cleanup")
    print("=" * 50)
    
    try:
        print("\n📁 Cleaning up test users...")
        cleanup_test_users()
        
        print("\n💾 Cleaning up backup files...")
        cleanup_backup_files()
        
        print("\n📜 Cleaning up old scripts...")
        cleanup_old_scripts()
        
        print("\n✅ Cleanup completed successfully!")
        print("\nYour MHM installation is now cleaner:")
        print("• Test users removed from data/users/")
        print("• Migration and testing backup files removed")
        print("• Obsolete scripts removed from scripts/")
        print("\nOnly your real user data and active scripts remain.")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        print(f"\n❌ Cleanup failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 