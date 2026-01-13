# Test Coverage Report

> **File**: `development_docs/TEST_COVERAGE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-01-13 04:37:59
> **Source**: `python development_tools/tests/generate_test_coverage.py --update-plan` - Coverage Metrics Regenerator

## Current Status

### **Overall Coverage: 72.0%**
- **Total Statements**: 28,643
- **Covered Statements**: 20,617
- **Uncovered Statements**: 8,026
- **Goal**: Expand to **80%+ coverage** for comprehensive reliability

### **Coverage Summary by Category**
- **Excellent (93% avg)**: 60 modules
- **Good (71% avg)**: 40 modules
- **Moderate (48% avg)**: 4 modules

### **Detailed Module Coverage**
- **X ui\widgets\checkin_settings_widget.py**: 44% (291/663 lines)
- **X communication\communication_channels\discord\bot.py**: 45% (562/1245 lines)
- **X ui\ui_app_qt.py**: 51% (714/1390 lines)
- **X communication\command_handlers\notebook_handler.py**: 52% (272/523 lines)
- **! core\file_locking.py**: 60% (77/129 lines)
- **! communication\core\channel_orchestrator.py**: 61% (626/1028 lines)
- **! core\service.py**: 62% (431/700 lines)
- **! ai\chatbot.py**: 64% (537/841 lines)
- **! communication\message_processing\conversation_flow_manager.py**: 64% (637/992 lines)
- **! communication\message_processing\interaction_manager.py**: 64% (362/569 lines)
- **! ui\dialogs\schedule_editor_dialog.py**: 64% (152/239 lines)
- **! communication\command_handlers\interaction_handlers.py**: 65% (168/260 lines)
- **! core\scheduler.py**: 65% (616/951 lines)
- **! core\tags.py**: 65% (140/215 lines)
- **! core\logger.py**: 66% (475/716 lines)
- **! ui\widgets\dynamic_list_container.py**: 66% (135/204 lines)
- **! communication\communication_channels\email\bot.py**: 67% (148/220 lines)
- **! ui\widgets\channel_selection_widget.py**: 67% (55/82 lines)
- **! ui\dialogs\account_creator_dialog.py**: 68% (444/649 lines)
- **! communication\message_processing\command_parser.py**: 69% (393/573 lines)
- **! core\user_data_handlers.py**: 69% (554/798 lines)
- **! ui\widgets\user_profile_settings_widget.py**: 70% (202/287 lines)
- **! core\user_data_manager.py**: 71% (618/867 lines)
- **! communication\command_handlers\analytics_handler.py**: 72% (332/460 lines)
- **! communication\command_handlers\profile_handler.py**: 72% (209/290 lines)
- **! core\message_management.py**: 72% (282/390 lines)
- **! ui\dialogs\task_crud_dialog.py**: 72% (155/216 lines)
- **! communication\communication_channels\discord\webhook_handler.py**: 73% (110/150 lines)
- **! core\auto_cleanup.py**: 73% (302/412 lines)
- **! ui\dialogs\task_completion_dialog.py**: 73% (84/115 lines)
- **! ui\generate_ui_files.py**: 73% (48/66 lines)
- **! core\checkin_analytics.py**: 74% (353/477 lines)
- **! core\user_management.py**: 74% (562/763 lines)
- **! ui\widgets\dynamic_list_field.py**: 75% (91/121 lines)
- **! core\backup_manager.py**: 76% (333/438 lines)
- **! core\config.py**: 77% (326/426 lines)
- **! core\file_auditor.py**: 77% (72/93 lines)
- **! ui\dialogs\task_edit_dialog.py**: 77% (301/393 lines)
- **! ai\conversation_history.py**: 79% (170/215 lines)
- **! communication\command_handlers\schedule_handler.py**: 79% (210/265 lines)
- **! core\checkin_dynamic_manager.py**: 79% (256/325 lines)
- **! core\error_handling.py**: 79% (311/396 lines)
- **! core\file_operations.py**: 79% (312/397 lines)
- **! ui\dialogs\user_profile_dialog.py**: 79% (209/263 lines)
- *** communication\command_handlers\task_handler.py**: 80% (495/617 lines)
- *** communication\core\channel_monitor.py**: 80% (110/137 lines)
- *** core\service_utilities.py**: 80% (118/148 lines)
- *** ui\dialogs\checkin_management_dialog.py**: 80% (130/162 lines)
- *** core\schedule_management.py**: 81% (248/306 lines)
- *** communication\communication_channels\base\base_channel.py**: 82% (76/93 lines)
- *** communication\communication_channels\base\message_formatter.py**: 82% (107/131 lines)
- *** tasks\task_management.py**: 82% (439/538 lines)
- *** ui\dialogs\admin_panel.py**: 82% (41/50 lines)
- *** core\headless_service.py**: 83% (180/216 lines)
- *** communication\command_handlers\base_handler.py**: 84% (68/81 lines)
- *** communication\communication_channels\discord\welcome_handler.py**: 85% (33/39 lines)
- *** core\schemas.py**: 86% (261/302 lines)
- *** ui\widgets\tag_widget.py**: 86% (185/214 lines)
- *** ui\widgets\period_row_widget.py**: 87% (213/245 lines)
- *** core\response_tracking.py**: 88% (104/118 lines)
- *** ai\context_builder.py**: 89% (238/266 lines)
- *** communication\communication_channels\base\rich_formatter.py**: 89% (116/131 lines)
- *** ui\dialogs\process_watcher_dialog.py**: 89% (262/296 lines)
- *** communication\command_handlers\account_handler.py**: 90% (159/177 lines)
- *** communication\communication_channels\discord\api_client.py**: 90% (164/182 lines)
- *** communication\core\retry_manager.py**: 90% (92/102 lines)
- *** core\__init__.py**: 91% (39/43 lines)
- *** communication\communication_channels\base\command_registry.py**: 92% (119/129 lines)
- *** core\message_analytics.py**: 92% (61/66 lines)
- *** user\context_manager.py**: 92% (143/155 lines)
- *** communication\communication_channels\discord\event_handler.py**: 93% (166/179 lines)
- *** core\user_data_validation.py**: 93% (275/297 lines)
- *** ui\dialogs\channel_management_dialog.py**: 93% (106/114 lines)
- *** communication\communication_channels\discord\webhook_server.py**: 94% (121/129 lines)
- *** communication\message_processing\message_router.py**: 95% (116/122 lines)
- *** ui\dialogs\task_management_dialog.py**: 95% (88/93 lines)
- *** ui\dialogs\user_analytics_dialog.py**: 95% (275/290 lines)
- *** ui\widgets\task_settings_widget.py**: 95% (173/183 lines)
- *** ai\lm_studio_manager.py**: 96% (111/116 lines)
- *** communication\command_handlers\checkin_handler.py**: 96% (72/75 lines)
- *** communication\core\factory.py**: 96% (45/47 lines)
- *** ui\dialogs\category_management_dialog.py**: 97% (114/117 lines)
- *** ui\dialogs\message_editor_dialog.py**: 97% (205/211 lines)
- *** communication\communication_channels\discord\checkin_view.py**: 98% (41/42 lines)
- *** ai\cache_manager.py**: 99% (176/177 lines)
- *** ai\__init__.py**: 100% (8/8 lines)
- *** ai\prompt_manager.py**: 100% (115/115 lines)
- *** communication\__init__.py**: 100% (111/111 lines)
- *** communication\command_handlers\__init__.py**: 100% (5/5 lines)
- *** communication\command_handlers\shared_types.py**: 100% (17/17 lines)
- *** communication\communication_channels\__init__.py**: 100% (2/2 lines)
- *** communication\core\__init__.py**: 100% (11/11 lines)
- *** communication\core\welcome_manager.py**: 100% (47/47 lines)
- *** communication\message_processing\__init__.py**: 100% (3/3 lines)
- *** core\schedule_utilities.py**: 100% (62/62 lines)
- *** core\ui_management.py**: 100% (86/86 lines)
- *** tasks\__init__.py**: 100% (5/5 lines)
- *** ui\__init__.py**: 100% (30/30 lines)
- *** ui\dialogs\__init__.py**: 100% (9/9 lines)
- *** ui\widgets\__init__.py**: 100% (9/9 lines)
- *** ui\widgets\category_selection_widget.py**: 100% (37/37 lines)
- *** user\__init__.py**: 100% (5/5 lines)
- *** user\user_context.py**: 100% (84/84 lines)
- *** user\user_preferences.py**: 100% (49/49 lines)

## Test Markers

**Note**: This section documents test execution markers. For detailed testing guidance, see [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md).

### E2E Marker

Tests marked with `@pytest.mark.e2e` are end-to-end verification tests that run real audits with actual tool execution (no mocks). These tests are:

- **Excluded by default**: The `e2e` marker is excluded from regular test runs via `pytest.ini` configuration (`-m "not e2e"`).
- **Slow**: Tier 3 E2E tests can take ~9-10 minutes due to coverage generation.
- **For verification**: Use these tests to verify actual audit tier execution before releases.

**Running E2E tests**:
```bash
# Run all E2E tests
pytest -m e2e tests/development_tools/test_audit_tier_e2e_verification.py

# Run specific E2E test
pytest -m e2e tests/development_tools/test_audit_tier_e2e_verification.py::TestAuditTierE2E::test_tier1_e2e
```

**Note**: This section may be overwritten when the coverage report is regenerated. See [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md) section 6.5 for authoritative documentation.