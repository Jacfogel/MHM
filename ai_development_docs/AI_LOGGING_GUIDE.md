# AI Logging Guide

> **File**: `ai_development_docs/AI_LOGGING_GUIDE.md`  
> **Purpose**: Fast logging patterns and troubleshooting tips for AI collaborators  
> **Style**: Minimal, pattern-focused  

For more detailed guidance, examples, and rationale for any topic in this file, use the matching sections in `logs/LOGGING_GUIDE.md`.


## Quick Reference

- Check `errors.log` first for stack traces and critical issues.  
- Then check the relevant component log (for example, `discord.log`, `scheduler.log`, `ui.log`, `communication_manager.log`).  
- Use `app.log` when behavior is unclear and you need high-level flow.  
- Keep all log files under `logs/` and never commit them to version control.  


## Directory Structure

```text
logs/
|- app.log
|- discord.log
|- ai.log
|- user_activity.log
|- errors.log
|- communication_manager.log
|- email.log
|- file_ops.log
|- scheduler.log
|- ui.log
|- message.log
|- backups/
`- archive/
```

- Active logs live directly under `logs/`.  
- `backups/` stores rotated logs.  
- `archive/` stores compressed / older logs.  


## Component Loggers

Each major subsystem uses a named component logger mapped to a file under `logs/`.

Typical mappings:

- Core: `main` → `app.log`, `errors` → `errors.log`  
- Communication: `discord` → `discord.log`, `email` → `email.log`, `communication_manager` → `communication_manager.log`, `message` → `message.log`  
- Scheduler and file operations: `scheduler` → `scheduler.log`, `file_ops` → `file_ops.log`  
- UI: `ui` → `ui.log`  
- User data and analytics: `user_activity` → `user_activity.log`  
- AI: `ai` → `ai.log`  

When adding or modifying code, prefer existing component loggers over new ad-hoc log files.  


## Log Rotation and Archival

Assumptions AI should use:

- Logs rotate daily into `logs/backups/`.  
- Old backups are compressed and moved into `logs/archive/`.  
- A scheduled task handles archival and cleanup using helpers such as `compress_old_logs()` and `cleanup_old_archives()`.  

Guidance:

- Do not suggest custom rotation; rely on existing helpers and scheduler integration.  
- When disk usage is an issue, suggest running or verifying the cleanup helpers rather than deleting files manually.  


## Configuration

Logging paths and options are defined via configuration helpers and environment variables.

AI rules:

- Keep log paths under `logs/` by default.  
- Prefer configuration helpers (for example, in `core.config`) over hard-coded paths.  
- When suggesting changes to logging structure, also mention updating `logs/LOGGING_GUIDE.md` and related configuration.  


## Best Practices

- Use levels consistently: `ERROR` / `CRITICAL` for failures, `WARNING` for recoverable or suspicious behavior, `INFO` for normal operations, `DEBUG` for targeted troubleshooting only.  
- Include identifiers where useful (user ids, task ids, channel ids), but never secrets or full tokens.  
- Keep messages clear and concise so they can be searched and correlated across logs.  
- After resolving an issue, recommend removing or downgrading noisy `DEBUG` statements.  
- Pair logging with standard error handling patterns; route to `AI_ERROR_HANDLING_GUIDE.md` for exception and decorator guidance.  


- For temporary legacy paths, use `LEGACY COMPATIBILITY` comments and a WARNING-level log entry with a clear TODO and removal plan (see `AI_LEGACY_REMOVAL_GUIDE.md`).  
## Log Analysis and Triage

Minimal patterns for AI suggestions:

1. Identify the feature or subsystem involved (UI, scheduler, Discord, email, AI, user data).  
2. Check `errors.log` to see whether exceptions are being raised.  
3. Open the corresponding component log to inspect detailed behavior.  
4. Use timestamps and identifiers to track flow across multiple logs.  
5. Use `app.log` when no obvious issue appears in component logs.

Useful PowerShell commands (for humans, from repo root):

```powershell
# Tail a specific log
Get-Content logs/discord.log -Wait -Tail 50

# Search for ERROR across all logs
Select-String -Path 'logs/*.log' -Pattern 'ERROR' | Select-Object Path, LineNumber, Line
```


## Maintenance

- Suggest checking log file sizes and confirming that rotation and archival are working as expected.  
- Recommend using cleanup helpers (`cleanup_old_logs()`, `cleanup_old_archives()`) instead of manual deletion.  
- When new modules are added, ensure they use existing component loggers and do not write to new ad-hoc log files.  


## Troubleshooting

- **Logs not updating**: Check that `logs/` exists and is writable, confirm the relevant process is running, and inspect `errors.log` for startup or configuration issues.  
- **No errors but behavior is incorrect**: Check the relevant component log and `app.log` around the time of the issue; consider temporarily increasing logging detail for that component.  
- **Disk space or too many logs**: Verify that rotation and archival tasks are running, use cleanup helpers, and, if needed, recommend tighter retention configuration in coordination with project maintainers.

For error handling patterns that interact with logging, refer to `AI_ERROR_HANDLING_GUIDE.md`.
