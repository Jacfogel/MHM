# AI Module Dependencies - Key Relationships & Patterns

> **File**: `ai_development_docs/AI_MODULE_DEPENDENCIES.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-07-08 00:04:55
> **Source**: `python development_tools/generate_module_dependencies.py` - Module Dependencies Generator

> **Audience**: AI collaborators
> **Purpose**: Essential module relationships and dependency patterns for AI context
> **Style**: Pattern-focused, relationship-driven, actionable

## Current Status

### Dependency Coverage: 100.0% - COMPLETED
- **Files Scanned**: 252
- **Total Imports**: 2147
- **Standard Library**: 633 (29.5%)
- **Third-Party**: 217 (10.1%)
- **Local Imports**: 1297 (60.4%)

## Dependency Decision Trees

### Need Core System Access?
Core System Dependencies:
- Configuration and Setup
  - core/config.py <- standard library (contextlib, logging, os, pathlib), third-party (dotenv), error_handling, token_crypto
  - core/logger.py <- standard library (contextlib, glob, gzip, json), error_handling, time_utilities, config
- Data Management
  - core/file_operations.py <- standard library (importlib, json, os, pathlib), logger, config, error_handling, time_utilities, file_auditor (+3 more)
- Error Handling
  - core/error_handling.py <- standard library (asyncio, collections.abc, contextlib, functools), network_probe, time_utilities

### Need AI or Chatbot Support?
AI System Dependencies:
- AI Core
  - ai/__init__.py <- chatbot, cache_manager, action_catalog, action_planner, command_interpreter (+11 more)
  - ai/chat/action_boundaries.py <- standard library (__future__, re), error_handling
- Command Processing
  - communication/command_handlers/account_handler.py <- standard library (secrets, string, typing), logger, error_handling, core, user_data_operations, base_handler (+2 more)
  - communication/command_handlers/analytics_formatting.py <- standard library (typing), checkin_data_manager, error_handling
  - communication/command_handlers/analytics_handler.py <- standard library (typing), error_handling, command_handlers, base_handler, shared_types
- Communication Integration
  - communication/communication_channels/interaction_view_factory.py <- standard library (__future__, importlib, typing), error_handling
  - communication/communication_channels/__init__.py <- none

### Need Communication Channel Coverage?
Communication Dependencies:
- Channel Infrastructure
  - communication/command_handlers/base_handler.py <- standard library (abc), shared_types, logger, error_handling, user_data_validation
  - communication/communication_channels/interaction_view_factory.py <- standard library (__future__, importlib, typing), error_handling
  - communication/core/factory.py <- standard library (importlib), base_channel, logger, error_handling, config
- Specific Channels
  - communication/communication_channels/discord/account_flow_handler.py <- standard library (contextlib), third-party (discord), logger, error_handling, shared_types, account_handler, user_data_presets
  - communication/communication_channels/discord/api_client.py <- standard library (asyncio, dataclasses, time, typing), third-party (discord), logger, error_handling
- Conversation Flow
  - communication/message_processing/conversation_flow_manager.py <- standard library (importlib), chatbot, checkin_data_manager, error_handling, logger, checkin_flow (+3 more)
  - communication/message_processing/flow_message_dispatcher.py <- standard library (dataclasses), error_handling, logger, shared_types, command_parser, conversation_flow_manager (+2 more)

### Need UI Dependencies?
UI Dependencies:
- Main Application
  - ui/ui_app_qt.py <- standard library (functools, importlib, os, pathlib), third-party (PySide6.QtCore, PySide6.QtWidgets)
- Dialogs
  - ui/dialog_actions.py <- standard library (collections.abc, importlib, typing), third-party (PySide6.QtWidgets)
  - ui/dialogs/account_creator_dialog.py <- standard library (contextlib, uuid, warnings), third-party (PySide6.QtCore, PySide6.QtWidgets), logger, user_data_validation, core, error_handling, dialog_helpers (+7 more)
  - ui/dialogs/admin_panel.py <- third-party (PySide6.QtCore, PySide6.QtWidgets), logger, error_handling
- Widgets
  - ui/widgets/category_selection_widget.py <- third-party (PySide6.QtWidgets), category_selection_widget_pyqt, user_data_validation, error_handling, message_data_manager, logger
  - ui/widgets/channel_selection_widget.py <- third-party (PySide6.QtWidgets), channel_selection_widget_pyqt, core, logger, error_handling
  - ui/widgets/checkin_settings_widget.py <- standard library (re), third-party (PySide6.QtCore, PySide6.QtWidgets), checkin_settings_widget_pyqt, ui_management, period_row_management, core, error_handling (+2 more)


## Key Dependency Patterns

### Core -> Communication and AI (most common)
Communication and AI modules depend on core system modules.
- `ai/chat/action_boundaries.py` -> core.error_handling
- `ai/chat/action_planner.py` -> core.config, core.error_handling, core.logger

### UI -> Core
UI modules rely on core configuration and data access.
- `ui/generate_ui_files.py` -> core.error_handling, core.time_utilities

### Communication -> Communication
Communication modules compose other communication utilities for complete flows.
- `ai/__init__.py` -> ai.chat.chatbot, ai.client.cache_manager, ai.prompts.action_catalog
- `ai/chat/action_planner.py` -> ai.context.service, ai.prompts.action_catalog, ai.prompts.command_interpreter

### Third-Party Integration
External libraries provide channel and UI support.
- `ai/chat/chatbot.py` -> psutil
- `ai/client/lm_studio_client.py` -> requests
- `ai/client/lm_studio_manager.py` -> requests
- `checkins/checkin_schemas.py` -> pydantic
- `checkins/__init__.py` -> checkin_analytics, checkin_data_manager


## Critical Dependencies for AI Context

### Entry Points
- `run_headless_service.py` -> standard library (argparse, sys, typing), error_handling, headless_service, logger (main application entry)

### Data Flow
- file_operations.py: core/file_operations.py <- standard library (importlib, json, os, pathlib), logger, config, error_handling, time_utilities, file_auditor (+3 more)
- user_data_operations.py: storage/user_data_operations.py <- standard library (collections.abc, importlib, json, os), logger, config, file_operations, user_data_read, user_management (+8 more)
- user_data_presets.py: storage/user_data_presets.py <- standard library (json, pathlib), third-party (pytz), logger, error_handling

### Communication Flow
- __init__: communication/__init__.py <- third-party (command_handlers.analytics_handler, command_handlers.base_handler, command_handlers.checkin_handler), retry_manager, channel_orchestrator, factory, channel_monitor
- account_handler: communication/command_handlers/account_handler.py <- standard library (secrets, string, typing), logger, error_handling, core, user_data_operations, base_handler (+2 more)
- analytics_formatting: communication/command_handlers/analytics_formatting.py <- standard library (typing), checkin_data_manager, error_handling


## Dependency Risk Areas

### High Coupling
- `communication/core/channel_orchestrator.py` -> 21 unique local dependencies (heavy coupling) (31 import statements; 10 duplicate)
- `communication/message_processing/interaction_manager.py` -> 17 unique local dependencies (heavy coupling) (18 import statements; 1 duplicate)
- `ai/__init__.py` -> 16 unique local dependencies (heavy coupling)
- `ai/chat/chatbot.py` -> 16 unique local dependencies (heavy coupling) (17 import statements; 1 duplicate)
- `ai/context/service.py` -> 14 unique local dependencies (heavy coupling) (15 import statements; 1 duplicate)

### Third-Party Risks
- `ui/admin_actions.py` -> PySide6.QtWidgets (38 modules use this)
- `ui/ui_app_qt.py` -> PySide6.QtCore (21 modules use this)
- `communication/communication_channels/base/command_registry.py` -> discord (18 modules use this)
- `ai/chat/chatbot.py` -> psutil (8 modules use this)
- `checkins/checkin_schemas.py` -> pydantic (7 modules use this)


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
- `checkins/` - Module directory
- `communication/` - Channels and message processing (depends on core)
- `core/` - System utilities (minimal dependencies)
- `integrations/` - Module directory
- `messages/` - Module directory
- `scheduler/` - Module directory
- `storage/` - Module directory
- `tasks/` - Task management (depends on core)
- `ui/` - User interface (depends on core, limited communication dependencies)
- `user/` - User context (depends on core)

> **For complete dependency details, see [MODULE_DEPENDENCIES_DETAIL.md](../development_docs/MODULE_DEPENDENCIES_DETAIL.md)**