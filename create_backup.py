#!/usr/bin/env python
"""Temporary script to create backup for check-in questions enhancement."""
from core.backup_manager import BackupManager

bm = BackupManager()
backup_path = bm.create_backup("checkin_questions_enhancement_backup")
print(f"Backup created at: {backup_path}")

if backup_path:
    is_valid, errors = bm.validate_backup(backup_path)
    print(f"Backup valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")
else:
    print("Backup creation failed")
