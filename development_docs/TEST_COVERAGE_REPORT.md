# Test Coverage Report

> **File**: `development_docs/TEST_COVERAGE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-01-20 23:33:30
> **Source**: `python development_tools/tests/generate_test_coverage.py --update-plan` - Coverage Metrics Regenerator

## Current Status

### **Overall Coverage: 34.8%**
- **Total Statements**: 28,543
- **Covered Statements**: 9,925
- **Uncovered Statements**: 18,618
- **Goal**: Expand to **80%+ coverage** for comprehensive reliability

### **Coverage Summary by Category**
- **Excellent (97% avg)**: 15 modules
- **Good (68% avg)**: 6 modules
- **Moderate (49% avg)**: 31 modules
- **Needs_Work (28% avg)**: 37 modules
- **Critical (15% avg)**: 15 modules

### **Detailed Module Coverage**
- **X communication\command_handlers\analytics_handler.py**: 10% (44/459 lines)
- **X communication\command_handlers\schedule_handler.py**: 11% (28/250 lines)
- **X communication\command_handlers\notebook_handler.py**: 13% (69/520 lines)
- **X communication\communication_channels\discord\bot.py**: 13% (164/1267 lines)
- **X ui\widgets\user_profile_settings_widget.py**: 13% (38/286 lines)
- **X core\checkin_analytics.py**: 14% (67/485 lines)
- **X core\headless_service.py**: 14% (30/212 lines)
- **X ui\dialogs\task_edit_dialog.py**: 14% (57/394 lines)
- **X ui\dialogs\user_analytics_dialog.py**: 15% (42/288 lines)
- **X ui\widgets\dynamic_list_container.py**: 15% (31/203 lines)
- **X communication\communication_channels\discord\checkin_view.py**: 17% (7/41 lines)
- **X ui\dialogs\channel_management_dialog.py**: 17% (19/114 lines)
- **X ui\dialogs\task_crud_dialog.py**: 17% (37/215 lines)
- **X communication\communication_channels\discord\webhook_server.py**: 18% (23/126 lines)
- **X communication\communication_channels\email\bot.py**: 19% (46/240 lines)
- **X communication\communication_channels\base\message_formatter.py**: 20% (23/116 lines)
- **X core\scheduler.py**: 20% (199/1012 lines)
- **X ui\dialogs\user_profile_dialog.py**: 20% (53/261 lines)
- **X ui\generate_ui_files.py**: 20% (13/64 lines)
- **X communication\communication_channels\base\rich_formatter.py**: 22% (25/116 lines)
- **X ui\dialogs\schedule_editor_dialog.py**: 22% (53/238 lines)
- **X ui\dialogs\task_completion_dialog.py**: 22% (25/115 lines)
- **X ai\lm_studio_manager.py**: 23% (26/114 lines)
- **X core\message_analytics.py**: 23% (15/64 lines)
- **X ui\dialogs\message_editor_dialog.py**: 23% (47/208 lines)
- **X core\schedule_utilities.py**: 24% (15/63 lines)
- **X core\service.py**: 24% (166/698 lines)
- **X ai\context_builder.py**: 25% (66/264 lines)
- **X communication\command_handlers\base_handler.py**: 25% (14/57 lines)
- **X communication\core\channel_orchestrator.py**: 25% (255/1038 lines)
- **X core\auto_cleanup.py**: 25% (103/412 lines)
- **X ai\chatbot.py**: 26% (221/835 lines)
- **X communication\command_handlers\task_handler.py**: 26% (159/608 lines)
- **X ui\ui_app_qt.py**: 26% (361/1402 lines)
- **X communication\command_handlers\interaction_handlers.py**: 28% (72/258 lines)
- **X communication\communication_channels\discord\api_client.py**: 28% (51/181 lines)
- **X core\logger.py**: 28% (197/711 lines)
- **X ai\conversation_history.py**: 30% (63/213 lines)
- **X communication\core\__init__.py**: 30% (3/10 lines)
- **X communication\core\channel_monitor.py**: 30% (42/138 lines)
- **X core\schedule_management.py**: 31% (94/304 lines)
- **X ui\dialogs\admin_panel.py**: 31% (15/49 lines)
- **X communication\message_processing\command_parser.py**: 32% (183/570 lines)
- **X communication\message_processing\conversation_flow_manager.py**: 32% (311/975 lines)
- **X core\service_utilities.py**: 33% (52/157 lines)
- **X communication\message_processing\interaction_manager.py**: 35% (198/565 lines)
- **X core\ui_management.py**: 35% (30/85 lines)
- **X communication\message_processing\message_router.py**: 36% (43/119 lines)
- **X core\config.py**: 36% (151/424 lines)
- **X communication\communication_channels\discord\event_handler.py**: 37% (68/185 lines)
- **X ui\dialogs\checkin_management_dialog.py**: 39% (63/160 lines)
- **X ui\widgets\tag_widget.py**: 39% (83/213 lines)
- **X communication\communication_channels\base\command_registry.py**: 40% (47/117 lines)
- **X ui\widgets\checkin_settings_widget.py**: 40% (264/662 lines)
- **X communication\command_handlers\profile_handler.py**: 41% (118/289 lines)
- **X communication\core\factory.py**: 41% (19/46 lines)
- **X core\checkin_dynamic_manager.py**: 41% (134/323 lines)
- **X core\message_management.py**: 41% (172/420 lines)
- **X ui\widgets\channel_selection_widget.py**: 41% (34/82 lines)
- **X communication\__init__.py**: 44% (48/110 lines)
- **X tasks\task_management.py**: 45% (242/540 lines)
- **X communication\communication_channels\discord\welcome_handler.py**: 46% (18/39 lines)
- **X communication\core\retry_manager.py**: 46% (47/102 lines)
- **X core\user_data_validation.py**: 47% (141/301 lines)
- **X ui\widgets\dynamic_list_field.py**: 48% (58/120 lines)
- **X core\user_data_manager.py**: 49% (423/868 lines)
- **X ui\dialogs\account_creator_dialog.py**: 50% (326/648 lines)
- **X ui\widgets\period_row_widget.py**: 50% (123/244 lines)
- **X ai\cache_manager.py**: 51% (88/174 lines)
- **X communication\command_handlers\checkin_handler.py**: 51% (37/72 lines)
- **X communication\communication_channels\discord\webhook_handler.py**: 51% (76/149 lines)
- **X core\time_utilities.py**: 51% (54/106 lines)
- **X ui\widgets\task_settings_widget.py**: 52% (96/183 lines)
- **X user\context_manager.py**: 52% (79/153 lines)
- **X user\user_context.py**: 52% (44/84 lines)
- **X core\tags.py**: 53% (113/214 lines)
- **X core\error_handling.py**: 54% (210/386 lines)
- **X core\response_tracking.py**: 54% (63/117 lines)
- **X core\file_auditor.py**: 56% (51/91 lines)
- **X ui\dialogs\process_watcher_dialog.py**: 56% (165/296 lines)
- **X ai\prompt_manager.py**: 57% (64/112 lines)
- **X core\file_locking.py**: 58% (61/105 lines)
- **X user\user_preferences.py**: 58% (28/48 lines)
- **! core\user_data_handlers.py**: 61% (881/1447 lines)
- **! core\file_operations.py**: 66% (261/397 lines)
- **! core\backup_manager.py**: 68% (300/438 lines)
- **! ui\dialogs\category_management_dialog.py**: 68% (80/117 lines)
- **! communication\communication_channels\base\base_channel.py**: 71% (47/66 lines)
- **! core\schemas.py**: 76% (230/301 lines)
- *** communication\command_handlers\account_handler.py**: 82% (143/175 lines)
- *** ui\dialogs\task_management_dialog.py**: 84% (78/93 lines)
- *** core\__init__.py**: 90% (38/42 lines)
- *** ai\__init__.py**: 100% (7/7 lines)
- *** communication\command_handlers\__init__.py**: 100% (4/4 lines)
- *** communication\command_handlers\shared_types.py**: 100% (15/15 lines)
- *** communication\communication_channels\__init__.py**: 100% (1/1 lines)
- *** communication\core\welcome_manager.py**: 100% (47/47 lines)
- *** communication\message_processing\__init__.py**: 100% (2/2 lines)
- *** tasks\__init__.py**: 100% (2/2 lines)
- *** ui\__init__.py**: 100% (29/29 lines)
- *** ui\dialogs\__init__.py**: 100% (8/8 lines)
- *** ui\widgets\__init__.py**: 100% (8/8 lines)
- *** ui\widgets\category_selection_widget.py**: 100% (37/37 lines)
- *** user\__init__.py**: 100% (4/4 lines)

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