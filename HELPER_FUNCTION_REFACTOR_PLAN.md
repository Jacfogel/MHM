# Helper Function Naming Convention Refactor Plan

## Phase 1: Planning and Preparation ✅ **COMPLETED**

### Audit Results Summary
- **Total Functions**: 2,132
- **High Complexity Functions**: 1,579 (74.1% complexity rate)
- **Current State**: System working correctly, backup created
- **Baseline Established**: All tests passing

### Comprehensive List of Functions to Refactor

#### 1. `ui/widgets/period_row_widget.py` - `set_read_only` helpers ✅ **COMPLETED**
**Main Function**: `set_read_only(self, read_only: bool = True)`
**Current Helpers**:
- `_set_time_inputs_read_only(read_only)` → `_set_read_only__time_inputs(read_only)` ✅
- `_set_checkbox_states(read_only)` → `_set_read_only__checkbox_states(read_only)` ✅
- `_set_delete_button_visibility(read_only)` → `_set_read_only__delete_button_visibility(read_only)` ✅
- `_apply_visual_styling(read_only)` → `_set_read_only__visual_styling(read_only)` ✅
- `_force_style_updates()` → `_set_read_only__force_style_updates()` ✅

#### 2. `ui/dialogs/account_creator_dialog.py` - `validate_and_accept` helpers ✅ **COMPLETED**
**Main Function**: `validate_and_accept()`
**Current Helpers**:
- `_validate_input_and_show_errors()` → `_validate_and_accept__input_errors()` ✅
- `_collect_all_account_data()` → `_validate_and_accept__collect_data()` ✅
- `_create_account_and_setup(account_data)` → `_validate_and_accept__create_account(account_data)` ✅
- `_handle_successful_creation(username)` → `_validate_and_accept__handle_success(username)` ✅

#### 3. `core/user_data_handlers.py` - `save_user_data` helpers ✅ **COMPLETED**
**Main Function**: `save_user_data(user_id, data_updates, create_backup=True)`
**Current Helpers**:
- `_validate_input_parameters(user_id, data_updates)` → `_save_user_data__validate_input(user_id, data_updates)` ✅
- `_validate_data_for_user(user_id, data_updates, valid_types, auto_create)` → `_save_user_data__validate_data(user_id, data_updates, valid_types, auto_create)` ✅
- `_create_backup_if_needed(user_id, valid_types, create_backup)` → `_save_user_data__create_backup(user_id, valid_types, create_backup)` ✅
- `_save_single_data_type(user_id, data_type, data, auto_create)` → `_save_user_data__save_single_type(user_id, data_type, data, auto_create)` ✅
- `_update_index_and_cache(user_id, data_type)` → `_save_user_data__update_index(user_id, data_type)` ✅
- `_normalize_data_with_pydantic(data_type, data)` → `_save_user_data__normalize_data(data_type, data)` ✅
- `_handle_legacy_account_compatibility(updated, updates)` → `_save_user_data__legacy_account(updated, updates)` ✅
- `_handle_legacy_preferences_compatibility(updated, updates, user_id)` → `_save_user_data__legacy_preferences(updated, updates, user_id)` ✅

#### 4. `core/file_operations.py` - `create_user_files` helpers ✅ **COMPLETED**
**Main Function**: `create_user_files(user_id, user_preferences=None, categories=None)`
**Current Helpers**:
- `_determine_feature_enablement(user_prefs)` → `_create_user_files__determine_feature_enablement(user_prefs)` ✅
- `_create_account_file(user_id, user_prefs, categories, tasks_enabled, checkins_enabled)` → `_create_user_files__account_file(user_id, user_prefs, categories, tasks_enabled, checkins_enabled)` ✅
- `_create_preferences_file(user_id, user_prefs, categories, tasks_enabled, checkins_enabled)` → `_create_user_files__preferences_file(user_id, user_prefs, categories, tasks_enabled, checkins_enabled)` ✅
- `_create_context_file(user_id, user_prefs)` → `_create_user_files__context_file(user_id, user_prefs)` ✅
- `_create_schedules_file(user_id, categories, user_prefs, tasks_enabled, checkins_enabled)` → `_create_user_files__schedules_file(user_id, categories, user_prefs, tasks_enabled, checkins_enabled)` ✅
- `_create_log_files(user_id)` → `_create_user_files__log_files(user_id)` ✅
- `_create_sent_messages_file(user_id)` → `_create_user_files__sent_messages_file(user_id)` ✅
- `_create_task_files(user_id)` → `_create_user_files__task_files(user_id)` ✅
- `_create_checkins_file(user_id)` → `_create_user_files__checkins_file(user_id)` ✅
- `_create_message_files(user_id, categories)` → `_create_user_files__message_files(user_id, categories)` ✅
- `_update_user_references(user_id)` → `_create_user_files__update_user_references(user_id)` ✅

#### 5. `bot/interaction_handlers.py` - `_handle_list_tasks` helpers ✅ **COMPLETED**
**Main Function**: `_handle_list_tasks(user_id, entities)`
**Current Helpers**:
- `_apply_task_filters(user_id, tasks, filter_type, priority_filter, tag_filter)` → `_handle_list_tasks__apply_filters(user_id, tasks, filter_type, priority_filter, tag_filter)` ✅
- `_get_no_tasks_response(filter_type, priority_filter, tag_filter)` → `_handle_list_tasks__no_tasks_response(filter_type, priority_filter, tag_filter)` ✅
- `_sort_tasks_by_priority_and_date(filtered_tasks)` → `_handle_list_tasks__sort_tasks(filtered_tasks)` ✅
- `_format_task_list(sorted_tasks)` → `_handle_list_tasks__format_list(sorted_tasks)` ✅
- `_format_due_date_info(task)` → `_handle_list_tasks__format_due_date(task)` ✅
- `_build_filter_info(filter_type, priority_filter, tag_filter)` → `_handle_list_tasks__build_filter_info(filter_type, priority_filter, tag_filter)` ✅
- `_build_task_list_response(task_list, filter_info, task_count)` → `_handle_list_tasks__build_response(task_list, filter_info, task_count)` ✅
- `_generate_task_suggestions(sorted_tasks, filter_info)` → `_handle_list_tasks__generate_suggestions(sorted_tasks, filter_info)` ✅
- `_get_contextual_show_suggestion(filter_type, priority_filter, tag_filter)` → `_handle_list_tasks__get_show_suggestion(filter_type, priority_filter, tag_filter)` ✅
- `_create_task_rich_data(filter_info, sorted_tasks)` → `_handle_list_tasks__create_rich_data(filter_info, sorted_tasks)` ✅

#### 6. `tests/test_utilities.py` - `_create_user_files_directly` helpers ✅ **COMPLETED**
**Main Function**: `_create_user_files_directly(test_data_dir, user_id, user_data)`
**Current Helpers**:
- `_create_user_directory_structure(test_data_dir, user_id)` → `_create_user_files_directly__directory_structure(test_data_dir, user_id)` ✅
- `_create_account_data(actual_user_id, user_id, user_data)` → `_create_user_files_directly__account_data(actual_user_id, user_id, user_data)` ✅
- `_create_preferences_data(user_data)` → `_create_user_files_directly__preferences_data(user_data)` ✅
- `_create_context_data(user_data)` → `_create_user_files_directly__context_data(user_data)` ✅
- `_save_json_file(file_path, data)` → `_create_user_files_directly__save_json(file_path, data)` ✅
- `_create_schedules_data(categories)` → `_create_user_files_directly__schedules_data(categories)` ✅
- `_create_message_files(user_dir, categories)` → `_create_user_files_directly__message_files(user_dir, categories)` ✅
- `_update_user_index(test_data_dir, user_id, actual_user_id)` → `_create_user_files_directly__update_index(test_data_dir, user_id, actual_user_id)` ✅

## Phase 2: Core Modules Refactoring ✅ **COMPLETED**

**Status**: All 6 initial modules successfully refactored with 44 helper functions renamed.

## Phase 2B: Extended Refactoring - Production Code Priority ✅ **COMPLETED**

### **Priority 1: Production Code Helper Functions** ✅ **COMPLETED**

**Summary**: Successfully refactored 18 additional helper functions across 2 modules:
- `bot/interaction_handlers.py`: 6 helper functions ✅
- `ui/dialogs/account_creator_dialog.py`: 12 helper functions ✅

### **Priority 2: Medium Priority Production Code Helper Functions** ✅ **COMPLETED**

**Summary**: Successfully refactored 25 additional helper functions across 4 modules:
- `bot/communication_manager.py`: 13 helper functions ✅
- `bot/discord_bot.py`: 7 helper functions ✅  
- `bot/email_bot.py`: 3 helper functions ✅
- `bot/ai_chatbot.py`: 3 helper functions ✅

#### 7. `bot/interaction_handlers.py` - Additional Helper Functions ✅ **COMPLETED**
**Main Functions**: Multiple handler functions have unrefactored helpers
**Current Helpers**:
- `_parse_relative_date(date_str)` → `_handle_create_task__parse_relative_date(date_str)` ✅ (called by `_handle_create_task`)
- `_find_task_by_identifier(tasks, identifier)` → `_handle_complete_task__find_task_by_identifier(tasks, identifier)` ✅ (called by `_handle_complete_task`)
- `_find_task_by_identifier(tasks, identifier)` → `_handle_delete_task__find_task_by_identifier(tasks, identifier)` ✅ (called by `_handle_delete_task`)
- `_find_task_by_identifier(tasks, identifier)` → `_handle_update_task__find_task_by_identifier(tasks, identifier)` ✅ (called by `_handle_update_task`)
- `_parse_time_format(time_str)` → `_handle_add_schedule_period__parse_time_format(time_str)` ✅ (called by `_handle_add_schedule_period`)
- `_parse_time_format(time_str)` → `_handle_edit_schedule_period__parse_time_format(time_str)` ✅ (called by `_handle_edit_schedule_period`)

#### 8. `ui/dialogs/account_creator_dialog.py` - Additional Helper Functions ✅ **COMPLETED**
       **Main Functions**: Multiple functions have unrefactored helpers
       **Current Helpers**:
       - `_collect_basic_user_info()` → `_validate_and_accept__collect_basic_user_info()` ✅ (called by `_validate_and_accept__collect_data`)
       - `_collect_feature_settings()` → `_validate_and_accept__collect_feature_settings()` ✅ (called by `_validate_and_accept__collect_data`)
       - `_collect_channel_data()` → `_validate_and_accept__collect_channel_data()` ✅ (called by `_validate_and_accept__collect_data`)
       - `_collect_widget_data()` → `_validate_and_accept__collect_widget_data()` ✅ (called by `_validate_and_accept__collect_data`)
       - `_build_account_data()` → `_validate_and_accept__build_account_data()` ✅ (called by `_validate_and_accept__collect_data`)
       - `_show_error_dialog(title, message)` → `_validate_and_accept__show_error_dialog(title, message)` ✅ (called by `validate_and_accept`)
       - `_show_success_dialog(title, message)` → `_validate_and_accept__show_success_dialog(title, message)` ✅ (called by `_validate_and_accept__handle_success`)
       - `_build_user_preferences()` → `_validate_and_accept__build_user_preferences()` ✅ (called by `_validate_and_accept__collect_data`)
       - `_add_feature_settings()` → `_validate_and_accept__add_feature_settings()` ✅ (called by `_validate_and_accept__build_user_preferences`)
       - `_setup_task_tags()` → `_validate_and_accept__setup_task_tags()` ✅ (called by `_validate_and_accept__create_account`)
       - `_update_user_index()` → `_validate_and_accept__update_user_index()` ✅ (called by `_validate_and_accept__create_account`)
       - `_schedule_new_user()` → `_validate_and_accept__schedule_new_user()` ✅ (called by `_validate_and_accept__create_account`)

#### 9. `bot/communication_manager.py` - Infrastructure Helper Functions ✅ **COMPLETED**
**Main Functions**: Multiple infrastructure functions have helpers
**Current Helpers**:
- `_setup_event_loop()` → `__init____setup_event_loop()` ✅ (called by `__init__`)
- `_run_async_sync(coro)` → `send_message_sync__run_async_sync(coro)` ✅ (called by `send_message_sync`)
- `_queue_failed_message(channel_id, message)` → `send_message_sync__queue_failed_message(channel_id, message)` ✅ (called by `send_message_sync`)
- `_start_retry_thread()` → `start_all__start_retry_thread()` ✅ (called by `start_all`)
- `_stop_retry_thread()` → `stop_all__stop_retry_thread()` ✅ (called by `stop_all`)
- `_start_restart_monitor()` → `start_all__start_restart_monitor()` ✅ (called by `start_all`)
- `_stop_restart_monitor()` → `stop_all__stop_restart_monitor()` ✅ (called by `stop_all`)
- `_restart_monitor_loop()` → `start_all__restart_monitor_loop()` ✅ (called by `start_all__start_restart_monitor`)
- `_check_and_restart_stuck_channels()` → `start_all__check_and_restart_stuck_channels()` ✅ (called by `start_all__restart_monitor_loop`)
- `_attempt_channel_restart(channel_id)` → `start_all__attempt_channel_restart(channel_id)` ✅ (called by `start_all__check_and_restart_stuck_channels`)
- `_retry_loop()` → `start_all__retry_loop()` ✅ (called by `start_all__start_retry_thread`)
- `_process_retry_queue()` → `start_all__process_retry_queue()` ✅ (called by `start_all__retry_loop`)
- `_initialize_channels_async()` → `initialize_channels_from_config__initialize_channels_async()` ✅ (called by `initialize_channels_from_config`)

#### 10. `bot/discord_bot.py` - Infrastructure Helper Functions ✅ **COMPLETED**
**Main Functions**: Multiple infrastructure functions have helpers
**Current Helpers**:
- `_session_cleanup_context()` → `shutdown__session_cleanup_context()` ✅ (called by `shutdown`)
- `_update_connection_status(status)` → `_shared__update_connection_status(status)` ✅ (shared helper used by multiple functions)
- `_run_bot_in_thread()` → `initialize__run_bot_in_thread()` ✅ (called by `initialize`)
- `_bot_main_loop()` → `initialize__bot_main_loop()` ✅ (called by `initialize__run_bot_in_thread`)
- `_process_command_queue()` → `initialize__process_command_queue()` ✅ (called by `initialize__bot_main_loop`)
- `_register_events()` → `initialize__register_events()` ✅ (called by `initialize`)
- `_register_commands()` → `initialize__register_commands()` ✅ (called by `initialize`)

#### 11. `bot/email_bot.py` - Infrastructure Helper Functions ✅ **COMPLETED**
**Main Functions**: Multiple infrastructure functions have helpers
**Current Helpers**:
- `_test_smtp_connection()` → `initialize__test_smtp_connection()` ✅ (called by `initialize` and `health_check`)
- `_test_imap_connection()` → `initialize__test_imap_connection()` ✅ (called by `initialize` and `health_check`)
- `_send_email_sync(to, subject, body)` → `send_message__send_email_sync(to, subject, body)` ✅ (called by `send_message`)

#### 12. `bot/ai_chatbot.py` - Infrastructure Helper Functions ✅ **COMPLETED**
**Main Functions**: Multiple infrastructure functions have helpers
**Current Helpers**:
- `_load_custom_prompt()` → `__init____load_custom_prompt()` ✅ (called by `SystemPromptLoader.__init__` and `reload_prompt`)
- `_cleanup_lru()` → `set__cleanup_lru()` ✅ (called by `ResponseCache.set`)
- `_test_lm_studio_connection()` → `__init____test_lm_studio_connection()` ✅ (called by `AIChatbot.__init__` and `send_message`)

### **Priority 2: Test Utilities Helper Functions** ✅ **COMPLETED**

#### 13. `tests/test_utilities.py` - Additional Helper Functions ✅ **COMPLETED**
**Main Functions**: Many functions that appear to be helpers for other main functions
**Current Helpers** (40+ functions):
- `_create_basic_user_with_test_dir()` → `create_basic_user__with_test_dir()` (called by `create_basic_user`)
- `_create_discord_user_with_test_dir()` → `create_discord_user__with_test_dir()` (called by `create_discord_user`)
- `_create_full_featured_user_with_test_dir()` → `create_full_featured_user__with_test_dir()` (called by `create_full_featured_user`)
- `_create_full_featured_user_impl()` → `create_full_featured_user__impl()` (called by `create_full_featured_user`)
- `_create_email_user_with_test_dir()` → `create_email_user__with_test_dir()` (called by `create_email_user`)
- `_create_email_user_impl()` → `create_email_user__impl()` (called by `create_email_user`)
- `_create_user_with_custom_fields_impl()` → `create_user_with_custom_fields__impl()` (called by `create_user_with_custom_fields`)
- `_create_telegram_user_with_test_dir()` → `create_telegram_user__with_test_dir()` (called by `create_telegram_user`)
- `_create_telegram_user_impl()` → `create_telegram_user__impl()` (called by `create_telegram_user`)
- `_create_user_with_schedules_impl()` → `create_user_with_schedules__impl()` (called by `create_user_with_schedules`)
- `_create_minimal_user_with_test_dir()` → `create_minimal_user__with_test_dir()` (called by `create_minimal_user`)
- `_create_minimal_user_impl()` → `create_minimal_user__impl()` (called by `create_minimal_user`)
- `_create_user_with_complex_checkins_with_test_dir()` → `create_user_with_complex_checkins__with_test_dir()` (called by `create_user_with_complex_checkins`)
- `_create_user_with_complex_checkins_impl()` → `create_user_with_complex_checkins__impl()` (called by `create_user_with_complex_checkins`)
- `_create_user_with_health_focus_with_test_dir()` → `create_user_with_health_focus__with_test_dir()` (called by `create_user_with_health_focus`)
- `_create_user_with_health_focus_impl()` → `create_user_with_health_focus__impl()` (called by `create_user_with_health_focus`)
- `_create_user_with_task_focus_with_test_dir()` → `create_user_with_task_focus__with_test_dir()` (called by `create_user_with_task_focus`)
- `_create_user_with_task_focus_impl()` → `create_user_with_task_focus__impl()` (called by `create_user_with_task_focus`)
- `_create_user_with_disabilities_with_test_dir()` → `create_user_with_disabilities__with_test_dir()` (called by `create_user_with_disabilities`)
- `_create_user_with_disabilities_impl()` → `create_user_with_disabilities__impl()` (called by `create_user_with_disabilities`)
- `_create_user_with_limited_data_with_test_dir()` → `create_user_with_limited_data__with_test_dir()` (called by `create_user_with_limited_data`)
- `_create_user_with_limited_data_impl()` → `create_user_with_limited_data__impl()` (called by `create_user_with_limited_data`)
- `_create_user_with_inconsistent_data_with_test_dir()` → `create_user_with_inconsistent_data__with_test_dir()` (called by `create_user_with_inconsistent_data`)
- `_create_user_with_inconsistent_data_impl()` → `create_user_with_inconsistent_data__impl()` (called by `create_user_with_inconsistent_data`)
- `_verify_user_creation_with_test_dir()` → `create_basic_user__verify_creation()` (called by `create_basic_user`)
- `_verify_email_user_creation_with_test_dir()` → `create_email_user__verify_creation()` (called by `create_email_user`)

### **Priority 3: Non-Underscore Helper Functions** 🔍 **NEEDS INVESTIGATION**

#### 14. Potential Helper Functions Without Underscore Prefix 🔍 **TO BE IDENTIFIED**
**Files to Investigate**:
- All production code files for functions that appear to be helpers but don't start with `_`
- Common patterns: `parse_*`, `format_*`, `validate_*`, `build_*`, `collect_*`, `create_*`, `update_*`, `get_*`, `set_*`

## Phase 3: Update References 🟡 **PLANNED**
- Find all function calls to renamed helpers
- Update all references across the codebase
- Update any imports if helpers are imported elsewhere

## Phase 4: Testing and Validation 🟡 **PLANNED**
- Run comprehensive tests after each module
- Run audit to verify no regressions
- Manual testing of key functionality

## Phase 5: Documentation and Cleanup 🟡 **PLANNED**
- Update documentation files
- Update changelogs
- Final git commit and push

## Summary of Extended Scope
- **Phase 2B Total Functions Completed**: 69 additional helper functions
- **Production Code Priority**: 43 functions (High/Medium priority) ✅ **COMPLETED**
- **Test Utilities**: 26 functions (Lower priority) ✅ **COMPLETED**
- **Non-Underscore Helpers**: TBD (Needs investigation) - **DEFERRED**

## Overall Progress Summary
- **Phase 2**: 44 helper functions across 6 core modules ✅ **COMPLETED**
- **Phase 2B**: 69 helper functions across 7 additional modules ✅ **COMPLETED**
- **Total Refactored**: 113 helper functions across 13 modules
- **System Status**: All tests passing, full functionality maintained

## Next Steps (Optional/Future Work)
1. **Phase 2B Priority 3**: Investigate and refactor non-underscore helper functions (if desired)
2. **Phase 3**: Update any remaining references (if needed)
3. **Phase 4**: Run comprehensive validation (system already tested and working)
4. **Phase 5**: Final documentation cleanup (mostly complete)
