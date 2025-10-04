# Run Tests and Handle Failures

## Overview
Execute the full test suite, investigate failures and fix any failing tests.

## Steps
1. Run the complete test suite.
   ```powershell
   python run_tests.py
   if ($LASTEXITCODE -ne 0) { Write-Host "Tests failed" -ForegroundColor Red; exit 1 }
   ```
2. For failing runs, capture output, categorise the failures (flaky, broken, new), consult `tests/TESTING_GUIDE.md` and fix any failing tests.
3. Confirm that no artefacts are written outside the test data directories.

## Additional Guidance
- **Testing Guide**: `ai_development_docs/AI_TESTING_GUIDE.md` - Fast testing patterns and troubleshooting
- **Test Strategy**: `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md` - Testing patterns and incremental testing
- **Troubleshooting**: `ai_development_docs/AI_REFERENCE.md` - Common test failure patterns and solutions
- **Manual Testing**: `tests/MANUAL_TESTING_GUIDE.md` - UI testing procedures and checklists
- **Test Coverage**: `development_docs/TEST_COVERAGE_EXPANSION_PLAN.md` - Coverage improvement strategies

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
