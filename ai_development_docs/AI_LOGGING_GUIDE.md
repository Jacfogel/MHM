> **File**: ai_development_docs/AI_LOGGING_GUIDE.md

# AI Logging Guide

This document is a compact reference for how to use logging in MHM when making code changes or writing tests.

For detailed rationale, examples, and human-focused explanations, see matching sections in `logs/LOGGING_GUIDE.md`.

---

## 1. Purpose

- Use the **central logger module** (`core/logger.py`) for all logging.
- Keep **log levels and destinations consistent** across the project.
- Avoid ad-hoc `print` or `logging.getLogger()` calls.

---

## 2. Core Patterns

### 2.1 Always use the component logger helper

Preferred pattern:

```python
from core import logger

log = logger.get_component_logger("scheduler")

log.info("Scheduling next run")
log.warning("Schedule delay detected")
log.error("Failed to schedule next run", exc_info=True)
```

Do **not** create raw loggers like:

```python
# Avoid
import logging
log = logging.getLogger("scheduler")
```

Centralization in `core/logger.py` ensures:

- Consistent formats
- Correct file destinations
- Respect for environment configuration

---

## 3. Log Levels

Use standard levels with clear intent:

- **DEBUG**: detailed diagnostics during development or investigation.
- **INFO**: normal, expected behavior (startup, shutdown, periodic events).
- **WARNING**: degraded or unexpected behavior that is handled.
- **ERROR**: failed operation that affects current behavior but is contained.
- **CRITICAL**: serious or process-threatening failures.

Avoid using `DEBUG` for routine information; keep it focused on real troubleshooting.

---

## 4. Component Logs and Files

Common components and expected logs (defaults):

- `main` → `logs/app.log`
- `errors` → `logs/errors.log`
- `ai` → `logs/ai.log`
- `discord` → `logs/discord.log`
- `email` → `logs/email.log`
- `telegram` → `logs/telegram.log` (integration currently disabled)
- `scheduler` → `logs/scheduler.log`
- `ui` → `logs/ui.log`
- `file_ops` → `logs/file_ops.log`
- `user_activity` → `logs/user_activity.log`

File mapping and overrides are implemented in `core/logger.py` and `core/config.py`.

When adding a new component:

- Use a clear component name (for example `"backup"`, `"auditor"`).
- Add a mapping in `core/logger.py` if needed.
- Avoid inventing many one-off component names.

For details and directory structure, see **"Component Log Files and Layout"** in `logs/LOGGING_GUIDE.md`.

---

## 5. Environment-Based Configuration

Key environment variables (from `.env`, interpreted by `core/config.py`):

- `LOG_LEVEL`: global level for console/file (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
- `LOGS_DIR`: root logs directory (default `logs`).
- `LOG_BACKUP_DIR`: directory for rotated/backup logs (default `logs/backups`).
- `LOG_ARCHIVE_DIR`: directory for archived logs (default `logs/archive`).
- `LOG_FILE_PATH` / `LOG_MAIN_FILE`: main application log path.

Per-component overrides (defaults under `LOGS_DIR` if unset):

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

Rotation and size:

- `LOG_MAX_BYTES`: max size before rotation.
- `LOG_BACKUP_COUNT`: number of rotated files to keep.
- `LOG_COMPRESS_BACKUPS`: whether to compress backups.
- `DISABLE_LOG_ROTATION`: set to `1` to turn rotation off (use only when necessary).

Testing and diagnostics:

- `MHM_TESTING`: indicates tests are running.
- `TEST_VERBOSE_LOGS`: set to `1` to write detailed test logs under `tests/logs`.

When modifying or introducing new logging behavior, ensure it respects these environment settings.

---

## 6. Legacy Compatibility Logging

When adding or maintaining a legacy code path, use the standard pattern:

```python
log.warning("LEGACY COMPATIBILITY: <what was called>; use <new path> instead")
```

And keep the full comment block:

```python
# LEGACY COMPATIBILITY: [Brief description]
# TODO: Remove after [specific condition]
# REMOVAL PLAN:
# 1. [Step 1]
# 2. [Step 2]
# 3. [Step 3]
```

Rules:

- Only use this when truly needed to preserve compatibility.
- Always log at `WARNING` level so usage is visible.
- Make the removal plan and condition clear.

For human-oriented context and examples, see **"Legacy Compatibility Logging Standard"** in `logs/LOGGING_GUIDE.md`.

---

## 7. Maintenance and Cleanup

Background tools (for example `backup_manager.py`, `auto_cleanup.py`, scheduled jobs) manage:

- Log backups under `LOG_BACKUP_DIR`
- Archives under `LOG_ARCHIVE_DIR`
- General retention (guided by env variables such as `BACKUP_RETENTION_DAYS`)

When changing log paths, rotation settings, or retention policies:

- Confirm that backup/cleanup scripts still target the correct directories.
- Avoid breaking assumptions in those tools (for example, moving or renaming directories without updating the scripts).

---

## 8. Best Practices

When editing or adding code:

- Always obtain a logger via `core.logger.get_component_logger(<component_name>)`.
- Do not log secrets or sensitive data.
- Include enough context in messages (what, where, which user or ID) without over-logging.
- Allow the centralized error handling system to drive most error logging (see `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`).

For tests:

- Use helpers and fixtures from `tests/test_utilities.py` when asserting on logs or creating temporary paths.
- Respect `TEST_VERBOSE_LOGS` and `MHM_TESTING` flags.

For detailed guidance, examples, and troubleshooting tips, see `logs/LOGGING_GUIDE.md`.
