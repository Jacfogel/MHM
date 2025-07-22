# Utils.py Refactoring Plan

## Phase 1: Preparation & Backup ✅ COMPLETED
- [x] Created backup: `../backup_YYYYMMDD_HHMMSS/`
- [x] Created test script: `scripts/test_utils_functions.py`
- [x] Verified current functionality works
- [x] Documented import patterns

## Phase 2: Create New Module Structure ✅ IN PROGRESS
- [x] Create core/validation.py ✅ COMPLETED
- [x] Create core/file_operations.py ✅ COMPLETED  
- [x] Create core/service_utilities.py ✅ COMPLETED
- [ ] Create core/user_management.py
- [ ] Create core/message_management.py
- [ ] Create core/schedule_management.py
- [ ] Create core/response_tracking.py

## Current Import Analysis

### Files that import from core.utils:
1. `core/user_data_manager.py` - imports specific functions
2. `core/service.py` - imports specific functions
3. `user/user_preferences.py` - imports entire module
4. `user/user_context.py` - imports entire module
5. `ui/ui_app.py` - imports entire module
6. `ui/account_manager.py` - imports entire module
7. `ui/account_creator.py` - imports entire module
8. `core/checkin_analytics.py` - imports entire module
9. `bot/user_context_manager.py` - imports entire module
10. `bot/telegram_bot.py` - imports entire module
11. `bot/discord_bot.py` - imports entire module
12. `bot/conversation_manager.py` - imports entire module
13. `bot/communication_manager.py` - imports entire module
14. `bot/ai_chatbot.py` - imports entire module

### Functions moved to new modules:

#### ✅ core/validation.py - COMPLETED
- [x] `is_valid_email()`
- [x] `is_valid_phone()`
- [x] `title_case()`

#### ✅ core/file_operations.py - COMPLETED
- [x] `load_json_data()`
- [x] `save_json_data()`
- [x] `determine_file_path()`
- [x] `verify_file_access()`
- [x] `create_user_files()`

#### ✅ core/service_utilities.py - COMPLETED
- [x] `create_reschedule_request()`
- [x] `is_service_running()`
- [x] `wait_for_network()`
- [x] `load_and_localize_datetime()`

#### core/user_management.py - PENDING
- `get_all_user_ids()`
- `load_user_info_data()`
- `save_user_info_data()`
- `get_user_info()`
- `get_user_preferences()`
- `add_user_info()`
- `ensure_unique_ids()`
- `load_and_ensure_ids()`
- `get_user_id_by_internal_username()`
- `get_user_id_by_chat_id()`
- `get_user_id_by_discord_user_id()`

#### core/message_management.py - PENDING
- `get_message_categories()`
- `load_default_messages()`
- `add_message()`
- `edit_message()`
- `delete_message()`
- `get_last_10_messages()`
- `store_sent_message()`

#### core/schedule_management.py - PENDING
- `get_schedule_time_periods()`
- `set_schedule_period_active()`
- `is_schedule_period_active()`
- `get_current_time_periods_with_validation()`
- `add_schedule_period()`
- `edit_schedule_period()`
- `delete_schedule_period()`
- `clear_schedule_periods_cache()`
- `validate_and_format_time()`

#### core/response_tracking.py - PENDING
- `store_user_response()`
- `store_daily_checkin_response()`
- `store_chat_interaction()`
- `store_survey_response()`
- `get_recent_responses()`
- `get_recent_daily_checkins()`
- `get_recent_chat_interactions()`
- `get_recent_survey_responses()`
- `get_user_checkin_preferences()`
- `is_user_checkins_enabled()`
- `get_user_checkin_questions()`

## Phase 3: Incremental Migration
- [ ] Move functions to new modules
- [ ] Add compatibility layer to utils.py
- [ ] Test functionality
- [ ] Update imports gradually
- [ ] Remove compatibility layer

## Phase 4: Testing & Validation
- [ ] Run test script
- [ ] Test main application
- [ ] Verify all functionality works

## Safety Checklist
- [x] Backup created
- [x] Test script created
- [x] Current functionality verified
- [x] Each step tested before proceeding
- [ ] Rollback plan ready

## Progress Summary
**Completed**: 3/7 modules (43%)
**Functions moved**: 11/47 functions (23%)
**Status**: All completed modules tested and working 