# UI Development Guide

> **File**: `ui/UI_GUIDE.md`  
> **Audience**: Developers working on MHM UI components  
> **Purpose**: Guide for UI development, generation, and maintenance  
> **Style**: Technical, step-by-step, reference-oriented  

This document is internal to the MHM project.

See [README.md](README.md), section 1 **"Navigation"** and section 7 **"Project Structure"** for documentation index and directory layout.  
See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md), section 1 **"Safety First"** and section 3 **"Development Process"** before changing UI code.

---

## Quick Reference

**UI Generation Commands**

```powershell
# From the project root

# Generate all UI files with proper headers (RECOMMENDED)
python ui/generate_ui_files.py

# Generate specific UI file with proper headers
python ui/generate_ui_files.py ui/designs/{filename}.ui

# Direct pyside6-uic call (NOT RECOMMENDED - missing MHM headers)
pyside6-uic ui/designs/{filename}.ui -o ui/generated/{filename}_pyqt.py
```

- Always prefer `python ui/generate_ui_files.py`.  
- The wrapper script:
  - Calls `pyside6-uic` under the hood
  - Adds MHM-standard generated file headers (timestamps, source path, "do not edit" notes)
  - Is wrapped in `handle_errors("generating UI file", ...)` for consistent error handling

If you ever use `pyside6-uic` directly (for debugging), **re-run** `python ui/generate_ui_files.py` afterward so headers stay consistent.

---

**UI Development Workflow**

1. **Design**: Create/edit `.ui` files in `ui/designs/`.
2. **Generate**: Run `python ui/generate_ui_files.py` to create Python classes with proper headers.
3. **Implement**: Create dialog and widget classes in `ui/dialogs/` and `ui/widgets/` that use the generated UI.
4. **Test**:
   - Verify basic layout and behavior in the PySide6 UI.
   - Confirm integration with service processes and communication channels, as described in:
     - [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md), section 4 **"Testing Strategy"**  
     - [TESTING_GUIDE.md](tests/TESTING_GUIDE.md), section 6 **"Running Tests"**

---

**Generated UI Files**

All UI files are auto-generated from `.ui` files in `ui/designs/` and stored in `ui/generated/`.

**Dialog Files (examples):**

- `ui/generated/account_creator_dialog_pyqt.py` - Account creation dialog  
- `ui/generated/admin_panel_pyqt.py` - Main admin panel interface  
- `ui/generated/category_management_dialog_pyqt.py` - Category management dialog  
- `ui/generated/channel_management_dialog_pyqt.py` - Channel management dialog  
- `ui/generated/checkin_management_dialog_pyqt.py` - Check-in management dialog  
- `ui/generated/message_editor_dialog_pyqt.py` - Message editing dialog (CRUD operations)  
- `ui/generated/schedule_editor_dialog_pyqt.py` - Schedule editing dialog  
- `ui/generated/task_completion_dialog_pyqt.py` - Task completion dialog  
- `ui/generated/task_crud_dialog_pyqt.py` - Task CRUD operations dialog  
- `ui/generated/task_edit_dialog_pyqt.py` - Task editing dialog  
- `ui/generated/task_management_dialog_pyqt.py` - Task management dialog  
- `ui/generated/user_analytics_dialog_pyqt.py` - User analytics dialog (wellness insights)  
- `ui/generated/user_profile_management_dialog_pyqt.py` - User profile management dialog  

**Widget Files (examples):**

- `ui/generated/category_selection_widget_pyqt.py` - Category selection widget  
- `ui/generated/channel_selection_widget_pyqt.py` - Channel selection widget  
- `ui/generated/checkin_element_template_pyqt.py` - Check-in element template  
- `ui/generated/checkin_settings_widget_pyqt.py` - Check-in settings widget  
- `ui/generated/dynamic_list_field_template_pyqt.py` - Dynamic list field template  
- `ui/generated/period_row_template_pyqt.py` - Period row template  
- `ui/generated/tag_widget_pyqt.py` - Tag widget  
- `ui/generated/task_settings_widget_pyqt.py` - Task settings widget  
- `ui/generated/user_profile_settings_widget_pyqt.py` - User profile settings widget  

> These lists are examples only. The authoritative list of generated UI files is whatever is currently in `ui/generated/`.

**Note:** All generated files include headers identifying them as auto-generated and **must not be edited manually**. Always change the `.ui` source file in `ui/designs/` and regenerate.

---

## 1. UI Generation

The **preferred** way to generate UI code is the wrapper script:

```powershell
# From project root
python ui/generate_ui_files.py
```

This will:

- Scan `ui/designs/` for all `.ui` files  
- Generate matching `*_pyqt.py` files into `ui/generated/`  
- Add standard MHM headers, including:
  - Generation timestamp
  - Source `.ui` path and output path
  - "Do not edit manually" warnings

To generate **one specific** UI file:

```powershell
python ui/generate_ui_files.py ui/designs/{filename}.ui
```

Direct `pyside6-uic` use is available but discouraged:

```powershell
pyside6-uic ui/designs/{filename}.ui -o ui/generated/{filename}_pyqt.py
```

If you do this (for example, when experimenting with `pyside6-uic` options):

1. Run `python ui/generate_ui_files.py ui/designs/{filename}.ui` afterward to restore standard headers.
2. Verify that imports in your dialog/widget code still point to the correct module name.

**Key rules:**

- **Never** edit files in `ui/generated/` by hand. Changes will be lost on next regeneration.  
- **Always** regenerate after editing `.ui` files.  
- If generated files fail or look wrong, check:
  - The `.ui` file in `ui/designs/`  
  - That `pyside6-uic` is installed and on your PATH  
  - `ui/generate_ui_files.py` output and logs for errors

---

## 2. File Structure

Core UI layout:

- `ui/designs/` - Qt Designer `.ui` files (source of truth for layout)
- `ui/generated/` - Auto-generated PySide6 UI classes (`*_pyqt.py`), created by `generate_ui_files.py`
- `ui/dialogs/` - Dialog implementation classes that:
  - Subclass `QDialog` (or `QWidget`, etc.)
  - Own an instance of the generated `Ui_*` class
  - Wire up signals, slots, and business logic
- `ui/widgets/` - Reusable widget implementations built on top of generated UI components
- `ui/ui_app_qt.py` - Main Qt admin panel entry point:
  - Imports `Ui_ui_app_mainwindow` from `ui.generated.admin_panel_pyqt`
  - Manages service processes, configuration validation, and high-level UI workflows

Where relevant, follow the error-handling and logging patterns described in:

- [ERROR_HANDLING_GUIDE.md](core/ERROR_HANDLING_GUIDE.md), section 2 **"Architecture Overview"**  
- [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md), section 3 **"Component Loggers and Layout"**

---

## 3. Usage Pattern

Basic pattern for using a generated UI class in a dialog:

```python
from PySide6.QtWidgets import QDialog
from ui.generated.{filename}_pyqt import Ui_{ClassName}

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_{ClassName}()
        self.ui.setupUi(self)
        # Connect signals, initialize state, etc.
```

For the main admin panel (as implemented in `ui/ui_app_qt.py`):

```python
from PySide6.QtWidgets import QMainWindow
from ui.generated.admin_panel_pyqt import Ui_ui_app_mainwindow

class MHMManagerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ui_app_mainwindow()
        self.ui.setupUi(self)
        # Load theme, connect signals, initialize UI state, etc.
```

**Implementation checklist:**

- Import from `ui.generated.*` only; never from `.ui` files directly.  
- Instantiate the `Ui_*` class once per widget/dialog and call `.setupUi(self)`.  
- Keep business logic in the dialog/widget class, not in the generated module.  
- When UI elements change in Qt Designer:
  1. Save the `.ui` file.
  2. Run `python ui/generate_ui_files.py`.
  3. Fix any broken attribute references in your dialog/widget code.

---

## 4. UI Flow and Signal-Based Updates

MHM UI follows a consistent flow so updates are predictable and maintainable:

- **Flow direction**:
  - Widgets emit signals upward.
  - Dialogs validate input and call service or task helpers.
  - The service updates data and notifies the UI of changes.
  - The UI refreshes visible state from the source of truth.

- **Signal-based updates (preferred)**:
  - Use Qt signals to announce changes (`data_changed`, `request_refresh`, `selection_updated`, etc.).
  - Connect signals in the dialog or main UI shell (`ui/ui_app_qt.py`) rather than wiring widgets directly to each other.
  - Keep signal payloads small and specific (IDs, minimal state), then re-read full state via helpers.

- **Avoid direct cross-widget state**:
  - Do not have widgets mutate each other directly.
  - Route shared updates through the dialog or the main UI controller.

This keeps the UI aligned with the service layer and avoids brittle implicit dependencies.
