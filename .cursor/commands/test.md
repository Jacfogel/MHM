# Run Tests

## Overview
Execute the full test suite, maintain isolation, and report outcomes.

## Steps
1. Run tests:
   ```powershell
   python run_tests.py
   if ($LASTEXITCODE -ne 0) { Write-Host "Tests failed" -ForegroundColor Red; exit 1 }
   ```
2. For failures:
   - Capture failing output.
   - Categorize (flaky/new/regression).
   - Consult `ai_development_docs/AI_TESTING_GUIDE.md` and `tests/TESTING_GUIDE.md`.
3. Confirm no files were written outside `tests/`.
4. Document fixes and rerun as needed.

## Additional Guidance
- `ai_development_docs/AI_REFERENCE.md` for troubleshooting patterns.
- `tests/MANUAL_TESTING_GUIDE.md` for UI walkthroughs when behaviour changes.
- `development_docs/TEST_COVERAGE_EXPANSION_PLAN.md` when planning coverage improvements.
- **AI Functionality Tests**: Run `python tests/ai/run_ai_functionality_tests.py` for manual review tests of AI response quality. See `.cursor/commands/ai-functionality-tests.md` for detailed workflow.

## Response Template
#### Test Results
- Status: Passed / Failed
- Totals (Passed/Failed/Skipped): ...

#### Failures (if any)
- Test: ...
- Root Cause: ...
- Fix Applied: ...

#### Follow-up
- Remaining tasks / additional tests.
