# MHM Testing Framework

> **Purpose**: Comprehensive testing framework focused on real behavior, integration scenarios, and side effect verification  
> **Audience**: Developers and AI assistants working on MHM  
> **Status**: **ACTIVE** - Real behavior testing implemented, expanding coverage  
> **Last Updated**: 2025-07-16

This directory contains the comprehensive test suite for the Mental Health Management (MHM) system. The testing framework prioritizes **real behavior testing**, **side effect verification**, and **integration scenarios** to ensure system reliability and catch issues early.

## 🎯 **Testing Philosophy & Priorities**

### **Core Principles**
1. **Real Behavior Testing**: Tests verify actual system changes, not just return values
2. **Side Effect Verification**: Functions are verified to actually change system state
3. **Integration Scenarios**: Test real-world workflows that span multiple modules
4. **Data Persistence**: Verify that changes are actually saved and persist
5. **Error Recovery**: Test how the system handles and recovers from errors

### **Test Quality Standards**
- **Isolation**: Tests don't interfere with each other or real data
- **Completeness**: Tests verify the full workflow, not just individual steps
- **Maintainability**: Tests are easy to understand and update
- **Reliability**: Tests produce consistent, repeatable results

## 🏗️ **Test Organization Structure**

### **Primary Organization: By Feature/Workflow (Operational Grouping)**
Tests are organized by real-world features and workflows, not just individual modules. This encourages integration testing and real behavior verification.

```
tests/
├── conftest.py                           # Shared fixtures and configuration
├── README.md                            # This file
├── unit/                                # Unit tests by module (core logic)
│   ├── test_config.py                   # Configuration validation
│   ├── test_error_handling.py           # Error handling framework
│   ├── test_file_operations.py          # File I/O operations
│   └── test_validation.py               # Data validation functions
├── integration/                         # Integration tests by feature
│   ├── test_account_lifecycle.py        # Complete account creation/editing/deletion
│   ├── test_user_preferences.py         # User preference management workflows
│   ├── test_message_categories.py       # Message category management
│   ├── test_schedule_periods.py         # Schedule period management
│   ├── test_feature_enablement.py       # Feature enable/disable workflows
│   └── test_dialog_integration.py       # UI dialog workflows
├── behavior/                            # Real behavior tests by system
│   ├── test_service_behavior.py         # Service startup/shutdown/restart
│   ├── test_communication_behavior.py   # Message sending/receiving
│   ├── test_task_behavior.py            # Task creation/management
│   └── test_scheduler_behavior.py       # Scheduling and timing
└── ui/                                  # UI-specific tests
    ├── test_account_creation_ui.py      # Account creation dialog
    ├── test_dialog_functionality.py     # General dialog testing
    └── test_widget_integration.py       # Widget behavior and integration
```

### **Test Categories & Markers**

#### **Unit Tests** (`@pytest.mark.unit`)
- **Purpose**: Test individual functions and methods in isolation
- **Scope**: Single module, pure functions, core logic
- **Speed**: Fast execution
- **Examples**: Configuration validation, data validation, utility functions

#### **Integration Tests** (`@pytest.mark.integration`)
- **Purpose**: Test how components work together across modules
- **Scope**: Multi-module workflows, data flow between components
- **Speed**: Medium execution
- **Examples**: Account lifecycle, feature enablement, preference management

#### **Behavior Tests** (`@pytest.mark.behavior`)
- **Purpose**: Test actual system behavior and side effects
- **Scope**: Real file operations, service state changes, data persistence
- **Speed**: Medium to slow execution
- **Examples**: Service management, communication channels, task operations

#### **UI Tests** (`@pytest.mark.ui`)
- **Purpose**: Test user interface functionality and workflows
- **Scope**: Dialog interactions, widget behavior, UI state changes
- **Speed**: Slow execution (UI operations)
- **Examples**: Account creation dialog, preference dialogs, widget integration

#### **Slow Tests** (`@pytest.mark.slow`)
- **Purpose**: Tests that require significant time or resources
- **Scope**: Performance testing, large data operations, complex workflows
- **Speed**: Slow execution
- **Examples**: Large dataset operations, performance benchmarks

## 🚀 **Quick Start**

### **Install Testing Dependencies**
```bash
pip install -r requirements.txt
```

### **Run All Tests**
```bash
python run_tests.py
```

### **Run Specific Test Categories**
```bash
# Unit tests only (fastest)
python run_tests.py --type unit

# Integration tests only
python run_tests.py --type integration

# Behavior tests only
python run_tests.py --type behavior

# UI tests only
python run_tests.py --type ui

# Quick tests (excludes slow tests)
python run_tests.py --quick
```

### **Run with Coverage**
```bash
python run_tests.py --coverage
```

### **Run in Parallel**
```bash
python run_tests.py --parallel
```

## 📋 **Test Commands**

### **Basic Commands**
```bash
# Run all tests
python run_tests.py

# Run with verbose output
python run_tests.py --verbose

# Run specific test type
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --type behavior
python run_tests.py --type ui
python run_tests.py --type slow

# Run quick tests only
python run_tests.py --quick
```

### **Advanced Commands**
```bash
# Run with coverage report
python run_tests.py --coverage

# Run tests in parallel
python run_tests.py --parallel

# Combine options
python run_tests.py --type integration --verbose --coverage
```

### **Direct Pytest Commands**
```bash
# Run specific test file
python -m pytest tests/integration/test_account_lifecycle.py

# Run specific test function
python -m pytest tests/integration/test_account_lifecycle.py::TestAccountLifecycle::test_create_account_with_all_features

# Run tests matching pattern
python -m pytest -k "account"

# Run tests with specific marker
python -m pytest -m "integration"
```

## 🏗️ **Test Architecture**

### **Fixtures**
The testing framework provides several shared fixtures in `conftest.py`:

- `test_data_dir` - Temporary test data directory
- `test_custom_data_dir` - Temporary custom data directory
- `mock_user_data` - Mock user data for testing
- `mock_config` - Mock configuration for testing
- `mock_logger` - Mock logger for testing
- `temp_file` - Temporary file for testing
- `mock_ai_response` - Mock AI response data
- `mock_task_data` - Mock task data
- `mock_message_data` - Mock message data

### **Real Behavior Testing Patterns**

#### **File Operation Verification**
```python
def test_create_user_creates_files(test_data_dir):
    """Test that creating a user actually creates the required files."""
    # Arrange
    user_id = "test-user"
    
    # Act
    create_user(user_id, user_data)
    
    # Assert - Verify actual file creation
    user_dir = os.path.join(test_data_dir, "users", user_id)
    assert os.path.exists(user_dir), "User directory should be created"
    assert os.path.exists(os.path.join(user_dir, "account.json")), "Account file should be created"
    assert os.path.exists(os.path.join(user_dir, "preferences.json")), "Preferences file should be created"
```

#### **Data Persistence Verification**
```python
def test_update_preferences_persists_changes(test_data_dir):
    """Test that preference updates are actually saved to disk."""
    # Arrange
    user_id = "test-user"
    create_user(user_id, initial_data)
    
    # Act
    new_preferences = {"timezone": "America/Los_Angeles"}
    update_user_preferences(user_id, new_preferences)
    
    # Assert - Verify actual data persistence
    loaded_data = get_user_data(user_id)
    assert loaded_data["preferences"]["timezone"] == "America/Los_Angeles", "Changes should persist"
```

#### **Integration Scenario Testing**
```python
def test_account_lifecycle_complete_workflow(test_data_dir):
    """Test complete account lifecycle: create, modify, disable, re-enable, delete."""
    # Arrange
    user_id = "test-user"
    
    # Act & Assert - Complete workflow
    # 1. Create account
    create_user(user_id, account_data)
    assert user_exists(user_id), "User should be created"
    
    # 2. Enable features
    enable_features(user_id, ["tasks", "checkins"])
    user_data = get_user_data(user_id)
    assert "tasks" in user_data["account"]["enabled_features"], "Tasks should be enabled"
    
    # 3. Disable features
    disable_features(user_id, ["tasks"])
    user_data = get_user_data(user_id)
    assert "tasks" not in user_data["account"]["enabled_features"], "Tasks should be disabled"
    
    # 4. Re-enable features
    enable_features(user_id, ["tasks"])
    user_data = get_user_data(user_id)
    assert "tasks" in user_data["account"]["enabled_features"], "Tasks should be re-enabled"
    
    # 5. Delete account
    delete_user(user_id)
    assert not user_exists(user_id), "User should be deleted"
```

## 📊 **Coverage Reports**

When running tests with coverage, reports are generated in:

- **HTML Report**: `htmlcov/index.html` - Interactive coverage report
- **Terminal Report**: Shows missing lines in terminal output

### **Coverage Targets**
- **Core Modules**: `core/`, `bot/`, `tasks/`, `user/`
- **Target Coverage**: 80%+ for critical modules
- **Current Coverage**: 29% of codebase (9 out of 31+ modules)

## 🔧 **Writing Tests**

### **Test Naming Convention**
- Test files: `test_<feature_or_module>.py`
- Test classes: `Test<FeatureName>`
- Test methods: `test_<scenario>_<expected_behavior>`

### **Example Test Structure**
```python
import pytest
import os
import json
from unittest.mock import patch, Mock

class TestAccountLifecycle:
    """Test complete account lifecycle workflows."""
    
    @pytest.mark.integration
    def test_create_account_with_all_features(self, test_data_dir):
        """Test creating an account with all features enabled."""
        # Arrange
        user_id = "test-user"
        account_data = {
            "internal_username": user_id,
            "enabled_features": ["messages", "tasks", "checkins"]
        }
        
        # Act
        create_user(user_id, account_data)
        
        # Assert - Verify actual system changes
        user_dir = os.path.join(test_data_dir, "users", user_id)
        assert os.path.exists(user_dir), "User directory should be created"
        
        # Verify account file
        account_file = os.path.join(user_dir, "account.json")
        assert os.path.exists(account_file), "Account file should be created"
        
        with open(account_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data["enabled_features"] == ["messages", "tasks", "checkins"], "Features should be saved"
        
        # Verify feature-specific files
        assert os.path.exists(os.path.join(user_dir, "tasks")), "Tasks directory should be created"
        assert os.path.exists(os.path.join(user_dir, "daily_checkins.json")), "Check-ins file should be created"
    
    @pytest.mark.behavior
    def test_enable_checkins_creates_files(self, test_data_dir):
        """Test that enabling check-ins creates the required files."""
        # Arrange
        user_id = "test-user"
        create_user(user_id, {"enabled_features": ["messages"]})
        
        # Act
        enable_feature(user_id, "checkins")
        
        # Assert - Verify side effects
        checkins_file = os.path.join(test_data_dir, "users", user_id, "daily_checkins.json")
        assert os.path.exists(checkins_file), "Check-ins file should be created"
        
        user_data = get_user_data(user_id)
        assert "checkins" in user_data["account"]["enabled_features"], "Check-ins should be enabled"
```

### **Test Markers**
Use appropriate markers for test categorization:

```python
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # Component interaction tests
@pytest.mark.behavior      # Real behavior and side effect tests
@pytest.mark.ui            # UI functionality tests
@pytest.mark.slow          # Performance or large data tests
```

### **Best Practices**
1. **Test Real Behavior**: Verify actual system changes, not just return values
2. **Verify Side Effects**: Ensure functions actually change system state
3. **Use Descriptive Names**: Test names should clearly describe the scenario and expected behavior
4. **Arrange-Act-Assert**: Structure tests with clear sections
5. **Use Fixtures**: Leverage shared fixtures for common test data
6. **Test Integration**: Focus on workflows that span multiple modules
7. **Verify Data Persistence**: Ensure changes are actually saved and persist
8. **Test Error Recovery**: Include tests for error conditions and recovery

## 🐛 **Debugging Tests**

### **Running Single Tests**
```bash
# Run specific test with verbose output
python -m pytest tests/integration/test_account_lifecycle.py::TestAccountLifecycle::test_create_account_with_all_features -v

# Run with print statements visible
python -m pytest tests/integration/test_account_lifecycle.py -s

# Run with full traceback
python -m pytest tests/integration/test_account_lifecycle.py --tb=long
```

### **Debugging with PDB**
```python
import pdb

def test_debug_example():
    result = some_function()
    pdb.set_trace()  # Debugger will stop here
    assert result == expected
```

### **Common Issues**
1. **Import Errors**: Ensure project root is in Python path
2. **Fixture Errors**: Check fixture dependencies and scope
3. **Path Issues**: Use `test_data_dir` fixture for file operations
4. **Data Isolation**: Ensure tests don't interfere with each other

## 📈 **Continuous Integration**

The testing framework is designed to work with CI/CD pipelines:

### **GitHub Actions Example**
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py --coverage
```

## 🎯 **Test Priorities & Roadmap**

### **Current Status**
- **205 tests passing** with 95% success rate
- **9 modules covered** (29% of codebase)
- **Real behavior testing** implemented for covered modules
- **Integration testing** framework established

### **High Priority (Next 1-2 weeks)**
1. **UI Layer Testing** - Add tests for all dialogs and widgets
2. **Bot/Communication Testing** - Test Discord, Telegram, Email bots
3. **Core Services Testing** - Test message management, schedule management
4. **Integration Scenarios** - Complete account lifecycle, feature enablement workflows

### **Medium Priority (Next month)**
1. **Performance Testing** - Load testing, stress testing
2. **Error Recovery Testing** - Comprehensive error scenario coverage
3. **Cross-Platform Testing** - Test on different platforms
4. **Advanced Integration** - Complex multi-user scenarios

### **Long-term Goals**
1. **80%+ Coverage** - Comprehensive coverage of all modules
2. **Automated Testing** - CI/CD integration
3. **Performance Monitoring** - Automated performance regression testing
4. **User Acceptance Testing** - End-to-end user workflow testing

## 📝 **Maintenance Guidelines**

### **When Adding New Features**
1. **Write tests first** - Test-driven development approach
2. **Include integration tests** - Test the complete workflow
3. **Verify real behavior** - Ensure tests verify actual system changes
4. **Update this README** - Document new test patterns and requirements

### **When Modifying Existing Features**
1. **Update existing tests** - Ensure tests reflect new behavior
2. **Add new test cases** - Cover new scenarios and edge cases
3. **Verify test isolation** - Ensure changes don't break other tests
4. **Run full test suite** - Verify nothing else is broken

### **When Refactoring Code**
1. **Keep tests working** - Tests should help catch regressions
2. **Update test organization** - Move tests to appropriate categories
3. **Simplify test logic** - Remove unnecessary complexity
4. **Document changes** - Update test documentation

---

**Remember**: The goal is to have confidence that changes work correctly and don't break existing functionality. Real behavior testing and integration scenarios are key to achieving this goal. 