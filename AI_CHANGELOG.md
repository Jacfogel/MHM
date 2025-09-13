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

### 2025-09-13 - Logging Style Enforcement + Docs ?. **COMPLETED**
- Fixed remaining multi-arg logger calls (converted to f-strings) and added static check to enforce no more than one positional arg to any `*.logger.*` call
- Extended static logger check to forbid `logging.getLogger(__name__)` in app code (allowed in `core/logger.py`, `tests/`, `scripts/`, `ai_tools/`)
- Updated `core/schemas.py` to use `get_component_logger('main')` for consistency
- Profile/help sanity: commands output links to `DISCORD.md`; profile display verified as formatted text

### 2025-09-13 - Scale Normalization + Discord Docs ?. **COMPLETED**
- Normalized all mood/energy displays to 1–5 across command handlers (status, history, mood trends)
- Added targeted behavior tests asserting “/5” rendering for status, history, and trends
- Introduced `DISCORD.md` with consolidated Discord command reference; linked from in-app commands output
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
