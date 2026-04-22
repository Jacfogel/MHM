# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-04-21 20:35:21
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 2
**Legacy Compatibility Markers Detected**: 2

## Summary
- Scan mode only: no automated fixes were applied.
- Changelogs, archive folders, and planning documents are intentionally historical and excluded from this report.

## Recommended Follow-Up
- Additional guidance: [AI_LEGACY_COMPATIBILITY_GUIDE.md](ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md)
1. Identify active legacy compatibility behavior and migrate all callers/dependencies to current implementations before deleting markers.
2. Add or update regression tests that prove migrated flows work without legacy compatibility code paths. See [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) for additional guidance.
3. Only after migration is verified, remove legacy markers/comments/docs evidence and rerun `python development_tools/run_development_tools.py legacy --clean --dry-run` until this report returns zero issues.

## Deprecation Inventory
- Inventory file: `development_tools/config/jsons/DEPRECATION_INVENTORY.json`
- Active/candidate entries: 1
- Removed entries: 9
- Active search terms: 0
- Current inventory-term hits in scan: 0 file(s), 0 marker(s)

## Legacy Inventory Tracking
**Files Affected**: 2

### development_tools\tests\domain_mapper.py
**Issues Found**: 1

- **Line 394**: `legacy path`
  ```
  callers can use legacy path-based / keyword inference.
  ```

### development_tools\tests\test_file_coverage_cache.py
**Issues Found**: 1

- **Line 1047**: `legacy path`
  ```
  uses the legacy path: test directory layout, then ``infer_domains_from_test_path`` when
  ```
