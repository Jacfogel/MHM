# AI Architecture - Quick Reference

> **Purpose**: Essential architectural patterns for AI collaborators  
> **For details**: See [ARCHITECTURE.md](ARCHITECTURE.md)

## 🚀 Quick Reference

### **Key Modules**
- **User data**: `core/user_data_handlers.py`, `core/user_data_validation.py`
- **UI**: `ui/dialogs/`, `ui/widgets/`
- **Communication**: `communication/` directory
- **Scheduling**: `core/scheduler.py`
- **Configuration**: `core/config.py`

### **Critical Files (Don't Break)**
- `run_mhm.py` - Main entry point
- `core/service.py` - Background service
- `ui/ui_app_qt.py` - Admin interface
- `core/user_data_handlers.py` - Unified user data access

## 🏗️ Data Flow
- **User Data**: `data/users/{user_id}/` → `core/user_data_handlers.py` → UI/communication module
- **Messages**: `resources/default_messages/` → `data/users/{user_id}/messages/`
- **UI**: `.ui` files → `ui/generated/` → `ui/dialogs/` → `ui_app_qt.py`

## 📊 Data Patterns
- **Always use**: `get_user_data()` handler (unified access)
- **Never use**: Legacy user data functions (removed)
- **Preferences**: Flat dict, not nested under 'preferences' key
- **Messages**: Per-user in `data/users/{user_id}/messages/`

## 🎨 UI Patterns
- **Dialogs**: `{purpose}_management_dialog.py`
- **Widgets**: `{purpose}_settings_widget.py`
- **Generated**: `{original_name}_pyqt.py`
- **Designs**: `{purpose}_management_dialog.ui`

## 🚨 Common Issues
- **Data Access**: Use `get_user_data()` handler only
- **UI Integration**: Use proper data handlers, not direct file manipulation
- **Configuration**: Use `core/config.py` for all configuration

---

**Remember**: Follow established patterns, use unified data access, maintain separation of concerns.
