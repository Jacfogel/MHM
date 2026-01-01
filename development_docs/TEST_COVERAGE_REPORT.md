# Test Coverage Report

> **File**: `development_docs/TEST_COVERAGE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2025-12-31 20:49:38
> **Source**: `python development_tools/tests/generate_test_coverage.py --update-plan` - Coverage Metrics Regenerator

## Current Status

### **Overall Coverage: 71.6%**
- **Total Statements**: 27,172
- **Covered Statements**: 19,467
- **Uncovered Statements**: 7,705
- **Goal**: Expand to **80%+ coverage** for comprehensive reliability

### **Coverage Summary by Category**
- **Excellent (93% avg)**: 58 modules
- **Good (70% avg)**: 41 modules
- **Moderate (50% avg)**: 3 modules

### **Detailed Module Coverage**
- **X communication\communication_channels\discord\bot.py**: 47% (561/1193 lines)
- **X ui\ui_app_qt.py**: 50% (687/1386 lines)
- **X ui\dialogs\account_creator_dialog.py**: 54% (352/648 lines)
- **! communication\core\channel_orchestrator.py**: 61% (623/1025 lines)
- **! ui\widgets\checkin_settings_widget.py**: 61% (106/173 lines)
- **! communication\command_handlers\interaction_handlers.py**: 62% (925/1499 lines)
- **! core\service.py**: 62% (429/697 lines)
- **! core\file_locking.py**: 63% (81/128 lines)
- **! ui\dialogs\schedule_editor_dialog.py**: 63% (151/238 lines)
- **! communication\message_processing\interaction_manager.py**: 64% (329/517 lines)
- **! core\scheduler.py**: 64% (609/951 lines)
- **! core\user_data_manager.py**: 64% (555/865 lines)
- **! ai\chatbot.py**: 65% (546/837 lines)
- **! core\message_management.py**: 65% (251/389 lines)
- **! core\logger.py**: 66% (466/711 lines)
- **! ui\widgets\dynamic_list_container.py**: 66% (134/203 lines)
- **! communication\communication_channels\email\bot.py**: 67% (147/219 lines)
- **! core\backup_manager.py**: 67% (290/436 lines)
- **! core\file_operations.py**: 67% (265/396 lines)
- **! ui\widgets\channel_selection_widget.py**: 67% (55/82 lines)
- **! communication\command_handlers\account_handler.py**: 70% (129/183 lines)
- **! communication\communication_channels\discord\webhook_handler.py**: 70% (104/149 lines)
- **! core\checkin_analytics.py**: 70% (312/448 lines)
- **! ui\widgets\user_profile_settings_widget.py**: 70% (201/286 lines)
- **! core\user_data_handlers.py**: 71% (558/788 lines)
- **! communication\message_processing\conversation_flow_manager.py**: 72% (412/574 lines)
- **! ui\dialogs\task_crud_dialog.py**: 72% (154/215 lines)
- **! communication\command_handlers\analytics_handler.py**: 73% (335/462 lines)
- **! core\service_utilities.py**: 73% (106/145 lines)
- **! ui\dialogs\task_completion_dialog.py**: 73% (83/114 lines)
- **! ui\generate_ui_files.py**: 73% (46/63 lines)
- **! communication\message_processing\command_parser.py**: 74% (267/363 lines)
- **! core\user_management.py**: 74% (543/735 lines)
- **! ui\widgets\dynamic_list_field.py**: 75% (90/120 lines)
- **! core\auto_cleanup.py**: 76% (300/396 lines)
- **! core\config.py**: 76% (324/424 lines)
- **! communication\command_handlers\profile_handler.py**: 77% (193/252 lines)
- **! core\error_handling.py**: 77% (292/377 lines)
- **! core\file_auditor.py**: 77% (70/91 lines)
- **! ui\dialogs\task_edit_dialog.py**: 77% (300/392 lines)
- **! ai\conversation_history.py**: 78% (163/210 lines)
- **! communication\command_handlers\schedule_handler.py**: 79% (207/262 lines)
- **! core\checkin_dynamic_manager.py**: 79% (157/199 lines)
- **! ui\dialogs\user_profile_dialog.py**: 79% (207/261 lines)
- *** communication\core\channel_monitor.py**: 80% (109/136 lines)
- *** core\schedule_management.py**: 81% (247/305 lines)
- *** communication\communication_channels\base\message_formatter.py**: 82% (95/116 lines)
- *** communication\communication_channels\discord\welcome_handler.py**: 82% (32/39 lines)
- *** tasks\task_management.py**: 82% (480/583 lines)
- *** ui\dialogs\admin_panel.py**: 82% (40/49 lines)
- *** communication\command_handlers\task_handler.py**: 83% (309/374 lines)
- *** communication\communication_channels\base\base_channel.py**: 83% (55/66 lines)
- *** core\headless_service.py**: 83% (177/212 lines)
- *** core\schemas.py**: 85% (256/301 lines)
- *** ui\dialogs\checkin_management_dialog.py**: 85% (100/118 lines)
- *** ui\widgets\tag_widget.py**: 86% (184/213 lines)
- *** ui\widgets\period_row_widget.py**: 87% (212/244 lines)
- *** core\response_tracking.py**: 88% (103/117 lines)
- *** ui\dialogs\process_watcher_dialog.py**: 88% (261/295 lines)
- *** ai\context_builder.py**: 89% (235/263 lines)
- *** communication\communication_channels\base\rich_formatter.py**: 90% (104/116 lines)
- *** communication\communication_channels\discord\api_client.py**: 90% (161/179 lines)
- *** communication\core\retry_manager.py**: 90% (90/100 lines)
- *** core\__init__.py**: 90% (38/42 lines)
- *** ui\dialogs\channel_management_dialog.py**: 91% (104/114 lines)
- *** core\message_analytics.py**: 92% (60/65 lines)
- *** core\user_data_validation.py**: 92% (244/266 lines)
- *** user\context_manager.py**: 92% (141/153 lines)
- *** communication\communication_channels\base\command_registry.py**: 93% (109/117 lines)
- *** communication\communication_channels\discord\event_handler.py**: 93% (163/176 lines)
- *** communication\communication_channels\discord\webhook_server.py**: 94% (118/126 lines)
- *** communication\command_handlers\base_handler.py**: 95% (56/59 lines)
- *** communication\message_processing\message_router.py**: 95% (113/119 lines)
- *** ui\dialogs\task_management_dialog.py**: 95% (88/93 lines)
- *** ui\dialogs\user_analytics_dialog.py**: 95% (273/288 lines)
- *** ui\widgets\task_settings_widget.py**: 95% (173/183 lines)
- *** ai\lm_studio_manager.py**: 96% (109/114 lines)
- *** communication\command_handlers\checkin_handler.py**: 96% (71/74 lines)
- *** communication\core\factory.py**: 96% (44/46 lines)
- *** ui\dialogs\category_management_dialog.py**: 97% (114/117 lines)
- *** ui\dialogs\message_editor_dialog.py**: 97% (202/208 lines)
- *** communication\communication_channels\discord\checkin_view.py**: 98% (40/41 lines)
- *** ai\cache_manager.py**: 99% (173/174 lines)
- *** ai\__init__.py**: 100% (7/7 lines)
- *** ai\prompt_manager.py**: 100% (113/113 lines)
- *** communication\__init__.py**: 100% (106/106 lines)
- *** communication\command_handlers\__init__.py**: 100% (3/3 lines)
- *** communication\command_handlers\shared_types.py**: 100% (15/15 lines)
- *** communication\communication_channels\__init__.py**: 100% (1/1 lines)
- *** communication\core\__init__.py**: 100% (10/10 lines)
- *** communication\core\welcome_manager.py**: 100% (46/46 lines)
- *** communication\message_processing\__init__.py**: 100% (2/2 lines)
- *** core\schedule_utilities.py**: 100% (61/61 lines)
- *** core\ui_management.py**: 100% (85/85 lines)
- *** tasks\__init__.py**: 100% (2/2 lines)
- *** ui\__init__.py**: 100% (29/29 lines)
- *** ui\dialogs\__init__.py**: 100% (8/8 lines)
- *** ui\widgets\__init__.py**: 100% (8/8 lines)
- *** ui\widgets\category_selection_widget.py**: 100% (37/37 lines)
- *** user\__init__.py**: 100% (4/4 lines)
- *** user\user_context.py**: 100% (84/84 lines)
- *** user\user_preferences.py**: 100% (48/48 lines)

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