"""
Comprehensive Error Handling System for MHM

This module provides centralized error handling, custom exceptions, and recovery strategies
to make the application more robust and user-friendly.
"""

import os
import sys
import traceback
import logging
from typing import Optional, Dict, Any, Callable, List, Tuple
from pathlib import Path
from datetime import datetime
from core.logger import get_component_logger

# Use basic logging to avoid circular imports
logger = logging.getLogger(__name__)
error_logger = get_component_logger('errors')

# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class MHMError(Exception):
    """Base exception for all MHM-specific errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, recoverable: bool = True):
        """
        Initialize a new MHM error.
        
        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error details
            recoverable: Whether this error can be recovered from
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()

class DataError(MHMError):
    """Raised when there are issues with data files or data integrity."""
    pass

class FileOperationError(DataError):
    """Raised when file operations fail."""
    pass

class ConfigurationError(MHMError):
    """Raised when configuration is invalid or missing."""
    pass

class CommunicationError(MHMError):
    """Raised when communication channels fail."""
    pass

class SchedulerError(MHMError):
    """Raised when scheduler operations fail."""
    pass

class UserInterfaceError(MHMError):
    """Raised when UI operations fail."""
    pass

class AIError(MHMError):
    """Raised when AI operations fail."""
    pass

class ValidationError(MHMError):
    """Raised when data validation fails."""
    pass

class RecoveryError(MHMError):
    """Raised when error recovery fails."""
    pass

# ============================================================================
# ERROR RECOVERY STRATEGIES
# ============================================================================

class ErrorRecoveryStrategy:
    """Base class for error recovery strategies."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize an error recovery strategy.
        
        Args:
            name: The name of the recovery strategy
            description: A description of what this strategy does
        """
        self.name = name
        self.description = description
    
    def can_handle(self, error: Exception) -> bool:
        """Check if this strategy can handle the given error."""
        raise NotImplementedError
    
    def recover(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Attempt to recover from the error. Returns True if successful."""
        raise NotImplementedError

class FileNotFoundRecovery(ErrorRecoveryStrategy):
    """Recovery strategy for missing files."""
    
    def __init__(self):
        """Initialize the FileNotFoundRecovery strategy."""
        super().__init__("File Not Found Recovery", "Creates missing files with default data")
    
    def can_handle(self, error: Exception) -> bool:
        """
        Check if this strategy can handle the given error.
        
        Args:
            error: The exception to check
            
        Returns:
            True if this strategy can handle FileNotFoundError or file operation errors containing "not found"
        """
        return isinstance(error, FileNotFoundError) or (
            isinstance(error, FileOperationError) and "not found" in str(error).lower()
        )
    
    def recover(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        Attempt to recover from the error by creating missing files with default data.
        
        Args:
            error: The exception that occurred
            context: Additional context containing file_path and other relevant information
            
        Returns:
            True if recovery was successful, False otherwise
        """
        try:
            file_path = context.get('file_path')
            if not file_path:
                return False
            
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created missing directory: {directory}")
            
            # Create default data based on file type
            default_data = self._get_default_data(file_path, context)
            if default_data is not None:
                with open(file_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(default_data, f, indent=4, ensure_ascii=False)
                logger.info(f"Created missing file with default data: {file_path}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"File recovery failed: {e}")
            return False
    
    def _get_default_data(self, file_path: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get appropriate default data based on file type."""
        if 'user_info' in file_path:
            return {
                "user_id": context.get('user_id', 'unknown'),
                "preferences": {},
                "created": datetime.now().isoformat()
            }
        elif 'messages' in file_path:
            return {
                "messages": [],
                "category": context.get('category', 'unknown'),
                "created": datetime.now().isoformat()
            }
        elif 'schedule' in file_path:
            return {
                "periods": [],
                "category": context.get('category', 'unknown'),
                "created": datetime.now().isoformat()
            }
        return None

class JSONDecodeRecovery(ErrorRecoveryStrategy):
    """Recovery strategy for corrupted JSON files."""
    
    def __init__(self):
        """Initialize the JSONDecodeRecovery strategy."""
        super().__init__("JSON Decode Recovery", "Attempts to fix corrupted JSON files")
    
    def can_handle(self, error: Exception) -> bool:
        """
        Check if this strategy can handle the given error.
        
        Args:
            error: The exception to check
            
        Returns:
            True if this strategy can handle JSON decode errors or JSON-related file operation errors
        """
        import json
        return isinstance(error, json.JSONDecodeError) or (
            isinstance(error, FileOperationError) and "json" in str(error).lower()
        )
    
    def recover(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        Attempt to recover from the error by recreating corrupted JSON files.
        
        Args:
            error: The exception that occurred
            context: Additional context containing file_path and other relevant information
            
        Returns:
            True if recovery was successful, False otherwise
        """
        try:
            file_path = context.get('file_path')
            if not file_path:
                return False
            
            # Try to create backup of corrupted file
            backup_path = f"{file_path}.corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if os.path.exists(file_path):
                import shutil
                shutil.copy2(file_path, backup_path)
                logger.warning(f"Created backup of corrupted file: {backup_path}")
            
            # Create new file with default data
            default_data = self._get_default_data(file_path, context)
            if default_data is not None:
                with open(file_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(default_data, f, indent=4, ensure_ascii=False)
                logger.info(f"Recreated corrupted file with default data: {file_path}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"JSON recovery failed: {e}")
            return False
    
    def _get_default_data(self, file_path: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get appropriate default data based on file type."""
        if 'user_info' in file_path:
            return {
                "user_id": context.get('user_id', 'unknown'),
                "preferences": {},
                "created": datetime.now().isoformat()
            }
        elif 'messages' in file_path:
            return {
                "messages": [],
                "category": context.get('category', 'unknown'),
                "created": datetime.now().isoformat()
            }
        elif 'schedule' in file_path:
            return {
                "periods": [],
                "category": context.get('category', 'unknown'),
                "created": datetime.now().isoformat()
            }
        return None

# ============================================================================
# ERROR HANDLER
# ============================================================================

class ErrorHandler:
    """Centralized error handler for MHM."""
    
    def __init__(self):
        """
        Initialize the ErrorHandler with default recovery strategies.
        
        Sets up recovery strategies for common error types like missing files and corrupted JSON.
        """
        self.recovery_strategies: List[ErrorRecoveryStrategy] = [
            FileNotFoundRecovery(),
            JSONDecodeRecovery(),
        ]
        self.error_count: Dict[str, int] = {}
        self.max_retries = 3
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None, 
                    operation: str = "unknown", user_friendly: bool = True) -> bool:
        """
        Handle an error with recovery strategies and logging.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            operation: Description of the operation that failed
            user_friendly: Whether to show user-friendly error messages
            
        Returns:
            True if error was recovered from, False otherwise
        """
        context = context or {}
        context['operation'] = operation
        
        # Log the error
        self._log_error(error, context)
        
        # Check if we've exceeded retry limits
        error_key = f"{type(error).__name__}:{operation}"
        if self.error_count.get(error_key, 0) >= self.max_retries:
            try:
                logger.error(f"Maximum retries exceeded for {error_key}")
            except Exception:
                pass  # Don't let logger failures break error handling
            if user_friendly:
                self._show_user_error(error, context, "Maximum retries exceeded")
            return False
        
        # Try recovery strategies
        for strategy in self.recovery_strategies:
            if strategy.can_handle(error):
                try:
                    logger.info(f"Attempting recovery with strategy: {strategy.name}")
                except Exception:
                    pass  # Don't let logger failures break error handling
                if strategy.recover(error, context):
                    try:
                        logger.info(f"Successfully recovered from error using {strategy.name}")
                    except Exception:
                        pass  # Don't let logger failures break error handling
                    return True
                else:
                    try:
                        logger.warning(f"Recovery strategy {strategy.name} failed")
                    except Exception:
                        pass  # Don't let logger failures break error handling
        
        # Increment error count
        self.error_count[error_key] = self.error_count.get(error_key, 0) + 1
        
        # Show user-friendly error if requested
        if user_friendly:
            self._show_user_error(error, context)
        
        return False
    
    def _log_error(self, error: Exception, context: Dict[str, Any]):
        """Log error with context."""
        error_msg = f"Error in {context.get('operation', 'unknown operation')}: {error}"
        if context.get('file_path'):
            error_msg += f" (File: {context['file_path']})"
        if context.get('user_id'):
            error_msg += f" (User: {context['user_id']})"
        
        try:
            logger.error(error_msg, exc_info=True)
            # Use component logger for structured error logging
            error_logger.error("Error occurred", 
                             operation=context.get('operation', 'unknown'),
                             error_type=type(error).__name__,
                             error_message=str(error),
                             file_path=context.get('file_path'),
                             user_id=context.get('user_id'))
        except Exception as log_error:
            # If logging fails, we don't want to break the error handling
            # Just print to stderr as a fallback
            print(f"Logging failed: {log_error}", file=sys.stderr)
            print(f"Original error: {error_msg}", file=sys.stderr)
    
    def _show_user_error(self, error: Exception, context: Dict[str, Any], 
                        custom_message: str = None):
        """Show user-friendly error message."""
        # This will be implemented to show UI messages when appropriate
        # For now, just log the user-friendly message
        if custom_message:
            user_msg = custom_message
        else:
            user_msg = self._get_user_friendly_message(error, context)
        
        try:
            logger.error(f"User Error: {user_msg}")
        except Exception as log_error:
            # If logging fails, we don't want to break the error handling
            # Just print to stderr as a fallback
            print(f"Logging failed: {log_error}", file=sys.stderr)
            print(f"User Error: {user_msg}", file=sys.stderr)
    
    def _get_user_friendly_message(self, error: Exception, context: Dict[str, Any]) -> str:
        """Convert technical error to user-friendly message."""
        operation = context.get('operation', 'operation')
        
        if isinstance(error, FileNotFoundError):
            return f"Could not find required file. The system will try to create it automatically."
        elif isinstance(error, PermissionError):
            return f"Permission denied. Please check file permissions and try again."
        elif isinstance(error, ConnectionError):
            return f"Connection failed. Please check your internet connection and try again."
        elif isinstance(error, TimeoutError):
            return f"Operation timed out. Please try again."
        elif isinstance(error, ValueError):
            return f"Invalid data format. Please check your input and try again."
        else:
            return f"An unexpected error occurred during {operation}. Please try again or contact support."

# ============================================================================
# DECORATORS AND UTILITIES
# ============================================================================

def handle_errors(operation: str = None, context: Dict[str, Any] = None, 
                 user_friendly: bool = True, default_return=None):
    """
    Decorator to automatically handle errors in functions.
    
    Args:
        operation: Description of the operation (defaults to function name)
        context: Additional context to pass to error handler
        user_friendly: Whether to show user-friendly error messages
        default_return: Value to return if error occurs and can't be recovered
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            ctx = context or {}
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Add function context
                ctx.update({
                    'function': func.__name__,
                    'args': str(args),
                    'kwargs': str(kwargs)
                })
                
                # Try to handle the error
                if error_handler.handle_error(e, ctx, op_name, user_friendly):
                    # If recovery was successful, try the operation again
                    try:
                        return func(*args, **kwargs)
                    except Exception as e2:
                        try:
                            logger.error(f"Operation failed again after recovery: {e2}")
                        except Exception:
                            pass  # Don't let logger failures break error handling
                        return default_return
                else:
                    return default_return
        
        return wrapper
    return decorator

def safe_file_operation(file_path: str, operation: str = "file operation", 
                       user_id: str = None, category: str = None):
    """
    Context manager for safe file operations with automatic error handling.
    
    Usage:
        with safe_file_operation("path/to/file.json", "loading user data", user_id="123"):
            # file operations here
    """
    class SafeFileContext:
        """Context manager for safe file operations."""
        
        def __init__(self, file_path, operation, user_id, category):
            """
            Initialize the safe file context.
            
            Args:
                file_path: Path to the file being operated on
                operation: Description of the operation being performed
                user_id: ID of the user performing the operation
                category: Category of the operation
            """
            self.file_path = file_path
            self.operation = operation
            self.user_id = user_id
            self.category = category
            self.context = {
                'file_path': file_path,
                'operation': operation,
                'user_id': user_id,
                'category': category
            }
        
        def __enter__(self):
            """
            Enter the context manager for safe file operations.
            
            Returns:
                self: The SafeFileContext instance
            """
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            """
            Exit the context manager and handle any exceptions.
            
            Args:
                exc_type: Type of exception if any occurred
                exc_val: Exception value if any occurred
                exc_tb: Exception traceback if any occurred
            """
            if exc_val is not None:
                error_handler.handle_error(exc_val, self.context, self.operation)
                return True  # Suppress the exception
            return False
    
    return SafeFileContext(file_path, operation, user_id, category)

# ============================================================================
# GLOBAL ERROR HANDLER INSTANCE
# ============================================================================

error_handler = ErrorHandler()



# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def handle_file_error(error: Exception, file_path: str, operation: str, 
                     user_id: str = None, category: str = None) -> bool:
    """Convenience function for handling file-related errors."""
    context = {
        'file_path': file_path,
        'user_id': user_id,
        'category': category
    }
    return error_handler.handle_error(error, context, operation)

def handle_communication_error(error: Exception, channel: str, operation: str, 
                             user_id: str = None) -> bool:
    """Convenience function for handling communication errors."""
    context = {
        'channel': channel,
        'user_id': user_id
    }
    return error_handler.handle_error(error, context, operation)

def handle_configuration_error(error: Exception, setting: str, operation: str) -> bool:
    """Convenience function for handling configuration errors."""
    context = {
        'setting': setting
    }
    return error_handler.handle_error(error, context, operation) 