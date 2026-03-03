# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-03-03 00:20:58
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 9
**Legacy Compatibility Markers Detected**: 14

## Summary
- Scan mode only: no automated fixes were applied.
- Changelogs, archive folders, and planning documents are intentionally historical and excluded from this report.
- Legacy compatibility markers remain in 2 file(s) (4 total markers).
- Remaining counts come from legacy inventory tracking categories (7 file(s), 10 marker(s)).

## Recommended Follow-Up
- Additional guidance: [AI_LEGACY_COMPATIBILITY_GUIDE.md](ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md)
1. Identify active legacy compatibility behavior and migrate all callers/dependencies to current implementations before deleting markers.
2. Add or update regression tests that prove migrated flows work without legacy compatibility code paths. See [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) for additional guidance.
3. Only after migration is verified, remove legacy markers/comments/docs evidence and rerun `python development_tools/run_development_tools.py legacy --clean --dry-run` until this report returns zero issues.

## Legacy Compatibility Markers
**Files Affected**: 2

### development_tools\shared\service\data_loading.py
**Issues Found**: 2

- **Line 59**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY:
  ```

- **Line 651**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY:
  ```

### development_tools\tests\run_test_coverage.py
**Issues Found**: 2

- **Line 4552**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Tier3 coverage_outcome_v1 fields retained (state/counts/return_code/failed_node_ids)
  ```

- **Line 4915**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY:
  ```

## Legacy Inventory Tracking
**Files Affected**: 6

### development_tools\config\config.py
**Issues Found**: 1

- **Line 1067**: `backward compatibility`
  ```
  Checks 'fix_function_docstrings' first, then 'generate_function_docstrings' for backward compatibility."""
  ```

### development_tools\shared\mtime_cache.py
**Issues Found**: 1

- **Line 384**: `legacy path`
  ```
  # This ensures we fix standardized storage issues rather than silently using legacy paths
  ```

### development_tools\shared\service\audit_orchestration.py
**Issues Found**: 1

- **Line 1959**: `Backward compatibility`
  ```
  # Backward compatibility: retained as sum of per-tool durations
  ```

### run_tests.py
**Issues Found**: 1

- **Line 3593**: `backward compatibility`
  ```
  # Handle case where parallel_results might be a bool (backward compatibility)
  ```

### tests\test_support\test_helpers.py
**Issues Found**: 1

- **Line 5**: `backward compatibility`
  ```
  from tests.conftest (re-exported for backward compatibility).
  ```

### user\user_context.py
**Issues Found**: 2

- **Line 45**: `legacy conversion`
  ```
  # Store data in the new format directly - no legacy conversion needed
  ```

- **Line 75**: `legacy extraction`
  ```
  # Extract data and update using new functions directly - no legacy extraction needed
  ```

## Tier3 Coverage Outcome Compat Bridge
**Files Affected**: 2

### development_tools\shared\service\commands.py
**Issues Found**: 2

- **Line 1146**: `tier3_coverage_outcome_v1`
  ```
  "LEGACY COMPATIBILITY: tier3_coverage_outcome_v1 bridge exercised; "
  ```

- **Line 1151**: `legacy_state_only_payload`
  ```
  track["classification_reason"] = "legacy_state_only_payload"
  ```

### development_tools\tests\run_test_coverage.py
**Issues Found**: 1

- **Line 4552**: `LEGACY COMPATIBILITY: Tier3 coverage_outcome_v1 fields retained (state/counts/return_code/failed_node_ids)`
  ```
  # LEGACY COMPATIBILITY: Tier3 coverage_outcome_v1 fields retained (state/counts/return_code/failed_node_ids)
  ```
