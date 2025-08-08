# AI Function Registry - Key Patterns & Status

> **Audience**: AI Collaborators  
> **Purpose**: Key function patterns and current status for AI context  
> **Style**: Concise, pattern-focused, actionable

## 🎯 **Current Function Status**

### **Documentation Coverage: 94.0% ⚠️ GOOD**
- **Total Functions**: 1900
- **Total Methods**: 1430
- **Documented**: 3131/3330
- **Files Scanned**: 162

## 🔧 **Key Function Patterns**

### **Core System Patterns**
- **19 core modules** - Configuration, error handling, data management
  - `core/auto_cleanup.py`: 9/9 functions documented
  - `core/backup_manager.py`: 18/18 functions documented
  - `core/checkin_analytics.py`: 19/19 functions documented
  - `core/config.py`: 19/19 functions documented
  - `core/error_handling.py`: 25/27 functions documented
  - `core/file_operations.py`: 5/5 functions documented
  - `core/logger.py`: 26/27 functions documented
  - `core/message_management.py`: 11/11 functions documented
  - `core/response_tracking.py`: 13/13 functions documented
  - `core/scheduler.py`: 30/31 functions documented
  - `core/schedule_management.py`: 16/19 functions documented
  - `core/service.py`: 16/16 functions documented
  - `core/service_utilities.py`: 7/7 functions documented
  - `core/ui_management.py`: 6/6 functions documented
  - `core/user_data_handlers.py`: 10/10 functions documented
  - `core/user_data_manager.py`: 25/25 functions documented
  - `core/user_data_validation.py`: 5/8 functions documented
  - `core/user_management.py`: 44/47 functions documented
  - `core/validation.py`: 0/0 functions documented

### **Communication Patterns**
- **13 bot modules** - Channel management, communication
  - `bot/ai_chatbot.py`: 31/31 functions documented
  - `bot/base_channel.py`: 7/7 functions documented
  - `bot/channel_factory.py`: 3/3 functions documented
  - `bot/channel_registry.py`: 1/1 functions documented
  - `bot/communication_manager.py`: 37/37 functions documented
  - `bot/conversation_manager.py`: 13/13 functions documented
  - `bot/discord_bot.py`: 19/19 functions documented
  - `bot/email_bot.py`: 9/9 functions documented
  - `bot/enhanced_command_parser.py`: 15/15 functions documented
  - `bot/interaction_handlers.py`: 38/62 functions documented
  - `bot/interaction_manager.py`: 11/11 functions documented
  - `bot/telegram_bot.py`: 29/35 functions documented
  - `bot/user_context_manager.py`: 13/13 functions documented

### **UI Patterns**
- **41 UI modules** - Dialogs, widgets, user interaction
  - `ui/ui_app_qt.py`: 42/50 functions documented
  - `ui/dialogs/account_creator_dialog.py`: 29/30 functions documented
  - `ui/dialogs/admin_panel.py`: 4/4 functions documented
  - `ui/dialogs/category_management_dialog.py`: 4/6 functions documented
  - `ui/dialogs/channel_management_dialog.py`: 1/4 functions documented
  - `ui/dialogs/checkin_management_dialog.py`: 5/6 functions documented
  - `ui/dialogs/schedule_editor_dialog.py`: 16/17 functions documented
  - `ui/dialogs/task_completion_dialog.py`: 8/8 functions documented
  - `ui/dialogs/task_crud_dialog.py`: 14/14 functions documented
  - `ui/dialogs/task_edit_dialog.py`: 18/18 functions documented
  - `ui/dialogs/task_management_dialog.py`: 2/4 functions documented
  - `ui/dialogs/user_profile_dialog.py`: 20/20 functions documented
  - `ui/generated/account_creator_dialog_pyqt.py`: 2/3 functions documented
  - `ui/generated/admin_panel_pyqt.py`: 0/2 functions documented
  - `ui/generated/category_management_dialog_pyqt.py`: 2/3 functions documented
  - `ui/generated/category_selection_widget_pyqt.py`: 2/3 functions documented
  - `ui/generated/channel_management_dialog_pyqt.py`: 2/3 functions documented
  - `ui/generated/channel_selection_widget_pyqt.py`: 2/3 functions documented
  - `ui/generated/checkin_element_template_pyqt.py`: 2/3 functions documented
  - `ui/generated/checkin_management_dialog_pyqt.py`: 2/3 functions documented
  - `ui/generated/checkin_settings_widget_pyqt.py`: 2/2 functions documented
  - `ui/generated/dynamic_list_field_template_pyqt.py`: 2/2 functions documented
  - `ui/generated/period_row_template_pyqt.py`: 2/3 functions documented
  - `ui/generated/schedule_editor_dialog_pyqt.py`: 2/3 functions documented
  - `ui/generated/tag_widget_pyqt.py`: 0/2 functions documented
  - `ui/generated/task_completion_dialog_pyqt.py`: 0/2 functions documented
  - `ui/generated/task_crud_dialog_pyqt.py`: 0/2 functions documented
  - `ui/generated/task_edit_dialog_pyqt.py`: 0/2 functions documented
  - `ui/generated/task_management_dialog_pyqt.py`: 2/3 functions documented
  - `ui/generated/task_settings_widget_pyqt.py`: 0/2 functions documented
  - `ui/generated/user_profile_management_dialog_pyqt.py`: 2/3 functions documented
  - `ui/generated/user_profile_settings_widget_pyqt.py`: 2/2 functions documented
  - `ui/widgets/category_selection_widget.py`: 1/3 functions documented
  - `ui/widgets/channel_selection_widget.py`: 5/8 functions documented
  - `ui/widgets/checkin_settings_widget.py`: 16/16 functions documented
  - `ui/widgets/dynamic_list_container.py`: 2/11 functions documented
  - `ui/widgets/dynamic_list_field.py`: 4/10 functions documented
  - `ui/widgets/period_row_widget.py`: 13/13 functions documented
  - `ui/widgets/tag_widget.py`: 14/14 functions documented
  - `ui/widgets/task_settings_widget.py`: 12/13 functions documented
  - `ui/widgets/user_profile_settings_widget.py`: 8/8 functions documented

## 🎯 **For AI Context**

### **When Working with Functions**
- **Check documentation status** before modifying functions
- **Use existing patterns** from well-documented modules
- **Follow naming conventions** established in core modules
- **Add docstrings** when creating new functions

### **Key Function Categories**
- **Core Functions**: `core/` - System utilities and data management
- **Communication Functions**: `bot/` - Channel and message handling
- **UI Functions**: `ui/` - User interface and interaction
- **User Functions**: `user/` - User data and preferences
- **Task Functions**: `tasks/` - Task management and scheduling

### **Documentation Standards**
- **All functions should have docstrings** explaining purpose and parameters
- **Use clear, action-oriented descriptions**
- **Include parameter types and return values** when relevant
- **Follow existing patterns** in similar modules

> **For complete function registry and detailed information, see [FUNCTION_REGISTRY_DETAIL.md](FUNCTION_REGISTRY_DETAIL.md)**
> **Last Updated**: 2025-08-07 23:03:09
