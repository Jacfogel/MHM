# Missing Addresses Test Fixture

This fixture tests missing address (broken link) detection.

## Valid Links

This section has valid links:
- [Existing file](demo_module.py) - Should exist
- [Another existing file](demo_module2.py) - Should exist

## Broken Links

This section has broken links that should be detected:
- [Missing file](nonexistent_file.md) - Does not exist
- [Another missing file](core/missing_module.py) - Does not exist
- [Broken link](tests/missing_test.py) - Does not exist

## Mixed Links

This section has both valid and broken links:
- [Valid](demo_module.py) - Should exist
- [Broken](missing.py) - Should not exist

