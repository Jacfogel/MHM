# AI Function Registry - Key Patterns & Decision Trees

> **File**: `ai_development_docs/AI_FUNCTION_REGISTRY.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-01-14 04:48:07
> **Source**: `python development_tools/generate_function_registry.py` - Function Registry Generator
> **Audience**: AI Collaborators  
> **Purpose**: Essential function patterns and decision trees for AI context  
> **Style**: Pattern-focused, decision-tree driven, actionable

## [*] **Current Status**

### **Documentation Coverage: 96.0% [OK] EXCELLENT**
- **Total Functions**: 1532
- **Total Methods**: 1135
- **Documented**: 2561/2667
- **Files Scanned**: 110

## [DECISION TREES] **Decision Trees for AI Context**

### **[USER DATA] Need to Handle User Data?**
```
User Data Operations Decision Tree:
+-- Core Data Access
|   +-- `core/user_data_handlers.py` - Primary data access (26 functions)
|   +-- `core/user_data_manager.py` - Data management (64 functions)
|   `-- `core/user_data_validation.py` - Validation (8/11 functions)
+-- User Context
|   +-- `user/user_context.py` - User context management (20 functions)
|   `-- `user/user_preferences.py` - User preferences (20 functions)
`-- User Management
    `-- `core/user_management.py` - Account operations (44/45 functions)
```

### **[AI] Need AI/Chatbot Functionality?**
```
AI Operations Decision Tree:
+-- AI Chatbot
|   +-- `ai/chatbot.py` - Main AI implementation (55 functions)
|   `-- `user/context_manager.py` - Context for AI (24 functions)
+-- Command Parsing
|   +-- `communication/message_processing/command_parser.py` - Natural language parsing (30 functions)
|   `-- `communication/command_handlers/interaction_handlers.py` - Command handlers (20 functions)
`-- Interaction Management
    `-- `communication/message_processing/interaction_manager.py` - Main interaction flow (39/42 functions)
```

### **[COMM] Need Communication/Channels?**
```
Communication Decision Tree:
+-- Channel Management
|   +-- `communication/core/channel_orchestrator.py` - Main communication (81/83 functions)
|   +-- `communication/communication_channels/base/base_channel.py` - Channel base class (14 functions)
|   `-- `communication/core/factory.py` - Channel creation (6 functions)
+-- Specific Channels
|   +-- `communication/communication_channels/discord/bot.py` - Discord integration (40 functions)
|   `-- `communication/communication_channels/email/bot.py` - Email integration (14/16 functions)
`-- Conversation Flow
    `-- `communication/message_processing/conversation_flow_manager.py` - Conversation management (68/72 functions)
```

### **[UI] Need UI/User Interface?**
```
UI Operations Decision Tree:
+-- Main Application
|   `-- `ui/ui_app_qt.py` - Main admin interface (118/120 functions)
+-- Dialogs
|   +-- `ui/dialogs/account_creator_dialog.py` - Account creation (97/98 functions)
|   +-- `ui/dialogs/user_profile_dialog.py` - User profiles (38 functions)
|   +-- `ui/dialogs/task_management_dialog.py` - Task management (4/8 functions)
|   `-- `ui/dialogs/schedule_editor_dialog.py` - Schedule editing (38 functions)
`-- Widgets
    +-- `ui/widgets/tag_widget.py` - Tag management (30 functions)
    +-- `ui/widgets/task_settings_widget.py` - Task settings (34/36 functions)
    `-- `ui/widgets/user_profile_settings_widget.py` - Profile settings (28 functions)
```

### **[CORE] Need Core System Operations?**
```
Core System Decision Tree:
+-- Configuration
|   `-- `core/config.py` - System configuration (22 functions)
+-- Error Handling
|   `-- `core/error_handling.py` - Error management (60/62 functions)
+-- File Operations
|   +-- `core/file_operations.py` - File I/O (16 functions)
|   `-- `core/backup_manager.py` - Backup operations (53 functions)
+-- Logging
|   `-- `core/logger.py` - Logging system (65 functions)
`-- Scheduling
    +-- `core/scheduler.py` - Task scheduling (81/82 functions)
    `-- `core/schedule_management.py` - Schedule management (15/17 functions)
```

## [PATTERNS] **Key Function Patterns**

### **Handler Pattern** (9 found)
**Purpose**: Handle specific user intents or operations
**Location**: `communication/command_handlers/account_handler.py`, `communication/command_handlers/analytics_handler.py`, `communication/command_handlers/base_handler.py`
**Pattern**: 
- `can_handle(intent)` - Check if handler supports intent
- `handle(user_id, parsed_command)` - Process the command
- `get_help()` - Return help text

**Examples**:
- `AccountManagementHandler` (communication/command_handlers/account_handler.py)
- `AnalyticsHandler` (communication/command_handlers/analytics_handler.py)
- `InteractionHandler` (communication/command_handlers/base_handler.py)
- ... and 6 more

### **Widget Pattern** (7 found)
**Purpose**: Reusable UI components
**Location**: `ui/widgets/checkin_settings_widget.py`, `ui/widgets/period_row_widget.py`, `ui/widgets/tag_widget.py`
**Pattern**: 
- Inherit from QWidget
- Implement `get_*()` and `set_*()` methods
- Signal-based updates

**Examples**:
- `CheckinSettingsWidget` (ui/widgets/checkin_settings_widget.py)
- `PeriodRowWidget` (ui/widgets/period_row_widget.py)
- `TagWidget` (ui/widgets/tag_widget.py)
- ... and 4 more

### **Dialog Pattern** (15 found)
**Purpose**: Modal user interaction windows
**Location**: `ui/dialogs/account_creator_dialog.py`, `ui/dialogs/admin_panel.py`, `ui/dialogs/checkin_management_dialog.py`
**Pattern**: 
- Inherit from QDialog
- Use widgets for data entry
- Return result on accept/reject

**Examples**:
- `AccountCreatorDialog` (ui/dialogs/account_creator_dialog.py)
- `AdminPanelDialog` (ui/dialogs/admin_panel.py)
- `CheckinManagementDialog` (ui/dialogs/checkin_management_dialog.py)
- ... and 12 more

### **Context Manager Pattern** (1 found)
**Purpose**: Safe resource management
**Location**: `core/error_handling.py`
**Pattern**: 
- `__enter__()` and `__exit__()` methods
- Automatic cleanup
- Used with `with` statements

**Examples**:
- `SafeFileContext` (core/error_handling.py)

### **Decorator Pattern** (2 found)
**Purpose**: Function/method decoration (error handling, logging)
**Location**: `core/error_handling.py`
**Pattern**: 
- `@handle_errors` - Error handling decorator
- `@<name>` - Custom decorators
- Applied to functions/methods

**Examples**:
- `handle_errors` (core/error_handling.py)
- ... and 1 more



## [ENTRY POINTS] **Critical Functions for AI Context**

### **Entry Points** (Start Here)
- [OK] `communication/message_processing/interaction_manager.py::handle_message()` - Main message entry point
- [OK] `ai/chatbot.py::generate_response()` - AI response generation
- [OK] `core/headless_service.py::main()` - Application entry point
- [OK] `core/service.py::main()` - Application entry point
- [OK] `ui/generate_ui_files.py::main()` - Application entry point
- [OK] `ui/ui_app_qt.py::main()` - Application entry point
- [OK] `run_headless_service.py::main()` - Application entry point
- [OK] `run_mhm.py::main()` - Application entry point
- [OK] `run_tests.py::main()` - Application entry point
- [OK] `core/config.py::__init__()` - Initialization

### **Data Access Patterns**
- **User Data**: `core/user_data_handlers.py` - User data operations (26 functions)
- **Validation**: `core/user_data_validation.py` - Data validation (8/11 functions)
- **File Operations**: `core/file_operations.py` - File I/O (16 functions)

### **Communication Patterns**
- **Message Sending**: `communication/core/channel_orchestrator.py::_send_ai_generated_message()`
- **Command Parsing**: `communication/message_processing/command_parser.py::parse_command()`

## [!] **Areas Needing Attention**

### **High Priority** (Missing Documentation)
- `ui/widgets/dynamic_list_container.py` - 18/22 functions undocumented (18% coverage)
- `core/schemas.py` - 18/32 functions undocumented (44% coverage)
- `ui/widgets/dynamic_list_field.py` - 12/20 functions undocumented (40% coverage)
- `ui/dialogs/channel_management_dialog.py` - 7/11 functions undocumented (36% coverage)
- `ui/widgets/channel_selection_widget.py` - 6/16 functions undocumented (62% coverage)
- `ui/widgets/category_selection_widget.py` - 4/6 functions undocumented (33% coverage)

### **Medium Priority** (Partial Coverage)
- `ui/dialogs/task_management_dialog.py` - 4/8 functions undocumented (50% coverage)
- `ui/dialogs/category_management_dialog.py` - 4/12 functions undocumented (67% coverage)
- `core/user_data_validation.py` - 3/11 functions undocumented (73% coverage)



## [QUICK REF] **Quick Reference for AI**

### **Common Operations**
1. **User Message**: `communication/message_processing/interaction_manager.py::handle_message()`
2. **AI Response**: `ai/chatbot.py::generate_response()`
3. **Main Entry**: `run_headless_service.py::main()`
4. **User Data Access**: `core/config.py::get_user_data_dir()`
5. **Send Message**: `core/headless_service.py::send_test_message()`
6. **Command Parsing**: `communication/message_processing/command_parser.py::get_enhanced_command_parser()`
7. **Error Handling**: `core/error_handling.py::handle_errors()`
8. **Scheduling**: `core/scheduler.py::run_full_scheduler_standalone()`
9. **Configuration**: `core/config.py::get_user_data_dir()`


### **Complexity Metrics**
Most complex functions (may need refactoring):
1. [OK] `communication/communication_channels/discord/bot.py::initialize__register_events()` - Complexity: 2625
2. [OK] `communication/message_processing/interaction_manager.py::handle_message()` - Complexity: 2554
3. [OK] `communication/message_processing/command_parser.py::_extract_entities_rule_based()` - Complexity: 2298
4. [OK] `ai/chatbot.py::_create_comprehensive_context_prompt()` - Complexity: 2208
5. [OK] `run_tests.py::run_command()` - Complexity: 2200


### **Pattern Recognition**
- **Handler classes** end with "Handler" and implement standard interface
- **Manager classes** are singletons with lifecycle management
- **Factory classes** have "Factory" in name and create related objects
- **Context managers** can be used with `with` statements

### **File Organization**
- `core/` - System utilities and data management (27 files, 816 functions)
- `communication/` - Communication channels and message processing (38 files, 760 functions)
- `ai/` - AI chatbot functionality (7 files, 189 functions)
- `ui/` - User interface components (28 files, 793 functions)
- `user/` - User context and preferences (4 files, 64 functions)
- `tasks/` - Task management system (2 files, 21 functions)

> **For complete function details, see [FUNCTION_REGISTRY_DETAIL.md](development_docs/FUNCTION_REGISTRY_DETAIL.md)**  
> **Last Updated**: 2026-01-14 04:48:07
