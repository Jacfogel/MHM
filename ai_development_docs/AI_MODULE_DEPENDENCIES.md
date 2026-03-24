# AI Module Dependencies - Key Relationships & Patterns

> **File**: `ai_development_docs/AI_MODULE_DEPENDENCIES.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-03-24 00:47:12
> **Source**: `python development_tools/generate_module_dependencies.py` - Module Dependencies Generator

> **Audience**: AI collaborators
> **Purpose**: Essential module relationships and dependency patterns for AI context
> **Style**: Pattern-focused, relationship-driven, actionable

## Current Status

### Dependency Coverage: 100.0% - COMPLETED
- **Files Scanned**: 122
- **Total Imports**: 1569
- **Standard Library**: 437 (27.9%)
- **Third-Party**: 465 (29.6%)
- **Local Imports**: 667 (42.5%)

## Dependency Decision Trees

### Need Core System Access?
Core System Dependencies:
- Configuration and Setup
  - core/config.py <- standard library (contextlib, os, pathlib, typing), third-party (dotenv), error_handling, logger
  - core/logger.py <- standard library (contextlib, glob, gzip, json), error_handling, config
- Data Management
  - core/file_operations.py <- standard library (json, os, pathlib, re), logger, config, error_handling, time_utilities, file_auditor (+2 more)
  - core/user_data_manager.py <- standard library (collections.abc, json, os, pathlib), logger, config, file_operations, core, schemas (+7 more)
  - core/user_data_presets.py <- standard library (json, pathlib), third-party (pytz), logger, error_handling
- Error Handling
  - core/error_handling.py <- standard library (asyncio, collections.abc, datetime, functools), time_utilities, service_utilities, logger

### Need AI or Chatbot Support?
AI System Dependencies:
- AI Core
  - ai/cache_manager.py <- standard library (dataclasses, hashlib, threading, time), logger, error_handling, config
  - ai/chatbot.py <- standard library (asyncio, collections, datetime, json), third-party (ai.cache_manager, ai.lm_studio_manager, ai.prompt_manager), logger, config, response_tracking, core, error_handling (+2 more)
- Command Processing
  - communication/command_handlers/account_handler.py <- standard library (secrets, string, typing), third-party (communication.command_handlers.account_handler, communication.command_handlers.base_handler, communication.command_handlers.shared_types), logger, error_handling, core, user_data_manager
  - communication/command_handlers/analytics_handler.py <- standard library (collections, typing), third-party (communication.command_handlers.base_handler, communication.command_handlers.shared_types, tasks), logger, error_handling, checkin_analytics, core, checkin_dynamic_manager (+2 more)
  - communication/command_handlers/base_handler.py <- standard library (abc), third-party (communication.command_handlers.shared_types), logger, error_handling
- Communication Integration
  - communication/communication_channels/__init__.py <- none
  - communication/core/channel_monitor.py <- standard library (threading, time, typing), third-party (communication.communication_channels.base.base_channel), time_utilities, logger, error_handling

### Need Communication Channel Coverage?
Communication Dependencies:
- Channel Infrastructure
  - communication/command_handlers/base_handler.py <- standard library (abc), third-party (communication.command_handlers.shared_types), logger, error_handling
  - communication/core/factory.py <- standard library (importlib), third-party (communication.communication_channels.base.base_channel), logger, error_handling, config
  - communication/communication_channels/base/base_channel.py <- standard library (abc, dataclasses, enum, typing), logger, error_handling
- Specific Channels
  - communication/communication_channels/discord/account_flow_handler.py <- standard library (contextlib), third-party (communication.command_handlers.account_handler, communication.command_handlers.shared_types, discord), logger, error_handling, user_data_presets
  - communication/communication_channels/discord/api_client.py <- standard library (asyncio, dataclasses, time, typing), third-party (discord), logger, error_handling
- Conversation Flow
  - communication/message_processing/conversation_flow_manager.py <- standard library (contextlib, datetime, json, pathlib), third-party (ai.chatbot, communication.command_handlers.analytics_handler, communication.command_handlers.interaction_handlers), logger, core, response_tracking, error_handling, time_utilities (+3 more)
  - communication/communication_channels/discord/account_flow_handler.py <- standard library (contextlib), third-party (communication.command_handlers.account_handler, communication.command_handlers.shared_types, discord), logger, error_handling, user_data_presets

### Need UI Dependencies?
UI Dependencies:
- Main Application
  - ui/ui_app_qt.py <- standard library (contextlib, json, os, pathlib), third-party (PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets), time_utilities, logger, config, error_handling, service_utilities (+5 more)
- Dialogs
  - ui/dialogs/account_creator_dialog.py <- standard library (contextlib, pathlib, time, typing), third-party (PySide6.QtCore, PySide6.QtWidgets, tasks), logger, user_data_validation, core, error_handling, file_operations (+3 more)
  - ui/dialogs/admin_panel.py <- third-party (PySide6.QtCore, PySide6.QtWidgets), logger, error_handling
  - ui/dialogs/category_management_dialog.py <- third-party (PySide6.QtCore, PySide6.QtWidgets, ui.generated.category_management_dialog_pyqt), logger, core, error_handling, schedule_management
- Widgets
  - ui/widgets/category_selection_widget.py <- third-party (PySide6.QtWidgets, ui.generated.category_selection_widget_pyqt), user_data_validation, error_handling, logger
  - ui/widgets/channel_selection_widget.py <- third-party (PySide6.QtWidgets, ui.generated.channel_selection_widget_pyqt), core, logger, error_handling
  - ui/widgets/checkin_settings_widget.py <- standard library (re), third-party (PySide6.QtCore, PySide6.QtWidgets, ui.generated.checkin_settings_widget_pyqt), ui_management, core, error_handling, logger, checkin_dynamic_manager


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

### Third-Party Integration
External libraries provide channel and UI support.
- `ai/chatbot.py` -> requests, user.context_manager
- `ai/context_builder.py` -> user.context_manager
- `ai/lm_studio_manager.py` -> requests
- `ai/__init__.py` -> chatbot, cache_manager
- `communication/__init__.py` -> communication_channels.base.base_channel, message_processing.command_parser


## Critical Dependencies for AI Context

### Entry Points
- `run_headless_service.py` -> standard library (sys), headless_service, logger, error_handling (main application entry)
- `run_mhm.py` -> standard library (os, pathlib, subprocess, sys), error_handling (main application entry)
- `run_tests.py` -> standard library (argparse, contextlib, ctypes, json), third-party (psutil, pytest), error_handling, time_utilities, conftest_hooks (main application entry)

### Data Flow
- file_operations.py: core/file_operations.py <- standard library (json, os, pathlib, re), logger, config, error_handling, time_utilities, file_auditor (+2 more)
- user_data_manager.py: core/user_data_manager.py <- standard library (collections.abc, json, os, pathlib), logger, config, file_operations, core, schemas (+7 more)
- user_data_presets.py: core/user_data_presets.py <- standard library (json, pathlib), third-party (pytz), logger, error_handling

### Communication Flow
- __init__: communication/__init__.py <- third-party (command_handlers.analytics_handler, command_handlers.base_handler, command_handlers.checkin_handler), retry_manager, channel_orchestrator, factory, channel_monitor
- account_handler: communication/command_handlers/account_handler.py <- standard library (secrets, string, typing), third-party (communication.command_handlers.account_handler, communication.command_handlers.base_handler, communication.command_handlers.shared_types), logger, error_handling, core, user_data_manager
- analytics_handler: communication/command_handlers/analytics_handler.py <- standard library (collections, typing), third-party (communication.command_handlers.base_handler, communication.command_handlers.shared_types, tasks), logger, error_handling, checkin_analytics, core, checkin_dynamic_manager (+2 more)


## Dependency Risk Areas

### High Coupling
- `communication/command_handlers/analytics_handler.py` -> 29 local dependencies (heavy coupling)
- `ui/ui_app_qt.py` -> 27 local dependencies (heavy coupling)
- `core/error_handling.py` -> 23 local dependencies (heavy coupling)
- `core/service.py` -> 23 local dependencies (heavy coupling)
- `communication/core/channel_orchestrator.py` -> 19 local dependencies (heavy coupling)

### Third-Party Risks
- `ai/chatbot.py` -> tasks (34 modules use this)
- `ui/ui_app_qt.py` -> PySide6.QtWidgets (31 modules use this)
- `ui/ui_app_qt.py` -> PySide6.QtCore (19 modules use this)
- `communication/core/channel_orchestrator.py` -> communication.message_processing.interaction_manager (17 modules use this)
- `communication/command_handlers/account_handler.py` -> communication.command_handlers.shared_types (16 modules use this)

### Circular Dependencies to Monitor
- `core/config.py` <-> `core/logger.py`
- `core/error_handling.py` <-> `core/time_utilities.py`
- `core/error_handling.py` <-> `core/service_utilities.py`
- `core/error_handling.py` <-> `core/logger.py`
- `core/file_operations.py` <-> `core/message_management.py`


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