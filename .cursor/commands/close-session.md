# Close Session Checklist

## Overview
Use this command to wrap up a session, ensure the project is healthy, and record follow-up tasks.

## Steps
1. Run the full audit and test suite.
   ```powershell
   python ai_development_tools/ai_tools_runner.py audit --full
   if ($LASTEXITCODE -ne 0) { Write-Host "Full audit failed" -ForegroundColor Red }

   python run_tests.py
   if ($LASTEXITCODE -ne 0) { Write-Host "Tests failed" -ForegroundColor Red }
   ```
2. Review results and note any remaining issues or tests that must be revisited.
3. Update documentation and planning files as needed:
   - `TODO.md`
   - `development_docs/PLANS.md`
   - `ai_development_docs/AI_CHANGELOG.md`
   - `development_docs/CHANGELOG_DETAIL.md`
4. Summarise outstanding To-dos, required follow-up testing, and deployment actions.
5. If all work is complete, add/commit/push changes (include the exact commands, ask the user for confirmation before pushing when appropriate).

## Response Template
- Summary of Work Completed: ...
- Audit Results: ...
- Test Results: ...
- Outstanding Actions (with owners or next steps): ...
- Documentation Updates: ...
- Git Status / Next Git Actions: ...
