# Run Tests and Handle Failures

## Overview
Execute the full test suite, investigate failures, and record follow-up actions.

## Steps
1. Run the complete test suite.
   ```powershell
   python run_tests.py
   if ($LASTEXITCODE -ne 0) { Write-Host "Tests failed" -ForegroundColor Red; exit 1 }
   ```
2. For failing runs, capture output, categorise the failures (flaky, broken, new), and re-run targeted tests as needed.
3. Confirm that no artefacts are written outside the test data directories.
4. Update documentation and changelogs when fixes land (`development_docs/CHANGELOG_DETAIL.md`, `ai_development_docs/AI_CHANGELOG.md`).

Consult `ai_development_docs/AI_REFERENCE.md` and the testing guidance in `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md` for troubleshooting patterns.

## Response Template
#### Test Results
- Status: ...
- Total / Passed / Failed / Skipped: ...

#### Failures
- ...

#### Fixes Applied
- ...

#### Follow-up
- Outstanding Work: ...
- Additional Tests Needed: ...
