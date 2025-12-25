# False Negative Test Documentation

This document contains known issues that path drift analysis should detect:

## Broken References

This document references files that don't exist:
- `core/nonexistent_module.py` - This file doesn't exist
- `ui/missing_dialog.py` - This file doesn't exist
- `tests/fake_test_file.py` - This file doesn't exist

## Valid References

These references are valid (files exist in the demo project):
- `demo_module.py` - This file exists
- `demo_module2.py` - This file exists

## Code References

Inline code references:
- `core.service` - May or may not exist
- `development_tools.shared.common` - Should exist

