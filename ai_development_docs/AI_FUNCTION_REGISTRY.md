# AI Function Registry - Key Patterns & Decision Trees

> **File**: `ai_development_docs/AI_FUNCTION_REGISTRY.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-06-16 22:23:13
> **Source**: `python development_tools/generate_function_registry.py` - Function Registry Generator
> **Audience**: AI Collaborators  
> **Purpose**: Essential function patterns and decision trees for AI context  
> **Style**: Pattern-focused, decision-tree driven, actionable

## [*] **Current Status**

### **Documentation Coverage: 91.6% [!] GOOD**
- **Total Functions**: 2107
- **Total Methods**: 1328
- **Documented**: 3148/3435
- **Files Scanned**: 207

## [DECISION TREES] **Decision Trees for AI Context**

### **[USER DATA] Need to Handle User Data?**
```
User Data Operations Decision Tree:
+-- `core/user_data_read.py` - Primary data access
+-- `core/user_data_operations.py` - Data management
+-- `core/user_data_validation.py` - Validation
+-- `user/user_context.py` - User context management (20 functions)
+-- `user/user_preferences.py` - User preferences (18 functions)
`-- `core/user_data_read.py` - Account operations```

### **[AI] Need AI/Chatbot Functionality?**
```
AI Operations Decision Tree:
+-- `ai/chatbot.py` - Main AI implementation (65 functions)
+-- `user/context_manager.py` - Context for AI (24 functions)
+-- `communication/message_processing/command_parser.py` - Natural language parsing (60 functions)
+-- `communication/command_handlers/interaction_handlers.py` - Command handlers (20 functions)
`-- `communication/message_processing/interaction_manager.py` - Main interaction flow (49/51 functions)```

### **[COMM] Need Communication/Channels?**
```
Communication Decision Tree:
+-- `communication/core/channel_orchestrator.py` - Main communication (68/86 functions)
+-- `communication/communication_channels/base/base_channel.py` - Channel base class (14 functions)
`-- `communication/core/factory.py` - Channel creation (6 functions)```

### **[UI] Need UI/User Interface?**
```
UI Operations Decision Tree:
+-- `ui/ui_app_qt.py` - Main admin interface (58 functions)
+-- `ui/admin_actions.py` - Admin system/menu actions (27 functions)
+-- `ui/request_actions.py` - Admin request-file actions (14/15 functions)
+-- `ui/dialogs/task_crud_dialog.py` - Task CRUD (28 functions)
`-- `ui/widgets/task_settings_widget.py` - Task settings (32/35 functions)```

### **[CORE] Need Core System Operations?**
```
Core System Decision Tree:
+-- `core/service.py` - Main service (73 functions)
+-- `core/config.py` - Configuration (19 functions)
`-- `scheduler/manager.py` - Scheduling (71/72 functions)```

## [PATTERNS] **Key Function Patterns**

### **Handler Pattern** (10 found)
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
- ... and 7 more

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

### **Dialog Pattern** (16 found)
**Purpose**: Modal user interaction windows
**Location**: `ui/dialog_actions.py`, `ui/dialogs/account_creator_dialog.py`, `ui/dialogs/admin_panel.py`
**Pattern**: 
- Inherit from QDialog
- Use widgets for data entry
- Return result on accept/reject

**Examples**:
- `DialogActions` (ui/dialog_actions.py)
- `AccountCreatorDialog` (ui/dialogs/account_creator_dialog.py)
- `AdminPanelDialog` (ui/dialogs/admin_panel.py)
- ... and 13 more

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
- **User Data**: `core/user_data_read.py` - User data operations
- **Validation**: `core/user_data_validation.py` - Data validation
- **File Operations**: `core/file_operations.py` - File I/O (16 functions)

### **Communication Patterns**
- **Message Sending**: `communication/core/channel_orchestrator.py::_channel_send_failure_detail()`
- **Channel Status**: `core/response_tracking.py::is_automated_messages_enabled()`
- **Command Parsing**: `communication/message_processing/command_parser.py::parse_command()`

## [!] **Areas Needing Attention**

### **High Priority** (Missing Documentation)
- `core/profile_v2_schemas.py` - 24/46 functions undocumented (48% coverage)
- `ui/widgets/dynamic_list_container.py` - 18/22 functions undocumented (18% coverage)
- `communication/core/channel_orchestrator.py` - 18/86 functions undocumented (79% coverage)
- `communication/delivery/message_dispatcher.py` - 15/17 functions undocumented (12% coverage)
- `storage/user_data_write.py` - 15/19 functions undocumented (21% coverage)
- `core/schemas.py` - 15/27 functions undocumented (44% coverage)
- `core/service_requests.py` - 14/34 functions undocumented (59% coverage)
- `ui/widgets/dynamic_list_field.py` - 12/20 functions undocumented (40% coverage)
- `storage/user_data_registry.py` - 11/23 functions undocumented (52% coverage)
- `tasks/task_schemas.py` - 10/10 functions undocumented (0% coverage)

### **Medium Priority** (Partial Coverage)
- `ui/dialogs/task_management_dialog.py` - 4/8 functions undocumented (50% coverage)
- `ui/dialogs/category_management_dialog.py` - 4/12 functions undocumented (67% coverage)
- `storage/user_data_validation.py` - 3/12 functions undocumented (75% coverage)
- `ai/fallback_responses/conversational.py` - 2/4 functions undocumented (50% coverage)
- `communication/command_handlers/handler_registry.py` - 2/5 functions undocumented (60% coverage)
- `core/user_lookup.py` - 1/3 functions undocumented (67% coverage)



## [QUICK REF] **Quick Reference for AI**

### **Common Operations**
1. **User Message**: `communication/message_processing/interaction_manager.py::handle_message()`
2. **AI Response**: `ai/chatbot.py::generate_response()`
3. **Main Entry**: `run_headless_service.py::main()`
4. **Command Parsing**: `communication/message_processing/command_parser.py::get_enhanced_command_parser()`
5. **Error Handling**: `core/error_handling.py::handle_errors()`
6. **Configuration**: `communication/core/channel_orchestrator.py::get_configured_channels()`


### **Complexity Metrics**
Most complex functions (may need refactoring):
1. [OK] `run_tests.py::run_command()` - Complexity: 3215
2. [OK] `run_tests.py::print_combined_summary()` - Complexity: 2960
3. [OK] `communication/message_processing/interaction_manager.py::handle_message()` - Complexity: 2776
4. [OK] `run_tests.py::main()` - Complexity: 2693
5. [OK] `storage/user_data_read.py::get_user_data()` - Complexity: 1622


### **Pattern Recognition**
- **Handler classes** end with "Handler" and implement standard interface
- **Manager classes** are singletons with lifecycle management
- **Factory classes** have "Factory" in name and create related objects
- **Context managers** can be used with `with` statements

### **File Organization**
- `ai/` - AI chatbot functionality (26 files, 266 functions)
- `checkins/` -  (6 files, 135 functions)
- `communication/` - Communication channels and message processing (69 files, 1015 functions)
- `core/` - System utilities and data management (29 files, 605 functions)
- `messages/` -  (5 files, 38 functions)
- `scheduler/` -  (6 files, 94 functions)
- `storage/` -  (11 files, 151 functions)
- `tasks/` - Task management system (7 files, 97 functions)
- `ui/` - User interface components (40 files, 918 functions)
- `user/` - User context and preferences (5 files, 66 functions)

> **For complete function details, see [FUNCTION_REGISTRY_DETAIL.md](development_docs/FUNCTION_REGISTRY_DETAIL.md)**
