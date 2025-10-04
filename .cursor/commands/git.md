# Git Operations

## Overview
Add, commit and push changes to git.

## Steps
1. Add all changes to git.
   ```powershell
   git add .
   ```
2. Commit changes with a descriptive message.
   ```powershell
   git commit -m "Your commit message here"
   ```
3. Push changes to remote repository.
   ```powershell
   git push
   ```
4. Verify success by checking git status.
   ```powershell
   git status
   ```

## Important Notes
- **Exit Code Handling**: PowerShell's `$LASTEXITCODE` can be unreliable for git operations
- **Success Verification**: Use `git status` to confirm operations completed successfully
- **Working Tree Clean**: Final status should show "nothing to commit, working tree clean"
- **Branch Status**: Should show "Your branch is up to date with 'origin/main'"

## Response Template
- Git Status: ...
- Changes Added: ...
- Commit Message: ...
- Push Status: ...
- Next Steps: ...
