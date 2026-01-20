# AI Development Workflow Guide

> **File**: `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`  
> **Pair**: [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)
> **Audience**: AI collaborators and tools
> **Purpose**: Route AI assistance to the right docs and safe workflows
> **Style**: Minimal, routing-first
> For detailed behavior and rationale, use the matching sections in DEVELOPMENT_WORKFLOW.md.
> Keep this file's H2 headings in lockstep with DEVELOPMENT_WORKFLOW.md whenever you change the structure.


---

## Quick Reference

- Purpose of this doc:
  - Route AI tools to the right human docs, sections, and commands.
  - Enforce safe patterns for making and testing changes.
- Always prefer:
  - Human workflow doc: [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) (full detail).
  - This AI doc: high-level routing and constraints.
- When you need more detail, jump to:
  - Running the app and environment commands:
    - [HOW_TO_RUN.md](HOW_TO_RUN.md), section 1. "Quick Start (Recommended)" and section 4. "Alternative Launch Methods".
    - [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md), section 2. "Virtual Environment Best Practices".
    - [ARCHITECTURE.md](ARCHITECTURE.md), section 4. "Key Modules and Responsibilities" (entry points).
  - Testing:
    - [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) (routing for which tests to run and which commands to use).
  - Logging:
    - [AI_LOGGING_GUIDE.md](ai_development_docs/AI_LOGGING_GUIDE.md) (routing for logging patterns and component log usage).
  - Error handling:
    - [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md) (routing for error categories and handling patterns).
  - Documentation:
    - [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md) (routing for documentation categories and sync rules).
  - Architecture and responsibilities:
    - [AI_ARCHITECTURE.md](ai_development_docs/AI_ARCHITECTURE.md) (routing for key modules, responsibilities, and patterns).
- Data and configuration rules:
  - Use `core.user_data_handlers.get_user_data()` and related helpers for user data access; do not invent new direct file-access wrappers.
  - Use `.env` and `core/config.py` for configuration; do not add ad hoc `os.getenv` calls outside the established patterns.

---

## 1. Safety First

- **Datetime rules**  
  Use only helpers from `core/time_utilities.py` for current time, formatting, or parsing.
  Do not introduce `datetime.now()`, `strftime()`, or `strptime()` in other modules.

- Default assumptions:
  - The user is working on the `main` branch unless they say otherwise.
  - The virtual environment is `.venv` in the project root.
- When giving instructions:
  - Prefer small, reversible changes instead of broad refactors.
  - Do not invent new entry points; use the ones documented in:
    - [HOW_TO_RUN.md](HOW_TO_RUN.md), section 1.5. "Step 5: Launch the Application" and section 4. "Alternative Launch Methods".
    - [ARCHITECTURE.md](ARCHITECTURE.md), section 4. "Key Modules and Responsibilities" (run_mhm/run_headless).
- For crashes, confusing errors, or suspected configuration issues, route to:
  - [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md), section 6. "Emergency Procedures".
  - [HOW_TO_RUN.md](HOW_TO_RUN.md), section 6. "Troubleshooting".
  - [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md).
  - [AI_LOGGING_GUIDE.md](ai_development_docs/AI_LOGGING_GUIDE.md).
- For the full safety checklist, see section 1. "Safety First" in [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md).

---

## 2. Virtual Environment Best Practices

- Assume a standard virtual environment named `.venv` in the project root.
- When the user asks how to create or activate the environment, point them to [HOW_TO_RUN.md](HOW_TO_RUN.md), especially:
  - section 1, "Quick Start (Recommended)" for setup and activation commands.
  - troubleshooting sections if activation fails or Python is not on PATH.
- Do not invent alternative virtual environment layouts (different folder names, global installs, etc.) unless the user explicitly tells you they are using something else.
- If imports fail or dependencies look broken:
  - Suggest reinstalling dependencies inside the active `.venv` with `pip install -r requirements.txt`.
  - Point them back to HOW_TO_RUN.md for deeper troubleshooting steps.

## 3. Development Process

Use the same high-level loop as the human development workflow, but keep answers short and routing-focused:

- Plan the change.
- Implement in small, reviewable slices.
- Test (automated + minimal manual verification).
- Document and clean up.

When planning:

- Ask which parts of the system are affected (UI, core, bots, tests, docs).
- Route yourself or the user to:
  - [AI_ARCHITECTURE.md](ai_development_docs/AI_ARCHITECTURE.md) for where new logic should live and how components interact.
  - [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) for where tests should go and which kinds of tests to add.
  - [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md) for which docs must be updated and how to keep pairs in sync.

When implementing:

- Prefer small, reversible changes instead of broad refactors.
- Use existing helpers and patterns:
  - Data access: functions in `core/user_data_handlers.py`.
  - Configuration: `core/config.py` and `.env` values, not ad hoc `os.getenv` calls.
  - Logging: patterns described in [AI_LOGGING_GUIDE.md](ai_development_docs/AI_LOGGING_GUIDE.md).
  - Error handling: patterns described in [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md).
- Preserve existing comments and structure unless a human doc explicitly says to remove or replace something.
- Do not invent new global patterns for logging, configuration, or data access; reuse the existing ones.

When documenting:

- Decide which docs to update using [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md).
- Keep H2 headings aligned across doc pairs as described in [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md), section 3. "Documentation Synchronization Checklist".
## 4. Testing Strategy

- Always propose tests when suggesting code changes.
- For where and how to write tests, route to:
  - [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) for routing and quick commands.
- Default commands you may recommend:
  - Targeted module or test-file runs only if they match patterns described in the human testing guide.
- For deeper AI-specific testing patterns, route the tool to [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) instead of re-explaining them here.

---

## 5. Common Tasks

Use these patterns for frequent change types. Keep responses concise and route to the right AI docs for details.

**New feature**

- Clarify the user-visible behavior and which channels or components are involved.
- Propose small, incremental changes rather than a large, all-at-once implementation.
- Recommend tests to add or update, using [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) to choose scope and commands.
- Identify which docs should be updated (for example, `README.md`, `HOW_TO_RUN.md`, or a guide) using [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md).

**Bug fix**

- Ask how the bug reproduces and whether there are relevant logs.
- Suggest checking component logs using patterns from [AI_LOGGING_GUIDE.md](ai_development_docs/AI_LOGGING_GUIDE.md).
- Recommend the smallest change that clearly fixes the issue.
- Ensure tests cover the bug going forward, guided by [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md).

**Refactor**

- Keep behavior the same while improving structure or clarity.
- Use [AI_ARCHITECTURE.md](ai_development_docs/AI_ARCHITECTURE.md) to confirm that responsibilities are in the right modules.
- Encourage running the relevant tests (see [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md)) after each significant step.
- Remind the user to update or confirm docs where behavior, naming, or public interfaces have changed.

When the user asks high-level questions like:

- "How do I run the app or service?"
- "Where should this new logic live?"
- "How do I log this?"
- "How should I handle this error?"
- "What docs should I update?"

answer briefly and route to the appropriate AI doc:

- Running and environment: AI_DEVELOPMENT_WORKFLOW.md (this doc) plus [HOW_TO_RUN.md](HOW_TO_RUN.md) for commands.
- Placement and responsibilities: [AI_ARCHITECTURE.md](ai_development_docs/AI_ARCHITECTURE.md).
- Logging: [AI_LOGGING_GUIDE.md](ai_development_docs/AI_LOGGING_GUIDE.md).
- Error handling: [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md).
- Documentation: [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md).

## 6. Emergency Procedures

When things look broken or confusing:

- For environment or startup failures:
  - [HOW_TO_RUN.md](HOW_TO_RUN.md), section 6. "Troubleshooting".
  - [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md), section 2. "Virtual Environment Best Practices".
- For unexpected tracebacks, crashes, or repeated errors:
  - [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md).
  - [AI_LOGGING_GUIDE.md](ai_development_docs/AI_LOGGING_GUIDE.md).
- For failing or flaky tests:
  - [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md).
  - [TESTING_GUIDE.md](tests/TESTING_GUIDE.md), section 7. "Debugging and Troubleshooting".
- For documentation that appears inconsistent with behavior:
  - [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md).
  - [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md), section 4. "Documentation Synchronization Checklist".
- For the full emergency checklist, see section 6. "Emergency Procedures" in [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md).

---

## 7. Learning Resources

- Beginners should be pointed to:
  - [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md), section 7. "Learning Resources".
- For deeper understanding of structure and data flow:
  - [ARCHITECTURE.md](ARCHITECTURE.md), section 1. "Directory Overview" and section 2. "User Data Model".
  - [AI_ARCHITECTURE.md](ai_development_docs/AI_ARCHITECTURE.md) for quick routing.
- For learning about testing, logging, and error handling:
  - [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md), [AI_LOGGING_GUIDE.md](ai_development_docs/AI_LOGGING_GUIDE.md), and [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md) for routing.

Keep guidance brief and always route to the human docs for long explanations.

---

## 8. Success Tips

- Always:
  - Use existing helpers for data, configuration, logging, and error handling.
  - Keep changes small and easy to review.
- Never:
  - Invent new file layouts, entry points, or global patterns that are not already documented.
  - Duplicate large sections of human docs inside AI docs; instead, point back to the correct section.

For a fuller list of tips and examples, see section 8. "Success Tips" in [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md).

---

## 9. Git Workflow (PowerShell-Safe)

- Git guidance should be aligned with section 9. "Git Workflow (PowerShell-Safe)" in [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md).
- High-level rules for AI assistance:
  - Do not suggest complex branching strategies unless the user asks; default to simple `main`-based workflows.
  - Prefer commands that are safe in PowerShell on Windows.
  - Encourage small, frequent commits with clear messages summarizing the change.
- When users need more detailed Git instructions, always route them back to [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md), section 9, instead of inventing new workflows here.

---

## 10. Standard Audit Recipe

When to run AI development tools for codebase analysis and health checks:

- **Quick health check / pre-commit**: Run `python development_tools/run_development_tools.py audit --quick` (Tier 1, ~30-60s) for core metrics: function discovery, documentation sync status, system signals, and quick status snapshot.

- **Day-to-day checks**: Run `python development_tools/run_development_tools.py audit` (Tier 2, default, ~2-5min) for standard quality checks. Includes everything in Tier 1 plus: documentation analysis, error handling coverage, decision support insights, config validation, and AI work validation.

- **Pre-merge / pre-release checks**: Run `python development_tools/run_development_tools.py audit --full` (Tier 3, ~10-30min) for comprehensive analysis. Includes everything in Tier 1 & 2 plus: full test coverage regeneration, unused import detection, legacy reference scanning, module dependency analysis, and improvement opportunity reports (LEGACY_REFERENCE_REPORT.md, TEST_COVERAGE_EXPANSION_PLAN.md, UNUSED_IMPORTS_REPORT.md).

- **Documentation work**: 
  - Run `python development_tools/run_development_tools.py doc-sync` to check documentation pairing and path drift.
  - Run `python development_tools/run_development_tools.py docs` to regenerate static reference documentation (FUNCTION_REGISTRY, MODULE_DEPENDENCIES, DIRECTORY_TREE). Note: These are informational docs that don't change frequently; audits validate their accuracy but don't regenerate them.

- **Quick status snapshot**: Run `python development_tools/run_development_tools.py status` to view cached summaries from the most recent audit (rerun `audit` if cache is stale).

**Note**: All three audit tiers update the same output files (AI_STATUS.md, AI_PRIORITIES.md, consolidated_report.txt, analysis_detailed_results.json). Each tier encompasses all functionality of lighter tiers, so Tier 2 includes all Tier 1 tools, and Tier 3 includes all Tier 1 & 2 tools.

For detailed tool usage and output locations, see [AI_DEVELOPMENT_TOOLS_GUIDE.md](development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md).
