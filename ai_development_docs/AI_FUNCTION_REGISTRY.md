# AI Function Registry - Key Patterns & Decision Trees

> **Audience**: AI Collaborators  
> **Purpose**: Essential function patterns and decision trees for AI context  
> **Style**: Pattern-focused, decision-tree driven, actionable

## 🎯 **Current Status**

### **Documentation Coverage: 94.8% ⚠️ GOOD**
- **Total Functions**: 2575
- **Total Methods**: 2112
- **Documented**: 4443/4687
- **Files Scanned**: 139

## 🧠 **Decision Trees for AI Context**

### **🔧 Need to Handle User Data?**
```
User Data Operations Decision Tree:
├── Core Data Access
│   ├── `core/user_data_handlers.py` - Primary data access (10 functions)
│   ├── `core/user_data_manager.py` - Data management (25 functions)
│   └── `core/user_data_validation.py` - Validation (5/8 functions)
├── User Context
│   ├── `user/user_context.py` - User context management
│   └── `user/user_preferences.py` - User preferences
└── User Management
    └── `core/user_management.py` - Account operations (44/47 functions)
```

### **🤖 Need AI/Chatbot Functionality?**
```
AI Operations Decision Tree:
├── AI Chatbot
│   ├── `ai/chatbot.py` - Main AI implementation (31 functions)
│   └── `user/context_manager.py` - Context for AI (13 functions)
├── Command Parsing
│   ├── `communication/message_processing/command_parser.py` - Natural language parsing (15 functions)
│   └── `communication/command_handlers/interaction_handlers.py` - Command handlers (38/62 functions)
└── Interaction Management
    └── `communication/message_processing/interaction_manager.py` - Main interaction flow (11 functions)
```

### **💬 Need Communication/Channels?**
```
Communication Decision Tree:
├── Channel Management
│   ├── `communication/core/channel_orchestrator.py` - Main communication (37 functions)
│   ├── `communication/communication_channels/base/base_channel.py` - Channel base class (7 functions)
│   └── `communication/core/factory.py` - Channel creation (3 functions)
├── Specific Channels
│   ├── `communication/communication_channels/discord/bot.py` - Discord integration (19 functions)
│   ├── `communication/communication_channels/email/bot.py` - Email integration (9 functions)

└── Conversation Flow
    └── `communication/message_processing/conversation_flow_manager.py` - Conversation management (13 functions)
```

### **🖥️ Need UI/User Interface?**
```
UI Operations Decision Tree:
├── Main Application
│   └── `ui/ui_app_qt.py` - Main admin interface (42/50 functions)
├── Dialogs
│   ├── `ui/dialogs/account_creator_dialog.py` - Account creation (29/30 functions)
│   ├── `ui/dialogs/user_profile_dialog.py` - User profiles (20 functions)
│   ├── `ui/dialogs/task_management_dialog.py` - Task management (2/4 functions)
│   └── `ui/dialogs/schedule_editor_dialog.py` - Schedule editing (16/17 functions)
└── Widgets
    ├── `ui/widgets/tag_widget.py` - Tag management (14 functions)
    ├── `ui/widgets/task_settings_widget.py` - Task settings (12/13 functions)
    └── `ui/widgets/user_profile_settings_widget.py` - Profile settings (8 functions)
```

### **⚙️ Need Core System Operations?**
```
Core System Decision Tree:
├── Configuration
│   └── `core/config.py` - System configuration (19 functions)
├── Error Handling
│   └── `core/error_handling.py` - Error management (25/27 functions)
├── File Operations
│   ├── `core/file_operations.py` - File I/O (5 functions)
│   └── `core/backup_manager.py` - Backup operations (18 functions)
├── Logging
│   └── `core/logger.py` - Logging system (26/27 functions)
└── Scheduling
    ├── `core/scheduler.py` - Task scheduling (30/31 functions)
    └── `core/schedule_management.py` - Schedule management (16/19 functions)
```

## 🔍 **Key Function Patterns**

### **Handler Pattern** (Most Common)
**Purpose**: Handle specific user intents or operations
**Location**: `communication/command_handlers/interaction_handlers.py`, `ui/dialogs/`, `core/`
**Pattern**: 
- `can_handle(intent)` - Check if handler supports intent
- `handle(user_id, parsed_command)` - Process the command
- `get_help()` - Return help text
- `get_examples()` - Return usage examples

**Examples**:
- `TaskManagementHandler` - Task CRUD operations
- `ProfileHandler` - User profile management
- `ScheduleManagementHandler` - Schedule operations

### **Manager Pattern** (Singleton)
**Purpose**: Centralized management of system components
**Location**: `communication/core/channel_orchestrator.py`, `communication/message_processing/interaction_manager.py`
**Pattern**:
- Singleton instance management
- Lifecycle methods (`start()`, `stop()`, `initialize()`)
- Status reporting methods

### **Factory Pattern**
**Purpose**: Create instances of related objects
**Location**: `communication/core/factory.py`
**Pattern**:
- `register_channel(name, channel_class)` - Register channel types
- `create_channel(name, config)` - Create channel instances
- `get_available_channels()` - List available types

### **Context Manager Pattern**
**Purpose**: Safe resource management
**Location**: `core/error_handling.py`
**Pattern**:
- `__enter__()` and `__exit__()` methods
- Automatic cleanup and error handling
- Used with `with` statements

## 🎯 **Critical Functions for AI Context**

### **Entry Points** (Start Here)
- `communication/message_processing/interaction_manager.py::handle_message()` - Main message entry point
- `ai/chatbot.py::generate_response()` - AI response generation
- `core/user_data_handlers.py::get_user_data()` - User data access
- `ui/ui_app_qt.py::__init__()` - UI application startup

### **Data Access Patterns**
- **User Data**: `core/user_data_handlers.py` (10 functions)
- **Validation**: `core/user_data_validation.py` (5/8 functions)
- **File Operations**: `core/file_operations.py` (5 functions)

### **Communication Patterns**
- **Message Sending**: `communication/core/channel_orchestrator.py::send_message_sync()`
- **Channel Status**: `communication/core/channel_orchestrator.py::is_channel_ready()`
- **Command Parsing**: `communication/message_processing/command_parser.py::parse()`

## ⚠️ **Areas Needing Attention**

### **High Priority** (Missing Documentation)
- `communication/command_handlers/interaction_handlers.py` - 24/62 functions undocumented
- `core/user_data_validation.py` - 3/8 functions undocumented
- `ui/dialogs/task_management_dialog.py` - 2/4 functions undocumented

### **Medium Priority** (Partial Coverage)
- `ui/ui_app_qt.py` - 8/50 functions undocumented
- `core/error_handling.py` - 2/27 functions undocumented
- `core/logger.py` - 1/27 functions undocumented

## 🚀 **Quick Reference for AI**

### **Common Operations**
1. **User Message**: `communication/message_processing/interaction_manager.py::handle_message()`
2. **AI Response**: `ai/chatbot.py::generate_response()`
3. **User Data**: `core/user_data_handlers.py::get_user_data()`
4. **File Save**: `core/file_operations.py::save_json_data()`
5. **Error Handling**: `core/error_handling.py::handle_errors` decorator

### **Pattern Recognition**
- **Handler classes** end with "Handler" and implement standard interface
- **Manager classes** are singletons with lifecycle management
- **Factory classes** have "Factory" in name and create related objects
- **Context managers** can be used with `with` statements

### **File Organization**
- `core/` - System utilities and data management
- `communication/` - Communication channels and message processing
- `ai/` - AI chatbot functionality
- `ui/` - User interface components
- `user/` - User context and preferences
- `tasks/` - Task management system

> **For complete function details, see [FUNCTION_REGISTRY_DETAIL.md](development_docs/FUNCTION_REGISTRY_DETAIL.md)**  
> **Last Updated**: 2025-09-15 00:22:48
