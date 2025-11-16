# AI Error Handling Guide - Quick Reference


> **File**: `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`
> **Purpose**: Fast error handling patterns and troubleshooting for AI collaborators  
> **Style**: Concise, pattern-focused, actionable  
> **For details**: See [core/ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md)

## Quick Reference

### **Error Handling Hierarchy**
```python
# Use centralized error handling
from core.error_handling import handle_errors, MHMError, DataError, FileOperationError

# Exception hierarchy (use these)
MHMError (base)
+-- DataError (data issues)
+-- FileOperationError (file system issues)
+-- ConfigError (configuration issues)
+-- CommunicationError (network/service issues)
```

### **Enhanced Error Handling Patterns**
```python
# Enhanced error handling with validation and proper defaults
@handle_errors("loading user data", default_return={})
def load_user_data(user_id: str) -> dict:
    # Validate user_id
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return {}
        
    if not user_id.strip():
        logger.error("Empty user_id provided")
        return {}
    
    # Function logic here
    return data
```

### **Common Error Patterns**
```python
# Standard error handling pattern
@handle_errors
def your_function():
    try:
        # Your code here
        result = risky_operation()
        return result
    except SpecificError as e:
        logger.error(f"Specific error occurred: {e}")
        raise DataError(f"Operation failed: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise MHMError(f"Unexpected failure: {e}") from e
```

### **Input Validation Patterns**
```python
# Validate inputs early and return appropriate defaults
@handle_errors("processing data", default_return=[])
def process_data(data: list) -> list:
    # Validate data
    if not data or not isinstance(data, list):
        logger.error(f"Invalid data: {data}")
        return []
        
    if not data:
        logger.error("Empty data provided")
        return []
    
    # Process with confidence that data is valid
    return processed_data
```

### **Specialized Error Handlers**
```python
# Use specialized error handlers for specific operations
try:
    data = load_file("path/to/file.json")
except Exception as e:
    handle_file_error(e, "path/to/file.json", "loading data", user_id="123")
    return {}

try:
    response = send_message(channel, recipient, message)
except Exception as e:
    handle_network_error(e, "sending message", user_id="123")
    return False
```

## Error Handling Patterns

### **Data Operations**
```python
# Safe data access
@handle_errors
def get_user_data(user_id):
    try:
        data = load_user_data(user_id)
        return data
    except FileNotFoundError:
        logger.warning(f"User data not found: {user_id}")
        return create_default_user_data(user_id)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid user data format: {e}")
        raise DataError(f"Corrupted user data: {user_id}") from e
```

### **File Operations**
```python
# Safe file operations
@handle_errors
def safe_file_operation(file_path):
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except PermissionError as e:
        logger.error(f"Permission denied: {file_path}")
        raise FileOperationError(f"Cannot access file: {file_path}") from e
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {file_path}")
        raise DataError(f"Corrupted file: {file_path}") from e
```

### **Configuration Handling**
```python
# Safe configuration access
@handle_errors
def get_config_value(key, default=None):
    try:
        value = os.getenv(key)
        if value is None:
            logger.warning(f"Configuration missing: {key}")
            return default
        return value
    except Exception as e:
        logger.error(f"Configuration error: {key}")
        raise ConfigError(f"Invalid configuration: {key}") from e
```

## Error Recovery Strategies

### **Automatic Retry**
```python
# Retry mechanism for transient errors
@handle_errors
def retry_operation(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return operation()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Retry {attempt + 1}/{max_retries}: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
```

### **Graceful Degradation**
```python
# Fallback mechanisms
@handle_errors
def get_user_preference(user_id, preference_key):
    try:
        return get_user_data(user_id)[preference_key]
    except (KeyError, DataError):
        logger.warning(f"Preference not found: {preference_key}")
        return get_default_preference(preference_key)
```

## Error Logging Patterns

### **Structured Logging**
```python
# Use structured logging with context
logger.error(
    "Operation failed",
    extra={
        "user_id": user_id,
        "operation": "data_load",
        "error_type": type(e).__name__,
        "error_message": str(e)
    }
)
```

### **Error Context**
```python
# Include context in error messages
try:
    result = process_user_data(user_id)
except DataError as e:
    logger.error(f"Data processing failed for user {user_id}: {e}")
    raise DataError(f"User data processing failed: {user_id}") from e
```

## Common Error Types

### **Data Errors**
- **Missing data files** - Check file paths and permissions
- **Corrupted JSON** - Validate data format
- **Invalid user data** - Check data structure and validation

### **File System Errors**
- **Permission denied** - Check file permissions and ownership
- **File not found** - Verify file paths and existence
- **Disk space** - Check available storage

### **Configuration Errors**
- **Missing environment variables** - Check .env file and system environment
- **Invalid configuration values** - Validate configuration format
- **Missing dependencies** - Check required packages and modules

### **Communication Errors**
- **Network connectivity** - Check internet connection and firewall
- **Service unavailable** - Check external service status
- **Authentication failures** - Verify tokens and credentials

## Troubleshooting Patterns

### **If System Won't Start**
1. Check `logs/errors.log` for startup failures
2. Verify configuration and environment variables
3. Check for missing dependencies or permissions

### **If Data Operations Fail**
1. Check file permissions and paths
2. Verify data format and structure
3. Check for disk space and storage issues

### **If Communication Fails**
1. Check network connectivity
2. Verify service tokens and credentials
3. Check external service status

## Error Prevention

### **Input Validation**
```python
# Validate inputs before processing
def validate_user_id(user_id):
    if not user_id or not isinstance(user_id, str):
        raise ValueError("Invalid user ID format")
    if not user_id.isalnum():
        raise ValueError("User ID must be alphanumeric")
    return user_id
```

### **Resource Management**
```python
# Use context managers for resources
@handle_errors
def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # File automatically closed
    return process_data(data)
```

## Resources
- **Full Guide**: `core/ERROR_HANDLING_GUIDE.md` - Complete error handling system documentation
- **Logging**: `ai_development_docs/AI_LOGGING_GUIDE.md` - Logging patterns and troubleshooting
- **Development Workflow**: `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md` - Error handling in development
- **Troubleshooting**: `ai_development_docs/AI_REFERENCE.md` - General troubleshooting patterns
