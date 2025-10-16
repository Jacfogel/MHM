# MHM Testing Framework

> **Audience**: Developers and AI assistants working on MHM  
> **Purpose**: Comprehensive testing framework focused on real behavior, integration scenarios, and side effect verification  
> **Style**: Technical, comprehensive, actionable  
> **Status**: **ACTIVE** - Real behavior testing implemented, expanding coverage  
> **Last Updated**: 2025-09-28

> **See [README.md](../README.md) for complete navigation and project overview**  
> **See [DEVELOPMENT_WORKFLOW.md](../DEVELOPMENT_WORKFLOW.md) for safe development practices**  
> **See [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) for essential commands**  
> **See [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md) for comprehensive manual testing for non-automated scenarios**  
> **See [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md) for exception handling patterns**

## Quick Reference

### **Test Suite Hanging Prevention**
```python
# Qt components in tests require proper mocking to avoid hanging
# Mock-based approach provides same coverage without Qt initialization dependencies

# BAD: Direct Qt instantiation in tests
def test_ui_validation():
    manager = MHMManagerUI()  # HANGS - requires Qt app context

# GOOD: Mock-based testing
def test_ui_validation():
    class MockMHMManagerUI:
        def on_user_selected(self, user_id):
            if user_id is None or user_id == "":
                return None
            return user_id
    
    manager = MockMHMManagerUI()
    # Test validation logic without Qt dependencies
```

### **Analytics Test Patching**
```python
# Analytics tests must match backend function usage
# Test patching must target correct import paths and function names

# BAD: Patching wrong function
with patch('core.checkin_analytics.get_recent_checkins', return_value=mock_data):
    result = analytics.get_mood_trends('user', days=30)  # FAILS

# GOOD: Patching correct function  
with patch('core.checkin_analytics.get_checkins_by_days', return_value=mock_data):
    result = analytics.get_mood_trends('user', days=30)  # WORKS
```

### **Test Execution**
```powershell
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --verbose

# Run automation tests
python -m pytest tests/behavior/test_*automation* -v

# Run specific automation categories
python -m pytest tests/behavior/test_discord_automation_complete.py -v
python -m pytest tests/behavior/test_ui_automation_complete.py -v
python -m pytest tests/behavior/test_discord_advanced_automation.py -v
```

### **CRITICAL: Windows Task Prevention**
```powershell
# Check for Windows task pollution
schtasks /query /fo csv /nh | findstr "Wake_" | Measure-Object

# Clean up Windows tasks if needed
python scripts/cleanup_windows_tasks.py
```

### **Test Categories**
- **Unit Tests**: Individual function testing
- **Integration Tests**: Cross-module workflows
- **Behavior Tests**: Real system behavior verification
- **UI Tests**: User interface functionality
- **Automation Tests**: Comprehensive automated testing for UI and Discord scenarios

The testing framework prioritizes **real behavior testing**, **side effect verification**, and **integration scenarios** to ensure system reliability and catch issues early.

## Automation Coverage
✅ **UI Dialog Testing** - All 7 dialog types fully automated  
✅ **Discord Command Testing** - All 15 basic + 16 advanced scenarios automated  
✅ **Data Persistence Testing** - Save/load functionality automated  
✅ **Error Handling Testing** - Edge cases and recovery automated  

**Manual Testing Focus**: Visual verification, user experience, performance, and real-world integration testing.

## Testing Philosophy & Priorities

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

### **Test Data Cleanup Standards**
- **Pre-run**: Remove `tests/data/pytest-of-Julie`, clear `tests/data/tmp`, remove stray config files
- **Post-run**: Clear `tests/data/tmp` and `tests/data/flags`, remove test backups and logs
- **Users directory**: All test users must reside under `tests/data/users/<id>`, fail if found elsewhere

## Test Organization Structure

Tests are organized by real-world features and workflows to encourage integration testing and real behavior verification.

```
tests/
|-- conftest.py                          # Shared fixtures and configuration
|-- unit/                                # Unit tests by module (core logic)
|-- integration/                         # Integration tests by feature
|-- behavior/                            # Real behavior tests by system
`-- ui/                                  # UI-specific tests
```

### **Test Categories**
- **Unit Tests**: Individual function testing with mocked dependencies
- **Integration Tests**: Cross-module workflows and component interactions
- **Behavior Tests**: Real system behavior verification with side effects
- **UI Tests**: User interface functionality and dialog testing

## Test Utilities and Infrastructure

### **Critical Requirements**
- **Data Isolation**: All tests must use `tests/data/` directory only
- **Environment Isolation**: Use `monkeypatch.setenv()` for env vars, never `os.environ[...] = ...`
- **Mock External Systems**: Never create real Windows tasks or system resources
- **UI Testing**: Use headless mode, mock Qt applications
- **User Data Access**: Use `TestUserFactory` and centralized `get_user_data()` over custom scaffolding

### **CRITICAL: Windows Task Prevention Requirements**
**MANDATORY**: All tests that interact with scheduler functionality MUST prevent Windows task creation.

#### **Required Mocking Patterns**
```python
# CORRECT: Mock the scheduler method to prevent real Windows tasks
from unittest.mock import patch

def test_scheduler_functionality():
    with patch.object(scheduler_manager, 'set_wake_timer') as mock_wake_timer:
        # Test the functionality
        scheduler_manager.set_wake_timer(schedule_time, user_id, category, period)
        
        # Verify the method was called with correct parameters
        mock_wake_timer.assert_called_once_with(schedule_time, user_id, category, period)
```

#### **FORBIDDEN Patterns**
```python
# WRONG: Never call real scheduler methods in tests
def test_scheduler_functionality():
    # This creates real Windows tasks - FORBIDDEN
    scheduler_manager.set_wake_timer(schedule_time, user_id, category, period)
    
    # This also creates real Windows tasks - FORBIDDEN
    subprocess.run(['schtasks', '/create', ...])
```

#### **Verification Commands**
```powershell
# Check for Windows task pollution after test runs
schtasks /query /fo csv /nh | findstr "Wake_" | Measure-Object

# Clean up if tasks are found
python scripts/cleanup_windows_tasks.py
```

#### **Test Categories Requiring Special Attention**
- **Scheduler Tests**: `test_scheduler_*.py` - MUST mock `set_wake_timer`
- **Wake Timer Tests**: Any test with "wake" or "timer" in name
- **Real Behavior Tests**: Tests with "real_behavior" in name - MUST use proper mocking
- **Integration Tests**: Tests that exercise full scheduler workflows

#### **Enforcement Rules**
1. **Pre-Test Check**: Verify no Windows tasks exist before running tests
2. **Post-Test Check**: Verify no new Windows tasks were created
3. **Mock Verification**: All scheduler methods must be mocked in tests
4. **Cleanup Required**: Any test that creates Windows tasks must clean them up immediately
5. **Documentation**: All scheduler tests must document their mocking strategy

### **Key Fixtures**
- `force_test_data_directory` (session, autouse): routes all temp I/O to `tests/data`
- `env_guard_and_restore` (function, autouse): snapshots/restores critical env vars
- `path_sanitizer` (function, autouse): asserts temp directory stays within `tests/data`
- `test_path_factory` (function): creates per-test directory under `tests/data/tmp/<uuid>`
- `fix_user_data_loaders` (function, autouse): ensures centralized loaders are registered

### **Critical Testing Methodology**
**Always investigate the actual implementation first** - Read source code before writing tests
- **Understand real behavior** - Implementation may import functions dynamically with specific data structures
- **Test what actually exists** - Verify what's available in codebase, don't assume functions exist
- **Start with basic functionality** - Begin simple before attempting complex interaction tests
- **Verify imports and dependencies** - Check what modules and functions are actually imported

### **Centralized Test Utilities**
Comprehensive utilities in `tests/test_utilities.py`:

#### **Test User Factory**
```python
from tests.test_utilities import TestUserFactory

# Create different user types for testing
TestUserFactory.create_basic_user("user1")
TestUserFactory.create_discord_user("discord_user")
TestUserFactory.create_user_with_health_focus("health_user")
```

**Available User Types** (12 comprehensive types):
- **Basic Types**: `basic_user`, `minimal_user`, `full_featured_user`
- **Channel-Specific**: `discord_user`, `email_user`, `telegram_user`
- **Feature-Focused**: `health_focus`, `task_focus`, `disabilities`
- **Complex Configurations**: `complex_checkins`, `custom_fields`, `schedules`
- **Edge Cases**: `limited_data`, `inconsistent_data`

## Test Categories & Markers

### **Core Test Type Markers**
| Marker | Purpose | Usage |
|--------|---------|-------|
| `@pytest.mark.unit` | Fast, isolated function tests | Individual function testing |
| `@pytest.mark.integration` | Multi-module workflow tests | Component interaction testing |
| `@pytest.mark.behavior` | Real system behavior tests | Side effect verification |
| `@pytest.mark.ui` | UI component tests | Dialog and widget testing |

### **Performance & Resource Markers**
| Marker | Purpose | Usage |
|--------|---------|-------|
| `@pytest.mark.slow` | Slow-running tests | Tests taking >1 second |
| `@pytest.mark.performance` | Performance testing | Load and benchmark tests |
| `@pytest.mark.memory` | Memory-intensive tests | Large data operations |
| `@pytest.mark.network` | Network-dependent tests | API calls, external services |
| `@pytest.mark.external` | External service tests | Discord, email, Telegram |
| `@pytest.mark.file_io` | Heavy file operations | File creation, reading, writing |

### **Feature-Specific Markers**
| Marker | Purpose | Usage |
|--------|---------|-------|
| `@pytest.mark.tasks` | Task management tests | Task CRUD operations |
| `@pytest.mark.checkins` | Check-in system tests | Check-in functionality |
| `@pytest.mark.schedules` | Schedule management tests | Time period management |
| `@pytest.mark.messages` | Message system tests | Automated messaging |
| `@pytest.mark.analytics` | Analytics tests | Reporting and insights |
| `@pytest.mark.user_management` | User account tests | Account management |
| `@pytest.mark.channels` | Communication tests | Discord, email, Telegram |

## Quick Start

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

### **Order Independence**
```bash
# Install plugin once (in CI or locally)
pip install pytest-randomly

# Run with randomized order to enforce determinism
python -m pytest --randomly-seed=auto
```
The suite should remain green under randomized order. Import-order guards and one-time loader registration in `tests/conftest.py` support this.

## Test Commands

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

## Test Architecture

### **Fixtures**
The testing framework provides several shared fixtures in `conftest.py`:

- `test_data_dir` - Temporary test data directory
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

## Coverage Reports

When running tests with coverage, reports are generated in:

- **HTML Report**: `htmlcov/index.html` - Interactive coverage report
- **Terminal Report**: Shows missing lines in terminal output

### **Coverage Targets**
- **Core Modules**: `core/`, `communication/`, `ai/`, `tasks/`, `user/`
- **Target Coverage**: 80%+ for critical modules
- **Current Coverage**: 29% of codebase (9 out of 31+ modules)

## Writing Tests

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
        assert os.path.exists(os.path.join(user_dir, "checkins.json")), "Check-ins file should be created"
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

## Debugging Tests

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

## Test Priorities & Roadmap

### **Current Status**
- **1,481 tests passing** with 95% success rate
- **9 modules covered** (29% of codebase)
- **Real behavior testing** implemented for covered modules
- **Integration testing** framework established

### **High Priority (Next 1-2 weeks)**
1. **UI Layer Testing** - Add tests for all dialogs and widgets
2. **Discord Command Testing** - Complete automation for all Discord command scenarios
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

## Maintenance Guidelines

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