# Start New Session

## Overview
Use this command when opening a chat so the assistant aligns with the current project context and user preferences.

## Steps
1. Review key references:
   - `ai_development_docs/AI_SESSION_STARTER.md`
   - `ai_development_docs/AI_CHANGELOG.md`
   - `TODO.md` and `development_docs/PLANS.md`
2. Confirm environment basics (Windows 11, PowerShell, beginner-friendly explanations).
3. Ask the user about their immediate goal or pain point before proposing work.
4. **Optional**: Run `python ai_development_tools/ai_tools_runner.py status` for current system status
5. Offer a brief status summary if useful (recent changelog items, open priorities).

## Response Template
- Greeting that acknowledges the user profile and energy level.
- One-paragraph recap of recent activity or open priorities.
- Clarifying questions about today's objective.
- Suggested next steps or options tailored to the user's goals.
- Reminder that all work will follow audit-first and testing requirements.
- **Audit-First Protocol**: Run `python ai_development_tools/ai_tools_runner.py audit` before any documentation work
