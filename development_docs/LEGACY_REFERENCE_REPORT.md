# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-03-26 01:05:10
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 3
**Legacy Compatibility Markers Detected**: 7

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
- Active search terms: 3
- Current inventory-term hits in scan: 3 file(s), 7 marker(s)

## Deprecation Inventory Terms
**Files Affected**: 3

### development_tools\config\sync_ruff_toml.py
**Issues Found**: 4

- **Line 4**: `.ruff.toml`
  ```
  """Generate root .ruff.toml from shared development-tools exclusions.
  ```

- **Line 107**: `.ruff.toml`
  ```
  _write_if_changed(project_root / ".ruff.toml", content)
  ```

- **Line 126**: `.ruff.toml`
  ```
  help="Do not generate compatibility .ruff.toml at repository root.",
  ```

- **Line 138**: `.ruff.toml`
  ```
  print(f"Generated {output_path} and {project_root / '.ruff.toml'}")
  ```

### tests\development_tools\test_pyright_config_paths.py
**Issues Found**: 1

- **Line 75**: `.ruff.toml`
  ```
  path = project_root / ".ruff.toml"
  ```

### tests\development_tools\test_sync_ruff_toml.py
**Issues Found**: 2

- **Line 23**: `.ruff.toml`
  ```
  assert (tmp_path / ".ruff.toml").exists()
  ```

- **Line 35**: `.ruff.toml`
  ```
  assert not (tmp_path / ".ruff.toml").exists()
  ```
