# Logging Guide

> **File**: `logs/LOGGING_GUIDE.md`  
> **Audience**: Developers and maintainers  
> **Purpose**: Describe logging architecture, behavior, and maintenance tasks for MHM  
> **Style**: Technical, example-driven, detailed  
> **Pair**: `ai_development_docs/AI_LOGGING_GUIDE.md`  

This document describes how logging works in MHM and how to use it safely when developing or debugging.


---

## 1. Purpose and Scope

MHM uses a central logging system to:

- Track normal behavior (info, debug)
- Record warnings and recoverable errors
- Capture critical failures for troubleshooting
- Support long-term maintenance (legacy compatibility, deprecation paths)
- Provide input for audits, coverage, and quality tooling

This guide covers:

- Overall logging architecture
- Log levels and when to use them
- Component log files and directory layout
- Environment-based configuration
- Rotation, archival, and maintenance
- Legacy compatibility logging
- Best practices and examples

---

## 2. Logging Architecture

### 2.1. Central logger module

The logging system is centralized in `core/logger.py`:

- Provides helpers (for example `logger.get_component_logger(name)`) that:
  - Attach the correct handlers (file and optional console)
  - Use the configured log format
  - Direct output to the right component log file

Always obtain loggers via the central helper instead of calling `logging.getLogger` directly. This keeps formats, destinations, and levels consistent across the codebase.

### 2.2. Component loggers

Common components include:

- `main` / core service -> `logs/app.log`
- `discord` -> `logs/discord.log`
- `email` -> `logs/email.log`
- `telegram` -> `logs/telegram.log` (currently disabled in code, but logging path exists)
- `scheduler` -> `logs/scheduler.log`
- `ui` -> `logs/ui.log`
- `ai` -> `logs/ai.log`
- `file_ops` -> `logs/file_ops.log`
- `user_activity` -> `logs/user_activity.log`
- `errors` -> `logs/errors.log`

The actual mapping is defined in `core/logger.py` and may be overridden via environment variables (see below).

### 2.3. Format

Log messages follow a standard format similar to:

```text
YYYY-MM-DD HH:MM:SS,mmm | LEVEL | component | message...
```

This format is enforced by the handlers in `core/logger.py` so logs remain consistent across modules and processes.

---

## 3. Log Levels and When to Use Them

MHM uses standard Python logging levels:

### 3.1. DEBUG

Highly detailed information for debugging and development.

- Avoid in hot paths unless it is genuinely useful during troubleshooting.

### 3.2. INFO

Normal operational messages.

- Startup/shutdown, configuration loaded, tasks scheduled or completed.

### 3.3. WARNING

Something unexpected or degraded, but the system can continue.

- Network retry, fallback behavior, use of a legacy path, soft validation failure.

### 3.4. ERROR

A failure of an operation that affects current behavior but does not crash the whole system.

- Unhandled exceptions in a specific operation that are caught by the error handler.

### 3.5. CRITICAL

Serious failures that may require immediate attention.

- For example, configuration missing such that the system cannot start, or data corruption detected.

Use the lowest level that clearly conveys the severity while keeping noise manageable.

---

## 4. Component Log Files and Layout

Default structure (may vary slightly as the project evolves):

```text
logs/
|-- app.log              # Main application log
|-- errors.log           # Centralized error log
|-- ai.log               # AI interactions and tooling
|-- discord.log          # Discord bot and interactions
|-- email.log            # Email sending/receiving
|-- telegram.log         # Telegram integration (currently disabled)
|-- scheduler.log        # Scheduling and timers
|-- ui.log               # Qt UI events and actions
|-- file_ops.log         # File operations, backups, auto-cleanup
|-- user_activity.log    # High-level user actions/events
|-- backups/             # Rotated/backup log files (see config)
`-- archive/             # Archived/long-term storage
```

Tests may also write logs under:

```text
tests/logs/
```

when test logging is enabled (see `TEST_VERBOSE_LOGS` below).

---

## 5. Configuration (Environment Variables)

Logging is configured via environment variables loaded in `core/config.py`. From your `.env`:

### 5.1. Core locations

- `LOGS_DIR`  
  Root logs directory (default: `logs`).

- `LOG_BACKUP_DIR`  
  Directory for backup copies of logs (default: `logs/backups`).

- `LOG_ARCHIVE_DIR`  
  Directory for archived logs (default: `logs/archive`).

- `LOG_FILE_PATH`  
  Main app log file path (often the same as `LOG_MAIN_FILE`).

### 5.2. Per-component log files

Optional overrides (all default under `LOGS_DIR`):

- `LOG_MAIN_FILE`
- `LOG_DISCORD_FILE`
- `LOG_AI_FILE`
- `LOG_USER_ACTIVITY_FILE`
- `LOG_ERRORS_FILE`
- `LOG_COMMUNICATION_MANAGER_FILE`
- `LOG_EMAIL_FILE`
- `LOG_TELEGRAM_FILE`
- `LOG_UI_FILE`
- `LOG_FILE_OPS_FILE`
- `LOG_SCHEDULER_FILE`

If unset, `core/logger.py` derives sensible defaults under `LOGS_DIR`.

### 5.3. Levels and rotation

- `LOG_LEVEL`  
  Overall log level (console and file): `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.  
  Default is typically `WARNING` for production-like runs.

- `LOG_MAX_BYTES`  
  Max size of each log file before rotation (for example `5242880` for ~5 MB).

- `LOG_BACKUP_COUNT`  
  Number of rotated log files to keep per component.

- `LOG_COMPRESS_BACKUPS`  
  `true` / `false` (or `1` / `0`) to control compression of rotated logs.

- `DISABLE_LOG_ROTATION`  
  Set to `1` to disable rotation entirely (for example, during certain types of debugging).

### 5.4. Testing and diagnostics

- `MHM_TESTING`  
  Flag used to indicate tests are running. Logging behavior may adjust (for example, different destinations or verbosity).

- `TEST_VERBOSE_LOGS`  
  Set to `1` to write detailed test logs under `tests/logs`.  
  Set to `0` (default) to avoid clutter when running tests frequently.

Other diagnostic and backup environment variables (such as `BACKUP_RETENTION_DAYS` and file-auditor settings) may affect how long logs and backups are kept, but are not logging-exclusive.

---

## 6. Log Rotation, Backups, and Archival

Rotation is typically implemented via rotating handlers configured in `core/logger.py`:

- When a log file reaches `LOG_MAX_BYTES`, it is rotated.
- Up to `LOG_BACKUP_COUNT` rotated files are kept (for example `app.log.1`, `app.log.2`, ...).
- If `LOG_COMPRESS_BACKUPS` is enabled, rotated logs may be gzipped or otherwise compressed.

Supporting scripts and services (for example, `backup_manager.py`, `auto_cleanup.py`, and scheduled tasks) may:

- Move older logs into `LOG_ARCHIVE_DIR`
- Enforce retention policies
- Clean up stale or oversized log directories

Exact behavior is driven both by configuration and those scripts; always check the implementation when making changes to retention policies.

---

## 7. Legacy Compatibility Logging Standard

Use the following pattern for any temporary legacy paths:

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

- Only add legacy paths when necessary to prevent breakage.
- Always log legacy usage at `WARNING` level so it is visible in `errors.log` and metrics.
- Add a clear removal condition and specific steps.
- As part of refactors, search for `LEGACY COMPATIBILITY` and reduce/remove those code paths when safe.

---

## 8. Maintenance and Cleanup

Operational guidelines:

- Keep logs out of version control. They should be ignored via `.gitignore`.
- Monitor disk usage in `LOGS_DIR`; adjust `LOG_MAX_BYTES` and `LOG_BACKUP_COUNT` if logs grow too quickly.
- When changing log locations or file names:
  - Update `.env` and `core/config.py` as needed.
  - Confirm that `core/logger.py` still initializes correctly.

Backups and auto-cleanup tools:

- `backup_manager.py` and `auto_cleanup.py` participate in overall log and data maintenance.
- Their exact behavior (retention, archive structure) should be reviewed before changing retention-related environment variables or directory layouts.

---

## 9. Best Practices

### 9.1. Always use component loggers

Prefer `core.logger.get_component_logger("scheduler")` (or equivalent) instead of `logging.getLogger()` directly.

### 9.2. Log context, not secrets

- Include identifiers, counts, and high-level context.
- Never log passwords, tokens, or sensitive user content.

### 9.3. Log expected errors at appropriate levels

- Validation failures that are handled → `INFO` or `WARNING`.
- Unexpected exceptions → `ERROR` or `CRITICAL` (depending on impact), via the central error handling system.

### 9.4. Keep DEBUG focused and temporary

Use `DEBUG` for detailed diagnostics; remove or tone down once issues are resolved.

### 9.5. Align logging with error handling

Most error paths should flow through the centralized error handling system; for category guidance, see section 4. "Error Categories and Severity" in `core/ERROR_HANDLING_GUIDE.md`.

### 9.6. Respect test settings

When writing tests that assert on logs, use helpers/fixtures in `tests/test_utilities.py` rather than ad-hoc file manipulation.

---

## 10. Usage Examples

### 10.1. Basic component logger

```python
from core import logger

log = logger.get_component_logger("scheduler")

def schedule_next_run():
    log.info("Scheduling next run for health reminders")
    # ...
```

### 10.2. Logging a handled error with context

```python
from core import logger

log = logger.get_component_logger("email")

def send_email(to_address, subject, body):
    try:
        # ... send email
        ...
    except Exception as exc:
        log.error(
            "Email send failed",
            exc_info=True,
            extra={"to": to_address, "subject": subject},
        )
        # Defer structured handling to the central error handler where appropriate
```

### 10.3. Legacy compatibility example

```python
from core import logger

log = logger.get_component_logger("main")

def old_entry_point():
    # LEGACY COMPATIBILITY: Kept for older external scripts that still call this function.
    # TODO: Remove after all external callers have been migrated to run_mhm.py.
    # REMOVAL PLAN:
    # 1. Identify and notify remaining callers.
    # 2. Provide migration guidance and timeline.
    # 3. Remove this function and associated documentation.
    log.warning("LEGACY COMPATIBILITY: old_entry_point; use run_mhm.py main entry instead")
    # Delegate to new path
    # ...
```
