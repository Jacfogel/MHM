# Git Operations

## Overview
Add, commit and push changes to git.

## Steps
1. Add all changes to git.
   ```powershell
   git add .
   if ($LASTEXITCODE -ne 0) { Write-Host "Git add failed" -ForegroundColor Red; exit 1 }
   ```
2. Commit changes with a descriptive message.
   ```powershell
   git commit -m "Your commit message here"
   if ($LASTEXITCODE -ne 0) { Write-Host "Git commit failed" -ForegroundColor Red; exit 1 }
   ```
3. Push changes to remote repository.
   ```powershell
   git push
   if ($LASTEXITCODE -ne 0) { Write-Host "Git push failed" -ForegroundColor Red; exit 1 }
   ```

## Response Template
- Git Status: ...
- Changes Added: ...
- Commit Message: ...
- Push Status: ...
- Next Steps: ...
