# AI Reference - Troubleshooting & System Understanding


> **File**: `ai_development_docs/AI_REFERENCE.md`
> **Purpose**: Troubleshooting patterns and deep system understanding for AI collaborators  
> **For context**: See [AI_SESSION_STARTER.md](AI_SESSION_STARTER.md)

## 1. Troubleshooting Patterns

### 1.1. Documentation appears incomplete
1. Run `python ai_development_tools/ai_tools_runner.py audit` to refresh metrics.
2. Review `ai_development_tools/AI_STATUS.md` and `AI_PRIORITIES.md` to highlight specific gaps.
3. Draft a remediation plan and confirm next steps with the user before editing docs.

### 1.2. Code change introduced failures
1. Check recent logs (`logs/errors.log`, then component logs) for stack traces or context.
2. Re-run the relevant tests (`python run_headless_service.py start`, `python run_tests.py`) to reproduce.
3. Fix incrementally and record the outcome in both changelog tracks.

### 1.3. PowerShell command failed
1. Inspect `$LASTEXITCODE` and ensure PowerShell syntax is used (`;`, `-and`, `$env:`).
2. Verify paths, permissions, and prerequisites before retrying.
3. Capture the corrected command/output and share it with the user if reruns still fail.

### 1.4. User questions accuracy
1. Provide the latest audit metrics (rerun if the previous run is stale).
2. Highlight known limitations or stale data and propose validation steps.
3. Ask what additional evidence or artifacts they want before continuing.

## 2. Communication Patterns
- Ask about the user's goal and any risks they are worried about before suggesting work.
- Offer constructive alternatives when a safer or more efficient option exists.
- Explain why each recommendation matters and keep guidance focused on one concept.
- Handy prompts: "What's your goal for this change?", "Have you considered <alternative>?", "What risks concern you most?"

## 3. System Understanding

### 3.1. Critical files (do not break)
- `run_headless_service.py` - service entry point for collaborators.
- `run_mhm.py` - admin UI entry point.
- `core/service.py`, `core/config.py` - service lifecycle and configuration.
- `core/user_data_handlers.py`, `core/user_data_validation.py` - user data helpers and validation.
- `communication/core/channel_orchestrator.py` - channel coordination.

### 3.2. Data flow patterns
- User data: `data/users/{user_id}/` -> helper APIs -> UI / communication surfaces.
- Messages: `resources/default_messages/` -> per-user `messages/` directories.
- Configuration: `.env` -> `core/config.py` -> runtime consumers.
- Backups: scheduler checks daily at 01:00, keeping seven rotating backups and 30-day archives.

### 3.3. Common issues to watch
- Access data only through helper APIs; avoid direct file edits.
- Regenerate UI layers from `.ui` sources and keep generated Python untouched.
- Centralize configuration changes in `core/config.py`.
- Monitor scheduler logs to ensure reminders and backups run as expected.

## 4. Success Metrics
- Documentation and plans reference the latest audit output.
- Tests and service checks pass after each change.
- The user understands trade-offs and agrees on next steps before continuing.
- Work is logged in both changelog tracks with clear follow-up actions.

## 5. Further Reading
- `../DOCUMENTATION_GUIDE.md`, `../ARCHITECTURE.md`, `../DEVELOPMENT_WORKFLOW.md` for deeper background.
- `SYSTEM_AI_GUIDE.md` for AI subsystem architecture, modes, and runtime behavior.
- `AI_LOGGING_GUIDE.md`, `AI_TESTING_GUIDE.md`, `AI_ERROR_HANDLING_GUIDE.md` for focused playbooks.