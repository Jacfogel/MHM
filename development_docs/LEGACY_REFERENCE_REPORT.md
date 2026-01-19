# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-01-19 05:47:30
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 38
**Legacy Compatibility Markers Detected**: 86

## Summary
- Scan mode only: no automated fixes were applied.
- Legacy compatibility markers remain in 2 file(s) (3 total markers).

## Recommended Follow-Up
1. Confirm whether legacy `enabled_fields` payloads are still produced; if not, plan removal and data migration.
2. Add regression tests covering analytics handler flows and user data migrations before deleting markers.
3. Track the cleanup effort and rerun `python development_tools/run_development_tools.py legacy --clean --dry-run` until this report returns zero issues.

## Deprecated Functions
**Files Affected**: 1

### tests\data\tmpt0l34t9s\demo_project\legacy_code.py
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

### tests\data\tmpt0l34t9s\demo_project\legacy_code.py
**Issues Found**: 1

- **Line 23**: `bot/communication`
  ```
  old_path = "bot/communication/old_file.py"
  ```

## Legacy Compatibility Markers
**Files Affected**: 2

### core\message_management.py
**Issues Found**: 1

- **Line 675**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY:
  ```

### tests\data\tmpt0l34t9s\demo_project\legacy_code.py
**Issues Found**: 2

- **Line 9**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: This function is kept for backward compatibility
  ```

- **Line 15**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Old import pattern
  ```

## Legacy Inventory Tracking
**Files Affected**: 36

### communication\command_handlers\account_handler.py
**Issues Found**: 1

- **Line 98**: `backward compatibility`
  ```
  # Extract feature selection (default to True for backward compatibility)
  ```

### communication\communication_channels\discord\bot.py
**Issues Found**: 1

- **Line 666**: `Backward compatibility`
  ```
  # Backward compatibility: just message
  ```

### communication\core\channel_orchestrator.py
**Issues Found**: 1

- **Line 1042**: `legacy channels`
  ```
  channel.stop()  # Fallback for any remaining legacy channels
  ```

### core\__init__.py
**Issues Found**: 2

- **Line 519**: `backward compatibility`
  ```
  # Legacy module names (for backward compatibility)
  ```

- **Line 519**: `Legacy module`
  ```
  # Legacy module names (for backward compatibility)
  ```

### core\config.py
**Issues Found**: 1

- **Line 708**: `backward compatibility`
  ```
  # Legacy validation functions (kept for backward compatibility)
  ```

### core\message_management.py
**Issues Found**: 2

- **Line 664**: `backward compatibility`
  ```
  Handles multiple timestamp formats for backward compatibility.
  ```

- **Line 677**: `backward compatibility`
  ```
  # This function preserves backward compatibility for persisted message timestamps.
  ```

### core\scheduler.py
**Issues Found**: 1

- **Line 1664**: `backward compatibility`
  ```
  Legacy function for backward compatibility.
  ```

### core\schemas.py
**Issues Found**: 1

- **Line 242**: `backward compatibility`
  ```
  # If invalid, keep as-is for backward compatibility (tests may set placeholders)
  ```

### core\user_data_handlers.py
**Issues Found**: 2

- **Line 1765**: `backward compatibility`
  ```
  # This function is kept for backward compatibility but should primarily be used
  ```

- **Line 2251**: `backward compatibility`
  ```
  # Check for explicit messages_enabled flag first, then fall back to categories check (for backward compatibility)
  ```

### core\user_data_validation.py
**Issues Found**: 4

- **Line 335**: `backward compatibility`
  ```
  # This function is kept for backward compatibility but delegates to Pydantic
  ```

- **Line 339**: `backward compatibility`
  ```
  # This maintains backward compatibility with the old validation approach
  ```

- **Line 381**: `backward compatibility`
  ```
  # This function is kept for backward compatibility but delegates to Pydantic
  ```

- **Line 440**: `backward compatibility`
  ```
  # This function is kept for backward compatibility but delegates to Pydantic
  ```

### development_tools\ai_work\analyze_ai_work.py
**Issues Found**: 1

- **Line 466**: `backward compatibility`
  ```
  # Print text output for backward compatibility
  ```

### development_tools\config\__init__.py
**Issues Found**: 1

- **Line 3**: `backward compatibility`
  ```
  # Re-export config module for backward compatibility
  ```

### development_tools\config\config.py
**Issues Found**: 2

- **Line 49**: `backward compatibility`
  ```
  # Fallback to project root for backward compatibility
  ```

- **Line 808**: `backward compatibility`
  ```
  # Default paths include development_tools/ for backward compatibility
  ```

### development_tools\docs\analyze_documentation_sync.py
**Issues Found**: 1

- **Line 203**: `backward compatibility`
  ```
  # The --check flag is maintained for backward compatibility but has no effect
  ```

### development_tools\imports\analyze_dependency_patterns.py
**Issues Found**: 1

- **Line 532**: `backward compatibility`
  ```
  # Convenience functions for backward compatibility
  ```

### development_tools\imports\analyze_module_imports.py
**Issues Found**: 1

- **Line 464**: `backward compatibility`
  ```
  # Convenience functions for backward compatibility
  ```

### development_tools\reports\analyze_system_signals.py
**Issues Found**: 1

- **Line 788**: `backward compatibility`
  ```
  # Legacy warnings/errors (for backward compatibility)
  ```

### development_tools\shared\constants.py
**Issues Found**: 1

- **Line 369**: `backward compatibility`
  ```
  # If it's a real list, use it (for backward compatibility)
  ```

### development_tools\shared\mtime_cache.py
**Issues Found**: 1

- **Line 246**: `legacy path`
  ```
  # This ensures we fix standardized storage issues rather than silently using legacy paths
  ```

### development_tools\shared\service\audit_orchestration.py
**Issues Found**: 3

- **Line 46**: `backward compatibility`
  ```
  # Fallback to default STATUS config values for backward compatibility
  ```

- **Line 247**: `backward compatibility`
  ```
  # Fallback to default STATUS config values for backward compatibility
  ```

- **Line 254**: `backward compatibility`
  ```
  # Fallback to default STATUS config values for backward compatibility
  ```

### development_tools\shared\service\commands.py
**Issues Found**: 3

- **Line 270**: `backward compatibility`
  ```
  # Fallback to default STATUS config values for backward compatibility
  ```

- **Line 277**: `backward compatibility`
  ```
  # Fallback to default STATUS config values for backward compatibility
  ```

- **Line 380**: `backward compatibility`
  ```
  # Note: --update-plan flag is kept for backward compatibility but does nothing
  ```

### development_tools\shared\service\data_loading.py
**Issues Found**: 1

- **Line 379**: `backward compatibility`
  ```
  # Fallback to old location (development_tools/tests/coverage.json) for backward compatibility
  ```

### development_tools\shared\service\report_generation.py
**Issues Found**: 3

- **Line 36**: `backward compatibility`
  ```
  # Default matches development_tools_config.json for backward compatibility
  ```

- **Line 4256**: `backward compatibility`
  ```
  # Fallback to default STATUS config values for backward compatibility
  ```

- **Line 4263**: `backward compatibility`
  ```
  # Fallback to default STATUS config values for backward compatibility
  ```

### development_tools\shared\service\tool_wrappers.py
**Issues Found**: 1

- **Line 1312**: `backward compatibility`
  ```
  logger.debug("analyze_path_drift: Using legacy format (backward compatibility)")
  ```

### development_tools\shared\standard_exclusions.py
**Issues Found**: 1

- **Line 336**: `backward compatibility`
  ```
  # For backward compatibility: ALL_GENERATED_FILES contains only exact paths
  ```

### development_tools\tests\analyze_test_markers.py
**Issues Found**: 1

- **Line 142**: `backward compatibility`
  ```
  Note: This method is kept here for backward compatibility but the fixing
  ```

### development_tools\tests\generate_test_coverage_report.py
**Issues Found**: 1

- **Line 79**: `backward compatibility`
  ```
  # Fall back to root location for backward compatibility
  ```

### development_tools\tests\run_test_coverage.py
**Issues Found**: 4

- **Line 172**: `backward compatibility`
  ```
  # Fall back to root location for backward compatibility
  ```

- **Line 237**: `backward compatibility`
  ```
  self.use_domain_cache = use_domain_cache  # Keep name for backward compatibility
  ```

- **Line 1058**: `backward compatibility`
  ```
  stdout_log_path  # Keep variable name for backward compatibility
  ```

- **Line 3713**: `backward compatibility`
  ```
  # Keeping for backward compatibility but it shouldn't be called
  ```

### run_tests.py
**Issues Found**: 1

- **Line 2172**: `backward compatibility`
  ```
  # Handle case where parallel_results might be a bool (backward compatibility)
  ```

### tests\behavior\test_account_handler_behavior.py
**Issues Found**: 1

- **Line 173**: `backward compatibility`
  ```
  # Create account without feature selection parameters (backward compatibility)
  ```

### tests\conftest.py
**Issues Found**: 1

- **Line 1684**: `backward compatibility`
  ```
  This function is kept for backward compatibility but does nothing.
  ```

### tests\data\tmpt0l34t9s\demo_project\legacy_code.py
**Issues Found**: 1

- **Line 9**: `backward compatibility`
  ```
  # LEGACY COMPATIBILITY: This function is kept for backward compatibility
  ```

### tests\development_tools\test_config.py
**Issues Found**: 2

- **Line 59**: `backward compatibility`
  ```
  # Check both new location and old location for backward compatibility
  ```

- **Line 169**: `backward compatibility`
  ```
  # Check both new location and old location for backward compatibility
  ```

### tests\test_utilities.py
**Issues Found**: 13

- **Line 588**: `backward compatibility`
  ```
  # Use real user directory (for backward compatibility)
  ```

- **Line 796**: `backward compatibility`
  ```
  # Use real user directory (for backward compatibility)
  ```

- **Line 966**: `backward compatibility`
  ```
  # Use real user directory (for backward compatibility)
  ```

- **Line 1091**: `backward compatibility`
  ```
  # Use real user directory (for backward compatibility)
  ```

- **Line 1396**: `backward compatibility`
  ```
  # Use real user directory (for backward compatibility)
  ```

- **Line 1424**: `backward compatibility`
  ```
  # Use real user directory (for backward compatibility)
  ```

- **Line 1638**: `backward compatibility`
  ```
  # Use real user directory (for backward compatibility)
  ```

- **Line 1827**: `backward compatibility`
  ```
  # Use real user directory (for backward compatibility)
  ```

- **Line 2017**: `backward compatibility`
  ```
  # Use real user directory (for backward compatibility)
  ```

- **Line 2185**: `backward compatibility`
  ```
  # Use real user directory (for backward compatibility)
  ```

- **Line 2358**: `backward compatibility`
  ```
  # Use real user directory (for backward compatibility)
  ```

- **Line 2515**: `backward compatibility`
  ```
  # Use real user directory (for backward compatibility)
  ```

- **Line 2996**: `backward compatibility`
  ```
  # Convenience functions for backward compatibility
  ```

### tests\ui\test_signal_handler_integration.py
**Issues Found**: 1

- **Line 155**: `backward compatibility`
  ```
  # Also verify it works when called with no parameter (backward compatibility)
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

## Legacy Timestamp Parsing
**Files Affected**: 3

### core\message_management.py
**Issues Found**: 7

- **Line 456**: `_parse_timestamp(`
  ```
  if _parse_timestamp(msg.get("timestamp", "")) >= cutoff_date
  ```

- **Line 461**: `_parse_timestamp(`
  ```
  key=lambda msg: _parse_timestamp(msg.get("timestamp", "")), reverse=True
  ```

- **Line 530**: `_parse_timestamp(`
  ```
  new_timestamp = _parse_timestamp(new_message["timestamp"])
  ```

- **Line 533**: `_parse_timestamp(`
  ```
  existing_timestamp = _parse_timestamp(existing_msg.get("timestamp", ""))
  ```

- **Line 596**: `_parse_timestamp(`
  ```
  message_timestamp = _parse_timestamp(message.get("timestamp", ""))
  ```

- **Line 660**: `_parse_timestamp(`
  ```
  def _parse_timestamp(timestamp_str: str) -> datetime:
  ```

- **Line 696**: `LEGACY COMPATIBILITY: Parsed non-{TIMESTAMP_FULL} message timestamp`
  ```
  f"LEGACY COMPATIBILITY: Parsed non-{TIMESTAMP_FULL} message timestamp: {timestamp_str!r}"
  ```

### development_tools\shared\output_storage.py
**Issues Found**: 3

- **Line 437**: `_parse_timestamp(`
  ```
  def _parse_timestamp(result_data: Dict[str, Any], result_file: Path) -> datetime:
  ```

- **Line 479**: `_parse_timestamp(`
  ```
  existing_ts = _parse_timestamp(existing, result_file)
  ```

- **Line 480**: `_parse_timestamp(`
  ```
  candidate_ts = _parse_timestamp(result_data, result_file)
  ```

### tests\behavior\test_core_message_management_coverage_expansion.py
**Issues Found**: 1

- **Line 90**: `_parse_timestamp(`
  ```
  result = _parse_timestamp(timestamp_str)
  ```

## Old Bot Directory
**Files Affected**: 1

### tests\data\tmpt0l34t9s\demo_project\legacy_code.py
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

### tests\data\tmpt0l34t9s\demo_project\legacy_code.py
**Issues Found**: 1

- **Line 17**: `from bot.communication`
  ```
  # from bot.communication import old_module  # noqa: F401
  ```
