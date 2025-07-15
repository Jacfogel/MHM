# MHM Testing Framework

This directory contains the comprehensive test suite for the Mental Health Management (MHM) system. The testing framework is designed to ensure reliability, catch bugs early, and provide confidence when making changes.

## 🧪 **Test Structure**

### **Test Categories**
- **Unit Tests** (`@pytest.mark.unit`): Test individual functions and methods in isolation
- **Integration Tests** (`@pytest.mark.integration`): Test how components work together
- **Slow Tests** (`@pytest.mark.slow`): Tests that take longer to run (performance, large data)
- **AI Tests** (`@pytest.mark.ai`): Tests that require AI functionality

### **Test Files**
- `conftest.py` - Pytest configuration and shared fixtures
- `test_config.py` - Configuration validation tests
- `test_user_management.py` - User management functionality tests
- `test_file_operations.py` - File I/O operations tests
- `test_error_handling.py` - Error handling and recovery tests

## 🚀 **Quick Start**

### **Install Testing Dependencies**
```bash
pip install -r requirements.txt
```

### **Run All Tests**
```bash
python run_tests.py
```

### **Run Specific Test Types**
```bash
# Unit tests only (fastest)
python run_tests.py --type unit

# Integration tests only
python run_tests.py --type integration

# Quick tests (excludes slow and AI tests)
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
python run_tests.py --type slow
python run_tests.py --type ai

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
python run_tests.py --type unit --verbose --coverage
```

### **Direct Pytest Commands**
```bash
# Run specific test file
python -m pytest tests/test_config.py

# Run specific test function
python -m pytest tests/test_config.py::TestConfigValidation::test_validate_core_paths_success

# Run tests matching pattern
python -m pytest -k "config"

# Run tests with specific marker
python -m pytest -m "unit"
```

## 🏗️ **Test Architecture**

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

### **Test Organization**
Tests are organized by module and functionality:

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_config.py           # Configuration validation tests
├── test_user_management.py  # User management tests
├── test_file_operations.py  # File operations tests
├── test_error_handling.py   # Error handling tests
└── README.md               # This file
```

## 📊 **Coverage Reports**

When running tests with coverage, reports are generated in:

- **HTML Report**: `htmlcov/index.html` - Interactive coverage report
- **Terminal Report**: Shows missing lines in terminal output

### **Coverage Targets**
- **Core Modules**: `core/`, `bot/`, `tasks/`, `user/`
- **Target Coverage**: 80%+ for critical modules

## 🔧 **Writing Tests**

### **Test Naming Convention**
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<function_name>_<scenario>`

### **Example Test Structure**
```python
import pytest
from unittest.mock import patch, Mock

class TestExampleModule:
    """Test example module functionality."""
    
    @pytest.mark.unit
    def test_function_success(self, mock_data):
        """Test successful function execution."""
        result = example_function(mock_data)
        assert result == expected_value
    
    @pytest.mark.unit
    def test_function_error(self, mock_logger):
        """Test function error handling."""
        with patch('module.dependency') as mock_dep:
            mock_dep.side_effect = ValueError("Test error")
            result = example_function(data)
            assert result is None
            mock_logger.error.assert_called_once()
    
    @pytest.mark.integration
    def test_function_integration(self, test_data_dir):
        """Test function integration with other components."""
        # Integration test logic
        pass
```

### **Test Markers**
Use appropriate markers for test categorization:

```python
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # Component interaction tests
@pytest.mark.slow          # Performance or large data tests
@pytest.mark.ai            # AI functionality tests
```

### **Best Practices**
1. **Test One Thing**: Each test should verify one specific behavior
2. **Use Descriptive Names**: Test names should clearly describe what's being tested
3. **Arrange-Act-Assert**: Structure tests with clear sections
4. **Use Fixtures**: Leverage shared fixtures for common test data
5. **Mock External Dependencies**: Don't rely on external services in unit tests
6. **Test Edge Cases**: Include tests for error conditions and edge cases

## 🐛 **Debugging Tests**

### **Running Single Tests**
```bash
# Run specific test with verbose output
python -m pytest tests/test_config.py::TestConfigValidation::test_validate_core_paths_success -v

# Run with print statements visible
python -m pytest tests/test_config.py -s

# Run with full traceback
python -m pytest tests/test_config.py --tb=long
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
3. **Mock Issues**: Verify mock setup and assertions
4. **Path Issues**: Use `test_data_dir` fixture for file operations

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

## 🎯 **Test Priorities**

### **High Priority (Run Frequently)**
- Unit tests for core functions
- Configuration validation tests
- Error handling tests

### **Medium Priority (Run Before Releases)**
- Integration tests
- File operations tests
- User management tests

### **Low Priority (Run Occasionally)**
- Slow performance tests
- AI functionality tests
- Large data handling tests

## 📝 **Adding New Tests**

### **For New Modules**
1. Create `test_<module_name>.py`
2. Import the module and its functions
3. Create test classes for different functionality
4. Add unit tests for all public functions
5. Add integration tests for component interactions
6. Add edge case and error condition tests

### **For New Features**
1. Add tests to existing test files
2. Create new test files if needed
3. Update fixtures if new test data is required
4. Add integration tests for feature interactions

### **Test Checklist**
- [ ] Unit tests for all public functions
- [ ] Error condition tests
- [ ] Edge case tests
- [ ] Integration tests for component interactions
- [ ] Performance tests for critical functions
- [ ] Documentation for complex test scenarios

## 🤝 **Contributing to Tests**

When contributing to the test suite:

1. **Follow existing patterns** - Use similar structure and naming
2. **Add appropriate markers** - Mark tests as unit, integration, slow, or ai
3. **Use shared fixtures** - Leverage existing fixtures when possible
4. **Write descriptive tests** - Clear test names and documentation
5. **Test edge cases** - Include error conditions and boundary cases
6. **Update documentation** - Keep this README current

## 📚 **Additional Resources**

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/how-to/mark.html)
- [Pytest Coverage](https://pytest-cov.readthedocs.io/)

---

**Remember**: Good tests are an investment in code quality and developer confidence. They help catch bugs early and make refactoring safer! 