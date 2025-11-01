# Run AI Functionality Tests

## Overview
Execute AI functionality tests (manual review tests) that validate AI response quality, performance, and edge cases. The AI (you) should review the results and mark them as pass, partial, or fail.

## Steps
1. Run the AI functionality tests:
   ```powershell
   python tests/ai/run_ai_functionality_tests.py
   if ($LASTEXITCODE -ne 0) { Write-Host "Some tests failed or were partial" -ForegroundColor Yellow }
   ```

2. Review the results:
   - Open `tests/ai/results/ai_functionality_test_results_latest.md`
   - Review each test result, especially those marked as PARTIAL or FAIL
   - Check the automatic validation results (meta-text, code fragments, etc.)

3. Check logs (if needed):
   - `tests/logs/test_consolidated.log` - Component logs from `mhm.*` loggers
   - `tests/logs/test_run.log` - Test execution logs from the test runner
   - Both files use consolidated logging (no individual component log files)

4. For failures or partials:
   - Identify root causes (response quality issues, unexpected content, etc.)
   - Determine if fixes are needed in the AI system or test validation
   - Update test plan or test validation rules if needed

5. Document findings:
   - Update `tests/AI_FUNCTIONALITY_TEST_PLAN.md` with status changes
   - Note any issues in the test results file

## Test Details
- **Test Type**: Manual review tests (AI reviews responses automatically, human review may be needed for complex issues)
- **Automatic Validation**: Tests automatically check for:
  - Meta-text (e.g., "Response 1:", "Mode:", test artifacts)
  - Code fragments in responses (Python imports, functions, etc.)
  - Response quality issues
- **Test Categories**: 
  - Core functionality (response generation, mode detection)
  - Integration (context, conversation history)
  - Error handling
  - Cache behavior
  - Performance metrics
  - Response quality
  - Edge cases

## Output Files
- **Results**: `tests/ai/results/ai_functionality_test_results_latest.md` (also timestamped versions, last 10 kept)
- **Logs**: `tests/logs/test_consolidated.log` (component logs), `tests/logs/test_run.log` (test execution)
- **No Individual Logs**: Component-specific log files (ai.log, app.log, etc.) are NOT created

## Response Template
#### Test Results
- Status: Passed / Partial / Failed
- Total Tests: X
- Passed: X | Partial: X | Failed: X
- Performance: Average response time Xs (if applicable)

#### Issues Found
- Test ID: Description of issue
- Root Cause: Analysis of why this occurred
- Recommendation: Suggested fix or follow-up

#### Follow-up
- Tests needing attention
- Validation rules that may need adjustment
- System improvements identified

## Additional Guidance
- See `tests/AI_FUNCTIONALITY_TEST_PLAN.md` for complete test plan and coverage
- See `tests/ai/ai_response_validator.py` for validation rules and patterns
- Deterministic tests moved to `tests/unit/test_ai_deterministic.py` (run via pytest)

