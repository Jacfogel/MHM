# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2025-12-31 02:36:06
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 8
**Legacy Compatibility Markers Detected**: 28

## Summary
- Scan mode only: no automated fixes were applied.
- Legacy compatibility markers remain in 8 file(s) (22 total markers).

## Recommended Follow-Up
1. Confirm whether legacy `enabled_fields` payloads are still produced; if not, plan removal and data migration.
2. Add regression tests covering analytics handler flows and user data migrations before deleting markers.
3. Track the cleanup effort and rerun `python development_tools/run_development_tools.py legacy --clean --dry-run` until this report returns zero issues.

## Deprecated Functions
**Files Affected**: 1

### tests\data\tmplgig3zdw\demo_project\legacy_code.py
**Issues Found**: 2

- **Line 27**: `LegacyChannelWrapper`
  ```
  class LegacyChannelWrapper:
  ```

- **Line 32**: `_create_legacy_channel_access(`
  ```
  def _create_legacy_channel_access():
  ```

## Historical References
**Files Affected**: 1

### tests\data\tmplgig3zdw\demo_project\legacy_code.py
**Issues Found**: 1

- **Line 23**: `bot/communication`
  ```
  old_path = "bot/communication/old_file.py"
  ```

## Legacy Compatibility Markers
**Files Affected**: 8

### development_tools\reports\analyze_system_signals.py
**Issues Found**: 1

- **Line 79**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Alias for backward compatibility
  ```

### development_tools\shared\service\audit_orchestration.py
**Issues Found**: 1

- **Line 785**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also store with old key for backward compatibility
  ```

### development_tools\shared\service\commands.py
**Issues Found**: 1

- **Line 492**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Wrapper for backward compatibility with tests and existing code
  ```

### development_tools\shared\service\report_generation.py
**Issues Found**: 2

- **Line 1143**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Check for both new and old key names
  ```

- **Line 4043**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Check for both new and old key names
  ```

### tests\data\tmplgig3zdw\demo_project\legacy_code.py
**Issues Found**: 2

- **Line 9**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: This function is kept for backward compatibility
  ```

- **Line 15**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Old import pattern
  ```

### tests\development_tools\test_audit_status_updates.py
**Issues Found**: 4

- **Line 71**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

- **Line 160**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

- **Line 247**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

- **Line 329**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

### tests\development_tools\test_audit_tier_comprehensive.py
**Issues Found**: 9

- **Line 122**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

- **Line 181**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

- **Line 244**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

- **Line 319**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

- **Line 369**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

- **Line 437**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

- **Line 494**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

- **Line 554**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

- **Line 900**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

### tests\development_tools\test_path_drift_integration.py
**Issues Found**: 2

- **Line 122**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

- **Line 170**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

## Old Bot Directory
**Files Affected**: 1

### tests\data\tmplgig3zdw\demo_project\legacy_code.py
**Issues Found**: 2

- **Line 17**: `from bot.`
  ```
  # from bot.communication import old_module  # noqa: F401
  ```

- **Line 23**: `bot/`
  ```
  old_path = "bot/communication/old_file.py"
  ```

## Old Import Paths
**Files Affected**: 1

### tests\data\tmplgig3zdw\demo_project\legacy_code.py
**Issues Found**: 1

- **Line 17**: `from bot.communication`
  ```
  # from bot.communication import old_module  # noqa: F401
  ```
