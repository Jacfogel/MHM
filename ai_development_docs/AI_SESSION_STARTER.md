# AI Session Starter

> **File**: `ai_development_docs/AI_SESSION_STARTER.md`
> **Audience**: AI collaborators working on the MHM codebase and docs
> **Purpose**: Provide a compact starting point for where to look and what rules to follow in a new session
> **Style**: Minimal, routing-focused, no deep explanations

> For detailed explanations, rationale, and examples, use:
> - `README.md` (project overview)
> - `HOW_TO_RUN.md` (run modes and environment details)
> - The paired human docs referenced below for deep behavior and history

## 1. Starting a Session

When you attach to MHM, do this first:

1. **Identify the user’s focus**  
   - Read the latest user message carefully.  
   - If they mention a specific file or doc, open that file first.

2. **Locate the relevant AI guide**  
   - For development work, start with `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`, especially:
     - Section 1 "Safety First"
     - Section 3 "Standard Development Cycle"
   - For documentation changes, use `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`, especially:
     - Section 3 "Documentation Synchronization Checklist"
     - Section 5 "Generated Documentation Standards"
   - For tooling or reports, use `ai_development_tools/AI_DEV_TOOLS_GUIDE.md` as the primary reference.

3. **Stay within scope**  
   - Use only the files present in the current workspace (for example, those the user has uploaded or explicitly referenced).  
   - If a needed file or report is missing, ask the user to provide it instead of guessing its contents.

4. **Confirm expectations**  
   - If the task is ambiguous (for example, "fix this" without context), ask 1–2 pointed clarification questions.  
   - Once the scope is clear, follow the relevant AI guide(s) from step 2.

## 2. Core AI References

Use these AI docs as your primary routing table; they, in turn, point to detailed human docs:

- **Development workflow** – `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`  
  - Section 1 "Safety First" – constraints and guardrails.  
  - Section 3 "Standard Development Cycle" – step-by-step development loop.

- **Architecture** – `ai_development_docs/AI_ARCHITECTURE.md`  
  - For where modules live, key services, and high-level boundaries.

- **Logging** – `ai_development_docs/AI_LOGGING_GUIDE.md`  
  - For where logs live and how to extend logging safely.

- **Testing** – `ai_development_docs/AI_TESTING_GUIDE.md`  
  - Section 4 "Test Layout and Discovery" – where tests live and how to add new ones.

- **Error handling** – `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`  
  - For how to use `MHMError` and structure error handling.

- **Development tooling** – `ai_development_tools/AI_DEV_TOOLS_GUIDE.md`  
  - Section 1 "Main Entry Point" – `ai_tools_runner.py` commands.  
  - Section 2 "Fast Mode vs Full Mode" – when to use `audit` vs `audit --full`.  
  - Section 3 "Generated Outputs" – where reports and status files live.

- **Legacy removal** – `ai_development_docs/AI_LEGACY_REMOVAL_GUIDE.md`  
  - Quick reference for using `legacy_reference_cleanup.py` and the `legacy` command.  
  - Tightly coupled with `AI_DEV_TOOLS_GUIDE.md` and the legacy reports described there.

## 3. Safe Change Rules

Follow these high-level rules whenever you propose or describe changes:

1. **Respect existing patterns**  
   - Match existing styles in logging, testing, error handling, and configuration.  
   - Prefer extending existing docs, tests, and modules over inventing new top-level structures.

2. **Keep AI vs human docs aligned**  
   - For paired docs, H2 headings must match as a set (see section 3 "Documentation Synchronization Checklist" in `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`).  
   - AI docs summarize and route; human docs contain detailed explanations.

3. **Avoid partial or speculative edits**  
   - Do not describe or "fix" modules you cannot see.  
   - If a function or behavior is unclear, ask for the relevant file or an example before rewriting it.

4. **Tie changes to tests and tools**  
   - When you propose code changes, also point to where tests should be added or updated (see `ai_development_docs/AI_TESTING_GUIDE.md`).  
   - Where appropriate, suggest re-running:
     - `python ai_development_tools/ai_tools_runner.py audit`  
     - `python ai_development_tools/ai_tools_runner.py status`  
     - `python ai_development_tools/ai_tools_runner.py legacy` (for legacy-related work).

## 4. Typical Tasks and Where to Look

Use this as a routing table for common request types.

### 4.1. "Help me edit documentation"

- Start with `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`, sections:
  - 3 "Documentation Synchronization Checklist"  
  - 4 "Maintenance Guidelines"  
- Then open the relevant human doc (for example, `DOCUMENTATION_GUIDE.md`, `LOGGING_GUIDE.md`, `TESTING_GUIDE.md`).  
- Keep AI docs short; push detailed narrative into the human docs.

### 4.2. "Help me refactor or clean up code"

- Start with `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`, especially section 1 "Safety First" and section 3 "Standard Development Cycle".  
- Use `ai_development_tools/AI_DEV_TOOLS_GUIDE.md` for commands to run audits and checks.  
- For legacy-related refactors, also use `ai_development_docs/AI_LEGACY_REMOVAL_GUIDE.md` and the legacy tools described there.

### 4.3. "Help me understand the system"

- Use `ai_development_docs/AI_ARCHITECTURE.md` as the primary overview.  
- Use `README.md` and `HOW_TO_RUN.md` for a human-readable overview of goals and run modes.  
- For channel-specific behavior (Discord, email, etc.), look for channel guides under `communication/communication_channels/`.

---

This file is intentionally compact. For any deep explanation, examples, or historical context, always route to the human-facing documentation first, using the AI guides above to locate the right section.
