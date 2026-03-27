# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-03-27 00:38:05
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 1
**Legacy Compatibility Markers Detected**: 4

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
- Removed entries: 3
- Active search terms: 4
- Current inventory-term hits in scan: 1 file(s), 4 marker(s)

## Deprecation Inventory Terms
**Files Affected**: 1

### development_tools\config\sync_ruff_toml.py
**Issues Found**: 4

- **Line 4**: `Generate root .ruff.toml from shared development-tools exclusions.`
  ```
  """Generate root .ruff.toml from shared development-tools exclusions.
  ```

- **Line 9**: `Run: python -m development_tools.config.sync_ruff_toml [--project-root .]`
  ```
  Run: python -m development_tools.config.sync_ruff_toml [--project-root .]
  ```

- **Line 126**: `Do not generate compatibility .ruff.toml at repository root`
  ```
  help="Do not generate compatibility .ruff.toml at repository root.",
  ```

- **Line 138**: `Generated {output_path} and {project_root / '.ruff.toml'}`
  ```
  print(f"Generated {output_path} and {project_root / '.ruff.toml'}")
  ```
