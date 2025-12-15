# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2025-12-15 02:21:15
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 6
**Legacy Compatibility Markers Detected**: 25

## Summary
- Scan mode only: no automated fixes were applied.
- Legacy compatibility markers remain in 4 file(s) (6 total markers).

## Recommended Follow-Up
1. Confirm whether legacy `enabled_fields` payloads are still produced; if not, plan removal and data migration.
2. Add regression tests covering analytics handler flows and user data migrations before deleting markers.
3. Track the cleanup effort and rerun `python development_tools/run_development_tools.py legacy --clean --dry-run` until this report returns zero issues.

## Deprecated Functions
**Files Affected**: 2

### tests\development_tools\test_legacy_reference_cleanup.py
**Issues Found**: 9

- **Line 93**: `LegacyChannelWrapper`
  ```
  assert 'LegacyChannelWrapper' in content, "LegacyChannelWrapper should exist in legacy_code.py"
  ```

- **Line 93**: `LegacyChannelWrapper`
  ```
  assert 'LegacyChannelWrapper' in content, "LegacyChannelWrapper should exist in legacy_code.py"
  ```

- **Line 98**: `LegacyChannelWrapper`
  ```
  # Find references to LegacyChannelWrapper
  ```

- **Line 100**: `LegacyChannelWrapper`
  ```
  references = analyzer.find_all_references('LegacyChannelWrapper')
  ```

- **Line 103**: `LegacyChannelWrapper`
  ```
  # It searches for patterns like 'class LegacyChannelWrapper', 'LegacyChannelWrapper(', etc.
  ```

- **Line 103**: `LegacyChannelWrapper`
  ```
  # It searches for patterns like 'class LegacyChannelWrapper', 'LegacyChannelWrapper(', etc.
  ```

- **Line 104**: `LegacyChannelWrapper`
  ```
  assert len(references) > 0, f"find_all_references should find LegacyChannelWrapper. Found: {references}"
  ```

- **Line 129**: `LegacyChannelWrapper`
  ```
  # Test with LegacyChannelWrapper which exists in legacy_code.py
  ```

- **Line 130**: `LegacyChannelWrapper`
  ```
  verification = analyzer.verify_removal_readiness('LegacyChannelWrapper')
  ```

### tests\fixtures\development_tools_demo\legacy_code.py
**Issues Found**: 2

- **Line 25**: `LegacyChannelWrapper`
  ```
  class LegacyChannelWrapper:
  ```

- **Line 30**: `_create_legacy_channel_access(`
  ```
  def _create_legacy_channel_access():
  ```

## Historical References
**Files Affected**: 1

### tests\fixtures\development_tools_demo\legacy_code.py
**Issues Found**: 1

- **Line 21**: `bot/communication`
  ```
  old_path = "bot/communication/old_file.py"
  ```

## Legacy Compatibility Markers
**Files Affected**: 4

### development_tools\docs\analyze_path_drift.py
**Issues Found**: 1

- **Line 751**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Handle both standard format (new) and legacy format (old)
  ```

### development_tools\shared\cli_interface.py
**Issues Found**: 1

- **Line 63**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Handle deprecated --fast flag
  ```

### development_tools\shared\mtime_cache.py
**Issues Found**: 2

- **Line 112**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Fallback to legacy file-based loading
  ```

- **Line 164**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Fallback to legacy file-based saving
  ```

### tests\fixtures\development_tools_demo\legacy_code.py
**Issues Found**: 2

- **Line 7**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: This function is kept for backward compatibility
  ```

- **Line 13**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Old import pattern
  ```

## Old Bot Directory
**Files Affected**: 3

### tests\development_tools\test_legacy_reference_cleanup.py
**Issues Found**: 3

- **Line 236**: `bot/`
  ```
  ('bot/', 'communication/'),
  ```

- **Line 237**: `from bot.`
  ```
  ('from bot.', 'from communication.'),
  ```

- **Line 238**: `import bot.`
  ```
  ('import bot.', 'import communication.'),
  ```

### tests\development_tools\test_path_drift_detection.py
**Issues Found**: 1

- **Line 121**: `bot/`
  ```
  - `bot/old_module.py` (legacy path)
  ```

### tests\fixtures\development_tools_demo\legacy_code.py
**Issues Found**: 2

- **Line 15**: `from bot.`
  ```
  # from bot.communication import old_module  # noqa: F401
  ```

- **Line 21**: `bot/`
  ```
  old_path = "bot/communication/old_file.py"
  ```

## Old Import Paths
**Files Affected**: 1

### tests\fixtures\development_tools_demo\legacy_code.py
**Issues Found**: 1

- **Line 15**: `from bot.communication`
  ```
  # from bot.communication import old_module  # noqa: F401
  ```
