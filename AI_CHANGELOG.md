# AI Changelog - Brief Summaries for AI Context

> Purpose: Provide AI assistants with concise summaries of recent changes and current system state  
> Audience: AI collaborators (Cursor, Codex, etc.)  
> Style: Brief, action-oriented, scannable

This file contains brief summaries of recent changes for AI context.
For complete detailed changelog history, see CHANGELOG_DETAIL.md.

## How to Add Changes

When adding new changes to this brief changelog, follow this format:

```markdown
### YYYY-MM-DD - Brief Title ✅. **COMPLETED**
- Key accomplishment or fix in one sentence
- Additional important details if needed
- Impact or benefit of the change
```

Guidelines:
- Keep entries concise and action‑oriented
- Focus on what was accomplished and why it matters
- Entries should generally be limited to a maximum of 1 per day, if an entry already exists for the current day you can edit it to include additional updates. Exceptions may be made for multiple unrelated changes
- Maintain chronological order (most recent first)
- REMOVE OLDER ENTRIES when adding new ones to keep context short
- Target 10–15 recent entries maximum for optimal AI context window usage

------------------------------------------------------------------------------------------
## Recent Changes (Most Recent First)

### 2025-09-14 - Minor Logging Enhancements to Core Modules ✅. **COMPLETED**
- Enhanced logging in `core/schedule_utilities.py` with detailed schedule processing and activity tracking
- Enhanced logging in `ai/context_builder.py` with context building, analysis, and prompt creation tracking
- Enhanced logging in `ai/prompt_manager.py` with prompt loading, retrieval, and creation tracking
- Added comprehensive debug and warning logs to track data flow, validation outcomes, and operational steps
- **Impact**: Better visibility into schedule processing, AI context building, and prompt management for debugging and monitoring

### 2025-09-14 - Enhanced Message Logging with Content and Time Period ✅. **COMPLETED**
- Added message content preview (first 50 characters) to all message sending logs
- Added time period information to message sending logs for better debugging and monitoring
- Enhanced logging in channel orchestrator, Discord bot, and email bot for comprehensive message tracking
- Improved log format includes user ID, category, time period, and message content preview
- **Impact**: Much better visibility into what messages are being sent, when, and to whom for debugging and monitoring

### 2025-09-14 - Discord Channel ID Parsing Fix ✅. **COMPLETED**
- Fixed channel ID parsing error in `send_message_sync` method that was trying to convert `discord_user:` format to integer
- Added proper handling for `discord_user:` format in sync Discord message sending fallback
- Messages were still being delivered successfully via async fallback, but sync method was logging unnecessary errors
- **Impact**: Eliminates "invalid literal for int()" errors in channel orchestrator logs while maintaining message delivery

### 2025-09-14 - Critical Logging Issues Resolution ✅. **COMPLETED**
- Fixed Windows file locking during log rotation that was causing app.log and errors.log to stop updating
- Improved `BackupDirectoryRotatingFileHandler` with better Windows file handling and recovery mechanisms
- Added `clear_log_file_locks()` and `force_restart_logging()` functions for logging system recovery
- Fixed error logging configuration to properly route errors to errors.log via component loggers
- **Impact**: Both app.log and errors.log now update properly, essential for debugging and system monitoring

### 2025-09-14 - Discord Command Processing Fix ✅. **COMPLETED**
- Fixed critical issue where Discord bot was not processing `!` and `/` commands due to incorrect command handling
- Removed `return` statement in Discord bot's `on_message` event that was preventing commands from reaching the interaction manager
- Commands were being processed by Discord's built-in system and then discarded instead of going through our custom command handling
- Added enhanced logging to track command detection and processing flow
- **Impact**: Both `!help` and `/help` commands now work correctly, providing users with proper command discovery and functionality

### 2025-09-13 - Checkin Flow State Persistence and Overwrite Fix ✅. **COMPLETED**
- Fixed critical issue where checkin flows were lost on system restart due to in-memory state storage
- Added persistent storage for conversation flow states in `data/conversation_states.json`
- Fixed checkin flow overwrite issue - new checkins were silently overwriting existing active checkins
- Added protection against starting new checkins when one is already active
- Added `/restart` command to explicitly restart checkin flows when needed
- Reduced overly aggressive checkin cancellation - only cancels for truly interfering message types
- **Impact**: Users can now complete checkins even if system restarts during the flow, and won't lose progress to accidental overwrites

### 2025-09-13 - AI Response Quality and Command Parsing Fixes ✅. **COMPLETED**
- Fixed duplicate AI processing and inappropriate command classification for emotional distress messages
- Enhanced command parsing logic to skip AI calls for clearly non-command messages (confidence = 0.0)
- Disabled AI enhancement for help commands to prevent duplicate processing
- Updated AI prompts with conversational engagement guidelines to always leave natural openings
- Eliminated inappropriate data responses to emotional pleas; now provides empathetic support
- **Remaining**: Message truncation and need for stronger conversational endings

### 2025-09-13 - Logging Style Enforcement + Docs ?. **COMPLETED**
- Fixed remaining multi-arg logger calls (converted to f-strings) and added static check to enforce no more than one positional arg to any `*.logger.*` call
- Extended static logger check to forbid `logging.getLogger(__name__)` in app code (allowed in `core/logger.py`, `tests/`, `scripts/`, `ai_tools/`)
- Updated `core/schemas.py` to use `get_component_logger('main')` for consistency
- Profile/help sanity: profile display verified as formatted text; general help points users to in-app 'commands' instead of docs

### 2025-09-13 - Scale Normalization + Discord Docs ?. **COMPLETED**
- Normalized all mood/energy displays to 1–5 across command handlers (status, history, mood trends)
- Added targeted behavior tests asserting “/5” rendering for status, history, and trends
- Introduced `DISCORD.md` with consolidated Discord command reference (developer/admin doc); in-app commands do not reference docs directly
- Cleaned `QUICK_REFERENCE.md` to point to `DISCORD.md` instead of duplicating commands

### 2025-09-12 - Commands Help + Report Length Safeguard ✅ COMPLETED
- Added concise in-bot command list (help + new `commands` intent) sourced from central registry
- Excluded report-style intents (analytics/profile/schedule/messages/status) from AI enhancement to avoid truncation
- Full suite green: 1405 passed, 1 skipped

### 2025-09-12 - Analytics Scale Normalization (Mood/Energy) ✅ PARTIAL
- Mood displays updated to 1–5 in analytics overview/trends/history; energy adjusted to 1–5 in history
- Follow-up: sweep legacy handlers for any remaining `/10` occurrences (tracked in TODO.md)

Note: Trimmed to the most recent entries for context. Older items are archived in CHANGELOG_DETAIL.md.

### 2025-09-11 - Critical Test Issues Resolution ✅. **COMPLETED**
- Fixed data persistence issue in `test_integration_scenarios_real_behavior` (invalid category name)
- Stopped lingering CommunicationManager threads via session cleanup fixture
- Completed 6‑seed validation; throttler test expectation corrected

### 2025-09-11 - Test Coverage Expansion Phase 3 Completion ✅. **COMPLETED**
- Expanded targeted coverage: logger (75%), error handling (65%), config (79%), command parser (68%), email bot (91%)
- Maintained 99.9% suite success rate (1404/1405)

### 2025-09-10 - Test Coverage Expansion Phase 2 Completion ✅. **COMPLETED**
- Core service coverage to 40%; message management tests added
- Focus on reliable tests; removed flaky patterns

### 2025-09-10 - Health Category Message Filtering Fix and Weighted Selection ✅. **COMPLETED**
- Added 'ALL' time period to applicable health messages; implemented 70/30 weighted selector
- Verified via Discord delivery; maintained backward compatibility

### 2025-09-10 - Message Deduplication System Implementation ✅. **COMPLETED**
- Implemented chronological storage + inline dedupe (60‑day window); integrated with monthly archiving
- Migrated 1,473 messages; consolidated functions in `message_management.py`

### 2025-09-10 - Message Deduplication Consolidation and Structure Improvements ✅. **COMPLETED**
- Cleaned up legacy structure, ensured per‑user message files and archiving flow

### 2025-09-09 - Test Suite Stabilization – Green Run with 6‑Seed Loop ✅. **COMPLETED**
- Full suite green across randomized seeds; logging/test environment defaults solidified

### 2025-09-07 - Test Suite Stabilization and Runner Defaults ✅. **COMPLETED**
- Set UTF‑8, default seed, and test‑time shims; one‑command green runs

### 2025-09-06 - Intermittent Test Failures Resolved; Suite Stable (1141/1) ✅. **COMPLETED**
- Loader registration guard and isolation fixes; eliminated flakiness

### Test Suite Stabilization and Deterministic User‑Data Loading
- Standardized temp paths, env guardrails, idempotent loader registration; suite stable

### 2025-09-05 - Test Suite Stabilization Completed; 1141 Passing ✅. **COMPLETED**
- Session‑wide temp routing; path sanitizer; fixtures refactored; suite green

### 2025-09-03 - Reliability Fixes – Temp Directory and Loader Issues ✅. **COMPLETED**
- Removed `redirect_tempdir`; added `fix_user_data_loaders` fixture; localized file creation
