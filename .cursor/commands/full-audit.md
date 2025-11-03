# Run Full Audit

## Overview
Regenerate complete health metrics, including coverage, legacy scans, and unused-import reports.

## Steps
1. Execute the full audit:
   ```powershell
   python -m ai_development_tools.ai_tools_runner audit --full
   if ($LASTEXITCODE -ne 0) { Write-Host "Full audit failed" -ForegroundColor Red; exit 1 }
   ```
2. Review outputs (includes fast audit artifacts plus):
   - `development_docs/LEGACY_REFERENCE_REPORT.md`
   - `development_docs/UNUSED_IMPORTS_REPORT.md`
   - Updated coverage reports
3. Present key metrics and findings to the user (coverage deltas, unused imports, legacy hits) and confirm next steps together.
4. Summarize critical issues, explicit blockers, and legacy follow-up.
5. Propose a prioritized plan (tests, cleanup, refactors).

## Response Template
#### System Overview
- Total Functions / Complexity: ...
- Coverage Status: ...
- Legacy References: ...
- Unused Imports: ...

#### Critical Issues
- ...

#### Immediate Actions
1. ...
2. ...
3. ...

#### Follow-up
- Next audit cadence / monitoring notes.
