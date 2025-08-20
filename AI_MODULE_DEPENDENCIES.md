# AI Module Dependencies - Key Relationships & Patterns

> **Audience**: AI Collaborators  
> **Purpose**: Essential module relationships and dependency patterns for AI context  
> **Style**: Pattern-focused, relationship-driven, actionable

## 🎯 **Current Status**

### **Dependency Coverage: 100.0% ✅ COMPLETED**
- **Files Scanned**: 176
- **Total Imports**: 1840
- **Standard Library**: 0 (0.0%)
- **Third-Party**: 323 (17.6%)
- **Local Imports**: 846 (46.0%)

## 🧠 **Dependency Decision Trees**

### **🔧 Need Core System Access?**
```
Core System Dependencies:
├── Configuration & Setup
│   ├── `core/config.py` ← Standard library (os, json, typing)
│   └── `core/logger.py` ← Standard library (logging, pathlib)
├── Data Management
│   ├── `core/file_operations.py` ← Standard library (json, pathlib)
│   ├── `core/user_data_handlers.py` ← core/config, core/logger
│   └── `core/user_data_manager.py` ← core/user_data_handlers
└── Error Handling
    └── `core/error_handling.py` ← Standard library (logging, traceback)
```

### **🤖 Need AI/Chatbot Dependencies?**
```
AI System Dependencies:
├── AI Core
│   ├── `bot/ai_chatbot.py` ← core/config, core/logger, core/user_data_handlers
│   └── `bot/user_context_manager.py` ← core/user_data_handlers
├── Command Processing
│   ├── `bot/enhanced_command_parser.py` ← bot/ai_chatbot
│   ├── `bot/interaction_handlers.py` ← core/user_data_handlers, core/task_management
│   └── `bot/interaction_manager.py` ← bot/enhanced_command_parser, bot/interaction_handlers
└── Communication
    └── `bot/communication_manager.py` ← bot/ai_chatbot, bot/conversation_manager
```

### **💬 Need Communication Channel Dependencies?**
```
Communication Dependencies:
├── Channel Infrastructure
│   ├── `bot/base_channel.py` ← Standard library (abc, dataclasses, enum)
│   ├── `bot/channel_factory.py` ← bot/base_channel
│   └── `bot/communication_manager.py` ← bot/channel_factory, bot/base_channel
├── Specific Channels
│   ├── `bot/discord_bot.py` ← Third-party (discord.py), bot/base_channel
│   ├── `bot/email_bot.py` ← Standard library (smtplib, imaplib), bot/base_channel
│   └── `bot/telegram_bot.py` ← Third-party (telegram), bot/base_channel
└── Conversation Flow
    └── `bot/conversation_manager.py` ← core/user_data_handlers, bot/user_context_manager
```

### **🖥️ Need UI Dependencies?**
```
UI Dependencies:
├── Main Application
│   └── `ui/ui_app_qt.py` ← Third-party (PySide6), core/config, bot/communication_manager
├── Dialogs
│   ├── `ui/dialogs/account_creator_dialog.py` ← ui/widgets, core/user_data_handlers
│   ├── `ui/dialogs/user_profile_dialog.py` ← ui/widgets, core/user_data_handlers
│   └── `ui/dialogs/task_management_dialog.py` ← ui/widgets, core/task_management
└── Widgets
    ├── `ui/widgets/tag_widget.py` ← Third-party (PySide6)
    ├── `ui/widgets/task_settings_widget.py` ← ui/widgets/tag_widget
    └── `ui/widgets/user_profile_settings_widget.py` ← Third-party (PySide6)
```

## 🔍 **Key Dependency Patterns**

### **Core → Bot Pattern** (Most Common)
**Description**: Bot modules depend on core system modules
**Examples**:
- `bot/ai_chatbot.py` → `core/config.py`, `core/logger.py`
- `bot/interaction_handlers.py` → `core/user_data_handlers.py`
- `bot/communication_manager.py` → `core/logger.py`

**Why Important**: Ensures bots have access to system configuration and data

### **UI → Core Pattern**
**Description**: UI modules depend on core data and configuration
**Examples**:
- `ui/dialogs/` → `core/user_data_handlers.py`
- `ui/ui_app_qt.py` → `core/config.py`
- `ui/widgets/` → `core/validation.py`

**Why Important**: UI needs access to user data and system configuration

### **Bot → Bot Pattern**
**Description**: Bot modules depend on other bot modules for functionality
**Examples**:
- `bot/interaction_manager.py` → `bot/enhanced_command_parser.py`
- `bot/communication_manager.py` → `bot/ai_chatbot.py`
- `bot/conversation_manager.py` → `bot/user_context_manager.py`

**Why Important**: Enables modular bot functionality and separation of concerns

### **Third-Party Integration Pattern**
**Description**: External library dependencies for specific functionality
**Examples**:
- `bot/discord_bot.py` → `discord.py`
- `ui/ui_app_qt.py` → `PySide6`
- `bot/telegram_bot.py` → `python-telegram-bot`

**Why Important**: Provides external service integration and UI framework

## 🎯 **Critical Dependencies for AI Context**

### **Entry Points** (Start Here)
- `run_mhm.py` → `core/service.py` - Main application entry
- `ui/ui_app_qt.py` → `bot/communication_manager.py` - UI startup
- `bot/interaction_manager.py` → `bot/ai_chatbot.py` - Message handling

### **Data Flow Dependencies**
- **User Data**: `core/user_data_handlers.py` ← `core/config.py`, `core/logger.py`
- **AI Context**: `bot/user_context_manager.py` ← `core/user_data_handlers.py`
- **File Operations**: `core/file_operations.py` ← Standard library (json, pathlib)

### **Communication Dependencies**
- **Channel Management**: `bot/communication_manager.py` ← `bot/channel_factory.py`
- **Message Handling**: `bot/interaction_manager.py` ← `bot/enhanced_command_parser.py`
- **AI Integration**: `bot/ai_chatbot.py` ← `core/config.py`, `core/user_data_handlers.py`

## ⚠️ **Dependency Risk Areas**

### **High Coupling** (Tight Dependencies)
- `bot/interaction_handlers.py` → `core/user_data_handlers.py` (Heavy dependency)
- `ui/dialogs/` → `core/user_data_handlers.py` (UI tightly coupled to data)
- `bot/communication_manager.py` → `bot/ai_chatbot.py` (Communication depends on AI)

### **Third-Party Risks**
- `bot/discord_bot.py` → `discord.py` (External API dependency)
- `ui/ui_app_qt.py` → `PySide6` (UI framework dependency)
- `bot/telegram_bot.py` → `python-telegram-bot` (External API dependency)

### **Circular Dependencies** (Potential Issues)
- Monitor: `bot/communication_manager.py` ↔ `bot/conversation_manager.py`
- Monitor: `core/user_data_handlers.py` ↔ `core/user_data_manager.py`

## 🚀 **Quick Reference for AI**

### **Common Dependency Patterns**
1. **Core System**: Standard library + minimal local dependencies
2. **Bot Modules**: Core dependencies + other bot modules
3. **UI Modules**: Third-party UI framework + core data access
4. **Data Access**: Core configuration + logging dependencies

### **Dependency Rules**
- **Core modules** should have minimal dependencies (mostly standard library)
- **Bot modules** can depend on core and other bot modules
- **UI modules** should depend on core data access, not direct bot access
- **Third-party dependencies** should be isolated to specific modules

### **When Adding Dependencies**
- **Check existing patterns** in similar modules
- **Prefer core modules** over direct third-party access
- **Avoid circular dependencies** between modules
- **Use dependency injection** for testability

### **Module Organization**
- `core/` - System utilities (minimal dependencies)
- `bot/` - Communication and AI (depends on core)
- `ui/` - User interface (depends on core, minimal bot dependencies)
- `user/` - User context (depends on core)
- `tasks/` - Task management (depends on core)

> **For complete dependency details, see [MODULE_DEPENDENCIES_DETAIL.md](MODULE_DEPENDENCIES_DETAIL.md)**  
> **Last Updated**: 2025-08-19 23:41:42
