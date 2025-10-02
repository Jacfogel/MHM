# Exception Handling Guide - MHM System

> **Audience**: Developers, AI collaborators, and maintainers  
> **Purpose**: Comprehensive guide to the MHM exception handling system  
> **Style**: Technical, comprehensive, actionable  
> **Status**: **ACTIVE** - Always follow these patterns

> **See [README.md](../README.md) for complete navigation and project overview**  
> **See [DEVELOPMENT_WORKFLOW.md](../DEVELOPMENT_WORKFLOW.md) for safe development practices**  
> **See [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) for essential commands**

## 🚀 Quick Reference

### **Error Handling Patterns**
- **Use centralized error handling**: `core/error_handling.py`
- **Follow exception hierarchy**: `MHMError` → specific exceptions
- **Implement recovery strategies**: Automatic retry mechanisms
- **Log errors properly**: Use structured logging with context

### **Common Error Types**
- **Configuration Errors**: Invalid settings or missing files
- **Data Errors**: Corrupted or invalid user data
- **Communication Errors**: Discord/email failures
- **UI Errors**: Interface failures and user input issues

### **Error Handling Coverage Analysis**
- **Audit Integration**: Error handling coverage is automatically analyzed during audits
- **Coverage Metrics**: Tracks error handling patterns, quality, and missing coverage
- **Quality Assessment**: Rates error handling from "none" to "excellent" based on patterns used
- **Actionable Recommendations**: Provides specific guidance for improving error handling coverage

## 🎯 **Overview**

The MHM system implements a comprehensive, centralized exception handling system designed to:
- **Provide graceful error recovery** with automatic retry mechanisms
- **Ensure system stability** through proper error isolation
- **Improve user experience** with friendly error messages
- **Enable debugging** through structured error logging
- **Support maintainability** with consistent error handling patterns

## 🏗️ **Architecture**

### **Core Components**

1. **Custom Exception Hierarchy** (`core/error_handling.py`)
2. **Error Recovery Strategies** (Automatic recovery mechanisms)
3. **Centralized Error Handler** (Single point of error processing)
4. **Decorators and Utilities** (Easy-to-use error handling tools)
5. **Convenience Functions** (Specialized error handling for common scenarios)

### **Exception Hierarchy**

```
MHMError (Base Exception)
├── DataError
│   └── FileOperationError
├── ConfigurationError
├── CommunicationError
├── SchedulerError
├── UserInterfaceError
├── AIError
├── ValidationError
└── RecoveryError
```

## 🛠️ **Usage Patterns**

### **1. Using the @handle_errors Decorator**

**Recommended for most functions:**

```python
from core.error_handling import handle_errors

@handle_errors("loading user data", default_return={})
def load_user_data(user_id: str) -> dict:
    # Your function logic here
    return data
```

**Parameters:**
- `operation`: Description of what the function does
- `context`: Additional context dictionary
- `user_friendly`: Whether to show user-friendly error messages (default: True)
- `default_return`: Value to return if error occurs and can't be recovered

### **2. Using Convenience Functions**

**For specific error types:**

```python
from core.error_handling import (
    handle_file_error,
    handle_network_error,
    handle_communication_error,
    handle_configuration_error,
    handle_validation_error,
    handle_ai_error
)

# File operations
try:
    data = load_file("path/to/file.json")
except Exception as e:
    handle_file_error(e, "path/to/file.json", "loading data", user_id="123")

# Network operations
try:
    response = send_message(channel, recipient, message)
except Exception as e:
    handle_network_error(e, "sending message", user_id="123")

# Communication operations
try:
    result = discord_bot.send_message(user, message)
except Exception as e:
    handle_communication_error(e, "discord", "sending message", user_id="123")
```

### **3. Using the Safe File Context Manager**

**For file operations:**

```python
from core.error_handling import safe_file_operation

with safe_file_operation("path/to/file.json", "loading user data", user_id="123"):
    # File operations here are automatically protected
    with open("path/to/file.json", "r") as f:
        data = json.load(f)
```

**Benefits:**
- Automatic error handling for all file operations within the context
- Proper error logging with file path and operation context
- Automatic recovery for common file errors (missing files, permission issues)
- User-friendly error messages when operations fail

### **4. Direct Error Handler Usage**

**For complex scenarios:**

```python
from core.error_handling import error_handler

try:
    # Your operation here
    result = complex_operation()
except Exception as e:
    context = {
        'user_id': user_id,
        'operation_type': 'complex_operation',
        'additional_data': some_data
    }
    recovered = error_handler.handle_error(e, context, "complex operation")
    if not recovered:
        # Handle the case where recovery failed
        return fallback_value
```

## 🔄 **Error Recovery Strategies**

The system includes automatic recovery strategies for common error types:

### **1. FileNotFoundRecovery**
- **Handles**: `FileNotFoundError`, file operation errors with "not found"
- **Action**: Creates missing files with appropriate default data
- **Use Case**: User data files, configuration files, message files

### **2. JSONDecodeRecovery**
- **Handles**: `json.JSONDecodeError`, JSON-related file operation errors
- **Action**: Creates backup of corrupted file and recreates with default data
- **Use Case**: Corrupted JSON files, malformed data files

### **3. NetworkRecovery**
- **Handles**: `ConnectionError`, `TimeoutError`, `OSError`, network-related communication errors
- **Action**: Waits for network connectivity and retries
- **Use Case**: Discord API calls, email sending, external service communication

### **4. ConfigurationRecovery**
- **Handles**: `ConfigurationError`, configuration-related `KeyError`
- **Action**: Uses default configuration values
- **Use Case**: Missing configuration settings, invalid configuration values

## 📝 **Best Practices**

### **DO:**
- ✅ Use `@handle_errors` decorator for most functions
- ✅ Provide meaningful operation descriptions
- ✅ Use appropriate default return values
- ✅ Include user_id in context when available
- ✅ Use convenience functions for specific error types
- ✅ Let the system handle recovery automatically
- ✅ Test error scenarios in your code

### **DON'T:**
- ❌ Use bare `except Exception:` blocks without proper handling
- ❌ Ignore errors or use `pass` without logging
- ❌ Create custom exception handling when the system provides it
- ❌ Suppress errors without understanding the impact
- ❌ Forget to test error recovery scenarios

## 🎨 **Error Message Guidelines**

### **User-Friendly Messages**
The system automatically converts technical errors to user-friendly messages:

- **FileNotFoundError**: "Could not find required file. The system will try to create it automatically."
- **PermissionError**: "Permission denied. Please check file permissions and try again."
- **ConnectionError**: "Connection failed. Please check your internet connection and try again."
- **TimeoutError**: "Operation timed out. Please try again."
- **ValueError**: "Invalid data format. Please check your input and try again."
- **KeyError**: "Missing required information. Please check your input and try again."
- **TypeError**: "Data type error. Please check your input format and try again."

### **Technical Logging**
All errors are logged with:
- Full exception details and traceback
- Operation context
- User ID (when available)
- File paths (when relevant)
- Timestamp and error type

### **Component Logger Integration**
The error handling system integrates with the MHM component logging system:
- **Main Logger**: General application errors go to `app.log`
- **Error Logger**: Structured error information goes to `errors.log`
- **Component Loggers**: Errors are also logged to relevant component logs (e.g., Discord errors to `discord.log`)
- **Structured Data**: Error context is logged with structured metadata for analysis

## 🔧 **Configuration**

### **Error Handler Settings**
```python
# In core/error_handling.py
class ErrorHandler:
    def __init__(self):
        self.max_retries = 3  # Maximum retry attempts
        self.recovery_strategies = [
            FileNotFoundRecovery(),
            JSONDecodeRecovery(),
            NetworkRecovery(),
            ConfigurationRecovery(),
        ]
```

### **Custom Recovery Strategies**
You can add custom recovery strategies by extending `ErrorRecoveryStrategy`:

```python
class CustomRecovery(ErrorRecoveryStrategy):
    def __init__(self):
        super().__init__("Custom Recovery", "Handles specific error types")
    
    def can_handle(self, error: Exception) -> bool:
        return isinstance(error, CustomError)
    
    def recover(self, error: Exception, context: Dict[str, Any]) -> bool:
        # Implement recovery logic
        return True
```

## 🧪 **Testing Error Handling**

### **Unit Tests**
```python
def test_error_handling():
    # Test that errors are properly caught and handled
    with pytest.raises(FileNotFoundError):
        load_nonexistent_file()
    
    # Test recovery mechanisms
    result = load_file_with_recovery("missing_file.json")
    assert result == default_data
```

### **Integration Tests**
```python
def test_network_error_recovery():
    # Simulate network failure
    with mock_network_failure():
        result = send_message_with_recovery()
        assert result is not None  # Should recover
```

## 📊 **Monitoring and Debugging**

### **Error Logging**
All errors are logged to:
- **Main log**: `logs/app.log` - General application errors
- **Error log**: `logs/errors.log` - Structured error information
- **Component logs**: Specific component error logs

### **Error Metrics**
The system tracks:
- Error counts by type and operation
- Recovery success rates
- Retry attempts and outcomes

### **Debugging Tips**
1. Check `logs/errors.log` for structured error information
2. Look for recovery strategy logs in `logs/app.log`
3. Use error context to understand failure points
4. Monitor error counts to identify recurring issues

## 🚨 **Critical Error Scenarios**

### **High Priority**
1. **File System Errors**: Missing user data, corrupted files
2. **Network Failures**: Discord API, email service failures
3. **Configuration Issues**: Missing environment variables, invalid settings
4. **Data Validation Errors**: Invalid user input, malformed data

### **Recovery Priorities**
1. **User Data**: Always attempt recovery for user data files
2. **Communication**: Retry network operations with backoff
3. **Configuration**: Use sensible defaults when possible
4. **Validation**: Provide clear error messages for user input

## 🔄 **Migration Guide**

### **Converting Existing Code**

**Before (Bad):**
```python
def load_user_data(user_id):
    try:
        with open(f"data/users/{user_id}.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return {}
```

**After (Good):**
```python
@handle_errors("loading user data", default_return={})
def load_user_data(user_id):
    with open(f"data/users/{user_id}.json", "r") as f:
        return json.load(f)
```

### **Gradual Migration**
1. Start with high-risk functions (file operations, network calls)
2. Add error handling to user-facing functions
3. Update internal functions as you encounter them
4. Test error scenarios after each migration

## 📚 **Related Documentation**

- **`core/error_handling.py`**: Complete implementation
- **`tests/unit/test_error_handling.py`**: Test examples
- **`CHANGELOG_DETAIL.md`**: Recent error handling improvements
- **`AI_CHANGELOG.md`**: AI-focused error handling updates

## 🎯 **Future Enhancements**

### **Planned Improvements**
1. **Metrics Dashboard**: Real-time error monitoring
2. **Advanced Recovery**: Machine learning-based recovery strategies
3. **User Notifications**: Proactive error notifications
4. **Performance Monitoring**: Error impact on system performance

### **Extension Points**
1. **Custom Recovery Strategies**: Domain-specific error recovery
2. **Error Analytics**: Advanced error pattern analysis
3. **Integration Hooks**: Third-party error handling integration
4. **Configuration Management**: Dynamic error handling configuration

---

**Remember**: Good error handling is not just about catching errors—it's about providing a smooth, reliable user experience even when things go wrong. The MHM error handling system is designed to make your code more robust and your users happier.
