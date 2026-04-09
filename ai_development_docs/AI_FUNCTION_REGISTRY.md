# AI Function Registry - Key Patterns & Decision Trees

> **File**: `ai_development_docs/AI_FUNCTION_REGISTRY.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-04-09 01:08:57
> **Source**: `python development_tools/generate_function_registry.py` - Function Registry Generator
> **Audience**: AI Collaborators  
> **Purpose**: Essential function patterns and decision trees for AI context  
> **Style**: Pattern-focused, decision-tree driven, actionable

## [*] **Current Status**

### **Documentation Coverage: 95.2% [OK] EXCELLENT**
- **Total Functions**: 1700
- **Total Methods**: 1229
- **Documented**: 2788/2929
- **Files Scanned**: 124

## [DECISION TREES] **Decision Trees for AI Context**

### **[USER DATA] Need to Handle User Data?**
```
User Data Operations Decision Tree:
+-- `core/user_data_read.py` - Primary data access (5 functions)
+-- `core/user_data_manager.py` - Data management (67 functions)
+-- `core/user_data_validation.py` - Validation (9/12 functions)
+-- `user/user_context.py` - User context management (20 functions)
+-- `user/user_preferences.py` - User preferences (20 functions)
`-- `core/user_data_read.py` - Account operations (5 functions)```

### **[AI] Need AI/Chatbot Functionality?**
```
AI Operations Decision Tree:
+-- `ai/chatbot.py` - Main AI implementation (85 functions)
+-- `user/context_manager.py` - Context for AI (24 functions)
+-- `communication/message_processing/command_parser.py` - Natural language parsing (43 functions)
+-- `communication/command_handlers/interaction_handlers.py` - Command handlers (20 functions)
`-- `communication/message_processing/interaction_manager.py` - Main interaction flow (48/50 functions)```

### **[COMM] Need Communication/Channels?**
```
Communication Decision Tree:
+-- `communication/core/channel_orchestrator.py` - Main communication (91/93 functions)
+-- `communication/communication_channels/base/base_channel.py` - Channel base class (14 functions)
`-- `communication/core/factory.py` - Channel creation (8 functions)```

### **[UI] Need UI/User Interface?**
```
UI Operations Decision Tree:
+-- `ui/ui_app_qt.py` - Main admin interface (134/136 functions)
+-- `ui/dialogs/task_crud_dialog.py` - Task CRUD (28 functions)
`-- `ui/widgets/task_settings_widget.py` - Task settings (34/37 functions)```

### **[CORE] Need Core System Operations?**
```
Core System Decision Tree:
+-- `core/service.py` - Main service (96 functions)
+-- `core/config.py` - Configuration (19 functions)
`-- `core/scheduler.py` - Scheduling (82/83 functions)```

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

### **Decorator Pattern** (3 found)
**Purpose**: Function/method decoration (error handling, logging)
**Location**: `core/error_handling.py`, `core/file_auditor.py`
**Pattern**: 
- `@handle_errors` - Error handling decorator
- `@<name>` - Custom decorators
- Applied to functions/methods

**Examples**:
- `handle_errors` (core/error_handling.py)
- ... and 2 more



## [ENTRY POINTS] **Critical Functions for AI Context**

### **Entry Points** (Start Here)
- [OK] `communication/message_processing/interaction_manager.py::handle_message()` - Main message entry point
- [OK] `ai/chatbot.py::generate_response()` - AI response generation
- [OK] `core/headless_service.py::main()` - Application entry point
- [OK] `core/service.py::main()` - Application entry point
- [OK] `ui/generate_ui_files.py::main()` - Application entry point
- [OK] `ui/ui_app_qt.py::main()` - Application entry point
- [OK] `run_headless_service.py::main()` - Application entry point
- [OK] `core/config.py::__init__()` - Initialization
- [OK] `core/service.py::__init__()` - Initialization

### **Data Access Patterns**
- **User Data**: `core/user_data_read.py` - User data operations (5 functions)
- **Validation**: `core/user_data_validation.py` - Data validation (9/12 functions)
- **File Operations**: `core/file_operations.py` - File I/O (16 functions)

### **Communication Patterns**
- **Message Sending**: `communication/core/channel_orchestrator.py::_send_ai_generated_message()`
- **Command Parsing**: `communication/message_processing/command_parser.py::parse_command()`

## [!] **Areas Needing Attention**

### **High Priority** (Missing Documentation)
- `ui/widgets/dynamic_list_container.py` - 18/22 functions undocumented (18% coverage)
- `core/schemas.py` - 18/32 functions undocumented (44% coverage)
- `ui/widgets/dynamic_list_field.py` - 12/20 functions undocumented (40% coverage)
- `core/user_data_registry.py` - 11/22 functions undocumented (50% coverage)
- `core/user_data_write.py` - 10/12 functions undocumented (17% coverage)
- `ui/dialogs/channel_management_dialog.py` - 7/11 functions undocumented (36% coverage)
- `ui/widgets/channel_selection_widget.py` - 6/16 functions undocumented (62% coverage)
- `core/user_lookup.py` - 5/6 functions undocumented (17% coverage)
- `core/user_data_updates.py` - 5/7 functions undocumented (29% coverage)
- `ui/widgets/category_selection_widget.py` - 4/6 functions undocumented (33% coverage)

### **Medium Priority** (Partial Coverage)
- `ui/dialogs/task_management_dialog.py` - 4/8 functions undocumented (50% coverage)
- `ui/dialogs/category_management_dialog.py` - 4/12 functions undocumented (67% coverage)
- `core/user_data_validation.py` - 3/12 functions undocumented (75% coverage)



## [QUICK REF] **Quick Reference for AI**

### **Common Operations**
1. **User Message**: `communication/message_processing/interaction_manager.py::handle_message()`
2. **AI Response**: `ai/chatbot.py::generate_response()`
3. **Main Entry**: `run_headless_service.py::main()`
4. **User Data Save**: `communication/message_processing/conversation_flow_manager.py::_save_user_states()`
5. **Command Parsing**: `communication/message_processing/command_parser.py::get_enhanced_command_parser()`
6. **Error Handling**: `core/error_handling.py::handle_errors()`
7. **Scheduling**: `core/scheduler.py::run_full_scheduler_standalone()`
8. **Configuration**: `communication/core/channel_orchestrator.py::get_configured_channels()`


### **Complexity Metrics**
Most complex functions (may need refactoring):
1. [OK] `run_tests.py::run_command()` - Complexity: 3211
2. [OK] `run_tests.py::print_combined_summary()` - Complexity: 2960
3. [OK] `communication/message_processing/interaction_manager.py::handle_message()` - Complexity: 2783
4. [OK] `run_tests.py::main()` - Complexity: 2691
5. [OK] `communication/communication_channels/discord/bot.py::initialize__register_events()` - Complexity: 2359


### **Pattern Recognition**
- **Handler classes** end with "Handler" and implement standard interface
- **Manager classes** are singletons with lifecycle management
- **Factory classes** have "Factory" in name and create related objects
- **Context managers** can be used with `with` statements

### **File Organization**
- `core/` - System utilities and data management (37 files, 885 functions)
- `communication/` - Communication channels and message processing (39 files, 860 functions)
- `ai/` - AI chatbot functionality (7 files, 219 functions)
- `ui/` - User interface components (29 files, 827 functions)
- `user/` - User context and preferences (4 files, 65 functions)
- `tasks/` - Task management system (5 files, 25 functions)

> **For complete function details, see [FUNCTION_REGISTRY_DETAIL.md](development_docs/FUNCTION_REGISTRY_DETAIL.md)**
