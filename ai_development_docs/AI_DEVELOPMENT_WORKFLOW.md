# AI Development Workflow Guide

> **File**: `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`  
> **Purpose**: Condensed development workflow guidance for AI collaborators  
> **Style**: Pattern-first, routing-focused  

For more detailed guidance, examples, and rationale for any topic in this file, use the matching sections in `DEVELOPMENT_WORKFLOW.md`.


## Quick Reference

Use this to decide what to do next and which docs to open.

- Project overview  
  - `README.md`
- Environment setup and running the app  
  - "Environment Setup" and "Quick Start (Recommended)" in `HOW_TO_RUN.md`
- Testing  
  - `ai_development_docs/AI_TESTING_GUIDE.md` → `tests/TESTING_GUIDE.md`
- Documentation  
  - `ai_development_docs/AI_DOCUMENTATION_GUIDE.md` → `DOCUMENTATION_GUIDE.md`
- Architecture  
  - `ai_development_docs/AI_ARCHITECTURE.md` → `ARCHITECTURE.md`

Core safety and quality rules:

- Work inside `(.venv)` before running Python or tests.  
- Use `core.user_data_handlers.get_user_data()` and related helpers for user data; do not add new direct file-access wrappers.  
- Prefer module imports plus explicit usage (for example, `import core.utils` then `core.utils.validate_and_format_time()`).  
- Test incrementally after each meaningful change; route to `AI_TESTING_GUIDE.md` for patterns.  
- Record changes in `development_docs/CHANGELOG_DETAIL.md` and summarize them in `ai_development_docs/AI_CHANGELOG.md`.  
- Follow documentation rules in `AI_DOCUMENTATION_GUIDE.md` / `DOCUMENTATION_GUIDE.md` when editing docs.


## Safety First

Minimal rules for safe changes:

- Assume real user data and real machines; avoid destructive actions.  
- Treat scheduling, user data, and communication channels as high-risk areas; prefer small, reversible changes.  
- Stay inside `(.venv)` and avoid global package installs.  
- Encourage backups and frequent commits before broad edits or refactors.  
- When something looks risky or confusing:
  - Suggest pausing, capturing a short summary (what changed / what broke / what was expected),  
  - Then asking for help instead of guessing.


## Virtual Environment Best Practices

Key patterns for environment handling:

- Create .venv once: `python -m .venv .venv`.  
- Activate in each session: `.venv\\Scripts\\activate`.  
- Install dependencies: `pip install -r requirements.txt`.  
- If imports fail after a pull, suggest: `pip install -r requirements.txt --force-reinstall` inside `(.venv)`.  
- Keep changes to dependencies reflected in `requirements.txt`; avoid global installs.

For step-by-step instructions, combine this with "Environment Setup" in `HOW_TO_RUN.md` and the environment section of `DEVELOPMENT_WORKFLOW.md` when needed.



### Configuration and .env

- Configuration is driven by environment variables loaded from a `.env` file via `config.py` (python-dotenv).
- Use `.env.example` as a template: copy it to `.env` and fill in tokens, credentials, and any overrides you need.
- Key groups of settings:
  - Core paths and data roots: `BASE_DATA_DIR`, `USER_INFO_DIR_PATH`, `DEFAULT_MESSAGES_DIR_PATH`.
  - Logging: `LOGS_DIR`, component log files, and rotation settings.
  - Channels: `EMAIL_*`, `DISCORD_BOT_TOKEN`, and related flags.
  - AI / LM Studio: `LM_STUDIO_*`, `AI_*` timeouts and temperature values.
- For automated checks and reports, prefer the `config` command in `ai_development_tools/ai_tools_runner.py` (see `ai_development_tools/README.md`).

## Development Process

Use this high-level loop when reasoning about changes or suggesting steps.

### Step 1: Plan

- Capture the goal in plain language.  
- Identify risks: user data, scheduling, multi-channel behavior, or external services.  
- Decide how success will be verified (specific tests or manual flows).  
- Note which docs may need updates (for example, `HOW_TO_RUN.md`, `README.md`, specific guides).

### Step 2: Implement

- Recommend small, reversible slices rather than large rewrites.  
- Encourage use of existing helpers and patterns:
  - Data: `core.user_data_handlers.get_user_data()` and related functions.  
  - Logging / errors: follow `LOGGING_GUIDE.md` and `ERROR_HANDLING_GUIDE.md`.  
- Avoid suggesting new thin wrappers or deep, fragile imports.

### Step 3: Test

- Start with targeted tests for the changed behavior, then broaden (unit → integration → behavior → UI).  
- Route to `AI_TESTING_GUIDE.md` for commands, markers, and parallel-safety rules.  
- For Discord/email-dependent features, recommend minimal manual verification per "Manual Testing Procedures" in `tests/TESTING_GUIDE.md`.

### Step 4: Document and Clean Up

- Suggest updating `development_docs/CHANGELOG_DETAIL.md` plus a concise entry in `ai_development_docs/AI_CHANGELOG.md`.  
- Update any affected guides (for example, `HOW_TO_RUN.md`, `README.md`, or specific topic guides).  
- Remove clearly dead code, obsolete comments, and unused imports where safe.


## Testing Strategy

AI view of testing:

- Default to **incremental testing**: test each slice before moving on.  
- Prefer behavior and integration tests when deciding where to add coverage.  
- Verify side effects (messages, files, logs), not just return values.  
- Encourage parallel-safe tests and use `@pytest.mark.no_parallel` only when necessary.

Routing:

- Commands and patterns: `AI_TESTING_GUIDE.md`.  
- Explanations and manual flows: `tests/TESTING_GUIDE.md` and the testing sections of `DEVELOPMENT_WORKFLOW.md` when needed.


## Common Tasks

Patterns for frequent change types.

- **New feature**  
  - Plan user-visible behavior and side effects.  
  - Implement in small slices; add tests alongside changes.  
  - Run relevant tests and minimal manual checks.  
  - Update docs and changelogs.

- **Bug fix**  
  - Reproduce and capture logs or traces.  
  - Apply the smallest fix that clearly resolves the issue.  
  - Add or adjust tests so it cannot silently regress.  
  - Update docs if behavior changed.

- **Refactor**  
  - Preserve behavior; change structure only.  
  - Break into reversible steps and test heavily between steps.  
  - Remove obsolete wrappers/helpers and update imports and docs.


## Emergency Procedures

When things go wrong, AI guidance should be:

- Stop making additional edits; avoid compounding the problem.  
- Gather error messages, stack traces, and a brief description of what changed.  
- If available, consider restoring from a recent backup rather than experimenting blindly.  
- Suggest summarising:
  - What changed,  
  - What broke,  
  - What was expected.  
- Encourage asking for help using that summary instead of risky trial-and-error.


## Learning Resources

Routing only:

- Project-specific patterns: `DEVELOPMENT_WORKFLOW.md`, `DOCUMENTATION_GUIDE.md`, `ARCHITECTURE.md`.  
- AI behavior and constraints: `AI_SESSION_STARTER.md` and `.cursor/rules/`.  
- Testing, logging, error handling: `AI_TESTING_GUIDE.md`, `AI_LOGGING_GUIDE.md`, `AI_ERROR_HANDLING_GUIDE.md`.  
- General Python/Qt questions: external docs or tutorials (avoid fabricating URLs).


## Success Tips

Minimal coaching for AI suggestions:

- Prefer small, well-tested changes over broad, risky refactors.  
- Keep tests, docs, and changelogs aligned with actual behavior.  
- Follow existing patterns for logging, error handling, and configuration rather than inventing new ones.  
- Emphasize clarity and maintainability over cleverness in both code and tests.


## Git Workflow (PowerShell-Safe)

AI view of Git usage for this project:

- Encourage the standard cycle:
  - Check status → stage → commit → fetch → diff → pull → push.  
- Suggest safe inspection commands (for example, `git status`, `git log --oneline`, `git show`) rather than destructive operations.  
- Recommend backups before big merges or refactors and test runs after pulling significant changes.

For explicit PowerShell examples and conflict-handling steps, see "Git Workflow (PowerShell-Safe)" in `DEVELOPMENT_WORKFLOW.md`.
