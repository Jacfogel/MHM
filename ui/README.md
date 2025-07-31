# UI Development Guide

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