# AI Session Starter

> **File**: `ai_development_docs/AI_SESSION_STARTER.md`
> **Audience**: AI collaborators working on the MHM codebase and docs
> **Purpose**: Provide a compact starting point for where to look and what rules to follow in a new session
> **Style**: Minimal, routing-focused, no deep explanations

> For detailed explanations, rationale, and examples, use:
> - README.md (project overview)
> - HOW_TO_RUN.md (run modes and environment details)
> - The paired human docs referenced below for deep behavior and history

## 1. Starting a Session

When you attach to MHM, do this first:

1. **Identify the user's focus**  
   - Read the latest user message carefully.  
   - If they mention a specific file or doc, open that file first.

2. **Locate the relevant AI guide**  
   - For development work, start with [AI_DEVELOPMENT_WORKFLOW.md](AI_DEVELOPMENT_WORKFLOW.md), especially:
     - Section 1 "Safety First"
     - Section 3 "Standard Development Cycle"
     - Section 10 "Standard Audit Recipe" (when to run audit commands)
   - For documentation changes, use [AI_DOCUMENTATION_GUIDE.md](AI_DOCUMENTATION_GUIDE.md), especially:
     - Section 3 "Documentation Synchronization Checklist"
     - Section 5 "Generated Documentation Standards"
   - **For development tools, audits, or reports**: When the user's task touches dev tools, audits, coverage, or analysis, route to [AI_DEVELOPMENT_TOOLS_GUIDE.md](../development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md) as the primary reference. This includes:
     - Running audits or status checks
     - Understanding tool tiers and trust levels
     - Working with generated reports (AI_STATUS.md, AI_PRIORITIES.md, consolidated_report.txt)
     - Using commands like `audit`, `status`, `doc-sync`, `docs`, `legacy`, `coverage`

3. **Stay within scope**  
   - Use only the files present in the current workspace (for example, those the user has uploaded or explicitly referenced).  
   - If a needed file or report is missing, ask the user to provide it instead of guessing its contents.

4. **Confirm expectations**  
   - If the task is ambiguous (for example, "fix this" without context), ask 1-2 pointed clarification questions.  
   - Once the scope is clear, follow the relevant AI guide(s) from step 2.

## 2. Core AI References

Use these AI docs as your primary routing table; they, in turn, point to detailed human docs:

- **Development workflow** - [AI_DEVELOPMENT_WORKFLOW.md](AI_DEVELOPMENT_WORKFLOW.md)  
  - Section 1 "Safety First" - constraints and guardrails.  
  - Section 3 "Standard Development Cycle" - step-by-step development loop.

- **Architecture** - [AI_ARCHITECTURE.md](AI_ARCHITECTURE.md)  
  - For where modules live, key services, and high-level boundaries.

- **Logging** - [AI_LOGGING_GUIDE.md](AI_LOGGING_GUIDE.md)  
  - For where logs live and how to extend logging safely.

- **Testing** - [AI_TESTING_GUIDE.md](AI_TESTING_GUIDE.md)  
  - Section 4 "Test Layout and Discovery" - where tests live and how to add new ones.

- **Error handling** - [AI_ERROR_HANDLING_GUIDE.md](AI_ERROR_HANDLING_GUIDE.md)  
  - For how to use `MHMError` and structure error handling.

- **Development tooling** - [AI_DEVELOPMENT_TOOLS_GUIDE.md](../development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md)  
  - Section 1 "Main Entry Point" - `development_tools/run_development_tools.py` commands.  
  - Section 2 "Fast Mode vs Full Mode" - when to use `audit` vs `audit --full`.  
  - Section 3 "Generated Outputs" - where reports and status files live.  
  - Check `development_tools/shared/standard_exclusions.py` (and config) before running tools so `.ruff_cache`, `mhm.egg-info`, `scripts`, `tests/ai/results`, and `tests/coverage_html` stay skipped.

- **Legacy removal** - [AI_LEGACY_REMOVAL_GUIDE.md](AI_LEGACY_REMOVAL_GUIDE.md)  
  - Quick reference for using `development_tools/legacy/fix_legacy_references.py` and the `legacy` command.  
  - Tightly coupled with [AI_DEVELOPMENT_TOOLS_GUIDE.md](../development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md) and the legacy reports described there.

## 3. Safe Change Rules

Follow these high-level rules whenever you propose or describe changes:

1. **Respect existing patterns**  
   - Match existing styles in logging, testing, error handling, and configuration.  
   - Prefer extending existing docs, tests, and modules over inventing new top-level structures.

2. **Keep AI vs human docs aligned**  
  - For paired docs, H2 headings must match as a set (see section 3 "Documentation Synchronization Checklist" in [AI_DOCUMENTATION_GUIDE.md](AI_DOCUMENTATION_GUIDE.md)).  
   - AI docs summarize and route; human docs contain detailed explanations.

3. **Avoid partial or speculative edits**  
   - Do not describe or "fix" modules you cannot see.  
   - If a function or behavior is unclear, ask for the relevant file or an example before rewriting it.

4. **Tie changes to tests and tools**  
  - When you propose code changes, also point to where tests should be added or updated (see [AI_TESTING_GUIDE.md](AI_TESTING_GUIDE.md)).  
   - Where appropriate, suggest re-running:
     - `python development_tools/run_development_tools.py audit`  
     - `python development_tools/run_development_tools.py status`  
     - `python development_tools/run_development_tools.py legacy` (for legacy-related work).

## 4. Typical Tasks and Where to Look

Use this as a routing table for common request types.

### 4.1. "Help me edit documentation"

- Start with [AI_DOCUMENTATION_GUIDE.md](AI_DOCUMENTATION_GUIDE.md), sections:
  - 3 "Documentation Synchronization Checklist"  
  - 4 "Maintenance Guidelines"  
- Then open the relevant human doc (for example, `DOCUMENTATION_GUIDE.md`, `logs/LOGGING_GUIDE.md`, `tests/TESTING_GUIDE.md`).  
- Keep AI docs short; push detailed narrative into the human docs.

### 4.2. "Help me refactor or clean up code"

- Start with [AI_DEVELOPMENT_WORKFLOW.md](AI_DEVELOPMENT_WORKFLOW.md), especially section 1 "Safety First" and section 3 "Standard Development Cycle".  
- Use [AI_DEVELOPMENT_TOOLS_GUIDE.md](../development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md) for commands to run audits and checks.  
- For legacy-related refactors, also use [AI_LEGACY_REMOVAL_GUIDE.md](AI_LEGACY_REMOVAL_GUIDE.md) and the legacy tools described there.

### 4.3. "Help me understand the system"

- Use [AI_ARCHITECTURE.md](AI_ARCHITECTURE.md) as the primary overview.  
- Use [README.md](README.md) and [HOW_TO_RUN.md](HOW_TO_RUN.md) for a human-readable overview of goals and run modes.  
- For channel-specific behavior (Discord, email, etc.), look for channel guides under `communication/communication_channels/`.


## 5. Troubleshooting Patterns and System Understanding

### 1. Troubleshooting Patterns

#### 1.1. Documentation appears incomplete
1. Run `python development_tools/run_development_tools.py audit` to refresh metrics.
2. Review [AI_STATUS.md](development_tools/AI_STATUS.md) and [AI_PRIORITIES.md](development_tools/AI_PRIORITIES.md) to highlight specific gaps.
3. Draft a remediation plan and confirm next steps with the user before editing docs.

#### 1.2. Code change introduced failures
1. Check recent logs (`logs/errors.log`, then component logs) for stack traces or context.
2. Re-run the relevant tests (`python run_headless_service.py start`, `python run_tests.py`) to reproduce.
3. Fix incrementally and record the outcome in both changelog tracks.

#### 1.3. PowerShell command failed
1. Inspect `$LASTEXITCODE` and ensure PowerShell syntax is used (`;`, `-and`, `$env:`).
2. Verify paths, permissions, and prerequisites before retrying.
3. Capture the corrected command/output and share it with the user if reruns still fail.

#### 1.4. User questions accuracy
1. Provide the latest audit metrics (rerun if the previous run is stale).
2. Highlight known limitations or stale data and propose validation steps.
3. Ask what additional evidence or artifacts they want before continuing.

### 2. Communication Patterns
- Ask about the user's goal and any risks they are worried about before suggesting work.
- Offer constructive alternatives when a safer or more efficient option exists.
- Explain why each recommendation matters and keep guidance focused on one concept.
- Handy prompts: "What's your goal for this change?", "Have you considered <alternative>?", "What risks concern you most?"

### 3. System Understanding

#### 3.1. Critical files (do not break)
- `run_headless_service.py` - service entry point for collaborators.
- `run_mhm.py` - admin UI entry point.
- `core/service.py`, `core/config.py` - service lifecycle and configuration.
- `core/user_data_handlers.py`, `core/user_data_validation.py` - user data helpers and validation.
- `communication/core/channel_orchestrator.py` - channel coordination.

#### 3.2. Data flow patterns

User data persistence guarantees and access rules are defined in `core/USER_DATA_MODEL.md`.

- User data: `data/users/{user_id}/` -> helper APIs -> UI / communication surfaces.
- Messages: `resources/default_messages/` -> per-user `messages/` directories.
- Configuration: `.env` -> `core/config.py` -> runtime consumers.
- Backups: see BACKUP_GUIDE.md for operational behavior and `CONFIGURATION_REFERENCE.md` for retention/diagnostic settings.

#### 3.3. Common issues to watch
- Access data only through helper APIs; avoid direct file edits.
- Regenerate UI layers from `.ui` sources and keep generated Python untouched.
- Centralize configuration changes in `core/config.py`.
- Monitor scheduler logs to ensure reminders and backups run as expected.

### 4. Success Metrics
- Documentation and plans reference the latest audit output.
- Tests and service checks pass after each change.
- The user understands trade-offs and agrees on next steps before continuing.
- Work is logged in both changelog tracks with clear follow-up actions.

### 5. Further Reading
- [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md), [ARCHITECTURE.md](ARCHITECTURE.md), [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for deeper background.
- [SYSTEM_AI_GUIDE.md](ai/SYSTEM_AI_GUIDE.md) for AI subsystem architecture, modes, and runtime behavior.
- [AI_LOGGING_GUIDE.md](ai_development_docs/AI_LOGGING_GUIDE.md), [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md), [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md) for focused playbooks.

---

This file is intentionally compact. For any deep explanation, examples, or historical context, always route to the human-facing documentation first, using the AI guides above to locate the right section.