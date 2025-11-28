# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: 2025-11-27 19:50:17
**Total Files with Issues**: 3
**Legacy Compatibility Markers Detected**: 49

## Summary
- Scan mode only: no automated fixes were applied.
- Legacy compatibility markers remain in 2 file(s) (3 total markers).

## Recommended Follow-Up
1. Confirm whether legacy `enabled_fields` payloads are still produced; if not, plan removal and data migration.
2. Add regression tests covering analytics handler flows and user data migrations before deleting markers.
3. Track the cleanup effort and rerun `python development_tools/ai_tools_runner.py legacy --clean --dry-run` until this report returns zero issues.

## Deprecated Functions
**Files Affected**: 3

### development_tools\legacy_reference_cleanup.py
**Issues Found**: 3

- **Line 72**: `LegacyChannelWrapper`
  ```
  r'LegacyChannelWrapper',
  ```

- **Line 100**: `LegacyChannelWrapper`
  ```
  'LegacyChannelWrapper': 'direct channel access',
  ```

- **Line 101**: `_create_legacy_channel_access(`
  ```
  '_create_legacy_channel_access(': 'direct channel access (',
  ```

### tests\development_tools\test_legacy_reference_cleanup.py
**Issues Found**: 9

- **Line 89**: `LegacyChannelWrapper`
  ```
  assert 'LegacyChannelWrapper' in content, "LegacyChannelWrapper should exist in legacy_code.py"
  ```

- **Line 89**: `LegacyChannelWrapper`
  ```
  assert 'LegacyChannelWrapper' in content, "LegacyChannelWrapper should exist in legacy_code.py"
  ```

- **Line 94**: `LegacyChannelWrapper`
  ```
  # Find references to LegacyChannelWrapper
  ```

- **Line 96**: `LegacyChannelWrapper`
  ```
  references = checker.find_all_references('LegacyChannelWrapper')
  ```

- **Line 99**: `LegacyChannelWrapper`
  ```
  # It searches for patterns like 'class LegacyChannelWrapper', 'LegacyChannelWrapper(', etc.
  ```

- **Line 99**: `LegacyChannelWrapper`
  ```
  # It searches for patterns like 'class LegacyChannelWrapper', 'LegacyChannelWrapper(', etc.
  ```

- **Line 100**: `LegacyChannelWrapper`
  ```
  assert len(references) > 0, f"find_all_references should find LegacyChannelWrapper. Found: {references}"
  ```

- **Line 125**: `LegacyChannelWrapper`
  ```
  # Test with LegacyChannelWrapper which exists in legacy_code.py
  ```

- **Line 126**: `LegacyChannelWrapper`
  ```
  verification = checker.verify_removal_readiness('LegacyChannelWrapper')
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
**Files Affected**: 2

### development_tools\legacy_reference_cleanup.py
**Issues Found**: 3

- **Line 67**: `bot/communication`
  ```
  r'bot/communication',
  ```

- **Line 68**: `bot/discord`
  ```
  r'bot/discord',
  ```

- **Line 69**: `bot/email`
  ```
  r'bot/email',
  ```

### tests\fixtures\development_tools_demo\legacy_code.py
**Issues Found**: 1

- **Line 21**: `bot/communication`
  ```
  old_path = "bot/communication/old_file.py"
  ```

## Legacy Compatibility Markers
**Files Affected**: 2

### development_tools\legacy_reference_cleanup.py
**Issues Found**: 1

- **Line 77**: `# LEGACY COMPATIBILITY:`
  ```
  r'# LEGACY COMPATIBILITY:',
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

### development_tools\legacy_reference_cleanup.py
**Issues Found**: 16

- **Line 9**: `bot/`
  ```
  - Old bot/ directory (now communication/)
  ```

- **Line 51**: `bot/`
  ```
  # Legacy patterns to identify - specific to old bot/ directory structure and deprecated functions
  ```

- **Line 54**: `bot/`
  ```
  r'bot/',
  ```

- **Line 67**: `bot/`
  ```
  r'bot/communication',
  ```

- **Line 68**: `bot/`
  ```
  r'bot/discord',
  ```

- **Line 69**: `bot/`
  ```
  r'bot/email',
  ```

- **Line 89**: `bot/`
  ```
  # Replacement mappings - specific to old bot/ directory structure and deprecated functions
  ```

- **Line 91**: `bot/`
  ```
  'bot/': 'communication/',
  ```

- **Line 92**: `from bot.`
  ```
  'from bot.': 'from communication.',
  ```

- **Line 93**: `import bot.`
  ```
  'import bot.': 'import communication.',
  ```

- **Line 94**: `from bot.`
  ```
  'from bot.communication': 'from communication.communication_channels',
  ```

- **Line 95**: `from bot.`
  ```
  'from bot.discord': 'from communication.communication_channels.discord',
  ```

- **Line 96**: `from bot.`
  ```
  'from bot.email': 'from communication.communication_channels.email',
  ```

- **Line 97**: `import bot.`
  ```
  'import bot.communication': 'import communication.communication_channels',
  ```

- **Line 98**: `import bot.`
  ```
  'import bot.discord': 'import communication.communication_channels.discord',
  ```

- **Line 99**: `import bot.`
  ```
  'import bot.email': 'import communication.communication_channels.email',
  ```

### tests\development_tools\test_legacy_reference_cleanup.py
**Issues Found**: 3

- **Line 229**: `bot/`
  ```
  ('bot/', 'communication/'),
  ```

- **Line 230**: `from bot.`
  ```
  ('from bot.', 'from communication.'),
  ```

- **Line 231**: `import bot.`
  ```
  ('import bot.', 'import communication.'),
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
**Files Affected**: 2

### development_tools\legacy_reference_cleanup.py
**Issues Found**: 6

- **Line 94**: `from bot.communication`
  ```
  'from bot.communication': 'from communication.communication_channels',
  ```

- **Line 95**: `from bot.discord`
  ```
  'from bot.discord': 'from communication.communication_channels.discord',
  ```

- **Line 96**: `from bot.email`
  ```
  'from bot.email': 'from communication.communication_channels.email',
  ```

- **Line 97**: `import bot.communication`
  ```
  'import bot.communication': 'import communication.communication_channels',
  ```

- **Line 98**: `import bot.discord`
  ```
  'import bot.discord': 'import communication.communication_channels.discord',
  ```

- **Line 99**: `import bot.email`
  ```
  'import bot.email': 'import communication.communication_channels.email',
  ```

### tests\fixtures\development_tools_demo\legacy_code.py
**Issues Found**: 1

- **Line 15**: `from bot.communication`
  ```
  # from bot.communication import old_module  # noqa: F401
  ```
