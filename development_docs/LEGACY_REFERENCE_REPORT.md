# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-05-30 21:31:13
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 4
**Legacy Compatibility Markers Detected**: 51

## Summary
- Scan mode only: no automated fixes were applied.
- Changelogs, archive folders, and planning documents are intentionally historical and excluded from this report.
- Legacy compatibility markers remain in 1 file(s) (2 total markers).
- Remaining counts come from legacy inventory tracking categories (3 file(s), 49 marker(s)).

## Recommended Follow-Up
- Additional guidance: [AI_LEGACY_COMPATIBILITY_GUIDE.md](../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md)
1. Identify active legacy compatibility behavior and migrate all callers/dependencies to current implementations before deleting markers.
2. Add or update regression tests that prove migrated flows work without legacy compatibility code paths. See [AI_TESTING_GUIDE.md](../ai_development_docs/AI_TESTING_GUIDE.md) for additional guidance.
3. Only after migration is verified, remove legacy markers/comments/docs evidence and rerun `python development_tools/run_development_tools.py legacy --clean --dry-run` until this report returns zero issues.

## Deprecation Inventory
- Inventory file: `development_tools/config/jsons/DEPRECATION_INVENTORY.json`
- Active/candidate entries: 2
- Removed entries: 27
- Active search terms: 3
- Current inventory-term hits in scan: 4 file(s), 49 marker(s)

## Deprecation Inventory Terms
**Files Affected**: 4

### communication\__init__.py
**Issues Found**: 8

- **Line 70**: `DiscordEventHandler`
  ```
  elif name == 'DiscordEventHandler':
  ```

- **Line 71**: `DiscordEventHandler`
  ```
  from .communication_channels.discord.event_handler import DiscordEventHandler
  ```

- **Line 72**: `DiscordEventHandler`
  ```
  return DiscordEventHandler
  ```

- **Line 91**: `get_discord_event_handler`
  ```
  elif name == 'get_discord_event_handler':
  ```

- **Line 92**: `get_discord_event_handler`
  ```
  from .communication_channels.discord.event_handler import get_discord_event_handler
  ```

- **Line 93**: `get_discord_event_handler`
  ```
  return get_discord_event_handler
  ```

- **Line 224**: `DiscordEventHandler`
  ```
  'DiscordEventHandler',
  ```

- **Line 226**: `get_discord_event_handler`
  ```
  'get_discord_event_handler',
  ```

### communication\communication_channels\discord\event_handler.py
**Issues Found**: 6

- **Line 2**: `DiscordEventHandler`
  ```
  # LEGACY COMPATIBILITY: DiscordEventHandler is deprecated in favor of bot.py handlers
  ```

- **Line 58**: `DiscordEventHandler`
  ```
  class DiscordEventHandler:
  ```

- **Line 355**: `get_discord_event_handler`
  ```
  def get_discord_event_handler(
  ```

- **Line 357**: `DiscordEventHandler`
  ```
  ) -> DiscordEventHandler:
  ```

- **Line 360**: `get_discord_event_handler`
  ```
  "LEGACY COMPATIBILITY: get_discord_event_handler invoked; "
  ```

- **Line 363**: `DiscordEventHandler`
  ```
  return DiscordEventHandler(bot)
  ```

### tests\unit\test_communication_init.py
**Issues Found**: 7

- **Line 341**: `DiscordEventHandler`
  ```
  """Test: DiscordEventHandler can be imported lazily"""
  ```

- **Line 345**: `DiscordEventHandler`
  ```
  # Act: Access DiscordEventHandler (should trigger lazy import)
  ```

- **Line 346**: `DiscordEventHandler`
  ```
  handler = communication.DiscordEventHandler
  ```

- **Line 347**: `get_discord_event_handler`
  ```
  get_handler = communication.get_discord_event_handler
  ```

- **Line 350**: `DiscordEventHandler`
  ```
  assert handler is not None, "DiscordEventHandler should be importable via lazy import"
  ```

- **Line 351**: `get_discord_event_handler`
  ```
  assert get_handler is not None, "get_discord_event_handler should be importable via lazy import"
  ```

- **Line 352**: `get_discord_event_handler`
  ```
  assert callable(get_handler), "get_discord_event_handler should be callable"
  ```

### tests\unit\test_discord_event_handler.py
**Issues Found**: 28

- **Line 4**: `communication/communication_channels/discord/event_handler.py`
  ```
  Tests for communication/communication_channels/discord/event_handler.py:
  ```

- **Line 7**: `DiscordEventHandler`
  ```
  - DiscordEventHandler class
  ```

- **Line 17**: `DiscordEventHandler`
  ```
  DiscordEventHandler,
  ```

- **Line 18**: `get_discord_event_handler`
  ```
  get_discord_event_handler
  ```

- **Line 92**: `DiscordEventHandler`
  ```
  class TestDiscordEventHandler:
  ```

- **Line 93**: `DiscordEventHandler`
  ```
  """Test DiscordEventHandler class"""
  ```

- **Line 107**: `DiscordEventHandler`
  ```
  """Create a DiscordEventHandler instance"""
  ```

- **Line 108**: `DiscordEventHandler`
  ```
  return DiscordEventHandler(mock_bot)
  ```

- **Line 112**: `DiscordEventHandler`
  ```
  """Create a DiscordEventHandler instance without bot"""
  ```

- **Line 113**: `DiscordEventHandler`
  ```
  return DiscordEventHandler(None)
  ```

- **Line 118**: `DiscordEventHandler`
  ```
  """Test: DiscordEventHandler initializes correctly with bot"""
  ```

- **Line 120**: `DiscordEventHandler`
  ```
  handler = DiscordEventHandler(mock_bot)
  ```

- **Line 132**: `DiscordEventHandler`
  ```
  """Test: DiscordEventHandler initializes correctly without bot"""
  ```

- **Line 134**: `DiscordEventHandler`
  ```
  handler = DiscordEventHandler(None)
  ```

- **Line 144**: `DiscordEventHandler`
  ```
  DiscordEventHandler(mock_bot)
  ```

- **Line 157**: `DiscordEventHandler`
  ```
  handler = DiscordEventHandler(mock_bot)
  ```

- **Line 672**: `DiscordEventHandler`
  ```
  class TestGetDiscordEventHandler:
  ```

- **Line 673**: `get_discord_event_handler`
  ```
  """Test get_discord_event_handler factory function"""
  ```

- **Line 677**: `get_discord_event_handler`
  ```
  def test_get_discord_event_handler_with_bot(self):
  ```

- **Line 678**: `get_discord_event_handler`
  ```
  """Test: get_discord_event_handler returns handler with bot"""
  ```

- **Line 683**: `get_discord_event_handler`
  ```
  handler = get_discord_event_handler(mock_bot)
  ```

- **Line 686**: `DiscordEventHandler`
  ```
  assert isinstance(handler, DiscordEventHandler), "Should return DiscordEventHandler"
  ```

- **Line 686**: `DiscordEventHandler`
  ```
  assert isinstance(handler, DiscordEventHandler), "Should return DiscordEventHandler"
  ```

- **Line 691**: `get_discord_event_handler`
  ```
  def test_get_discord_event_handler_without_bot(self):
  ```

- **Line 692**: `get_discord_event_handler`
  ```
  """Test: get_discord_event_handler returns handler without bot"""
  ```

- **Line 694**: `get_discord_event_handler`
  ```
  handler = get_discord_event_handler(None)
  ```

- **Line 697**: `DiscordEventHandler`
  ```
  assert isinstance(handler, DiscordEventHandler), "Should return DiscordEventHandler"
  ```

- **Line 697**: `DiscordEventHandler`
  ```
  assert isinstance(handler, DiscordEventHandler), "Should return DiscordEventHandler"
  ```

## Legacy Compatibility Markers
**Files Affected**: 1

### communication\communication_channels\discord\event_handler.py
**Issues Found**: 2

- **Line 2**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: DiscordEventHandler is deprecated in favor of bot.py handlers
  ```

- **Line 352**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: prefer bot.initialize__register_events extracted handlers.
  ```
