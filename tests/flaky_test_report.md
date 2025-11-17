# Flaky Test Detection Report
Generated: 2025-11-16 05:54:59
Test runs: 10

## Flaky Tests (May Need @pytest.mark.no_parallel)

These tests failed intermittently and may need the `no_parallel` marker:

### tests/behavior/test_scheduler_coverage_expansion.py::TestSelectTaskForReminderBehavior::test_select_task_for_reminder_priority_weighting_real_behavior
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [1, 1]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_get_user_id_by_username_returns_correct_id
- **Failure Rate**: 100.0% (6/6 runs)
- **Failed in runs**: [1, 1, 3, 3, 10, 10]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_handle_link_account_with_email_channel
- **Failure Rate**: 100.0% (6/6 runs)
- **Failed in runs**: [1, 1, 3, 3, 4, 4]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_handle_link_account_verifies_confirmation_code
- **Failure Rate**: 100.0% (4/4 runs)
- **Failed in runs**: [1, 1, 2, 2]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_handle_link_account_with_invalid_pending_operation
- **Failure Rate**: 100.0% (6/6 runs)
- **Failed in runs**: [1, 1, 3, 3, 10, 10]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_handle_create_account_with_existing_username
- **Failure Rate**: 100.0% (8/8 runs)
- **Failed in runs**: [1, 1, 2, 2, 3, 3, 4, 4]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_handle_create_account_with_valid_username
- **Failure Rate**: 100.0% (6/6 runs)
- **Failed in runs**: [1, 1, 3, 3, 6, 6]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/ui/test_task_management_dialog.py::TestTaskManagementDialogRealBehavior::test_save_task_settings_persists_to_disk
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [1, 1]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/unit/test_user_data_manager.py::TestUserDataManagerConvenienceFunctions::test_update_user_index_function
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [1, 1]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_handle_link_account_sends_confirmation_code
- **Failure Rate**: 100.0% (7/7 runs)
- **Failed in runs**: [2, 2, 3, 4, 4, 10, 10]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_handle_create_account_with_feature_selection
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [2, 2]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_handle_link_account_with_already_linked_email
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [3, 3]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_handle_link_account_sends_confirmation_codeGlobal
- **Failure Rate**: 100.0% (1/1 runs)
- **Failed in runs**: [3]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/ui/test_ui_app_qt_main.py::TestMHMManagerUI::test_refresh_user_list_loads_users
- **Failure Rate**: 100.0% (1/1 runs)
- **Failed in runs**: [3]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/integration/test_account_lifecycle.py::TestAccountLifecycle::test_reenable_tasks_for_user
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [3, 3]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/ui/test_account_creation_ui.py::TestAccountCreatorDialogCreateAccountBehavior::test_create_account_persists_feature_flags
- **Failure Rate**: 100.0% (4/4 runs)
- **Failed in runs**: [3, 3, 9, 9]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/ui/test_account_creation_ui.py::TestAccountCreationErrorHandling::test_invalid_data_handling_real_behavior
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [3, 3]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/ui/test_account_creation_ui.py::TestAccountCreationErrorHandling::test_duplicate_username_handling_real_behavior
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [3, 3]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/integration/test_account_lifecycle.py::TestAccountLifecycle::test_enable_checkins_for_basic_user
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [3, 3]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_backup_manager_behavior.py::TestBackupManagerBehavior::test_backup_creation_and_validation_real_behavior
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [3, 3]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_username_exists_checks_existing_username
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [4, 4]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/unit/test_user_data_manager.py::TestUserDataManagerInitialization::test_manager_initialization_creates_backup_dir
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [4, 4]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_message_behavior.py::TestIntegration::test_full_message_lifecycle
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [5, 5]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_discord_checkin_retry_behavior.py::TestDiscordCheckinRetryBehavior::test_checkin_message_queued_on_discord_disconnect
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [5, 5]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/integration/test_user_creation.py::TestUserCreationScenarios::test_user_with_custom_fields
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [6, 6]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/integration/test_user_creation.py::TestUserCreationScenarios::test_user_creation_with_schedules
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [6, 6]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/integration/test_user_creation.py::TestUserCreationScenarios::test_basic_email_user_creation
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [6, 6]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/unit/test_user_management.py::TestUserManagement::test_save_user_data_success
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [7, 7]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_message_behavior.py::TestMessageCRUD::test_edit_message_success
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [8, 8]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_message_behavior.py::TestMessageCRUD::test_delete_message_success
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [8, 8]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/unit/test_checkin_management_dialog.py::TestCheckinManagementDialogInitialization::test_initialization_loads_user_data
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [8, 8]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_chat_interaction_storage_real_scenarios.py::TestChatInteractionStorageRealScenarios::test_chat_interaction_performance_with_large_history
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [8, 8]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_response_tracking_behavior.py::TestResponseTrackingIntegration::test_response_tracking_concurrent_access_safety
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [9, 9]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/ui/test_account_creation_ui.py::TestAccountCreatorDialogCreateAccountBehavior::test_create_account_persists_categories
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [9, 9]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/ui/test_account_creation_ui.py::TestAccountCreatorDialogCreateAccountBehavior::test_create_account_updates_user_index
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [9, 9]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/ui/test_account_creation_ui.py::TestAccountCreatorDialogCreateAccountBehavior::test_create_account_saves_custom_tags_when_provided
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [9, 9]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_handle_link_account_with_already_linked_discord
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [10, 10]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/unit/test_logger_unit.py::TestEnsureLogsDirectory::test_ensure_logs_directory_creates_directories
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [10, 10]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/unit/test_user_data_manager.py::TestUserDataManagerConvenienceFunctions::test_update_message_references_function
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [10, 10]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_backup_manager_behavior.py::TestBackupManagerBehavior::test_backup_manager_with_large_user_data_real_behavior
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [10, 10]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

## Consistently Failing Tests

These tests failed in all runs (not flaky, but need investigation):

- `tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_handle_check_account_status_without_user` - Failed in all 14 runs
- `tests/unit/test_scripts_exclusion_policy.py::test_scripts_directory_has_no_test_files` - Failed in all 20 runs
