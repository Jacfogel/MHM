# AI Module Dependencies - Key Patterns & Status

> **Audience**: AI Collaborators  
> **Purpose**: Key module dependency patterns and current status for AI context  
> **Style**: Concise, pattern-focused, actionable

## 🎯 **Current Module Status**

### **Dependency Overview**
- **Total Modules**: 162
- **Total Imports**: 1678
- **Local Dependencies**: 800
- **Coverage**: 100% (all modules documented)

## 🔧 **Key Module Patterns**

### **Core System Dependencies**
- **19 core modules** - System utilities and data management
  - `core/auto_cleanup.py`: 3/11 local dependencies
  - `core/backup_manager.py`: 4/12 local dependencies
  - `core/checkin_analytics.py`: 3/7 local dependencies
  - `core/config.py`: 1/6 local dependencies
  - `core/error_handling.py`: 1/12 local dependencies
  - `core/file_operations.py`: 5/11 local dependencies
  - `core/logger.py`: 0/13 local dependencies
  - `core/message_management.py`: 7/13 local dependencies
  - `core/response_tracking.py`: 5/10 local dependencies
  - `core/scheduler.py`: 14/29 local dependencies
  - `core/schedule_management.py`: 9/14 local dependencies
  - `core/service.py`: 13/24 local dependencies
  - `core/service_utilities.py`: 3/12 local dependencies
  - `core/ui_management.py`: 5/6 local dependencies
  - `core/user_data_handlers.py`: 18/21 local dependencies
  - `core/user_data_manager.py`: 10/18 local dependencies
  - `core/user_data_validation.py`: 7/15 local dependencies
  - `core/user_management.py`: 39/50 local dependencies
  - `core/validation.py`: 1/2 local dependencies

### **Communication Dependencies**
- **13 bot modules** - Channel management and communication
  - `bot/ai_chatbot.py`: 6/16 local dependencies
  - `bot/base_channel.py`: 2/7 local dependencies
  - `bot/channel_factory.py`: 3/4 local dependencies
  - `bot/channel_registry.py`: 4/4 local dependencies
  - `bot/communication_manager.py`: 17/31 local dependencies
  - `bot/conversation_manager.py`: 4/6 local dependencies
  - `bot/discord_bot.py`: 16/28 local dependencies
  - `bot/email_bot.py`: 4/11 local dependencies
  - `bot/enhanced_command_parser.py`: 5/9 local dependencies
  - `bot/interaction_handlers.py`: 27/39 local dependencies
  - `bot/interaction_manager.py`: 12/13 local dependencies
  - `bot/telegram_bot.py`: 12/27 local dependencies
  - `bot/user_context_manager.py`: 7/11 local dependencies

### **UI Dependencies**
- **41 UI modules** - User interface and interaction
  - `ui/ui_app_qt.py`: 31/48 local dependencies
  - `ui/dialogs/account_creator_dialog.py`: 20/29 local dependencies
  - `ui/dialogs/admin_panel.py`: 0/2 local dependencies
  - `ui/dialogs/category_management_dialog.py`: 7/9 local dependencies
  - `ui/dialogs/channel_management_dialog.py`: 4/7 local dependencies
  - `ui/dialogs/checkin_management_dialog.py`: 8/13 local dependencies
  - `ui/dialogs/schedule_editor_dialog.py`: 7/15 local dependencies
  - `ui/dialogs/task_completion_dialog.py`: 3/5 local dependencies
  - `ui/dialogs/task_crud_dialog.py`: 13/15 local dependencies
  - `ui/dialogs/task_edit_dialog.py`: 5/7 local dependencies
  - `ui/dialogs/task_management_dialog.py`: 9/11 local dependencies
  - `ui/dialogs/user_profile_dialog.py`: 9/17 local dependencies
  - `ui/generated/account_creator_dialog_pyqt.py`: 0/3 local dependencies
  - `ui/generated/admin_panel_pyqt.py`: 0/3 local dependencies
  - `ui/generated/category_management_dialog_pyqt.py`: 0/3 local dependencies
  - `ui/generated/category_selection_widget_pyqt.py`: 0/3 local dependencies
  - `ui/generated/channel_management_dialog_pyqt.py`: 0/3 local dependencies
  - `ui/generated/channel_selection_widget_pyqt.py`: 0/3 local dependencies
  - `ui/generated/checkin_element_template_pyqt.py`: 0/3 local dependencies
  - `ui/generated/checkin_management_dialog_pyqt.py`: 0/3 local dependencies
  - `ui/generated/checkin_settings_widget_pyqt.py`: 0/3 local dependencies
  - `ui/generated/dynamic_list_field_template_pyqt.py`: 0/3 local dependencies
  - `ui/generated/period_row_template_pyqt.py`: 0/3 local dependencies
  - `ui/generated/schedule_editor_dialog_pyqt.py`: 0/3 local dependencies
  - `ui/generated/tag_widget_pyqt.py`: 0/3 local dependencies
  - `ui/generated/task_completion_dialog_pyqt.py`: 0/3 local dependencies
  - `ui/generated/task_crud_dialog_pyqt.py`: 0/3 local dependencies
  - `ui/generated/task_edit_dialog_pyqt.py`: 0/3 local dependencies
  - `ui/generated/task_management_dialog_pyqt.py`: 0/3 local dependencies
  - `ui/generated/task_settings_widget_pyqt.py`: 0/3 local dependencies
  - `ui/generated/user_profile_management_dialog_pyqt.py`: 0/3 local dependencies
  - `ui/generated/user_profile_settings_widget_pyqt.py`: 0/3 local dependencies
  - `ui/widgets/category_selection_widget.py`: 2/3 local dependencies
  - `ui/widgets/channel_selection_widget.py`: 2/6 local dependencies
  - `ui/widgets/checkin_settings_widget.py`: 8/14 local dependencies
  - `ui/widgets/dynamic_list_container.py`: 2/5 local dependencies
  - `ui/widgets/dynamic_list_field.py`: 4/7 local dependencies
  - `ui/widgets/period_row_widget.py`: 4/10 local dependencies
  - `ui/widgets/tag_widget.py`: 4/9 local dependencies
  - `ui/widgets/task_settings_widget.py`: 9/13 local dependencies
  - `ui/widgets/user_profile_settings_widget.py`: 4/12 local dependencies

## 🎯 **For AI Context**

### **When Working with Modules**
- **Check dependencies** before modifying modules
- **Understand import patterns** in similar modules
- **Follow dependency structure** established in core modules
- **Minimize circular dependencies** when adding new imports

### **Key Module Categories**
- **Core Modules**: `core/` - System utilities and data management
- **Communication Modules**: `bot/` - Channel and message handling
- **UI Modules**: `ui/` - User interface and interaction
- **User Modules**: `user/` - User data and preferences
- **Task Modules**: `tasks/` - Task management and scheduling

### **Dependency Patterns**
- **Core modules** are imported by most other modules
- **UI modules** depend on core and user modules
- **Bot modules** depend on core and communication modules
- **User modules** are imported by UI and core modules

> **For complete module dependencies and detailed information, see [MODULE_DEPENDENCIES_DETAIL.md](MODULE_DEPENDENCIES_DETAIL.md)**
> **Last Updated**: 2025-08-07 23:03:14
