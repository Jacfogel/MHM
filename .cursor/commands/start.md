# Start New Session


> **File**: `.cursor/commands/start.md`
## Overview
Kick off a chat with fresh context and confirm today's goal before acting.

## Steps
1. Optionally refresh the status snapshot:
   ```powershell
   python -m development_tools.run_development_tools status
   ```
2. Confirm environment basics (Windows 11, PowerShell syntax) and reminders from `ai_development_docs/AI_SESSION_STARTER.md`.
3. Review active priorities:
   - `TODO.md`
   - `development_docs/PLANS.md`
   - `development_tools/AI_PRIORITIES.md`
4. Ask the user about today's objective and their energy level.
5. Offer 2-3 actionable paths (tests, feature work, cleanup) and confirm the next step.
6. Note any safety prerequisites (audit, tests, backups) for the chosen path.

## Response Template
- Greeting acknowledging the user profile and energy.
- Snapshot of relevant priorities or recent audit findings.
- Clarifying questions about today's objective.
- Suggested next steps (2-3 options) with estimated effort.
- Reminder that work will follow audit-first, testing, and paired-doc requirements.
