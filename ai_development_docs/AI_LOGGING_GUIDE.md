# AI Logging Guide

> **File**: `ai_development_docs/AI_LOGGING_GUIDE.md`  
> **Pair**: [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md)  
> **Audience**: AI assistants and automation tools  
> **Purpose**: Fast routing across logging-related docs for AI collaborators  
> **Style**: Minimal, routing-first  

> This AI document is paired with LOGGING_GUIDE.md. Keep this file's H2 headings in lockstep with LOGGING_GUIDE.md whenever you change the structure. For detailed guidance, examples, and rationale for any topic in this file, use the matching sections in LOGGING_GUIDE.md.

---

## 1. Purpose and Scope

Use this file to decide **where** to look and **which helpers to call** when you need logging:

- Prefer `core/logger.py` helpers over raw `logging` calls.  
- Prefer component loggers (for example `get_component_logger("scheduler")`) over the root logger.  

---

## 2. Logging Architecture

High-level rules:

- Initialize logging once via `setup_logging()` in `core/logger.py` from top-level entry points (`run_mhm.py`, scripts).  
- For all new code, obtain a logger via `core.logger.get_component_logger(component_name)`.  
- Do **not** call `logging.basicConfig` or construct ad-hoc handlers.

Where to look:

- Directory layout and key modules -> section 4. "Key Modules and Responsibilities" in [AI_ARCHITECTURE.md](ai_development_docs/AI_ARCHITECTURE.md).

Common component names (mapped in `core/logger.py`):

- `main`, `errors`, `ai`, `discord`, `email`, `communication_manager`, `scheduler`, `ui`, `file_ops`, `user_activity`, plus a few specialized ones (for example `backup`, `checkin_dynamic`, `development_tools`).  

When in doubt, check the current `log_file_map` in `core/logger.py` rather than inventing new names.

---

## 3. Log Levels and When to Use Them

Core behavior:

- Use standard levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.  
- Only use `DEBUG` for temporary or diagnostic detail.  
- Use `INFO` for normal, high-level events (startup, shutdown, periodic jobs).  
- Use `WARNING` for degraded but handled behavior.  
- Use `ERROR` for failures that affect behavior but are contained by error handling.  
- Use `CRITICAL` for process-threatening situations.

Routing:

- For how log levels interact with error categories and logging, see section 4. "Error Categories and Severity" and section 5.2. "Log messages" in [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md).

---

## 4. Component Log Files and Layout

- Directory overview -> section 1. "Directory Overview" in [AI_ARCHITECTURE.md](ai_development_docs/AI_ARCHITECTURE.md).

Key patterns:

- Component log files live under `LOGS_DIR` (or `tests/logs` when `MHM_TESTING=1`).  
- Backup files live under `LOG_BACKUP_DIR`.  
- Older compressed archives live under `LOG_ARCHIVE_DIR`.  
- Do **not** hard-code paths; use configuration from `core/config.py` and the mapping in `core/logger.py`.

When adding a new component:

1. Add or reuse a component name in the `log_file_map` inside `core/logger.py`.  
2. Use `get_component_logger("<name>")` in the relevant module.  
3. Update section 4. Component Log Files and Layout in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) if the new component is permanent.

---

## 5. Configuration (Environment Variables)

Logging configuration semantics (env vars, defaults, failure modes) are defined in [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) (see Section 3 Logging and Section 10 Testing settings).

Where behavior is configured:

- Logging-related settings live in `core/config.py` and are usually driven by `.env` values.
- For human-facing operational guidance and full variable list, see [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md).

Do not introduce new logging environment variables without updating:

- [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md)
- Section 5. Configuration (Environment Variables) in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md)
- The constants in `core/config.py`

**Development tools isolation** (see Section 5.5 in LOGGING_GUIDE.md): When the entry point is a development-tools script or `MHM_DEV_TOOLS_RUN=1`, logging that would go to `app.log` is routed to `logs/ai_dev_tools.log` so the main app log is untouched. Subprocesses spawned by development tools set this automatically.

## 6. Log Rotation, Backups, and Archival

Core behavior is implemented by `BackupDirectoryRotatingFileHandler` and helpers in `core/logger.py`:

- Time-based (midnight) and size-based rotation ensure logs don't grow unbounded.  
- Rotated files are moved into `LOG_BACKUP_DIR` (e.g. `logs/backups/`) with a date suffix.  
- Backups older than 7 days are compressed and moved to `LOG_ARCHIVE_DIR` (e.g. `logs/archive/`) as `.gz`; archives older than 30 days are removed.

**Backup vs archive**: See section 6.1 in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) and [AI_BACKUP_GUIDE.md](ai_development_docs/AI_BACKUP_GUIDE.md) for how backup filenames relate to content and when files move to archive.

Where to look:

- Implementation details -> `BackupDirectoryRotatingFileHandler`, `compress_old_logs`, `cleanup_old_logs`, and `cleanup_old_archives` in `core/logger.py`.  
- For disk-usage policies or schedules, see `core/backup_manager.py` and `core/auto_cleanup.py`.

AI usage:

- Don't reimplement rotation; call existing helpers or adjust configuration.  
- If you change rotation policies, update section 6 in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) to match.

---

## 7. Legacy Compatibility Logging Standard

For any legacy path that you **must** keep temporarily:

- Follow the comment+warning pattern documented in section 7. Legacy Compatibility Logging Standard in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md).  
- Log at `WARNING` so usage is visible in `errors.log`.  
- Include a clear removal condition and steps in the comment block.

AI rules:

- Never introduce a legacy path without:  
  - A migration plan, and  
  - A `LEGACY COMPATIBILITY` comment block as defined in section 7 of [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md).  
- Coordinate with the error-handling patterns in [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md) when legacy behavior impacts error reporting.

---

## 8. Maintenance and Cleanup

Responsibilities:

- Implementation helpers are in `core/logger.py`, `core/backup_manager.py`, and `core/auto_cleanup.py`.

AI usage:

- When proposing automated cleanup tasks, rely on:  
  - `cleanup_old_logs()` and `compress_old_logs()` in `core/logger.py`.  
  - `cleanup_old_archives()` for long-term archive trimming.  
- Keep retention thresholds and schedules aligned with section 8 of [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md).

---

## 9. Best Practices

High-level rules:

- Always use component loggers (via `get_component_logger`) in new code.  
- Log structured context (key-value pairs) instead of concatenated strings where useful.  
- Never log secrets, tokens, or PHI/PII.  
- Make log messages line up with error categories from section 4. "Error Categories and Severity" in [ERROR_HANDLING_GUIDE.md](core/ERROR_HANDLING_GUIDE.md).  
- Respect testing flags (`MHM_TESTING`, `TEST_VERBOSE_LOGS`) and don't force real log paths during tests.  
- **Noise reduction**: Tools/short-lived processes log init and prompt load at DEBUG; FLOW_STATE_LOAD with 0 user states and scheduler heartbeat are at DEBUG. See section 9.7 in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md).

Cross-doc routing:

- Error-handling patterns -> [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md).  
- Testing and log assertions -> [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md).  
- General development workflow -> [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md).

---

## 10. Usage Examples

This section intentionally **does not** duplicate code samples. Use it as a map:

- Basic component logger usage -> section 10.1. Basic component logger in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md).  
- Logging handled errors with context -> section 10.2. Logging a handled error with context in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md).  
- Legacy compatibility example -> section 10.3. Legacy compatibility example in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md).  

If you need new patterns:

1. Sketch them in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) under section 10. Usage Examples.  
2. Add a short pointer here (one bullet) that routes AI back to the new example.