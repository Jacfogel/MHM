# AI Development Workflow - Quick Reference

> **Purpose**: Condensed development workflow guidance for AI collaborators  
> **Style**: Pattern-first, actionable, link-heavy  
> **For details**: See [DEVELOPMENT_WORKFLOW.md](../DEVELOPMENT_WORKFLOW.md)

## Quick Reference

### Essential Commands
```powershell
venv\Scripts\activate
python run_headless_service.py start
pip install -r requirements.txt
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"; Copy-Item . ../MHM_backup_$timestamp -Recurse
```

### Decision Guide
1. Need next action? -> Follow "Development Process" steps.
2. About to touch code? -> Check "Safety First" shortcuts.
3. Running tests? -> Scan "Testing Strategy" for coverage priorities.
4. Updating docs? -> Record in both changelog files.

## Safety First

### Core Safety Rules
- Stay in the virtual environment; never install packages globally.
- Create a timestamped backup before risky edits.
- Work in small increments with tests between each change.
- Document every meaningful update in both changelog files.
- Escalate questions early with concrete context.
- Run the Audit-First tooling before producing documentation deliverables.

### Pre-Change Checklist
- Confirm `(venv)` is active; activate if missing.
- Run `python run_headless_service.py start` to confirm baseline health (for AI collaborators - launches service directly).
- Create a backup folder using the command above.
- Outline your plan, test approach, and touched files.

## Virtual Environment Best Practices

### Why It Matters
- Keeps dependencies isolated and reproducible.
- Protects against permission issues on Windows.
- Ensures collaborators share the same environment snapshot.

### Common Commands
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip freeze > requirements.txt
```

### Troubleshooting
- "Command not found" -> activate the venv.
- Import failures -> reinstall requirements with `--force-reinstall`.
- Permission problems -> relaunch PowerShell as Administrator.

## Development Process

### Step 1: Plan
- Capture the objective, risks, and validation strategy.
- Note any communication-channel behaviour that must stay intact.

### Step 2: Implement
- Ship the smallest safe slice.
- Use `get_user_data()` helpers-wrappers were removed.
- Verify behaviour after each slice.

### Step 3: Test
- Target the change, then nearby surfaces.
- Run the app via `python run_headless_service.py start` to launch the service directly and verify comms flows 

### Step 4: Document
- Update both changelog files (detailed vs summary).
- Revise any impacted guides or READMEs.
- Record new dependencies in `requirements.txt`.

## Testing Strategy

### Incremental Testing
- Test every slice immediately.
- Expand outward: unit -> integration -> behaviour/UI.

### Test Categories
- Unit, integration, behaviour, UI (PySide6), and communication channel flows.

### Tips
- Capture failing output for fast iteration.
- Leave TODOs documenting coverage gaps you find.

## Common Tasks

### Adding a New Feature
- Backup -> plan small milestones -> implement slice -> test -> document.

### Fixing a Bug
- Reproduce -> isolate -> apply targeted fix -> regression-test.

### Refactoring Code
- Understand current flow -> script the refactor steps -> execute slice by slice with tests and documentation updates.

## Emergency Procedures

### If Something Breaks Badly
- Stop changes, restore the latest backup, gather error context, escalate.

### If You Are Stuck
- Write up the goal, attempts, and blockers; ask focused questions.

## Learning Resources
- `DEVELOPMENT_WORKFLOW.md` for deep context.
- `README.md`, `ARCHITECTURE.md`, and `DOCUMENTATION_GUIDE.md` for supporting detail.
- `AI_LOGGING_GUIDE.md` for logging patterns and troubleshooting.
- `AI_TESTING_GUIDE.md` for testing patterns and procedures.
- `AI_ERROR_HANDLING_GUIDE.md` for error handling patterns and recovery.

## Success Tips
- Prefer clarity over speed.
- Keep communication specific.
- Celebrate incremental wins; note lessons in the changelog.

## Git Workflow (PowerShell-Safe)

### Avoid Terminal Freezes
- Do not run bare `git log`, `git show`, or `git diff`-they trigger pagers in PowerShell.

### Safe Alternatives
```powershell
git log --oneline -5 | Out-String
git show --name-only <commit> | Out-String
git diff --name-only HEAD..origin/main | Out-String
git status --porcelain | Out-String
```

### Standard Git Cycle
- Status -> stage -> commit -> fetch -> diff -> pull -> push.

### Handling Merge Conflicts
- Identify conflicted files, resolve manually, `git add`, commit, push.
