# Development Workflow Guide

> **Audience**: Human developer (beginner programmer)  
> **Purpose**: Safe development practices and day-to-day procedures  
> **Style**: Comprehensive, step-by-step, supportive

> **See [README.md](README.md) for complete navigation and project overview**  
> **See [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md) for AI-optimized quick reference**

## Quick Reference

### Essential Commands
```powershell
# Activate environment
venv\Scripts\activate

# Run the application
python run_mhm.py

# Create a timestamped backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item -Path "." -Destination "../MHM_backup_$timestamp" -Recurse

# Install dependencies
pip install -r requirements.txt
```

### Decision Guide
1. **Planning the next step?** Review the "Development Process" section.
2. **About to code?** Walk through "Safety First" and the pre-change checklist.
3. **Need to test?** Follow the "Testing Strategy" section.
4. **Writing documentation?** Update both changelog files and any affected guides.
5. **Feeling stuck?** Check "Emergency Procedures" and ask for help early.

## Safety First

### Core Safety Rules
1. **Work inside the virtual environment** to avoid polluting the global Python install.
2. **Create a backup before major edits** using the PowerShell command above.
3. **Test incrementally** after each small change to catch regressions early.
4. **Document every meaningful change** in `development_docs/CHANGELOG_DETAIL.md` and summarise it in `ai_development_docs/AI_CHANGELOG.md`.
5. **Ask questions early** with concrete examples of what is confusing.
6. **Use the Audit-First Protocol** before producing documentation so automated quality checks guide your updates.

### Pre-Change Checklist
1. Confirm the virtual environment prompt shows `(venv)`. If not, run `venv\Scripts\activate`.
2. Run `python run_mhm.py` to make sure the current state is healthy (launches UI only - background service started separately).
3. Create a timestamped backup of the repository.
4. Outline what you plan to change, how you'll test it, and which files might be affected.

## Virtual Environment Best Practices

### Why It Matters
- Keeps the system Python installation clean and conflict free.
- Makes dependency management explicit through `requirements.txt`.
- Avoids permission issues on Windows.
- Ensures collaborators can reproduce the environment exactly.

### Common Commands
```powershell
# Create the environment (once)
python -m venv venv

# Activate the environment (each session)
venv\Scripts\activate

# Install dependencies after activation
pip install -r requirements.txt

# Add a new dependency
pip install package_name
pip freeze > requirements.txt

# Leave the environment
deactivate
```

### Troubleshooting
- **Command not found**: Make sure `(venv)` appears in the prompt.
- **Import errors**: Reinstall requirements with `pip install -r requirements.txt --force-reinstall`.
- **Permission issues**: Reopen PowerShell as Administrator or adjust execution policy.

## Development Process

### Step 1: Plan
- Define the goal in plain language.
- Identify risks and edge cases.
- Decide how you will verify success.
- Note any user communication requirements.

### Step 2: Implement
- Work in the smallest safe increments.
- Run quick tests after each change.
- Confirm user-facing features continue to work through every communication channel.
- Keep functions focused and remove unnecessary wrappers.
- All user data access must go through `get_user_data()` and related helpers.

### Step 3: Test
- Test the feature you just touched.
- Exercise related areas that might be impacted.
- Run `python run_mhm.py` to launch the admin UI and verify communication flows, especially Discord. Note: The background service must be started manually.

### Step 4: Document
- Record the change in `development_docs/CHANGELOG_DETAIL.md`.
- Add a concise summary to `ai_development_docs/AI_CHANGELOG.md`.
- Update any affected guides and note new dependencies.

## Testing Strategy

### Incremental Testing
- Test after every meaningful change.
- Start with unit-level checks, then integration, then behavior.
- Confirm UI workflows, communication channels, and scheduler tasks.

### Test Categories
- **Unit tests**: Individual functions and small modules.
- **Integration tests**: Multiple components working together.
- **Behavior tests**: End-to-end scenarios mirroring real usage.
- **UI tests**: PySide6 dialogs and widgets.

### Tips
- Use `print()` or logging when debugging.
- Rerun failing tests immediately to confirm fixes.
- Keep notes on test coverage gaps you notice.

## Common Tasks

### Adding a New Feature
1. Plan the feature and consider user touchpoints.
2. Back up the project and ensure `(venv)` is active.
3. Implement in small, testable slices.
4. Test after each slice and at the end-to-end level.
5. Document the new behavior and any configuration changes.

### Fixing a Bug
1. Reproduce the bug reliably.
2. Trace the root cause using logs, breakpoints, or print statements.
3. Apply the smallest fix that solves the issue.
4. Test the fix plus nearby functionality.
5. Update documentation to describe the resolution.

### Refactoring Code
1. Understand the existing behavior before moving code.
2. Break refactorings into clear, reversible steps.
3. Keep functions purposeful-remove redundant wrappers.
4. Run targeted and regression tests after each step.
5. Update imports, references, and docs to match the new structure.

## Emergency Procedures

### If Something Breaks Badly
1. Pause and avoid making additional changes.
2. Restore the backup you created before starting.
3. Capture errors or stack traces for later analysis.
4. Ask for help with a brief summary and the error output.

### If You Are Stuck
1. Take a short break and reset.
2. Write down what you know, what you tried, and what failed.
3. Formulate a specific question with context and code snippets.
4. Explore an alternate approach or pair with another developer.

## Learning Resources

- [Python Official Tutorial](https://docs.python.org/3/tutorial/)
- [Real Python](https://realpython.com/)
- Project documentation in `development_docs/` and `.cursor/rules/`
- Team meeting notes or prior changelog entries for historical context

## Success Tips

1. Start with small improvements to build confidence.
2. Test often to catch regressions early.
3. Keep communication open and questions specific.
4. Celebrate progress and document lessons learned.
5. Be patient-steady progress matters more than speed.

## Git Workflow (PowerShell-Safe)

### Avoid Terminal Freezes
Do **not** run bare `git log`, `git show`, or `git diff` commands in PowerShell-they invoke a pager that hangs the terminal.

### Safe Alternatives
```powershell
# View recent commits
git log --oneline -5 | Out-String

# Show a commit summary
git show --name-only <commit> | Out-String

# Compare with remote
git diff --name-only HEAD..origin/main | Out-String

# Check current status
git status --porcelain | Out-String
```

### Standard Git Cycle
```powershell
# 1. Review current changes
git status --porcelain | Out-String

# 2. Stage updates
git add .

# 3. Commit with a descriptive message
git commit -m "Describe the change"

# 4. Pull remote updates
git fetch origin
git diff --name-only HEAD..origin/main | Out-String
git pull origin main

# 5. Push your work
git push origin main
```

### Handling Merge Conflicts
```powershell
# Identify conflicting files
git status --porcelain | Out-String

# After resolving conflicts
git add .
git commit -m "Resolve merge conflicts"
git push origin main
```

Always pair Git operations with the backup and testing practices described earlier to keep the repository healthy.
