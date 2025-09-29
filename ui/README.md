# UI Development Guide

> **Audience**: Developers working on MHM UI components  
> **Purpose**: Guide for UI development, generation, and maintenance  
> **Style**: Technical, step-by-step, reference-oriented

> **See [README.md](../README.md) for complete navigation and project overview**  
> **See [DEVELOPMENT_WORKFLOW.md](../DEVELOPMENT_WORKFLOW.md) for safe development practices**  
> **See [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) for essential commands**

## 🚀 Quick Reference

### **UI Generation Commands**
```powershell
# Generate all UI files with proper headers (RECOMMENDED)
python ui/generate_ui_files.py

# Generate specific UI file with proper headers
python ui/generate_ui_files.py ui/designs/{filename}.ui

# Legacy method (not recommended - missing headers)
pyside6-uic ui/designs/{filename}.ui -o ui/generated/{filename}_pyqt.py
```

### **UI Development Workflow**
1. **Design**: Create/edit `.ui` files in `ui/designs/`
2. **Generate**: Run `python ui/generate_ui_files.py` to create Python classes with proper headers
3. **Implement**: Create dialog classes in `ui/dialogs/`
4. **Test**: Verify UI functionality and integration

### **Generated UI Files**
All UI files are auto-generated from `.ui` files in `ui/designs/` and stored in `ui/generated/`:

**Dialog Files:**
- `account_creator_dialog_pyqt.py` - Account creation dialog
- `admin_panel_pyqt.py` - Main admin panel interface
- `category_management_dialog_pyqt.py` - Category management dialog
- `channel_management_dialog_pyqt.py` - Channel management dialog
- `checkin_management_dialog_pyqt.py` - Check-in management dialog
- `schedule_editor_dialog_pyqt.py` - Schedule editing dialog
- `task_completion_dialog_pyqt.py` - Task completion dialog
- `task_crud_dialog_pyqt.py` - Task CRUD operations dialog
- `task_edit_dialog_pyqt.py` - Task editing dialog
- `task_management_dialog_pyqt.py` - Task management dialog
- `user_profile_management_dialog_pyqt.py` - User profile management dialog

**Widget Files:**
- `category_selection_widget_pyqt.py` - Category selection widget
- `channel_selection_widget_pyqt.py` - Channel selection widget
- `checkin_element_template_pyqt.py` - Check-in element template
- `checkin_settings_widget_pyqt.py` - Check-in settings widget
- `dynamic_list_field_template_pyqt.py` - Dynamic list field template
- `period_row_template_pyqt.py` - Period row template
- `tag_widget_pyqt.py` - Tag widget
- `task_settings_widget_pyqt.py` - Task settings widget
- `user_profile_settings_widget_pyqt.py` - User profile settings widget

**Note**: All generated files include proper headers identifying them as auto-generated and should not be edited manually.

## UI Generation

**Command**: `pyside6-uic ui/designs/{filename}.ui -o ui/generated/{filename}_pyqt.py`

**Example**: `pyside6-uic ui/designs/task_edit_dialog.ui -o ui/generated/task_edit_dialog_pyqt.py`

**Important**: Always regenerate after editing .ui files. Never edit generated Python files directly.

## File Structure

- `ui/designs/` - Qt Designer .ui files (source)
- `ui/generated/` - Auto-generated Python UI classes
- `ui/dialogs/` - Dialog implementations using generated UI
- `ui/widgets/` - Reusable widget implementations

## Usage Pattern

```python
from ui.generated.{filename}_pyqt import Ui_{ClassName}

class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_{ClassName}()
        self.ui.setupUi(self)
``` 