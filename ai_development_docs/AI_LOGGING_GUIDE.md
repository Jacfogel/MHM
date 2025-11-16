# AI Logging Guide - Quick Reference


> **File**: `ai_development_docs/AI_LOGGING_GUIDE.md`
> **Purpose**: Fast logging patterns and troubleshooting tips for AI collaborators  
> **For details**: See [LOGGING_GUIDE.md](../logs/LOGGING_GUIDE.md)

## Directory Structure
```
logs/
|- app.log                  # Main application flow
|- discord.log              # Discord bot activity
|- ai.log                   # AI interactions and processing
|- user_activity.log        # User actions and check-ins
|- errors.log               # Critical errors (check first)
|- communication_manager.log
|- email.log
|- file_ops.log
|- scheduler.log
|- ui.log
|- message.log
|- ai_dev_tools.log         # AI development tools (separate from core system)
|- backups/                 # Rotated logs (7-day retention)
`- archive/                 # Compressed archives (>7 days)
```

## Component Loggers
```python
from core.logger import get_component_logger

logger = get_component_logger(__name__)
discord_logger = get_component_logger("discord")
ai_logger = get_component_logger("ai")
user_logger = get_component_logger("user_activity")
ai_dev_tools_logger = get_component_logger("ai_development_tools")
```

**Note**: AI development tools (`ai_development_tools/`) use a dedicated component logger (`ai_development_tools` or `ai_dev_tools`) that writes to `ai_dev_tools.log`, keeping development tooling logs separate from core system logs.

- Use component loggers instead of creating ad hoc `logging.getLogger` instances.
- Include context (user id, operation, status) in each message, but avoid sensitive data.

## Triage Workflow
1. Start with `logs/errors.log` to see recent failures.
2. Read `logs/app.log` for surrounding context.
3. Drill into the relevant component log (discord, ai, scheduler, etc.).
4. Look for repeating patterns, missing entries, or timing correlations.

## Handy PowerShell Snippets
```powershell
# Tail recent errors
Get-Content "logs/errors.log" -Tail 20

# Follow the app log live
Get-Content "logs/app.log" -Wait -Tail 10

# Search for critical messages
Select-String -Path "logs/*.log" -Pattern "ERROR|CRITICAL" -SimpleMatch

# Check log sizes
Get-ChildItem "logs/*.log" | Select-Object Name, Length
```

## Common Scenarios
- **Service fails to start**: check `errors.log`, then `app.log` for configuration errors or missing dependencies.
- **Discord issues**: inspect `discord.log` for authentication or connectivity problems.
- **AI processing failures**: review `ai.log` and confirm external dependencies or API access.
- **Scheduler anomalies**: read `scheduler.log` and verify that Windows tasks were not created unintentionally.

## Maintenance
- Logs rotate daily and when they reach 5 MB. Rotated files move to `logs/backups/`; archives older than a week are compressed into `logs/archive/`.
- Cleanup runs automatically, but you can archive manually:
  ```powershell
  Move-Item "logs/*.log" "logs/archive/" -Force
  ```
- Keep the `logs/` directory out of version control.

## Best Practices
1. Choose appropriate levels: ERROR/CRITICAL for failures, WARNING for recoverable issues, INFO for normal operations, DEBUG for temporary tracing.
2. Structure messages with identifiers to help search and correlation.
3. Remove or downgrade noisy DEBUG logs once an issue is resolved.
4. Pair logging with error handling utilities (`core.error_handling`) so callers receive meaningful feedback.

## Related References
- `core/ERROR_HANDLING_GUIDE.md` for exception hierarchy and decorators.
- `AI_REFERENCE.md` for broader troubleshooting workflows.
- `.cursor/rules/quality-standards.mdc` for logging expectations enforced by the ruleset.
