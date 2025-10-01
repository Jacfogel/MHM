# Close Session Checklist

## Overview
Use this command to wrap up a session, ensure the project is healthy, and record follow-up tasks.

## Steps
1. Run the full audit suite.
   ```powershell
   python ai_development_tools/ai_tools_runner.py audit --full
   if ($LASTEXITCODE -ne 0) { Write-Host "Full audit failed" -ForegroundColor Red }
   ```
2. Review results and note any remaining issues or tests that must be revisited.
3. Update documentation and planning files, if appropriate:
   Documentation (Ensure any outstanding To-dos are noted):
   - `ai_development_docs/AI_CHANGELOG.md`
   - `development_docs/CHANGELOG_DETAIL.md`
   Planning Files:
   - `TODO.md`
   - `development_docs/PLANS.md`
4. Summarise outstanding To-dos, required follow-up testing, and deployment actions.
5. If all work is complete, request confirmation from user to add/commit/push changes.

## Response Template
- Summary of Work Completed: ...
- Audit Results: ...
- Test Results: ...
- Outstanding Actions (with owners or next steps): ...
- Documentation Updates: ...
- Git Status / Next Git Actions: ...
