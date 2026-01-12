# Test Coverage Report

> **File**: `development_docs/TEST_COVERAGE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-01-12 04:10:45
> **Source**: `python development_tools/tests/generate_test_coverage.py --update-plan` - Coverage Metrics Regenerator

## Current Status

### **Overall Coverage: 55.9%**
- **Total Statements**: 28,471
- **Covered Statements**: 15,916
- **Uncovered Statements**: 12,555
- **Goal**: Expand to **80%+ coverage** for comprehensive reliability

### **Coverage Summary by Category**
- **Excellent (94% avg)**: 37 modules
- **Good (72% avg)**: 30 modules
- **Moderate (47% avg)**: 12 modules
- **Needs_Work (29% avg)**: 19 modules
- **Critical (14% avg)**: 6 modules

### **Detailed Module Coverage**
- **X communication\command_handlers\analytics_handler.py**: 10% (44/459 lines)
- **X communication\command_handlers\schedule_handler.py**: 11% (30/264 lines)
- **X communication\command_handlers\notebook_handler.py**: 13% (69/521 lines)
- **X communication\communication_channels\discord\bot.py**: 13% (164/1244 lines)
- **X communication\communication_channels\discord\checkin_view.py**: 17% (7/41 lines)
- **X communication\communication_channels\discord\webhook_server.py**: 18% (23/126 lines)
- **X communication\communication_channels\email\bot.py**: 20% (44/219 lines)
- **X ai\lm_studio_manager.py**: 23% (26/114 lines)
- **X communication\communication_channels\base\message_formatter.py**: 25% (32/128 lines)
- **X communication\core\channel_orchestrator.py**: 25% (257/1025 lines)
- **X ai\context_builder.py**: 25% (65/263 lines)
- **X communication\command_handlers\task_handler.py**: 26% (158/615 lines)
- **X communication\communication_channels\base\rich_formatter.py**: 27% (34/128 lines)
- **X ai\chatbot.py**: 27% (223/839 lines)
- **X communication\command_handlers\interaction_handlers.py**: 28% (72/258 lines)
- **X communication\communication_channels\discord\api_client.py**: 28% (51/179 lines)
- **X ai\conversation_history.py**: 29% (62/212 lines)
- **X communication\core\__init__.py**: 30% (3/10 lines)
- **X communication\core\channel_monitor.py**: 30% (41/136 lines)
- **X communication\message_processing\command_parser.py**: 32% (183/570 lines)
- **X communication\message_processing\conversation_flow_manager.py**: 32% (314/991 lines)
- **X communication\command_handlers\base_handler.py**: 33% (26/79 lines)
- **X communication\message_processing\interaction_manager.py**: 35% (196/567 lines)
- **X communication\message_processing\message_router.py**: 36% (43/119 lines)
- **X communication\communication_channels\discord\event_handler.py**: 39% (68/176 lines)
- **X communication\command_handlers\profile_handler.py**: 41% (118/289 lines)
- **X communication\core\factory.py**: 41% (19/46 lines)
- **X communication\communication_channels\base\command_registry.py**: 42% (53/125 lines)
- **X ui\widgets\checkin_settings_widget.py**: 44% (290/662 lines)
- **X communication\__init__.py**: 44% (48/110 lines)
- **X communication\communication_channels\discord\welcome_handler.py**: 46% (17/37 lines)
- **X communication\core\retry_manager.py**: 46% (46/100 lines)
- **X communication\command_handlers\checkin_handler.py**: 49% (36/74 lines)
- **X ui\ui_app_qt.py**: 51% (707/1388 lines)
- **X communication\communication_channels\discord\webhook_handler.py**: 51% (76/149 lines)
- **X ai\cache_manager.py**: 51% (88/174 lines)
- **X ai\prompt_manager.py**: 58% (65/113 lines)
- **! core\service.py**: 62% (430/699 lines)
- **! ui\dialogs\schedule_editor_dialog.py**: 63% (151/238 lines)
- **! core\file_locking.py**: 63% (81/128 lines)
- **! core\logger.py**: 65% (460/711 lines)
- **! core\scheduler.py**: 65% (615/951 lines)
- **! core\tags.py**: 65% (139/214 lines)
- **! ui\widgets\dynamic_list_container.py**: 66% (134/203 lines)
- **! ui\widgets\channel_selection_widget.py**: 67% (55/82 lines)
- **! ui\dialogs\account_creator_dialog.py**: 68% (443/648 lines)
- **! ui\widgets\user_profile_settings_widget.py**: 70% (201/286 lines)
- **! core\auto_cleanup.py**: 71% (291/411 lines)
- **! core\user_data_handlers.py**: 71% (567/797 lines)
- **! core\user_data_manager.py**: 71% (617/865 lines)
- **! ui\dialogs\task_crud_dialog.py**: 72% (154/215 lines)
- **! ui\generate_ui_files.py**: 72% (47/65 lines)
- **! core\message_management.py**: 72% (279/389 lines)
- **! communication\communication_channels\base\base_channel.py**: 73% (66/91 lines)
- **! core\service_utilities.py**: 73% (106/145 lines)
- **! core\user_management.py**: 73% (559/762 lines)
- **! ui\dialogs\task_completion_dialog.py**: 74% (84/114 lines)
- **! core\checkin_analytics.py**: 74% (352/476 lines)
- **! ui\widgets\dynamic_list_field.py**: 75% (90/120 lines)
- **! core\backup_manager.py**: 76% (333/436 lines)
- **! core\config.py**: 76% (324/424 lines)
- **! ui\dialogs\task_edit_dialog.py**: 77% (300/392 lines)
- **! core\file_auditor.py**: 77% (70/91 lines)
- **! core\error_handling.py**: 78% (295/379 lines)
- **! ui\dialogs\user_profile_dialog.py**: 79% (207/261 lines)
- **! core\checkin_dynamic_manager.py**: 79% (254/323 lines)
- **! core\file_operations.py**: 79% (311/396 lines)
- *** ui\dialogs\checkin_management_dialog.py**: 80% (128/160 lines)
- *** core\schedule_management.py**: 81% (247/305 lines)
- *** ui\dialogs\admin_panel.py**: 82% (40/49 lines)
- *** communication\command_handlers\account_handler.py**: 82% (143/175 lines)
- *** tasks\task_management.py**: 82% (437/536 lines)
- *** core\headless_service.py**: 83% (178/214 lines)
- *** ui\widgets\tag_widget.py**: 86% (184/213 lines)
- *** core\schemas.py**: 86% (260/301 lines)
- *** ui\widgets\period_row_widget.py**: 87% (212/244 lines)
- *** ui\dialogs\process_watcher_dialog.py**: 88% (261/295 lines)
- *** core\response_tracking.py**: 88% (103/117 lines)
- *** core\__init__.py**: 90% (38/42 lines)
- *** user\context_manager.py**: 92% (141/153 lines)
- *** core\message_analytics.py**: 92% (60/65 lines)
- *** ui\dialogs\channel_management_dialog.py**: 93% (106/114 lines)
- *** core\user_data_validation.py**: 93% (274/296 lines)
- *** ui\dialogs\task_management_dialog.py**: 95% (88/93 lines)
- *** ui\dialogs\user_analytics_dialog.py**: 95% (273/288 lines)
- *** ui\widgets\task_settings_widget.py**: 95% (173/183 lines)
- *** ui\dialogs\category_management_dialog.py**: 97% (114/117 lines)
- *** ui\dialogs\message_editor_dialog.py**: 97% (202/208 lines)
- *** ui\__init__.py**: 100% (29/29 lines)
- *** ui\dialogs\__init__.py**: 100% (8/8 lines)
- *** ui\widgets\__init__.py**: 100% (8/8 lines)
- *** ui\widgets\category_selection_widget.py**: 100% (37/37 lines)
- *** user\__init__.py**: 100% (4/4 lines)
- *** user\user_context.py**: 100% (84/84 lines)
- *** user\user_preferences.py**: 100% (48/48 lines)
- *** communication\command_handlers\__init__.py**: 100% (4/4 lines)
- *** communication\command_handlers\shared_types.py**: 100% (15/15 lines)
- *** communication\communication_channels\__init__.py**: 100% (1/1 lines)
- *** communication\core\welcome_manager.py**: 100% (46/46 lines)
- *** communication\message_processing\__init__.py**: 100% (2/2 lines)
- *** ai\__init__.py**: 100% (7/7 lines)
- *** tasks\__init__.py**: 100% (2/2 lines)
- *** core\schedule_utilities.py**: 100% (61/61 lines)
- *** core\ui_management.py**: 100% (85/85 lines)

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