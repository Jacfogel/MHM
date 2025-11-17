# Enhanced Logging System Guide

> **File**: `logs/LOGGING_GUIDE.md`  
> **Audience**: Developers and AI collaborators working with the MHM logging system  
> **Purpose**: Explain how logging is structured, where logs live, and how to use them for debugging and maintenance  
> **Style**: Technical, comprehensive, reference-oriented


## Quick Reference

Use this section when you need to debug something quickly.

- Start with `errors.log` for unhandled errors and critical issues.  
- Then check the component log for the area you are working on (for example, `discord.log`, `scheduler.log`, `ui.log`).  
- Use `app.log` when behavior is unclear and you need a high-level view of application flow.  
- For communication issues, check `communication_manager.log`, `discord.log`, `email.log`, and `message.log`.  
- For scheduling issues, check `scheduler.log` and any related component logs (for example, `file_ops.log` for archival).  
- For user activity and check-ins, check `user_activity.log` and related analytics logs.

PowerShell triage snippets from the repo root:

```powershell
# Show all log files and their last write times
Get-ChildItem logs/*.log | Select-Object Name, LastWriteTime | Format-Table -AutoSize

# Follow the main error log
Get-Content logs/errors.log -Wait -Tail 50

# Search for a specific user or ID across logs
Select-String -Path 'logs/*.log' -Pattern 'user_id=123' | Select-Object Path, LineNumber, Line
```


## Directory Structure

The logging system uses a dedicated `logs/` directory with per-component log files and two subdirectories for rotated and archived logs.

Example layout:

```text
logs/
|-- app.log                    # Main application logs (active)
|-- discord.log                # Discord bot logs (active)
|-- ai.log                     # AI interactions and processing (active)
|-- user_activity.log          # User actions and check-ins (active)
|-- errors.log                 # Error and critical messages (active)
|-- communication_manager.log  # Communication orchestration (active)
|-- email.log                  # Email bot operations (active)
|-- file_ops.log               # File operations (active)
|-- scheduler.log              # Scheduler operations (active)
|-- ui.log                     # UI operations (active)
|-- message.log                # Message processing (active)
|-- backups/                   # Rotated log files (recent, uncompressed)
`-- archive/                   # Compressed / older logs
```

Directory purposes:

- **Active logs** – Current log files being written to.  
- **Backups** – Rotated log files kept for a limited time (recent days).  
- **Archive** – Compressed logs kept for long-term retention.


## Component Loggers

The enhanced logging system uses **component loggers** instead of one global logger. Each major subsystem has its own named logger and log file.

### Component loggers and files

| Logger name              | File                          | Purpose                               |
|--------------------------|-------------------------------|---------------------------------------|
| `main`                   | `app.log`                     | Overall application flow              |
| `discord`                | `discord.log`                 | Discord bot activity                  |
| `ai`                     | `ai.log`                      | AI processing and interactions        |
| `user_activity`          | `user_activity.log`           | User actions and check-ins            |
| `errors`                 | `errors.log`                  | Errors and critical issues            |
| `communication_manager`  | `communication_manager.log`   | Message routing and orchestration     |
| `email`                  | `email.log`                   | Email bot operations                  |
| `file_ops`               | `file_ops.log`                | File operations and backups           |
| `scheduler`              | `scheduler.log`               | Scheduling and timer operations       |
| `ui`                     | `ui.log`                      | UI interactions and dialogs           |
| `message`                | `message.log`                 | Message processing and templating     |

### Typical module → logger mapping

Core modules:

- `core/service.py` – `main`, `discord`  
- `core/user_data_handlers.py` – `main`, `user_activity`  
- `core/config.py` – `main`  
- `core/schedule_utilities.py` – `scheduler`  
- `core/file_operations.py` – `file_ops`  
- `core/scheduler.py` – `scheduler`  
- `core/backup_manager.py` – `file_ops`, `main`  
- `core/message_management.py` – `message`  
- `core/user_management.py` – `main`, `user_activity`  
- `core/checkin_dynamic_manager.py` – `user_activity`  
- `core/checkin_analytics.py` – `user_activity`  
- `core/response_tracking.py` – `user_activity`  

Communication modules:

- `communication/core/channel_orchestrator.py` – `communication_manager`, `user_activity`  
- `communication/communication_channels/discord/bot.py` – `discord`  
- `communication/communication_channels/email/bot.py` – `email`  
- `communication/message_processing/message_router.py` – `message`  

AI modules:

- `ai/chatbot.py` – `ai`  
- `ai/lm_studio_manager.py` – `ai`  

UI modules:

- `ui/ui_app_qt.py` – `ui`  
- `ui/dialogs/*.py` – `ui`  
- `ui/widgets/*.py` – `ui`  


## Log Rotation and Archival

Logs rotate and are archived automatically to keep disk usage under control.

- Daily rotation moves active logs into `logs/backups/`.  
- Older backups are compressed and moved into `logs/archive/`.  
- The scheduler triggers daily archival and cleanup tasks.  
- Default retention periods:
  - Recent uncompressed backups – kept for several days.  
  - Archived compressed logs – kept for longer-term history.

Key helper functions (names may vary slightly depending on implementation):

- `compress_old_logs()` – Compress logs older than a threshold into `.gz` files in `archive/`.  
- `cleanup_old_archives(max_days=30)` – Remove very old archives.  
- `cleanup_old_logs()` – Remove old backup files when needed.

Scheduler integration:

- Daily archival is orchestrated through the scheduler system (for example, `SchedulerManager.perform_daily_log_archival()`).  
- All log archival operations write to `scheduler.log` and component logs.  
- Errors during archival are handled by the standard error handling system and should appear in `errors.log`.  


## Configuration

Logging paths and options are controlled primarily through environment variables and configuration helpers in `core.config` and related modules.

Examples of configuration entries (conceptual):

```text
# Base log directory
LOG_DIR=logs

# Core log files
LOG_APP_FILE=logs/app.log
LOG_ERRORS_FILE=logs/errors.log

# Communication log files
LOG_DISCORD_FILE=logs/discord.log
LOG_EMAIL_FILE=logs/email.log
LOG_COMMUNICATION_MANAGER_FILE=logs/communication_manager.log
LOG_MESSAGE_FILE=logs/message.log

# AI system log files
LOG_AI_FILE=logs/ai.log

# UI and management log files
LOG_UI_FILE=logs/ui.log
LOG_BACKUP_FILE=logs/backup.log
LOG_SCHEDULER_FILE=logs/scheduler.log

# Analytics and check-in log files
LOG_USER_ACTIVITY_FILE=logs/user_activity.log
```

Guidelines:

- Keep all log paths under the `logs/` directory by default.  
- Use the configuration helpers rather than hard-coding paths in new modules.  
- When changing log structure, update both configuration and this guide.  


## Best Practices

### Logging style

- Use clear, concise messages with enough context to understand what happened.  
- Include identifiers (user id, task id, channel id) where helpful for correlation.  
- Avoid logging secrets, full tokens, or sensitive personal data.  
- Prefer `INFO` for normal operations, `WARNING` for recoverable issues, `ERROR` for failures, and `CRITICAL` for unrecoverable conditions.  
- Use `DEBUG` sparingly and remove or downgrade noisy debug logs once issues are resolved.

### Integration with error handling

- When catching exceptions, log the error with context and then use the established error handling patterns (see `core/ERROR_HANDLING_GUIDE.md` and `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`).  
- Prefer raising well-structured custom exceptions after logging, instead of returning ambiguous values.  
- Ensure that user-facing errors and logs remain in sync so issues can be diagnosed from logs alone.  



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

## Log Analysis and Triage

Use these patterns when investigating a problem.

### General triage

1. Check `errors.log` first for stack traces and critical issues.  
2. Identify the subsystem involved (UI, scheduler, Discord, email, AI, user data).  
3. Open the corresponding component log (for example, `discord.log`, `scheduler.log`, `ui.log`).  
4. Use timestamps and identifiers to follow the flow across multiple logs.  
5. If nothing is obvious, inspect `app.log` for higher-level context.

### Useful PowerShell commands

From the repo root:

```powershell
# Tail a specific log
Get-Content logs/discord.log -Wait -Tail 50

# Search for a specific phrase across all logs
Select-String -Path 'logs/*.log' -Pattern 'ERROR' | Select-Object Path, LineNumber, Line

# Show only ERROR/CRITICAL lines from errors.log
Select-String -Path 'logs/errors.log' -Pattern 'ERROR|CRITICAL'
```


## Maintenance

Routine tasks:

- Periodically check log file sizes and rotation behavior.  
- Ensure that `backups/` and `archive/` do not grow without bound.  
- Run cleanup helpers (`cleanup_old_logs()`, `cleanup_old_archives()`) when needed or verify that scheduled tasks are running.  
- Confirm that new modules use the correct component loggers rather than creating ad-hoc log files.

When making structural changes to logging:

- Update the configuration and this guide.  
- Ensure that any new component logger has a clear purpose, file path, and is integrated into rotation/archival.  
- Update `ai_development_docs/AI_LOGGING_GUIDE.md` so AI collaborators route to the correct logs.  


## Troubleshooting

### Symptoms: logs not updating

- Verify the `logs/` directory exists and is writable.  
- Confirm that the relevant process is running (for example, via Task Manager or `Get-Process python`).  
- Check for file locks or permission issues; if necessary, stop other processes that may be holding log files open.  
- Restart the service or application and watch `errors.log` for startup issues.

### Symptoms: no errors but incorrect behavior

- Use `app.log` to understand the high-level flow around the time of the issue.  
- Use the component logs to inspect detailed behavior.  
- Cross-reference any unusual events with `errors.log` to see if subtle exceptions are being caught and logged.  
- If necessary, temporarily increase logging detail for the relevant component (for example, enabling more DEBUG logs).

### Symptoms: disk space issues

- Check the size of `logs/`, `logs/backups/`, and `logs/archive/`.  
- Run the cleanup helpers to remove old backups and archives.  
- Ensure that rotation and archival are actually running (scheduler log, scheduler configuration).  
- Consider tightening retention if logs grow faster than expected.  
