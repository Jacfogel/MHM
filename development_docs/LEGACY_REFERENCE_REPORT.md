# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-01-04 17:41:36
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 8
**Legacy Compatibility Markers Detected**: 25

## Summary
- Scan mode only: no automated fixes were applied.
- Legacy compatibility markers remain in 7 file(s) (21 total markers).

## Recommended Follow-Up
1. Confirm whether legacy `enabled_fields` payloads are still produced; if not, plan removal and data migration.
2. Add regression tests covering analytics handler flows and user data migrations before deleting markers.
3. Track the cleanup effort and rerun `python development_tools/run_development_tools.py legacy --clean --dry-run` until this report returns zero issues.

## Legacy Compatibility Markers
**Files Affected**: 7

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
**Issues Found**: 2

- **Line 438**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Support for 'all_cleanup', 'coverage', and 'dry_run' parameters
  ```

- **Line 516**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Wrapper for backward compatibility with tests and existing code
  ```

### development_tools\shared\service\report_generation.py
**Issues Found**: 2

- **Line 1176**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Check for both new and old key names
  ```

- **Line 4191**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Check for both new and old key names
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

- **Line 529**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

- **Line 593**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Also mock legacy wrapper for backward compatibility
  ```

- **Line 1017**: `# LEGACY COMPATIBILITY:`
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

## Legacy Parameters
**Files Affected**: 2

### development_tools\docs\fix_documentation_ascii.py
**Issues Found**: 1

- **Line 161**: `dry_run=args.dry_run`
  ```
  result = fixer.fix_ascii(dry_run=args.dry_run)
  ```

### development_tools\shared\service\commands.py
**Issues Found**: 3

- **Line 441**: `all_cleanup=`
  ```
  # Detection pattern: "all_cleanup=", "coverage=args.coverage", "dry_run=args.dry_run"
  ```

- **Line 441**: `coverage=args.coverage`
  ```
  # Detection pattern: "all_cleanup=", "coverage=args.coverage", "dry_run=args.dry_run"
  ```

- **Line 441**: `dry_run=args.dry_run`
  ```
  # Detection pattern: "all_cleanup=", "coverage=args.coverage", "dry_run=args.dry_run"
  ```
