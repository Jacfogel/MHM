# AI Module Dependencies - Key Relationships & Patterns

> **File**: `ai_development_docs/AI_MODULE_DEPENDENCIES.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-05-22 01:10:00
> **Source**: `python development_tools/generate_module_dependencies.py` - Module Dependencies Generator

> **Audience**: AI collaborators
> **Purpose**: Essential module relationships and dependency patterns for AI context
> **Style**: Pattern-focused, relationship-driven, actionable

## Current Status

### Dependency Coverage: 100.0% - COMPLETED
- **Files Scanned**: 151
- **Total Imports**: 1514
- **Standard Library**: 432 (28.5%)
- **Third-Party**: 234 (15.5%)
- **Local Imports**: 848 (56.0%)

## Dependency Decision Trees

### Need Core System Access?
Core System Dependencies:
- Configuration and Setup
  - core/config.py <- standard library (contextlib, logging, os, pathlib), third-party (dotenv), error_handling
  - core/logger.py <- standard library (contextlib, glob, gzip, json), error_handling, time_utilities, config
- Data Management
  - core/file_operations.py <- standard library (importlib, json, os, pathlib), third-party (storage.user_data_v2_base), logger, config, error_handling, time_utilities, file_auditor (+1 more)
- Error Handling
  - core/error_handling.py <- standard library (asyncio, collections.abc, contextlib, functools), network_probe, time_utilities

### Need AI or Chatbot Support?
AI System Dependencies:
- AI Core
  - ai/cache_manager.py <- standard library (dataclasses, hashlib, threading, time), logger, error_handling, config
  - ai/chatbot.py <- standard library (asyncio, collections, os, threading), third-party (psutil), logger, config, response_tracking, context_manager, prompt_manager (+9 more)
- Command Processing
  - communication/command_handlers/account_handler.py <- standard library (secrets, string, typing), third-party (storage.user_data_operations), logger, error_handling, core, base_handler, shared_types (+1 more)
  - communication/command_handlers/analytics_handler.py <- standard library (collections, typing), logger, error_handling, base_handler, shared_types, response_tracking (+5 more)
  - communication/command_handlers/base_handler.py <- standard library (abc), third-party (storage.user_data_validation), shared_types, logger, error_handling
- Communication Integration
  - communication/communication_channels/__init__.py <- none
  - communication/core/channel_monitor.py <- standard library (threading, time, typing), time_utilities, logger, error_handling, base_channel

### Need Communication Channel Coverage?
Communication Dependencies:
- Channel Infrastructure
  - communication/command_handlers/base_handler.py <- standard library (abc), third-party (storage.user_data_validation), shared_types, logger, error_handling
  - communication/core/factory.py <- standard library (importlib), base_channel, logger, error_handling, config
  - communication/communication_channels/base/base_channel.py <- standard library (abc, dataclasses, enum, typing), logger, error_handling
- Specific Channels
  - communication/communication_channels/discord/account_flow_handler.py <- standard library (contextlib), third-party (discord, storage.user_data_presets), logger, error_handling, shared_types, account_handler
  - communication/communication_channels/discord/api_client.py <- standard library (asyncio, dataclasses, time, typing), third-party (discord), logger, error_handling
- Conversation Flow
  - communication/message_processing/conversation_flow_manager.py <- standard library (contextlib, datetime, importlib, random), third-party (storage.runtime_state_storage, storage.user_data_v2_base), chatbot, logger, core, response_tracking, error_handling (+14 more)
  - communication/communication_channels/discord/account_flow_handler.py <- standard library (contextlib), third-party (discord, storage.user_data_presets), logger, error_handling, shared_types, account_handler

### Need UI Dependencies?
UI Dependencies:
- Main Application
  - ui/ui_app_qt.py <- standard library (contextlib, json, os, pathlib), third-party (PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets), launch_env, time_utilities, logger, config, error_handling (+20 more)
- Dialogs
  - ui/dialogs/account_creator_dialog.py <- standard library (contextlib, pathlib, time, typing), third-party (PySide6.QtCore, PySide6.QtWidgets, storage.user_data_operations), logger, core, error_handling, dialog_helpers, category_selection_widget (+9 more)
  - ui/dialogs/admin_panel.py <- third-party (PySide6.QtCore, PySide6.QtWidgets), logger, error_handling
  - ui/dialogs/category_management_dialog.py <- third-party (PySide6.QtCore, PySide6.QtWidgets), category_management_dialog_pyqt, category_selection_widget, logger, core, error_handling (+1 more)
- Widgets
  - ui/widgets/category_selection_widget.py <- third-party (PySide6.QtWidgets, storage.user_data_validation), category_selection_widget_pyqt, error_handling, logger
  - ui/widgets/channel_selection_widget.py <- third-party (PySide6.QtWidgets), channel_selection_widget_pyqt, core, logger, error_handling
  - ui/widgets/checkin_settings_widget.py <- standard library (re), third-party (PySide6.QtCore, PySide6.QtWidgets), checkin_settings_widget_pyqt, ui_management, period_row_management, core, error_handling (+2 more)


## Key Dependency Patterns

### Core -> Communication and AI (most common)
Communication and AI modules depend on core system modules.
- `ai/cache_manager.py` -> core.logger, core.error_handling, core.config
- `ai/chatbot.py` -> core.logger, core.config, core.response_tracking
- `ai/command_interpreter.py` -> core.error_handling

### UI -> Core
UI modules rely on core configuration and data access.
- `ui/generate_ui_files.py` -> core.error_handling, core.time_utilities
- `ui/period_row_management.py` -> core.error_handling, core.logger, core.ui_management
- `ui/ui_app_qt.py` -> core.launch_env, core.time_utilities, core.logger

### Communication -> Communication
Communication modules compose other communication utilities for complete flows.
- `ai/chatbot.py` -> ai.prompt_manager, ai.cache_manager, ai.command_interpreter
- `ai/command_interpreter.py` -> ai.prompt_manager

### Third-Party Integration
External libraries provide channel and UI support.
- `ai/chatbot.py` -> psutil
- `ai/lm_studio_client.py` -> requests
- `ai/lm_studio_manager.py` -> requests
- `ai/__init__.py` -> chatbot, cache_manager
- `communication/__init__.py` -> communication_channels.base.base_channel, message_processing.command_parser


## Critical Dependencies for AI Context

### Entry Points
- `run_headless_service.py` -> standard library (argparse, sys, typing), error_handling, headless_service, logger (main application entry)

### Data Flow
- file_operations.py: core/file_operations.py <- standard library (importlib, json, os, pathlib), third-party (storage.user_data_v2_base), logger, config, error_handling, time_utilities, file_auditor (+1 more)

### Communication Flow
- __init__: communication/__init__.py <- third-party (command_handlers.analytics_handler, command_handlers.base_handler, command_handlers.checkin_handler), retry_manager, channel_orchestrator, factory, channel_monitor
- account_handler: communication/command_handlers/account_handler.py <- standard library (secrets, string, typing), third-party (storage.user_data_operations), logger, error_handling, core, base_handler, shared_types (+1 more)
- analytics_handler: communication/command_handlers/analytics_handler.py <- standard library (collections, typing), logger, error_handling, base_handler, shared_types, response_tracking (+5 more)


## Dependency Risk Areas

### High Coupling
- `ui/ui_app_qt.py` -> 45 local dependencies (heavy coupling)
- `communication/command_handlers/analytics_handler.py` -> 34 local dependencies (heavy coupling)
- `communication/message_processing/conversation_flow_manager.py` -> 34 local dependencies (heavy coupling)
- `communication/core/channel_orchestrator.py` -> 28 local dependencies (heavy coupling)
- `communication/command_handlers/interaction_handlers.py` -> 22 local dependencies (heavy coupling)

### Third-Party Risks
- `ui/ui_app_qt.py` -> PySide6.QtWidgets (31 modules use this)
- `ui/ui_app_qt.py` -> PySide6.QtCore (19 modules use this)
- `communication/command_handlers/base_handler.py` -> storage.user_data_validation (13 modules use this)
- `communication/communication_channels/base/command_registry.py` -> discord (11 modules use this)
- `communication/message_processing/conversation_flow_manager.py` -> storage.user_data_v2_base (8 modules use this)


## Quick Reference for AI

### Common Patterns
1. Core system modules expose utilities with minimal dependencies.
2. Communication and AI modules depend on core and peer communication modules.
3. UI modules rely on the UI framework and core services.
4. Data access modules rely on configuration plus logging.

### Dependency Guidelines
- Prefer core modules for shared logic instead of duplicating functionality.
- Avoid circular dependencies; break them with interfaces or utility modules.
- Use dependency injection for testability when modules call into services.
- Keep third-party usage wrapped by dedicated modules.

### Module Organisation
- `ai/` - Chatbot functionality (depends on core)
- `communication/` - Channels and message processing (depends on core)
- `core/` - System utilities (minimal dependencies)
- `scheduler/` - Module directory
- `tasks/` - Task management (depends on core)
- `ui/` - User interface (depends on core, limited communication dependencies)
- `user/` - User context (depends on core)

> **For complete dependency details, see [MODULE_DEPENDENCIES_DETAIL.md](../development_docs/MODULE_DEPENDENCIES_DETAIL.md)**