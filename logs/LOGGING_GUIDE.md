# Enhanced Logging System Guide

> **Audience**: Developers working with MHM logging system  
> **Purpose**: Guide for enhanced logging system with component-based separation  
> **Style**: Technical, comprehensive, reference-oriented

> **See [README.md](../README.md) for complete navigation and project overview**  
> **See [DEVELOPMENT_WORKFLOW.md](../DEVELOPMENT_WORKFLOW.md) for safe development practices**  
> **See [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) for essential commands**

## Quick Reference

### **Log Files**
- `app.log` - Main application logs
- `discord.log` - Discord bot operations
- `ai.log` - AI interactions and processing
- `errors.log` - Error and critical messages
- `user_activity.log` - User actions and check-ins

### **Logging Commands**
```powershell
# View recent logs
Get-Content logs/app.log -Tail 50
Get-Content logs/errors.log -Tail 20

# Monitor logs in real-time
Get-Content logs/app.log -Wait
```

## Overview

The MHM logging system has been enhanced with component-based separation, structured logging, and better organization. This guide explains how to use the new features.

## Directory Structure

```
logs/
|-- app.log                    # Main application logs (active)
|-- discord.log               # Discord bot specific logs (active)
|-- ai.log                    # AI interactions and processing (active)
|-- user_activity.log         # User actions and check-ins (active)
|-- errors.log                # Error and critical messages only (active)
|-- communication_manager.log # Communication orchestration (active)
|-- email.log                 # Email bot operations (active)
|-- file_ops.log              # File operations (active)
|-- scheduler.log             # Scheduler operations (active)
|-- ui.log                    # UI operations (active)
|-- message.log               # Message processing (active)
|-- backups/                  # Rotated log files (daily rotation)
`-- archive/                  # Compressed old logs (>7 days old)
```

### Directory Purposes

- **Active Logs**: Current log files being written to
- **Backups**: Daily rotated log files (kept for 7 days)
- **Archive**: Compressed log files older than 7 days (kept for 30 days)

## Component Loggers Reference

### All Available Component Loggers

The MHM system includes **11 component loggers** organized by functional area:

| Category | Logger | File | Purpose |
|----------|--------|------|---------|
| **Core System** | `main` | `app.log` | Main application operations |
| | `errors` | `errors.log` | Error and critical messages |
| | `scheduler` | `scheduler.log` | Scheduler operations and timing |
| | `file_ops` | `file_ops.log` | File operations and I/O |
| | `user_activity` | `user_activity.log` | User actions and check-ins |
| **Communication** | `discord` | `discord.log` | Discord bot operations |
| | `email` | `email.log` | Email bot operations |
| | `communication_manager` | `communication_manager.log` | Communication orchestration |
| | `message` | `message.log` | Message processing and routing |
| **AI System** | `ai` | `ai.log` | AI system operations |
| **UI & Management** | `ui` | `ui.log` | UI operations and dialogs |

### Component Logger Creation Locations

Component loggers are created **decentrally** throughout the codebase using `get_component_logger()`:

#### **Core Modules**
- `core/service.py`: `main`, `discord`
- `core/user_data_handlers.py`: `main`, `user_activity`
- `core/config.py`: `main`
- `core/schedule_utilities.py`: `scheduler`
- `core/file_operations.py`: `file_ops`
- `core/scheduler.py`: `scheduler`
- `core/backup_manager.py`: `file_ops`, `main`
- `core/message_management.py`: `message`
- `core/user_management.py`: `main`, `user_activity`
- `core/checkin_dynamic_manager.py`: `user_activity`
- `core/checkin_analytics.py`: `user_activity`
- `core/response_tracking.py`: `user_activity`

#### **Communication Modules**
- `communication/core/channel_orchestrator.py`: `channel_orchestrator`, `user_activity`
- `communication/communication_channels/discord/bot.py`: `discord`
- `communication/communication_channels/email/bot.py`: `email`
- `communication/message_processing/message_router.py`: `message`

#### **AI Modules**
- `ai/chatbot.py`: `ai`
- `ai/lm_studio_manager.py`: `ai`

#### **UI Modules**
- `ui/ui_app_qt.py`: `ui`
- `ui/dialogs/*.py`: `ui`
- `ui/widgets/*.py`: `ui`

### Basic Usage

```python
from core.logger import get_component_logger

# Get component-specific loggers (propagate=False, own files, errors also to errors.log)
discord_logger = get_component_logger('discord')
email_logger = get_component_logger('email')
ui_logger = get_component_logger('ui')
file_ops_logger = get_component_logger('file_ops')
scheduler_logger = get_component_logger('scheduler')
user_logger = get_component_logger('user_activity')
ai_logger = get_component_logger('ai')
comm_logger = get_component_logger('communication_manager')
main_logger = get_component_logger('main')
```

### Logging with Structured Data

```python
# Simple logging
discord_logger.info("Discord bot connected")

# Structured logging with metadata
discord_logger.info("Discord bot connected", latency=0.1, guild_count=1)

# Error logging with context
error_logger.error("Database connection failed", retry_count=3, error_code="DB001")
```

### Available Log Levels

```python
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error messages")
logger.critical("Critical errors")
```

## Log Rotation and Archival

### Universal Rotation System

**All 23 component loggers follow the same rotation system** using `BackupDirectoryRotatingFileHandler`:

- **When**: All logs rotate at midnight
- **Format**: `component.log.2025-08-07`, `component.log.2025-08-08`, etc.
- **Location**: Rotated files moved to `logs/backups/` directory
- **Retention**: 7 days of rotated logs kept by default
- **Windows-Safe**: Handles file locking issues with retry logic

### Archival Process

- **Trigger**: Logs older than 7 days are automatically compressed
- **Schedule**: Daily at 02:00 via the scheduler system
- **Compression**: Gzip compression to save space
- **Location**: Compressed files moved to `logs/archive/`
- **Retention**: Archived logs kept for 30 days by default
- **Naming**: `component.log.YYYY-MM-DD.gz` format
- **Automatic**: No manual intervention required - runs via `SchedulerManager.perform_daily_log_archival()`

### Example File Lifecycle
1. **Day 1**: `discord.log` (active)
2. **Day 2**: `discord.log` (active) + `logs/backups/discord.log.2025-08-07` (rotated)
3. **Day 8**: `logs/backups/discord.log.2025-08-07` gets compressed to `logs/archive/discord.log.2025-08-07.gz`
4. **Day 38**: `logs/archive/discord.log.2025-08-07.gz` gets deleted

### Component Logger Rotation Configuration

All component loggers use identical rotation settings:
```python
file_handler = BackupDirectoryRotatingFileHandler(
    log_file_path,
    backup_dir=log_paths['backup_dir'],  # logs/backups/
    when='midnight',
    interval=1,
    backupCount=7,  # Keep 7 days of logs
    encoding='utf-8'
)
```

## Configuration

### Essential Environment Variables

```bash
# Log level (WARNING, INFO, DEBUG, etc.)
LOG_LEVEL=WARNING

# Log directories
LOGS_DIR=logs
LOG_BACKUP_DIR=logs/backups
LOG_ARCHIVE_DIR=logs/archive

# Core system log files
LOG_MAIN_FILE=logs/app.log
LOG_ERRORS_FILE=logs/errors.log
LOG_SCHEDULER_FILE=logs/scheduler.log
LOG_FILE_OPS_FILE=logs/file_ops.log
LOG_USER_ACTIVITY_FILE=logs/user_activity.log

# Communication log files
LOG_DISCORD_FILE=logs/discord.log
LOG_EMAIL_FILE=logs/email.log
LOG_COMMUNICATION_MANAGER_FILE=logs/communication_manager.log
LOG_MESSAGE_FILE=logs/message.log

# AI system log files
LOG_AI_FILE=logs/ai.log
LOG_AI_CACHE_FILE=logs/ai_cache.log
LOG_AI_CONTEXT_FILE=logs/ai_context.log
LOG_AI_CONVERSATION_FILE=logs/ai_conversation.log
LOG_AI_PROMPT_FILE=logs/ai_prompt.log

# UI and management log files
LOG_UI_FILE=logs/ui.log
LOG_BACKUP_FILE=logs/backup.log
LOG_SCHEDULE_UTILITIES_FILE=logs/schedule_utilities.log

# Analytics and check-in log files
LOG_ANALYTICS_FILE=logs/analytics.log
LOG_CHECKIN_DYNAMIC_FILE=logs/checkin_dynamic.log

# Channel management log files
LOG_CHANNEL_ORCHESTRATOR_FILE=logs/channel_orchestrator.log
LOG_CHANNEL_MONITOR_FILE=logs/channel_monitor.log
LOG_RETRY_MANAGER_FILE=logs/retry_manager.log
```

### Component-Specific Configuration

Each component logger can be configured independently:

```python
# Get logger with custom level
discord_logger = ComponentLogger('discord', LOG_DISCORD_FILE, level=logging.DEBUG)
```

## Best Practices

### 1. Use Appropriate Components

- **Channels**: `discord`, `email`
- **UI**: `ui`
- **Orchestration**: `communication_manager`, `channel_orchestrator`
- **Core subsystems**: `file_ops`, `scheduler`, `user_activity`, `main`
- **AI system**: `ai`, `ai_cache`, `ai_context`, `ai_conversation`, `ai_prompt`
- **Message processing**: `message`
- **Analytics**: `analytics`, `checkin_dynamic`
- **Management**: `backup`, `schedule_utilities`
- **Monitoring**: `channel_monitor`, `retry_manager`
- **System**: `main`, `errors`

### 2. BaseChannel Pattern (Standardized)
- Subclasses do not set their own loggers
- `communication/communication_channels/base/base_channel.py` assigns `self.logger = get_component_logger(self.config.name)`
- Channel classes should ensure `config.name` matches the component (`discord`, `email`, `telegram`)

### 3. Test Isolation Behavior
- When `MHM_TESTING=1` and `TEST_VERBOSE_LOGS=1`:
  - All component logs (including errors) are remapped under `tests/logs/`
  - **TestContextFormatter** automatically prepends test names to all log messages
  - Real logs are not written during tests
- When `MHM_TESTING=1` and `TEST_VERBOSE_LOGS` is not set:
  - Component loggers are no-ops; tests remain quiet

### 4. Include Relevant Context

```python
# Good: Include relevant metadata
user_logger.info("User check-in completed", 
                user_id="123", 
                checkin_type="daily",
                questions_answered=5)

# Avoid: Too much or irrelevant data
user_logger.info("User check-in completed", 
                user_id="123",
                timestamp="2025-08-07T01:00:00Z",  # Redundant
                random_data="unnecessary")
```

### 5. Use Structured Data for Analysis

```python
# Structured data makes logs easier to analyze
ai_logger.info("AI request processed", 
              model="phi-2", 
              response_time=2.5,
              tokens_used=150,
              confidence=0.85)
```

## Log Analysis

### Viewing Specific Logs

```bash
# View Discord logs
Get-Content logs/discord.log

# View recent errors
Get-Content logs/errors.log -Tail 20

# View user activity
Get-Content logs/user_activity.log
```

### Finding Specific Information

```bash
# Find all Discord connection events
Select-String "connected" logs/discord.log

# Find errors with specific error codes
Select-String "DB001" logs/errors.log

# Find user check-ins
Select-String "check-in" logs/user_activity.log
```

## Maintenance

### Automatic Cleanup

The system automatically:
- Rotates logs daily
- Compresses logs older than 7 days
- Maintains disk space usage

### Manual Cleanup

```python
from core.logger import cleanup_old_logs, compress_old_logs, cleanup_old_archives

# Clean up if total size exceeds 50MB
cleanup_old_logs(max_total_size_mb=50)

# Compress and archive old logs (>7 days)
compressed_count = compress_old_logs()

# Remove archived logs older than 30 days
removed_count = cleanup_old_archives(max_days=30)
```

### Automatic Maintenance

The system automatically:
- Rotates logs daily at midnight
- **Schedules log archival daily at 02:00** via the scheduler system
- Compresses logs older than 7 days
- Moves compressed logs to archive directory
- Cleans up archives older than 30 days
- Maintains disk space usage

### Scheduler Integration

Log archival is now fully integrated with the MHM scheduler system:
- **Daily Schedule**: Runs automatically at 02:00 every day
- **Method**: `SchedulerManager.perform_daily_log_archival()`
- **Functions**: Calls `compress_old_logs()` and `cleanup_old_archives()`
- **Logging**: All archival operations are logged to the scheduler log
- **Error Handling**: Uses the standard error handling system with `@handle_errors`

## Migration from Old System

The system prefers component loggers. Replace module loggers in channel-related modules with `get_component_logger('<component>')`. Root logger remains simple (app.log + console). Discord library noise is suppressed (WARNING, propagate=False) with gateway heartbeat filter applied.

### Legacy Compatibility Logging Standard

Use the following format for any temporary legacy paths:

```python
# LEGACY COMPATIBILITY: [Brief description]
# TODO: Remove after [specific condition]
# REMOVAL PLAN:
# 1. [Step 1]
# 2. [Step 2]
# 3. [Step 3]
logger.warning("LEGACY COMPATIBILITY: <what was called>; use <new path> instead")
```

Guidelines:
- Only add legacy paths when necessary to prevent breakage
- Always log usage at WARNING level to track and plan removal
- Add a clear removal condition and steps

### Before (Old System)
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Discord bot connected")
```

### After (New System)
```python
from core.logger import get_component_logger
discord_logger = get_component_logger('discord')
discord_logger.info("Discord bot connected", latency=0.1)

# Channel orchestration
comm_logger = get_component_logger('communication_manager')
comm_logger.info("All channels started successfully")

# UI module
ui_logger = get_component_logger('ui')
ui_logger.info("Admin panel started")
```

## Troubleshooting

### Log Files Not Created
- Ensure `logs/` directory exists
- Check file permissions
- Verify component name is valid

### Log Rotation Issues (Windows)
- **Problem**: Log files stop updating due to file locking during rotation
- **Solution**: Use `clear_log_file_locks()` to clear file locks
- **Recovery**: Use `force_restart_logging()` to restart logging system
- **Prevention**: Improved rotation handling with better Windows compatibility

### Performance Issues
- Use appropriate log levels
- Avoid excessive structured data
- Consider using `debug` level sparingly

### Disk Space
- Monitor log file sizes
- Use `cleanup_old_logs()` if needed
- Check compression is working

### Logging System Recovery
If logging stops working:
1. Check for conflicting MHM processes: `Get-Process python`
2. Stop conflicting processes if found
3. Use `clear_log_file_locks()` to clear file locks
4. Use `force_restart_logging()` to restart logging system
5. Verify logs are updating: `Get-ChildItem logs/ -Name | ForEach-Object { Write-Host "$_ - Last modified: $((Get-Item "logs/$_").LastWriteTime)" }`