# Duplicate Functions Investigation

> **File**: `development_docs/DUPLICATE_FUNCTIONS_INVESTIGATION.md`  
> **Temporary planning file.** This doc supports refactor planning and audit follow-up. It can be archived or removed once duplicate-group refactors are done and the duplicate-functions report is no longer in active use for prioritization. Do not treat as long-term project documentation.

> **Context**: AI_PRIORITIES.md and `development_tools/functions/jsons/analyze_duplicate_functions_results.json` list duplicate groups from the duplicate-functions analyzer. This document covers all reported groups with verdicts. For exclusion and tool behavior, see [DEVELOPMENT_TOOLS_GUIDE.md](development_tools/DEVELOPMENT_TOOLS_GUIDE.md) (Duplicate function analysis).  
> **Suppressing “Not duplication” groups**: Add the same comment with a group id to **every** function in the group, e.g. `# not_duplicate: format_message`. Only pairs where both functions have that same group id are omitted; any future duplicate without the comment will still be reported. **Markers added**: The groups with verdicts "Intentional polymorphism", "Intentional API pattern", "intentional", "Same pattern; intentional", "Intentional async vs sync", "no action", "Pair ops; intentional", "Channel polymorphism" now have `# not_duplicate: <group_id>` in every function of the group, so they are suppressed in the report (future runs show ~19 groups).

## Audit run (2026-03-14) and pipeline

- **Run**: Full audit with body-for-near-miss enabled. Body similarity runs automatically on name-token pairs that exceed `body_similarity_min_name_threshold` (0.35) but are below the normal reporting bar; high body similarity can still report them.
- **Report**: **30 duplicate groups** across **26 files**. Groups are ordered by **clearest duplicates first** (max similarity, then cluster size) in AI_PRIORITIES and this doc.
- **Details**: `groups_filtered_single_function: 10`, `groups_reported: 30`, `pairs_reported: 70`, `max_groups: 50`. Weights include `body: 0.25` when body similarity is used.
- **Source**: `development_tools/functions/jsons/analyze_duplicate_functions_results.json` (last_generated 2026-03-14).

---

## Summary: All 30 groups (ordered by max similarity, clearest first)

| # | Max | N | File / description | Verdict |
|---|-----|---|--------------------|---------|
| 1 | 0.954 | 3 | message_formatter.py — format_message (MessageFormatter, Text, Email) | Intentional polymorphism |
| 2 | 0.920 | 3 | rich_formatter.py — get_color_for_type (RichFormatter, Discord, Email) | Intentional polymorphism |
| 3 | 0.840 | 9 | user_data_manager.py — backup_user_data, get_user_data_summary, get_user_summary, +6 | Class + module API + helpers; optional refactor for _get_user_data_summary__* |
| 4 | 0.840 | 5 | user_data_manager.py — _get_user_data_summary__process_* (enabled, orphaned, message, log, core) | Same-class helpers; optional shared structure |
| 5 | 0.840 | 2 | user_data_manager.py — update_user_index (class + module) | Intentional API pattern |
| 6 | 0.833 | 2 | notebook_handler.py — _handle_list_by_group, _handle_list_by_tag | Similar handlers; optional shared helper |
| 7 | 0.820 | 3 | user_data_updates.py — update_user_account, update_user_context, update_user_schedules | Parallel updaters; optional shared helper |
| 8 | 0.820 | 2 | tags.py — add_user_tag, remove_user_tag | Pair ops; optional shared helper |
| 9 | 0.809 | 2 | account_creator_dialog.py — AccountCreatorDialog.keyPressEvent, UserProfileDialog.keyPressEvent | Same event override in two dialogs; intentional |
| 10 | 0.800 | 2 | analytics_handler.py, task_handler.py — _handle_task_stats (Analytics, TaskManagement) | Two handlers; may delegate to shared logic |
| 11 | 0.787 | 2 | cache_manager.py — ResponseCache.clear, ContextCache.clear | Same pattern (clear cache); intentional |
| 12 | 0.760 | 2 | channel_orchestrator.py — send_message, send_message_sync | Intentional async vs sync entry points |
| 13 | 0.760 | 2 | message_editor_dialog.py — edit_message_by_row, delete_message_by_row | Different ops (edit vs delete); similar structure |
| 14 | 0.760 | 2 | user_data_manager.py — delete_user_completely (class + module) | Intentional API pattern |
| 15 | 0.752 | 3 | file_operations.py — _create_user_files__preferences_file, __schedules_file, __account_file | Parallel file creators; optional shared helper |
| 16 | 0.752 | 2 | user_data_manager.py — _get_user_data_summary__add_schedule_details, __add_sent_messages_details | Same-class helpers; optional shared structure |
| 17 | 0.740 | 2 | notebook_handler.py — _handle_pin_entry, _handle_archive_entry | Similar handlers; optional shared helper |
| 18 | 0.739 | 5 | user_data_manager.py — _get_user_data_summary__add_* (file_info, message_file_info, missing_message_file_info, special_file_details, +1) | Same-class helpers; optional shared structure |
| 19 | 0.725 | 2 | user_data_write.py — _save_user_data__validate_input, __validate_data | Validation helpers; optional merge |
| 20 | 0.720 | 4 | user_data_registry.py — _get_user_data__load_preferences, __load_schedules, __load_context, __load_account | Parallel loaders; refactored to shared loader pattern |
| 21 | 0.720 | 2 | command_parser.py — _extract_intent_from_ai_response, _extract_entities_from_ai_response | Extraction helpers; optional shared helper |
| 22 | 0.719 | 2 | chatbot.py — generate_response, generate_contextual_response | Related but distinct entry points; no action |
| 23 | 0.712 | 2 | user_item_storage.py — load_user_json_file, save_user_json_file | Pair ops (load/save); intentional |
| 24 | 0.705 | 2 | service.py — _check_test_message_requests__cleanup_request_file, _check_reschedule_requests__cleanup_request_file | Parallel cleanup helpers; optional shared |
| 25 | 0.703 | 2 | auto_cleanup.py — _perform_cleanup__remove_cache_files, __remove_cache_files_list | Overload/variant; optional merge |
| 26 | 0.703 | 2 | cache_manager.py — ResponseCache.clear_expired, ContextCache.clear_expired | Same pattern; intentional |
| 27 | 0.703 | 2 | cache_manager.py — get_entries_by_type, remove_entries_by_type | Different ops (get vs remove); similar structure |
| 28 | 0.700 | 2 | discord/bot.py — DiscordBot.send_message, EmailBot.send_message | Channel polymorphism |
| 29 | 0.682 | 2 | welcome_manager.py — get_welcome_message (two definitions) | Core vs channel-specific; intentional |
| 30 | 0.642 | 2 | user_data_read.py — clear_user_caches (two definitions) | Same name; verify if intentional overload or true duplicate |

*Single-function (self-pair) groups are filtered out (10 in this run).*

---

## Group 1: format_message (message_formatter.py) — max 0.954

**Functions**: MessageFormatter.format_message (abstract), TextMessageFormatter.format_message, EmailMessageFormatter.format_message.

**Verdict: Not duplication — intentional polymorphism.**

MessageFormatter is the abstract base; Text produces plain text (Markdown-style); Email produces HTML. Same structure (title, fields, footer), different output by design. No refactor needed.

---

## Group 2: get_color_for_type (rich_formatter.py) — max 0.920

**Functions**: RichFormatter.get_color_for_type (abstract), DiscordRichFormatter.get_color_for_type, EmailRichFormatter.get_color_for_type.

**Verdict: Not duplication — intentional polymorphism.**

Abstract base plus channel-specific implementations (Discord colour int, Email HTML hex). No action.

---

## Groups 3–5, 14, 16, 18: user_data_manager.py — class + module and _get_user_data_summary__* helpers

**Pattern**: Module-level functions (backup_user_data, get_user_data_summary, delete_user_completely, update_user_index, etc.) are the public API; they validate inputs and call `UserDataManager().method()`. Class holds implementation. **Do not merge** class and module-level; this is intentional.

**Groups 4, 16, 18**: `_get_user_data_summary__process_*` and `_get_user_data_summary__add_*` are same-class helpers with similar structure. **Optional refactor**: extract shared structure (e.g. loop over file types, add-to-summary pattern) if it reduces duplication without obscuring intent.

**Group 3**: Includes get_user_data_summary, get_user_summary, backup_user_data, and other helpers. Class + module API + internal helpers; largest cluster. Refactor only the internal helpers if desired (see groups 4, 16, 18).

---

## Groups 6, 17: NotebookHandler — _handle_list_by_*, _handle_pin_entry, _handle_archive_entry

**Verdict: Similar handlers; optional shared helper.**

Same handler pattern (user_id, entities, response). Could extract a small shared helper for the common flow; low priority.

---

## Groups 9, 11, 26, 28: Intentional patterns (keyPressEvent, cache clear, send_message)

**Group 9**: AccountCreatorDialog.keyPressEvent, UserProfileDialog.keyPressEvent — same event override in two dialogs; intentional.

**Groups 11, 26**: ResponseCache.clear / clear_expired, ContextCache.clear / clear_expired — same pattern across cache classes; intentional.

**Group 28**: DiscordBot.send_message, EmailBot.send_message — channel polymorphism. No action.

---

## Group 12: send_message vs send_message_sync

**Verdict: Intentional async vs sync.**

Async and sync entry points by design. No refactor.

---

## Group 20: _get_user_data__load_* (user_data_registry.py)

**Verdict: Refactored.**

Parallel loaders were refactored to shared loader pattern in user_data_registry. No further action unless new duplication appears.

---

## Groups 13, 27: Different operations, similar structure

**Group 13**: edit_message_by_row vs delete_message_by_row — different ops (edit vs delete); similar structure. Optional shared helper only if logic converges.

**Group 27**: get_entries_by_type vs remove_entries_by_type — same. No action unless consolidating.

---

## Recommendations

1. **No action (polymorphism or intentional pattern)**: Groups 1, 2, 5, 9, 11, 12, 14, 22, 23, 26, 28, 29 (format_message, get_color_for_type, user_data_manager class+module, keyPressEvent, cache clear/send_message, load/save pair, etc.).
2. **Optional refactor (shared structure)**: Groups 3, 4, 6, 7, 8, 10, 15, 16, 17, 18, 19, 21, 24, 25 — extract shared helpers only where it clearly reduces duplication and preserves clarity.
3. **Verify**: Group 30 (clear_user_caches twice in user_data_read.py) — confirm whether two definitions are intentional or a true duplicate.
4. **Single-function groups**: Filtered out by the tool (10 in this run).

---

*Source: analyze_duplicate_functions_results.json (duplicate_groups). Last audit run: 2026-03-14 (30 groups, 26 files, body-for-near-miss enabled).*

---

## Overlap with AI_PRIORITIES (current 19-group report)

After `# not_duplicate: <group_id>` markers were added, the duplicate-functions report shows **19 groups** across **16 files**. AI_PRIORITIES item 3 ("Investigate possible duplicate functions/methods") calls out the same set; the table below maps its **top target groups** to this doc’s verdicts and actions.

| AI_PRIORITIES group | N funcs | Max score | Maps to (this doc) | Verdict / action |
|---------------------|--------|-----------|---------------------|------------------|
| Group 1             | 9      | 0.84      | Groups 3–5, 14, 16, 18 (user_data_manager) | Class + module API intentional; **optional** refactor only for `_get_user_data_summary__*` helpers (see Group 2). |
| Group 2             | 5      | 0.84      | Group 4 (`_get_user_data_summary__process_*`) | Same-class helpers; **optional** shared structure (loop / add-to-summary pattern). |
| Group 3             | 2      | 0.833     | Group 6 (NotebookHandler `_handle_list_by_group`, `_handle_list_by_tag`) | Similar handlers; **optional** shared helper. |

**Action plan (items with overlap):**

1. **NotebookHandler (Group 6 / AI_PRIORITIES Group 3)** — **Done.** Extracted `_build_paginated_list_response()`; `_handle_list_by_group` and `_handle_list_by_tag` now delegate to it.
2. **user_data_manager `_get_user_data_summary__*` (Groups 4, 16, 18 / AI_PRIORITIES Groups 1–2)** — **Done.** Extracted `_get_user_data_summary__process_file_types_with_adder()` (loop over file types, call adder if path exists) and `_get_user_data_summary__add_core_file_info()` (file_info + special_file_details). `process_core_files` and `process_log_files` now use the shared loop; message-file process_* left as-is (different data sources and intent).
3. **Remaining 19-group items** — No action for intentional patterns; optional refactor for other “optional shared helper” groups per the summary table and Recommendations above.
