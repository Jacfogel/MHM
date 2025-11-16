# Development Workflow Guide

> **File**: `DEVELOPMENT_WORKFLOW.md`  
> **Audience**: Human developer (beginner programmer)  
> **Purpose**: Safe development practices and day-to-day procedures  
> **Style**: Comprehensive, step-by-step, practical


## Quick Reference

This section summarizes the most common tasks and where to look for detail.

- Project overview and navigation  
  - See `README.md`.

- Environment setup and running the app  
  - See "Environment Setup" and "Quick Start (Recommended)" in `HOW_TO_RUN.md`.

- Running tests  
  - See `tests/TESTING_GUIDE.md` (full) and `ai_development_docs/AI_TESTING_GUIDE.md` (AI-optimized).

- Updating documentation  
  - See `DOCUMENTATION_GUIDE.md` and `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`.

- Architecture and data flow  
  - See `ARCHITECTURE.md` and `ai_development_docs/AI_ARCHITECTURE.md`.

- If you are unsure what to do next  
  - Start with "Development Process" below, then consult the relevant guide for testing, docs, or logging.


### Essential Commands (PowerShell, from repo root)

```powershell
# Create the virtual environment (once)
python -m venv venv

# Activate the virtual environment (each new shell)
venv\Scripts\activate

# Install or refresh dependencies
pip install -r requirements.txt

# Run the headless service (background core + bots)
python run_headless_service.py start

# Run the UI + service (see HOW_TO_RUN.md for details)
python run_mhm.py

# Run tests via helper script (parallel by default)
python run_tests.py

# Create a timestamped backup (simple whole-repo copy one level up)
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"; `
  Copy-Item . ../MHM_backup_$timestamp -Recurse
```

When in doubt: activate the virtual environment, make a backup, then follow the "Development Process" steps.


## Safety First

### Core Safety Rules

1. **Work inside the virtual environment**  
   - Always ensure your prompt shows `(venv)` before running Python or test commands.

2. **Back up before major edits**  
   - Use the timestamped backup command above before large refactors, cross-cutting changes, or doc rewrites.

3. **Test incrementally**  
   - After each meaningful change, run the smallest relevant test slice (unit, integration, or behavior) before moving on.

4. **Use the official data-access helpers**  
   - All user data access must go through `core.user_data_handlers.get_user_data()` and related helpers.  
   - Do not reintroduce or create new direct file-access wrappers.

5. **Keep imports consistent**  
   - Prefer module imports and explicit usage (for example, `import core.utils` then `core.utils.validate_and_format_time()`).  
   - Avoid reintroducing removed wrapper functions or deep, brittle imports.

6. **Document meaningful changes**  
   - Describe each meaningful change in `development_docs/CHANGELOG_DETAIL.md`.  
   - Ensure the summarized change appears in `ai_development_docs/AI_CHANGELOG.md`.

7. **Use the Audit-First Protocol for docs**  
   - Before editing documentation, consult `DOCUMENTATION_GUIDE.md` and follow the Audit-First instructions so automated checks remain effective.

8. **Ask for help early**  
   - When something feels risky or confusing, stop, collect a short description and errors, and ask for help instead of guessing.


### Pre-Change Checklist

Before starting significant work:

1. Confirm `(venv)` appears in the prompt. If not, run `venv\Scripts\activate`.  
2. Confirm you can start the service (for example, `python run_headless_service.py start`) without unexpected errors.  
3. Create a timestamped backup of the repo if you are changing multiple modules or refactoring core logic.  
4. Write down:
   - What you plan to change.  
   - How you will test it (specific commands).  
   - Which files you expect to touch.  
5. Identify any high-risk areas (for example, user data handling, scheduling, cross-channel behavior). If unsure, treat it as high risk.


## Virtual Environment Best Practices

### Why It Matters

- Keeps the system Python installation clean and conflict free.  
- Makes dependency management explicit through `requirements.txt`.  
- Reduces permission issues on Windows.  
- Ensures others can reproduce your environment from scratch.

### Common Commands (PowerShell)

```powershell
# Create the environment (once)
python -m venv venv

# Activate (each session)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Upgrade a package and refresh requirements
pip install some_package --upgrade
pip freeze > requirements.txt

# Deactivate when you are done
deactivate
```

### Troubleshooting

- **"python: command not found" or wrong version**  
  - Confirm Python is installed and on PATH; see `HOW_TO_RUN.md` if setup fails.

- **Import errors after pulling recent changes**  
  - Run `pip install -r requirements.txt --force-reinstall` inside `(venv)`.

- **Permission problems on Windows**  
  - Reopen PowerShell as Administrator if needed.  
  - Avoid installing packages outside the `(venv)` environment.


## Development Process

Use this as your default loop for any change: features, bug fixes, or refactors.

### Step 1: Plan

- Describe the goal in plain language.  
- Identify risks and edge cases (especially user data, scheduling, and channel-specific behavior).  
- Decide how you will verify success (specific tests or manual flows).  
- Note any documentation that might need updates (README, HOW_TO_RUN, specific guides).

### Step 2: Implement (Small Slices)

- Work in **small, testable increments**.  
- Keep functions focused; avoid reintroducing thin wrappers that just call other functions.  
- Use consistent imports and the official helpers (for example, `get_user_data()` from `core.user_data_handlers`).  
- Maintain the existing patterns for logging, error handling, and configuration (see `LOGGING_GUIDE.md` and `ERROR_HANDLING_GUIDE.md`).

### Step 3: Test

- Start with targeted tests that cover the change directly.  
- Expand outward: unit -> integration -> behavior -> UI flows.  
- Use `python run_tests.py` for broad runs, and see `tests/TESTING_GUIDE.md` for details and parallel-safe practices.  
- For features that depend on Discord or email, perform minimal manual verification as described in "Manual Testing Procedures" in `tests/TESTING_GUIDE.md`.

### Step 4: Document

- Update `development_docs/CHANGELOG_DETAIL.md` with a clear description of what changed and why.  
- Ensure `ai_development_docs/AI_CHANGELOG.md` contains a concise summary referencing the same change.  
- Update any impacted docs (for example, `HOW_TO_RUN.md`, `README.md`, or specialized guides).  
- If you introduce new patterns for testing, logging, or error handling, update the relevant guide pair (human + AI).

### Step 5: Clean Up

- Remove dead code, commented-out blocks that are no longer accurate, and unused imports.  
- Run tests one more time for safety if you touched many files.  
- Confirm Git status is clean (`git status`) and your changes are committed with a clear message.  


## Testing Strategy

### Incremental Testing

- Test after every meaningful change, even if small.  
- Start with unit-level checks, then expand to integration and behavior tests.  
- Confirm UI workflows and communication channels still behave correctly for affected features.  
- For details and commands, see "Quick Reference" and "Testing Strategy" in `tests/TESTING_GUIDE.md`.

### Test Categories

- **Unit tests** – Validate small pieces of logic in isolation.  
- **Integration tests** – Verify multiple modules working together (for example, scheduling + communication).  
- **Behavior tests** – Exercise realistic end-to-end flows (for example, a check-in through Discord).  
- **UI tests** – Focus on PySide6 dialogs, widgets, and signal/slot behavior.

For AI-optimized testing instructions and patterns, see `ai_development_docs/AI_TESTING_GUIDE.md`.


## Common Tasks

### Adding a New Feature

1. Plan the feature and consider user-facing touchpoints and side effects.  
2. Ensure `(venv)` is active and create a backup if the change is broad.  
3. Implement the feature in small, testable slices.  
4. Add or update tests to cover the new behavior.  
5. Run the relevant tests and minimal manual checks.  
6. Update documentation and changelogs.

### Fixing a Bug

1. Reproduce the bug reliably (note inputs, environment, logs).  
2. Use logs, breakpoints, or targeted prints to find the root cause.  
3. Apply the smallest change that fully resolves the issue.  
4. Add or adjust tests so the bug cannot silently return.  
5. Update documentation and changelogs if behavior changed.  

### Refactoring Code

1. Understand existing behavior before moving code.  
2. Break refactors into clear, reversible steps.  
3. Keep functions purposeful; remove redundant wrapper functions and unused helpers.  
4. Run targeted and regression tests after each step.  
5. Update imports and documentation to reflect the new structure.  
6. If you change test or logging patterns, update the associated guides.


## Emergency Procedures

### If Something Breaks Badly

1. Stop and avoid making additional edits.  
2. Capture the error message, traceback, and any logs.  
3. If needed, restore from the most recent backup you created.  
4. Describe what you changed, what broke, and what you expected to happen.  
5. Ask for help with this summary and relevant code snippets instead of guessing.

### If You Are Stuck

1. Take a short break and reset.  
2. Write down:
   - What you tried.  
   - What happened.  
   - What you expected.  
3. Formulate specific questions based on that summary.  
4. Review relevant guides (development, testing, or documentation) for patterns.  
5. If needed, ask for help and attach the summary, stack traces, and logs.


## Learning Resources

- `README.md` and project-specific guides in `development_docs/`.  
- `.cursor/rules/` and `ai_development_docs/` for AI-focused instructions and constraints.  
- Official Python resources and tutorials (for syntax and standard library questions).  
- Existing tests and modules as concrete examples of project patterns.  


## Success Tips

1. Start with small, low-risk changes to build confidence.  
2. Keep changes narrow and well-tested before expanding scope.  
3. Prefer clarity over cleverness in both code and tests.  
4. Keep documentation current when you change behavior or patterns.  
5. Use logs and error-handling patterns consistently; do not invent new ad-hoc styles.  


## Git Workflow (PowerShell-Safe)

These commands are designed to be safe defaults on Windows PowerShell.

### Basic Commands

```powershell
# See what changed
git status | Out-String

# View recent commits
git log --oneline -10 | Out-String

# Inspect a specific commit
git show <commit> | Out-String
```

### Standard Change Cycle

```powershell
# Check current status
git status | Out-String

# Stage changes
git add .

# Commit with a clear message
git commit -m "Short, specific summary"

# Fetch and review remote changes
git fetch origin
git diff --name-only HEAD..origin/main | Out-String

# Pull and push
git pull origin main
git push origin main
```

### Handling Merge Conflicts

```powershell
# See which files conflict
git status --porcelain | Out-String

# After resolving conflicts in your editor
git add .
git commit -m "Resolve merge conflicts"
git push origin main
```

Pair Git operations with the backup and testing practices described earlier, especially before large merges or rebases.
