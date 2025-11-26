# Development Tools Demo Project

> **File**: `tests/fixtures/development_tools_demo/README.md`
> **Audience**: Developers and AI assistants working on development tools tests
> **Purpose**: Document the synthetic fixture project used for testing development tools
> **Style**: Technical, concise

This is a synthetic fixture project for testing development tools.

## 1. Purpose

This project provides:
- Demo modules with various function types
- Paired documentation files (some synced, some mismatched)
- Legacy code patterns for cleanup testing
- Test files for coverage runs

## 2. Structure

- `demo_module.py` - Main demo module with functions and classes
- `demo_module2.py` - Second module that imports from demo_module
- `demo_tests.py` - Test file for coverage runs
- `legacy_code.py` - Contains legacy patterns
- `docs/` - Documentation files for testing doc sync

## 3. Expected Test Outcomes

- Function registry should find all functions in demo_module.py
- Module dependencies should detect imports between modules
- Documentation sync should detect mismatched H2 headings
- Legacy cleanup should find legacy markers and patterns
- Coverage should generate metrics for demo_tests.py

