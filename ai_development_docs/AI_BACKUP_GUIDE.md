# AI Backup Guide

> **File**: `ai_development_docs/AI_BACKUP_GUIDE.md`  
> **Pair**: [BACKUP_GUIDE.md](../development_docs/BACKUP_GUIDE.md)  
> **Audience**: AI collaborators  
> **Purpose**: Fast routing and constraints for backup/archive operations  
> **Style**: Minimal, routing-first

> This AI document is paired with BACKUP_GUIDE.md. Keep this file's H2 headings in lockstep with BACKUP_GUIDE.md whenever you change the structure. For detailed guidance, examples, and rationale, use the matching sections in BACKUP_GUIDE.md.

---

## Overview

MHM uses multiple backup and archiving systems: log rotation, user data backups, message archives, development-tools rotation, and external archive. For routing and constraints, see the numbered sections below; for full procedures and restore steps, see BACKUP_GUIDE.md.

---

## 1. Log Rotation System

**Where to look:**
- Implementation: `core/logger.py` - `BackupDirectoryRotatingFileHandler`
- Configuration: `core/config.py` - `LOG_BACKUP_COUNT`, `LOG_MAX_BYTES`
- Retention: rotated copies under `logs/backups/`; compress to `logs/archive/*.gz` after 7 days (02:00 job); delete archives older than 30 days

**Key rules:**
- Rotation happens at midnight (time-based) or when file exceeds 5MB (size-based)
- Files under 5KB won't rotate (intentional to prevent rotating tiny files)
- Files under 1 hour old won't rotate (intentional to prevent rotating new files)
- Rotated files go to `logs/backups/`; age-based compress to `logs/archive/` (7+ days), not a strict "seven files then move" cap
- Multiple log streams can produce more than seven files under `logs/backups/` without indicating failure

**AI usage:**
- Don't reimplement rotation - use existing handlers
- If changing rotation behavior, update both `core/logger.py` and documentation

**Restore:** See BACKUP_GUIDE.md section 1.3 for restore procedures.

---

## 2. User Data Backups

User data persistence layout and backup scope expectations are defined in [USER_DATA_MODEL.md](../core/USER_DATA_MODEL.md) (see Section 8 Backup scope expectations).

Backup configuration semantics (paths, retention, feature flags) are defined in [CONFIGURATION_REFERENCE.md](../CONFIGURATION_REFERENCE.md) (see Section 9 Backups and developer diagnostics).

**Where to look:**
- Implementation: `core/backup_manager.py` - `BackupManager`
- Scheduler integration: `scheduler/manager.py` and `scheduler/maintenance.py`
- Backup artifacts: `data/backups/*` (directory backups by policy; zip is read-only compatibility for historical artifacts)

**Key rules:**
- Weekly scheduler logic keys off `weekly_backup_*` artifacts (not generic latest backup)
- Weekly health checks are explicit: `weekly_backup_present`, `weekly_backup_recent_enough`
- Retention keeps weekly artifacts in a separate keep window from non-weekly backups (`WEEKLY_BACKUP_MAX_KEEP`, default 4)
- On-demand per-user zips: `UserDataManager.backup_user_data()` -> `user_backup_{user_id}_{timestamp}.zip`
- Manifest-less directories under `data/backups/` (no `manifest.json`, older than 1 hour) are removed by `cleanup_manifest_less_backup_directories()` during backup retention and monthly cleanup

**AI usage:**
- Use `BackupManager.create_backup()` for creating backups
- Use `BackupManager.restore_backup()` for restoring
- Use `BackupManager.validate_backup()` to verify integrity
- Use `BackupManager.list_backups()` to see available backups

**Restore:** See BACKUP_GUIDE.md section 2.3 for restore procedures.

---

## 3. Message Archives

**Where to look:**
- Implementation: `messages/message_data_manager.py` - `archive_old_messages()`
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
- Policy models: `development_tools/shared/backup_policy_models.py`
- Inventory/retention: `development_tools/shared/backup_inventory.py`, `development_tools/shared/retention_engine.py`
- Archives: `development_tools/reports/archive/` or `{domain}/jsons/archive/`

**Key rules:**
- `backup inventory` generates ownership map + producer/output inventory from config
- `backup retention --dry-run|--apply` enforces category-B retention for dev-tools-owned artifacts
- `backup drill` runs isolated restore drill via core backup API and writes reports
- `backup verify` runs end-to-end backup health checks (inventory + explicit weekly presence/recency checks + latest backup validation + drill)
- Dev-tools policy is config-driven from `development_tools/config/development_tools_config.json`

**AI usage:**
- Use `create_output_file()` for status files and generated docs
- Use `save_tool_result()` for tool JSON results
- Use `FileRotator.rotate_file()` for custom rotation needs
- Use `python development_tools/run_development_tools.py backup <inventory|retention|drill|verify>` for policy workflows

**Restore:** See BACKUP_GUIDE.md section 4.3 for restore procedures.

---

## 5. External Archive Directory

**Where to look:**
- Location: `c:\Users\Julie\projects\MHM\Archive\`

**Key rules:**
- Manual artifact storage only (no automation)
- Use tracked backup tooling for restorable recovery artifacts
- Use tracked export tooling for LLM-readable code/docs snapshots
- No cleanup policy for the external Archive (manual management)

**AI usage:**
- Recovery backup: `backup_manager.create_backup(include_code=True)` when code should be included
- Code context bundle: `python development_tools/run_development_tools.py export-code --root . --include-tests --include-dev-tools`
- Docs context bundle: `python development_tools/run_development_tools.py export-docs`
- The former `scripts/create_project_snapshot.py` utility is retired; do not recreate or reference it
- Don't automate external Archive - it's for manual use

**Restore:** See BACKUP_GUIDE.md section 5.3 for restore guidance.

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
- Category A (runtime recovery): `max_age_days=30`, `min_keep=4`, `max_keep=10` (core-owned)
- Category B (engineering artifacts): `max_age_days=90`, `min_keep=7`, `max_keep=30` (development-tools-owned)
- Category C (git-canonical tracked assets): local retention disabled; rely on Git history

**Category A note:**
- Runtime backup retention uses separate count buckets: non-weekly max 10, weekly max from `WEEKLY_BACKUP_MAX_KEEP` (default 4)

**Ownership map:**
- `core/*`: user-data backup creation/restore + scheduler weekly backup
- `development_tools/*`: engineering artifact inventory/retention/reporting
- `git`: canonical code/docs/changelog history

**Artifact mapping:**
- Generated docs, test logs, tool JSON archives, coverage artifacts, manual snapshots -> Category B
- User backup artifacts (directory by policy; historical zip read support only) and runtime log archives -> Category A
- Code files, non-generated docs, changelogs -> Category C

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
- Isolated restore (drill): `backup_manager.restore_backup_to_path(path, destination, restore_users=True, restore_config=False)`
- Validate: `backup_manager.validate_backup(path)`
- Rotate file: `create_output_file(path, content, rotate=True, max_versions=7)`
- Export code context: `python development_tools/run_development_tools.py export-code --root . --include-tests --include-dev-tools`
- Export docs context: `python development_tools/run_development_tools.py export-docs`
- Inventory report: `python development_tools/run_development_tools.py backup inventory`
- Retention dry-run: `python development_tools/run_development_tools.py backup retention --dry-run`
- Retention apply: `python development_tools/run_development_tools.py backup retention --apply`
- Restore drill: `python development_tools/run_development_tools.py backup drill`
- Backup health verify: `python development_tools/run_development_tools.py backup verify`

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
- Check last `weekly_backup_*` age (weekly creation gates on weekly artifact recency, 7+ days)
- Run `backup verify` and inspect `weekly_backup_present` + `weekly_backup_recent_enough`
- Check disk space
- Check logs for errors

### 9.2.1. Orphan Directories in data/backups
- Manifest-less dirs older than 1 hour are auto-removed (`cleanup_manifest_less_backup_directories`)
- Legacy `*_backup_user_data_v2_*` folders are safe to delete once weekly backups exist
- `backup verify` only counts managed artifacts (manifest or zip)

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
