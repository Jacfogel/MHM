# Run Fast Audit


> **File**: `.cursor/commands/audit.md`
## Overview
Refresh code health metrics without running coverage or heavy hygiene checks.

## Steps
1. Execute the fast audit:
   ```powershell
   python -m ai_development_tools.ai_tools_runner audit
   if ($LASTEXITCODE -ne 0) { Write-Host "Audit failed" -ForegroundColor Red; exit 1 }
   ```
2. Review updated artifacts:
   - `ai_development_tools/AI_STATUS.md`
   - `ai_development_tools/AI_PRIORITIES.md`
   - `ai_development_tools/consolidated_report.txt`
3. Share key metrics with the user (totals, warnings, documentation coverage) and confirm whether they want to proceed with follow-up work.
4. Capture highlights and blockers; link to source docs for detail.
5. Recommend immediate follow-up actions (tests, refactors, doc updates).

## Response Template
#### Audit Highlights
- System Health: ...
- Key Warnings: ...
- Documentation / Error Handling: ...

#### Recommended Actions
1. ...
2. ...
3. ...

#### Notes
- If coverage or unused import data looks stale, schedule `/full-audit`.
