# Development Tools Testing Guide

> **File**: `tests/DEVELOPMENT_TOOLS_TESTING_GUIDE.md`  
> **Audience**: Developers and AI assistants working on development tools  
> **Purpose**: Quick reference for running and understanding development tools tests  
> **Style**: Technical, concise, actionable  
> **Parent**: [TESTING_GUIDE.md](tests/TESTING_GUIDE.md)  
> This document is subordinate to [TESTING_GUIDE.md](tests/TESTING_GUIDE.md) and should be kept consistent with its standards and terminology.

This guide describes how to run and interpret the **development tools tests**.  
Use it when you change development tools behavior (analysis, reporting, CLI routing, or tool execution) or when investigating issues with the development tools infrastructure.

---

## 1. Quick Start

**Run Development Tools Tests**:
```powershell
& c:/Users/Julie/projects/MHM/MHM/.venv/Scripts/Activate.ps1
pytest tests/development_tools/
```

**Test Results Location**: Test output appears in console; logs go to `tests/logs/` if configured.

## 2. Test Suite Structure

The development tools test suite is organized into focused, maintainable modules:

- **`tests/development_tools/conftest.py`**: Shared fixtures (demo project, temp copies, config paths, module loading)
- **`tests/development_tools/test_config.py`**: Configuration validation and structure tests
- **`tests/development_tools/test_constants.py`**: Constants and exclusion pattern tests
- **`tests/development_tools/test_standard_exclusions.py`**: File exclusion logic tests
- **`tests/development_tools/test_analyze_documentation.py`**: Documentation analysis tool tests
- **`tests/development_tools/test_analyze_missing_addresses.py`**: Missing address detection tests
- **`tests/development_tools/test_analysis_tool_validation.py`**: Analysis tool validation fixture tests
- **`tests/development_tools/test_path_drift_detection.py`**: Path drift detection tests
- **`tests/development_tools/test_path_drift_integration.py`**: Path drift integration with audit workflow
- **`tests/development_tools/test_documentation_sync_checker.py`**: Documentation sync checker tests
- **`tests/development_tools/test_generate_function_registry.py`**: Function registry generation tests
- **`tests/development_tools/test_generate_module_dependencies.py`**: Module dependency analysis tests
- **`tests/development_tools/test_regenerate_coverage_metrics.py`**: Coverage regeneration tests
- **`tests/development_tools/test_legacy_reference_cleanup.py`**: Legacy reference cleanup tests
- **`tests/development_tools/test_audit_status_updates.py`**: Audit status file update behavior tests
- **`tests/development_tools/test_status_file_timing.py`**: Status file write timing verification
- **`tests/development_tools/test_output_storage_archiving.py`**: Output storage and archiving tests
- **`tests/development_tools/test_run_development_tools.py`**: CLI runner smoke tests
- **`tests/development_tools/test_integration_workflows.py`**: Integration workflow tests
- **`tests/development_tools/test_error_scenarios.py`**: Error handling and edge case tests
- **`tests/development_tools/test_supporting_tools.py`**: Supporting utility tests
- **`tests/development_tools/test_analyze_ai_work.py`**: AI work validation tests

## 3. Prerequisites

- Python virtual environment activated
- Development tools dependencies installed
- Test fixtures available at `tests/fixtures/development_tools_demo/`

## 4. Test Fixtures and Isolation

### 4.1. Synthetic Demo Project

Tests use a synthetic fixture project at `tests/fixtures/development_tools_demo/` for isolated testing. This fixture provides:

- **Demo modules** (`demo_module.py`, `demo_module2.py`) with various function types for function registry testing
- **Paired documentation files** (some synced, some mismatched) for documentation sync testing
- **Legacy code patterns** (`legacy_code.py`) for legacy cleanup testing
- **Test files** (`demo_tests.py`) for coverage runs
- **Documentation files** in `docs/` for path drift and documentation analysis testing

**Expected Test Outcomes**:
- Function registry should find all functions in `demo_module.py`
- Module dependencies should detect imports between modules
- Documentation sync should detect mismatched H2 headings
- Legacy cleanup should find legacy markers and patterns
- Coverage should generate metrics for `demo_tests.py`

### 4.2. Test Configuration

**Critical**: Development tools tests must use `test_config.json` fixture instead of the default config.

The `test_config_path` fixture (from `conftest.py`) provides a path to `tests/development_tools/test_config.json`, which:
- Does **not** exclude `tests/fixtures/` (unlike the default config)
- Allows tests to run on the demo project without being filtered out
- Maintains other standard exclusions for test isolation

**Usage Pattern**:
```python
def test_example(demo_project_root, test_config_path):
    analyzer = SomeAnalyzer(
        project_root=str(demo_project_root),
        config_path=test_config_path,  # Use test config, not default
        use_cache=False
    )
```

### 4.3. Temporary Project Copies

For destructive tests, use the `temp_project_copy` fixture which creates a temporary copy of the demo project:

```python
def test_destructive_operation(temp_project_copy):
    # temp_project_copy is a temporary directory with demo project copied
    service = AIToolsService(project_root=str(temp_project_copy))
    # ... test operations that modify files ...
```

## 5. Critical Safety Rules

### 5.1. Never Modify Real Project Files

**Overarching Principle**: Development tools tests must **never** run actual commands on the real project root in a way that affects files outside the `tests/` directory.

**Rules**:
- Tests must use `demo_project_root` or `temp_project_copy` fixtures, **never** the actual project root
- CLI smoke tests that run subprocess commands must check for audit lock files and skip during audits
- Tests that create `AIToolsService` instances must pass a fixture project root, not the real project root
- All test writes must stay under `tests/data/` or temporary directories created by fixtures

**Example Violation** (DO NOT DO THIS):
```python
# WRONG - uses real project root
service = AIToolsService(project_root=str(Path(__file__).parent.parent.parent))
service.run_audit(quick=True)  # This would write to real status files!
```

**Correct Pattern**:
```python
# CORRECT - uses fixture project
service = AIToolsService(project_root=str(temp_project_copy))
service.run_audit(quick=True)  # Writes only to temp directory
```

### 5.2. CLI Subprocess Tests

CLI smoke tests that run actual subprocess commands (like `test_status_command_exits_zero`) must:
- Check for audit lock files and skip during audits to prevent mid-audit status file writes
- Use the real project root **only** for read-only operations or when the command is guaranteed not to write files
- Prefer mocking `AIToolsService` over subprocess calls when possible (see `test_integration_workflows.py`)

**Example**:
```python
def test_status_command_exits_zero(self):
    # Check if audit is in progress - skip to prevent mid-audit writes
    lock_file = PROJECT_ROOT / "development_tools" / ".audit_in_progress.lock"
    if lock_file.exists():
        pytest.skip("Skipping status command test during audit to prevent mid-audit status file writes")
    
    # Only then run subprocess (still risky - prefer mocking)
    result = subprocess.run([...], cwd=str(PROJECT_ROOT), ...)
```

### 5.3. Test Isolation

- All test artifacts must be created under `tests/data/` or temporary directories
- Tests must clean up any temporary files they create
- Tests must not leave behind files in the real project directory structure

## 6. Portability Considerations

**Important**: The development tools are intended to be **portable** and not limited to use in the MHM project.

When writing tests:
- Avoid hardcoding MHM-specific paths or assumptions
- Use relative paths and configuration-driven paths where possible
- Test with the synthetic demo project to ensure tools work in different project structures
- Consider how tools would behave in other Python projects with different directory layouts

## 7. Test Features

- **Comprehensive coverage** (55+ tests) for core analysis tools:
  - Documentation sync validation (12 tests)
  - Function registry generation (12 tests)
  - Module dependency analysis (11 tests)
  - Legacy reference cleanup (10 tests)
  - Coverage regeneration (10 tests)
- **Fixture-based isolation** using synthetic demo project
- **Mock-based CLI tests** to avoid subprocess overhead and real file writes
- **Error scenario simulation** via monkeypatching (works identically on Windows/Linux)
- **Status file timing verification** to ensure files are only written at audit end

## 8. Running Tests

### 8.1. Run All Development Tools Tests

```bash
pytest tests/development_tools/
```

### 8.2. Run Specific Test File

```bash
pytest tests/development_tools/test_analyze_documentation.py
```

### 8.3. Run with Verbose Output

```bash
pytest -vv tests/development_tools/
```

### 8.4. Run with Coverage

```bash
pytest --cov=development_tools tests/development_tools/
```

## 9. Debugging Test Failures

1. **Check fixture availability**: Ensure `tests/fixtures/development_tools_demo/` exists and has expected structure
2. **Verify config path**: Confirm test is using `test_config_path` fixture, not default config
3. **Check project root**: Ensure test is using `demo_project_root` or `temp_project_copy`, not real project root
4. **Review logs**: Check `tests/logs/` for test execution logs
5. **Isolate failing test**: Run single test with `-vv` flag for detailed output

## 10. Known Issues and Patterns

- **Parallel execution**: Some tests use `@pytest.mark.no_parallel` for tests that modify shared resources
- **Audit lock files**: CLI tests check for `.audit_in_progress.lock` to avoid mid-audit writes
- **Module loading**: Tests use `load_development_tools_module()` helper to properly load modules with dependencies

---

**Note**: For detailed test plan information and test structure, see [TESTING_GUIDE.md](tests/TESTING_GUIDE.md), especially section 2.3 "Development tools tests" and section 3 "Fixtures, Utilities, and Safety".

