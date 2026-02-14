# Exclusion Rules Documentation

> **File**: `development_tools/shared/EXCLUSION_RULES.md`  
> **Audience**: AI collaborators and developers  
> **Purpose**: Document standardized exclusion rules used across all analysis tools  
> **Last Generated**: 2025-12-24

## Overview

This document describes the exclusion rules used by development tools to filter out files, functions, and code that should not be included in analysis. These rules ensure consistent behavior across all analysis tools and prevent false positives.

## File-Level Exclusions

File-level exclusions are handled by `standard_exclusions.py` and use the `should_exclude_file()` function.

### Universal Exclusions

These patterns apply to all tools and contexts:

- Python cache and compiled files: `__pycache__`, `*.pyc`, `*.pyo`, `*.pyi`
- Virtual environments: `venv`, `.venv`, `env`, `.env`, `node_modules`
- Git and version control: `.git`, `.gitignore`, `.gitattributes`
- IDE and editor files: `.vscode`, `.idea`, `*.swp`, `*.swo`, `*~`, `.cursorignore`
- OS generated files: `.DS_Store`, `Thumbs.db`, `desktop.ini`
- Archive and backup directories: `archive`, `backup*`, `backups`
- Scripts directory: `scripts`, `scripts/*`, `*/scripts/*`
- Build metadata and caches: `.ruff_cache`, `mhm.egg-info`
- Test artifacts: `.pytest_cache`, `tests/__pycache__`, `tests/.pytest_cache`, `tests/logs/`, `tests/data/`, `tests/temp/`, `tests/fixtures/`, `tests/ai/results`, `tests/coverage_html`
- Generated files: `*/generated/*`, `*/ui/generated/*`, `*/pyscript*`, `*/shibokensupport/*`, `*/signature_bootstrap.py`

`tests/data/` is treated as excluded-by-default for analyzer-style tooling to keep development tools isolated from mutable test artifacts unless a tool is explicitly designed to inspect that directory.

### Context-Specific Exclusions

#### Production Context
Excludes development and test files:
- `development_tools/*`, `*/development_tools/*`
- `tests/*`, `*/tests/*`, `*/test_*`
- `scripts/*`, `*/scripts/*`
- `archive/*`, `*/archive/*`

#### Development Context
Excludes sensitive data:
- `*/data/*`
- `*/logs/*`
- `*/backup*`, `*/backups/*`

#### Testing Context
Excludes generated files and data:
- `*/generated/*`, `*/ui/generated/*`
- `*/data/*`, `*/logs/*`
- `*/backup*`, `*/backups/*`

## Function-Level Exclusions

Function-level exclusions are handled by `exclusion_utilities.py` and provide utilities for identifying functions that should be excluded from specific analyses.

### Auto-Generated Code

Functions are excluded if they match auto-generated code patterns:

**File Patterns:**
- Files in `generated/` directories
- Files ending with `_pyqt.py`, `_ui.py`, `_generated.py`, `_auto.py`
- Files containing `generated` and `_pyqt.py` in path

**Function Patterns:**
- Function names: `setupUi`, `retranslateUi`, `setup_ui`, `retranslate_ui`
- Function names containing: `setup_ui_`, `retranslate_ui_`, `_generated_`, `_auto_`

**Rationale:** Auto-generated code (especially PyQt UI files) should not be included in complexity or documentation analysis as it's machine-generated and not maintainable by developers.

### Special Python Methods

Special Python methods (magic methods) are excluded from undocumented function counts:

**Excluded Methods:**
- `__new__`, `__post_init__`, `__repr__`, `__str__`, `__hash__`, `__eq__`
- Comparison methods: `__lt__`, `__le__`, `__gt__`, `__ge__`
- `__len__`, `__bool__`, `__call__`
- Item access: `__getitem__`, `__setitem__`, `__delitem__`
- Iteration: `__iter__`, `__next__`, `__contains__`
- Arithmetic: `__add__`, `__sub__`, `__mul__`, `__truediv__`, and reverse/in-place variants
- Simple `__init__` methods (complexity < 20)

**Not Excluded (should be documented):**
- Context managers: `__enter__`, `__exit__`

**Rationale:** Special methods have well-defined behavior in Python and typically don't need documentation. However, context managers define custom behavior and should be documented.

### Test Functions

Test functions are identified by:

**Function Name Patterns:**
- Function names starting with `test_` or containing `test` keyword (configurable via `test_keywords` in config)

**File Path Patterns:**
- Files with `test_` in name
- Files in `tests/` directory (Unix or Windows path separators)

**Rationale:** Test functions should be tracked separately from production code and excluded from complexity and documentation metrics.

## Tool-Specific Exclusions

Some tools have additional exclusion logic specific to their analysis:

### Error Handling Analysis

Additional exclusions for error handling analysis:
- Pydantic validators (`@field_validator`, `@model_validator`)
- Functions with exclusion comments (`# ERROR_HANDLING_EXCLUDE`)
- Logger methods (`debug`, `info`, `warning`, `error`, `critical`)
- File auditor logging methods
- Error handling infrastructure functions (`handle_errors`, `handle_error`, etc.)
- Private methods (`_log_error`, `_show_user_error`)
- Nested decorator functions
- Simple constructors (just `super().__init__()` and 1-2 assignments)

### Path Drift Analysis

Additional exclusions for path drift analysis:
- Test fixture files (detected via `_should_skip_path_drift_check()`)
- Example contexts (detected via `_is_in_example_context()`)
- Archive references

## Configuration

Exclusion patterns can be customized via `development_tools_config.json`:

```json
{
  "exclusions": {
    "base_exclusions": [...],
    "tool_exclusions": {
      "coverage": [...],
      "analysis": [...],
      "documentation": [...]
    },
    "context_exclusions": {
      "production": [...],
      "development": [...],
      "testing": [...]
    },
    "generated_files": [...],
    "test_keywords": ["test_", "test"]
  }
}
```

## Coverage Artifact Locations

Coverage tooling uses dedicated paths under `development_tools/tests/` to avoid mixing runtime artifacts with project root files:

- Main app coverage data file: `development_tools/tests/.coverage`
- Dev-tools coverage data file: `development_tools/tests/.coverage_dev_tools`
- Main app coverage JSON: `development_tools/tests/jsons/coverage.json`
- Dev-tools coverage JSON: `development_tools/tests/jsons/coverage_dev_tools.json`
- HTML coverage output: `development_tools/tests/coverage_html/`

Transient shard files such as `.coverage_parallel.*` and `.coverage_dev_tools.*` can appear during parallel/worker execution and are expected to be cleaned up after report generation.

## Usage

### File Exclusions

```python
from development_tools.shared.standard_exclusions import should_exclude_file

if should_exclude_file(file_path, tool_type='analysis', context='production'):
    # Skip this file
```

### Function Exclusions

```python
from development_tools.shared.exclusion_utilities import (
    is_generated_file,
    is_generated_function,
    is_special_python_method,
    is_test_function
)

if is_generated_file(file_path):
    # Skip this file

if is_generated_function(func_name):
    # Skip this function

if is_special_python_method(func_name, complexity):
    # Exclude from undocumented count

if is_test_function(func_name, file_path):
    # Exclude from complexity metrics
```

## Testing

Exclusion logic is tested in:
- `tests/development_tools/test_exclusion_utilities.py` (function-level exclusions)
- `tests/development_tools/test_standard_exclusions.py` (file-level exclusions)

## Maintenance

When adding new exclusion patterns:

1. **File-level exclusions**: Add to `standard_exclusions.py` (universal, tool-specific, or context-specific)
2. **Function-level exclusions**: Add to `exclusion_utilities.py` (auto-generated, special methods, test functions)
3. **Tool-specific exclusions**: Add to the specific tool's exclusion logic (document in tool's docstring)
4. **Update this document**: Document the new exclusion pattern and rationale
5. **Add tests**: Create test cases to verify the exclusion works correctly

## Rationale Summary

Exclusions serve several purposes:

1. **Reduce false positives**: Exclude code that shouldn't be analyzed (auto-generated, test fixtures)
2. **Improve accuracy**: Focus analysis on maintainable, production code
3. **Consistency**: Ensure all tools use the same exclusion rules
4. **Performance**: Skip files/functions that don't need analysis
5. **Clarity**: Separate concerns (tests vs production, generated vs hand-written)

