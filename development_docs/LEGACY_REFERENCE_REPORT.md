# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-04-04 15:19:52
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 3
**Legacy Compatibility Markers Detected**: 6

## Summary
- Scan mode only: no automated fixes were applied.
- Changelogs, archive folders, and planning documents are intentionally historical and excluded from this report.
- Legacy compatibility markers remain in 3 file(s) (5 total markers).

## Recommended Follow-Up
- Additional guidance: [AI_LEGACY_COMPATIBILITY_GUIDE.md](ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md)
1. Identify active legacy compatibility behavior and migrate all callers/dependencies to current implementations before deleting markers.
2. Add or update regression tests that prove migrated flows work without legacy compatibility code paths. See [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) for additional guidance.
3. Only after migration is verified, remove legacy markers/comments/docs evidence and rerun `python development_tools/run_development_tools.py legacy --clean --dry-run` until this report returns zero issues.

## Deprecation Inventory
- Inventory file: `development_tools/config/jsons/DEPRECATION_INVENTORY.json`
- Active/candidate entries: 1
- Removed entries: 3
- Active search terms: 0
- Current inventory-term hits in scan: 0 file(s), 0 marker(s)

## Legacy Compatibility Markers
**Files Affected**: 3

### development_tools\reports\analyze_system_signals.py
**Issues Found**: 1

- **Line 80**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: pre-scopes aggregate path (V5 Section 7.16).
  ```

### development_tools\shared\fix_project_cleanup.py
**Issues Found**: 1

- **Line 245**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: flat paths before scopes migration (still read by some fallbacks).
  ```

### development_tools\shared\service\audit_orchestration.py
**Issues Found**: 3

- **Line 1524**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: unscoped aggregate (V5 Section 7.16).
  ```

- **Line 1645**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: unscoped aggregate (V5 Section 7.16).
  ```

- **Line 2075**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: pre-scopes reports/jsons/tool_timings.json (see V5 Section 7.16).
  ```

## Legacy Inventory Tracking
**Files Affected**: 1

### development_tools\reports\analyze_system_signals.py
**Issues Found**: 1

- **Line 150**: `legacy path`
  ```
  # Check for recent audit and calculate freshness (scoped + legacy paths)
  ```
