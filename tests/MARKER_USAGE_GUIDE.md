# Pytest Marker Usage Guide

> **Purpose**: Comprehensive guide for using pytest markers effectively in MHM testing  
> **Audience**: Developers and AI assistants working on MHM  
> **Status**: **ACTIVE** - Enhanced marker system implemented  
> **Last Updated**: 2025-08-05

## 🎯 **Overview**

This guide covers the enhanced pytest marker system for MHM testing. The markers are designed to provide clear categorization, enable selective test execution, and improve test organization and maintainability.

## 📋 **Available Markers**

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

### **Test Quality Markers**

| Marker | Purpose | Usage |
|--------|---------|-------|
| `@pytest.mark.flaky` | Occasionally failing tests | Needs investigation |
| `@pytest.mark.known_issue` | Known bug tests | Document limitations |
| `@pytest.mark.regression` | Regression prevention | Catch recurring bugs |
| `@pytest.mark.smoke` | Basic functionality tests | Quick validation |
| `@pytest.mark.critical` | Essential path tests | Must always pass |

### **Development Workflow Markers**

| Marker | Purpose | Usage |
|--------|---------|-------|
| `@pytest.mark.wip` | Work in progress | Still being developed |
| `@pytest.mark.todo` | Not yet implemented | Placeholder tests |
| `@pytest.mark.skip_ci` | Skip in CI/CD | Too slow or special setup |
| `@pytest.mark.manual` | Manual intervention | Requires human input |
| `@pytest.mark.debug` | Debug-specific | For troubleshooting |

## 🚀 **Usage Examples**

### **Basic Marker Usage**

```python
@pytest.mark.unit
def test_config_validation():
    """Unit test for configuration validation."""
    assert validate_config({"key": "value"}) == True

@pytest.mark.behavior
def test_user_creation_creates_files():
    """Behavior test verifying file creation."""
    user_id = "test-user"
    create_user(user_id, user_data)
    assert os.path.exists(f"data/users/{user_id}/account.json")

@pytest.mark.integration
def test_account_lifecycle():
    """Integration test for complete account workflow."""
    # Test creation, modification, and deletion
    pass
```

### **Combining Multiple Markers**

```python
@pytest.mark.behavior
@pytest.mark.tasks
@pytest.mark.critical
def test_critical_task_creation():
    """Critical behavior test for task creation."""
    # This test is critical, tests real behavior, and is task-related
    pass

@pytest.mark.integration
@pytest.mark.external
@pytest.mark.slow
def test_discord_integration():
    """Slow integration test with Discord."""
    # Tests Discord integration, is slow, and requires external service
    pass
```

### **Conditional Markers**

```python
@pytest.mark.skipif(
    os.getenv('SKIP_EXTERNAL_TESTS') == 'true',
    reason="External tests disabled"
)
@pytest.mark.external
def test_discord_connection():
    """External test that can be conditionally skipped."""
    pass

@pytest.mark.skipif(
    not os.path.exists('/path/to/required/file'),
    reason="Required file not found"
)
@pytest.mark.file_io
def test_file_operations():
    """File test that requires specific file."""
    pass
```

### **Class-Level Markers**

```python
@pytest.mark.tasks
class TestTaskManagement:
    """All task management tests grouped together."""
    
    @pytest.mark.unit
    def test_task_creation_unit(self):
        """Unit test for task creation."""
        pass
    
    @pytest.mark.behavior
    def test_task_creation_behavior(self):
        """Behavior test for task creation."""
        pass
    
    @pytest.mark.integration
    def test_task_workflow_integration(self):
        """Integration test for task workflow."""
        pass
```

### **Parametrized Tests with Markers**

```python
@pytest.mark.parametrize("channel", ["discord", "email", "telegram"])
@pytest.mark.channels
def test_channel_functionality(channel):
    """Test functionality across different channels."""
    assert channel in ["discord", "email", "telegram"]

@pytest.mark.parametrize("feature", ["tasks", "checkins", "messages"])
@pytest.mark.integration
def test_feature_integration(feature):
    """Test integration for different features."""
    assert feature in ["tasks", "checkins", "messages"]
```

## 🎯 **Test Execution Commands**

### **Running Tests by Marker**

```bash
# Run all unit tests (fastest)
python -m pytest -m unit

# Run all behavior tests
python -m pytest -m behavior

# Run all integration tests
python -m pytest -m integration

# Run all UI tests
python -m pytest -m ui

# Run all slow tests
python -m pytest -m slow

# Run all external service tests
python -m pytest -m external

# Run all critical tests
python -m pytest -m critical

# Run all smoke tests
python -m pytest -m smoke
```

### **Running Tests by Feature**

```bash
# Run all task-related tests
python -m pytest -m tasks

# Run all check-in tests
python -m pytest -m checkins

# Run all schedule tests
python -m pytest -m schedules

# Run all message tests
python -m pytest -m messages

# Run all analytics tests
python -m pytest -m analytics

# Run all user management tests
python -m pytest -m user_management

# Run all channel tests
python -m pytest -m channels
```

### **Combining Markers**

```bash
# Run critical behavior tests
python -m pytest -m "critical and behavior"

# Run external integration tests
python -m pytest -m "external and integration"

# Run slow UI tests
python -m pytest -m "slow and ui"

# Run task tests that are not slow
python -m pytest -m "tasks and not slow"

# Run all tests except slow ones
python -m pytest -m "not slow"

# Run all tests except external ones
python -m pytest -m "not external"
```

### **Using run_tests.py Script**

```bash
# Run unit tests only
python run_tests.py --mode unit

# Run behavior tests only
python run_tests.py --mode behavior

# Run integration tests only
python run_tests.py --mode integration

# Run UI tests only
python run_tests.py --mode ui

# Run all tests (excluding slow)
python run_tests.py

# Run all tests including slow
python run_tests.py --mode all
```

## 📊 **Test Organization Patterns**

### **By Feature (Recommended)**

```python
# tests/behavior/test_task_management.py
@pytest.mark.tasks
class TestTaskManagement:
    """Task management behavior tests."""
    
    @pytest.mark.behavior
    def test_task_creation_creates_files(self):
        """Test that task creation creates required files."""
        pass
    
    @pytest.mark.behavior
    def test_task_deletion_removes_files(self):
        """Test that task deletion removes files."""
        pass

# tests/integration/test_task_workflows.py
@pytest.mark.tasks
class TestTaskWorkflows:
    """Task workflow integration tests."""
    
    @pytest.mark.integration
    def test_complete_task_lifecycle(self):
        """Test complete task creation to completion workflow."""
        pass
```

### **By Test Type**

```python
# tests/unit/test_task_validation.py
@pytest.mark.tasks
class TestTaskValidation:
    """Task validation unit tests."""
    
    @pytest.mark.unit
    def test_task_title_validation(self):
        """Test task title validation logic."""
        pass

# tests/behavior/test_task_persistence.py
@pytest.mark.tasks
class TestTaskPersistence:
    """Task persistence behavior tests."""
    
    @pytest.mark.behavior
    def test_task_saves_to_file(self):
        """Test that tasks are saved to files."""
        pass
```

## 🔧 **Best Practices**

### **Marker Selection Guidelines**

1. **Always use core type markers**: Every test should have `unit`, `integration`, `behavior`, or `ui`
2. **Add feature markers**: Use feature-specific markers for better organization
3. **Use performance markers**: Mark slow, memory-intensive, or external tests
4. **Use quality markers**: Mark flaky, critical, or regression tests
5. **Use workflow markers**: Mark WIP, TODO, or CI-skipped tests

### **Marker Combinations**

```python
# Good: Clear categorization
@pytest.mark.behavior
@pytest.mark.tasks
@pytest.mark.critical
def test_critical_task_creation():
    pass

# Good: Performance awareness
@pytest.mark.integration
@pytest.mark.external
@pytest.mark.slow
def test_discord_integration():
    pass

# Good: Development workflow
@pytest.mark.wip
@pytest.mark.ui
def test_new_dialog_feature():
    pytest.skip("Work in progress")
```

### **Avoiding Marker Overuse**

```python
# Bad: Too many markers
@pytest.mark.unit
@pytest.mark.tasks
@pytest.mark.user_management
@pytest.mark.critical
@pytest.mark.smoke
@pytest.mark.regression
def test_task_creation():
    pass

# Good: Focused markers
@pytest.mark.behavior
@pytest.mark.tasks
@pytest.mark.critical
def test_task_creation():
    pass
```

## 🚨 **Common Patterns**

### **Real Behavior Testing**

```python
@pytest.mark.behavior
def test_user_creation_side_effects():
    """Test that user creation has the expected side effects."""
    user_id = "test-user"
    
    # Act
    create_user(user_id, user_data)
    
    # Assert - Verify side effects
    assert os.path.exists(f"data/users/{user_id}/account.json")
    assert os.path.exists(f"data/users/{user_id}/preferences.json")
    
    # Verify data persistence
    loaded_data = get_user_data(user_id)
    assert loaded_data["account"]["user_id"] == user_id
```

### **Integration Testing**

```python
@pytest.mark.integration
def test_feature_enablement_workflow():
    """Test complete feature enablement workflow."""
    user_id = "test-user"
    create_user(user_id, {"enabled_features": ["messages"]})
    
    # Test feature enablement
    enable_feature(user_id, "tasks")
    
    # Verify integration
    user_data = get_user_data(user_id)
    assert "tasks" in user_data["account"]["enabled_features"]
    
    # Test feature functionality
    create_task(user_id, {"title": "Test Task"})
    tasks = get_user_tasks(user_id)
    assert len(tasks) == 1
```

### **UI Testing**

```python
@pytest.mark.ui
def test_dialog_behavior():
    """Test dialog behavior without showing UI."""
    # Test dialog creation
    dialog = AccountCreatorDialog()
    assert dialog is not None
    
    # Test widget population
    assert dialog.username_field is not None
    assert dialog.email_field is not None
    
    # Test validation
    result = dialog.validate_input()
    assert result is False  # Should fail without input
```

## 📈 **Performance Optimization**

### **Selective Test Execution**

```bash
# Run only fast tests during development
python -m pytest -m "not slow and not external"

# Run only critical tests for quick validation
python -m pytest -m critical

# Run smoke tests for basic functionality
python -m pytest -m smoke

# Run all tests except flaky ones
python -m pytest -m "not flaky"
```

### **CI/CD Optimization**

```bash
# In CI pipeline: Skip slow and external tests
python -m pytest -m "not slow and not external and not skip_ci"

# In development: Run everything
python -m pytest

# In staging: Run with external tests
python -m pytest -m "not skip_ci"
```

## 🔍 **Debugging with Markers**

### **Running Specific Test Categories**

```bash
# Run only flaky tests to investigate
python -m pytest -m flaky -v

# Run only known issue tests
python -m pytest -m known_issue -v

# Run only debug tests
python -m pytest -m debug -v
```

### **Test Discovery**

```bash
# List all tests with their markers
python -m pytest --collect-only

# List tests by marker
python -m pytest --collect-only -m tasks

# Show test markers
python -m pytest --markers
```

## 📝 **Documentation**

### **Updating Test Documentation**

When adding new tests, update the relevant documentation:

1. **Test file docstring**: Describe the test category and purpose
2. **Class docstring**: Explain the test group focus
3. **Function docstring**: Describe the specific test scenario
4. **Markers**: Use appropriate markers for categorization

### **Example Documentation**

```python
"""
Task Management Behavior Tests

This module contains behavior tests for task management functionality.
Tests verify actual system behavior, side effects, and data persistence.
"""

@pytest.mark.tasks
class TestTaskCreation:
    """Task creation behavior tests."""
    
    @pytest.mark.behavior
    def test_task_creation_creates_files(self):
        """
        Test that creating a task creates the required files.
        
        This test verifies the side effect of task creation by checking
        that the task file is actually created in the user's data directory.
        """
        pass
```

## 🎯 **Summary**

The enhanced pytest marker system provides:

1. **Clear categorization** of tests by type, feature, and quality
2. **Selective execution** for faster development cycles
3. **Better organization** of test code and documentation
4. **Performance awareness** for test execution planning
5. **Development workflow** support for WIP and TODO items

Use these markers consistently to improve test maintainability and execution efficiency.
