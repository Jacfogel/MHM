# Project Directory Tree

> **File**: `development_docs/DIRECTORY_TREE.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-04-29 15:07:44
> **Source**: `python development_tools/docs/generate_directory_tree.py` - Directory Tree Generator
> **Audience**: Human developer and AI collaborators
> **Purpose**: Visual representation of project directory structure
> **Status**: **ACTIVE** - Auto-generated from filesystem tree command

Folder PATH listing
Volume serial number is 5EAC-07BC
C:.
|   .coverage
|   .ruff.toml
|   ARCHITECTURE.md
|   CONFIGURATION_REFERENCE.md
|   DEVELOPMENT_WORKFLOW.md
|   DOCUMENTATION_GUIDE.md
|   HOW_TO_RUN.md
|   PROJECT_VISION.md
|   pyproject.toml
|   pytest.ini
|   README.md
|   requirements.txt
|   run_headless_service.py
|   TODO.md
|   
+---.cursor
|   |   worktrees.json
|   |   
|   +---commands
|   |       ai-functionality-tests.md
|   |       audit.md
|   |       backup.md
|   |       close.md
|   |       docs.md
|   |       explore-options.md
|   |       full-audit.md
|   |       refactor.md
|   |       review.md
|   |       start.md
|   |       test.md
|   |       triage-issue.md
|   |       
|   +---plans
|   |   |   conftest_refactor_plan_4aa2eb26.plan.md
|   |   |   continue_v5_roadmap_314d28fc.plan.md
|   |   |   dev_tools_v4_continuation_6131deb0.plan.md
|   |   |   invalidation_backlog_continuation_330c8fc9.plan.md
|   |   |   planning_documents_consolidation_f3a74815.plan.md
|   |   |   reduce_dependency_risk_70688c22.plan.md
|   |   |   unified_user_items_and_shared_helpers.plan.md
|   |   |   v5_dev-tools_continuation_5ab62a62.plan.md
|   |   |   v5_dev-tools_continuation_95e84204.plan.md
|   |   |   
|   \---rules
|           communication-guidelines.mdc
|           context.mdc
|           core-guidelines.mdc
|           critical.mdc
|           dev_tools.mdc
|           quality-standards.mdc
|           testing-guidelines.mdc
|           ui-guidelines.mdc
|           
+---ai
|   |   cache_manager.py
|   |   chatbot.py
|   |   context_builder.py
|   |   conversation_history.py
|   |   lm_studio_manager.py
|   |   prompt_manager.py
|   |   SYSTEM_AI_GUIDE.md
|   |   __init__.py
|   |   
+---ai_development_docs
|   |   AI_ARCHITECTURE.md
|   |   AI_BACKUP_GUIDE.md
|   |   AI_CHANGELOG.md
|   |   AI_DEVELOPMENT_WORKFLOW.md
|   |   AI_DOCUMENTATION_GUIDE.md
|   |   AI_ERROR_HANDLING_GUIDE.md
|   |   AI_FUNCTION_REGISTRY.md
|   |   AI_LEGACY_COMPATIBILITY_GUIDE.md
|   |   AI_LOGGING_GUIDE.md
|   |   AI_MODULE_DEPENDENCIES.md
|   |   AI_SESSION_STARTER.md
|   |   AI_TESTING_GUIDE.md
|   |   
+---communication
|   |   COMMUNICATION_GUIDE.md
|   |   __init__.py
|   |   
|   +---command_handlers
|   |   |   account_handler.py
|   |   |   analytics_handler.py
|   |   |   base_handler.py
|   |   |   checkin_handler.py
|   |   |   interaction_handlers.py
|   |   |   notebook_handler.py
|   |   |   profile_handler.py
|   |   |   schedule_handler.py
|   |   |   shared_types.py
|   |   |   task_handler.py
|   |   |   __init__.py
|   |   |   
|   +---communication_channels
|   |   |   __init__.py
|   |   |   
|   |   +---base
|   |   |   |   base_channel.py
|   |   |   |   command_registry.py
|   |   |   |   message_formatter.py
|   |   |   |   rich_formatter.py
|   |   |   |   
|   |   +---discord
|   |   |   |   account_flow_handler.py
|   |   |   |   api_client.py
|   |   |   |   bot.py
|   |   |   |   checkin_view.py
|   |   |   |   DISCORD_GUIDE.md
|   |   |   |   event_handler.py
|   |   |   |   task_reminder_view.py
|   |   |   |   webhook_handler.py
|   |   |   |   webhook_server.py
|   |   |   |   welcome_handler.py
|   |   |   |   
|   |   +---email
|   |   |   |   bot.py
|   |   |   |   
|   +---core
|   |   |   channel_monitor.py
|   |   |   channel_orchestrator.py
|   |   |   factory.py
|   |   |   retry_manager.py
|   |   |   welcome_manager.py
|   |   |   __init__.py
|   |   |   
|   +---message_processing
|   |   |   command_parser.py
|   |   |   conversation_flow_manager.py
|   |   |   intent_validation.py
|   |   |   interaction_manager.py
|   |   |   message_router.py
|   |   |   __init__.py
|   |   |   
+---core
|   |   auto_cleanup.py
|   |   backup_manager.py
|   |   checkin_analytics.py
|   |   checkin_dynamic_manager.py
|   |   config.py
|   |   error_handling.py
|   |   ERROR_HANDLING_GUIDE.md
|   |   file_auditor.py
|   |   file_locking.py
|   |   file_operations.py
|   |   headless_service.py
|   |   logger.py
|   |   message_analytics.py
|   |   message_management.py
|   |   network_probe.py
|   |   response_tracking.py
|   |   scheduler.py
|   |   schedule_management.py
|   |   schedule_utilities.py
|   |   schemas.py
|   |   service.py
|   |   service_utilities.py
|   |   tags.py
|   |   time_format_constants.py
|   |   time_utilities.py
|   |   ui_management.py
|   |   user_data_manager.py
|   |   USER_DATA_MODEL.md
|   |   user_data_presets.py
|   |   user_data_read.py
|   |   user_data_registry.py
|   |   user_data_schedule_defaults.py
|   |   user_data_updates.py
|   |   user_data_v2.py
|   |   user_data_validation.py
|   |   user_data_write.py
|   |   user_item_storage.py
|   |   user_lookup.py
|   |   user_management.py
|   |   __init__.py
|   |   
+---data
    (data files)
+---development_docs
|   |   BACKUP_GUIDE.md
|   |   CHANGELOG_DETAIL.md
|   |   DIRECTORY_TREE.md
|   |   DUPLICATE_FUNCTIONS_INVESTIGATION.md
|   |   FUNCTION_REGISTRY_DETAIL.md
|   |   LEGACY_REFERENCE_REPORT.md
|   |   LIST_OF_LISTS.md
|   |   MODULE_DEPENDENCIES_DETAIL.md
|   |   NOTES_PLAN.md
|   |   PLANS.md
|   |   TASKS_PLAN.md
|   |   TEST_COVERAGE_REPORT.md
|   |   TEST_PLAN.md
|   |   UNUSED_IMPORTS_REPORT.md
|   |   
|   \---changelog_history
|           CHANGELOG_DETAIL_2025_08.md
|           CHANGELOG_DETAIL_2025_09.md
|           CHANGELOG_DETAIL_2025_10.md
|           CHANGELOG_DETAIL_2025_11.md
|           CHANGELOG_DETAIL_2025_12.md
|           
+---development_tools
|   |   AI_DEVELOPMENT_TOOLS_GUIDE.md
|   |   AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md
|   |   AI_PRIORITIES.md
|   |   AI_STATUS.md
|   |   CONSOLIDATED_REPORT.md
|   |   DEVELOPMENT_TOOLS_GUIDE.md
|   |   DEV_TOOLS_CONSOLIDATED_REPORT.md
|   |   DEV_TOOLS_PRIORITIES.md
|   |   DEV_TOOLS_STATUS.md
|   |   run_development_tools.py
|   |   run_dev_tools.py
|   |   __init__.py
|   |   
|   +---ai_work
|   |   |   analyze_ai_work.py
|   |   |   __init__.py
|   |   |   
|   |   +---jsons
    (JSON files created by development tools)
|   +---config
|   |   |   analyze_config.py
|   |   |   audit_tool_matrix.json
|   |   |   config.py
|   |   |   development_tools_config.json
|   |   |   development_tools_config.json.example
|   |   |   pyrightconfig.json
|   |   |   ruff.toml
|   |   |   sync_ruff_toml.py
|   |   |   tool_cache_inventory.json
|   |   |   __init__.py
|   |   |   
|   |   +---jsons
    (JSON files created by development tools)
|   +---docs
|   |   |   analyze_ascii_compliance.py
|   |   |   analyze_documentation.py
|   |   |   analyze_documentation_sync.py
|   |   |   analyze_heading_numbering.py
|   |   |   analyze_missing_addresses.py
|   |   |   analyze_path_drift.py
|   |   |   analyze_unconverted_links.py
|   |   |   example_marker_validation.py
|   |   |   fix_documentation.py
|   |   |   fix_documentation_addresses.py
|   |   |   fix_documentation_ascii.py
|   |   |   fix_documentation_headings.py
|   |   |   fix_documentation_links.py
|   |   |   fix_version_sync.py
|   |   |   generate_directory_tree.py
|   |   |   __init__.py
|   |   |   
|   |   +---jsons
    (JSON files created by development tools)
|   +---error_handling
|   |   |   analyze_error_handling.py
|   |   |   generate_error_handling_report.py
|   |   |   __init__.py
|   |   |   
|   |   +---jsons
    (JSON files created by development tools)
|   +---functions
|   |   |   analyze_duplicate_functions.py
|   |   |   analyze_functions.py
|   |   |   analyze_function_patterns.py
|   |   |   analyze_function_registry.py
|   |   |   analyze_module_refactor_candidates.py
|   |   |   analyze_package_exports.py
|   |   |   fix_function_docstrings.py
|   |   |   generate_function_registry.py
|   |   |   __init__.py
|   |   |   
|   |   +---jsons
    (JSON files created by development tools)
|   +---imports
|   |   |   analyze_dependency_patterns.py
|   |   |   analyze_dev_tools_import_boundaries.py
|   |   |   analyze_module_dependencies.py
|   |   |   analyze_module_imports.py
|   |   |   analyze_unused_imports.py
|   |   |   generate_module_dependencies.py
|   |   |   generate_unused_imports_report.py
|   |   |   __init__.py
|   |   |   
|   |   +---jsons
    (JSON files created by development tools)
|   +---legacy
|   |   |   analyze_legacy_references.py
|   |   |   fix_legacy_references.py
|   |   |   generate_legacy_reference_report.py
|   |   |   __init__.py
|   |   |   
|   |   +---jsons
    (JSON files created by development tools)
|   +---reports
|   |   |   analyze_system_signals.py
|   |   |   decision_support.py
|   |   |   generate_consolidated_report.py
|   |   |   quick_status.py
|   |   |   __init__.py
|   |   |   
|   |   +---jsons
    (JSON files created by development tools)
|   |   +---logs
    (log files)
|   |   +---scopes
|   |   |   +---dev_tools
|   |   |   |   \---jsons
    (JSON files created by development tools)
|   |   |   \---full
|   |   |       |   analysis_detailed_results.json
|   |   |       |   
|   |   |       \---jsons
    (JSON files created by development tools)
|   +---shared
|   |   |   audit_signal_state.py
|   |   |   audit_storage_scope.py
|   |   |   audit_tiers.py
|   |   |   audit_tool_matrix.py
|   |   |   backup_inventory.py
|   |   |   backup_policy_models.py
|   |   |   backup_reports.py
|   |   |   cache_dependency_paths.py
|   |   |   cli_interface.py
|   |   |   common.py
|   |   |   constants.py
|   |   |   error_helpers.py
|   |   |   exclusion_utilities.py
|   |   |   export_code_snapshot.py
|   |   |   export_docs_snapshot.py
|   |   |   file_rotation.py
|   |   |   fix_project_cleanup.py
|   |   |   lock_state.py
|   |   |   measure_tool_timings.py
|   |   |   mtime_cache.py
|   |   |   output_storage.py
|   |   |   result_format.py
|   |   |   retention_engine.py
|   |   |   sharded_static_analysis.py
|   |   |   standard_exclusions.py
|   |   |   static_analysis_shard_cache.py
|   |   |   time_helpers.py
|   |   |   tool_cache_inventory.py
|   |   |   tool_guide.py
|   |   |   tool_metadata.py
|   |   |   verify_tool_storage.py
|   |   |   __init__.py
|   |   |   
|   |   +---service
|   |   |   |   audit_orchestration.py
|   |   |   |   commands.py
|   |   |   |   core.py
|   |   |   |   data_freshness_audit.py
|   |   |   |   data_loading.py
|   |   |   |   report_generation.py
|   |   |   |   report_generation_linkify.py
|   |   |   |   tool_wrappers.py
|   |   |   |   utilities.py
|   |   |   |   __init__.py
|   |   |   |   
|   +---static_checks
|   |   |   analyze_bandit.py
|   |   |   analyze_pip_audit.py
|   |   |   analyze_pyright.py
|   |   |   analyze_ruff.py
|   |   |   check_channel_loggers.py
|   |   |   
|   |   +---jsons
    (JSON files created by development tools)
|   +---tests
|   |   |   .coverage
|   |   |   analyze_test_coverage.py
|   |   |   analyze_test_markers.py
|   |   |   coverage.ini
|   |   |   coverage_dev_tools.ini
|   |   |   dev_tools_coverage_cache.py
|   |   |   domain_mapper.py
|   |   |   fix_test_markers.py
|   |   |   flaky_detector.py
|   |   |   generate_test_coverage_report.py
|   |   |   run_test_coverage.py
|   |   |   test_file_coverage_cache.py
|   |   |   verify_process_cleanup.py
|   |   |   __init__.py
|   |   |   
|   |   +---jsons
    (JSON files created by development tools)
|   |   +---logs
    (log files)
+---logs
    (log files)
+---notebook
|   |   notebook_data_handlers.py
|   |   notebook_data_manager.py
|   |   notebook_schemas.py
|   |   notebook_validation.py
|   |   __init__.py
|   |   
+---resources
|   |   assistant_system_prompt.txt
|   |   default_tags.json
|   |   presets.json
|   |   
|   +---default_checkin
|   |       questions.json
|   |       question_templates.json
|   |       responses.json
|   |       
|   \---default_messages
|           fun_facts.json
|           health.json
|           motivational.json
|           quotes_to_ponder.json
|           word_of_the_day.json
|           
+---styles
|       admin_theme.qss
|       
+---tasks
|   |   task_data_handlers.py
|   |   task_data_manager.py
|   |   task_schemas.py
|   |   task_validation.py
|   |   __init__.py
|   |   
+---tests
|   |   conftest.py
|   |   DEVELOPMENT_TOOLS_TESTING_GUIDE.md
|   |   MANUAL_DISCORD_TEST_GUIDE.md
|   |   MANUAL_TESTING_GUIDE.md
|   |   TESTING_GUIDE.md
|   |   __init__.py
|   |   
|   +---ai
|   |   |   ai_response_validator.py
|   |   |   ai_test_base.py
|   |   |   run_ai_functionality_tests.py
|   |   |   SYSTEM_AI_FUNCTIONALITY_TESTING_GUIDE.md
|   |   |   test_ai_advanced.py
|   |   |   test_ai_cache.py
|   |   |   test_ai_core.py
|   |   |   test_ai_errors.py
|   |   |   test_ai_functionality_manual.py
|   |   |   test_ai_integration.py
|   |   |   test_ai_performance.py
|   |   |   test_ai_quality.py
|   |   |   test_cache_manager.py
|   |   |   test_context_includes_recent_messages.py
|   |   |   
|   +---behavior
|   |   |   test_account_handler_behavior.py
|   |   |   test_account_management_real_behavior.py
|   |   |   test_ai_chatbot_behavior.py
|   |   |   test_ai_context_builder_behavior.py
|   |   |   test_ai_context_builder_coverage_expansion.py
|   |   |   test_ai_conversation_history_behavior.py
|   |   |   test_analytics_handler_behavior.py
|   |   |   test_auto_cleanup_behavior.py
|   |   |   test_backup_manager_behavior.py
|   |   |   test_base_handler_behavior.py
|   |   |   test_chat_interaction_storage_real_scenarios.py
|   |   |   test_checkin_analytics_behavior.py
|   |   |   test_checkin_expiry_semantics.py
|   |   |   test_checkin_handler_behavior.py
|   |   |   test_checkin_questions_enhancement.py
|   |   |   test_command_discovery_help.py
|   |   |   test_command_parser_coverage_expansion_phase3_simple.py
|   |   |   test_communication_behavior.py
|   |   |   test_communication_command_parser_behavior.py
|   |   |   test_communication_factory_coverage_expansion.py
|   |   |   test_communication_interaction_manager_behavior.py
|   |   |   test_communication_manager_behavior.py
|   |   |   test_communication_manager_coverage_expansion.py
|   |   |   test_comprehensive_quantitative_analytics.py
|   |   |   test_config_coverage_expansion_phase3_simple.py
|   |   |   test_conversation_behavior.py
|   |   |   test_conversation_flow_manager_behavior.py
|   |   |   test_core_message_management_coverage_expansion.py
|   |   |   test_core_service_coverage_expansion.py
|   |   |   test_discord_advanced_automation.py
|   |   |   test_discord_automation_complete.py
|   |   |   test_discord_bot_behavior.py
|   |   |   test_discord_checkin_retry_behavior.py
|   |   |   test_discord_task_reminder_followup.py
|   |   |   test_dynamic_checkin_behavior.py
|   |   |   test_email_bot_behavior.py
|   |   |   test_enhanced_command_parser_behavior.py
|   |   |   test_error_handling_coverage_expansion_phase3_final.py
|   |   |   test_headless_service_behavior.py
|   |   |   test_interaction_handlers_behavior.py
|   |   |   test_interaction_handlers_coverage_expansion.py
|   |   |   test_logger_behavior.py
|   |   |   test_logger_coverage_expansion.py
|   |   |   test_logger_coverage_expansion_phase3_simple.py
|   |   |   test_message_analytics_behavior.py
|   |   |   test_message_behavior.py
|   |   |   test_message_router_behavior.py
|   |   |   test_natural_language_command_detection.py
|   |   |   test_notebook_handler_behavior.py
|   |   |   test_observability_logging.py
|   |   |   test_profile_display_formatting.py
|   |   |   test_profile_handler_behavior.py
|   |   |   test_quantitative_analytics_expansion.py
|   |   |   test_response_tracking_behavior.py
|   |   |   test_scheduler_behavior.py
|   |   |   test_scheduler_coverage_expansion.py
|   |   |   test_schedule_handler_behavior.py
|   |   |   test_schedule_management_behavior.py
|   |   |   test_schedule_suggestions.py
|   |   |   test_service_behavior.py
|   |   |   test_service_utilities_behavior.py
|   |   |   test_static_logging_check.py
|   |   |   test_task_behavior.py
|   |   |   test_task_cleanup_bug.py
|   |   |   test_task_crud_disambiguation.py
|   |   |   test_task_error_handling.py
|   |   |   test_task_handler_behavior.py
|   |   |   test_task_management_coverage_expansion.py
|   |   |   test_task_reminder_followup_behavior.py
|   |   |   test_task_suggestion_relevance.py
|   |   |   test_ui_app_behavior.py
|   |   |   test_ui_automation_complete.py
|   |   |   test_user_context_behavior.py
|   |   |   test_user_data_flow_architecture.py
|   |   |   test_user_management_coverage_expansion.py
|   |   |   test_utilities_demo.py
|   |   |   test_webhook_handler_behavior.py
|   |   |   test_webhook_server_behavior.py
|   |   |   test_welcome_handler_behavior.py
|   |   |   test_welcome_manager_behavior.py
|   |   |   
|   +---communication
|   |   |   test_channel_monitor.py
|   |   |   test_retry_manager.py
|   |   |   
|   +---core
|   |   |   test_file_auditor.py
|   |   |   test_file_auditor_gap_coverage.py
|   |   |   test_message_management.py
|   |   |   test_python_interpreter_selection.py
|   |   |   test_schedule_utilities.py
|   |   |   test_service_message_content_helpers.py
|   |   |   test_service_request_helpers.py
|   |   |   test_user_data_read_scenarios.py
|   |   |   
|   +---data
    (data files)
|   +---development_tools
|   |   |   conftest.py
|   |   |   regenerate_fixture_status_files.py
|   |   |   test_analysis_tool_validation.py
|   |   |   test_analysis_validation_framework.py
|   |   |   test_analyze_ai_work.py
|   |   |   test_analyze_ascii_compliance.py
|   |   |   test_analyze_config.py
|   |   |   test_analyze_dependency_patterns.py
|   |   |   test_analyze_dev_tools_import_boundaries.py
|   |   |   test_analyze_documentation.py
|   |   |   test_analyze_duplicate_functions.py
|   |   |   test_analyze_error_handling.py
|   |   |   test_analyze_functions.py
|   |   |   test_analyze_function_patterns.py
|   |   |   test_analyze_function_registry.py
|   |   |   test_analyze_heading_numbering.py
|   |   |   test_analyze_missing_addresses.py
|   |   |   test_analyze_module_dependencies.py
|   |   |   test_analyze_module_imports_cli.py
|   |   |   test_analyze_module_refactor_candidates.py
|   |   |   test_analyze_package_exports.py
|   |   |   test_analyze_security_static_checks.py
|   |   |   test_analyze_system_signals_additional.py
|   |   |   test_analyze_test_coverage.py
|   |   |   test_analyze_test_markers.py
|   |   |   test_analyze_test_markers_domain.py
|   |   |   test_analyze_unconverted_links.py
|   |   |   test_analyze_unused_imports.py
|   |   |   test_audit_orchestration_helpers.py
|   |   |   test_audit_signal_state.py
|   |   |   test_audit_status_updates.py
|   |   |   test_audit_storage_scope.py
|   |   |   test_audit_strict_mode.py
|   |   |   test_audit_tier_comprehensive.py
|   |   |   test_audit_tier_e2e_verification.py
|   |   |   test_audit_tool_matrix_policy.py
|   |   |   test_backup_inventory.py
|   |   |   test_backup_policy_models.py
|   |   |   test_backup_reports.py
|   |   |   test_cache_dependency_paths.py
|   |   |   test_changelog_trim_tooling.py
|   |   |   test_check_channel_loggers.py
|   |   |   test_cli_interface.py
|   |   |   test_commands_additional_helpers.py
|   |   |   test_commands_backup_flow.py
|   |   |   test_commands_coverage_helpers.py
|   |   |   test_commands_docs_locks.py
|   |   |   test_commands_docs_workflow.py
|   |   |   test_common_shared.py
|   |   |   test_config.json
|   |   |   test_config.py
|   |   |   test_constants.py
|   |   |   test_constants_config_alignment.py
|   |   |   test_constants_config_import_order.py
|   |   |   test_data_freshness_audit.py
|   |   |   test_data_loading_helpers.py
|   |   |   test_decision_support.py
|   |   |   test_deprecation_inventory_guard.py
|   |   |   test_deprecation_inventory_policy.py
|   |   |   test_development_tools_package_init.py
|   |   |   test_dev_tools_coverage_cache.py
|   |   |   test_dev_tools_scoped_status_report.py
|   |   |   test_directory_taxonomy_policy.py
|   |   |   test_documentation_sync_checker.py
|   |   |   test_error_scenarios.py
|   |   |   test_example_marker_validation.py
|   |   |   test_exclusion_utilities.py
|   |   |   test_export_snapshots.py
|   |   |   test_false_negative_detection.py
|   |   |   test_file_rotation.py
|   |   |   test_fixture_status_files.py
|   |   |   test_fix_documentation.py
|   |   |   test_fix_documentation_addresses.py
|   |   |   test_fix_documentation_ascii.py
|   |   |   test_fix_documentation_headings.py
|   |   |   test_fix_documentation_links.py
|   |   |   test_fix_function_docstrings.py
|   |   |   test_fix_project_cleanup.py
|   |   |   test_fix_test_markers.py
|   |   |   test_fix_version_sync_file_discovery.py
|   |   |   test_fix_version_sync_todo_sync.py
|   |   |   test_flaky_detector.py
|   |   |   test_generate_consolidated_report.py
|   |   |   test_generate_directory_tree.py
|   |   |   test_generate_error_handling_recommendations.py
|   |   |   test_generate_error_handling_report.py
|   |   |   test_generate_function_registry.py
|   |   |   test_generate_module_dependencies.py
|   |   |   test_generate_unused_imports_report.py
|   |   |   test_import_boundary_policy.py
|   |   |   test_integration_workflows.py
|   |   |   test_legacy_reference_cleanup.py
|   |   |   test_measure_tool_timings.py
|   |   |   test_mtime_cache.py
|   |   |   test_output_storage_archiving.py
|   |   |   test_output_storage_helpers.py
|   |   |   test_path_drift_detection.py
|   |   |   test_path_drift_integration.py
|   |   |   test_path_drift_verification_comprehensive.py
|   |   |   test_pyright_config_paths.py
|   |   |   test_regenerate_coverage_metrics.py
|   |   |   test_report_generation_dev_tools_scope.py
|   |   |   test_report_generation_helpers_pure.py
|   |   |   test_report_generation_quick_wins.py
|   |   |   test_report_generation_static_analysis.py
|   |   |   test_result_format.py
|   |   |   test_retention_engine.py
|   |   |   test_run_development_tools.py
|   |   |   test_run_dev_tools.py
|   |   |   test_run_test_coverage_helpers.py
|   |   |   test_service_utilities.py
|   |   |   test_sharded_static_analysis.py
|   |   |   test_sharded_static_scan_wiring.py
|   |   |   test_standard_exclusions.py
|   |   |   test_static_analysis_tools.py
|   |   |   test_status_file_timing.py
|   |   |   test_supporting_tools.py
|   |   |   test_sync_ruff_toml.py
|   |   |   test_test_file_coverage_cache.py
|   |   |   test_tooling_policy_consistency.py
|   |   |   test_tool_cache_inventory_policy.py
|   |   |   test_tool_guide.py
|   |   |   test_tool_wrappers_additional.py
|   |   |   test_tool_wrappers_branch_paths.py
|   |   |   test_tool_wrappers_cache_helpers.py
|   |   |   test_tool_wrappers_package_exports.py
|   |   |   test_tool_wrappers_static_analysis.py
|   |   |   test_verification_summary.py
|   |   |   test_verify_process_cleanup.py
|   |   |   test_verify_tool_storage.py
|   |   |   __init__.py
|   |   |   
|   +---fixtures
|   +---integration
|   |   |   test_account_lifecycle.py
|   |   |   test_account_management.py
|   |   |   test_error_handling_improvements.py
|   |   |   test_notebook_validation_integration.py
|   |   |   test_orphaned_reminder_cleanup.py
|   |   |   test_task_cleanup_real.py
|   |   |   test_task_cleanup_real_bug_verification.py
|   |   |   test_task_cleanup_silent_failure.py
|   |   |   test_task_reminder_integration.py
|   |   |   test_user_creation.py
|   |   |   
|   |   +---data
    (data files)
|   +---logs
    (log files)
|   +---notebook
|   |       __init__.py
|   |       
|   +---test_helpers
|   |   |   __init__.py
|   |   |   
|   |   +---test_support
|   |   |   |   conftest_cleanup.py
|   |   |   |   conftest_cleanup_impl.py
|   |   |   |   conftest_hooks.py
|   |   |   |   conftest_logging.py
|   |   |   |   conftest_logging_impl.py
|   |   |   |   conftest_mocks.py
|   |   |   |   conftest_user_data.py
|   |   |   |   test_helpers.py
|   |   |   |   test_isolation.py
|   |   |   |   __init__.py
|   |   |   |   
|   |   +---test_utilities
|   |   |   |   test_data_factory.py
|   |   |   |   test_data_manager.py
|   |   |   |   test_log_path_mocks.py
|   |   |   |   test_user_data_factory.py
|   |   |   |   test_user_factory.py
|   |   |   |   __init__.py
|   |   |   |   
|   +---ui
|   |   |   test_account_creation_ui.py
|   |   |   test_account_creator_dialog_validation.py
|   |   |   test_category_management_dialog.py
|   |   |   test_channel_management_dialog_coverage_expansion.py
|   |   |   test_channel_status_log_merge.py
|   |   |   test_checkin_settings_widget_question_counts.py
|   |   |   test_dialogs.py
|   |   |   test_dialog_behavior.py
|   |   |   test_dialog_coverage_expansion.py
|   |   |   test_message_editor_dialog.py
|   |   |   test_process_watcher_dialog.py
|   |   |   test_signal_handler_integration.py
|   |   |   test_task_crud_dialog.py
|   |   |   test_task_management_dialog.py
|   |   |   test_task_settings_widget.py
|   |   |   test_ui_app_qt_core.py
|   |   |   test_ui_app_qt_main.py
|   |   |   test_ui_button_verification.py
|   |   |   test_ui_components_headless.py
|   |   |   test_ui_generation.py
|   |   |   test_ui_user_combo_helpers.py
|   |   |   test_ui_widgets_coverage_expansion.py
|   |   |   test_user_analytics_dialog.py
|   |   |   test_user_profile_dialog_coverage_expansion.py
|   |   |   test_widget_behavior.py
|   |   |   test_widget_behavior_simple.py
|   |   |   
|   +---unit
|   |   |   debug_file_paths.py
|   |   |   test_admin_panel.py
|   |   |   test_ai_chatbot_helpers.py
|   |   |   test_ai_deterministic.py
|   |   |   test_analytics_handler.py
|   |   |   test_analytics_handler_helper_branches.py
|   |   |   test_auto_cleanup_backup_retention.py
|   |   |   test_auto_cleanup_gap_coverage.py
|   |   |   test_auto_cleanup_logic.py
|   |   |   test_auto_cleanup_paths.py
|   |   |   test_backup_manager_helpers.py
|   |   |   test_channel_orchestrator.py
|   |   |   test_channel_orchestrator_message_selection.py
|   |   |   test_checkin_analytics_conversion.py
|   |   |   test_checkin_management_dialog.py
|   |   |   test_checkin_view.py
|   |   |   test_cleanup.py
|   |   |   test_command_parser_helpers.py
|   |   |   test_command_parser_notebook_entities_expansion.py
|   |   |   test_command_parser_rule_based_patterns_expansion.py
|   |   |   test_command_parser_task_entities_expansion.py
|   |   |   test_command_registry.py
|   |   |   test_communication_core_init.py
|   |   |   test_communication_init.py
|   |   |   test_config.py
|   |   |   test_config_branch_coverage.py
|   |   |   test_conversation_flow_reminder_helpers.py
|   |   |   test_dialog_helpers.py
|   |   |   test_discord_api_client.py
|   |   |   test_discord_event_handler.py
|   |   |   test_email_bot_body_extraction.py
|   |   |   test_email_bot_gap_coverage.py
|   |   |   test_enhanced_checkin_responses.py
|   |   |   test_error_categorization.py
|   |   |   test_error_handling.py
|   |   |   test_file_locking.py
|   |   |   test_file_locking_platform_branches.py
|   |   |   test_file_operations.py
|   |   |   test_file_operations_branch_coverage.py
|   |   |   test_generate_ui_files_script.py
|   |   |   test_interaction_handlers_helpers.py
|   |   |   test_interaction_handlers_help_and_registry.py
|   |   |   test_lm_studio_manager.py
|   |   |   test_logger_unit.py
|   |   |   test_logging_components.py
|   |   |   test_message_formatter.py
|   |   |   test_notebook_data_manager_gap_coverage.py
|   |   |   test_notebook_handler_edge_cases.py
|   |   |   test_notebook_handler_pagination_formatting.py
|   |   |   test_notebook_validation.py
|   |   |   test_notebook_validation_error_handling.py
|   |   |   test_no_prints_policy.py
|   |   |   test_profile_handler.py
|   |   |   test_profile_handler_gap_coverage.py
|   |   |   test_prompt_manager.py
|   |   |   test_recurring_tasks.py
|   |   |   test_rich_formatter.py
|   |   |   test_run_tests_interrupts.py
|   |   |   test_schedule_management.py
|   |   |   test_schemas_validation.py
|   |   |   test_schema_validation_helpers.py
|   |   |   test_service_utilities_network.py
|   |   |   test_tags.py
|   |   |   test_tags_expansion.py
|   |   |   test_tags_gap_coverage.py
|   |   |   test_test_policy_guards.py
|   |   |   test_ui_management.py
|   |   |   test_user_context.py
|   |   |   test_user_data_handlers.py
|   |   |   test_user_data_loader_idempotency.py
|   |   |   test_user_data_loader_order_insensitivity.py
|   |   |   test_user_data_manager.py
|   |   |   test_user_data_v2_migration.py
|   |   |   test_user_data_validation_user_id.py
|   |   |   test_user_item_storage.py
|   |   |   test_user_management.py
|   |   |   test_user_package_exports.py
|   |   |   test_user_preferences.py
|   |   |   test_validation.py
|   |   |   test_webhook_handler_gap_coverage.py
|   |   |   
+---ui
|   |   generate_ui_files.py
|   |   ui_app_qt.py
|   |   UI_GUIDE.md
|   |   __init__.py
|   |   
|   +---designs
|   |       account_creator_dialog.ui
|   |       admin_panel.ui
|   |       category_management_dialog.ui
|   |       category_selection_widget.ui
|   |       channel_management_dialog.ui
|   |       channel_selection_widget.ui
|   |       checkin_element_template.ui
|   |       checkin_management_dialog.ui
|   |       checkin_settings_widget.ui
|   |       dynamic_list_field_template.ui
|   |       message_editor_dialog.ui
|   |       period_row_template.ui
|   |       schedule_editor_dialog.ui
|   |       tag_widget.ui
|   |       task_completion_dialog.ui
|   |       task_crud_dialog.ui
|   |       task_edit_dialog.ui
|   |       task_management_dialog.ui
|   |       task_settings_widget.ui
|   |       user_analytics_dialog.ui
|   |       user_profile_management_dialog.ui
|   |       user_profile_settings_widget.ui
|   |       
|   +---dialogs
    (log files)
|   +---generated
|   +---widgets
|   |   |   category_selection_widget.py
|   |   |   channel_selection_widget.py
|   |   |   checkin_settings_widget.py
|   |   |   dynamic_list_container.py
|   |   |   dynamic_list_field.py
|   |   |   period_row_widget.py
|   |   |   tag_widget.py
|   |   |   task_settings_widget.py
|   |   |   user_profile_settings_widget.py
|   |   |   __init__.py
|   |   |   
+---user
|   |   context_manager.py
|   |   user_context.py
|   |   user_preferences.py
|   |   __init__.py
|   |   

---

*Generated by generate_directory_tree.py*