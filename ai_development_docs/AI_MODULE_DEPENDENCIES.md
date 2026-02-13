# AI Module Dependencies - Key Relationships & Patterns

> **File**: `ai_development_docs/AI_MODULE_DEPENDENCIES.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-02-12 23:52:44
> **Source**: `python development_tools/generate_module_dependencies.py` - Module Dependencies Generator

> **Audience**: AI collaborators
> **Purpose**: Essential module relationships and dependency patterns for AI context
> **Style**: Pattern-focused, relationship-driven, actionable

## Current Status

### Dependency Coverage: 100.0% - COMPLETED
- **Files Scanned**: 108
- **Total Imports**: 1454
- **Standard Library**: 382 (26.3%)
- **Third-Party**: 223 (15.3%)
- **Local Imports**: 849 (58.4%)

## Dependency Decision Trees

### Need Core System Access?
Core System Dependencies:
- Configuration and Setup
  - core/config.py <- standard library (os, pathlib), third-party (dotenv), error_handling, logger
  - core/logger.py <- standard library (glob, gzip, json, logging), error_handling, config
- Data Management
  - core/file_operations.py <- standard library (json, os, pathlib, re), logger, config, error_handling, time_utilities, file_auditor (+2 more)
  - core/user_data_handlers.py <- standard library (copy, json, os, pathlib), third-party (pytz), logger, error_handling, config, file_operations, time_utilities (+6 more)
  - core/user_data_manager.py <- standard library (json, os, pathlib, shutil), logger, config, file_operations, user_data_handlers, schemas (+5 more)
- Error Handling
  - core/error_handling.py <- standard library (asyncio, datetime, functools, json), time_utilities, service_utilities, logger

### Need AI or Chatbot Support?
AI System Dependencies:
- AI Core
  - ai/cache_manager.py <- standard library (dataclasses, hashlib, threading, time), logger, error_handling, config
  - ai/chatbot.py <- standard library (asyncio, collections, datetime, json), third-party (psutil, requests), logger, config, response_tracking, user_data_handlers, context_manager (+7 more)
- Command Processing
  - communication/command_handlers/account_handler.py <- standard library (secrets, string, typing), logger, error_handling, user_data_handlers, user_data_manager, base_handler (+3 more)
  - communication/command_handlers/analytics_handler.py <- standard library (collections, typing), logger, error_handling, base_handler, shared_types, checkin_analytics (+5 more)
  - communication/command_handlers/base_handler.py <- standard library (abc), shared_types, logger, error_handling
- Communication Integration
  - communication/communication_channels/__init__.py <- none
  - communication/core/channel_monitor.py <- standard library (threading, time, typing), time_utilities, logger, error_handling, base_channel

### Need Communication Channel Coverage?
Communication Dependencies:
- Channel Infrastructure
  - communication/command_handlers/base_handler.py <- standard library (abc), shared_types, logger, error_handling
  - communication/core/factory.py <- standard library (importlib), base_channel, logger, error_handling, config
  - communication/communication_channels/base/base_channel.py <- standard library (abc, dataclasses, enum, typing), logger, error_handling
- Specific Channels
  - communication/communication_channels/discord/account_flow_handler.py <- standard library (typing), third-party (discord), logger, error_handling, shared_types, account_handler, user_data_handlers
  - communication/communication_channels/discord/api_client.py <- standard library (asyncio, dataclasses, time, typing), third-party (discord), logger, error_handling
- Conversation Flow
  - communication/message_processing/conversation_flow_manager.py <- standard library (datetime, json, pathlib, random), chatbot, logger, user_data_handlers, response_tracking, error_handling (+13 more)
  - communication/communication_channels/discord/account_flow_handler.py <- standard library (typing), third-party (discord), logger, error_handling, shared_types, account_handler, user_data_handlers

### Need UI Dependencies?
UI Dependencies:
- Main Application
  - ui/ui_app_qt.py <- standard library (datetime, json, os, pathlib), third-party (PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets), time_utilities, logger, config, error_handling, service_utilities (+20 more)
- Dialogs
  - ui/dialogs/account_creator_dialog.py <- standard library (pathlib, time, typing, uuid), third-party (PySide6.QtCore, PySide6.QtWidgets), logger, user_data_validation, user_data_handlers, error_handling, category_selection_widget (+10 more)
  - ui/dialogs/admin_panel.py <- third-party (PySide6.QtCore, PySide6.QtWidgets), logger, error_handling
  - ui/dialogs/category_management_dialog.py <- third-party (PySide6.QtCore, PySide6.QtWidgets), category_management_dialog_pyqt, category_selection_widget, logger, user_data_handlers, error_handling (+1 more)
- Widgets
  - ui/widgets/category_selection_widget.py <- third-party (PySide6.QtWidgets), category_selection_widget_pyqt, user_data_validation, error_handling, logger
  - ui/widgets/channel_selection_widget.py <- third-party (PySide6.QtWidgets), channel_selection_widget_pyqt, user_data_handlers, logger, error_handling
  - ui/widgets/checkin_settings_widget.py <- standard library (re), third-party (PySide6.QtCore, PySide6.QtWidgets), checkin_settings_widget_pyqt, ui_management, user_data_handlers, error_handling, logger (+1 more)


## Key Dependency Patterns

### Core -> Communication and AI (most common)
Communication and AI modules depend on core system modules.
- `ai/cache_manager.py` -> core.logger, core.error_handling, core.config
- `ai/chatbot.py` -> core.logger, core.config, core.response_tracking
- `ai/context_builder.py` -> core.logger, core.error_handling, core.time_utilities

### UI -> Core
UI modules rely on core configuration and data access.
- `ui/generate_ui_files.py` -> core.error_handling, core.time_utilities
- `ui/ui_app_qt.py` -> core.time_utilities, core.logger, core.config

### Communication -> Communication
Communication modules compose other communication utilities for complete flows.
- `ai/chatbot.py` -> ai.prompt_manager, ai.cache_manager, ai.lm_studio_manager

### Third-Party Integration
External libraries provide channel and UI support.
- `ai/chatbot.py` -> requests, psutil
- `ai/lm_studio_manager.py` -> requests
- `ai/__init__.py` -> chatbot, cache_manager
- `communication/__init__.py` -> communication_channels.base.base_channel, message_processing.command_parser
- `communication/command_handlers/task_handler.py` -> base_handler


## Critical Dependencies for AI Context

### Entry Points
- `run_headless_service.py` -> standard library (sys), headless_service, logger, error_handling (main application entry)

### Data Flow
- file_operations.py: core/file_operations.py <- standard library (json, os, pathlib, re), logger, config, error_handling, time_utilities, file_auditor (+2 more)
- user_data_handlers.py: core/user_data_handlers.py <- standard library (copy, json, os, pathlib), third-party (pytz), logger, error_handling, config, file_operations, time_utilities (+6 more)
- user_data_manager.py: core/user_data_manager.py <- standard library (json, os, pathlib, shutil), logger, config, file_operations, user_data_handlers, schemas (+5 more)

### Communication Flow
- __init__: communication/__init__.py <- third-party (command_handlers.analytics_handler, command_handlers.base_handler, command_handlers.checkin_handler), retry_manager, channel_orchestrator, factory, channel_monitor
- account_handler: communication/command_handlers/account_handler.py <- standard library (secrets, string, typing), logger, error_handling, user_data_handlers, user_data_manager, base_handler (+3 more)
- analytics_handler: communication/command_handlers/analytics_handler.py <- standard library (collections, typing), logger, error_handling, base_handler, shared_types, checkin_analytics (+5 more)


## Dependency Risk Areas

### High Coupling
- `ui/ui_app_qt.py` -> 44 local dependencies (heavy coupling)
- `core/user_data_handlers.py` -> 43 local dependencies (heavy coupling)
- `communication/message_processing/conversation_flow_manager.py` -> 37 local dependencies (heavy coupling)
- `communication/command_handlers/analytics_handler.py` -> 34 local dependencies (heavy coupling)
- `communication/core/channel_orchestrator.py` -> 32 local dependencies (heavy coupling)

### Third-Party Risks
- `ui/ui_app_qt.py` -> PySide6.QtWidgets (30 modules use this)
- `ui/ui_app_qt.py` -> PySide6.QtCore (21 modules use this)
- `communication/communication_channels/base/command_registry.py` -> discord (11 modules use this)
- `ai/chatbot.py` -> psutil (7 modules use this)
- `core/scheduler.py` -> pytz (5 modules use this)

### Circular Dependencies to Monitor
- `communication/command_handlers/account_handler.py` <-> `communication/command_handlers/account_handler.py`
- `communication/command_handlers/task_handler.py` <-> `communication/message_processing/conversation_flow_manager.py`
- `communication/message_processing/conversation_flow_manager.py` <-> `communication/message_processing/interaction_manager.py`
- `core/config.py` <-> `core/logger.py`
- `core/error_handling.py` <-> `core/time_utilities.py`


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
- `tasks/` - Task management (depends on core)
- `ui/` - User interface (depends on core, limited communication dependencies)
- `user/` - User context (depends on core)

> **For complete dependency details, see [MODULE_DEPENDENCIES_DETAIL.md](development_docs/MODULE_DEPENDENCIES_DETAIL.md)**