# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-03-17 12:06:24
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 9
**Legacy Compatibility Markers Detected**: 18

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
- Active/candidate entries: 5
- Removed entries: 21
- Active search terms: 16
- Current inventory-term hits in scan: 9 file(s), 18 marker(s)

## Deprecation Inventory Terms
**Files Affected**: 9

### core\__init__.py
**Issues Found**: 2

- **Line 281**: `migrate_legacy_schedules_structure`
  ```
  migrate_legacy_schedules_structure,
  ```

- **Line 513**: `migrate_legacy_schedules_structure`
  ```
  "migrate_legacy_schedules_structure",
  ```

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

### core\user_data_schedule_defaults.py
**Issues Found**: 4

- **Line 3**: `migrate_legacy_schedules_structure`
  ```
  migrate_legacy_schedules_structure, ensure_category_has_default_schedule,
  ```

- **Line 53**: `migrate_legacy_schedules_structure`
  ```
  def migrate_legacy_schedules_structure(
  ```

- **Line 56**: `Migrate legacy schedules structure to new format`
  ```
  """Migrate legacy schedules structure to new format."""
  ```

- **Line 96**: `migrate_legacy_schedules_structure`
  ```
  schedules_data = migrate_legacy_schedules_structure(schedules_data)
  ```

### development_tools\config\config.py
**Issues Found**: 1

- **Line 910**: `ruff_sync_root_compat`
  ```
  "ruff_sync_root_compat": True,
  ```

### development_tools\config\sync_ruff_toml.py
**Issues Found**: 1

- **Line 124**: `--no-root-compat`
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
