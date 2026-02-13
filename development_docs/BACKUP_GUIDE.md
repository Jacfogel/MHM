# Backup and Archive System Guide

> **File**: `development_docs/BACKUP_GUIDE.md`  
> **Pair**: [AI_BACKUP_GUIDE.md](../ai_development_docs/AI_BACKUP_GUIDE.md)  
> **Audience**: Developers and users  
> **Purpose**: Complete documentation of backup, rotation, archiving, and restore procedures  
> **Style**: Detailed, comprehensive

## Overview

MHM uses multiple backup and archiving systems to protect data and manage disk space:

1. **Log Rotation** - Daily rotation of log files
2. **User Data Backups** - Weekly automated backups of user data and config
3. **Message Archives** - Archiving of old messages (>365 days)
4. **Development Tools Rotation** - Archiving of tool outputs and reports
5. **External Archive** - Manual project snapshots

This guide covers both how the systems work and how to restore from backups.

---

## 1. Log Rotation System

### 1.1. Location

- **Code**: `core/logger.py`
- **Active Logs**: `logs/*.log`
- **Backups**: `logs/backups/*.log.YYYY-MM-DD`
- **Archives**: `logs/archive/*.log.YYYY-MM-DD.gz` (compressed)

### 1.2. How It Works

**Rotation Triggers:**
- **Time-based**: Rotates at midnight daily (`when='midnight'`, `interval=1`)
- **Size-based**: Rotates when file exceeds `LOG_MAX_BYTES` (default: 5MB)

**Rotation Rules:**
- Files must be at least **5KB** to rotate (prevents rotating tiny files)
- Files must be at least **1 hour old** to rotate (prevents rotating newly created files)
- Rotated files are moved to `logs/backups/` with date suffix
- When backups exceed 7, older rotated copies move to `logs/archive/`
- Old backups are compressed to `.gz` format after 7 days
- Archived copies older than 30 days are deleted

**Retention:**
- **Protocol (default)**: Keep 1 current active file + 7 backup files + up to 7 archive copies
- **Archive pruning**: Delete archived copies older than 30 days
- **Effective target**: Up to 15 most recent copies retained (1 current + 7 backups + 7 archive)

**Configuration:**
- `LOG_MAX_BYTES`: Maximum file size before rotation (default: 5242880 = 5MB)
- `LOG_BACKUP_COUNT`: Number of backup files to keep (default: 7)
- `LOG_COMPRESS_BACKUPS`: Enable compression (default: false)
- `LOG_BACKUP_DIR`: Backup directory (default: `logs/backups`)
- `LOG_ARCHIVE_DIR`: Archive directory (default: `logs/archive`)

**Daily Archival:**
- Runs at 02:00 via scheduler
- Compresses logs older than 7 days
- Cleans up archives older than 30 days

### 1.3. Restoring Log Files

**When to Restore:**
- Need to review old log entries
- Investigating past errors or issues
- Recovering deleted log files

**Procedure:**

1. **Locate log backups:**
   - Check `logs/backups/` for rotated log files
   - Check `logs/archive/` for compressed archives

2. **Restore from backups:**
   ```powershell
   # Copy backup log to main log location
   Copy-Item -Path "logs\backups\app.log.2025-12-15" -Destination "logs\app.log.restored"
   ```

3. **Extract compressed logs:**
   ```python
   import gzip
   with gzip.open('logs/archive/app.log.2025-12-10.gz', 'rt') as f:
       content = f.read()
   with open('logs/app.log.restored', 'w') as f:
       f.write(content)
   ```

---

## 2. User Data Backups

### 2.1. Location

- **Code**: `core/backup_manager.py`
- **Backups**: `data/backups/*.zip`
- **Scheduler**: `core/scheduler.py` (weekly backup check)

### 2.2. How It Works

**Backup Schedule:**
- **Automatic**: Weekly backups created at 01:00 daily if:
  - No backups exist, OR
  - Last backup is 7+ days old

**Backup Contents:**
- All user data directories (`data/users/{user_id}/`)
- Configuration files (`.env`, `requirements.txt`, `user_index.json`)
> **Note:** Configuration semantics are canonically defined in [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) (source of truth: `.env.example`; loader/validation: `core/config.py`).
> Avoid duplicating per-setting definitions outside that reference.
- Optional: Log files (disabled by default)
- Optional: Project code (via `include_code` parameter)

**Backup Format:**
- ZIP files with compression (`ZIP_DEFLATED`)
- Includes `manifest.json` with metadata:
  - Backup name and creation timestamp
  - What's included (users, config, logs, code)
  - System info (user count, backup size)

**Retention Policy:**
- **Age-based**: Keep backups for 30 days (configurable via `BACKUP_RETENTION_DAYS`)
- **Count-based**: Keep maximum 10 backups
- **Enforcement**: Both policies apply (whichever is stricter)

**Backup Naming:**
- Format: `mhm_backup_YYYYMMDD_HHMMSS.zip` or `weekly_backup_YYYYMMDD_HHMMSS.zip`

**Verification:**
- Automatic verification after creation
- Health monitoring in scheduler

### 2.3. Restoring User Data from Backups

**Prerequisites:**
- Backup ZIP file from `data/backups/`
- Python environment with MHM installed
- Access to the project directory

**Procedure:**

#### Option A: Using BackupManager (Recommended)

1. **List available backups:**
   ```python
   from core.backup_manager import backup_manager
   backups = backup_manager.list_backups()
   for backup in backups:
       print(f"{backup['file_name']} - {backup['created_at']} - {backup['file_size'] / 1024 / 1024:.2f} MB")
   ```

2. **Restore from backup:**
   ```python
   from core.backup_manager import backup_manager
   
   # Restore user data only
   success = backup_manager.restore_backup(
       backup_path="data/backups/mhm_backup_20251217_120000.zip",
       restore_users=True,
       restore_config=False
   )
   
   # Or restore both users and config
   success = backup_manager.restore_backup(
       backup_path="data/backups/mhm_backup_20251217_120000.zip",
       restore_users=True,
       restore_config=True
   )
   ```

3. **Verify restoration:**
   - Check that user directories exist in `data/users/`
   - Verify user data files (account.json, preferences.json, etc.)
   - Test the application to ensure users can log in

#### Option B: Manual Restore

1. **Extract the backup ZIP:**
   - Right-click the backup file -> "Extract All"
   - Or use PowerShell: `Expand-Archive -Path data\backups\mhm_backup_YYYYMMDD_HHMMSS.zip -DestinationPath .\restore_temp`

2. **Verify backup contents:**
   - Check `manifest.json` to see what's included
   - Verify `users/` directory exists with user data

3. **Restore user data:**
   - Copy `users/` directory from extracted backup to `data/users/`
   - **WARNING**: This will overwrite existing user data!
   - Make a backup of current data first if needed

4. **Restore config (if needed):**
   - Copy files from `config/` directory to project root
   - **WARNING**: This will overwrite existing config files!

---

## 3. Message Archives

### 3.1. Location

- **Code**: `core/message_management.py`, `core/auto_cleanup.py`
- **Active Messages**: `data/users/{user_id}/messages/sent_messages.json`
- **Archives**: `data/users/{user_id}/messages/archives/sent_messages_archive_YYYYMMDD_HHMMSS.json`

### 3.2. How It Works

**Archiving Trigger:**
- Runs during monthly cleanup (every 30 days)
- Only archives messages older than **365 days** (1 year)

**Archiving Process:**
1. Reads `sent_messages.json` for user
2. Separates messages into active (<365 days) and archived (>365 days)
3. Creates archive file with metadata:
   - Total messages archived
   - Date range (oldest to newest)
   - Archive timestamp
4. Updates active file with remaining messages
5. Logs archiving results

**Archive Format:**
```json
{
  "metadata": {
    "version": "2.0",
    "archived_date": "2025-12-17 12:00:00",
    "total_messages": 100,
    "date_range": {
      "oldest": "2024-01-01 00:00:00",
      "newest": "2024-12-31 23:59:59"
    }
  },
  "messages": [...]
}
```

**Retention Policy:**
- Archive files older than **90 days** are deleted during cleanup
- Active messages are kept indefinitely (only old ones are archived)

**Expected Behavior:**
- **Empty archives are normal**: If all messages are less than 365 days old, archives will be empty
- **Archiving is infrequent**: Only runs monthly, so new archives may take time to appear

---

## 4. Development Tools Rotation

### 4.1. Location

- **Code**: `development_tools/shared/file_rotation.py`, `development_tools/shared/output_storage.py`
- **Status Files**: `development_tools/AI_STATUS.md`, `AI_PRIORITIES.md`, `consolidated_report.txt`
- **Tool Results**: `development_tools/{domain}/jsons/{tool}_results.json`
- **Archives**: `development_tools/reports/archive/` or `{domain}/jsons/archive/`

### 4.2. How It Works

**Rotation Method:**
- Uses `FileRotator` class for status files
- Uses `save_tool_result()` for JSON results
- Rotates existing files before writing new content

**Retention:**
- **Status files**: 7 versions (default)
- **Tool results**: 7 versions (default, standardized retention)
- **Test logs**: 1 current + 7 backups + up to 7 archive copies (archive >30 days deleted)
- **Generated docs**: 7 versions
- **Coverage JSON**: 5 versions

**Archive Naming:**
- Format: `{filename}_{YYYY-MM-DD_HHMMSS}_{counter}.{ext}`
- Counter ensures uniqueness even for same-second rotations

### 4.3. Restoring Development Tools Outputs

**When to Restore:**
- Need to review old analysis results
- Recovering deleted tool outputs
- Comparing current vs. previous results

**Procedure:**

1. **Locate archived outputs:**
   - Status files: `development_tools/reports/archive/`
   - Tool results: `development_tools/{domain}/jsons/archive/`
   - Generated docs: `development_docs/archive/` or `ai_development_docs/archive/`

2. **Restore status files:**
   ```powershell
   # Copy archived status file
   Copy-Item -Path "development_tools\reports\archive\AI_STATUS_2025-12-15_120000_0001.md" -Destination "development_tools\AI_STATUS.md"
   ```

3. **Restore tool results:**
   ```powershell
   # Copy archived tool result
   Copy-Item -Path "development_tools\functions\jsons\archive\analyze_functions_results_2025-12-15_120000.json" -Destination "development_tools\functions\jsons\analyze_functions_results.json"
   ```

4. **Restore generated documentation:**
   ```powershell
   # Copy archived documentation
   Copy-Item -Path "development_docs\archive\FUNCTION_REGISTRY_DETAIL_2025-12-15_120000_0001.md" -Destination "development_docs\FUNCTION_REGISTRY_DETAIL.md"
   ```

---

## 5. External Archive Directory

### 5.1. Location

- **Path**: `c:\Users\Julie\projects\MHM\Archive\`
- **Script**: `scripts/create_project_snapshot.py`
- **Status**: Manual backups only, no automation

### 5.2. How It Works

**Purpose:**
- Long-term project snapshots
- Manual backups before major changes
- Historical project versions

**Creating Snapshots:**
```python
from scripts.create_project_snapshot import create_project_snapshot
snapshot_path = create_project_snapshot(
    archive_dir="c:/Users/Julie/projects/MHM/Archive",
    include_user_data=False,
    compress=True
)
```

**Snapshot Contents:**
- Project code (Python files, config, documentation)
- Optional: User data
- Optional: ZIP compression

### 5.3. Restoring from Project Snapshots

**Prerequisites:**
- Snapshot ZIP file from external Archive directory
- Access to project directory
- Enough disk space for the snapshot

**Procedure:**

1. **Locate the snapshot:**
   - Navigate to `c:\Users\Julie\projects\MHM\Archive\`
   - Find the snapshot file: `mhm_snapshot_YYYYMMDD_HHMMSS.zip`

2. **Extract the snapshot:**
   ```powershell
   Expand-Archive -Path "c:\Users\Julie\projects\MHM\Archive\mhm_snapshot_YYYYMMDD_HHMMSS.zip" -DestinationPath ".\restore_temp"
   ```

3. **Review snapshot contents:**
   - Check `snapshot_manifest.json` to see what's included
   - Verify code directories and files are present

4. **Restore specific components:**
   - **Code only**: Copy `code/` directory contents to project root
   - **Documentation**: Copy `ai_development_docs/` and `development_docs/` from snapshot
   - **User data** (if included): Copy `data/` directory

5. **Verify restoration:**
   - Run tests: `python run_tests.py`
   - Check application startup: `python run_headless_service.py start`
   - Verify no import errors or missing files

---

## 6. Compression Files (.gz)

### 6.1. What Are .gz Files?

`.gz` files are compressed files using the gzip algorithm. They reduce file size significantly (often 50-90% smaller) and are used to save disk space for old/archived files.

### 6.2. How to Extract .gz Files

**On Windows:**
- **Right-click** -> "Extract All" (Windows 10/11 built-in support)
- **PowerShell**: `Expand-Archive -Path file.gz -DestinationPath .`
- **7-Zip/WinRAR**: Open and extract like any archive

**Via Python:**
```python
import gzip
with gzip.open('file.log.gz', 'rt') as f:
    content = f.read()
```

**Command Line:**
- Windows: Use 7-Zip or similar tools
- Linux/Mac: `gunzip file.gz` or `gzip -d file.gz`

### 6.3. When Are .gz Files Used?

- Old log files that are archived (saves disk space)
- Long-term backups that are rarely accessed
- Files that are too large but need to be kept

**Note**: The current system has `LOG_COMPRESS_BACKUPS` option but it's set to `false` by default. Enable it to save disk space for old logs.

---

## 7. Unified Retention Policy

All retention policies have been standardized for consistency. This is the authoritative reference.

### 7.1. Retention Tiers

1. **Active Files**: Current files (no rotation)
2. **Backup Files**: Recent rotated files (7-30 days, 5-10 versions)
3. **Archive Files**: Long-term storage (30-90 days, compressed)
4. **Deep Archive**: External storage (manual, no cleanup)

### 7.2. Policy Details

| System | Retention | Archive Location | Compression | Notes |
|--------|-----------|------------------|-------------|-------|
| **Logs (all)** | 1 current + 7 backups + up to 7 archive | `logs/backups/` -> `logs/archive/` | After 7 days | Archive >30 days deleted |
| **Log archives** | 30 days (plus max 7 archive copies) | `logs/archive/` | Yes (.gz) | Compressed after 7 days |
| **User backups** | 30 days OR 10 files | `data/backups/` | Yes (ZIP) | Whichever is stricter |
| **Message archives** | 90 days | `data/users/{id}/messages/archives/` | No | Only messages >365 days |
| **Dev tools (status)** | 7 versions | `development_tools/reports/archive/` | No | AI_STATUS.md, AI_PRIORITIES.md, etc. |
| **Dev tools (results)** | 7 versions | `{domain}/jsons/archive/` | No | Tool JSON results |
| **Test logs** | 1 current + 7 backups + up to 7 archive | `tests/logs/archive/` | No | Archive >30 days deleted |
| **Generated docs** | 7 versions | `{doc_dir}/archive/` | No | FUNCTION_REGISTRY_DETAIL.md, etc. |
| **Coverage JSON** | 5 versions | `development_tools/tests/jsons/archive/` | No | coverage.json, coverage_dev_tools.json |
| **External Archive** | Manual | `c:\Users\Julie\projects\MHM\Archive\` | Optional | No cleanup policy |

### 7.3. Configuration

Retention policies are configured in:
- **Logs**: `core/config.py` - `LOG_BACKUP_COUNT` (default: 7)
- **User backups**: `core/backup_manager.py` - `max_backups` (10), `backup_retention_days` (30)
- **Message archives**: `core/auto_cleanup.py` - `archive_retention_days` (90)
- **Dev tools**: `development_tools/shared/file_rotation.py` - `max_versions` (varies by type)

### 7.3.1. Default Rotation Protocol

For backup/archive-managed files, the default protocol is:
1. Keep `1` current active file
2. Keep `7` previous copies in `backups/`
3. Move older rotated copies to `archive/` and keep up to `7`
4. Delete archive copies older than `30` days

This keeps recent history immediately accessible while enforcing 30-day archive cleanup and a practical ceiling of 15 recent retained copies.

### 7.4. Policy Rationale

- **7 backups/versions**: Good balance between history and disk space for frequently updated files
- **7 versions**: Standardized retention for most files (tool results, generated docs, test logs)
- **5 versions**: Sufficient for less critical files (coverage JSON)
- **30 days**: Standard retention for backups (monthly cycle)
- **90 days**: Extended retention for archives (quarterly cycle)

---

## 8. Safety Procedures

### 8.1. Before Restoring

1. **Create a safety backup:**
   ```python
   from core.backup_manager import backup_manager
   safety_backup = backup_manager.create_backup("pre_restore_safety_backup")
   print(f"Safety backup created: {safety_backup}")
   ```

2. **Verify backup integrity:**
   ```python
   from core.backup_manager import backup_manager
   is_valid, errors = backup_manager.validate_backup("data/backups/mhm_backup_YYYYMMDD_HHMMSS.zip")
   if not is_valid:
       print(f"Backup has errors: {errors}")
       # Don't restore from invalid backup!
   ```

3. **Check disk space:**
   - Ensure you have enough space for the restore
   - Check backup file size vs. available space

### 8.2. After Restoring

1. **Verify system state:**
   ```python
   from core.backup_manager import validate_system_state
   is_valid = validate_system_state()
   if not is_valid:
       print("System state validation failed - restore may have issues")
   ```

2. **Test the application:**
   - Start the service: `python run_headless_service.py start`
   - Check for errors in logs
   - Test user login/functionality

3. **Check file permissions:**
   - Ensure restored files have correct permissions
   - Fix any permission issues if needed

---

## 9. Troubleshooting

### 9.1. Logs Not Rotating

**Problem**: Log files are not rotating as expected.

**Solutions:**
- Check file size: Files under 5KB won't rotate
- Check file age: Files under 1 hour won't rotate
- Check rotation time: Rotation happens at midnight
- Check for errors: Look in `logs/errors.log` for rotation failures

### 9.2. Backups Not Created

**Problem**: Weekly backups are not being created.

**Solutions:**
- Check scheduler: Weekly backups run at 01:00
- Check last backup: Backups only created if 7+ days old
- Check disk space: Insufficient space may prevent backups
- Check logs: Look for backup errors in `logs/file_ops.log`

### 9.3. Message Archives Empty

**Problem**: Message archive directories are empty.

**Solutions:**
- **This is normal**: Archives only contain messages >365 days old
- Check message ages: Use PowerShell to check oldest message timestamps
- Wait for monthly cleanup: Archiving runs every 30 days

### 9.4. Can't Extract .gz Files

**Problem**: Unable to extract compressed .gz files.

**Solutions:**
- Use 7-Zip: Free tool that handles .gz files
- Use Python: `gzip` module is built-in
- Use PowerShell: `Expand-Archive` may work depending on Windows version

### 9.5. Backup Not Found

**Problem**: Backup file doesn't exist or can't be found.

**Solutions:**
- Check backup directory: `data/backups/`
- List all backups: `Get-ChildItem data\backups\*.zip`
- Verify backup name and path are correct

### 9.6. Restore Failed

**Problem**: Restore operation failed with errors.

**Solutions:**
1. Check error logs: `logs/errors.log`
2. Verify backup file integrity: `backup_manager.validate_backup(path)`
3. Check disk space: Ensure enough space available
4. Check file permissions: Ensure write access to restore location
5. Try manual extract: Extract ZIP manually and copy files

### 9.7. Partial Restore

**Problem**: Only some files were restored.

**Solutions:**
1. Check restore logs for errors
2. Verify backup contents: Extract ZIP and check `manifest.json`
3. Manually restore missing files from extracted backup
4. Verify system state: `validate_system_state()`

### 9.8. Corrupted Backup

**Problem**: Backup file is corrupted or invalid.

**Solutions:**
1. Try validating: `backup_manager.validate_backup(path)`
2. Check for other backups: List all backups and try a different one
3. Check backup file size: Corrupted files may be smaller than expected
4. Try extracting manually: If ZIP extract fails, backup is likely corrupted

---

## 10. Best Practices

### 10.1. For Users

1. **Check backups regularly**: Verify `data/backups/` has recent files
2. **Monitor log sizes**: Large log files may indicate rotation issues
3. **Keep external Archive organized**: Use consistent naming for manual backups
4. **Enable compression**: Set `LOG_COMPRESS_BACKUPS=true` to save space

### 10.2. For Developers

1. **Use existing rotation systems**: Don't create new backup mechanisms
2. **Follow retention policies**: Don't keep more backups than configured
3. **Test restore procedures**: Verify backups can be restored
4. **Document new backup systems**: Update this file when adding new systems
5. **Always create a safety backup before restoring**
6. **Validate backups before restoring**
7. **Test the application after restoring**
8. **Keep multiple backup generations**
9. **Document what was restored and when**
10. **Verify system state after restore**

---

## 11. Related Documentation

- [AI_BACKUP_GUIDE.md](../ai_development_docs/AI_BACKUP_GUIDE.md) - AI collaborator guide
- [LOGGING_GUIDE.md](../logs/LOGGING_GUIDE.md) - Detailed logging documentation
