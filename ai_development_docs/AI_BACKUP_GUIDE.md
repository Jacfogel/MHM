# AI Backup Guide

> **File**: `ai_development_docs/AI_BACKUP_GUIDE.md`  
> **Pair**: [BACKUP_GUIDE.md](../development_docs/BACKUP_GUIDE.md)  
> **Audience**: AI collaborators  
> **Purpose**: Fast routing and constraints for backup/archive operations  
> **Style**: Minimal, routing-first

> This AI document is paired with BACKUP_GUIDE.md. Keep this file's H2 headings in lockstep with BACKUP_GUIDE.md whenever you change the structure. For detailed guidance, examples, and rationale, use the matching sections in BACKUP_GUIDE.md.

---

## 1. Log Rotation System

**Where to look:**
- Implementation: `core/logger.py` - `BackupDirectoryRotatingFileHandler`
- Configuration: `core/config.py` - `LOG_BACKUP_COUNT`, `LOG_MAX_BYTES`
- Retention: 7 backups (standardized), 30 days for archives

**Key rules:**
- Rotation happens at midnight (time-based) or when file exceeds 5MB (size-based)
- Files under 5KB won't rotate (intentional to prevent rotating tiny files)
- Files under 1 hour old won't rotate (intentional to prevent rotating new files)
- Rotated files go to `logs/backups/`, compressed archives go to `logs/archive/`

**AI usage:**
- Don't reimplement rotation - use existing handlers
- If changing rotation behavior, update both `core/logger.py` and documentation

**Restore:** See BACKUP_GUIDE.md section 1.3 for restore procedures.

---

## 2. User Data Backups

**Where to look:**
- Implementation: `core/backup_manager.py` - `BackupManager`
- Scheduler: `core/scheduler.py` - Weekly backup at 01:00
- Location: `data/backups/*.zip`

**Key rules:**
- Backups created weekly (if 7+ days since last backup)
- Retention: 30 days OR 10 files (whichever is stricter)
- Includes: User data + config files (logs optional, code optional)
- Verification: Automatic after creation

**AI usage:**
- Use `BackupManager.create_backup()` for creating backups
- Use `BackupManager.restore_backup()` for restoring
- Use `BackupManager.validate_backup()` to verify integrity
- Use `BackupManager.list_backups()` to see available backups

**Restore:** See BACKUP_GUIDE.md section 2.3 for restore procedures.

---

## 3. Message Archives

**Where to look:**
- Implementation: `core/message_management.py` - `archive_old_messages()`
- Scheduler: `core/auto_cleanup.py` - Monthly cleanup
- Location: `data/users/{user_id}/messages/archives/`

**Key rules:**
- Only archives messages >365 days old
- Empty archives are normal if messages are newer
- Retention: 90 days for archive files

**AI usage:**
- Don't manually archive - let scheduler handle it
- Empty archives are expected behavior, not a bug

---

## 4. Development Tools Rotation

**Where to look:**
- Implementation: `development_tools/shared/file_rotation.py` - `FileRotator`, `create_output_file()`
- Storage: `development_tools/shared/output_storage.py` - `save_tool_result()`
- Archives: `development_tools/reports/archive/` or `{domain}/jsons/archive/`

**Key rules:**
- Status files: 7 versions
- Tool results: 7 versions (standardized)
- Generated docs: 7 versions
- Coverage JSON: 5 versions
- Test logs: 7 versions total (consolidated)

**AI usage:**
- Use `create_output_file()` for status files and generated docs
- Use `save_tool_result()` for tool JSON results
- Use `FileRotator.rotate_file()` for custom rotation needs

**Restore:** See BACKUP_GUIDE.md section 4.3 for restore procedures.

---

## 5. External Archive Directory

**Where to look:**
- Location: `c:\Users\Julie\projects\MHM\Archive\`
- Script: `scripts/create_project_snapshot.py`

**Key rules:**
- Manual backups only (no automation)
- Use `create_project_snapshot.py` for creating snapshots
- No cleanup policy (manual management)

**AI usage:**
- Use snapshot script for creating project snapshots
- Don't automate external Archive - it's for manual use

**Restore:** See BACKUP_GUIDE.md section 5.3 for restore procedures.

---

## 6. Compression Files (.gz)

**What they are:**
- Compressed files using gzip algorithm
- Used to save disk space for old/archived files

**How to extract:**
- Windows: Right-click -> "Extract All" or use 7-Zip
- Python: `gzip.open('file.gz', 'rt')`
- PowerShell: `Expand-Archive` (may work depending on Windows version)

**AI usage:**
- Don't create .gz files manually - use existing compression functions
- Document compression usage when enabling `LOG_COMPRESS_BACKUPS`

---

## 7. Unified Retention Policy

**Standardized policies:**
- Logs: 7 backups
- User backups: 30 days OR 10 files
- Message archives: 90 days
- Dev tools (status): 7 versions
- Dev tools (results): 7 versions
- Generated docs: 7 versions
- Coverage JSON: 5 versions
- Test logs: 7 versions total

**AI usage:**
- Follow these policies consistently
- Don't create new retention policies without updating documentation

---

## 8. Safety Procedures

**Key safety rules:**
- Always create a safety backup before restoring
- Validate backups before restoring
- Test the application after restoring
- Verify system state after restore

**Common operations:**
- Create backup: `backup_manager.create_backup()`
- Restore: `backup_manager.restore_backup(path, restore_users=True)`
- Validate: `backup_manager.validate_backup(path)`
- Rotate file: `create_output_file(path, content, rotate=True, max_versions=7)`
- Create snapshot: `create_project_snapshot(include_user_data=False, compress=True)`

**For detailed procedures:** See BACKUP_GUIDE.md section 8 for complete safety procedures.

---

## 9. Troubleshooting

### 9.1. Logs Not Rotating
- Check file size (must be >5KB)
- Check file age (must be >1 hour)
- Check rotation time (happens at midnight)
- Check for errors in `logs/errors.log`

### 9.2. Backups Not Created
- Check scheduler (runs at 01:00)
- Check last backup age (only if 7+ days old)
- Check disk space
- Check logs for errors

### 9.3. Message Archives Empty
- **This is normal** if messages <365 days old
- Check message ages to verify
- Wait for monthly cleanup to run

**For more troubleshooting:** See BACKUP_GUIDE.md section 9 for detailed troubleshooting procedures.

---

## 10. Best Practices

**For users:**
- Check backups regularly
- Monitor log sizes
- Keep external Archive organized
- Enable compression to save space

**For developers:**
- Use existing rotation systems
- Follow retention policies
- Test restore procedures
- Document new backup systems

**For detailed guidance:** See BACKUP_GUIDE.md section 10 for complete best practices.

---

## 11. Related Documentation

- [BACKUP_GUIDE.md](../development_docs/BACKUP_GUIDE.md) - Complete backup system documentation and restore procedures
- [LOGGING_GUIDE.md](../logs/LOGGING_GUIDE.md) - Detailed logging documentation
