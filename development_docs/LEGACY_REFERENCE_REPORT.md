# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-03-05 23:54:16
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 7
**Legacy Compatibility Markers Detected**: 12

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
- Active/candidate entries: 4
- Removed entries: 21
- Active search terms: 14
- Current inventory-term hits in scan: 7 file(s), 12 marker(s)

## Deprecation Inventory Terms
**Files Affected**: 7

### core\message_management.py
**Issues Found**: 4

- **Line 697**: `parsing legacy timestamp for normalization`
  ```
  "parsing legacy timestamp for normalization",
  ```

- **Line 701**: `_parse_legacy_timestamp_for_normalization(`
  ```
  def _parse_legacy_timestamp_for_normalization(timestamp_str: str) -> datetime | None:
  ```

- **Line 742**: `_parse_legacy_timestamp_for_normalization(`
  ```
  legacy_dt = _parse_legacy_timestamp_for_normalization(timestamp_value)
  ```

- **Line 755**: `legacy timestamps`
  ```
  f"Normalized {normalized_count} legacy timestamps in {file_path_obj}"
  ```

### development_tools\config\config.py
**Issues Found**: 1

- **Line 869**: `ruff_sync_root_compat`
  ```
  "ruff_sync_root_compat": True,
  ```

### development_tools\config\sync_ruff_toml.py
**Issues Found**: 1

- **Line 118**: `--no-root-compat`
  ```
  "--no-root-compat",
  ```

### development_tools\legacy\fix_legacy_references.py
**Issues Found**: 1

- **Line 65**: `backup_zip_compat_bridge`
  ```
  "backup_zip_compat_bridge",
  ```

### development_tools\static_checks\analyze_ruff.py
**Issues Found**: 1

- **Line 137**: `ruff_sync_root_compat`
  ```
  sync_root_compat = bool(static_cfg.get("ruff_sync_root_compat", True))
  ```

### tests\development_tools\test_config.py
**Issues Found**: 3

- **Line 250**: `ruff_sync_root_compat`
  ```
  assert "ruff_sync_root_compat" in result
  ```

- **Line 262**: `ruff_sync_root_compat`
  ```
  "ruff_sync_root_compat": False,
  ```

- **Line 270**: `ruff_sync_root_compat`
  ```
  assert result["ruff_sync_root_compat"] is False
  ```

### tests\development_tools\test_static_analysis_tools.py
**Issues Found**: 1

- **Line 82**: `ruff_sync_root_compat`
  ```
  "ruff_sync_root_compat": False,
  ```
