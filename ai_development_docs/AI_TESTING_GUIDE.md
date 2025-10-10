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
```

### **Test Categories (Priority Order)**
1. **Unit Tests** - Individual function testing
2. **Integration Tests** - Component interaction testing
3. **Behavior Tests** - End-to-end user scenarios
4. **UI Tests** - Interface and dialog testing

## Common Testing Patterns

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

### **Discord Command Testing**
```python
# Test profile display formatting
python -m pytest tests/behavior/test_profile_display_formatting.py -v

# Test command discovery help system
python -m pytest tests/behavior/test_command_discovery_help.py -v

# Manual Discord testing
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

## Resources
- **Full Guide**: `tests/TESTING_GUIDE.md` - Complete testing framework documentation
- **Manual Testing**: `tests/MANUAL_TESTING_GUIDE.md` - UI testing procedures
- **Discord Testing**: `tests/MANUAL_DISCORD_TESTING_GUIDE.md` - Discord command testing procedures
- **Error Handling**: `core/ERROR_HANDLING_GUIDE.md` - Exception handling patterns
- **Development Workflow**: `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md` - Testing in development process
