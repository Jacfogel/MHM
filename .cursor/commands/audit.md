# Run Fast Audit


> **File**: `.cursor/commands/audit.md`
## Overview
Refresh code health metrics without running coverage or heavy hygiene checks.

## Steps
1. Execute the fast audit:
   ```powershell
   python -m development_tools.run_development_tools audit
   if ($LASTEXITCODE -ne 0) { Write-Host "Audit failed" -ForegroundColor Red; exit 1 }
   ```
2. Review updated artifacts:
   - `development_tools/AI_STATUS.md`
   - `development_tools/AI_PRIORITIES.md`
   - `development_tools/consolidated_report.txt`
3. Check documentation sync status (paired docs, path drift, ASCII compliance, heading numbering) in the audit output.
4. Share key metrics with the user (totals, warnings, documentation coverage) and confirm whether they want to proceed with follow-up work.
5. Capture highlights and blockers; link to source docs for detail.
6. Recommend immediate follow-up actions (tests, refactors, doc updates).

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
