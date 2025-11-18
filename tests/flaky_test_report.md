# Flaky Test Detection Report
Generated: 2025-11-18 03:22:17
Test runs: 5

## Flaky Tests (May Need @pytest.mark.no_parallel)

These tests failed intermittently in parallel execution and may need the `no_parallel` marker.
Note: Tests already marked with `@pytest.mark.no_parallel` are excluded from this report.

### tests/behavior/test_discord_bot_behavior.py::TestDiscordBotIntegration::test_discord_message_to_interaction_manager_complete_task_prompt
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [1, 1]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/ui/test_account_creation_ui.py::TestAccountManagementRealBehavior::test_user_profile_dialog_integration
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [3, 3]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/integration/test_account_management.py::test_account_management_data_structures
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [3, 3]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`

### tests/behavior/test_message_behavior.py::TestMessageCRUD::test_add_message_success
- **Failure Rate**: 100.0% (2/2 runs)
- **Failed in runs**: [4, 4]
- **Recommendation**: Consider adding `@pytest.mark.no_parallel`
