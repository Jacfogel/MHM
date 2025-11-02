# AI Testing Guide - Quick Reference

> **Purpose**: Fast testing patterns and troubleshooting for AI collaborators  
> **Style**: Concise, pattern-focused, actionable  
> **For details**: See [tests/TESTING_GUIDE.md](../tests/TESTING_GUIDE.md)

## Quick Reference

### **Test Execution Commands**
```powershell
# Run all tests
python run_tests.py

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/behavior/ -v
python -m pytest tests/ui/ -v

# Run AI functionality tests (manual review tests)
python tests/ai/run_ai_functionality_tests.py
```

### **Test Categories (Priority Order)**
1. **Unit Tests** - Individual function testing
2. **Integration Tests** - Component interaction testing
3. **Behavior Tests** - End-to-end user scenarios
4. **UI Tests** - Interface and dialog testing
5. **AI Functionality Tests** - Manual review tests for AI response quality

## Common Testing Patterns

### **Qt Test Hanging**
```python
# BAD: MHMManagerUI()  # HANGS
# GOOD: MockMHMManagerUI()  # Mock instead
```

### **Analytics Patching**
```python
# BAD: patch('get_recent_checkins')
# GOOD: patch('get_checkins_by_days')
```

### **Test Failure Investigation**
1. **Read the error message** - Look for specific failure details
2. **Check test data** - Verify test fixtures and setup
3. **Check dependencies** - Ensure all required modules are available
4. **Check environment** - Verify configuration and permissions

### **Test Data Management**
```python
# Use test data directories only
test_data_dir = "tests/data/"
user_data_dir = "tests/data/users/"

# Clean up after tests
def cleanup_test_data():
    # Remove test artifacts
    pass
```

### **CRITICAL: Windows Task Prevention**
**MANDATORY**: Mock all scheduler methods to prevent real Windows task creation.

```python
# CORRECT: Mock scheduler methods
from unittest.mock import patch

def test_scheduler_functionality():
    with patch.object(scheduler_manager, 'set_wake_timer') as mock_wake_timer:
        scheduler_manager.set_wake_timer(schedule_time, user_id, category, period)
        mock_wake_timer.assert_called_once_with(schedule_time, user_id, category, period)
```

```powershell
# Check for task pollution
schtasks /query /fo csv /nh | findstr "Wake_" | Measure-Object
```

### **Discord Command Testing**
```python
# Test profile display formatting
python -m pytest tests/behavior/test_profile_display_formatting.py -v

# Test command discovery help system
python -m pytest tests/behavior/test_command_discovery_help.py -v

# Complete Discord automation (replaces manual testing)
python -m pytest tests/behavior/test_discord_automation_complete.py -v

# Run all Discord tests together
python -m pytest tests/behavior/test_*discord* -v

# Manual Discord testing (when automation isn't sufficient)
# See tests/MANUAL_DISCORD_TESTING_GUIDE.md for comprehensive testing checklist
```

### **Test Categories**

#### **Unit Tests** (`tests/unit/`)
- Test individual functions and methods
- Mock external dependencies
- Focus on logic and edge cases

#### **Integration Tests** (`tests/integration/`)
- Test component interactions
- Use real data handlers
- Test communication flows

#### **Behavior Tests** (`tests/behavior/`)
- Test complete user scenarios
- End-to-end functionality
- Real user data interactions
- **Discord Commands**: Profile display formatting and command discovery testing

#### **UI Tests** (`tests/ui/`)
- Test PySide6 dialogs and widgets
- User interaction scenarios
- Visual and functional testing

#### **AI Functionality Tests** (`tests/ai/`)
- Manual review tests for AI response quality
- Automatic validation for meta-text, code fragments, and quality issues
- Performance metrics and edge case testing
- Results written to `tests/ai/results/ai_functionality_test_results_latest.md`
- Logs consolidated to `tests/logs/test_consolidated.log` and `test_run.log`

## Troubleshooting Patterns

### **If Tests Fail to Start**
1. Check Python environment and dependencies
2. Verify test data directories exist
3. Check for import errors in test files

### **If Tests Are Flaky**
1. Check for timing issues in async tests
2. Verify test data isolation
3. Look for external dependencies

### **If UI Tests Fail**
1. Check PySide6 installation
2. Verify display environment (if headless)
3. Check for dialog state issues

## Test Data Patterns

### **User Data Testing**
```python
# Use test user data
test_user_id = "test_user_001"
user_data_path = f"tests/data/users/{test_user_id}/"

# Clean up test data
def cleanup_user_data(user_id):
    # Remove test user data
    pass
```

### **Configuration Testing**
```python
# Use test configuration
test_config = {
    "DISCORD_BOT_TOKEN": "test_token",
    "AI_MODEL": "test_model"
}
```

## Manual Testing Procedures

### **Pre-Test Checklist**
- [ ] Run `python run_headless_service.py start` to ensure system starts (for AI collaborators)
- [ ] Have test user ready (or create one)
- [ ] Check test data directories exist
- [ ] Verify environment variables

### **UI Testing Checklist**
- [ ] Test dialog creation and display
- [ ] Test user input validation
- [ ] Test data persistence
- [ ] Test error handling and recovery

## Test Coverage Patterns

### **Coverage Commands**
```powershell
# Run with coverage
python -m pytest --cov=core --cov=ui --cov=communication

# Generate coverage report
python -m pytest --cov=core --cov-report=html
```

### **Coverage Priorities**
1. **Core modules** - `core/` directory
2. **Communication** - `communication/` directory
3. **UI components** - `ui/` directory
4. **Data handlers** - User data management

## Discord Test Automation

```powershell
# Complete Discord automation (replaces manual testing)
python -m pytest tests/behavior/test_discord_automation_complete.py -v

# Advanced Discord automation (performance, integration, security)
python -m pytest tests/behavior/test_discord_advanced_automation.py -v
```

**Status**: [CHECKMARK] **Profile/Help** automated, [WARNING] **Task/Flow/Error** need real implementation

## UI Test Automation

```powershell
# Complete UI automation (replaces manual testing)
python -m pytest tests/behavior/test_ui_automation_complete.py -v
```

**Status**: [WARNING] **All UI dialogs** need real implementation

## Best Practices

### **Test Real Behavior**
1. **Verify Actual System Changes**: Test that functions actually modify system state, not just return values
2. **Check Side Effects**: Ensure data is saved, files are created, state is updated
3. **Test Integration**: Focus on workflows that span multiple modules
4. **Verify Data Persistence**: Ensure changes are actually saved and persist

### **Test Structure**
1. **Use Descriptive Names**: Test names should clearly describe scenario and expected behavior
2. **Arrange-Act-Assert**: Structure tests with clear sections for setup, execution, verification
3. **Use Fixtures**: Leverage shared fixtures for common test data and setup
4. **Test Error Recovery**: Include tests for error conditions and recovery

### **Example Pattern**
```python
def test_user_profile_saves_correctly(self, test_data_dir):
    """Test: User profile changes are saved and persist."""
    # Arrange: Create user and load initial profile
    user_id = "test_user_profile_save"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    
    # Act: Update profile and save
    profile_handler = ProfileHandler()
    # ... perform profile update ...
    
    # Assert: Verify actual system changes
    assert profile_data_was_saved_to_disk(user_id)
    assert profile_changes_persist_after_reload(user_id)
```

## Resources
- **Full Guide**: `tests/TESTING_GUIDE.md` - Complete testing framework documentation
- **AI Functionality Tests**: `tests/AI_FUNCTIONALITY_TEST_PLAN.md` - AI functionality test plan and results
- **Manual Testing**: `tests/MANUAL_TESTING_GUIDE.md` - UI testing procedures
- **Discord Testing**: `tests/MANUAL_DISCORD_TESTING_GUIDE.md` - Discord command testing procedures
- **Discord Automation**: `tests/behavior/test_discord_automation_complete.py` - Automated Discord testing
- **Error Handling**: `core/ERROR_HANDLING_GUIDE.md` - Exception handling patterns
- **Development Workflow**: `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md` - Testing in development process
