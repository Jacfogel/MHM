# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: 2025-11-17 02:10:54
**Total Files with Issues**: 1
**Legacy Compatibility Markers Detected**: 29

## Summary
- Scan mode only: no automated fixes were applied.
- Legacy compatibility markers remain in 1 file(s) (1 total markers).

## Recommended Follow-Up
1. Confirm whether legacy `enabled_fields` payloads are still produced; if not, plan removal and data migration.
2. Add regression tests covering analytics handler flows and user data migrations before deleting markers.
3. Track the cleanup effort and rerun `python ai_development_tools/ai_tools_runner.py legacy --clean --dry-run` until this report returns zero issues.

## Deprecated Functions
**Files Affected**: 1

### ai_development_tools\legacy_reference_cleanup.py
**Issues Found**: 3

- **Line 69**: `LegacyChannelWrapper`
  ```
  r'LegacyChannelWrapper',
  ```

- **Line 97**: `LegacyChannelWrapper`
  ```
  'LegacyChannelWrapper': 'direct channel access',
  ```

- **Line 98**: `_create_legacy_channel_access(`
  ```
  '_create_legacy_channel_access(': 'direct channel access (',
  ```

## Historical References
**Files Affected**: 1

### ai_development_tools\legacy_reference_cleanup.py
**Issues Found**: 3

- **Line 64**: `bot/communication`
  ```
  r'bot/communication',
  ```

- **Line 65**: `bot/discord`
  ```
  r'bot/discord',
  ```

- **Line 66**: `bot/email`
  ```
  r'bot/email',
  ```

## Legacy Compatibility Markers
**Files Affected**: 1

### ai_development_tools\legacy_reference_cleanup.py
**Issues Found**: 1

- **Line 74**: `# LEGACY COMPATIBILITY:`
  ```
  r'# LEGACY COMPATIBILITY:',
  ```

## Old Bot Directory
**Files Affected**: 1

### ai_development_tools\legacy_reference_cleanup.py
**Issues Found**: 16

- **Line 6**: `bot/`
  ```
  - Old bot/ directory (now communication/)
  ```

- **Line 48**: `bot/`
  ```
  # Legacy patterns to identify - specific to old bot/ directory structure and deprecated functions
  ```

- **Line 51**: `bot/`
  ```
  r'bot/',
  ```

- **Line 64**: `bot/`
  ```
  r'bot/communication',
  ```

- **Line 65**: `bot/`
  ```
  r'bot/discord',
  ```

- **Line 66**: `bot/`
  ```
  r'bot/email',
  ```

- **Line 86**: `bot/`
  ```
  # Replacement mappings - specific to old bot/ directory structure and deprecated functions
  ```

- **Line 88**: `bot/`
  ```
  'bot/': 'communication/',
  ```

- **Line 89**: `from bot.`
  ```
  'from bot.': 'from communication.',
  ```

- **Line 90**: `import bot.`
  ```
  'import bot.': 'import communication.',
  ```

- **Line 91**: `from bot.`
  ```
  'from bot.communication': 'from communication.communication_channels',
  ```

- **Line 92**: `from bot.`
  ```
  'from bot.discord': 'from communication.communication_channels.discord',
  ```

- **Line 93**: `from bot.`
  ```
  'from bot.email': 'from communication.communication_channels.email',
  ```

- **Line 94**: `import bot.`
  ```
  'import bot.communication': 'import communication.communication_channels',
  ```

- **Line 95**: `import bot.`
  ```
  'import bot.discord': 'import communication.communication_channels.discord',
  ```

- **Line 96**: `import bot.`
  ```
  'import bot.email': 'import communication.communication_channels.email',
  ```

## Old Import Paths
**Files Affected**: 1

### ai_development_tools\legacy_reference_cleanup.py
**Issues Found**: 6

- **Line 91**: `from bot.communication`
  ```
  'from bot.communication': 'from communication.communication_channels',
  ```

- **Line 92**: `from bot.discord`
  ```
  'from bot.discord': 'from communication.communication_channels.discord',
  ```

- **Line 93**: `from bot.email`
  ```
  'from bot.email': 'from communication.communication_channels.email',
  ```

- **Line 94**: `import bot.communication`
  ```
  'import bot.communication': 'import communication.communication_channels',
  ```

- **Line 95**: `import bot.discord`
  ```
  'import bot.discord': 'import communication.communication_channels.discord',
  ```

- **Line 96**: `import bot.email`
  ```
  'import bot.email': 'import communication.communication_channels.email',
  ```
