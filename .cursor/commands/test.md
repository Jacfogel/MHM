# Run All Tests and Fix Failures

## Overview
Execute the full MHM test suite and systematically fix any failures, ensuring code quality and functionality.

## Instructions for AI Assistant

### 1. **Execute Test Suite**
Run the full test suite using PowerShell syntax:
```powershell
# Run full test suite
python run_tests.py

# Check exit code
if ($LASTEXITCODE -ne 0) { Write-Host "Tests failed" -ForegroundColor Red }
```

### 2. **Analyze Test Results**
- Capture output and identify failures
- Categorize by type: flaky, broken, new failures
- Prioritize fixes based on impact
- Check if failures are related to recent changes
- Identify patterns in failures

### 3. **Fix Issues Systematically**
- Start with the most critical failures
- Fix one issue at a time
- Re-run tests after each fix: `python run_tests.py`
- Ensure no regressions are introduced

## MHM-Specific Considerations

### Test Environment
- Ensure virtual environment is activated
- Check that test data directories are properly isolated
- Verify no test pollution in real data directories
- Use PowerShell syntax for all commands

### Common MHM Test Issues
- **User Data Pollution**: Tests creating files in real user directories
- **Path Issues**: Hardcoded paths instead of test-specific paths
- **Logging Conflicts**: Multiple tests interfering with logging
- **Async Issues**: Discord/Email bot test cleanup
- **File Locking**: Windows file locking during tests

### Fixing Strategy
1. **Isolate the problem** - Run specific test to identify issue
2. **Check test fixtures** - Ensure proper setup/teardown
3. **Fix incrementally** - One test at a time
4. **Verify isolation** - Ensure no side effects
5. **Update documentation** - Document any test changes

### PowerShell Commands
```powershell
# Run full test suite
python run_tests.py

# Check exit code
if ($LASTEXITCODE -ne 0) { Write-Host "Tests failed" -ForegroundColor Red }

# Run specific test file
python -m pytest tests/specific_test_file.py -v

# Run with coverage
python -m pytest --cov=core tests/ -v
```

### 4. **Provide Structured Test Report**
**ALWAYS provide this format in your response:**

#### **🧪 Test Results**
- Test Status: [All Passed/Failed/Partial]
- Total Tests: [number]
- Passed: [number]
- Failed: [number]
- Skipped: [number]

#### **🚨 Test Failures (if any)**
- [List specific test failures]
- [Include error messages and file paths]
- [Categorize by type: flaky, broken, new]

#### **🔧 Fixes Applied**
- [List fixes made]
- [Include specific changes]
- [Note any regressions introduced]

#### **✅ Final Status**
- All Tests: [Passed/Failed]
- Test Pollution: [None/Issues found]
- Coverage: [Meets standards/Needs improvement]
- Reliability: [Stable/Issues found]

## Success Criteria
- All tests pass: `python run_tests.py`
- No test pollution in real data directories
- Test output is clean and informative
- Coverage meets project standards
- Tests are deterministic and reliable

## Documentation Updates
- Update CHANGELOG_DETAIL.md with test fixes
- Update AI_CHANGELOG.md with brief summary
- Document any new test patterns or utilities
- Ensure test documentation is current
