# Duplicate Functions Investigation

> **Temporary planning file.** This doc supports refactor planning and audit follow-up. It can be archived or removed once duplicate-group refactors are done and the duplicate-functions report is no longer in active use for prioritization. Do not treat as long-term project documentation.

> **Context**: AI_PRIORITIES.md and `development_tools/functions/jsons/analyze_duplicate_functions_results.json` list duplicate groups from the duplicate-functions analyzer. This document covers all reported groups with verdicts.

## Audit run (2026-02-06 full audit) and pipeline fix

- **Were there really 11 false positives?** Yes. Those 11 were clusters with only one unique function (same function compared with itself), e.g. when the same function appeared twice in the record list (path format differences so dedupe did not merge them). The tool is not too restrictive; single-function "groups" are not real duplicates. Path normalization was added so future runs may dedupe more.
- **Showing 50 results?** The report shows **14 groups**, not 50. There are only 14 multi-function duplicate groups in the codebase after filtering. The config default `max_groups` is 50, so the tool *can* report up to 50 groups if that many exist; this run used `max_groups: 25` (from the run’s config) and reported 14, so the cap was not hit. To see more in future (if new duplicates appear), use `--max-groups 50` or rely on the default.
- **Was it "first 25, then drop 11, leaving 14"?** Yes. That was a bug; the pipeline used to cap by max_groups then filter. **Fixed**: filter to multi-function first, then apply max_groups, so we report the top N real duplicate groups (up to 50 by default).
- **Showing 50 results?** With max_groups=50 (config and development_tools_config.json in sync), the report now shows **29 groups** (29 multi-function duplicate groups in the codebase). Cap was not hit.
- **Details from last run**: `records_deduplicated: 0`, `groups_filtered_single_function: 11`, `groups_reported: 29`, `files_affected: 26`, `max_groups: 50` (development_tools_config.json now in sync with config.py).

## Summary: All 29 Groups (current report, 2026-02-06 audit)

| # | Function(s) / description | Verdict |
|---|---------------------------|---------|
| 1 | format_message (MessageFormatter, Text, Email) | Intentional polymorphism |
| 2 | remove_period_row (Checkin, Task, Schedule UI) | Copy-paste; optional refactor |
| 3 | add_new_period (same three UIs) | Copy-paste; optional refactor |
| 4 | _is_valid_intent (EnhancedCommandParser, InteractionManager) | Parallel impl; optional shared helper |
| 5 | get_color_for_type (RichFormatter, Discord, Email) | Intentional polymorphism |
| 6 | _handle_*__find_task_by_identifier (complete/delete/update) | Thin wrappers; optional refactor |
| 7 | _initialize_channel_with_retry vs _sync | Intentional async vs sync |
| 8 | _create_command_parsing_prompt vs _with_clarification | Near-duplicate; optional merge |
| 9 | update_message_references (class + module) | Intentional API pattern |
| 10 | backup_user_data (class + module) | Intentional API pattern |
| 11 | delete_user_completely (class + module) | Intentional API pattern |
| 12 | export_user_data (class + module) | Intentional API pattern |
| 13 | register_with_platform (CommandRegistry, Discord, Email) | Intentional polymorphism |
| 14 | get_user_data_summary (class + module + helper) | Class + module API + helper |
| 15 | update_user_index (class + module) | Intentional API pattern |
| 16 | _get_user_data_summary__process_enabled_message_files, __process_orphaned_message_files | Same-class helpers; optional shared structure |
| 17 | NotebookHandler._handle_list_by_group, _handle_list_by_tag | Similar handlers; optional shared helper |
| 18 | AccountCreatorDialog.keyPressEvent, UserProfileDialog.keyPressEvent | Same event override in two dialogs; intentional |
| 19 | ResponseCache.get_entries_by_type, remove_entries_by_type | Different ops (get vs remove); similar structure |
| 20 | _get_user_data__load_account, load_context, load_preferences, load_schedules (user_data_handlers) | Parallel loaders; good refactor candidate (shared loader pattern) |
| 21 | AnalyticsHandler._handle_task_stats, TaskManagementHandler._handle_task_stats | Two handlers; may delegate to shared logic |
| 22 | ResponseCache.clear, ContextCache.clear | Same pattern (clear cache); intentional |
| 23 | get_welcome_message (welcome_manager, discord welcome_handler) | Core vs channel-specific; intentional |
| 24 | DiscordBot.send_message, EmailBot.send_message | Channel polymorphism |
| 25 | find_lowest_available_period_number (Checkin, Task widgets) | Copy-paste; optional refactor (same as add/remove period) |
| 26 | get_user_summary, get_user_analytics_summary | Related but distinct; no action |
| 27 | SchedulerManager.cleanup_task_reminders, cleanup_task_reminders (module) | Class + module pattern |
| 28 | PromptManager.get_prompt, get_prompt_template | Related methods; no action |
| 29 | MessageEditorDialog.edit_message_by_row, delete_message_by_row | Different operations (edit vs delete); similar structure |

*Single-function (self-pair) groups are filtered out (11 in this run).*

---

## Group 1: format_message (message_formatter.py)

**Functions**: MessageFormatter.format_message (abstract), TextMessageFormatter.format_message, EmailMessageFormatter.format_message.

**Verdict: Not duplication — intentional polymorphism.**

MessageFormatter is the abstract base; Text produces plain text (Markdown-style); Email produces HTML. Same structure (title, fields, footer), different output by design. No refactor needed.

---

## Group 2: remove_period_row (3 files)

**Locations**: CheckinSettingsWidget, TaskSettingsWidget, ScheduleEditorDialog.

**Verdict: Copy-paste with small, intentional differences. Optional refactor.**

Same core flow (store deleted data, remove from layout, deleteLater, remove from list). Differences: which layout attribute; Checkin has “cannot delete last period” guard; ScheduleEditor has “cannot delete ALL period” guard for non-task/checkin. A shared helper with (layout, period_widgets, deleted_periods, guard_fn) could reduce duplication.

---

## Group 3: add_new_period (3 files)

**Locations**: Same three classes as Group 2.

**Verdict: Copy-paste with parameterized differences. Optional refactor.**

Common flow: default period_name/period_data, create PeriodRowWidget, connect delete_requested, add to layout, append to period_widgets. Differences: default name prefix, which layout; ScheduleEditor also sets creation_order and calls resort_period_widgets(). Existing shared pieces: load_period_widgets_for_category, collect_period_data_from_widgets in core/ui_management.py.

---

## Group 14: _is_valid_intent (2 funcs)

**Locations**: EnhancedCommandParser (command_parser.py), InteractionManager (interaction_manager.py).

**Verdict: Parallel implementation — optional shared helper.**

Both loop over self.interaction_handlers.values() and return True if any handler.can_handle(intent). Logic is identical. Could extract a small shared helper in message_processing.

---

## Group 15: get_color_for_type (3 funcs)

**Locations**: RichFormatter (abstract), DiscordRichFormatter, EmailRichFormatter (rich_formatter.py).

**Verdict: Not duplication — intentional polymorphism.**

Abstract base plus channel-specific implementations (Discord colour int, Email HTML hex). No action.

---

## Group 16: _handle_*__find_task_by_identifier (3 funcs)

**Locations**: TaskManagementHandler (task_handler.py) — complete, delete, update.

**Verdict: Thin wrappers — optional refactor.**

All three delegate to self._find_task_by_identifier(tasks, identifier). Only difference is @handle_errors message. Could use a single method with context for the decorator.

---

## Group 17: _initialize_channel_with_retry vs _initialize_channel_with_retry_sync

**Locations**: CommunicationManager (channel_orchestrator.py).

**Verdict: Intentional async vs sync — no refactor.**

Async uses await and asyncio.sleep; sync uses run_until_complete and time.sleep. Two entry points by design. No action.

---

## Group 18: _create_command_parsing_prompt vs _create_command_parsing_with_clarification_prompt

**Locations**: AIChatBotSingleton (chatbot.py).

**Verdict: Near-duplicate — optional merge.**

Both build [system_message, user_message] with prompt_manager.get_prompt("command"). Only differences are docstring and @handle_errors default_return. Could merge with a clarification: bool = False parameter; low priority.

---

## Note: Single-function groups (formerly 19–20)

Single-function “duplicate” groups (same function compared with itself) are **no longer reported**. The analyzer filters them out (`groups_filtered_single_function` in the JSON). In the 2026-02-06 run, 11 such groups were filtered.

---

## Groups 9–12: user_data_manager — class method + module-level function

**Functions**: update_message_references, backup_user_data, delete_user_completely, export_user_data.

**Locations**: UserDataManager class + module-level convenience functions (core/user_data_manager.py).

**Verdict: Intentional pattern — not duplication.**

Module-level functions are the public API (validate inputs, then call UserDataManager().method()). Class holds implementation; module-level provides validation and stable top-level API. Do not merge.

---

## Group 25: register_with_platform (3 funcs)

**Locations**: CommandRegistry (abstract), DiscordCommandRegistry, EmailCommandRegistry (command_registry.py).

**Verdict: Not duplication — intentional polymorphism.**

Base defines contract; Discord and Email implement platform-specific registration. No action.

---

## Group 25 (last): get_user_data_summary (3 funcs)

**Locations**: UserDataManager.get_user_data_summary, module-level get_user_data_summary, UserDataManager._get_user_data_summary__initialize_summary.

**Verdict: Class + module wrapper + internal helper.**

Same pattern as groups 21–24 for the first two. The third is an internal helper grouped by name/args similarity. No refactor needed.

---

## Recommendations

1. **No action (polymorphism or intentional pattern)**: Groups 1, 5, 13 (format_message, get_color_for_type, register_with_platform); 9–12, 15 (user_data_manager class+module); 7 (async vs sync); 14 (get_user_data_summary); 18 (keyPressEvent); 22 (cache clear); 23 (get_welcome_message core vs discord); 24 (DiscordBot/EmailBot send_message); 26–28.
2. **Optional refactor (copy-paste or thin wrappers)**: Groups 2, 3, 25 (period row add/remove and find_lowest_available_period_number in Checkin/Task/Schedule UI); Group 4 (_is_valid_intent); Group 6 (find_task_by_identifier); Group 8 (command parsing prompt merge); Group 20 (_get_user_data__load_* in user_data_handlers).
3. **Optional (similar structure, different ops)**: Groups 16, 19, 21, 29 — shared helper only if logic actually converges.
4. **Single-function groups**: Filtered out by the tool (11 in this run).

---

*Source: analyze_duplicate_functions_results.json (duplicate_groups) and AI_PRIORITIES.md. See TODO.md for refactor tasks. Last audit run: 2026-02-06 (29 groups, max_groups=50, 11 single-function groups filtered).*
